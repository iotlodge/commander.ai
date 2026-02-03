"use client";

import { CommandInput } from "./command-input";
import { useCommandSubmit } from "@/lib/hooks/use-command-submit";
import { useAgents } from "@/lib/hooks/use-agents";

export function CommandInputContainer() {
  const { agents, isLoading: agentsLoading } = useAgents();
  const { submitCommand, isLoading, error } = useCommandSubmit({ agents });

  return (
    <CommandInput
      onSubmit={submitCommand}
      isLoading={isLoading || agentsLoading}
      error={error}
      agents={agents}
    />
  );
}
