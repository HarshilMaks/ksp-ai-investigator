# KSP InvestigateAI Orchestration Architecture Addendum

**Status:** implementation architecture amendment  
**Scope:** runtime strategy only; domain, schema, ontology, workflows, Catalyst, Neo4j, tools, and frontend contracts are unchanged.

## Decision

Hexel Studio is the long-term runtime/platform. KSP InvestigateAI owns the investigation business layer; it does not recreate Hexel capabilities.

```text
Catalyst AppSail
      ↓
FastAPI
      ↓
InvestigationService
      ↓
Runner (Protocol)
      ├── LocalRunner (temporary)
      └── HexelRunner (future adapter)
      ↓
Strands Agents
      ↓
InvestigationState result
```

Future migration:

```text
FastAPI
  ↓
Hexel Studio Fleet
  ↓
Same Strands Agents
```

## Feature decision rule

Every proposed feature must answer one question: **Is this investigation intelligence or infrastructure?** Build investigation intelligence. If it is infrastructure already provided by Catalyst or Hexel, integrate with it instead of rebuilding it.

Only the runner/runtime adapter changes during migration. Domain models, tools, APIs, investigation logic, data stores, Neo4j, frontend, and agents remain portable.

## Ownership boundary

Hexel Studio owns agent deployment, fleet orchestration, scheduling, task lifecycle, parallel execution, durable execution, skills, Tool Gateway, MCP, memory, knowledge store, IAM, policies, governance, observability, metrics, and analytics.

KSP InvestigateAI owns investigation APIs, business logic, Strands agents, workflows, evidence, graph intelligence, timelines, crime intelligence, pattern/financial intelligence, reports, Catalyst/Neo4j integration, frontend, and synthetic data.

Until Hexel is available, KSP uses only a deliberately small local runner. It invokes agents, passes `InvestigationState`, and returns the final state. It does not implement workflow graphs, scheduling, distributed execution, durable execution, cancellation frameworks, or a replacement orchestration platform.

## Temporary Runner

The InvestigationService depends only on this protocol:

```python
class Runner(Protocol):
    async def run(self, state: InvestigationState) -> InvestigationState: ...
```

Implementations are:

```text
Runner
 ├── LocalRunner   # current, temporary
 └── HexelRunner   # future platform adapter
```

`LocalRunner` is temporary infrastructure. Business logic lives in agents, engines, services, and tools—not in the runner. A future `HexelRunner` adapter satisfies the same interface.

## Investigation State

Every agent receives and returns the same shared `InvestigationState`. Agents enrich state; they do not replace it, persist it, access databases, or invoke other agents.

State includes query/session/officer authorization, route, execution plan, engine results, evidence board, hypotheses, structured rationale, citations, contradictions, confidence, leads, timeline, package, errors, tool calls, and checkpoint reference.

### Strands agents

Production agents are reusable Strands implementations:

- **Planner** — creates a validated plan when needed.
- **Evidence** — validates evidence and release conditions.
- **Graph Intelligence** — interprets graph-engine results.
- **Pattern Intelligence** — interprets pattern-engine results.
- **Financial Intelligence** — interprets financial-engine results.
- **Timeline** — interprets timeline-engine results.
- **Reasoner** — grounded synthesis over validated results.
- **Reporter** — evidence-backed wording and reports.

Each agent receives and returns `InvestigationState`. Agents never orchestrate, schedule, call other agents, depend on Catalyst/Hexel, or own persistence.

```python
async def run(state: InvestigationState) -> InvestigationState: ...
```

The temporary LocalRunner invokes these agents in the minimal agreed sequence. Hexel will own the production fleet execution later.

### Infrastructure integrations

KSP agents and business logic use the existing typed T01–T23 registry, adapter ports, Catalyst adapters, Neo4j boundary, and provider-neutral LLM adapter. These are integration boundaries, not new platform services.

- The registry remains authoritative for typed tools, validation, authorization metadata, citations, and audit context.
- `src/adapters/llm.py` remains the provider-neutral LLM integration boundary.
- Catalyst remains infrastructure and the authoritative structured-data system.
- Neo4j remains a projection/query layer.
- MCP is not implemented as a core dependency; a future Hexel integration may provide it.

No separate Tool Gateway, AI Gateway, policy platform, skill platform, MCP server, or observability platform is built by KSP.

### Business capability modules

Reusable business capabilities may be implemented as ordinary Python services, deterministic engines, or Strands agent helpers. They compose existing tools and adapters; they do not become a new orchestration framework.

### Optional integration hooks

KSP may expose simple application callbacks for audit or logging where needed. These are ordinary integration points, not a local lifecycle platform. Hexel owns production lifecycle governance, metrics, plugins, and observability.

### Investigation workflows

Cyber Fraud, Vehicle Theft, Financial Crime, Missing Person, and Organized Crime workflows are KSP business logic. They are implemented as investigation services and agent sequences. They are not agents, and the temporary runner does not become a workflow engine.

## Execution model

```text
Request
  ↓
FastAPI investigation service
  ↓
Router
  ├── Fast Path → deterministic engine → cited response
  └── Runner.run(state)
        ↓
      Planner → Evidence → Intelligence Agents → Reasoner → Reporter
        ↓
      InvestigationState result
```

The P08 fast path remains completely outside the Runner. Exact FIR lookups, counts, dates, and simple deterministic graph queries do not create or invoke a Runner. The Runner executes only agent-based investigation workflows.

## Migration constraints

- No LangGraph, CrewAI, or locally built orchestration framework is introduced.
- No Hexel SDK dependency is introduced while Hexel is unavailable.
- No separate AI Gateway, Tool Gateway, policy engine, event platform, plugin platform, or MCP server is built by KSP.
- The temporary runner only invokes agents, passes `InvestigationState`, and returns the final state.
- P09 owns persistent investigation state/checkpoints as business application state; the runner does not own persistence.
- P12 owns the minimal Runner interface and Strands agent integration; P13 owns deterministic intelligence and business capability modules.
- Catalyst remains infrastructure and Neo4j remains a projection/query store.
- The protected PRD remains unchanged; this addendum governs the temporary runtime strategy.

## Agent context

Agents receive a small dependency-injected context assembled by the application service or runner. It contains the current `InvestigationState`, user query, authorization context, and references to the existing registry/adapters required by the agent. It is not a memory store, policy platform, skill registry, or orchestration framework.

```python
@dataclass(frozen=True)
class AgentContext:
    state: InvestigationState
    auth_context: dict[str, object]
    registry: object  # typed T01–T23 registry reference
    llm: object       # provider-neutral LLM boundary reference
    logger: object
```

`registry` and `llm` are typed application boundaries, not Catalyst clients, Neo4j drivers, database sessions, HTTP clients, or provider SDKs.
Agents enrich `InvestigationState` and return it. They do not persist state, access global state, call other agents, or depend on Hexel.

## Explicitly deferred to Hexel

The following are not rebuilt locally by KSP:

- fleet orchestration and scheduling
- durable execution and distributed task lifecycle
- platform-level Event Bus
- Policy/IAM platform
- plugin platform
- Skill platform
- MCP servers and gateway
- memory and knowledge stores
- platform observability, metrics, and analytics

KSP integrates with these capabilities later through the runner/platform boundary. The competitive implementation remains the investigation business layer.
