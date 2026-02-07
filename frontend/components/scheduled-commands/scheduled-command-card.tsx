"use client";

import { ScheduledCommand } from "@/lib/hooks/use-scheduled-commands";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Edit, Trash2, Play, Pause, Clock, Calendar, History } from "lucide-react";
import { formatDistanceToNow, format } from "date-fns";

interface ScheduledCommandCardProps {
  schedule: ScheduledCommand;
  onEdit: (schedule: ScheduledCommand) => void;
  onDelete: (scheduleId: string) => void;
  onToggleEnabled: (scheduleId: string, enabled: boolean) => void;
  onRunNow: (scheduleId: string) => void;
  onViewHistory: (schedule: ScheduledCommand) => void;
}

export function ScheduledCommandCard({
  schedule,
  onEdit,
  onDelete,
  onToggleEnabled,
  onRunNow,
  onViewHistory,
}: ScheduledCommandCardProps) {
  // Format schedule display
  const getScheduleDisplay = () => {
    if (schedule.schedule_type === "cron") {
      return {
        type: "Cron",
        value: schedule.cron_expression || "",
        icon: <Calendar className="h-3 w-3" />,
      };
    } else {
      return {
        type: "Interval",
        value: `Every ${schedule.interval_value} ${schedule.interval_unit}`,
        icon: <Clock className="h-3 w-3" />,
      };
    }
  };

  const scheduleDisplay = getScheduleDisplay();

  // Format next run time
  const getNextRunDisplay = () => {
    if (!schedule.next_run_at) return "Not scheduled";
    try {
      const nextRun = new Date(schedule.next_run_at);
      return formatDistanceToNow(nextRun, { addSuffix: true });
    } catch {
      return "Invalid date";
    }
  };

  // Format last run time
  const getLastRunDisplay = () => {
    if (!schedule.last_run_at) return "Never";
    try {
      const lastRun = new Date(schedule.last_run_at);
      return format(lastRun, "MMM d, h:mm a");
    } catch {
      return "Invalid date";
    }
  };

  // Status badge
  const getStatusBadge = () => {
    if (!schedule.enabled) {
      return (
        <Badge variant="outline" className="text-xs bg-gray-500/10 text-gray-400 border-gray-500/30">
          <Pause className="h-3 w-3 mr-1" />
          Disabled
        </Badge>
      );
    }

    if (schedule.last_run_status === "success") {
      return (
        <Badge variant="outline" className="text-xs bg-green-500/10 text-green-400 border-green-500/30">
          ✓ Healthy
        </Badge>
      );
    }

    if (schedule.last_run_status === "failed") {
      return (
        <Badge variant="outline" className="text-xs bg-red-500/10 text-red-400 border-red-500/30">
          ✗ Failed
        </Badge>
      );
    }

    return (
      <Badge variant="outline" className="text-xs bg-blue-500/10 text-blue-400 border-blue-500/30">
        <Play className="h-3 w-3 mr-1" />
          Active
        </Badge>
    );
  };

  return (
    <div className="p-4 bg-[var(--mc-bg-primary)] border border-[var(--mc-border)] rounded-lg hover:bg-[var(--mc-bg-secondary)] transition-colors">
      <div className="space-y-3">
        {/* Header */}
        <div className="flex items-start justify-between gap-3">
          <div className="flex-1 space-y-1">
            <div className="flex items-center gap-2">
              {getStatusBadge()}
              <Badge
                variant="outline"
                className="text-xs bg-purple-500/10 text-purple-400 border-purple-500/30"
              >
                {scheduleDisplay.icon}
                <span className="ml-1">{scheduleDisplay.type}</span>
              </Badge>
            </div>

            <div className="font-mono text-sm text-[var(--mc-text-primary)]">
              {schedule.command_text}
            </div>

            {schedule.description && (
              <div className="text-xs text-[var(--mc-text-secondary)]">
                {schedule.description}
              </div>
            )}
          </div>

          {/* Actions */}
          <div className="flex items-center gap-1">
            <Button
              onClick={() => onEdit(schedule)}
              size="sm"
              variant="ghost"
              className="h-7 w-7 p-0 hover:bg-[var(--mc-border)]"
              title="Edit"
            >
              <Edit className="h-3 w-3 text-[var(--mc-text-secondary)] hover:text-[var(--mc-accent-blue)]" />
            </Button>

            <Button
              onClick={() => onToggleEnabled(schedule.id, !schedule.enabled)}
              size="sm"
              variant="ghost"
              className="h-7 w-7 p-0 hover:bg-[var(--mc-border)]"
              title={schedule.enabled ? "Disable" : "Enable"}
            >
              {schedule.enabled ? (
                <Pause className="h-3 w-3 text-[var(--mc-text-secondary)] hover:text-yellow-400" />
              ) : (
                <Play className="h-3 w-3 text-[var(--mc-text-secondary)] hover:text-green-400" />
              )}
            </Button>

            <Button
              onClick={() => onRunNow(schedule.id)}
              size="sm"
              variant="ghost"
              className="h-7 w-7 p-0 hover:bg-[var(--mc-border)]"
              title="Run Now"
              disabled={!schedule.enabled}
            >
              <Play className="h-3 w-3 text-[var(--mc-text-secondary)] hover:text-[var(--mc-accent-blue)]" />
            </Button>

            <Button
              onClick={() => onViewHistory(schedule)}
              size="sm"
              variant="ghost"
              className="h-7 w-7 p-0 hover:bg-[var(--mc-border)]"
              title="View History"
            >
              <History className="h-3 w-3 text-[var(--mc-text-secondary)] hover:text-purple-400" />
            </Button>

            <Button
              onClick={() => onDelete(schedule.id)}
              size="sm"
              variant="ghost"
              className="h-7 w-7 p-0 hover:bg-[var(--mc-border)]"
              title="Delete"
            >
              <Trash2 className="h-3 w-3 text-[var(--mc-text-secondary)] hover:text-red-400" />
            </Button>
          </div>
        </div>

        {/* Schedule Details */}
        <div className="grid grid-cols-2 gap-3 text-xs">
          <div>
            <div className="text-[var(--mc-text-tertiary)]">Schedule</div>
            <div className="text-[var(--mc-text-primary)] font-mono">
              {scheduleDisplay.value}
            </div>
            {schedule.schedule_type === "cron" && schedule.timezone && (
              <div className="text-[var(--mc-text-tertiary)]">
                {schedule.timezone}
              </div>
            )}
          </div>

          <div>
            <div className="text-[var(--mc-text-tertiary)]">Next Run</div>
            <div className="text-[var(--mc-text-primary)]">
              {getNextRunDisplay()}
            </div>
          </div>
        </div>

        {/* Last Run */}
        {schedule.last_run_at && (
          <div className="pt-2 border-t border-[var(--mc-border)] text-xs">
            <span className="text-[var(--mc-text-tertiary)]">Last run:</span>{" "}
            <span className="text-[var(--mc-text-primary)]">{getLastRunDisplay()}</span>
            {schedule.last_run_status && (
              <span className={`ml-2 ${
                schedule.last_run_status === "success" ? "text-green-400" : "text-red-400"
              }`}>
                ({schedule.last_run_status})
              </span>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
