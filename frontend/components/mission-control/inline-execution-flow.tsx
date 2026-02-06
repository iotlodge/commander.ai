"use client";

import { GitBranch, Zap, Brain, Clock } from "lucide-react";

interface ExecutionStep {
  type: string;
  name: string;
  timestamp: string;
  duration_ms?: number;
  metadata?: Record<string, any>;
}

interface ExecutionSummary {
  total_steps: number;
  total_duration_ms: number;
  step_counts: Record<string, number>;
}

interface ExecutionMetrics {
  llm_calls: number;
  tool_calls: number;
  agent_calls: number;
  tokens: {
    prompt: number;
    completion: number;
    total: number;
  };
}

interface InlineExecutionFlowProps {
  executionTrace: ExecutionStep[];
  executionSummary?: ExecutionSummary;
  executionMetrics?: ExecutionMetrics;
}

export function InlineExecutionFlow({
  executionTrace,
  executionSummary,
  executionMetrics
}: InlineExecutionFlowProps) {
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
    <div className="space-y-3">
      {/* Metrics Summary */}
      {(executionMetrics || executionSummary) && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3 p-3 bg-[#1a1f2e] rounded-lg border border-[#2a3444]">
          {/* Token Metrics */}
          {executionMetrics && executionMetrics.tokens && (
            <>
              <div className="space-y-1">
                <div className="text-xs text-gray-500">Total Tokens</div>
                <div className="text-lg font-bold text-green-400">
                  {executionMetrics.tokens.total?.toLocaleString() || '0'}
                </div>
                {executionMetrics.tokens.prompt !== undefined && executionMetrics.tokens.completion !== undefined && (
                  <div className="text-xs text-gray-400">
                    {executionMetrics.tokens.prompt.toLocaleString()} prompt + {executionMetrics.tokens.completion.toLocaleString()} completion
                  </div>
                )}
              </div>
              {executionMetrics.llm_calls !== undefined && (
                <div className="space-y-1">
                  <div className="text-xs text-gray-500">LLM Calls</div>
                  <div className="text-lg font-bold text-purple-400">
                    {executionMetrics.llm_calls}
                  </div>
                </div>
              )}
              {executionMetrics.tool_calls !== undefined && (
                <div className="space-y-1">
                  <div className="text-xs text-gray-500">Tool Calls</div>
                  <div className="text-lg font-bold text-yellow-400">
                    {executionMetrics.tool_calls}
                  </div>
                </div>
              )}
              {executionMetrics.agent_calls !== undefined && executionMetrics.agent_calls > 0 && (
                <div className="space-y-1">
                  <div className="text-xs text-gray-500">Agent Calls</div>
                  <div className="text-lg font-bold text-cyan-400">
                    {executionMetrics.agent_calls}
                  </div>
                </div>
              )}
            </>
          )}

          {/* Duration */}
          {executionSummary && (
            <div className="space-y-1">
              <div className="text-xs text-gray-500">Duration</div>
              <div className="text-lg font-bold text-blue-400">
                {formatDuration(executionSummary.total_duration_ms)}
              </div>
            </div>
          )}
        </div>
      )}

      {/* Execution Flow Steps */}
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
    </div>
  );
}
