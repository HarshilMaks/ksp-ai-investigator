# Operations and limitations

## Current validation boundary

The repository is locally runnable with Python 3.11/`uv` and a pinned Next.js client. Backend adapters for Catalyst, Neo4j, model providers, Signals, Stratus, and Cache are disabled or injected by default. The local demo uses synthetic fixtures only.

## Measured

P19 measures local fixture construction/serialization, typed-card serialization, SSE event encoding, citation coverage over the ten synthetic scenario descriptors, deterministic replay digests, and bounded optional-model degradation. Machine-readable reports are written to a caller-selected path such as `/tmp/ksp-investigateai-benchmark.json`.

## Pending deployment validation

Live Catalyst Auth/API Gateway/AppSail mounting, production CORS/SSE transport, Catalyst Data Store/Cache/Stratus persistence, Neo4j driver execution, model CPU/memory behavior, labeled retrieval/entity-resolution accuracy, language parity, provider token/cost usage, and production capacity/concurrency remain pending because credentials/services/model assets are not available in the local environment.

No benchmark result in this repository establishes legal admissibility, guilt, predictive certainty, production throughput, or operational police outcomes. Consequential outputs require human review.
