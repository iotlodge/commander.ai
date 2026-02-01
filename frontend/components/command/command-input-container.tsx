"use client";

import { CommandInput } from "./command-input";
import { useCommandSubmit } from "@/lib/hooks/use-command-submit";

export function CommandInputContainer() {
  const { submitCommand, isLoading, error } = useCommandSubmit();

  return (
    <CommandInput
      onSubmit={submitCommand}
      isLoading={isLoading}
      error={error}
    />
  );
}
