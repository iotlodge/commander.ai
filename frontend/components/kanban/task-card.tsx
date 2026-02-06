"use client";

import { useState, useEffect } from "react";
import { AgentTask, TaskStatus } from "@/lib/types";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { Button } from "@/components/ui/button";
import { formatDistanceToNow, formatDistance } from "date-fns";
import { cn } from "@/lib/utils";
import { X, FileText } from "lucide-react";
import { useTaskStore } from "@/lib/store";
import { TaskResultsModal } from "./task-results-modal";

interface TaskCardProps {
  task: AgentTask;
}

const statusColors = {
  [TaskStatus.QUEUED]: "bg-gray-500/20 text-gray-300 border-gray-500/30",
  [TaskStatus.IN_PROGRESS]: "bg-[#4a9eff]/20 text-[#4a9eff] border-[#4a9eff]/30",
  [TaskStatus.TOOL_CALL]: "bg-purple-500/20 text-purple-400 border-purple-500/30",
  [TaskStatus.COMPLETED]: "bg-green-500/20 text-green-400 border-green-500/30",
  [TaskStatus.FAILED]: "bg-red-500/20 text-red-400 border-red-500/30",
};

async function removeTask(taskId: string) {
  try {
    await fetch(`http://localhost:8000/api/tasks/${taskId}?user_id=00000000-0000-0000-0000-000000000001`, {
      method: 'DELETE',
    });
  } catch (error) {
    console.error('Failed to remove task:', error);
  }
}

