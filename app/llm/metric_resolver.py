from dataclasses import dataclass
from typing import Optional


@dataclass
class MetricResolution:
    matched: bool
    metric_name: Optional[str] = None
    sql_expression: Optional[str] = None
    reason: str = ""
    disambiguation_note: str = ""

    def to_prompt_block(self) -> str:
        if not self.matched:
            return ""
        return (
            "Metric Resolution:\n"
            f"- metric_name: {self.metric_name}\n"
            f"- sql_expression: {self.sql_expression}\n"
            f"- reason: {self.reason}\n"
            f"- disambiguation_note: {self.disambiguation_note or 'none'}\n"
            "- instruction: Use this metric definition exactly for aggregates unless the user explicitly overrides it."
        )


def _normalize(text: str) -> str:
    return " ".join(text.lower().split())


def resolve_metric(question: str) -> MetricResolution:
    """
    Resolve ambiguous business metric terms into deterministic SQL expressions.
    """
    q = _normalize(question)

    token_units_markers = {
        "tokens traded",
        "token traded",
        "how many tokens",
        "number of tokens",
        "token quantity",
        "tokens were traded",
    }
    trade_count_markers = {
        "how many trades",
        "number of trades",
        "trade count",
        "count of trades",
        "how many transactions",
        "number of transactions",
        "transaction count",
    }
    amount_markers = {
        "trading volume",
        "trade volume",
        "volume traded",
        "usd traded",
        "usdc traded",
        "dollar volume",
        "revenue traded",
    }

    has_token_units_marker = any(marker in q for marker in token_units_markers)
    has_trade_count_marker = any(marker in q for marker in trade_count_markers)
    has_amount_marker = any(marker in q for marker in amount_markers)

    if has_token_units_marker:
        return MetricResolution(
            matched=True,
            metric_name="tokens_traded_units",
            sql_expression="SUM(transactions.quantity)",
            reason="Question references tokens traded (units), not number of transactions.",
            disambiguation_note="Use quantity for token units. Do not use COUNT(transaction_id) unless user asks for trades.",
        )

    if has_trade_count_marker:
        return MetricResolution(
            matched=True,
            metric_name="trades_count",
            sql_expression="COUNT(transactions.transaction_id)",
            reason="Question explicitly asks for number/count of trades or transactions.",
            disambiguation_note="Use trade count, not quantity sums.",
        )

    if has_amount_marker:
        return MetricResolution(
            matched=True,
            metric_name="traded_amount_usdc",
            sql_expression="SUM(transactions.total_amount_usdc)",
            reason="Question references trading volume/amount in currency terms.",
            disambiguation_note="Use total_amount_usdc for value volume.",
        )

    return MetricResolution(
        matched=False,
        reason="No explicit ambiguous metric phrase detected.",
    )
