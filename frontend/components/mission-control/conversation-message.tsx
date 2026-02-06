"use client";

import { useState } from "react";
import { AgentTask, TaskStatus } from "@/lib/types";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Copy, ChevronDown, ChevronUp, CheckCircle, AlertCircle } from "lucide-react";
import { InlineExecutionFlow } from "./inline-execution-flow";
import { MarkdownRenderer } from "@/components/ui/markdown-renderer";

interface ConversationMessageProps {
  task: AgentTask;
  timestamp: Date;
}

const AGENT_COLORS: Record<string, string> = {
  chat: "#4a9eff",
  bob: "#10b981",
  sue: "#f59e0b",
  rex: "#8b5cf6",
  alice: "#ec4899",
  maya: "#06b6d4",
  kai: "#f97316",
};

export function ConversationMessage({ task, timestamp }: ConversationMessageProps) {
  const [showExecutionFlow, setShowExecutionFlow] = useState(false);
  const [copied, setCopied] = useState(false);

  const agentColor = AGENT_COLORS[task.agent_nickname] || "#4a9eff";
  const isSuccess = task.status === TaskStatus.COMPLETED;
  const hasExecutionTrace = task.metadata?.execution_trace &&
    (task.metadata.execution_trace as any[]).length > 0;

  const handleCopy = async () => {
    const textToCopy = task.result || task.error_message || "";
    try {
      await navigator.clipboard.writeText(textToCopy);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch (err) {
      console.error("Failed to copy:", err);
    }
  };

  return (
    <div className="flex gap-3">
      {/* Avatar */}
      <Avatar
        className="h-10 w-10 flex-shrink-0"
        style={{ backgroundColor: agentColor }}
      >
        <AvatarFallback
          className="text-white text-sm font-bold"
          style={{ backgroundColor: agentColor }}
        >
          {task.agent_nickname.slice(0, 2).toUpperCase()}
        </AvatarFallback>
      </Avatar>

      {/* Message Content */}
      <div className="flex-1 min-w-0">
        {/* Header */}
        <div className="flex items-center gap-2 mb-2">
          <span className="text-white font-semibold">@{task.agent_nickname}</span>
          <Badge
            variant="outline"
            className={
              isSuccess
                ? "text-xs bg-green-500/10 text-green-400 border-green-500/30"
                : "text-xs bg-red-500/10 text-red-400 border-red-500/30"
            }
          >
            {isSuccess ? (
              <>
                <CheckCircle className="h-3 w-3 mr-1" />
                Success
              </>
            ) : (
              <>
                <AlertCircle className="h-3 w-3 mr-1" />
                Failed
              </>
            )}
          </Badge>
          <span className="text-xs text-gray-500">
            {timestamp.toLocaleTimeString()}
          </span>
        </div>

        {/* Execution Flow (inline, collapsible) */}
        {hasExecutionTrace && (
          <div className="mb-3">
            <button
              onClick={() => setShowExecutionFlow(!showExecutionFlow)}
              className="flex items-center gap-2 text-xs text-gray-400 hover:text-white transition-colors mb-2"
            >
              {showExecutionFlow ? (
                <ChevronUp className="h-4 w-4" />
              ) : (
                <ChevronDown className="h-4 w-4" />
              )}
              <span>
                Execution flow ({(task.metadata.execution_trace as any[]).length} steps)
              </span>
            </button>

            {showExecutionFlow && (
              <InlineExecutionFlow
                executionTrace={task.metadata.execution_trace as any[]}
              />
            )}
          </div>
        )}

        {/* Response Content */}
        <div className="bg-[#1e2433] border border-[#2a3444] rounded-lg p-4">
          {task.result && task.result.trim().length > 0 ? (
            <MarkdownRenderer
              content={task.result}
              variant="default"
              className="text-gray-200"
            />
          ) : task.error_message && task.error_message.trim().length > 0 ? (
            <div className="text-red-400">
              <MarkdownRenderer
                content={task.error_message}
                variant="error"
              />
            </div>
          ) : (
            <div className="text-gray-500 italic text-sm">
              Task completed with no output
            </div>
          )}
        </div>

        {/* Actions */}
        <div className="flex items-center gap-2 mt-2">
          <Button
            variant="ghost"
            size="sm"
            onClick={handleCopy}
            className="text-xs text-gray-400 hover:text-white"
          >
            {copied ? (
              <>
                <CheckCircle className="h-3 w-3 mr-1" />
                Copied!
              </>
            ) : (
              <>
                <Copy className="h-3 w-3 mr-1" />
                Copy
              </>
            )}
          </Button>
        </div>
      </div>
    </div>
  );
}
