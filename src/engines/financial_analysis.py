"""Deterministic financial flow and layering indicators."""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime
from typing import Iterable

from .intelligence_types import EngineMetadata, SourceEvidence, Uncertainty

MAX_TRANSACTIONS = 500
MAX_FINANCIAL_HOPS = 5


@dataclass(frozen=True)
class FinancialTransaction:
    transaction_id: str
    source_account: str
    target_account: str
    amount: float
    occurred_at: datetime
    channel: str
    source_ids: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if self.amount < 0:
            raise ValueError("transaction amount cannot be negative")


@dataclass(frozen=True)
class FinancialFlowSignal:
    source_account: str
    target_account: str
    transaction_count: int
    total_amount: float
    channels: tuple[str, ...]
    evidence: tuple[SourceEvidence, ...]


@dataclass(frozen=True)
class LayeringIndicators:
    rapid_movement: bool
    round_tripping: bool
    smurfing_detected: bool
    pattern_match_score: float


@dataclass(frozen=True)
class FinancialAnalysisResult:
    flows: tuple[FinancialFlowSignal, ...]
    indicators: LayeringIndicators
    metadata: EngineMetadata
    uncertainty: Uncertainty


def analyze_financial_flow(transactions: Iterable[FinancialTransaction], *, max_hops: int = MAX_FINANCIAL_HOPS, max_transactions: int = MAX_TRANSACTIONS) -> FinancialAnalysisResult:
    if not 1 <= max_hops <= MAX_FINANCIAL_HOPS or not 1 <= max_transactions <= MAX_TRANSACTIONS:
        raise ValueError("financial bounds are outside the permitted range")
    values = sorted(tuple(transactions), key=lambda item: (item.occurred_at, item.transaction_id))
    if len(values) > max_transactions:
        raise ValueError("financial input exceeds bounded transaction limit")
    grouped: dict[tuple[str, str], list[FinancialTransaction]] = defaultdict(list)
    for transaction in values:
        grouped[(transaction.source_account, transaction.target_account)].append(transaction)
    flows = tuple(FinancialFlowSignal(source, target, len(items), round(sum(item.amount for item in items), 2), tuple(sorted({item.channel for item in items})), _sources(items)) for (source, target), items in sorted(grouped.items()))
    outgoing = {item.source_account: item.target_account for item in values if item.source_account != item.target_account}
    round_trip = any(account in outgoing and outgoing.get(outgoing[account]) == account for account in outgoing)
    rapid = any((right.occurred_at - left.occurred_at).total_seconds() <= 24 * 3600 for left, right in zip(values, values[1:]))
    small = [item for item in values if item.amount < (sum(value.amount for value in values) / max(1, len(values)))]
    smurfing = len(small) >= 3 and len({item.source_account for item in small}) >= 2
    score = round(sum((rapid, round_trip, smurfing)) / 3, 6)
    return FinancialAnalysisResult(flows, LayeringIndicators(rapid, round_trip, smurfing, score), EngineMetadata("financial_analysis", "bounded_flow_aggregation_and_indicators", "p13.1", (("max_hops", max_hops), ("max_transactions", max_transactions)), len(values)), Uncertainty("transaction_record_coverage", 0.9 if values else 0.0, ("Indicators are review signals and do not establish laundering or guilt.",)))


def _sources(items: Iterable[FinancialTransaction]) -> tuple[SourceEvidence, ...]:
    return tuple(SourceEvidence(source) for source in sorted({source for item in items for source in item.source_ids}))


__all__ = ["FinancialAnalysisResult", "FinancialFlowSignal", "FinancialTransaction", "LayeringIndicators", "analyze_financial_flow"]
