"use client";

import {
  Activity,
  AlertTriangle,
  Bot,
  BrainCircuit,
  CalendarDays,
  CheckCircle2,
  CircleDot,
  FileSearch,
  GitBranch,
  MessageSquare,
  Network,
  Pin,
  Plus,
  RefreshCw,
  ShieldCheck,
  Target,
  Users,
} from "lucide-react";
import { useEffect, useMemo } from "react";
import { InvestigationApiClient } from "@/shared/api/client";
import { useWorkspaceStore } from "@/shared/lib/workspace-store";
import { emptyInvestigation, type InvestigationState } from "@/shared/types/investigation";

function Panel({ title, icon, children, className = "" }: { title: string; icon: React.ReactNode; children: React.ReactNode; className?: string }) {
  return (
    <section className={`workspace-panel ${className}`} aria-label={title}>
      <div className="panel-heading"><span className="panel-title">{icon}{title}</span><button className="icon-button" aria-label={`Add to ${title}`}><Plus size={15} /></button></div>
      {children}
    </section>
  );
}

function EmptyPanel({ message, action }: { message: string; action?: string }) {
  return <div className="empty-panel"><CircleDot size={18} /><span>{message}</span>{action && <button className="text-button">{action}</button>}</div>;
}

function ConversationPanel() {
  return <Panel title="Conversation" icon={<MessageSquare size={16} />} className="conversation-panel">
    <div className="proactive-alert"><AlertTriangle size={16} /><div><strong>Start with intelligence</strong><p>New linked evidence and alerts will appear here before a query is entered.</p></div></div>
    <EmptyPanel message="No conversation yet. Ask a cited question when you are ready." action="Open voice input" />
    <div className="composer"><input aria-label="Investigation question" placeholder="Ask about this investigation…" /><button aria-label="Send question"><Activity size={17} /></button></div>
  </Panel>;
}

function EvidencePanel({ state }: { state: InvestigationState }) {
  return <Panel title="Evidence Board" icon={<Pin size={16} />}>
    {state.evidence.length ? state.evidence.map((item) => <div className="list-row" key={item.id}><FileSearch size={15} /><div><strong>{item.subject}</strong><small>{item.kind} · {item.provenance?.citation ?? "Source pending"}</small></div></div>) : <EmptyPanel message="Pin evidence from a cited result to begin." action="Add evidence" />}
  </Panel>;
}

function TimelinePanel({ state }: { state: InvestigationState }) {
  return <Panel title="Timeline" icon={<CalendarDays size={16} />}>
    {state.timeline.length ? state.timeline.map((event) => <div className="timeline-row" key={event.id}><span className="timeline-dot" /><div><strong>{event.label}</strong><small>{event.occurredAt}</small></div></div>) : <EmptyPanel message="Evidence with timestamps will build the timeline." />}
  </Panel>;
}

function NetworkPanel({ state }: { state: InvestigationState }) {
  return <Panel title="Network Graph" icon={<Network size={16} />}>
    {state.graph.nodes.length ? <div className="graph-preview"><GitBranch size={28} /><strong>{state.graph.nodes.length} entities · {state.graph.edges.length} links</strong><small>Graph facts are rendered from cited backend projections.</small></div> : <EmptyPanel message="Network entities will appear as evidence is linked." action="Explore graph" />}
  </Panel>;
}

function LeadsPanel({ state }: { state: InvestigationState }) {
  return <Panel title="Leads" icon={<Target size={16} />}>
    {state.leads.length ? state.leads.map((lead) => <div className="list-row" key={lead.id}><Target size={15} className={`priority-${lead.priority.toLowerCase()}`} /><div><strong>{lead.title}</strong><small>{lead.priority} · {lead.status}</small></div></div>) : <EmptyPanel message="Validated leads will be ranked here." action="Review lead policy" />}
  </Panel>;
}

function HypothesisPanel({ state }: { state: InvestigationState }) {
  return <Panel title="Hypothesis Panel" icon={<BrainCircuit size={16} />}>
    {state.hypotheses.length ? state.hypotheses.map((hypothesis) => <div className="hypothesis" key={hypothesis.id}><strong>{hypothesis.statement}</strong><div className="confidence"><span>Confidence</span><b>{Math.round(hypothesis.confidence * 100)}%</b></div></div>) : <EmptyPanel message="Record a testable hypothesis with supporting evidence." action="Create hypothesis" />}
  </Panel>;
}

function CardsPanel({ state }: { state: InvestigationState }) {
  return <Panel title="Intelligence Cards" icon={<ShieldCheck size={16} />} className="cards-panel">
    {state.cards.length ? state.cards.map((card) => <div className="card-tile" key={card.id}><div><strong>{card.title}</strong><small>{card.kind} · {card.freshness.toLowerCase()}</small></div><span className="confidence-badge">{Math.round(card.confidence * 100)}%</span></div>) : <EmptyPanel message="Cited intelligence artifacts will dock here." action="Refresh cards" />}
  </Panel>;
}

function HealthBar({ state }: { state: InvestigationState }) {
  const metrics = useMemo(() => [
    ["Evidence", state.health.evidenceCoverage],
    ["Timeline", state.health.timelineCompleteness],
    ["Network", state.health.networkCoverage],
    ["Witness", state.health.witnessCoverage],
  ] as const, [state]);
  return <div className="health-strip"><div className="health-title"><ShieldCheck size={16} /> Investigation health</div>{metrics.map(([label, value]) => <div className="health-metric" key={label}><span>{label}</span><div className="meter"><i style={{ width: `${Math.round(value * 100)}%` }} /></div><b>{Math.round(value * 100)}%</b></div>)}<span className="health-note">{state.health.contradictionCount ? `${state.health.contradictionCount} contradiction(s) require review` : "No contradictions recorded"}</span></div>;
}

export function WorkspaceShell({ investigationId = "demo" }: { investigationId?: string }) {
  const state = useWorkspaceStore((store) => store.investigation) ?? emptyInvestigation(investigationId);
  const setInvestigation = useWorkspaceStore((store) => store.setInvestigation);
  useEffect(() => {
    if (investigationId === "demo") return;
    const controller = new AbortController();
    new InvestigationApiClient().getInvestigation(investigationId, controller.signal).then(setInvestigation).catch(() => setInvestigation(emptyInvestigation(investigationId)));
    return () => controller.abort();
  }, [investigationId, setInvestigation]);
  return <main className="workspace-shell">
    <header className="workspace-header"><div><div className="eyebrow">Investigation workspace</div><h1>{state.title}</h1><p className="header-meta"><span className={`status status-${state.status.toLowerCase()}`}>{state.status}</span><Users size={14} /> {state.owner} <span>·</span> Updated {state.updatedAt === new Date(0).toISOString() ? "not yet" : state.updatedAt}</p></div><div className="header-actions"><button className="secondary-button"><RefreshCw size={15} /> Refresh</button><button className="primary-button"><Bot size={15} /> Run investigation</button></div></header>
    <HealthBar state={state} />
    <div className="proactive-banner"><CheckCircle2 size={17} /><div><strong>Proactive intelligence feed</strong><span>System alerts and newly linked FIRs will be surfaced here when available.</span></div></div>
    <div className="workspace-grid"><ConversationPanel /><EvidencePanel state={state} /><TimelinePanel state={state} /><NetworkPanel state={state} /><LeadsPanel state={state} /><HypothesisPanel state={state} /><CardsPanel state={state} /></div>
  </main>;
}
