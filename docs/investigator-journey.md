# Investigator Journey — One Working Day

> Derived implementation north star from `.LOCK/investigation-workspace.md`, `.LOCK/investigation-workflow.md`, `.LOCK/investigation-engine.md`, and `.LOCK/investigation-scenarios.md`.
> This document does not add a new architecture or replace the locked documents.

The officer owns the investigation. AI supports the officer with evidence-backed artifacts, deterministic signals, and explicit uncertainty. The system must be useful before the officer asks a question.

## Morning: intelligence before conversation

1. The officer signs in and sees active investigations, investigation health, pending leads, and new proactive alerts.
2. A new alert is visible before chat input: **3 FIRs likely linked**.
3. The alert explains why with source-backed signals such as shared IMEI, shared vehicle, shared UPI, temporal proximity, or MO similarity.
4. The officer chooses **Review**, **Pin to investigation**, **Dismiss**, or **Open a new investigation**. No alert silently changes the case.

## Open the investigation

The officer opens an active investigation and sees one synchronized workspace:

- Conversation with full investigation context
- Evidence Board with pinned FIRs, entities, artifacts, notes, tags, and citations
- Timeline with source-linked events and gaps
- Network Graph with bounded, permission-filtered relationships
- Leads ranked by deterministic evidence value and urgency
- Hypothesis Panel with supporting, contradicting, and missing evidence
- Intelligence Cards dock with freshness, provenance, confidence, and review warnings

There is no cold start. Case memory restores the officer's prior evidence, hypotheses, notes, leads, graph state, and generated artifacts.

## Pin evidence and let the workspace update

The officer pins an FIR, person, phone, vehicle, UPI ID, account, location, or card. The pin retains its source and can be annotated, tagged, linked, and reviewed. The same state change updates the evidence board, timeline, graph, leads, hypotheses, health metrics, and relevant cards. The officer remains the owner of the decision to add or remove evidence.

## Test a hypothesis, not a hunch

The officer writes:

> "These three robbery FIRs may be connected."

The system returns a structured, reviewable hypothesis card:

```text
Evidence for       → cited facts and weights
Evidence against   → cited contradictions
Missing evidence   → critical gaps and suggested collection actions
Confidence         → deterministic/qualified score with change explanation
Officer notes      → human annotations
Status             → active / supported / refuted / inconclusive / superseded
```

The system must not convert a hypothesis into guilt, arrest advice, or a legal conclusion. The officer decides whether to continue, refute, or close it.

## Check Investigation Health

Every active investigation exposes a deterministic health summary so the officer can see what is missing:

```text
Evidence coverage       83%
Timeline completeness   91%
Network coverage        76%
Financial coverage      22%
Witness coverage        58%
Contradictions          3
Missing critical items  CDR, bank statement, CCTV
```

Each metric links to its source records and calculation. A low score is a prioritization signal, not a case-quality or legal determination. Health changes when evidence is pinned, a timeline event arrives, a relationship is verified, a hypothesis is evaluated, or a pending artifact becomes available.

## Generate and review the next action

The deterministic Lead Ranking Engine identifies evidence-backed next actions, with priority, expected evidence gain, confidence, provenance, and status. The officer can assign, act, dismiss with a reason, or defer. Optional Reporter wording may explain a ranked lead only after the evidence gate.

## Close the day

The officer can request a cited summary or report package, review contradictions and unresolved gaps, and leave notes for the next session. Checkpointed state preserves the investigation. A new session begins with changes since the last visit, not a blank conversation.

## Product acceptance lens

A feature is investigator-ready only when it answers all of these:

1. What changed in an investigation?
2. What evidence supports the change?
3. What contradicts it or is still missing?
4. What can the officer do next?
5. How does the officer remain in control?
6. Is the output permission-filtered, auditable, and explicitly qualified?
