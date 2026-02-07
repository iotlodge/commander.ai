"use client";

import { useEffect } from "react";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import {
  useScheduledCommands,
  ScheduledCommand,
  ScheduledCommandExecution,
} from "@/lib/hooks/use-scheduled-commands";
import { format } from "date-fns";
import { History, CheckCircle, XCircle, Clock, AlertCircle } from "lucide-react";

interface ExecutionHistoryModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  schedule: ScheduledCommand;
}

export function ExecutionHistoryModal({
  open,
  onOpenChange,
  schedule,
}: ExecutionHistoryModalProps) {
  const { executions, isLoading, error, fetchExecutions } = useScheduledCommands();

  useEffect(() => {
    if (open && schedule) {
      fetchExecutions(schedule.id, 50);
    }
  }, [open, schedule, fetchExecutions]);

  const getStatusIcon = (status: string) => {
    switch (status) {
      case "success":
        return <CheckCircle className="h-4 w-4 text-green-400" />;
      case "failed":
        return <XCircle className="h-4 w-4 text-red-400" />;
      case "running":
        return <Clock className="h-4 w-4 text-blue-400" />;
      case "timeout":
        return <AlertCircle className="h-4 w-4 text-yellow-400" />;
      default:
        return <Clock className="h-4 w-4 text-gray-400" />;
    }
  };

  const getStatusBadge = (status: string) => {
    const baseClasses = "text-xs font-medium";
    switch (status) {
      case "success":
        return (
          <Badge variant="outline" className={`${baseClasses} bg-green-500/10 text-green-400 border-green-500/30`}>
            Success
          </Badge>
        );
      case "failed":
        return (
          <Badge variant="outline" className={`${baseClasses} bg-red-500/10 text-red-400 border-red-500/30`}>
            Failed
          </Badge>
        );
      case "running":
        return (
          <Badge variant="outline" className={`${baseClasses} bg-blue-500/10 text-blue-400 border-blue-500/30`}>
            Running
          </Badge>
        );
      case "timeout":
        return (
          <Badge variant="outline" className={`${baseClasses} bg-yellow-500/10 text-yellow-400 border-yellow-500/30`}>
            Timeout
          </Badge>
        );
      default:
        return (
          <Badge variant="outline" className={`${baseClasses} bg-gray-500/10 text-gray-400 border-gray-500/30`}>
            {status}
          </Badge>
        );
    }
  };

  const formatDuration = (ms: number | null) => {
    if (!ms) return "-";
    if (ms < 1000) return `${ms}ms`;
    if (ms < 60000) return `${(ms / 1000).toFixed(1)}s`;
    return `${(ms / 60000).toFixed(1)}m`;
  };

  const formatDate = (dateString: string) => {
    try {
      return format(new Date(dateString), "MMM d, yyyy h:mm a");
    } catch {
      return "Invalid date";
    }
  };

  // Calculate stats
  const successCount = executions.filter((e) => e.status === "success").length;
  const failedCount = executions.filter((e) => e.status === "failed").length;
  const totalExecutions = executions.length;
  const successRate = totalExecutions > 0 ? ((successCount / totalExecutions) * 100).toFixed(1) : "0";

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-4xl max-h-[85vh] overflow-y-auto bg-[var(--mc-bg-secondary)] border-[var(--mc-border)]">
        <DialogHeader>
          <DialogTitle className="text-[var(--mc-text-primary)] text-xl flex items-center gap-2">
            <History className="h-5 w-5 text-purple-400" />
            Execution History
          </DialogTitle>
          <div className="text-sm text-[var(--mc-text-secondary)] font-mono">
            {schedule.command_text}
          </div>
        </DialogHeader>

        {/* Stats Summary */}
        <div className="grid grid-cols-4 gap-3 p-4 bg-[var(--mc-bg-primary)] rounded-lg border border-[var(--mc-border)]">
          <div>
            <div className="text-xs text-[var(--mc-text-tertiary)]">Total Runs</div>
            <div className="text-2xl font-bold text-[var(--mc-text-primary)]">{totalExecutions}</div>
          </div>
          <div>
            <div className="text-xs text-[var(--mc-text-tertiary)]">Success</div>
            <div className="text-2xl font-bold text-green-400">{successCount}</div>
          </div>
          <div>
            <div className="text-xs text-[var(--mc-text-tertiary)]">Failed</div>
            <div className="text-2xl font-bold text-red-400">{failedCount}</div>
          </div>
          <div>
            <div className="text-xs text-[var(--mc-text-tertiary)]">Success Rate</div>
            <div className="text-2xl font-bold text-[var(--mc-accent-blue)]">{successRate}%</div>
          </div>
        </div>

        {/* Execution List */}
        <div className="space-y-2">
          {isLoading && (
            <div className="text-center py-8 text-[var(--mc-text-secondary)]">
              Loading execution history...
            </div>
          )}

          {error && (
            <div className="text-center py-8 text-red-400">
              Error: {error}
            </div>
          )}

          {!isLoading && !error && executions.length === 0 && (
            <div className="text-center py-12 space-y-2">
              <History className="h-12 w-12 mx-auto text-[var(--mc-text-tertiary)] opacity-50" />
              <div className="text-[var(--mc-text-secondary)]">
                No execution history yet
              </div>
              <div className="text-xs text-[var(--mc-text-tertiary)]">
                This schedule hasn't run yet
              </div>
            </div>
          )}

          {!isLoading &&
            !error &&
            executions.map((execution) => (
              <ExecutionCard key={execution.id} execution={execution} />
            ))}
        </div>

        {/* Footer */}
        <div className="flex justify-end pt-4 border-t border-[var(--mc-border)]">
          <Button
            onClick={() => onOpenChange(false)}
            variant="outline"
            className="border-[var(--mc-border)] text-[var(--mc-text-primary)]"
          >
            Close
          </Button>
        </div>
      </DialogContent>
    </Dialog>
  );
}

