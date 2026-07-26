# KSP InvestigateAI

KSP InvestigateAI is a synthetic-data Crime Intelligence Operating System for Karnataka State Police.

It is investigation-first rather than chat-first:

```text
Investigation → evidence → updated investigation → next action
```

The implementation follows the locked domain architecture and the temporary runtime addendum in [`docs/orchestration-architecture.md`](docs/orchestration-architecture.md). Deterministic engines compute facts, the temporary LocalRunner invokes business agents, Hexel is the future platform runtime, and officers review consequential conclusions.

## Repository baseline

- `src/` — shared Python domain, engines, registry, orchestration, and adapters
- `functions/` — thin Python Catalyst entry-point adapters
- `client/` — Next.js 15 App Router + React 19 + TypeScript investigation workspace using Feature-Sliced Design
- `data/` — synthetic generators and fixtures only
- `appsail/` — Neo4j AppSail deployment assets
- `tests/` — standard-library smoke tests now; targeted framework tests are added in later phases
- `.LOCK/` — locked architecture and domain documentation; implementation must not modify it

## Current implementation state

Phases `P01`–`P20` are complete. The repository now contains the Python domain contracts, synthetic fixtures and ten replayable scenarios, local/Catalyst adapter boundaries, Neo4j projection contract, typed T01–T23 registry, deterministic retrieval/search and intelligence engines, the P08 evidence-gated fast path, persistent investigation state/checkpointing, versioned REST/SSE/multipart APIs, the Next.js investigation workspace, portable Runner/agent contracts, typed intelligence-card lifecycle storage, idempotent signals/entity resolution/scoped alerts, RBAC/masking/hash-chain audit governance, optional multilingual/voice/OCR/report boundaries, reproducible P19 benchmark/quality/resilience evaluation, and the P20 final review evidence.

The implementation is locally validated and synthetic-only. Production Catalyst/AppSail/Auth/SSE/Neo4j/model deployment, labeled accuracy, provider cost, and production capacity remain explicitly pending where the environment has no live services, credentials, or model assets. See [`docs/limitations.md`](docs/limitations.md), [`docs/benchmarks.md`](docs/benchmarks.md), and [`docs/demo-script.md`](docs/demo-script.md).

## Safety and scope

This repository uses synthetic data for development and demonstration. Do not add real police records, secrets, credentials, or sensitive operational data. Performance, accuracy, capacity, cost, and legal claims remain pending measured validation or separate review.
