"use client";

import { useEffect } from "react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { ThemeProvider } from "next-themes";
import { useWorkspaceStore } from "@/shared/lib/workspace-store";
import { emptyInvestigation } from "@/shared/types/investigation";

const queryClient = new QueryClient({
  defaultOptions: { queries: { staleTime: 30_000, retry: 1 } },
});

function WorkspaceBootstrap() {
  const setInvestigation = useWorkspaceStore((state) => state.setInvestigation);
  useEffect(() => {
    setInvestigation(emptyInvestigation());
  }, [setInvestigation]);
  return null;
}

export function Providers({ children }: { children: React.ReactNode }) {
  return (
    <ThemeProvider attribute="class" defaultTheme="dark" enableSystem={false}>
      <QueryClientProvider client={queryClient}>
        <WorkspaceBootstrap />
        {children}
      </QueryClientProvider>
    </ThemeProvider>
  );
}
