import { WorkspaceShell } from "@/widgets/workspace/workspace-shell";

export default async function InvestigationPage({ params }: { params: Promise<{ investigationId: string }> }) {
  const { investigationId } = await params;
  return <WorkspaceShell investigationId={investigationId} />;
}
