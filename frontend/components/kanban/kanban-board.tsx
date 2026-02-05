"use client";

import { useEffect, useState } from "react";
import Image from "next/image";
import { useTaskStore } from "@/lib/store";
import { useWebSocket } from "@/hooks/use-websocket";
import { TaskStatus } from "@/lib/types";
import { KanbanColumn } from "./kanban-column";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Trash2, Package, GitBranch, MessageSquare } from "lucide-react";
import { AgentGraphModal } from "@/components/graphs/agent-graph-modal";
import { useGraphModal } from "@/lib/hooks/use-graph-modal";
import { ChatModal } from "@/components/chat/chat-modal";

const MVP_USER_ID = "00000000-0000-0000-0000-000000000001";

export function KanbanBoard() {
  const { tasks, getTasksByStatus, handleWebSocketEvent, addTask } = useTaskStore();
  const { isConnected, events } = useWebSocket(MVP_USER_ID);
  const [lastProcessedIndex, setLastProcessedIndex] = useState(-1);
  const { isOpen, openModal, closeModal } = useGraphModal();
  const [showChatModal, setShowChatModal] = useState(false);

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

  // Handle WebSocket events - Process ALL new events, not just the latest
  useEffect(() => {
    if (events.length > lastProcessedIndex + 1) {
      // Process all unprocessed events
      for (let i = lastProcessedIndex + 1; i < events.length; i++) {
        handleWebSocketEvent(events[i]);
      }
      setLastProcessedIndex(events.length - 1);
    }
  }, [events, lastProcessedIndex, handleWebSocketEvent]);

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
          <Image
            src="/ui_logo.png"
            alt="Commander.ai"
            width={300}
            height={75}
            className="object-contain"
            priority
          />
          <p className="text-sm text-gray-400 mt-1">
            Real-time task monitoring and management
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Button
            onClick={handlePurgeCompleted}
            variant="outline"
            size="sm"
            className="gap-1.5 bg-green-500/10 hover:bg-green-500/20 text-green-400 border-green-500/30 h-8 text-xs"
          >
            <Trash2 className="h-3.5 w-3.5" />
            Purge Completed
          </Button>
          <Button
            onClick={handlePurgeFailed}
            variant="outline"
            size="sm"
            className="gap-1.5 bg-red-500/10 hover:bg-red-500/20 text-red-400 border-red-500/30 h-8 text-xs"
          >
            <Trash2 className="h-3.5 w-3.5" />
            Purge Failed
          </Button>
          <div className="h-6 w-px bg-gray-600 mx-1" />
          <Button
            variant="outline"
            size="sm"
            disabled={true}
            className="gap-1.5 bg-gray-500/10 hover:bg-gray-500/20 text-gray-400 border-gray-500/30 h-8 text-xs"
            title="Batch multiple commands (coming soon)"
          >
            <Package className="h-3.5 w-3.5" />
            Batch Tasks
          </Button>
          <Button
            variant="outline"
            size="sm"
            onClick={openModal}
            className="gap-1.5 bg-emerald-500/10 hover:bg-emerald-500/20 text-emerald-400 border-emerald-500/30 h-8 text-xs"
          >
            <GitBranch className="h-3.5 w-3.5" />
            View Agent Graphs
          </Button>
          <Button
            variant="outline"
            size="sm"
            onClick={() => setShowChatModal(true)}
            className="gap-1.5 bg-blue-500/10 hover:bg-blue-500/20 text-blue-400 border-blue-500/30 h-8 text-xs"
          >
            <MessageSquare className="h-3.5 w-3.5" />
            Chat with LLM
          </Button>
          <div className="h-6 w-px bg-gray-600 mx-1" />
          <Badge
            variant={isConnected ? "default" : "destructive"}
            className={isConnected ? "bg-green-500/20 text-green-400 border-green-500/30 h-8" : "h-8"}
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

      {/* Graph Modal */}
      <AgentGraphModal isOpen={isOpen} onClose={closeModal} />

      {/* Chat Modal */}
      <ChatModal
        isOpen={showChatModal}
        onClose={() => setShowChatModal(false)}
      />
    </div>
  );
}
