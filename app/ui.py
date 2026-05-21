import os
import sys
import tomllib
from pathlib import Path
from typing import Any

import altair as alt
import pandas as pd
import streamlit as st
import streamlit.components.v1 as components


sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.catalog_explorer import (  # noqa: E402
    build_architecture_mermaid,
    build_column_details,
    build_join_paths,
    build_kpi_category_counts,
    build_kpi_status_counts,
    build_kpi_summary,
    build_lineage_rows,
    build_mermaid_erd,
    build_metric_summary,
    build_relationships,
    build_table_summary,
    get_csv_profile,
    load_kpis,
    load_metric_docs,
    load_tables,
    sample_csv_rows,
    table_by_name,
)


PROJECT_ROOT = Path(__file__).resolve().parents[1]
LOCAL_TABLES_DIR = PROJECT_ROOT / "data" / "v2" / "tables"


st.set_page_config(
    page_title="ATHL Data Platform",
    layout="wide",
    initial_sidebar_state="expanded",
)


CUSTOM_CSS = """
<style>
    .block-container {
        padding-top: 1.5rem;
        padding-bottom: 3rem;
        max-width: 1440px;
    }
    [data-testid="stMetric"] {
        background: #f8fafc;
        border: 1px solid #e2e8f0;
        border-radius: 8px;
        padding: 0.85rem 1rem;
    }
    [data-testid="stMetricLabel"] {
        color: #334155;
    }
    .section-note {
        color: #475569;
        font-size: 0.95rem;
        line-height: 1.45;
    }
    div[data-testid="stTabs"] button {
        font-weight: 600;
    }
    .exec-shell {
        color: #101820;
    }
    .exec-eyebrow {
        color: #6f4d1f;
        font-size: 0.78rem;
        font-weight: 700;
        letter-spacing: 0;
        text-transform: uppercase;
        margin-bottom: 0.35rem;
    }
    .exec-title {
        font-size: 2.45rem;
        font-weight: 760;
        line-height: 1.04;
        letter-spacing: 0;
        margin: 0 0 0.55rem 0;
        max-width: 920px;
    }
    .exec-copy {
        color: #425466;
        font-size: 1rem;
        line-height: 1.45;
        max-width: 820px;
        margin-bottom: 1.1rem;
    }
    .northstar-band {
        border-left: 4px solid #1f9d8a;
        background: linear-gradient(90deg, rgba(31,157,138,0.10), rgba(244,167,66,0.10));
        padding: 1rem 1.15rem;
        margin: 0.4rem 0 1.15rem 0;
    }
    .northstar-label {
        color: #53606f;
        font-size: 0.82rem;
        font-weight: 700;
        letter-spacing: 0;
        text-transform: uppercase;
    }
    .northstar-value {
        color: #101820;
        font-size: 2.1rem;
        font-weight: 760;
        letter-spacing: 0;
        line-height: 1.05;
        margin-top: 0.2rem;
    }
    .northstar-note {
        color: #4c5b68;
        font-size: 0.88rem;
        margin-top: 0.35rem;
        line-height: 1.35;
    }
    .exec-card {
        min-height: 138px;
        border: 1px solid #d9e1e8;
        border-top: 4px solid var(--accent);
        border-radius: 8px;
        background: #ffffff;
        padding: 0.92rem 0.95rem;
        box-shadow: 0 10px 24px rgba(16,24,32,0.05);
        margin-bottom: 0.8rem;
    }
    .exec-card-label {
        color: #53606f;
        font-size: 0.78rem;
        font-weight: 700;
        letter-spacing: 0;
        text-transform: uppercase;
        min-height: 2rem;
    }
    .exec-card-value {
        color: #101820;
        font-size: 1.55rem;
        font-weight: 760;
        line-height: 1.12;
        letter-spacing: 0;
        margin-top: 0.4rem;
    }
    .exec-card-delta {
        color: var(--delta);
        font-size: 0.84rem;
        font-weight: 700;
        margin-top: 0.45rem;
    }
    .exec-card-helper {
        color: #667789;
        font-size: 0.78rem;
        line-height: 1.28;
        margin-top: 0.35rem;
    }
    .exec-section-title {
        color: #101820;
        font-size: 1.05rem;
        font-weight: 740;
        margin: 1.05rem 0 0.45rem 0;
    }
    .exec-pill {
        display: inline-block;
        border: 1px solid #d7dee6;
        border-radius: 999px;
        padding: 0.22rem 0.58rem;
        margin: 0 0.3rem 0.35rem 0;
        color: #425466;
        background: #fbfcfd;
        font-size: 0.78rem;
        font-weight: 650;
    }
</style>
"""


def _secret_value(key: str, default: str | None = None) -> str | None:
    if os.getenv(key):
        return os.getenv(key)

    try:
        if key in st.secrets:
            return st.secrets.get(key)
        db_env = str(st.secrets.get("DB_ENV", os.getenv("DB_ENV", "local"))).lower()
        section_name = "postgres_neon" if db_env == "prod" else "postgres_local"
        if section_name in st.secrets and key in st.secrets[section_name]:
            return st.secrets[section_name][key]
    except Exception:
        pass

    for path in (
        PROJECT_ROOT / ".streamlit" / "secrets.toml",
        PROJECT_ROOT / "app" / ".streamlit" / "secrets.toml",
        Path.home() / ".streamlit" / "secrets.toml",
    ):
        if not path.exists():
            continue
        try:
            data = tomllib.loads(path.read_text())
        except Exception:
            continue
        if key in data:
            return data[key]
        db_env = str(data.get("DB_ENV", os.getenv("DB_ENV", "local"))).lower()
        section_name = "postgres_neon" if db_env == "prod" else "postgres_local"
        section = data.get(section_name, {})
        if isinstance(section, dict) and key in section:
            return section[key]

    return default


