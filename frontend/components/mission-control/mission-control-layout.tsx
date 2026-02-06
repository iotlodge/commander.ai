"use client";

import { useState, useRef } from "react";
import { AgentTeamPanel } from "./agent-team-panel";
import { ConversationStream } from "./conversation-stream";
import { CommandInputBar } from "./command-input-bar";
import { KeyboardShortcutsHelp } from "./keyboard-shortcuts-help";
import { QuickActionsPanel } from "./quick-actions-panel";
import { ThemeToggle } from "./theme-toggle";
import { useKeyboardShortcuts } from "@/hooks/use-keyboard-shortcuts";
import { ChatModeProvider, useChatMode } from "./chat-mode-context";
import { Trash2 } from "lucide-react";
import { useTaskStore } from "@/lib/store";

function MissionControlContent() {
  const [selectedAgentFilter, setSelectedAgentFilter] = useState<string | null>(null);
  const commandInputRef = useRef<{ focus: () => void; insertMention: (nickname: string) => void; setCommand: (command: string) => void }>(null);
  const conversationRef = useRef<{ scrollToBottom: () => void }>(null);
  const { isChatMode, enterChatMode, exitChatMode } = useChatMode();
  const { clearAllTasks } = useTaskStore();

  const handleQuickActionSelect = (command: string) => {
    commandInputRef.current?.setCommand(command);
    commandInputRef.current?.focus();
  };

  const handleAgentClick = (nickname: string) => {
    if (nickname === "chat") {
      // Special handling for chat agent - enter chat mode
      enterChatMode();
      setSelectedAgentFilter(null);
      commandInputRef.current?.setCommand("");
      commandInputRef.current?.focus();
    } else {
      // Regular agents - auto-populate @mention
      exitChatMode();
      commandInputRef.current?.insertMention(nickname);
      commandInputRef.current?.focus();
    }
  };

  // Keyboard shortcuts
  useKeyboardShortcuts([
    {
      key: "k",
      metaKey: true,
      description: "Focus command input",
      action: () => commandInputRef.current?.focus(),
    },
    {
      key: "Escape",
      description: "Clear agent filter / Exit chat mode",
      action: () => {
        setSelectedAgentFilter(null);
        exitChatMode();
      },
    },
    {
      key: "g",
      metaKey: true,
      shiftKey: true,
      description: "Scroll to bottom",
      action: () => conversationRef.current?.scrollToBottom(),
    },
  ]);

  return (
    <div className="h-screen bg-[var(--mc-bg-primary)] flex overflow-hidden">
      {/* Left Panel: Agent Team Roster */}
      <div className="w-64 flex-shrink-0 bg-[var(--mc-bg-tertiary)] border-r border-[var(--mc-border)]">
        <AgentTeamPanel
          selectedAgent={selectedAgentFilter}
          onSelectAgent={setSelectedAgentFilter}
          onAgentClick={handleAgentClick}
        />
      </div>

      {/* Center Panel: Conversation Stream + Command Input */}
      <div className="flex-1 flex flex-col overflow-hidden min-w-0">
        {/* Header */}
        <div className="flex-shrink-0 h-16 bg-[var(--mc-bg-secondary)] border-b border-[var(--mc-border)] flex items-center justify-between px-6">
          <div className="flex items-center gap-3">
            <div className="text-lg font-bold text-[var(--mc-text-primary)]">MISSION CONTROL</div>
            <div className="text-xs text-[var(--mc-text-tertiary)]">Real-time AI orchestration</div>
          </div>
          <div className="flex items-center gap-4">
            {isChatMode && (
              <div className="flex items-center gap-2 px-3 py-1.5 bg-[var(--mc-accent-blue)]/10 border border-[var(--mc-accent-blue)]/30 rounded-full">
                <div className="w-2 h-2 bg-[var(--mc-accent-blue)] rounded-full animate-pulse" />
                <span className="text-sm text-[var(--mc-accent-blue)] font-medium">Chat Mode</span>
                <button
                  onClick={() => exitChatMode()}
                  className="ml-1 text-xs text-gray-400 hover:text-white"
                >
                  ✕
                </button>
              </div>
            )}
            {selectedAgentFilter && (
              <div className="text-sm text-gray-400">
                Filtering: <span className="text-[var(--mc-accent-blue)]">@{selectedAgentFilter}</span>
                <button
                  onClick={() => setSelectedAgentFilter(null)}
                  className="ml-2 text-xs text-gray-500 hover:text-white"
                >
                  ✕ Clear
                </button>
              </div>
            )}
            <button
              onClick={() => {
                if (confirm("Clear all conversation history? This cannot be undone.")) {
                  clearAllTasks();
                }
              }}
              className="flex items-center gap-2 px-3 py-1.5 text-xs bg-red-500/10 text-red-400 border border-red-500/30 rounded hover:bg-red-500/20 transition-colors"
              title="Clear chat window"
            >
              <Trash2 className="h-3 w-3" />
              Clear Chat
            </button>
            <ThemeToggle />
            <KeyboardShortcutsHelp />
          </div>
        </div>

        {/* Conversation Stream */}
        <div className="flex-1 overflow-y-auto">
          <ConversationStream agentFilter={selectedAgentFilter} />
        </div>

        {/* Command Input Bar */}
        <div className="flex-shrink-0 bg-[var(--mc-bg-secondary)] border-t border-[var(--mc-border)]">
          <CommandInputBar ref={commandInputRef} chatMode={isChatMode} />
        </div>
      </div>

      {/* Right Panel: Quick Actions */}
      <div className="w-72 flex-shrink-0">
        <QuickActionsPanel onCommandSelect={handleQuickActionSelect} />
      </div>
    </div>
  );
}

export function MissionControlLayout() {
  return (
    <ChatModeProvider>
      <MissionControlContent />
    </ChatModeProvider>
  );
}