export function TaskCard({ task }: TaskCardProps) {
  const { removeTask: removeTaskFromStore } = useTaskStore();
  const [showResults, setShowResults] = useState(false);
  const [currentTime, setCurrentTime] = useState(new Date());

  // Update current time every second for live duration display
  useEffect(() => {
    if (task.status === TaskStatus.IN_PROGRESS && task.started_at) {
      const interval = setInterval(() => {
        setCurrentTime(new Date());
      }, 1000);
      return () => clearInterval(interval);
    }
  }, [task.status, task.started_at]);

  const handleRemove = async () => {
    await removeTask(task.id);
    removeTaskFromStore(task.id);
  };

  // Calculate execution duration
  const getDuration = () => {
    if (task.status === TaskStatus.QUEUED || !task.started_at) {
      return null;
    }

    const start = new Date(task.started_at);
    const end = task.completed_at ? new Date(task.completed_at) : currentTime;
    const diffMs = end.getTime() - start.getTime();
    const diffSec = Math.floor(diffMs / 1000);

    // Format duration for better precision on short executions
    if (diffSec < 1) {
      return "less than a second";
    } else if (diffSec < 60) {
      return `${diffSec} second${diffSec !== 1 ? 's' : ''}`;
    } else if (diffSec < 3600) {
      const minutes = Math.floor(diffSec / 60);
      const seconds = diffSec % 60;
      return seconds > 0
        ? `${minutes} minute${minutes !== 1 ? 's' : ''} ${seconds} second${seconds !== 1 ? 's' : ''}`
        : `${minutes} minute${minutes !== 1 ? 's' : ''}`;
    } else {
      // For longer durations, use date-fns formatDistance
      return formatDistance(start, end, { includeSeconds: true });
    }
  };

  const duration = getDuration();

  return (
    <Card className="mb-3 hover:shadow-lg transition-shadow bg-[#1e2433] border-[#3a4454]">
      <CardHeader className="pb-3">
        <div className="flex items-start justify-between gap-2">
          <div className="flex items-center gap-2">
            <Avatar className="h-8 w-8">
              <AvatarFallback className="text-xs bg-[#4a9eff] text-white">
                {task.agent_nickname.slice(0, 2).toUpperCase()}
              </AvatarFallback>
            </Avatar>
            <div>
              <CardTitle className="text-sm font-medium text-white">
                @{task.agent_nickname}
              </CardTitle>
              <p className="text-xs text-gray-500">
                {task.agent_id}
              </p>
            </div>
          </div>
          <div className="flex items-center gap-1">
            <Badge variant="secondary" className={cn("text-xs border", statusColors[task.status])}>
              {task.status.replace("_", " ")}
            </Badge>
            {task.status === TaskStatus.QUEUED && (
              <Button
                variant="ghost"
                size="sm"
                onClick={handleRemove}
                className="h-6 w-6 p-0 text-red-400 hover:text-red-300 hover:bg-red-500/10"
              >
                <X className="h-4 w-4" />
              </Button>
            )}
          </div>
        </div>
      </CardHeader>

      <CardContent>
        <p className="text-sm mb-3 text-gray-300">
          {task.command_text.replace(/^@\w+\s*/, '')}
        </p>

        {/* Progress bar */}
        {task.status === TaskStatus.IN_PROGRESS && (
          <div className="mb-3">
            <div className="flex justify-between text-xs text-gray-400 mb-1">
              <span>{task.current_node || "Processing"}</span>
              <span>{task.progress_percentage}%</span>
            </div>
            <div className="w-full bg-[#2a3444] rounded-full h-2">
              <div
                className="bg-[#4a9eff] h-2 rounded-full transition-all duration-300"
                style={{ width: `${task.progress_percentage}%` }}
              />
            </div>
          </div>
        )}

        {/* Consultation indicator */}
        {task.status === TaskStatus.TOOL_CALL && task.consultation_target_nickname && (
          <Badge variant="outline" className="text-xs mb-2 border-purple-500/30 text-purple-400">
            Consulting @{task.consultation_target_nickname}
          </Badge>
        )}

        {/* Metrics Section - Live from execution_metrics */}
        {(task.status === TaskStatus.IN_PROGRESS || task.status === TaskStatus.COMPLETED) && (
          <div className="grid grid-cols-3 gap-2 mb-3 pb-3 border-b border-[#3a4454]">
            <div className="text-center">
              <div className="text-xs text-gray-500">LLM Calls</div>
              <div className="text-sm font-semibold text-gray-300">
                {task.metadata?.execution_metrics?.llm_calls ?? 0}
              </div>
            </div>
            <div className="text-center">
              <div className="text-xs text-gray-500">Agent Calls</div>
              <div className="text-sm font-semibold text-gray-300">
                {task.metadata?.execution_metrics?.agent_calls ?? 0}
              </div>
            </div>
            <div className="text-center">
              <div className="text-xs text-gray-500">Tokens</div>
              <div className="text-sm font-semibold text-gray-300">
                {task.metadata?.execution_metrics?.tokens?.total?.toLocaleString() ?? 0}
              </div>
            </div>
          </div>
        )}

        {/* Results Button for Completed Tasks */}
        {task.status === TaskStatus.COMPLETED && (
          <div className="pt-3 border-t border-[#3a4454]">
            <Button
              onClick={() => setShowResults(true)}
              variant="outline"
              size="sm"
              className="w-full gap-1.5 bg-green-500/10 hover:bg-green-500/20 text-green-400 border-green-500/30 h-8 text-xs"
            >
              <FileText className="h-3.5 w-3.5" />
              View Results
            </Button>
          </div>
        )}

        {/* Error Button for Failed Tasks */}
        {task.status === TaskStatus.FAILED && (
          <div className="pt-3 border-t border-[#3a4454]">
            <Button
              onClick={() => setShowResults(true)}
              variant="outline"
              size="sm"
              className="w-full gap-1.5 bg-red-500/10 hover:bg-red-500/20 text-red-400 border-red-500/30 h-8 text-xs"
            >
              <FileText className="h-3.5 w-3.5" />
              View Error
            </Button>
          </div>
        )}

        {/* Timestamps */}
        <div className="flex justify-between text-xs text-gray-500 pt-2 border-t border-[#3a4454] mt-3">
          {duration ? (
            <span className="text-blue-400 font-medium">
              Duration: {duration}
            </span>
          ) : (
            <span>
              Created {formatDistanceToNow(new Date(task.created_at), { addSuffix: true })}
            </span>
          )}
        </div>
      </CardContent>

      {/* Results Modal */}
      <TaskResultsModal
        task={task}
        isOpen={showResults}
        onClose={() => setShowResults(false)}
      />
    </Card>
  );
}
