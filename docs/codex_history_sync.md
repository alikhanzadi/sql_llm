# Codex History Sync

`app.codex_history_sync` copies the local Codex Desktop history artifacts that make conversations discoverable on another computer:

- `~/.codex/sessions`
- `~/.codex/archived_sessions`
- `~/.codex/session_index.jsonl`
- `~/.codex/memories`

It does not copy `auth.json`, config, logs, SQLite state, shell snapshots, plugin caches, or other machine-local files.

## One-Time Setup

Use a folder that exists on both computers, such as an iCloud Drive, Dropbox, Syncthing, or USB folder.

```bash
mkdir -p "$HOME/Library/Mobile Documents/com~apple~CloudDocs/codex-sync"
```

Replace that path with whichever shared folder you prefer.

## Commands

See what will be syncable on this computer:

```bash
python -m app.codex_history_sync status
```

Push this computer's Codex history to the shared folder:

```bash
python -m app.codex_history_sync push "$HOME/Library/Mobile Documents/com~apple~CloudDocs/codex-sync"
```

Pull the newest bundle from the shared folder into this computer:

```bash
python -m app.codex_history_sync pull "$HOME/Library/Mobile Documents/com~apple~CloudDocs/codex-sync"
```

Do both in one step:

```bash
python -m app.codex_history_sync sync "$HOME/Library/Mobile Documents/com~apple~CloudDocs/codex-sync"
```

Preview a pull without writing files:

```bash
python -m app.codex_history_sync pull "$HOME/Library/Mobile Documents/com~apple~CloudDocs/codex-sync" --dry-run
```

## Recommended Two-Computer Flow

On computer A:

```bash
python -m app.codex_history_sync sync "$HOME/Library/Mobile Documents/com~apple~CloudDocs/codex-sync"
```

Wait for the shared folder provider to upload the bundle.

On computer B:

```bash
python -m app.codex_history_sync sync "$HOME/Library/Mobile Documents/com~apple~CloudDocs/codex-sync"
```

Repeat the same command when switching machines.

## Notes

- The importer merges `session_index.jsonl` by thread id and keeps the newest `updated_at`.
- Session files are copied only when the incoming file is newer or different in size.
- Keep Codex closed while doing large imports if you want to avoid UI refresh timing issues.
- The generated bundles are ordinary `.tar.gz` archives named `codex-history-sync-<host>-<timestamp>.tar.gz`.
