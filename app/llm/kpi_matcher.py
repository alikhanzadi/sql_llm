from dataclasses import dataclass, field
import os
import re
from typing import Optional

from app.rag.catalog.kpi_catalog import load_kpi_catalog


TOKEN_RE = re.compile(r"[a-z0-9_]+")
MATCH_THRESHOLD = 0.58
AMBIGUOUS_MARGIN = 0.03
LEADERBOARD_TERMS = {"top", "rank", "ranking", "highest", "lowest", "most", "least", "leaderboard"}

# Cluster default-resolution: when top-2 candidates are within AMBIGUOUS_MARGIN,
# resolve to the cluster default rather than falling back to schema-only.
REVENUE_CLUSTER = {"total_token_revenue", "issuer_revenue", "platform_fee_revenue"}
REVENUE_CLUSTER_DEFAULT = "total_token_revenue"

# Embedding-shortlist matching (primary path). Each canonical KPI is embedded into the
# Neon `kpi_embeddings` (pgvector) table by app/rag/catalog/embed_kpis.py. At runtime we
# embed the question, retrieve the nearest KPIs, then resolve among them with the same
# deterministic rules used by the lexical path. Falls back to lexical if the vector store
# or embedding API is unavailable (e.g. offline local dev).
EMBED_MODEL = "text-embedding-3-small"
KPI_TOPK = 8                # recall@8 ~98% on the held-out paraphrase set
# Gate tuned against app/eval/{paraphrase,negative}_cases.json: KPI paraphrases bottom out
# at ~0.31, clear out-of-domain (weather/password/"list tables") sits <0.27. 0.30 keeps all
# real KPI questions and rejects out-of-domain. NOTE: schema-exploration questions ("sample
# the issuers table") overlap the KPI band and are NOT separable by similarity alone — an
# LLM judge over the shortlist (with a NONE option) is the principled fix for that overlap.
SIMILARITY_GATE = 0.30
SIMILARITY_MARGIN = 0.03    # near-tie band for deterministic resolution among candidates

_openai_client = None
_neon_conn = None


@dataclass
class KpiMatchDecision:
    """Structured outcome for KPI matching and downstream prompt routing."""

    matched: bool
    confidence: float
    reason: str
    kpi_id: Optional[str] = None
    status: Optional[str] = None
    missing_dependencies: list[str] = field(default_factory=list)
    kpi: Optional[dict] = None

    def to_prompt_block(self) -> str:
        """Return canonical KPI context for prompting only when match is active."""
        if not self.matched or not self.kpi:
            return ""
        if self.status != "active":
            return ""

        kpi = self.kpi
        recipe = kpi.get("sql_recipe", {})
        group_by = recipe.get("group_by")
        group_by_text = ", ".join(group_by) if isinstance(group_by, list) else (group_by or "none")

        lines = [
            "Canonical KPI Context (authoritative — follow this recipe exactly):",
            f"- kpi_id: {kpi.get('kpi_id', '')}",
            f"- name: {kpi.get('name', '')}",
            f"- definition: {kpi.get('business_definition', '')}",
            f"- required_tables: {', '.join(kpi.get('required_tables', [])) or 'none'}",
            f"- required_joins: {', '.join(kpi.get('required_joins', [])) or 'none'}",
            f"- MUST apply these filters: {', '.join(kpi.get('filters_defaults', [])) or 'none'}",
        ]

        # value_basis prevents gross/net/fee revenue confusion — always surface it.
        if kpi.get("value_basis"):
            lines.append(f"- value_basis: {kpi['value_basis']} (do not substitute a different revenue scale)")

        # raw_sql recipes are the exact intended query — present them as the template.
        raw_sql = recipe.get("raw_sql")
        if raw_sql:
            lines.append(f"- exact_sql_template (adapt aliases/filters as needed, keep the logic): {raw_sql}")
        else:
            lines.append(f"- recipe_pattern: {recipe.get('pattern', '')}")
            lines.append(f"- recipe_numerator: {recipe.get('numerator', '') or 'none'}")
            lines.append(f"- recipe_denominator: {recipe.get('denominator', '') or 'none'}")
            lines.append(f"- recipe_group_by: {group_by_text}")

        return "\n".join(lines)

    def blocked_message(self) -> str:
        """Build user-safe message for KPIs blocked by missing data dependencies."""
        deps = ", ".join(self.missing_dependencies) or "required source tables/events"
        return (
            f"KPI '{self.kpi_id}' is blocked_by_missing_data. "
            f"Missing dependencies: {deps}."
        )