def _apply_secrets_to_env() -> None:
    for key in ("OPENAI_API_KEY", "DB_ENV"):
        value = _secret_value(key)
        if value:
            os.environ[key] = str(value)


@st.cache_data(show_spinner=False)
def _table_summary_df() -> pd.DataFrame:
    return pd.DataFrame(build_table_summary())


@st.cache_data(show_spinner=False)
def _relationships_df() -> pd.DataFrame:
    return pd.DataFrame(build_relationships())


@st.cache_data(show_spinner=False)
def _lineage_df() -> pd.DataFrame:
    return pd.DataFrame(build_lineage_rows())


@st.cache_data(show_spinner=False)
def _metric_summary_df() -> pd.DataFrame:
    return pd.DataFrame(build_metric_summary())


@st.cache_data(show_spinner=False)
def _kpi_summary_df() -> pd.DataFrame:
    return pd.DataFrame(build_kpi_summary())


@st.cache_data(show_spinner=False)
def _load_static_table(table_name: str) -> pd.DataFrame:
    path = LOCAL_TABLES_DIR / f"{table_name}.csv"
    if not path.exists():
        return pd.DataFrame()

    df = pd.read_csv(path)
    for column in df.columns:
        if column.endswith("_at") or column in {"timestamp", "date", "created_at"}:
            df[column] = pd.to_datetime(df[column], errors="coerce")
    return df


def _fmt_compact(value: float | int | None, prefix: str = "", suffix: str = "") -> str:
    if value is None or pd.isna(value):
        return "n/a"

    value = float(value)
    sign = "-" if value < 0 else ""
    abs_value = abs(value)
    if abs_value >= 1_000_000_000:
        body = f"{abs_value / 1_000_000_000:.1f}B"
    elif abs_value >= 1_000_000:
        body = f"{abs_value / 1_000_000:.1f}M"
    elif abs_value >= 1_000:
        body = f"{abs_value / 1_000:.1f}K"
    elif abs_value >= 100:
        body = f"{abs_value:,.0f}"
    elif abs_value >= 10:
        body = f"{abs_value:,.1f}"
    else:
        body = f"{abs_value:,.2f}".rstrip("0").rstrip(".")
    return f"{sign}{prefix}{body}{suffix}"


def _fmt_money(value: float | int | None) -> str:
    return _fmt_compact(value, prefix="$")


def _fmt_pct(value: float | int | None, decimals: int = 1) -> str:
    if value is None or pd.isna(value):
        return "n/a"
    return f"{float(value):.{decimals}f}%"


def _delta_text(current: float | int | None, previous: float | int | None, *, pct_point: bool = False) -> tuple[str, str]:
    if current is None or previous is None or pd.isna(current) or pd.isna(previous):
        return "No comparison", "#667789"

    current = float(current)
    previous = float(previous)
    if pct_point:
        delta = current - previous
        text = f"{delta:+.1f} pp vs prior 30d"
    elif previous == 0:
        text = "New vs prior 30d" if current else "Flat vs prior 30d"
        delta = current
    else:
        delta = (current - previous) / abs(previous) * 100
        text = f"{delta:+.1f}% vs prior 30d"

    color = "#167f70" if delta > 0 else "#b24836" if delta < 0 else "#667789"
    return text, color


def _render_exec_card(label: str, value: str, delta: str, helper: str, accent: str, delta_color: str) -> str:
    return f"""
    <div class="exec-card" style="--accent: {accent}; --delta: {delta_color};">
        <div class="exec-card-label">{label}</div>
        <div class="exec-card-value">{value}</div>
        <div class="exec-card-delta">{delta}</div>
        <div class="exec-card-helper">{helper}</div>
    </div>
    """


