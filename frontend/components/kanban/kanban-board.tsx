"use client";

import { useEffect } from "react";
import { useTaskStore } from "@/lib/store";
import { useWebSocket } from "@/hooks/use-websocket";
import { TaskStatus } from "@/lib/types";
import { KanbanColumn } from "./kanban-column";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Trash2 } from "lucide-react";

const MVP_USER_ID = "00000000-0000-0000-0000-000000000001";

export function KanbanBoard() {
  const { tasks, getTasksByStatus, handleWebSocketEvent, addTask } = useTaskStore();
  const { isConnected, events } = useWebSocket(MVP_USER_ID);

  const handlePurgeCompleted = async () => {
    try {
      const response = await fetch(
        `http://localhost:8000/api/tasks/purge/completed?user_id=${MVP_USER_ID}`,
        { method: "DELETE" }
      );
      if (!response.ok) {
        console.error("Failed to purge completed tasks");
      }
    } catch (error) {
      console.error("Error purging completed tasks:", error);
    }
  };

  const handlePurgeFailed = async () => {
    try {
      const response = await fetch(
        `http://localhost:8000/api/tasks/purge/failed?user_id=${MVP_USER_ID}`,
        { method: "DELETE" }
      );
      if (!response.ok) {
        console.error("Failed to purge failed tasks");
      }
    } catch (error) {
      console.error("Error purging failed tasks:", error);
    }
  };

  // Handle WebSocket events
  useEffect(() => {
    if (events.length > 0) {
      const latestEvent = events[events.length - 1];
      handleWebSocketEvent(latestEvent);
    }
  }, [events, handleWebSocketEvent]);

  // Fetch initial tasks
  useEffect(() => {
    async function fetchTasks() {
      try {
        const response = await fetch(
          `http://localhost:8000/api/tasks?user_id=${MVP_USER_ID}`
        );

        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }

        const data = await response.json();

        data.forEach((task: any) => {
          addTask(task);
        });
      } catch (error) {
        console.error("Failed to fetch tasks:", error);
      }
    }

    fetchTasks();
  }, [addTask]);

  const columns = [
    { status: TaskStatus.QUEUED, tasks: getTasksByStatus(TaskStatus.QUEUED) },
    { status: TaskStatus.IN_PROGRESS, tasks: getTasksByStatus(TaskStatus.IN_PROGRESS) },
    { status: TaskStatus.TOOL_CALL, tasks: getTasksByStatus(TaskStatus.TOOL_CALL) },
    { status: TaskStatus.COMPLETED, tasks: getTasksByStatus(TaskStatus.COMPLETED) },
    { status: TaskStatus.FAILED, tasks: getTasksByStatus(TaskStatus.FAILED) },
  ];

  return (
    <div className="h-full flex flex-col p-6 bg-[#1a1f2e]">
      {/* Header */}
      <div className="flex-shrink-0 mb-4 flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">Agent Tasks</h1>
          <p className="text-sm text-gray-400">
            Real-time task monitoring and management
          </p>
        </div>
        <div className="flex items-center gap-3">
          <Button
            onClick={handlePurgeCompleted}
            variant="outline"
            size="sm"
            className="gap-2 bg-green-500/10 hover:bg-green-500/20 text-green-400 border-green-500/30"
          >
            <Trash2 className="h-4 w-4" />
            Purge Completed
          </Button>
          <Button
            onClick={handlePurgeFailed}
            variant="outline"
            size="sm"
            className="gap-2 bg-red-500/10 hover:bg-red-500/20 text-red-400 border-red-500/30"
          >
            <Trash2 className="h-4 w-4" />
            Purge Failed
          </Button>
          <Badge
            variant={isConnected ? "default" : "destructive"}
            className={isConnected ? "bg-green-500/20 text-green-400 border-green-500/30" : ""}
          >
            {isConnected ? "🟢 Connected" : "🔴 Disconnected"}
          </Badge>
        </div>
      </div>

      {/* Kanban Board - grows to fill remaining space */}
      <div className="flex-1 flex gap-4 overflow-x-auto overflow-y-hidden min-h-0">
        {columns.map((column) => (
          <KanbanColumn
            key={column.status}
            status={column.status}
            tasks={column.tasks}
            count={column.tasks.length}
          />
        ))}
      </div>

      {/* Stats */}
      <div className="flex-shrink-0 mt-4 text-xs text-gray-500">
        Total tasks: {tasks.size} | Events received: {events.length}
      </div>
    </div>
  );
}
