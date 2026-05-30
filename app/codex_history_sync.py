"""Portable Codex Desktop history sync utility.

This module syncs the conversation artifacts that make another Codex install
able to discover and resume prior threads. It intentionally avoids auth tokens,
local SQLite state, logs, plugin caches, and shell snapshots.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import socket
import tarfile
import tempfile
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable


SCHEMA_VERSION = 1
BUNDLE_PREFIX = "codex-history-sync"
BUNDLE_SUFFIX = ".tar.gz"

DEFAULT_INCLUDE_PATHS = (
    "sessions",
    "archived_sessions",
    "session_index.jsonl",
    "memories",
)


@dataclass(frozen=True)
class FileRecord:
    relative_path: str
    size: int
    sha256: str
    mtime_ns: int


def default_codex_home() -> Path:
    return Path(os.environ.get("CODEX_HOME", "~/.codex")).expanduser()


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as file:
        for chunk in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def iter_sync_files(codex_home: Path) -> Iterable[Path]:
    for relative in DEFAULT_INCLUDE_PATHS:
        path = codex_home / relative
        if not path.exists():
            continue
        if path.is_file():
            yield path
            continue
        for child in sorted(path.rglob("*")):
            if child.is_file():
                yield child


def build_file_records(codex_home: Path) -> list[FileRecord]:
    records = []
    for path in iter_sync_files(codex_home):
        stat = path.stat()
        records.append(
            FileRecord(
                relative_path=path.relative_to(codex_home).as_posix(),
                size=stat.st_size,
                sha256=sha256_file(path),
                mtime_ns=stat.st_mtime_ns,
            )
        )
    return records


def load_session_index(path: Path) -> dict[str, dict]:
    if not path.exists():
        return {}

    entries: dict[str, dict] = {}
    with path.open("r", encoding="utf-8") as file:
        for line in file:
            line = line.strip()
            if not line:
                continue
            try:
                item = json.loads(line)
            except json.JSONDecodeError:
                continue
            session_id = item.get("id")
            if not session_id:
                continue
            existing = entries.get(session_id)
            if existing is None or item.get("updated_at", "") > existing.get("updated_at", ""):
                entries[session_id] = item
    return entries


def write_session_index(path: Path, entries: dict[str, dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    ordered = sorted(entries.values(), key=lambda item: item.get("updated_at", ""))
    with path.open("w", encoding="utf-8") as file:
        for item in ordered:
            file.write(json.dumps(item, sort_keys=True, separators=(",", ":")) + "\n")


def merge_session_indices(left: dict[str, dict], right: dict[str, dict]) -> dict[str, dict]:
    merged = dict(left)
    for session_id, item in right.items():
        existing = merged.get(session_id)
        if existing is None or item.get("updated_at", "") > existing.get("updated_at", ""):
            merged[session_id] = item
    return merged


def make_manifest(codex_home: Path, records: list[FileRecord]) -> dict:
    return {
        "schema_version": SCHEMA_VERSION,
        "created_at": utc_now(),
        "created_by_host": socket.gethostname(),
        "codex_home": str(codex_home),
        "included_paths": list(DEFAULT_INCLUDE_PATHS),
        "file_count": len(records),
        "total_bytes": sum(record.size for record in records),
        "files": [record.__dict__ for record in records],
    }


def create_bundle(codex_home: Path, output_dir: Path) -> Path:
    codex_home = codex_home.expanduser().resolve()
    output_dir = output_dir.expanduser().resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    records = build_file_records(codex_home)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    host = socket.gethostname().replace("/", "-")
    bundle_path = output_dir / f"{BUNDLE_PREFIX}-{host}-{stamp}{BUNDLE_SUFFIX}"

    with tempfile.TemporaryDirectory(prefix="codex-history-sync-") as temp_root:
        temp_path = Path(temp_root)
        manifest_path = temp_path / "manifest.json"
        manifest_path.write_text(
            json.dumps(make_manifest(codex_home, records), indent=2, sort_keys=True),
            encoding="utf-8",
        )

        with tarfile.open(bundle_path, "w:gz") as tar:
            tar.add(manifest_path, arcname="manifest.json")
            for record in records:
                source = codex_home / record.relative_path
                tar.add(source, arcname=f"codex/{record.relative_path}", recursive=False)

    return bundle_path


def find_latest_bundle(sync_dir: Path) -> Path:
    bundles = sorted(
        sync_dir.expanduser().glob(f"{BUNDLE_PREFIX}-*{BUNDLE_SUFFIX}"),
        key=lambda path: path.stat().st_mtime_ns,
    )
    if not bundles:
        raise FileNotFoundError(f"No {BUNDLE_PREFIX} bundle found in {sync_dir}")
    return bundles[-1]


def safe_member_target(codex_home: Path, member_name: str) -> Path:
    if not member_name.startswith("codex/"):
        raise ValueError(f"Unexpected bundle member: {member_name}")
    relative = Path(member_name.removeprefix("codex/"))
    if relative.is_absolute() or ".." in relative.parts:
        raise ValueError(f"Unsafe bundle path: {member_name}")
    target = (codex_home / relative).resolve()
    codex_root = codex_home.resolve()
    if codex_root not in (target, *target.parents):
        raise ValueError(f"Bundle member escapes Codex home: {member_name}")
    return target


def copy_if_newer(source: Path, target: Path, dry_run: bool) -> bool:
    if target.exists():
        source_stat = source.stat()
        target_stat = target.stat()
        if target_stat.st_mtime_ns >= source_stat.st_mtime_ns and target_stat.st_size == source_stat.st_size:
            return False
    if dry_run:
        return True
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, target)
    return True


def import_bundle(codex_home: Path, bundle_path: Path, dry_run: bool = False) -> dict:
    codex_home = codex_home.expanduser().resolve()
    bundle_path = bundle_path.expanduser().resolve()
    imported_files = 0

    with tempfile.TemporaryDirectory(prefix="codex-history-import-") as temp_root:
        temp_path = Path(temp_root)
        with tarfile.open(bundle_path, "r:gz") as tar:
            members = tar.getmembers()
            for member in members:
                if member.name == "manifest.json":
                    continue
                if member.isfile():
                    safe_member_target(codex_home, member.name)
                elif member.isdir():
                    continue
                else:
                    raise ValueError(f"Unsupported bundle member type: {member.name}")

            for member in members:
                if member.isdir():
                    continue
                if member.name == "manifest.json":
                    tar.extract(member, temp_path, filter="data")
                    continue
                if member.isfile():
                    tar.extract(member, temp_path, filter="data")

        incoming_root = temp_path / "codex"
        incoming_index = load_session_index(incoming_root / "session_index.jsonl")
        existing_index = load_session_index(codex_home / "session_index.jsonl")

        for source in sorted(incoming_root.rglob("*")):
            if not source.is_file() or source.name == "session_index.jsonl":
                continue
            target = codex_home / source.relative_to(incoming_root)
            if copy_if_newer(source, target, dry_run):
                imported_files += 1

        merged_index = merge_session_indices(existing_index, incoming_index)
        if merged_index != existing_index:
            imported_files += 1
            if not dry_run:
                write_session_index(codex_home / "session_index.jsonl", merged_index)

    return {"bundle": str(bundle_path), "imported_files": imported_files, "dry_run": dry_run}


def status(codex_home: Path) -> dict:
    codex_home = codex_home.expanduser()
    records = build_file_records(codex_home)
    sessions = [record for record in records if record.relative_path.startswith("sessions/")]
    archived = [record for record in records if record.relative_path.startswith("archived_sessions/")]
    memories = [record for record in records if record.relative_path.startswith("memories/")]
    return {
        "codex_home": str(codex_home),
        "syncable_files": len(records),
        "total_bytes": sum(record.size for record in records),
        "sessions": len(sessions),
        "archived_sessions": len(archived),
        "memories": len(memories),
        "has_session_index": (codex_home / "session_index.jsonl").exists(),
    }


def print_json(payload: dict) -> None:
    print(json.dumps(payload, indent=2, sort_keys=True))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Sync Codex Desktop chat history and memory artifacts between computers."
    )
    parser.add_argument("--codex-home", type=Path, default=default_codex_home())

    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("status", help="Show syncable Codex history counts.")

    export_parser = subparsers.add_parser("export", help="Create a portable history bundle.")
    export_parser.add_argument("--out", type=Path, required=True, help="Directory for the bundle.")

    import_parser = subparsers.add_parser("import", help="Merge a bundle into this machine.")
    import_parser.add_argument("bundle", type=Path)
    import_parser.add_argument("--dry-run", action="store_true")

    push_parser = subparsers.add_parser("push", help="Export a bundle into a shared sync folder.")
    push_parser.add_argument("sync_dir", type=Path)

    pull_parser = subparsers.add_parser("pull", help="Import the newest bundle from a shared sync folder.")
    pull_parser.add_argument("sync_dir", type=Path)
    pull_parser.add_argument("--dry-run", action="store_true")

    sync_parser = subparsers.add_parser("sync", help="Pull newest bundle, then push this machine's state.")
    sync_parser.add_argument("sync_dir", type=Path)
    sync_parser.add_argument("--dry-run", action="store_true")

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "status":
        print_json(status(args.codex_home))
        return 0

    if args.command in {"export", "push"}:
        output_dir = args.out if args.command == "export" else args.sync_dir
        bundle_path = create_bundle(args.codex_home, output_dir)
        print_json({"bundle": str(bundle_path)})
        return 0

    if args.command == "import":
        print_json(import_bundle(args.codex_home, args.bundle, args.dry_run))
        return 0

    if args.command == "pull":
        bundle_path = find_latest_bundle(args.sync_dir)
        print_json(import_bundle(args.codex_home, bundle_path, args.dry_run))
        return 0

    if args.command == "sync":
        pull_result = None
        try:
            bundle_path = find_latest_bundle(args.sync_dir)
            pull_result = import_bundle(args.codex_home, bundle_path, args.dry_run)
        except FileNotFoundError:
            pull_result = {"skipped": "no remote bundle found"}

        pushed_bundle = None
        if not args.dry_run:
            pushed_bundle = str(create_bundle(args.codex_home, args.sync_dir))
        print_json({"pull": pull_result, "pushed_bundle": pushed_bundle, "dry_run": args.dry_run})
        return 0

    parser.error(f"Unhandled command: {args.command}")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