@st.cache_data(show_spinner=False)
def _executive_dashboard_data() -> dict[str, Any]:
    transactions = _load_static_table("transactions")
    tokens = _load_static_table("tokens")
    users = _load_static_table("users")
    issuers = _load_static_table("issuers")
    issuer_daily_revenue = _load_static_table("issuer_daily_revenue")
    user_wallet = _load_static_table("user_wallet")
    user_token_wallet = _load_static_table("user_token_wallet")
    identity = _load_static_table("identity_verification")
    social = _load_static_table("social_verification")

    for frame, columns in (
        (transactions, ["quantity", "total_amount_usdc"]),
        (tokens, ["initial_supply", "current_supply_minted", "total_sold", "total_revenue", "current_price"]),
        (users, ["email_verification_score"]),
        (issuer_daily_revenue, ["total_amount_usdc"]),
        (user_wallet, ["eth_balance", "usdc_balance", "total_token_value"]),
        (user_token_wallet, ["quantity", "total_value"]),
        (identity, ["alias_confidence"]),
        (social, ["followers_count", "attempts"]),
    ):
        for column in columns:
            if column in frame.columns:
                frame[column] = pd.to_numeric(frame[column], errors="coerce").fillna(0)

    completed_tx = transactions[
        transactions.get("status", pd.Series(dtype=str)).astype(str).str.lower().eq("completed")
    ].copy()
    completed_tx["timestamp"] = pd.to_datetime(completed_tx["timestamp"], errors="coerce")
    completed_tx = completed_tx.dropna(subset=["timestamp"])

    latest_date = completed_tx["timestamp"].max().normalize() if not completed_tx.empty else pd.Timestamp.today().normalize()
    period_start = latest_date - pd.Timedelta(days=29)
    previous_start = period_start - pd.Timedelta(days=30)
    current_tx = completed_tx[(completed_tx["timestamp"] >= period_start) & (completed_tx["timestamp"] <= latest_date + pd.Timedelta(days=1))]
    previous_tx = completed_tx[(completed_tx["timestamp"] >= previous_start) & (completed_tx["timestamp"] < period_start)]

    token_lookup = tokens[["token_id", "issuer_id", "token_symbol", "initial_supply", "current_price", "total_revenue"]].copy()
    current_tx_tokens = current_tx.merge(token_lookup, on="token_id", how="left")
    previous_tx_tokens = previous_tx.merge(token_lookup, on="token_id", how="left")
    completed_tx_tokens = completed_tx.merge(token_lookup, on="token_id", how="left")

    users["created_at"] = pd.to_datetime(users.get("created_at"), errors="coerce")
    issuers["created_at"] = pd.to_datetime(issuers.get("created_at"), errors="coerce")

    current_users = users[(users["created_at"] >= period_start) & (users["created_at"] <= latest_date + pd.Timedelta(days=1))]
    previous_users = users[(users["created_at"] >= previous_start) & (users["created_at"] < period_start)]

    completed_statuses = {"PASSED", "FAILED", "MANUAL_REVIEW", "REJECTED"}
    identity_status = identity.get("status", pd.Series(dtype=str)).astype(str).str.upper()
    completed_identity = identity[identity_status.isin(completed_statuses)]
    verification_pass_rate = (identity_status.eq("PASSED").sum() / len(completed_identity) * 100) if len(completed_identity) else 0

    def active_traders(frame: pd.DataFrame) -> int:
        if frame.empty:
            return 0
        ids = pd.concat([frame["buyer_id"], frame["seller_id"].dropna()]).dropna().astype(str)
        return ids.nunique()

    def repeat_buyer_rate(frame: pd.DataFrame) -> float:
        if frame.empty:
            return 0
        buyer_counts = frame.groupby("buyer_id")["transaction_id"].count()
        return float((buyer_counts > 1).sum() / len(buyer_counts) * 100) if len(buyer_counts) else 0

    total_holding_quantity = float(user_token_wallet.get("quantity", pd.Series(dtype=float)).sum())
    current_velocity = float(current_tx.get("quantity", pd.Series(dtype=float)).sum() / total_holding_quantity * 100) if total_holding_quantity else 0
    previous_velocity = float(previous_tx.get("quantity", pd.Series(dtype=float)).sum() / total_holding_quantity * 100) if total_holding_quantity else 0

    funded_wallets = 0
    if not user_wallet.empty:
        funded_wallets = int(((user_wallet["usdc_balance"] > 0) | (user_wallet["eth_balance"] > 0)).sum())
    wallet_funding_rate = funded_wallets / max(len(users), 1) * 100

    suspended_mask = users.get("account_status", pd.Series(dtype=str)).astype(str).str.upper().isin(
        {"SUSPENDED", "LOCKED", "DISABLED"}
    )
    suspended_accounts = int(suspended_mask.sum())

    top10_current = current_tx_tokens.groupby(["token_id", "token_symbol"], dropna=False)["total_amount_usdc"].sum().reset_index()
    top10_current = top10_current.sort_values("total_amount_usdc", ascending=False)
    current_total_volume = float(current_tx["total_amount_usdc"].sum())
    previous_total_volume = float(previous_tx["total_amount_usdc"].sum())
    current_concentration = float(top10_current.head(10)["total_amount_usdc"].sum() / current_total_volume * 100) if current_total_volume else 0

    previous_top10 = previous_tx_tokens.groupby(["token_id", "token_symbol"], dropna=False)["total_amount_usdc"].sum().reset_index()
    previous_top10 = previous_top10.sort_values("total_amount_usdc", ascending=False)
    previous_total_volume = float(previous_tx["total_amount_usdc"].sum())
    previous_concentration = float(previous_top10.head(10)["total_amount_usdc"].sum() / previous_total_volume * 100) if previous_total_volume else 0

    daily = (
        completed_tx.assign(date=completed_tx["timestamp"].dt.date)
        .groupby("date", as_index=False)
        .agg(transactions=("transaction_id", "count"), volume=("total_amount_usdc", "sum"))
    )
    daily["date"] = pd.to_datetime(daily["date"])
    daily_recent = daily[daily["date"] >= latest_date - pd.Timedelta(days=89)]

    monthly = (
        completed_tx.assign(month=completed_tx["timestamp"].dt.to_period("M").dt.to_timestamp())
        .groupby("month", as_index=False)
        .agg(gtv=("total_amount_usdc", "sum"), transactions=("transaction_id", "count"), buyers=("buyer_id", "nunique"))
    )

    user_growth = (
        users.dropna(subset=["created_at"])
        .assign(month=users["created_at"].dt.to_period("M").dt.to_timestamp())
        .groupby("month", as_index=False)
        .agg(new_users=("user_id", "nunique"))
    )
    growth_monthly = monthly[["month", "buyers"]].merge(user_growth, on="month", how="outer").sort_values("month").fillna(0)

    top_tokens = top10_current.head(10).copy()
    top_tokens["token_symbol"] = top_tokens["token_symbol"].fillna(top_tokens["token_id"].astype(str))

    issuer_revenue_trend = issuer_daily_revenue.copy()
    if not issuer_revenue_trend.empty:
        issuer_revenue_trend["date"] = pd.to_datetime(issuer_revenue_trend["date"], errors="coerce")
        issuer_revenue_trend = (
            issuer_revenue_trend.dropna(subset=["date"])
            .groupby("date", as_index=False)["total_amount_usdc"]
            .sum()
            .sort_values("date")
        )
        issuer_revenue_trend = issuer_revenue_trend[issuer_revenue_trend["date"] >= issuer_revenue_trend["date"].max() - pd.Timedelta(days=89)]

    issuer_mix = issuers.groupby("issuer_type", dropna=False).size().reset_index(name="issuers")
    issuer_mix["issuer_type"] = issuer_mix["issuer_type"].fillna("UNKNOWN")

    raise_progress = pd.DataFrame()
    preferences = _load_static_table("issuer_preferences")
    if not preferences.empty and not completed_tx_tokens.empty:
        issuer_revenue = completed_tx_tokens.groupby("issuer_id", as_index=False)["total_amount_usdc"].sum()
        raise_progress = issuer_revenue.merge(preferences[["issuer_id", "raise_target_usd"]], on="issuer_id", how="left")
        raise_progress["raise_target_usd"] = pd.to_numeric(raise_progress["raise_target_usd"], errors="coerce")
        raise_progress["pct_to_target"] = raise_progress["total_amount_usdc"] / raise_progress["raise_target_usd"].replace(0, pd.NA) * 100
        raise_progress = raise_progress.replace([float("inf"), -float("inf")], pd.NA).dropna(subset=["pct_to_target"])

    verification_status = identity_status.value_counts().rename_axis("status").reset_index(name="checks")

    social_status = social.get("status", pd.Series(dtype=str)).astype(str).str.upper().value_counts().rename_axis("status").reset_index(name="checks")

    card_specs = [
        {
            "label": "Gross Transaction Volume",
            "value": _fmt_money(current_total_volume),
            "delta": _delta_text(current_total_volume, previous_total_volume),
            "helper": "Completed transaction volume, latest 30 days.",
            "accent": "#1f9d8a",
        },
        {
            "label": "Monthly Active Traders",
            "value": _fmt_compact(active_traders(current_tx)),
            "delta": _delta_text(active_traders(current_tx), active_traders(previous_tx)),
            "helper": "Distinct buyers and sellers, latest 30 days.",
            "accent": "#315f8a",
        },
        {
            "label": "Total Token Revenue",
            "value": _fmt_money(tokens.get("total_revenue", pd.Series(dtype=float)).sum()),
            "delta": _delta_text(current_total_volume, previous_total_volume),
            "helper": "Cumulative token revenue in current token table.",
            "accent": "#b5792a",
        },
        {
            "label": "Active Tokens",
            "value": _fmt_compact(current_tx["token_id"].nunique()),
            "delta": _delta_text(current_tx["token_id"].nunique(), previous_tx["token_id"].nunique()),
            "helper": "Tokens with completed trading in the latest 30 days.",
            "accent": "#5e6ad2",
        },
        {
            "label": "Net New Users",
            "value": _fmt_compact(current_users["user_id"].nunique()),
            "delta": _delta_text(current_users["user_id"].nunique(), previous_users["user_id"].nunique()),
            "helper": "User signups, latest 30 days.",
            "accent": "#cc6b49",
        },
        {
            "label": "Active Issuers",
            "value": _fmt_compact(current_tx_tokens["issuer_id"].nunique()),
            "delta": _delta_text(current_tx_tokens["issuer_id"].nunique(), previous_tx_tokens["issuer_id"].nunique()),
            "helper": "Issuers with traded tokens in the latest 30 days.",
            "accent": "#248f5f",
        },
        {
            "label": "Verification Pass Rate",
            "value": _fmt_pct(verification_pass_rate),
            "delta": ("Current static table", "#667789"),
            "helper": "Passed identity checks over completed identity checks.",
            "accent": "#6f4d1f",
        },
        {
            "label": "Daily Transactions",
            "value": _fmt_compact(len(current_tx) / 30),
            "delta": _delta_text(len(current_tx) / 30, len(previous_tx) / 30),
            "helper": "Average completed transactions per day, latest 30 days.",
            "accent": "#2d7f9f",
        },
        {
            "label": "Repeat Buyer Rate",
            "value": _fmt_pct(repeat_buyer_rate(current_tx)),
            "delta": _delta_text(repeat_buyer_rate(current_tx), repeat_buyer_rate(previous_tx), pct_point=True),
            "helper": "Buyers with more than one completed transaction.",
            "accent": "#9b6bb3",
        },
        {
            "label": "Token Liquidity Velocity",
            "value": _fmt_pct(current_velocity),
            "delta": _delta_text(current_velocity, previous_velocity, pct_point=True),
            "helper": "Latest-30-day traded quantity as share of held supply.",
            "accent": "#2e8c7d",
        },
        {
            "label": "Wallet Funding Rate",
            "value": _fmt_pct(wallet_funding_rate),
            "delta": ("Static wallet snapshot", "#667789"),
            "helper": "Funded wallets divided by total users.",
            "accent": "#ba7a2b",
        },
        {
            "label": "Revenue Concentration",
            "value": _fmt_pct(current_concentration),
            "delta": _delta_text(current_concentration, previous_concentration, pct_point=True),
            "helper": "Top 10 tokens share of latest-30-day GTV.",
            "accent": "#7b5ea7",
        },
        {
            "label": "Suspended Accounts",
            "value": _fmt_compact(suspended_accounts),
            "delta": ("Current user table", "#667789"),
            "helper": "Suspended, locked, or disabled user accounts.",
            "accent": "#b24836",
        },
    ]

    return {
        "latest_date": latest_date,
        "period_start": period_start,
        "north_star_value": current_total_volume,
        "north_star_delta": _delta_text(current_total_volume, previous_total_volume),
        "cards": card_specs,
        "daily_recent": daily_recent,
        "monthly": monthly,
        "growth_monthly": growth_monthly,
        "top_tokens": top_tokens,
        "issuer_revenue_trend": issuer_revenue_trend,
        "issuer_mix": issuer_mix,
        "raise_progress": raise_progress,
        "verification_status": verification_status,
        "social_status": social_status,
        "completed_tx_count": len(completed_tx),
        "source_rows": {
            "transactions": len(transactions),
            "tokens": len(tokens),
            "users": len(users),
            "issuers": len(issuers),
            "issuer_daily_revenue": len(issuer_daily_revenue),
            "user_wallet": len(user_wallet),
            "user_token_wallet": len(user_token_wallet),
            "identity_verification": len(identity),
            "social_verification": len(social),
        },
    }


