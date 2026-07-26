# Frontend Architecture

> Frontend-only implementation contract. Backend, AI, database, ontology, workflows, APIs, and business logic remain defined by `.LOCK/` and are not changed by this document.

## Stack

- **Framework:** Next.js 15 with App Router
- **UI runtime:** React 19 + TypeScript
- **Styling:** Tailwind CSS v4
- **Component primitives:** shadcn/ui + Radix UI
- **Icons and motion:** Lucide React + Motion (Framer Motion)
- **Server state:** TanStack Query v5
- **Client state:** Zustand
- **Forms and validation:** React Hook Form + Zod
- **Data tables:** TanStack Table
- **Visualization:** Cytoscape.js, Apache ECharts, MapLibre GL
- **Workspace layout:** react-resizable-panels
- **Command/search UI:** cmdk
- **Notifications:** Sonner
- **Drag and drop:** React DnD
- **Markdown and reports:** react-markdown + React PDF
- **Theme:** next-themes

## Communication and deployment

The frontend communicates only through the locked external boundary:

- REST APIs for capability and resource operations
- Server-Sent Events (SSE) for investigation progress, AI streaming, citations, cards, and proactive alerts
- JWT/Catalyst Authentication, with authorization enforced by the backend
- Multipart REST for voice/audio and document uploads where enabled

The Next.js application is deployed on Catalyst AppSail. This changes the frontend hosting/runtime only; Catalyst Functions, the Runner/runtime boundary, deterministic engines, Data Store, pgvector, Neo4j, Stratus, Cache, Signals, Cron, and Circuits remain unchanged.

## Feature-Sliced Design

The frontend package is `client/`; the following tree is rooted at `client/src/`:

```text
client/
├── next.config.ts
├── package.json
├── tsconfig.json
├── postcss.config.mjs
└── src/
    ├── app/                    # Next.js App Router routes, layouts, providers
    ├── features/
    │   ├── investigation/      # Investigation lifecycle and health
    │   ├── evidence/           # Evidence board, pinning, provenance
    │   ├── graph/              # Cytoscape graph interactions
    │   ├── intelligence/       # Card dock, freshness, confidence
    │   ├── timeline/           # Timeline and gaps
    │   ├── reports/            # Report preview/export UI
    │   ├── chat/               # Conversation and SSE stream UI
    │   └── authentication/     # Catalyst login, JWT session UI
    ├── entities/               # FIR, person, vehicle, phone, account, and user models
    ├── widgets/                # Workspace shell, panels, navigation, alert feed
    ├── shared/
    │   ├── ui/                 # shadcn/ui, Radix, and shared primitives
    │   ├── api/                # REST and SSE clients; no backend business logic
    │   ├── hooks/              # Shared React hooks
    │   ├── lib/                # Query client, theme, DnD, formatting setup
    │   ├── types/              # Shared TypeScript API/view types
    │   └── utils/              # Pure presentation utilities
    └── styles/                 # Tailwind v4 theme and global styles
```

Feature modules may depend on entities and shared layers; shared code must not depend on features. Backend authorization, evidence gating, deterministic computation, and API contracts remain server-owned.

## Workspace composition

The seven locked workspace panels are implemented as widgets composed from features: Conversation, Evidence Board, Timeline, Network Graph, Leads, Hypothesis Panel, and Intelligence Cards. `react-resizable-panels` provides the officer-controlled layout. Zustand holds local workspace/view state, TanStack Query v5 holds REST resource state, and SSE events update the query/cache layer and relevant stores. `next-themes` controls light/dark theme without changing investigation semantics.

Cytoscape.js renders relationship graphs, Apache ECharts renders Sankey/timeline/heatmap/trend views, and MapLibre GL renders geographic/H3 overlays. No visualization library computes authoritative facts; all data arrives from cited backend artifacts.

## Frontend acceptance boundary

- The home view surfaces proactive intelligence and active investigations before an empty chat prompt.
- Every card, hypothesis, health metric, timeline event, graph edge, and lead links to backend evidence/provenance metadata.
- The officer remains the investigation owner; UI labels predictions and consequential conclusions for human review.
- REST/SSE/JWT behavior is tested against the backend contracts without introducing WebSockets, gRPC, MCP, or direct database access.