def _norm(text: str) -> str:
    """Lowercase and normalize whitespace for deterministic string comparisons."""
    return " ".join(text.lower().split())


def _tokenize(text: str) -> set[str]:
    """Tokenize normalized text and lightly singularize plural nouns."""
    normalized = set()
    for token in TOKEN_RE.findall(_norm(text)):
        if len(token) > 3 and token.endswith("s"):
            token = token[:-1]
        normalized.add(token)
    return normalized


def _score_entry(question: str, q_tokens: set[str], kpi: dict, plan) -> float:
    """Score one KPI candidate against question text plus planner signals."""
    score = 0.0
    name = _norm(kpi.get("name", ""))
    aliases = [_norm(a) for a in kpi.get("aliases", [])]
    name_tokens = _tokenize(name)

    if name and name in question:
        score += 0.65
    for alias in aliases:
        if alias and alias in question:
            score += 0.55
            break

    overlap_count = len(q_tokens & name_tokens)
    if overlap_count >= 2:
        score += 0.45
    elif overlap_count == 1:
        score += 0.18

    candidate_tokens = _tokenize(" ".join([name] + aliases))
    if candidate_tokens:
        overlap = len(q_tokens & candidate_tokens) / len(candidate_tokens)
        score += overlap * 0.35

    examples = " ".join(kpi.get("example_questions", []))
    example_tokens = _tokenize(examples)
    if example_tokens:
        overlap_examples = len(q_tokens & example_tokens) / len(example_tokens)
        score += overlap_examples * 0.30

    time_grains = set(kpi.get("time_grains", []))
    if plan.time_grain in time_grains:
        score += 0.08

    recipe_pattern = str(kpi.get("sql_recipe", {}).get("pattern", ""))
    if plan.intent == "top_k" and "rank" in recipe_pattern:
        score += 0.08
    elif plan.intent in {"count", "sum", "avg_per_entity"} and any(
        word in recipe_pattern for word in {"count", "sum", "average", "ratio"}
    ):
        score += 0.05

    if plan.entities:
        entity_tokens = set(plan.entities)
        if q_tokens & entity_tokens:
            score += 0.04

    return min(score, 0.99)


def _longest_match_in_question(kpi: dict, question: str) -> int:
    """Return the character length of the longest name/alias substring found in question."""
    name = _norm(kpi.get("name", ""))
    aliases = [_norm(a) for a in kpi.get("aliases", [])]
    candidates = [name] + aliases
    return max((len(c) for c in candidates if c and c in question), default=0)


def _resolve_ambiguous(best: dict, second: Optional[dict], question: str = "") -> Optional[dict]:
    """
    When two candidates are within AMBIGUOUS_MARGIN, attempt deterministic resolution.

    Rules (in order):
    1. If both candidates are in the revenue cluster, return the cluster default.
    2. If the top-2 differ in value_basis, force the cluster default.
    3. Specificity tiebreak: prefer the candidate whose longest matching name/alias
       substring is longer. A 25-char exact match beats a 16-char one — more specific.
    4. Otherwise return None — fall back to schema-only.
    """
    if second is None:
        return None

    best_id = best.get("kpi_id", "")
    second_id = second.get("kpi_id", "")

    # Rule 1: both in revenue cluster → default
    if best_id in REVENUE_CLUSTER and second_id in REVENUE_CLUSTER:
        catalog = load_kpi_catalog()
        kpis_by_id = {k["kpi_id"]: k for k in catalog.get("kpis", [])}
        return kpis_by_id.get(REVENUE_CLUSTER_DEFAULT)

    # Rule 2: specificity tiebreak via longest exact substring match.
    # A 23-char exact match is far more specific than a 7-char one — use it first
    # so we don't over-apply the revenue cluster default to clearly-distinguished KPIs.
    if question:
        best_len = _longest_match_in_question(best, question)
        second_len = _longest_match_in_question(second, question)
        if best_len > second_len:
            return best
        if second_len > best_len:
            return second

    # Rule 3: value_basis mismatch in near-tie → force revenue cluster default.
    # Only reaches here when specificity cannot break the tie (equal-length matches).
    best_basis = best.get("value_basis")
    second_basis = second.get("value_basis")
    if best_basis and second_basis and best_basis != second_basis:
        catalog = load_kpi_catalog()
        kpis_by_id = {k["kpi_id"]: k for k in catalog.get("kpis", [])}
        return kpis_by_id.get(REVENUE_CLUSTER_DEFAULT)

    return None