def _render_mermaid(source: str, height: int = 520) -> None:
    html = f"""
    <div class="mermaid">{source}</div>
    <script type="module">
      import mermaid from 'https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.esm.min.mjs';
      mermaid.initialize({{ startOnLoad: true, securityLevel: 'loose', theme: 'base' }});
    </script>
    """
    components.html(html, height=height, scrolling=True)


def _rows_to_dataframe(rows: Any) -> pd.DataFrame:
    if isinstance(rows, list):
        return pd.DataFrame(rows)
    return pd.DataFrame()


def _render_auto_chart(df: pd.DataFrame) -> None:
    if df.empty:
        return

    numeric_cols = list(df.select_dtypes(include="number").columns)
    date_candidates = []
    for column in df.columns:
        if "date" in column.lower() or "time" in column.lower() or column.endswith("_at"):
            parsed = pd.to_datetime(df[column], errors="coerce")
            if parsed.notna().any():
                date_candidates.append(column)

    if date_candidates and numeric_cols:
        chart_df = df.copy()
        x_col = date_candidates[0]
        y_col = numeric_cols[0]
        chart_df[x_col] = pd.to_datetime(chart_df[x_col], errors="coerce")
        chart = (
            alt.Chart(chart_df.dropna(subset=[x_col]))
            .mark_line(point=True)
            .encode(x=alt.X(x_col, title=x_col), y=alt.Y(y_col, title=y_col), tooltip=list(df.columns))
            .properties(height=320)
        )
        st.altair_chart(chart)
        return

    category_cols = [col for col in df.columns if col not in numeric_cols]
    if category_cols and numeric_cols:
        x_col = category_cols[0]
        y_col = numeric_cols[0]
        chart = (
            alt.Chart(df.head(50))
            .mark_bar()
            .encode(
                x=alt.X(x_col, sort="-y", title=x_col),
                y=alt.Y(y_col, title=y_col),
                tooltip=list(df.columns),
            )
            .properties(height=320)
        )
        st.altair_chart(chart)


