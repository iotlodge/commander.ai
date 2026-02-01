"use client";

import { useEffect } from "react";
import { useTaskStore } from "@/lib/store";
import { useWebSocket } from "@/hooks/use-websocket";
import { TaskStatus } from "@/lib/types";
import { KanbanColumn } from "./kanban-column";
import { Badge } from "@/components/ui/badge";

const MVP_USER_ID = "00000000-0000-0000-0000-000000000001";

export function KanbanBoard() {
  const { tasks, getTasksByStatus, handleWebSocketEvent, addTask } = useTaskStore();
  const { isConnected, events } = useWebSocket(MVP_USER_ID);

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
    <div className="p-6">
      {/* Header */}
      <div className="mb-6 flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Agent Tasks</h1>
          <p className="text-muted-foreground">
            Real-time task monitoring and management
          </p>
        </div>
        <Badge variant={isConnected ? "default" : "destructive"}>
          {isConnected ? "🟢 Connected" : "🔴 Disconnected"}
        </Badge>
      </div>

      {/* Kanban Board */}
      <div className="flex gap-4 overflow-x-auto pb-4">
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
      <div className="mt-6 text-sm text-muted-foreground">
        Total tasks: {tasks.size} | Events received: {events.length}
      </div>
    </div>
  );
}