// Individual execution card component
function ExecutionCard({ execution }: { execution: ScheduledCommandExecution }) {
  const getStatusIcon = (status: string) => {
    switch (status) {
      case "success":
        return <CheckCircle className="h-4 w-4 text-green-400" />;
      case "failed":
        return <XCircle className="h-4 w-4 text-red-400" />;
      case "running":
        return <Clock className="h-4 w-4 text-blue-400 animate-spin" />;
      case "timeout":
        return <AlertCircle className="h-4 w-4 text-yellow-400" />;
      default:
        return <Clock className="h-4 w-4 text-gray-400" />;
    }
  };

  const getStatusBadge = (status: string) => {
    const baseClasses = "text-xs font-medium";
    switch (status) {
      case "success":
        return (
          <Badge variant="outline" className={`${baseClasses} bg-green-500/10 text-green-400 border-green-500/30`}>
            Success
          </Badge>
        );
      case "failed":
        return (
          <Badge variant="outline" className={`${baseClasses} bg-red-500/10 text-red-400 border-red-500/30`}>
            Failed
          </Badge>
        );
      case "running":
        return (
          <Badge variant="outline" className={`${baseClasses} bg-blue-500/10 text-blue-400 border-blue-500/30`}>
            Running
          </Badge>
        );
      case "timeout":
        return (
          <Badge variant="outline" className={`${baseClasses} bg-yellow-500/10 text-yellow-400 border-yellow-500/30`}>
            Timeout
          </Badge>
        );
      default:
        return (
          <Badge variant="outline" className={`${baseClasses} bg-gray-500/10 text-gray-400 border-gray-500/30`}>
            {status}
          </Badge>
        );
    }
  };

  const formatDuration = (ms: number | null) => {
    if (!ms) return "-";
    if (ms < 1000) return `${ms}ms`;
    if (ms < 60000) return `${(ms / 1000).toFixed(1)}s`;
    return `${(ms / 60000).toFixed(1)}m`;
  };

  const formatDate = (dateString: string) => {
    try {
      return format(new Date(dateString), "MMM d, yyyy h:mm:ss a");
    } catch {
      return "Invalid date";
    }
  };

  return (
    <div className="p-3 bg-[var(--mc-bg-primary)] border border-[var(--mc-border)] rounded-lg hover:bg-[var(--mc-bg-secondary)] transition-colors">
      <div className="flex items-start justify-between gap-3">
        <div className="flex items-start gap-3 flex-1">
          <div className="mt-1">{getStatusIcon(execution.status)}</div>

          <div className="flex-1 space-y-2">
            <div className="flex items-center gap-2">
              {getStatusBadge(execution.status)}
              <span className="text-xs text-[var(--mc-text-tertiary)]">
                {formatDate(execution.triggered_at)}
              </span>
            </div>

            {/* Metrics */}
            <div className="flex items-center gap-3 text-xs">
              {execution.execution_duration_ms && (
                <span className="text-[var(--metric-duration)]">
                  ⏱️ {formatDuration(execution.execution_duration_ms)}
                </span>
              )}
              {execution.tokens_used && (
                <span className="text-[var(--metric-tokens)]">
                  🪙 {execution.tokens_used.toLocaleString()} tok
                </span>
              )}
              {execution.llm_calls && (
                <span className="text-[var(--metric-llm)]">
                  🤖 {execution.llm_calls} LLM
                </span>
              )}
              {execution.retry_count > 0 && (
                <span className="text-yellow-400">
                  🔄 {execution.retry_count} retries
                </span>
              )}
            </div>

            {/* Result or Error */}
            {execution.result_summary && (
              <div className="text-xs text-[var(--mc-text-secondary)] bg-[var(--mc-bg-secondary)] p-2 rounded border border-[var(--mc-border)] font-mono">
                {execution.result_summary.slice(0, 200)}
                {execution.result_summary.length > 200 && "..."}
              </div>
            )}

            {execution.error_message && (
              <div className="text-xs text-red-400 bg-red-500/5 p-2 rounded border border-red-500/20 font-mono">
                {execution.error_message}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
