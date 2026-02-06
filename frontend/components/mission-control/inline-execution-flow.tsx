"use client";

import { GitBranch, Zap, Brain, Clock } from "lucide-react";

interface ExecutionStep {
  type: string;
  name: string;
  timestamp: string;
  duration_ms?: number;
  metadata?: Record<string, any>;
}

interface InlineExecutionFlowProps {
  executionTrace: ExecutionStep[];
}

export function InlineExecutionFlow({ executionTrace }: InlineExecutionFlowProps) {
  const getStepIcon = (type: string) => {
    switch (type) {
      case "node":
        return <GitBranch className="h-3 w-3 text-blue-400" />;
      case "tool":
        return <Zap className="h-3 w-3 text-yellow-400" />;
      case "llm":
        return <Brain className="h-3 w-3 text-purple-400" />;
      default:
        return <GitBranch className="h-3 w-3 text-gray-400" />;
    }
  };

  const getStepColor = (type: string) => {
    switch (type) {
      case "node":
        return "border-blue-500/30 bg-blue-500/5 text-blue-300";
      case "tool":
        return "border-yellow-500/30 bg-yellow-500/5 text-yellow-300";
      case "llm":
        return "border-purple-500/30 bg-purple-500/5 text-purple-300";
      default:
        return "border-gray-500/30 bg-gray-500/5 text-gray-300";
    }
  };

  const formatDuration = (ms: number) => {
    if (ms < 1000) {
      return `${Math.round(ms)}ms`;
    }
    return `${(ms / 1000).toFixed(2)}s`;
  };

  return (
    <div className="space-y-1.5 pl-4 border-l-2 border-[#2a3444]">
      {executionTrace.map((step, index) => (
        <div
          key={index}
          className={`flex items-center gap-2 px-3 py-1.5 rounded border text-xs ${getStepColor(
            step.type
          )}`}
        >
          {/* Icon */}
          <div className="flex-shrink-0">{getStepIcon(step.type)}</div>

          {/* Step name */}
          <span className="flex-1 font-medium truncate">{step.name}</span>

          {/* Metadata */}
          <div className="flex items-center gap-2 text-xs">
            {/* Duration */}
            {step.duration_ms !== undefined && (
              <div className="flex items-center gap-1 text-gray-400">
                <Clock className="h-3 w-3" />
                <span>{formatDuration(step.duration_ms)}</span>
              </div>
            )}

            {/* Token count */}
            {step.metadata?.tokens && (
              <span className="text-green-400">
                {step.metadata.tokens.total_tokens || step.metadata.tokens.total} tok
              </span>
            )}

            {/* Error indicator */}
            {step.metadata?.status === "failed" && (
              <span className="text-red-400">✗ Failed</span>
            )}
          </div>
        </div>
      ))}
    </div>
  );
}
