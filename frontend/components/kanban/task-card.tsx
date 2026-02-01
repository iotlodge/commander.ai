"use client";

import { AgentTask, TaskStatus } from "@/lib/types";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { formatDistanceToNow } from "date-fns";
import { cn } from "@/lib/utils";

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

export function TaskCard({ task }: TaskCardProps) {
  return (
    <Card className="mb-3 hover:shadow-lg transition-shadow bg-[#1e2433] border-[#3a4454]">
      <CardHeader className="pb-3">
        <div className="flex items-start justify-between">
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
          <Badge variant="secondary" className={cn("text-xs border", statusColors[task.status])}>
            {task.status.replace("_", " ")}
          </Badge>
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

        {/* Timestamps */}
        <div className="flex justify-between text-xs text-gray-500 pt-2 border-t border-[#3a4454]">
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
    </Card>
  );
}