def _has_ai_config() -> bool:
    return bool(_secret_value("OPENAI_API_KEY"))


def _run_nl_query(question: str) -> dict[str, Any]:
    _apply_secrets_to_env()

    from app.db.query_runner import PostgresClient
    from app.db.validator import enforce_limit, validate_sql
    from app.llm.explain_results import explain_results
    from app.llm.generate_sql import fix_sql, generate_sql
    from app.rag.context_service import get_retrieval_context
    from app.rag.ingest import run_ingest

    run_ingest()
    retrieval_ctx = get_retrieval_context(question)
    context = retrieval_ctx.text
    sql = generate_sql(question, context)

    if not validate_sql(sql):
        return {
            "question": question,
            "sql": sql,
            "rows": [],
            "error": "Generated SQL did not pass the SELECT-only validator.",
            "context": context,
        }

    sql = enforce_limit(sql, limit=100)
    client = PostgresClient()
    result = client.run_query(sql)

    if isinstance(result, dict) and "error" in result:
        fixed_sql = fix_sql(question, sql, result["error"], context)
        if validate_sql(fixed_sql):
            fixed_sql = enforce_limit(fixed_sql, limit=100)
            result = client.run_query(fixed_sql)
            sql = fixed_sql

    if isinstance(result, dict) and "error" in result:
        return {
            "question": question,
            "sql": sql,
            "rows": [],
            "error": result["error"],
            "context": context,
        }

    rows = [dict(row) for row in result]
    explanation = explain_results(question, sql, rows[:50]) if rows else "The query returned no rows."
    return {
        "question": question,
        "sql": sql,
        "rows": rows,
        "error": None,
        "context": context,
        "explanation": explanation,
    }


def _render_header() -> None:
    tables = load_tables()
    metrics = load_metric_docs()
    kpis = load_kpis()
    active_kpis = [kpi for kpi in kpis if kpi.get("status") == "active"]
    blocked_kpis = [kpi for kpi in kpis if kpi.get("status") == "blocked_by_missing_data"]
    row_total = int(_table_summary_df()["csv_rows"].fillna(0).sum())

    st.markdown(CUSTOM_CSS, unsafe_allow_html=True)
    st.title("ATHL Data Platform")
    st.caption("Schema documentation, lineage, metric definitions, onboarding guide, and AI-assisted analytics.")

    left, mid, right, last = st.columns(4)
    left.metric("Tables", len(tables))
    mid.metric("Documented metrics", len(metrics))
    right.metric("Canonical KPIs", len(kpis), f"{len(active_kpis)} active")
    last.metric("Local CSV rows", f"{row_total:,}", f"{len(blocked_kpis)} blocked KPIs")


