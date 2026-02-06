"use client";

import { useEffect, useState, useRef } from "react";
import { useTaskStore } from "@/lib/store";
import { useWebSocket } from "@/hooks/use-websocket";
import { AgentTask, TaskStatus } from "@/lib/types";
import { ConversationMessage } from "./conversation-message";
import { SystemMessage } from "./system-message";
import { Inbox, Sparkles } from "lucide-react";

const MVP_USER_ID = "00000000-0000-0000-0000-000000000001";

interface ConversationStreamProps {
  agentFilter: string | null;
}

type ConversationItem = {
  id: string;
  type: "user_command" | "agent_response" | "system_event";
  timestamp: Date;
  content: any;
};

export function ConversationStream({ agentFilter }: ConversationStreamProps) {
  const { tasks, handleWebSocketEvent } = useTaskStore();
  const { events } = useWebSocket(MVP_USER_ID);
  const [conversationItems, setConversationItems] = useState<ConversationItem[]>([]);
  const [lastProcessedIndex, setLastProcessedIndex] = useState(-1);
  const streamEndRef = useRef<HTMLDivElement>(null);
  const [autoScroll, setAutoScroll] = useState(true);
  const hasAnimatedRef = useRef(new Set<string>());
  const previousItemCountRef = useRef(0);

  // Handle WebSocket events
  useEffect(() => {
    if (events.length > lastProcessedIndex + 1) {
      for (let i = lastProcessedIndex + 1; i < events.length; i++) {
        handleWebSocketEvent(events[i]);
      }
      setLastProcessedIndex(events.length - 1);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [events, lastProcessedIndex]);

  // Build conversation from tasks
  useEffect(() => {
    const items: ConversationItem[] = [];
    const taskArray = Array.from(tasks.values()).sort((a, b) =>
      new Date(a.created_at).getTime() - new Date(b.created_at).getTime()
    );

    for (const task of taskArray) {
      // Filter by agent if selected
      if (agentFilter && task.agent_nickname !== agentFilter) {
        continue;
      }

      // User command (when task created)
      items.push({
        id: `${task.id}-command`,
        type: "user_command",
        timestamp: new Date(task.created_at),
        content: {
          command: task.command_text,
          agentNickname: task.agent_nickname,
        },
      });

      // Agent response (when task completed or failed)
      if (task.status === TaskStatus.COMPLETED || task.status === TaskStatus.FAILED) {
        items.push({
          id: `${task.id}-response`,
          type: "agent_response",
          timestamp: task.completed_at ? new Date(task.completed_at) : new Date(),
          content: {
            task,
          },
        });
      }

      // In-progress indicator
      if (task.status === TaskStatus.IN_PROGRESS || task.status === TaskStatus.TOOL_CALL) {
        items.push({
          id: `${task.id}-working`,
          type: "system_event",
          timestamp: task.started_at ? new Date(task.started_at) : new Date(),
          content: {
            message: `@${task.agent_nickname} is ${task.current_node || "processing"}...`,
            task,
          },
        });
      }
    }

    // Update conversation items
    setConversationItems(items);
  }, [tasks, agentFilter]);

  // Auto-scroll to bottom on new messages (if enabled)
  useEffect(() => {
    if (autoScroll && streamEndRef.current) {
      // Use instant scroll instead of smooth to prevent jitter
      streamEndRef.current.scrollIntoView({ behavior: "instant" });
    }
    // Update previous count after render
    previousItemCountRef.current = conversationItems.length;
  }, [conversationItems, autoScroll]);

  // Detect manual scroll
  const handleScroll = (e: React.UIEvent<HTMLDivElement>) => {
    const target = e.currentTarget;
    const isAtBottom =
      target.scrollHeight - target.scrollTop <= target.clientHeight + 100;
    setAutoScroll(isAtBottom);
  };

  if (conversationItems.length === 0) {
    return (
      <div className="h-full flex items-center justify-center">
        <div className="text-center animate-fade-in">
          <div className="relative inline-block mb-6">
            <Inbox className="h-16 w-16 text-gray-600 mx-auto" />
            <Sparkles className="h-6 w-6 text-[#4a9eff] absolute -top-2 -right-2 animate-pulse" />
          </div>
          <h3 className="text-gray-300 text-xl font-semibold mb-2">
            Welcome to Mission Control
          </h3>
          <p className="text-gray-400 text-sm mb-4 max-w-md mx-auto">
            Your AI team is ready. Start by typing a command below and mention an agent with <span className="text-[#4a9eff] font-mono">@agent</span>
          </p>
          <div className="flex flex-col gap-2 items-center">
            <p className="text-xs text-gray-500">Try these commands:</p>
            <div className="flex flex-wrap gap-2 justify-center max-w-lg">
              {[
                "@chat what's the weather?",
                "@bob research quantum computing",
                "@alice search web for AI news"
              ].map((cmd, i) => (
                <div key={i} className="text-xs bg-[#1e2433] border border-[#2a3444] rounded px-3 py-1.5 text-gray-400 font-mono">
                  {cmd}
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div
      className="h-full overflow-y-auto px-6 py-4"
      onScroll={handleScroll}
    >
      <div className="space-y-4">
        {conversationItems.map((item, index) => {
          // Animations disabled to prevent shaking - can re-enable later
          if (item.type === "user_command") {
            return (
              <div
                key={item.id}
                className="flex justify-end"
              >
                <div className="max-w-2xl bg-[#4a9eff]/10 border border-[#4a9eff]/30 rounded-lg px-4 py-3 hover:bg-[#4a9eff]/15 transition-colors">
                  <div className="text-sm text-gray-400 mb-1">
                    You → @{item.content.agentNickname}
                  </div>
                  <div className="text-white">
                    {item.content.command.replace(/^@\w+\s*/, "")}
                  </div>
                  <div className="text-xs text-gray-500 mt-2">
                    {item.timestamp.toLocaleTimeString()}
                  </div>
                </div>
              </div>
            );
          }

          if (item.type === "agent_response") {
            return (
              <div
                key={item.id}
              >
                <ConversationMessage
                  task={item.content.task}
                  timestamp={item.timestamp}
                />
              </div>
            );
          }

          if (item.type === "system_event") {
            return (
              <div
                key={item.id}
              >
                <SystemMessage
                  message={item.content.message}
                  task={item.content.task}
                  timestamp={item.timestamp}
                />
              </div>
            );
          }

          return null;
        })}
        <div ref={streamEndRef} />
      </div>

      {/* Scroll indicator */}
      {!autoScroll && (
        <button
          onClick={() => {
            streamEndRef.current?.scrollIntoView({ behavior: "smooth" });
            setAutoScroll(true);
          }}
          className="fixed bottom-24 right-8 bg-[#4a9eff] text-white px-4 py-2 rounded-full shadow-lg hover:bg-[#3a8edf] transition-all hover:scale-105 flex items-center gap-2 animate-bounce-subtle"
        >
          <span className="text-sm">↓ New messages</span>
        </button>
      )}
    </div>
  );
}
