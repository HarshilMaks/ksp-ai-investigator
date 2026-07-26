import { create } from "zustand";
import type { InvestigationState } from "@/shared/types/investigation";

interface WorkspaceStore {
  investigation: InvestigationState | null;
  selectedEvidenceId: string | null;
  setInvestigation: (investigation: InvestigationState) => void;
  selectEvidence: (id: string | null) => void;
}

export const useWorkspaceStore = create<WorkspaceStore>((set) => ({
  investigation: null,
  selectedEvidenceId: null,
  setInvestigation: (investigation) => set({ investigation }),
  selectEvidence: (selectedEvidenceId) => set({ selectedEvidenceId }),
}));
