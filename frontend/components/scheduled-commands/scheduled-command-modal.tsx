"use client";

import { useState, useEffect } from "react";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Badge } from "@/components/ui/badge";
import {
  useScheduledCommands,
  ScheduledCommand,
  ScheduledCommandCreate,
  ScheduledCommandUpdate,
} from "@/lib/hooks/use-scheduled-commands";
import { Calendar, Clock, Info, AlertCircle } from "lucide-react";

interface ScheduledCommandModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  agentId: string;
  agentNickname: string;
  schedule: ScheduledCommand | null;
  isCreating: boolean;
  onSuccess: () => void;
}

// Common timezones
const COMMON_TIMEZONES = [
  "UTC",
  "America/New_York",
  "America/Chicago",
  "America/Denver",
  "America/Los_Angeles",
  "America/Toronto",
  "America/Vancouver",
  "Europe/London",
  "Europe/Paris",
  "Europe/Berlin",
  "Asia/Tokyo",
  "Asia/Shanghai",
  "Asia/Singapore",
  "Australia/Sydney",
];

export function ScheduledCommandModal({
  open,
  onOpenChange,
  agentId,
  agentNickname,
  schedule,
  isCreating,
  onSuccess,
}: ScheduledCommandModalProps) {
  const { createSchedule, updateSchedule, isLoading, error } = useScheduledCommands();

  // Form state
  const [scheduleType, setScheduleType] = useState<"cron" | "interval">("interval");
  const [commandText, setCommandText] = useState("");
  const [description, setDescription] = useState("");

  // Cron fields
  const [cronExpression, setCronExpression] = useState("");
  const [timezone, setTimezone] = useState("UTC");

  // Interval fields
  const [intervalValue, setIntervalValue] = useState(5);
  const [intervalUnit, setIntervalUnit] = useState<"minutes" | "hours" | "days">("minutes");

  // Advanced options
  const [showAdvanced, setShowAdvanced] = useState(false);
  const [maxRetries, setMaxRetries] = useState(3);
  const [retryDelayMinutes, setRetryDelayMinutes] = useState(5);
  const [timeoutSeconds, setTimeoutSeconds] = useState(300);
  const [enabled, setEnabled] = useState(true);

  const [validationError, setValidationError] = useState<string | null>(null);

  // Load existing schedule data
  useEffect(() => {
    if (schedule && !isCreating) {
      setScheduleType(schedule.schedule_type);
      setCommandText(schedule.command_text);
      setDescription(schedule.description || "");

      if (schedule.schedule_type === "cron") {
        setCronExpression(schedule.cron_expression || "");
        setTimezone(schedule.timezone || "UTC");
      } else {
        setIntervalValue(schedule.interval_value || 5);
        setIntervalUnit(schedule.interval_unit || "minutes");
      }

      setMaxRetries(schedule.max_retries);
      setRetryDelayMinutes(schedule.retry_delay_minutes);
      setTimeoutSeconds(schedule.timeout_seconds);
      setEnabled(schedule.enabled);
    } else {
      // Reset for new schedule
      setCommandText(`@${agentNickname} `);
    }
  }, [schedule, isCreating, agentNickname]);

  const validateForm = (): boolean => {
    setValidationError(null);

    if (!commandText.trim()) {
      setValidationError("Command text is required");
      return false;
    }

    if (scheduleType === "cron") {
      if (!cronExpression.trim()) {
        setValidationError("Cron expression is required");
        return false;
      }
      // Basic cron validation (5 fields)
      const parts = cronExpression.trim().split(/\s+/);
      if (parts.length !== 5) {
        setValidationError("Cron expression must have 5 fields (minute hour day month weekday)");
        return false;
      }
    } else {
      if (intervalValue < 5) {
        setValidationError("Minimum interval is 5 minutes");
        return false;
      }
      if (intervalValue > 1440 && intervalUnit === "minutes") {
        setValidationError("Maximum interval is 1440 minutes (24 hours)");
        return false;
      }
    }

    return true;
  };

  const handleSubmit = async () => {
    if (!validateForm()) {
      return;
    }

    if (isCreating) {
      // Create new schedule
      const data: ScheduledCommandCreate = {
        command_text: commandText.trim(),
        agent_id: agentId,
        schedule_type: scheduleType,
        description: description.trim() || undefined,
        enabled,
        max_retries: maxRetries,
        retry_delay_minutes: retryDelayMinutes,
        timeout_seconds: timeoutSeconds,
      };

      if (scheduleType === "cron") {
        data.cron_expression = cronExpression.trim();
        data.timezone = timezone;
      } else {
        data.interval_value = intervalValue;
        data.interval_unit = intervalUnit;
      }

      const result = await createSchedule(data);
      if (result) {
        onSuccess();
      }
    } else if (schedule) {
      // Update existing schedule
      const data: ScheduledCommandUpdate = {
        command_text: commandText.trim(),
        schedule_type: scheduleType,
        description: description.trim() || undefined,
        enabled,
        max_retries: maxRetries,
        retry_delay_minutes: retryDelayMinutes,
        timeout_seconds: timeoutSeconds,
      };

      if (scheduleType === "cron") {
        data.cron_expression = cronExpression.trim();
        data.timezone = timezone;
      } else {
        data.interval_value = intervalValue;
        data.interval_unit = intervalUnit;
      }

      const result = await updateSchedule(schedule.id, data);
      if (result) {
        onSuccess();
      }
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-2xl max-h-[85vh] overflow-y-auto bg-[var(--mc-bg-secondary)] border-[var(--mc-border)]">
        <DialogHeader>
          <DialogTitle className="text-[var(--mc-text-primary)] text-xl">
            {isCreating ? "Create New Schedule" : "Edit Schedule"} - @{agentNickname}
          </DialogTitle>
        </DialogHeader>

        <div className="space-y-4">
          {/* Command Text */}
          <div className="space-y-2">
            <Label htmlFor="command" className="text-[var(--mc-text-primary)]">
              Command
            </Label>
            <Input
              id="command"
              value={commandText}
              onChange={(e) => setCommandText(e.target.value)}
              placeholder={`@${agentNickname} check for updates`}
              className="bg-[var(--mc-bg-primary)] border-[var(--mc-border)] text-[var(--mc-text-primary)] font-mono"
            />
          </div>

          {/* Description */}
          <div className="space-y-2">
            <Label htmlFor="description" className="text-[var(--mc-text-primary)]">
              Description (Optional)
            </Label>
            <Input
              id="description"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="Daily health check"
              className="bg-[var(--mc-bg-primary)] border-[var(--mc-border)] text-[var(--mc-text-primary)]"
            />
          </div>

          {/* Schedule Type Toggle */}
          <div className="space-y-2">
            <Label className="text-[var(--mc-text-primary)]">Schedule Type</Label>
            <div className="flex gap-2">
              <Button
                type="button"
                variant={scheduleType === "interval" ? "default" : "outline"}
                onClick={() => setScheduleType("interval")}
                className={
                  scheduleType === "interval"
                    ? "bg-[var(--mc-accent-blue)] text-white"
                    : "border-[var(--mc-border)]"
                }
              >
                <Clock className="h-4 w-4 mr-2" />
                Interval
              </Button>
              <Button
                type="button"
                variant={scheduleType === "cron" ? "default" : "outline"}
                onClick={() => setScheduleType("cron")}
                className={
                  scheduleType === "cron"
                    ? "bg-[var(--mc-accent-blue)] text-white"
                    : "border-[var(--mc-border)]"
                }
              >
                <Calendar className="h-4 w-4 mr-2" />
                Cron
              </Button>
            </div>
          </div>

          {/* Interval Schedule */}
          {scheduleType === "interval" && (
            <div className="space-y-3 p-4 bg-[var(--mc-bg-primary)] rounded-lg border border-[var(--mc-border)]">
              <div className="flex items-center gap-2 text-sm text-[var(--mc-text-secondary)]">
                <Info className="h-4 w-4" />
                Run every...
              </div>
              <div className="flex gap-2">
                <Input
                  type="number"
                  min={5}
                  value={intervalValue}
                  onChange={(e) => setIntervalValue(parseInt(e.target.value) || 5)}
                  className="bg-[var(--mc-bg-secondary)] border-[var(--mc-border)] text-[var(--mc-text-primary)] w-24"
                />
                <select
                  value={intervalUnit}
                  onChange={(e) => setIntervalUnit(e.target.value as any)}
                  className="flex-1 bg-[var(--mc-bg-secondary)] border border-[var(--mc-border)] rounded px-3 py-2 text-[var(--mc-text-primary)]"
                >
                  <option value="minutes">Minutes</option>
                  <option value="hours">Hours</option>
                  <option value="days">Days</option>
                </select>
              </div>
              {intervalValue < 5 && (
                <div className="text-xs text-red-400 flex items-center gap-1">
                  <AlertCircle className="h-3 w-3" />
                  Minimum interval is 5 minutes
                </div>
              )}
            </div>
          )}

          {/* Cron Schedule */}
          {scheduleType === "cron" && (
            <div className="space-y-3 p-4 bg-[var(--mc-bg-primary)] rounded-lg border border-[var(--mc-border)]">
              <div className="space-y-2">
                <Label htmlFor="cron" className="text-[var(--mc-text-primary)]">
                  Cron Expression
                </Label>
                <Input
                  id="cron"
                  value={cronExpression}
                  onChange={(e) => setCronExpression(e.target.value)}
                  placeholder="0 9 * * 1-5"
                  className="bg-[var(--mc-bg-secondary)] border-[var(--mc-border)] text-[var(--mc-text-primary)] font-mono"
                />
                <div className="text-xs text-[var(--mc-text-tertiary)]">
                  Format: minute hour day month weekday (e.g., "0 9 * * 1-5" = 9am weekdays)
                </div>
              </div>

              <div className="space-y-2">
                <Label htmlFor="timezone" className="text-[var(--mc-text-primary)]">
                  Timezone
                </Label>
                <select
                  id="timezone"
                  value={timezone}
                  onChange={(e) => setTimezone(e.target.value)}
                  className="w-full bg-[var(--mc-bg-secondary)] border border-[var(--mc-border)] rounded px-3 py-2 text-[var(--mc-text-primary)]"
                >
                  {COMMON_TIMEZONES.map((tz) => (
                    <option key={tz} value={tz}>
                      {tz}
                    </option>
                  ))}
                </select>
              </div>

              {/* Cron examples */}
              <div className="space-y-1 text-xs text-[var(--mc-text-tertiary)]">
                <div className="font-semibold">Examples:</div>
                <div>• "0 9 * * *" - Every day at 9:00 AM</div>
                <div>• "0 9 * * 1-5" - Weekdays at 9:00 AM</div>
                <div>• "*/30 * * * *" - Every 30 minutes</div>
                <div>• "0 0 * * 0" - Every Sunday at midnight</div>
              </div>
            </div>
          )}

          {/* Advanced Options */}
          <div className="space-y-2">
            <button
              type="button"
              onClick={() => setShowAdvanced(!showAdvanced)}
              className="text-sm text-[var(--mc-accent-blue)] hover:underline"
            >
              {showAdvanced ? "Hide" : "Show"} Advanced Options
            </button>

            {showAdvanced && (
              <div className="space-y-3 p-4 bg-[var(--mc-bg-primary)] rounded-lg border border-[var(--mc-border)]">
                <div className="grid grid-cols-3 gap-3">
                  <div className="space-y-1">
                    <Label htmlFor="retries" className="text-xs text-[var(--mc-text-primary)]">
                      Max Retries
                    </Label>
                    <Input
                      id="retries"
                      type="number"
                      min={0}
                      max={10}
                      value={maxRetries}
                      onChange={(e) => setMaxRetries(parseInt(e.target.value) || 3)}
                      className="bg-[var(--mc-bg-secondary)] border-[var(--mc-border)] text-[var(--mc-text-primary)]"
                    />
                  </div>

                  <div className="space-y-1">
                    <Label htmlFor="delay" className="text-xs text-[var(--mc-text-primary)]">
                      Retry Delay (min)
                    </Label>
                    <Input
                      id="delay"
                      type="number"
                      min={1}
                      value={retryDelayMinutes}
                      onChange={(e) => setRetryDelayMinutes(parseInt(e.target.value) || 5)}
                      className="bg-[var(--mc-bg-secondary)] border-[var(--mc-border)] text-[var(--mc-text-primary)]"
                    />
                  </div>

                  <div className="space-y-1">
                    <Label htmlFor="timeout" className="text-xs text-[var(--mc-text-primary)]">
                      Timeout (sec)
                    </Label>
                    <Input
                      id="timeout"
                      type="number"
                      min={60}
                      value={timeoutSeconds}
                      onChange={(e) => setTimeoutSeconds(parseInt(e.target.value) || 300)}
                      className="bg-[var(--mc-bg-secondary)] border-[var(--mc-border)] text-[var(--mc-text-primary)]"
                    />
                  </div>
                </div>

                <div className="flex items-center gap-2">
                  <input
                    type="checkbox"
                    id="enabled"
                    checked={enabled}
                    onChange={(e) => setEnabled(e.target.checked)}
                    className="rounded"
                  />
                  <Label htmlFor="enabled" className="text-sm text-[var(--mc-text-primary)] cursor-pointer">
                    Enable schedule immediately
                  </Label>
                </div>
              </div>
            )}
          </div>

          {/* Validation Error */}
          {validationError && (
            <div className="p-3 bg-red-500/10 border border-red-500/30 rounded text-sm text-red-400 flex items-center gap-2">
              <AlertCircle className="h-4 w-4" />
              {validationError}
            </div>
          )}

          {/* API Error */}
          {error && (
            <div className="p-3 bg-red-500/10 border border-red-500/30 rounded text-sm text-red-400">
              {error}
            </div>
          )}

          {/* Actions */}
          <div className="flex justify-end gap-2 pt-4 border-t border-[var(--mc-border)]">
            <Button
              onClick={() => onOpenChange(false)}
              variant="outline"
              className="border-[var(--mc-border)] text-[var(--mc-text-primary)]"
              disabled={isLoading}
            >
              Cancel
            </Button>
            <Button
              onClick={handleSubmit}
              className="bg-[var(--mc-accent-blue)] hover:opacity-90 text-white"
              disabled={isLoading}
            >
              {isLoading ? "Saving..." : isCreating ? "Create Schedule" : "Update Schedule"}
            </Button>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
}
