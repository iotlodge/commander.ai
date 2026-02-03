"use client";

import { useState } from "react";
import { AgentTask, TaskStatus } from "@/lib/types";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { Button } from "@/components/ui/button";
import { formatDistanceToNow } from "date-fns";
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
    await fetch(`http://localhost:8000/api/tasks/${taskId}`, {
      method: 'DELETE',
    });
  } catch (error) {
    console.error('Failed to remove task:', error);
  }
}

export function TaskCard({ task }: TaskCardProps) {
  const { removeTask: removeTaskFromStore } = useTaskStore();
  const [showResults, setShowResults] = useState(false);

  const handleRemove = async () => {
    await removeTask(task.id);
    removeTaskFromStore(task.id);
  };

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
        <p className="text-sm mb-3 text-gray-300">{task.command_text}</p>

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

        {/* Metrics Section - Basic placeholders */}
        {(task.status === TaskStatus.IN_PROGRESS || task.status === TaskStatus.COMPLETED) && (
          <div className="grid grid-cols-3 gap-2 mb-3 pb-3 border-b border-[#3a4454]">
            <div className="text-center">
              <div className="text-xs text-gray-500">Tool Calls</div>
              <div className="text-sm font-semibold text-gray-300">
                {task.tool_calls_count ?? 0}
              </div>
            </div>
            <div className="text-center">
              <div className="text-xs text-gray-500">Agent Calls</div>
              <div className="text-sm font-semibold text-gray-300">
                {task.agent_calls_count ?? 0}
              </div>
            </div>
            <div className="text-center">
              <div className="text-xs text-gray-500">Tokens</div>
              <div className="text-sm font-semibold text-gray-300">
                {task.total_tokens?.toLocaleString() ?? 0}
              </div>
            </div>
          </div>
        )}
        {/* TODO: Wire up backend instrumentation to track actual metrics */}

        {/* Results Button for Completed/Failed Tasks */}
        {(task.status === TaskStatus.COMPLETED || task.status === TaskStatus.FAILED) && (
          <div className="pt-3 border-t border-[#3a4454]">
            <Button
              onClick={() => setShowResults(true)}
              variant="outline"
              size="sm"
              className="w-full gap-2 text-[#4a9eff] border-[#4a9eff]/30 hover:bg-[#4a9eff]/10"
            >
              <FileText className="h-4 w-4" />
              View Results
            </Button>
          </div>
        )}

        {/* Timestamps */}
        <div className="flex justify-between text-xs text-gray-500 pt-2 border-t border-[#3a4454] mt-3">
          <span>
            Created {formatDistanceToNow(new Date(task.created_at), { addSuffix: true })}
          </span>
          {task.completed_at && (
            <span>
              Completed {formatDistanceToNow(new Date(task.completed_at), { addSuffix: true })}
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
