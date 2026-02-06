"use client";

import { AgentTask } from "@/lib/types";
import { Loader2 } from "lucide-react";

interface SystemMessageProps {
  message: string;
  task?: AgentTask;
  timestamp: Date;
}

export function SystemMessage({ message, task, timestamp }: SystemMessageProps) {
  return (
    <div className="flex items-center justify-center">
      <div className="flex items-center gap-2 bg-[#1e2433]/50 border border-[#2a3444] rounded-full px-4 py-2">
        <Loader2 className="h-3 w-3 text-[#4a9eff] animate-spin" />
        <span className="text-xs text-gray-400">{message}</span>
        {task && task.progress_percentage !== undefined && (
          <span className="text-xs text-[#4a9eff]">
            {task.progress_percentage}%
          </span>
        )}
      </div>
    </div>
  );
}
