export type InvestigationStatus = "CREATED" | "ACTIVE" | "SUSPENDED" | "CLOSED" | "ARCHIVED";

export interface Provenance {
  source: string;
  citation?: string;
  observedAt?: string;
}

export interface InvestigationHealth {
  evidenceCoverage: number;
  timelineCompleteness: number;
  networkCoverage: number;
  financialCoverage: number;
  witnessCoverage: number;
  contradictionCount: number;
  missingCriticalEvidence: string[];
}

export interface EvidenceItem {
  id: string;
  subject: string;
  kind: string;
  status?: string;
  provenance?: Provenance;
  pinnedAt?: string;
}

export interface TimelineEvent {
  id: string;
  label: string;
  occurredAt: string;
  provenance?: Provenance;
}

export interface Lead {
  id: string;
  title: string;
  priority: "LOW" | "MEDIUM" | "HIGH";
  status: "OPEN" | "IN_PROGRESS" | "DONE";
  rationale?: string;
}

export interface Hypothesis {
  id: string;
  statement: string;
  confidence: number;
  supportingEvidence: string[];
  opposingEvidence: string[];
  missingEvidence: string[];
}

export interface GraphNode {
  id: string;
  label: string;
  kind: string;
}

export interface GraphEdge {
  id: string;
  source: string;
  target: string;
  relationship: string;
}

export interface IntelligenceCard {
  id: string;
  title: string;
  kind: string;
  confidence: number;
  freshness: "FRESH" | "STALE" | "ARCHIVED";
  provenance?: Provenance;
}

export interface InvestigationState {
  id: string;
  title: string;
  status: InvestigationStatus;
  owner: string;
  updatedAt: string;
  evidence: EvidenceItem[];
  timeline: TimelineEvent[];
  leads: Lead[];
  hypotheses: Hypothesis[];
  graph: { nodes: GraphNode[]; edges: GraphEdge[] };
  cards: IntelligenceCard[];
  health: InvestigationHealth;
}

export const emptyInvestigation = (id = "demo") : InvestigationState => ({
  id,
  title: "New investigation workspace",
  status: "CREATED",
  owner: "Assigned officer",
  updatedAt: new Date(0).toISOString(),
  evidence: [],
  timeline: [],
  leads: [],
  hypotheses: [],
  graph: { nodes: [], edges: [] },
  cards: [],
  health: {
    evidenceCoverage: 0,
    timelineCompleteness: 0,
    networkCoverage: 0,
    financialCoverage: 0,
    witnessCoverage: 0,
    contradictionCount: 0,
    missingCriticalEvidence: [],
  },
});
