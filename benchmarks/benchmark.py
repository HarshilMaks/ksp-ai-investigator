"""Reproducible local benchmark and quality/resilience report for P19."""

from __future__ import annotations

import json
import platform
import statistics
import time
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable

from data.scenarios import build_scenarios, scenario_digest
from src.adapters.onnx import OptionalModel
from src.domain.cards import CardProvenance, LeadCard
from src.api.sse import SSEEvent


@dataclass(frozen=True)
class TimingMeasurement:
    name: str
    iterations: int
    p50_ms: float
    p95_ms: float
    p99_ms: float
    min_ms: float
    max_ms: float
    throughput_per_second: float


@dataclass(frozen=True)
class BenchmarkReport:
    schema_version: str
    measured_at_utc: str
    environment: dict[str, str]
    scenario_seed: int
    scenario_digest: str
    timings: tuple[TimingMeasurement, ...]
    quality: dict[str, object]
    resilience: dict[str, object]
    pending: tuple[str, ...]

    def to_record(self) -> dict[str, object]:
        return asdict(self)


def _measure(name: str, function: Callable[[], object], iterations: int) -> TimingMeasurement:
    values: list[float] = []
    for _ in range(iterations):
        start = time.perf_counter()
        function()
        values.append((time.perf_counter() - start) * 1000)
    ordered = sorted(values)
    percentile = lambda fraction: ordered[min(len(ordered) - 1, max(0, int(len(ordered) * fraction) - 1))]
    elapsed_seconds = sum(values) / 1000
    return TimingMeasurement(name, iterations, round(percentile(.50), 6), round(percentile(.95), 6), round(percentile(.99), 6), round(min(values), 6), round(max(values), 6), round(iterations / elapsed_seconds, 3) if elapsed_seconds else 0.0)


def run_benchmark(*, iterations: int = 25, seed: int = 20260726) -> BenchmarkReport:
    if not 5 <= iterations <= 500:
        raise ValueError("iterations must be between 5 and 500")
    scenarios = build_scenarios(seed)
    provenance = CardProvenance(engine="benchmark", algorithm_version="p19.1", source_ids=("SYNTHETIC-BENCHMARK-SOURCE",), data_snapshot="synthetic")
    payload = LeadCard(lead_id="benchmark-lead", investigation_id="benchmark-investigation", action="review", rationale="synthetic benchmark", priority="medium", confidence=.5, status="pending")
    event = SSEEvent("token", {"text": "synthetic", "citation": "SYNTHETIC-BENCHMARK-SOURCE"})
    timings = (
        _measure("scenario_fixture_build", lambda: build_scenarios(seed), iterations),
        _measure("scenario_json_serialization", lambda: json.dumps([item.to_record() for item in scenarios], sort_keys=True), iterations),
        _measure("card_payload_serialization", lambda: payload.model_dump(mode="json"), iterations),
        _measure("sse_event_encoding", event.encode, iterations),
    )
    cited = sum(bool(item.citations) for item in scenarios)
    quality = {
        "scenario_count": len(scenarios),
        "citation_coverage": round(cited / len(scenarios), 6),
        "synthetic_fixture_coverage": round(sum(item.citations[0].startswith("SYNTHETIC-") for item in scenarios) / len(scenarios), 6),
        "unsupported_claims_in_fixture_metadata": 0,
        "labeled_accuracy_metrics": False,
    }
    unavailable = OptionalModel("benchmark-optional-model").status
    resilience = {
        "optional_model_degrades_without_assets": not unavailable.available,
        "scenario_fallbacks_present": all(bool(item.fallback) for item in scenarios),
        "external_service_calls": 0,
        "bounded_fixture_replay": True,
    }
    pending = (
        "production Catalyst/AppSail latency and throughput",
        "live SSE first-token timing",
        "pgvector/Neo4j performance",
        "Precision@K/Recall@K against labeled data",
        "language parity with model assets",
        "token/cost usage with provider credentials",
        "production capacity and concurrency limits",
    )
    return BenchmarkReport("p19.1", datetime.now(timezone.utc).isoformat(), {"python": platform.python_version(), "platform": platform.platform()}, seed, scenario_digest(scenarios), timings, quality, resilience, pending)


def write_report(path: str | Path, report: BenchmarkReport | None = None) -> Path:
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps((report or run_benchmark()).to_record(), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return destination


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=Path("/tmp/ksp-investigateai-benchmark.json"))
    parser.add_argument("--iterations", type=int, default=25)
    args = parser.parse_args()
    report = run_benchmark(iterations=args.iterations)
    write_report(args.output, report)
    print(json.dumps(report.to_record(), indent=2, sort_keys=True))
