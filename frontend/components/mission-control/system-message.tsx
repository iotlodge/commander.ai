"use client";

import { memo } from "react";
import { AgentTask } from "@/lib/types";
import { Loader2 } from "lucide-react";

interface SystemMessageProps {
  message: string;
  task?: AgentTask;
  timestamp: Date;
}

function SystemMessageComponent({ message, task, timestamp }: SystemMessageProps) {
  return (
    <div className="flex items-center justify-center">
      <div className="flex items-center gap-2 bg-[var(--mc-bg-secondary)]/50 border border-[var(--mc-border)] rounded-full px-4 py-2">
        <Loader2 className="h-3 w-3 text-[var(--mc-accent-blue)] animate-spin" />
        <span className="text-xs text-gray-400">{message}</span>
        {task && task.progress_percentage !== undefined && (
          <span className="text-xs text-[var(--mc-accent-blue)]">
            {task.progress_percentage}%
          </span>
        )}
      </div>
    </div>
  );
}

// Memoize to prevent unnecessary re-renders
export const SystemMessage = memo(SystemMessageComponent);
