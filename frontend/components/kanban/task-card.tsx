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
  [TaskStatus.QUEUED]: "bg-gray-100 text-gray-800",
  [TaskStatus.IN_PROGRESS]: "bg-blue-100 text-blue-800",
  [TaskStatus.TOOL_CALL]: "bg-purple-100 text-purple-800",
  [TaskStatus.COMPLETED]: "bg-green-100 text-green-800",
  [TaskStatus.FAILED]: "bg-red-100 text-red-800",
};

export function TaskCard({ task }: TaskCardProps) {
  return (
    <Card className="mb-3 hover:shadow-md transition-shadow">
      <CardHeader className="pb-3">
        <div className="flex items-start justify-between">
          <div className="flex items-center gap-2">
            <Avatar className="h-8 w-8">
              <AvatarFallback className="text-xs bg-blue-500 text-white">
                {task.agent_nickname.slice(0, 2).toUpperCase()}
              </AvatarFallback>
            </Avatar>
            <div>
              <CardTitle className="text-sm font-medium">
                @{task.agent_nickname}
              </CardTitle>
              <p className="text-xs text-muted-foreground">
                {task.agent_id}
              </p>
            </div>
          </div>
          <Badge variant="secondary" className={cn("text-xs", statusColors[task.status])}>
            {task.status.replace("_", " ")}
          </Badge>
        </div>
      </CardHeader>

      <CardContent>
        <p className="text-sm mb-3">{task.command_text}</p>

        {/* Progress bar */}
        {task.status === TaskStatus.IN_PROGRESS && (
          <div className="mb-3">
            <div className="flex justify-between text-xs text-muted-foreground mb-1">
              <span>{task.current_node || "Processing"}</span>
              <span>{task.progress_percentage}%</span>
            </div>
            <div className="w-full bg-gray-200 rounded-full h-2">
              <div
                className="bg-blue-500 h-2 rounded-full transition-all duration-300"
                style={{ width: `${task.progress_percentage}%` }}
              />
            </div>
          </div>
        )}

        {/* Consultation indicator */}
        {task.status === TaskStatus.TOOL_CALL && task.consultation_target_nickname && (
          <Badge variant="outline" className="text-xs mb-2">
            Consulting @{task.consultation_target_nickname}
          </Badge>
        )}

        {/* Timestamps */}
        <div className="flex justify-between text-xs text-muted-foreground pt-2 border-t">
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
