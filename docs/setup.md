# Development Setup

## Locked runtime

The deployment target is Python 3.11. Local development may use another compatible Python version, but deployment-specific behavior must be validated on Python 3.11 before release. The frontend target is Next.js 15 App Router + React 19 + TypeScript on Catalyst AppSail, using REST APIs and SSE for AI/progress/alert streams with JWT/Catalyst Authentication.

## Phase 1 validation

No third-party runtime dependency is required for the repository baseline. Use `uv` as the implementation and validation runner:

```bash
uv --version
uv run python --version
uv run python -m unittest discover -s tests -p 'test_*.py'
git diff --check
git status --short --ignored
```

`uv run` creates/uses the project environment and resolves the locked Python 3.11 interpreter when available. `pytest` and service dependencies are introduced only in later phases after the configuration and adapter boundaries are established. Do not use raw `python`/`pip` commands for implementation or dependency management, and do not install or commit secrets as part of the baseline.

## Local boundaries

- Core business logic belongs in `src/`.
- Catalyst entry points belong in `functions/` and must delegate to `src/`.
- Synthetic fixtures belong in `data/`; real police data is prohibited.
- Neo4j assets belong in `appsail/neo4j/`; the application Bolt port is `7687` and the Neo4j Browser port `7474` is not a production public interface.
- `.LOCK/` is documentation ground truth and is not modified by implementation work.

## Investigator-first product north star

Read [`investigator-journey.md`](investigator-journey.md) before adding user-facing behavior. The home experience begins with proactive intelligence and active investigations, not an empty chat box.