def _get_openai_client():
    """Lazy-init the OpenAI client so the module imports without the dependency/key."""
    global _openai_client
    if _openai_client is None:
        from openai import OpenAI
        _openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    return _openai_client


def _get_neon_conn():
    """Return a cached read-only Neon connection, or None if unavailable."""
    global _neon_conn
    if _neon_conn is not None and not getattr(_neon_conn, "closed", 1):
        return _neon_conn
    url = os.getenv("DATABASE_URL")
    if not url:
        return None
    import psycopg2

    conn = psycopg2.connect(url, sslmode="require", options="-c statement_timeout=10000")
    conn.set_session(readonly=True, autocommit=True)
    _neon_conn = conn
    return _neon_conn


def _vec_literal(vec) -> str:
    """Format an embedding as a pgvector literal."""
    return "[" + ",".join(f"{x:.8f}" for x in vec) + "]"


def _embedding_candidates(question: str, k: int = KPI_TOPK):
    """Return [(similarity, kpi_dict), ...] from the pgvector index, or None on failure.

    None signals the caller to fall back to lexical matching (offline / no key / Neon down).
    """
    global _neon_conn
    try:
        client = _get_openai_client()
        embedding = client.embeddings.create(model=EMBED_MODEL, input=question).data[0].embedding
        conn = _get_neon_conn()
        if conn is None:
            return None
        by_id = {k["kpi_id"]: k for k in load_kpi_catalog().get("kpis", [])}
        literal = _vec_literal(embedding)
        with conn.cursor() as cur:
            cur.execute(
                "SELECT kpi_id, 1 - (embedding <=> %s::vector) AS sim "
                "FROM kpi_embeddings ORDER BY embedding <=> %s::vector LIMIT %s;",
                (literal, literal, k),
            )
            rows = cur.fetchall()
        candidates = [(float(sim), by_id[kid]) for kid, sim in rows if kid in by_id]
        return candidates or None
    except Exception:
        # Reset a possibly-broken connection and signal lexical fallback.
        try:
            if _neon_conn is not None:
                _neon_conn.close()
        except Exception:
            pass
        _neon_conn = None
        return None


def _resolve_candidates(normalized_question: str, plan, candidates) -> KpiMatchDecision:
    """Pick one KPI from the embedding shortlist using the deterministic resolver."""
    best_sim, best_kpi = candidates[0]

    if best_sim < SIMILARITY_GATE:
        return KpiMatchDecision(
            matched=False,
            confidence=best_sim,
            reason=f"Top semantic similarity {best_sim:.3f} below gate; using schema fallback.",
        )

    # Candidates within the near-tie band of the best similarity.
    within = [(s, k) for s, k in candidates if best_sim - s < SIMILARITY_MARGIN]
    winner = None
    if len(within) > 1:
        # Specificity tiebreak: a literal name/alias match in the question wins.
        lm = {k["kpi_id"]: _longest_match_in_question(k, normalized_question) for _, k in within}
        max_lm = max(lm.values(), default=0)
        if max_lm > 0:
            tops = [k for _, k in within if lm[k["kpi_id"]] == max_lm]
            if len(tops) == 1:
                winner = tops[0]
        if winner is None:
            resolved = _resolve_ambiguous(within[0][1], within[1][1], normalized_question)
            if resolved is not None:
                winner = resolved
    if winner is None:
        winner = best_kpi

    # Leaderboard guardrail: only match ranking-style questions.
    if winner.get("category") == "leaderboard":
        has_leaderboard_language = any(term in normalized_question for term in LEADERBOARD_TERMS)
        if not plan.requires_ranking and not has_leaderboard_language:
            return KpiMatchDecision(
                matched=False,
                confidence=best_sim,
                reason="Leaderboard KPI requires ranking intent; using schema fallback.",
            )

    return KpiMatchDecision(
        matched=True,
        confidence=best_sim,
        reason=f"Semantic match (similarity {best_sim:.3f}).",
        kpi_id=winner.get("kpi_id"),
        status=winner.get("status"),
        missing_dependencies=winner.get("missing_dependencies", []),
        kpi=winner,
    )