def render_executive_dashboard() -> None:
    data = _executive_dashboard_data()
    north_delta, north_delta_color = data["north_star_delta"]
    period_start = data["period_start"].strftime("%b %-d, %Y")
    latest_date = data["latest_date"].strftime("%b %-d, %Y")

    st.markdown(
        f"""
        <div class="exec-shell">
            <div class="exec-eyebrow">North Star Executive Dashboard</div>
            <div class="exec-title">ATHL marketplace health, issuer momentum, and trust in one CEO view.</div>
            <div class="exec-copy">
                Built from the current static CSV layer and the Phase 1 MVP KPI list. The operating window is
                latest 30 days in the dummy dataset: <b>{period_start}</b> to <b>{latest_date}</b>.
            </div>
        </div>
        <div class="northstar-band">
            <div class="northstar-label">North Star Metric: Token Economic Activity</div>
            <div class="northstar-value">{_fmt_money(data["north_star_value"])}</div>
            <div class="northstar-note" style="color: {north_delta_color}; font-weight: 700;">{north_delta}</div>
            <div class="northstar-note">
                Completed USDC transaction volume generated by active users across ATHL tokens. This is the best current
                proxy for network health until product-event tracking and a platform revenue ledger are available.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    cards = data["cards"]
    for start in range(0, len(cards), 4):
        columns = st.columns(4)
        for column, card in zip(columns, cards[start : start + 4]):
            delta, delta_color = card["delta"]
            column.markdown(
                _render_exec_card(
                    card["label"],
                    card["value"],
                    delta,
                    card["helper"],
                    card["accent"],
                    delta_color,
                ),
                unsafe_allow_html=True,
            )

    st.markdown('<div class="exec-section-title">Marketplace Momentum</div>', unsafe_allow_html=True)
    left, right = st.columns([1.25, 1])
    with left:
        monthly = data["monthly"].copy()
        latest_month = data["latest_date"].to_period("M").to_timestamp()
        if data["latest_date"].day < 20:
            monthly = monthly[monthly["month"] < latest_month]
        if not monthly.empty:
            chart = (
                alt.Chart(monthly)
                .mark_area(line={"color": "#1f9d8a"}, color=alt.Gradient(
                    gradient="linear",
                    stops=[
                        alt.GradientStop(color="rgba(31,157,138,0.32)", offset=0),
                        alt.GradientStop(color="rgba(31,157,138,0.04)", offset=1),
                    ],
                    x1=1,
                    x2=1,
                    y1=1,
                    y2=0,
                ))
                .encode(
                    x=alt.X("month:T", title=None),
                    y=alt.Y("gtv:Q", title="GTV (USDC)"),
                    tooltip=[
                        alt.Tooltip("month:T", title="Month", format="%b %Y"),
                        alt.Tooltip("gtv:Q", title="GTV", format="$,.0f"),
                        alt.Tooltip("transactions:Q", title="Transactions", format=","),
                        alt.Tooltip("buyers:Q", title="Buyers", format=","),
                    ],
                )
                .properties(height=330)
            )
            st.altair_chart(chart, use_container_width=True)
    with right:
        top_tokens = data["top_tokens"].copy()
        if not top_tokens.empty:
            chart = (
                alt.Chart(top_tokens)
                .mark_bar(cornerRadiusTopRight=3, cornerRadiusBottomRight=3, color="#315f8a")
                .encode(
                    y=alt.Y("token_symbol:N", sort="-x", title=None),
                    x=alt.X("total_amount_usdc:Q", title="30d volume"),
                    tooltip=[
                        alt.Tooltip("token_symbol:N", title="Token"),
                        alt.Tooltip("total_amount_usdc:Q", title="Volume", format="$,.0f"),
                    ],
                )
                .properties(height=330)
            )
            st.altair_chart(chart, use_container_width=True)

    st.markdown('<div class="exec-section-title">Growth Engine and Issuer Ecosystem</div>', unsafe_allow_html=True)
    growth_col, issuer_col = st.columns([1, 1])
    with growth_col:
        growth_monthly = data["growth_monthly"].copy()
        if data["latest_date"].day < 20:
            growth_monthly = growth_monthly[growth_monthly["month"] < latest_month]
        if not growth_monthly.empty:
            growth_long = growth_monthly.melt(
                id_vars=["month"],
                value_vars=["new_users", "buyers"],
                var_name="metric",
                value_name="users",
            )
            growth_long["metric"] = growth_long["metric"].replace({"new_users": "New users", "buyers": "Active buyers"})
            chart = (
                alt.Chart(growth_long)
                .mark_line(point=True)
                .encode(
                    x=alt.X("month:T", title=None),
                    y=alt.Y("users:Q", title="Users"),
                    color=alt.Color("metric:N", scale=alt.Scale(range=["#cc6b49", "#1f9d8a"]), title=None),
                    tooltip=[
                        alt.Tooltip("month:T", title="Month", format="%b %Y"),
                        alt.Tooltip("metric:N", title="Metric"),
                        alt.Tooltip("users:Q", title="Users", format=","),
                    ],
                )
                .properties(height=300)
            )
            st.altair_chart(chart, use_container_width=True)
    with issuer_col:
        issuer_mix = data["issuer_mix"].copy()
        if not issuer_mix.empty:
            chart = (
                alt.Chart(issuer_mix)
                .mark_bar(cornerRadiusTopRight=3, cornerRadiusTopLeft=3)
                .encode(
                    x=alt.X("issuer_type:N", title=None),
                    y=alt.Y("issuers:Q", title="Issuers"),
                    color=alt.Color("issuer_type:N", scale=alt.Scale(range=["#5e6ad2", "#b5792a", "#1f9d8a"]), legend=None),
                    tooltip=["issuer_type:N", alt.Tooltip("issuers:Q", format=",")],
                )
                .properties(height=300)
            )
            st.altair_chart(chart, use_container_width=True)

    finance_col, trust_col = st.columns([1.15, 0.85])
    with finance_col:
        st.markdown('<div class="exec-section-title">Issuer Revenue Trend</div>', unsafe_allow_html=True)
        issuer_revenue = data["issuer_revenue_trend"].copy()
        if not issuer_revenue.empty:
            chart = (
                alt.Chart(issuer_revenue)
                .mark_line(color="#b5792a")
                .encode(
                    x=alt.X("date:T", title=None),
                    y=alt.Y("total_amount_usdc:Q", title="Issuer revenue"),
                    tooltip=[
                        alt.Tooltip("date:T", title="Date", format="%b %-d, %Y"),
                        alt.Tooltip("total_amount_usdc:Q", title="Revenue", format="$,.0f"),
                    ],
                )
                .properties(height=300)
            )
            st.altair_chart(chart, use_container_width=True)
    with trust_col:
        st.markdown('<div class="exec-section-title">Trust and Risk</div>', unsafe_allow_html=True)
        verification_status = data["verification_status"].copy()
        if not verification_status.empty:
            chart = (
                alt.Chart(verification_status)
                .mark_arc(innerRadius=56, outerRadius=104)
                .encode(
                    theta=alt.Theta("checks:Q"),
                    color=alt.Color(
                        "status:N",
                        scale=alt.Scale(range=["#1f9d8a", "#cc6b49", "#b5792a", "#7b5ea7"]),
                        title=None,
                    ),
                    tooltip=["status:N", alt.Tooltip("checks:Q", format=",")],
                )
                .properties(height=300)
            )
            st.altair_chart(chart, use_container_width=True)

    st.markdown('<div class="exec-section-title">Current Data Coverage</div>', unsafe_allow_html=True)
    coverage_cols = st.columns([0.65, 0.35])
    with coverage_cols[0]:
        st.markdown(
            """
            <span class="exec-pill">Liquidity</span>
            <span class="exec-pill">Marketplace activity</span>
            <span class="exec-pill">Issuer ecosystem</span>
            <span class="exec-pill">Trust/compliance</span>
            <span class="exec-pill">Early engagement</span>
            """,
            unsafe_allow_html=True,
        )
        st.markdown(
            '<p class="section-note">Excluded from this executive view: SaaS-style retention, margin, support operations, and forecasting metrics. Those require product-event tracking, platform revenue ledger, treasury, order-book, and community engagement systems that are not present in the current static data.</p>',
            unsafe_allow_html=True,
        )
    with coverage_cols[1]:
        source_df = pd.DataFrame(
            [{"table": table, "rows": rows} for table, rows in data["source_rows"].items()]
        )
        st.dataframe(source_df, width="stretch", hide_index=True)


def render_overview() -> None:
    st.subheader("Data Overview")
    st.markdown(
        '<p class="section-note">This page is generated from the runtime schema docs, KPI catalog, and local CSV files. It is intended to be the first stop for anyone trying to understand what data exists and what analytics are supported.</p>',
        unsafe_allow_html=True,
    )

    summary = _table_summary_df()
    taxonomy_counts = summary["classification"].fillna("unknown").replace("", "unknown").value_counts()
    csv_rows = summary[["table", "classification", "columns", "csv_rows", "time_columns"]].copy()

    col1, col2 = st.columns([1, 1])
    with col1:
        st.markdown("**Table Roles**")
        st.dataframe(
            taxonomy_counts.rename_axis("classification").reset_index(name="tables"),
            width="stretch",
            hide_index=True,
        )
    with col2:
        st.markdown("**CSV Inventory**")
        st.dataframe(csv_rows, width="stretch", hide_index=True)

    st.markdown("**Architecture Flow**")
    _render_mermaid(build_architecture_mermaid(), height=420)
    with st.expander("Mermaid source"):
        st.code(build_architecture_mermaid(), language="mermaid")


def render_schema_explorer() -> None:
    st.subheader("Auto-Generated Schema Explorer")
    summary = _table_summary_df()

    search = st.text_input("Search tables, columns, or descriptions", key="schema_search")
    filtered = summary.copy()
    if search:
        query = search.lower()
        matching_tables = []
        for table in load_tables():
            haystack = " ".join(
                [
                    table.get("table", ""),
                    table.get("description", ""),
                    " ".join(column.get("name", "") for column in table.get("columns", [])),
                    " ".join(column.get("comment", "") for column in table.get("columns", [])),
                ]
            ).lower()
            if query in haystack:
                matching_tables.append(table["table"])
        filtered = summary[summary["table"].isin(matching_tables)]

    st.dataframe(filtered, width="stretch", hide_index=True)

    table_names = list(summary["table"])
    default_index = table_names.index(filtered.iloc[0]["table"]) if not filtered.empty else 0
    selected_table = st.selectbox("Inspect table", table_names, index=default_index)
    table = table_by_name()[selected_table]

    top_left, top_mid, top_right = st.columns(3)
    top_left.metric("Columns", len(table.get("columns", [])))
    top_mid.metric("Foreign keys", len(table.get("foreign_keys", [])))
    top_right.metric("CSV rows", get_csv_profile(selected_table).get("row_count") or 0)

    st.markdown(f"**{selected_table}**")
    st.write(table.get("description", ""))
    st.dataframe(pd.DataFrame(build_column_details(selected_table)), width="stretch", hide_index=True)

    join_paths = build_join_paths().get(selected_table, [])
    if join_paths:
        st.markdown("**Join Paths**")
        for join in join_paths:
            st.code(join, language="sql")

    samples = sample_csv_rows(selected_table, limit=20)
    if samples:
        with st.expander("Local CSV sample rows", expanded=False):
            st.dataframe(pd.DataFrame(samples), width="stretch", hide_index=True)


def render_lineage() -> None:
    st.subheader("ERD and Lineage")
    diagram_mode = st.segmented_control("Diagram", ["ERD", "Architecture"], default="ERD")
    source = build_mermaid_erd() if diagram_mode == "ERD" else build_architecture_mermaid()
    _render_mermaid(source, height=650)

    with st.expander("Mermaid source"):
        st.code(source, language="mermaid")

    left, right = st.columns([1, 1])
    with left:
        st.markdown("**Foreign Key Relationships**")
        st.dataframe(_relationships_df(), width="stretch", hide_index=True)
    with right:
        st.markdown("**Table, Metric, and KPI Lineage**")
        lineage = _lineage_df()
        lineage_type = st.multiselect(
            "Lineage type",
            sorted(lineage["lineage_type"].unique()),
            default=sorted(lineage["lineage_type"].unique()),
        )
        st.dataframe(lineage[lineage["lineage_type"].isin(lineage_type)], width="stretch", hide_index=True)


def render_metrics() -> None:
    st.subheader("Metric Definitions and KPI Catalog")
    kpi_status_counts = build_kpi_status_counts()
    kpi_category_counts = build_kpi_category_counts()

    status_cols = st.columns(max(1, len(kpi_status_counts)))
    for column, (status, count) in zip(status_cols, sorted(kpi_status_counts.items())):
        column.metric(status.replace("_", " ").title(), count)

    st.markdown("**KPI Categories**")
    category_df = pd.DataFrame(
        [{"category": key, "kpis": value} for key, value in sorted(kpi_category_counts.items())]
    )
    if not category_df.empty:
        chart = alt.Chart(category_df).mark_bar().encode(x=alt.X("category", sort="-y"), y="kpis", tooltip=["category", "kpis"])
        st.altair_chart(chart.properties(height=260))

    metric_query = st.text_input("Search metrics and KPIs", key="metric_search")
    metric_df = _metric_summary_df()
    kpi_df = _kpi_summary_df()
    if metric_query:
        needle = metric_query.lower()
        metric_df = metric_df[metric_df.apply(lambda row: needle in " ".join(map(str, row.values)).lower(), axis=1)]
        kpi_df = kpi_df[kpi_df.apply(lambda row: needle in " ".join(map(str, row.values)).lower(), axis=1)]

    metric_tab, kpi_tab = st.tabs(["Schema Metrics", "Canonical KPIs"])
    with metric_tab:
        st.dataframe(metric_df, width="stretch", hide_index=True)
    with kpi_tab:
        status_filter = st.multiselect(
            "Status",
            sorted(_kpi_summary_df()["status"].unique()),
            default=sorted(_kpi_summary_df()["status"].unique()),
        )
        st.dataframe(kpi_df[kpi_df["status"].isin(status_filter)], width="stretch", hide_index=True)


def render_chat() -> None:
    st.subheader("Ask the Data")
    st.markdown(
        '<p class="section-note">The chat path uses schema retrieval, KPI matching, SQL generation, SELECT-only validation, PostgreSQL execution, and an explanation step. The rest of the documentation app works without AI or database secrets.</p>',
        unsafe_allow_html=True,
    )

    ai_ready = _has_ai_config()
    if not ai_ready:
        st.warning("Add `OPENAI_API_KEY` in Streamlit secrets to enable AI query generation.")

    with st.expander("Suggested questions", expanded=not ai_ready):
        examples = [
            "What is total platform revenue by month?",
            "Which tokens have the highest number of buyers?",
            "What is the identity verification pass rate this month?",
            "Show issuer daily revenue by issuer for the latest 30 days.",
            "What KPIs are blocked because required data is missing?",
        ]
        for example in examples:
            st.code(example)

    if "chat_results" not in st.session_state:
        st.session_state.chat_results = []

    for item in st.session_state.chat_results:
        with st.chat_message("user"):
            st.write(item["question"])
        with st.chat_message("assistant"):
            if item.get("error"):
                st.error(item["error"])
            else:
                st.write(item.get("explanation", "Query completed."))
            st.code(item.get("sql", ""), language="sql")
            df = _rows_to_dataframe(item.get("rows", []))
            if not df.empty:
                st.dataframe(df, width="stretch", hide_index=True)
                _render_auto_chart(df)
            with st.expander("Retrieved context"):
                st.text(item.get("context", ""))

    prompt = st.chat_input("Ask a question about ATHL data", disabled=not ai_ready)
    if prompt:
        with st.chat_message("user"):
            st.write(prompt)
        with st.chat_message("assistant"):
            with st.spinner("Retrieving schema context, generating SQL, and querying the database..."):
                try:
                    result = _run_nl_query(prompt)
                except Exception as exc:
                    result = {
                        "question": prompt,
                        "sql": "",
                        "rows": [],
                        "error": str(exc),
                        "context": "",
                    }
                st.session_state.chat_results.append(result)
            st.rerun()


def render_onboarding() -> None:
    st.subheader("Onboarding and Streamlit Cloud Guide")

    st.markdown(
        """
**What this app shows**

1. Schema docs generated from `app/rag/catalog/schema_docs/v2_schema_docs.json`.
2. Table lineage from declared foreign keys and metric dependencies.
3. Metric and KPI definitions from `app/rag/catalog/kpi_catalog.json`.
4. Optional AI chat over PostgreSQL when OpenAI and database secrets are configured.

**Streamlit Community Cloud settings**

- Entrypoint: `app/ui.py`
- Python version: `3.11` from `runtime.txt`
- Dependencies: `requirements.txt`
- Required AI secret: `OPENAI_API_KEY`
- Recommended environment secret: `DB_ENV = "prod"`

**Database secrets**

Paste this structure into Streamlit secrets and replace the values:

```toml
OPENAI_API_KEY = "sk-..."
DB_ENV = "prod"

[postgres_neon]
host = "your-neon-host.neon.tech"
port = 5432
database = "your_database"
user = "your_user"
password = "your_password"
```

**How to onboard a new analyst**

1. Start in `Data Overview` to see table roles and available row counts.
2. Use `Schema Explorer` to inspect columns, keys, suggested values, and sample CSV rows.
3. Use `ERD and Lineage` before writing multi-table SQL.
4. Use `Metric Definitions` to confirm formulas and blocked KPI dependencies.
5. Use `Ask the Data` for natural-language exploration, then inspect the generated SQL before trusting the answer.
        """
    )

    st.markdown("**Local run**")
    st.code("pip install -r requirements.txt\nstreamlit run app/ui.py", language="bash")


def main() -> None:
    _apply_secrets_to_env()
    _render_header()

    with st.sidebar:
        st.markdown("**ATHL Data Platform**")
        page = st.radio(
            "Navigation",
            [
                "Executive Dashboard",
                "Data Overview",
                "Schema Explorer",
                "ERD and Lineage",
                "Metric Definitions",
                "Ask the Data",
                "Onboarding Guide",
            ],
        )
        st.divider()
        st.write("Runtime status")
        st.write(f"AI configured: {'yes' if _has_ai_config() else 'no'}")
        st.write(f"DB_ENV: `{os.getenv('DB_ENV', 'local')}`")

    if page == "Executive Dashboard":
        render_executive_dashboard()
    elif page == "Data Overview":
        render_overview()
    elif page == "Schema Explorer":
        render_schema_explorer()
    elif page == "ERD and Lineage":
        render_lineage()
    elif page == "Metric Definitions":
        render_metrics()
    elif page == "Ask the Data":
        render_chat()
    elif page == "Onboarding Guide":
        render_onboarding()


if __name__ == "__main__":
    main()
