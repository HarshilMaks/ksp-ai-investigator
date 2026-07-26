<!-- Runtime amendment: Hexel owns platform orchestration; KSP owns investigation intelligence. The temporary Runner only passes InvestigationState through Strands agents. -->
# InvestigateAI — Product Vision
> Status: DERIVED FROM LOCKED DECISIONS
> Decision baseline: DECISIONS.md (2026-07-23)
> Last reviewed: 2026-07-24


> **AI Investigation Operating System for Karnataka State Police**

---

## The Problem

Karnataka State Police operates **1100+ police stations** across 31 districts. Today, every investigation insight requires:

- Manual SQL queries against siloed databases
- Dashboard navigation across 4–6 disconnected tools
- Hours of cross-referencing FIRs, criminal histories, and network connections
- Zero proactive intelligence — everything is reactive, query-time compute

**Result:** Investigations that should take hours take days. Patterns that should be caught early go unnoticed. Officers spend more time wrestling with data systems than investigating crimes.

---

## The Solution

**InvestigateAI is NOT a chatbot.** It is an **AI Investigation Copilot** powered by an InvestigationService, temporary Runner, reusable Strands agents, reasoning stages, and deterministic engines.

```text
User Layer: Chat + Voice + Investigation Cards
                  ↕ REST/SSE
Catalyst Gateway → Investigation Service with Runner protocol
                  ├─ Fast path: deterministic engine → evidence gate → response
                  └─ Deep path: Planner? → parallel engines → Reasoner →
                               Lead Ranking Engine → Reporter
                  ↕
Data: Catalyst Data Store + pgvector authority; Neo4j projection;
      Stratus cards/artifacts; Catalyst Cache; Signals/Cron/Circuits
```

Deterministic engines compute facts and maintain precomputed intelligence artifacts through Signals/Cron/Circuits. AI interprets intent and explains validated evidence; humans review consequential conclusions.

---

## Core Insight

### The Palantir Gotham Principle

> **Continuous intelligence, not query-time compute.**

Palantir's Gotham platform doesn't wait for an analyst to ask a question. It continuously:
- Builds and updates entity graphs
- Scores relationships by strength and recency
- Detects anomalies in transaction patterns
- Pre-computes network centrality and community clusters

**We apply this same principle to KSP's crime data:**

| Layer | Traditional Approach | InvestigateAI Approach |
|-------|---------------------|----------------------|
| Graph | Build graph on query | Graph always current, centrality pre-scored |
| Patterns | Run analytics on demand | Patterns detected continuously, alerts pushed |
| Profiles | Static criminal records | Living behavioral profiles, updated per FIR |
| Forecasts | Monthly crime reports | Rolling forecasts, updated daily |
| Leads | Officer intuition alone | AI-generated leads ranked by confidence |

---

### Architecture principle: AI decides intent; engines compute facts

The orchestrator decides which path and tools are needed. Deterministic engines compute retrieval, graph, pattern, behavioral, financial, forecast, timeline, and ranking outputs. Planner, Reasoner, and Reporter stages interpret or communicate; the Evidence/Explainability gate validates claims before release. Fast structured queries avoid LLM calls entirely.

## Key Differentiation

### What 100+ Teams Will Build vs What We Build

| Dimension | What Others Build | What We Build |
|-----------|------------------|---------------|
| **Interface** | Chat window with text responses | Investigation Operating System with cards, graphs, maps |
| **Architecture** | RAG over FIR PDFs | Orchestrator with deterministic intelligence engines and reasoning stages |
| **Graph** | Basic relationship display | Neo4j GDS with PageRank, Louvain community detection, temporal edges |
| **Forecasting** | Simple trend lines | Prophet per district × category with confidence intervals |
| **Spatial** | Pin-on-map visualization | H3 hexagonal grid with hotspot clustering |
| **Explainability** | "Based on data analysis..." | Structured rationale with clickable evidence citations |
| **Latency** | Current baseline to measure | Dated acceptance target to be set after benchmark; streaming UX |
| **Output** | Text answers | Investigation Packages: PDF brief + network diagram + lead list |
| **Security** | Basic login | Role-based views (SHO sees station, SP sees district) with full audit |
| **Demo** | Generic Q&A | 5 end-to-end investigation workflows showing real police value |

---

## Success Metrics

| Metric | Target | Why It Matters |
|--------|--------|----------------|
| **Retrieval latency** | Acceptance target to be set by 2026-08-15 benchmark | Measure representative Catalyst workloads; not an achieved fact. |
| **Precision@10** | Acceptance target to be set by 2026-08-15 benchmark | Evaluate labeled retrieval set; not an achieved fact. |
| **Citation Coverage** | Dated acceptance target pending benchmark | Every claim should trace to source FIR/record. |
| **Investigation Package Generation** | Dated acceptance target pending benchmark | Full brief with network + leads; measure representative runs. |
| **Challenge Requirement Coverage** | Dated acceptance target pending demo validation | Demonstrate the applicable datathon requirements. |
| **Demo Scenario Pass Rate** | Dated acceptance target pending scripted validation | Validate all five investigation scenarios end-to-end. |

---

## Target

### KSP Datathon 2026 — Challenge 1

**Win strategy:** Demonstrate **investigation workflow**, not chat.

The judges are senior police officers. They don't care about:
- How clever your prompts are
- How many LLM providers you support
- Generic AI capabilities

They care about:
- "Can this help my IO solve a chain-snatching series?"
- "Can this show me the network behind a financial fraud ring?"
- "Can this predict where the next burglary cluster will emerge?"

**We win by showing 5 realistic investigation scenarios that make officers say: "I need this in my station."**

---

## Philosophy

> **Every response leaves the investigator in a better position to ACT, not just informed.**

This means every interaction produces:

1. **Actionable Intelligence** — not data summaries, but "here's what to do next"
2. **Evidence Package** — citations, confidence scores, reasoning trace
3. **Next Steps** — ranked leads, suggested actions, similar case precedents
4. **Exportable Artifacts** — PDF briefs for authorized review, network diagrams for briefings

An officer should never finish an InvestigateAI interaction thinking "interesting." They should finish thinking "I know exactly what to do next."

---

## Vision Timeline

```
Phase 1 (Datathon):  one deeply implemented vertical slice; five scenarios and all requirements remain validation scope
Phase 2 (Pilot):     Live data integration, 10 pilot stations, feedback loop
Phase 3 (Scale):     1100+ stations, precompute/update pipeline, KSP-wide deployment subject to validation
```

---

*Built for Karnataka State Police. Designed to win. Engineered to deploy.*
