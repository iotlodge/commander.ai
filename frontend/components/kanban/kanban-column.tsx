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
    color: "bg-[#2a3444] border-[#3a4454]",
    textColor: "text-gray-300",
  },
  [TaskStatus.IN_PROGRESS]: {
    title: "In Progress",
    color: "bg-[#2a3444] border-[#4a9eff]",
    textColor: "text-[#4a9eff]",
  },
  [TaskStatus.TOOL_CALL]: {
    title: "Feedback Requested",
    color: "bg-[#2a3444] border-[#a855f7]",
    textColor: "text-[#a855f7]",
  },
  [TaskStatus.COMPLETED]: {
    title: "Completed",
    color: "bg-[#2a3444] border-[#4ade80]",
    textColor: "text-[#4ade80]",
  },
  [TaskStatus.FAILED]: {
    title: "Failed",
    color: "bg-[#2a3444] border-[#ef4444]",
    textColor: "text-[#ef4444]",
  },
};

export function KanbanColumn({ status, tasks, count }: KanbanColumnProps) {
  const config = statusConfig[status];

  return (
    <div className="flex-shrink-0 w-[285px] h-full flex flex-col">
      <div className={`rounded-lg border-2 ${config.color} p-4 h-full flex flex-col`}>
        {/* Column Header */}
        <div className="flex-shrink-0 flex items-center justify-between mb-4">
          <h2 className={`font-semibold text-lg ${config.textColor}`}>{config.title}</h2>
          <span className="text-sm text-gray-400 bg-[#1e2433] px-2 py-1 rounded-full border border-[#3a4454]">
            {count}
          </span>
        </div>

        {/* Scrollable Task List */}
        <div className="flex-1 overflow-y-auto overflow-x-hidden min-h-0">
          <div className="space-y-3 pr-2">
            {tasks.length === 0 ? (
              <p className="text-sm text-gray-500 text-center py-8">
                No tasks
              </p>
            ) : (
              tasks.map((task) => <TaskCard key={task.id} task={task} />)
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
