"use client";

import { useState, useEffect } from "react";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { useScheduledCommands, ScheduledCommand } from "@/lib/hooks/use-scheduled-commands";
import { ScheduledCommandCard } from "./scheduled-command-card";
import { ScheduledCommandModal } from "./scheduled-command-modal";
import { ExecutionHistoryModal } from "./execution-history-modal";
import { Plus, Clock, AlertCircle } from "lucide-react";

interface ScheduledCommandListProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  agentId: string;
  agentNickname: string;
  agentName: string;
}

export function ScheduledCommandList({
  open,
  onOpenChange,
  agentId,
  agentNickname,
  agentName,
}: ScheduledCommandListProps) {
  const {
    schedules,
    isLoading,
    error,
    fetchSchedules,
    deleteSchedule,
    enableSchedule,
    disableSchedule,
    executeScheduleNow,
  } = useScheduledCommands(agentId);

  const [selectedSchedule, setSelectedSchedule] = useState<ScheduledCommand | null>(null);
  const [showEditor, setShowEditor] = useState(false);
  const [isCreating, setIsCreating] = useState(false);
  const [showHistory, setShowHistory] = useState(false);
  const [historySchedule, setHistorySchedule] = useState<ScheduledCommand | null>(null);

  // Fetch schedules when modal opens
  useEffect(() => {
    if (open) {
      fetchSchedules({ agent_id: agentId });
    }
  }, [open, agentId, fetchSchedules]);

  const handleCreateNew = () => {
    setSelectedSchedule(null);
    setIsCreating(true);
    setShowEditor(true);
  };

  const handleEditSchedule = (schedule: ScheduledCommand) => {
    setSelectedSchedule(schedule);
    setIsCreating(false);
    setShowEditor(true);
  };

  const handleDeleteSchedule = async (scheduleId: string) => {
    if (confirm("Are you sure you want to delete this schedule? This action cannot be undone.")) {
      const success = await deleteSchedule(scheduleId);
      if (success) {
        // Refresh list
        fetchSchedules({ agent_id: agentId });
      }
    }
  };

  const handleToggleEnabled = async (scheduleId: string, enabled: boolean) => {
    if (enabled) {
      await enableSchedule(scheduleId);
    } else {
      await disableSchedule(scheduleId);
    }
    // Refresh list
    fetchSchedules({ agent_id: agentId });
  };

  const handleRunNow = async (scheduleId: string) => {
    const success = await executeScheduleNow(scheduleId);
    if (success) {
      // Success! Task will appear in Mission Control
      console.log("Schedule executed successfully");
    }
  };

  const handleViewHistory = (schedule: ScheduledCommand) => {
    setHistorySchedule(schedule);
    setShowHistory(true);
  };

  const handleEditorClose = () => {
    setShowEditor(false);
    setSelectedSchedule(null);
    setIsCreating(false);
    // Refresh list
    fetchSchedules({ agent_id: agentId });
  };

  // Calculate stats
  const activeSchedules = schedules.filter((s) => s.enabled).length;
  const totalSchedules = schedules.length;

  return (
    <>
      <Dialog open={open} onOpenChange={onOpenChange}>
        <DialogContent className="max-w-5xl max-h-[85vh] overflow-y-auto bg-[var(--mc-bg-secondary)] border-[var(--mc-border)]">
          <DialogHeader>
            <DialogTitle className="text-[var(--mc-text-primary)] text-xl flex items-center gap-2">
              <Clock className="h-5 w-5 text-[var(--mc-accent-blue)]" />
              Scheduled Commands - @{agentNickname} ({agentName})
            </DialogTitle>
          </DialogHeader>

          {/* Stats & Actions */}
          <div className="flex items-center justify-between gap-4 pb-3 border-b border-[var(--mc-border)]">
            <div className="flex items-center gap-2">
              <Badge
                variant="outline"
                className="text-xs bg-green-500/10 text-green-400 border-green-500/30"
              >
                {activeSchedules} active
              </Badge>
              <Badge
                variant="outline"
                className="text-xs bg-gray-500/10 text-gray-400 border-gray-500/30"
              >
                {totalSchedules} total
              </Badge>
              {totalSchedules >= 50 && (
                <Badge
                  variant="outline"
                  className="text-xs bg-red-500/10 text-red-400 border-red-500/30"
                >
                  <AlertCircle className="h-3 w-3 mr-1" />
                  Limit reached
                </Badge>
              )}
            </div>

            <Button
              onClick={handleCreateNew}
              className="bg-[var(--mc-accent-blue)] hover:opacity-90 text-white"
              disabled={totalSchedules >= 50}
            >
              <Plus className="h-4 w-4 mr-2" />
              New Schedule
            </Button>
          </div>

          {/* Schedule List */}
          <div className="space-y-3 min-h-[300px]">
            {isLoading && (
              <div className="text-center py-8 text-[var(--mc-text-secondary)]">
                Loading schedules...
              </div>
            )}

            {error && (
              <div className="text-center py-8 text-red-400">
                Error: {error}
              </div>
            )}

            {!isLoading && !error && schedules.length === 0 && (
              <div className="text-center py-12 space-y-2">
                <Clock className="h-12 w-12 mx-auto text-[var(--mc-text-tertiary)] opacity-50" />
                <div className="text-[var(--mc-text-secondary)]">
                  No schedules yet for @{agentNickname}
                </div>
                <div className="text-xs text-[var(--mc-text-tertiary)]">
                  Click "New Schedule" to create one
                </div>
              </div>
            )}

            {!isLoading &&
              !error &&
              schedules.map((schedule) => (
                <ScheduledCommandCard
                  key={schedule.id}
                  schedule={schedule}
                  onEdit={handleEditSchedule}
                  onDelete={handleDeleteSchedule}
                  onToggleEnabled={handleToggleEnabled}
                  onRunNow={handleRunNow}
                  onViewHistory={handleViewHistory}
                />
              ))}
          </div>

          {/* Footer */}
          <div className="flex justify-between items-center pt-4 border-t border-[var(--mc-border)]">
            <div className="text-xs text-[var(--mc-text-tertiary)]">
              Min interval: 5 minutes • Max schedules: 50 per user
            </div>
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

      {/* Editor Modal (nested) */}
      {showEditor && (
        <ScheduledCommandModal
          open={showEditor}
          onOpenChange={setShowEditor}
          agentId={agentId}
          agentNickname={agentNickname}
          schedule={selectedSchedule}
          isCreating={isCreating}
          onSuccess={handleEditorClose}
        />
      )}

      {/* Execution History Modal (nested) */}
      {showHistory && historySchedule && (
        <ExecutionHistoryModal
          open={showHistory}
          onOpenChange={setShowHistory}
          schedule={historySchedule}
        />
      )}
    </>
  );
}
