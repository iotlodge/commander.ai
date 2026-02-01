"use client";

import { TaskStatus, AgentTask } from "@/lib/types";
import { TaskCard } from "./task-card";

interface KanbanColumnProps {
  status: TaskStatus;
  tasks: AgentTask[];
  count: number;
}

const statusConfig = {
  [TaskStatus.QUEUED]: {
    title: "Queued",
    color: "bg-gray-100 border-gray-300",
  },
  [TaskStatus.IN_PROGRESS]: {
    title: "In Progress",
    color: "bg-blue-50 border-blue-300",
  },
  [TaskStatus.TOOL_CALL]: {
    title: "Tool Call",
    color: "bg-purple-50 border-purple-300",
  },
  [TaskStatus.COMPLETED]: {
    title: "Completed",
    color: "bg-green-50 border-green-300",
  },
  [TaskStatus.FAILED]: {
    title: "Failed",
    color: "bg-red-50 border-red-300",
  },
};

export function KanbanColumn({ status, tasks, count }: KanbanColumnProps) {
  const config = statusConfig[status];

  return (
    <div className="flex-1 min-w-[300px]">
      <div className={`rounded-lg border-2 ${config.color} p-4 h-full`}>
        <div className="flex items-center justify-between mb-4">
          <h2 className="font-semibold text-lg">{config.title}</h2>
          <span className="text-sm text-muted-foreground bg-white px-2 py-1 rounded-full">
            {count}
          </span>
        </div>

        <div className="space-y-3 max-h-[calc(100vh-200px)] overflow-y-auto">
          {tasks.length === 0 ? (
            <p className="text-sm text-muted-foreground text-center py-8">
              No tasks
            </p>
          ) : (
            tasks.map((task) => <TaskCard key={task.id} task={task} />)
          )}
        </div>
      </div>
    </div>
  );
}
