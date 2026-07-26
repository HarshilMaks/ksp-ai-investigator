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

Phases `P01`–`P12` are complete. The repository now contains the Python domain contracts, synthetic fixtures, local/Catalyst adapter boundaries, Neo4j projection contract, typed T01–T23 registry, deterministic retrieval/search engines, the P08 evidence-gated fast path, P09 persistent investigation state/checkpointing, P10 versioned REST/SSE/multipart API boundaries, the P11 Next.js investigation workspace shell, and the P12 portable Runner/agent contracts.

`P13` — deterministic intelligence engines and agent business capabilities — is next. The P08 fast path remains outside the Runner, and the P12 LocalRunner only passes `InvestigationState` through injected agents. See [`docs/api-reference.md`](docs/api-reference.md) for the current API contract.

## Safety and scope

This repository uses synthetic data for development and demonstration. Do not add real police records, secrets, credentials, or sensitive operational data. Performance, accuracy, capacity, cost, and legal claims remain pending measured validation or separate review.