def match_kpi(question: str, plan) -> KpiMatchDecision:
    """Match a question to one canonical KPI via embedding shortlist + deterministic resolver.

    Falls back to lexical matching when the vector store / embedding API is unavailable.
    """
    candidates = _embedding_candidates(question)
    if candidates is None:
        return _lexical_match_kpi(question, plan)
    return _resolve_candidates(_norm(question), plan, candidates)


def _lexical_match_kpi(question: str, plan) -> KpiMatchDecision:
    """Lexical fallback: score all KPIs by name/alias/example overlap with guardrails."""
    normalized_question = _norm(question)
    q_tokens = _tokenize(normalized_question)
    catalog = load_kpi_catalog()
    kpis = catalog.get("kpis", [])

    ranked: list[tuple[float, dict]] = []
    for kpi in kpis:
        score = _score_entry(normalized_question, q_tokens, kpi, plan)
        ranked.append((score, kpi))

    ranked.sort(key=lambda x: x[0], reverse=True)
    best_score, best_kpi = ranked[0] if ranked else (0.0, None)
    second_score = ranked[1][0] if len(ranked) > 1 else 0.0

    if not best_kpi or best_score < MATCH_THRESHOLD:
        return KpiMatchDecision(
            matched=False,
            confidence=best_score,
            reason="No KPI match passed confidence threshold.",
        )

    # Guardrail: leaderboard KPIs should only match ranking-style questions.
    # Otherwise generic trading questions can inherit a narrow default window (e.g., 7d)
    # and return empty/null outputs on stale local datasets.
    if best_kpi.get("category") == "leaderboard":
        has_leaderboard_language = any(
            term in normalized_question for term in LEADERBOARD_TERMS
        )
        if not plan.requires_ranking and not has_leaderboard_language:
            return KpiMatchDecision(
                matched=False,
                confidence=best_score,
                reason="Leaderboard KPI requires ranking intent; using schema fallback.",
            )

    if (best_score - second_score) < AMBIGUOUS_MARGIN:
        # Collect ALL candidates within AMBIGUOUS_MARGIN of the best score.
        # The 0.99 cap collapses genuinely different-quality matches — use longest
        # exact substring match across all tied candidates to pick the most specific.
        within_margin = [k for s, k in ranked if best_score - s < AMBIGUOUS_MARGIN]
        lm_by_kpi = {k["kpi_id"]: _longest_match_in_question(k, normalized_question) for k in within_margin}
        max_lm = max(lm_by_kpi.values(), default=0)
        if max_lm > 0:
            top_by_lm = [k for k in within_margin if lm_by_kpi[k["kpi_id"]] == max_lm]
            if len(top_by_lm) == 1:
                winner = top_by_lm[0]
                return KpiMatchDecision(
                    matched=True,
                    confidence=best_score,
                    reason=f"Ambiguous match resolved by specificity (longest exact match) to '{winner['kpi_id']}'.",
                    kpi_id=winner.get("kpi_id"),
                    status=winner.get("status"),
                    missing_dependencies=winner.get("missing_dependencies", []),
                    kpi=winner,
                )

        second_kpi = ranked[1][1] if len(ranked) > 1 else None
        resolved = _resolve_ambiguous(best_kpi, second_kpi, normalized_question)
        if resolved is not None:
            return KpiMatchDecision(
                matched=True,
                confidence=best_score,
                reason=(
                    f"Ambiguous match resolved to cluster default '{resolved.get('kpi_id')}'. "
                    f"Also available: {best_kpi.get('kpi_id')}, {second_kpi.get('kpi_id') if second_kpi else ''}."
                ),
                kpi_id=resolved.get("kpi_id"),
                status=resolved.get("status"),
                missing_dependencies=resolved.get("missing_dependencies", []),
                kpi=resolved,
            )
        return KpiMatchDecision(
            matched=False,
            confidence=best_score,
            reason="KPI match ambiguous; using schema fallback.",
        )

    return KpiMatchDecision(
        matched=True,
        confidence=best_score,
        reason="Matched canonical KPI.",
        kpi_id=best_kpi.get("kpi_id"),
        status=best_kpi.get("status"),
        missing_dependencies=best_kpi.get("missing_dependencies", []),
        kpi=best_kpi,
    )
