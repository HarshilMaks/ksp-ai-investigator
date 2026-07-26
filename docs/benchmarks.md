# P19 benchmark report

Run the local benchmark with:

```bash
uv run python scripts/benchmark.py --iterations 25 --output /tmp/ksp-investigateai-benchmark.json
```

The report is machine-readable JSON with:

- p50/p95/p99/min/max latency in milliseconds
- local throughput per second
- deterministic scenario digest
- citation/synthetic coverage metrics
- optional-model and external-service resilience checks
- explicit pending measurements

The benchmark measures only the current local Python implementation: scenario fixture construction/serialization, typed card serialization, and SSE event encoding. It does **not** claim Catalyst, AppSail, Neo4j, pgvector, live SSE, model, token-cost, or production-capacity performance. Accuracy metrics remain pending labeled data; no Precision@K/Recall@K claim is emitted.

The benchmark is intentionally small and bounded. It is a reproducible evaluation artifact, not a load generator for production infrastructure.
