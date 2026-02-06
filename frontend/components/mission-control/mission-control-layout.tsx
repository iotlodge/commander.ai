"use client";

import { useState, useRef, useEffect } from "react";
import { AgentTeamPanel } from "./agent-team-panel";
import { ConversationStream } from "./conversation-stream";
import { CommandInputBar } from "./command-input-bar";
import { KeyboardShortcutsHelp } from "./keyboard-shortcuts-help";
import { useKeyboardShortcuts } from "@/hooks/use-keyboard-shortcuts";

export function MissionControlLayout() {
  const [selectedAgentFilter, setSelectedAgentFilter] = useState<string | null>(null);
  const commandInputRef = useRef<{ focus: () => void; insertMention: (nickname: string) => void }>(null);
  const conversationRef = useRef<{ scrollToBottom: () => void }>(null);

  const handleAgentClick = (nickname: string) => {
    // Auto-populate @mention in input and focus
    commandInputRef.current?.insertMention(nickname);
    commandInputRef.current?.focus();
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
      description: "Clear agent filter",
      action: () => setSelectedAgentFilter(null),
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
    <div className="h-screen bg-[#1a1f2e] flex overflow-hidden">
      {/* Left Panel: Agent Team Roster */}
      <div className="w-64 flex-shrink-0 bg-[#141824] border-r border-[#2a3444]">
        <AgentTeamPanel
          selectedAgent={selectedAgentFilter}
          onSelectAgent={setSelectedAgentFilter}
          onAgentClick={handleAgentClick}
        />
      </div>

      {/* Center Panel: Conversation Stream + Command Input */}
      <div className="flex-1 flex flex-col overflow-hidden">
        {/* Header */}
        <div className="flex-shrink-0 h-16 bg-[#1e2433] border-b border-[#2a3444] flex items-center justify-between px-6">
          <div className="flex items-center gap-3">
            <div className="text-lg font-bold text-white">MISSION CONTROL</div>
            <div className="text-xs text-gray-500">Real-time AI orchestration</div>
          </div>
          <div className="flex items-center gap-4">
            {selectedAgentFilter && (
              <div className="text-sm text-gray-400">
                Filtering: <span className="text-[#4a9eff]">@{selectedAgentFilter}</span>
                <button
                  onClick={() => setSelectedAgentFilter(null)}
                  className="ml-2 text-xs text-gray-500 hover:text-white"
                >
                  ✕ Clear
                </button>
              </div>
            )}
            <KeyboardShortcutsHelp />
          </div>
        </div>

        {/* Conversation Stream */}
        <div className="flex-1 overflow-y-auto">
          <ConversationStream agentFilter={selectedAgentFilter} />
        </div>

        {/* Command Input Bar */}
        <div className="flex-shrink-0 bg-[#1e2433] border-t border-[#2a3444]">
          <CommandInputBar ref={commandInputRef} />
        </div>
      </div>
    </div>
  );
}
