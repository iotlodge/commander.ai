"use client";

import { useState } from "react";
import { ChevronDown, ChevronRight, Zap, FileText, Search, BarChart3, MessageSquare, Shield, Sparkles, Network } from "lucide-react";

interface QuickAction {
  label: string;
  command: string;
  icon?: React.ReactNode;
}

interface AgentQuickActions {
  agentNickname: string;
  agentName: string;
  color: string;
  icon: React.ReactNode;
  actions: QuickAction[];
}

// Agent color helper - uses CSS variables
const getAgentColor = (nickname: string): string => {
  const colorMap: Record<string, string> = {
    leo: "var(--agent-leo)",
    chat: "var(--agent-chat)",
    bob: "var(--agent-bob)",
    sue: "var(--agent-sue)",
    rex: "var(--agent-rex)",
    alice: "var(--agent-alice)",
    maya: "var(--agent-maya)",
    kai: "var(--agent-kai)",
  };
  return colorMap[nickname] || "var(--mc-accent-blue)";
};

const QUICK_ACTIONS: AgentQuickActions[] = [
  {
    agentNickname: "leo",
    agentName: "Leo",
    color: getAgentColor("leo"),
    icon: <Network className="h-4 w-4" />,
    actions: [
      { label: "Complex task", command: "@leo coordinate a multi-step task to " },
      { label: "Multi-agent workflow", command: "@leo orchestrate agents to " },
      { label: "Delegate intelligently", command: "@leo analyze and delegate: " },
    ],
  },
  {
    agentNickname: "chat",
    agentName: "Chat",
    color: getAgentColor("chat"),
    icon: <MessageSquare className="h-4 w-4" />,
    actions: [
      { label: "Get help", command: "@chat what can you help me with?" },
      { label: "Quick question", command: "@chat " },
    ],
  },
  {
    agentNickname: "alice",
    agentName: "Alice",
    color: getAgentColor("alice"),
    icon: <FileText className="h-4 w-4" />,
    actions: [
      { label: "Check deprecated models", command: "@alice check for deprecated LLM models" },
      { label: "Aggregate performance stats", command: "@alice run agent performance stats aggregation" },
      { label: "List all documents", command: "@alice list all documents in the system" },
      { label: "Archive old files", command: "@alice archive documents older than 6 months" },
      { label: "Generate summary", command: "@alice generate a summary of recent documents" },
      { label: "Search documents", command: "@alice search for " },
    ],
  },
  {
    agentNickname: "bob",
    agentName: "Bob",
    color: getAgentColor("bob"),
    icon: <Search className="h-4 w-4" />,
    actions: [
      { label: "Latest AI news", command: "@bob what's the latest news in AI?" },
      { label: "Market research", command: "@bob research current market trends for " },
      { label: "Competitor analysis", command: "@bob analyze competitors in " },
      { label: "Technology review", command: "@bob research the latest developments in " },
    ],
  },
  {
    agentNickname: "rex",
    agentName: "Rex",
    color: getAgentColor("rex"),
    icon: <BarChart3 className="h-4 w-4" />,
    actions: [
      { label: "Analyze data", command: "@rex analyze the following data: " },
      { label: "Generate report", command: "@rex generate a detailed analytical report on " },
      { label: "Find patterns", command: "@rex identify patterns and insights in " },
    ],
  },
  {
    agentNickname: "sue",
    agentName: "Sue",
    color: getAgentColor("sue"),
    icon: <Shield className="h-4 w-4" />,
    actions: [
      { label: "Compliance check", command: "@sue perform a compliance review of " },
      { label: "Risk assessment", command: "@sue assess risks for " },
      { label: "Policy review", command: "@sue review current policies for " },
    ],
  },
  {
    agentNickname: "maya",
    agentName: "Maya",
    color: getAgentColor("maya"),
    icon: <Sparkles className="h-4 w-4" />,
    actions: [
      { label: "Reflect on approach", command: "@maya reflect on the best approach for " },
      { label: "Evaluate options", command: "@maya evaluate different options for " },
    ],
  },
  {
    agentNickname: "kai",
    agentName: "Kai",
    color: getAgentColor("kai"),
    icon: <Zap className="h-4 w-4" />,
    actions: [
      { label: "Deep analysis", command: "@kai perform a deep reflexive analysis of " },
      { label: "Problem solving", command: "@kai solve the following problem: " },
    ],
  },
];

interface QuickActionsPanelProps {
  onCommandSelect: (command: string) => void;
}

export function QuickActionsPanel({ onCommandSelect }: QuickActionsPanelProps) {
  const [expandedAgent, setExpandedAgent] = useState<string | null>("alice");

  const toggleAgent = (nickname: string) => {
    setExpandedAgent(expandedAgent === nickname ? null : nickname);
  };

  return (
    <div className="h-full flex flex-col bg-[var(--mc-bg-tertiary)] border-l border-[var(--mc-border)]">
      {/* Header */}
      <div className="flex-shrink-0 p-4 border-b border-[var(--mc-border)]">
        <div className="flex items-center gap-2 mb-2">
          <Zap className="h-5 w-5 text-[var(--mc-accent-blue)]" />
          <h2 className="text-sm font-bold text-[var(--mc-text-primary)] uppercase tracking-wide">
            Quick Actions
          </h2>
        </div>
        <p className="text-xs text-[var(--mc-text-tertiary)]">
          One-click commands for common tasks
        </p>
      </div>

      {/* Agent Actions */}
      <div className="flex-1 overflow-y-auto p-2">
        {QUICK_ACTIONS.map((agent) => (
          <div key={agent.agentNickname} className="mb-2">
            <button
              onClick={() => toggleAgent(agent.agentNickname)}
              className="w-full flex items-center justify-between p-3 rounded-lg bg-[var(--mc-bg-primary)] hover:bg-[var(--mc-bg-secondary)] border border-[var(--mc-border)] transition-all"
            >
              <div className="flex items-center gap-2">
                <div
                  className="p-1.5 rounded"
                  style={{ backgroundColor: `${agent.color}20`, color: agent.color }}
                >
                  {agent.icon}
                </div>
                <span className="text-sm font-semibold text-[var(--mc-text-primary)]">
                  @{agent.agentNickname}
                </span>
                <span className="text-xs text-[var(--mc-text-secondary)]">
                  {agent.actions.length}
                </span>
              </div>
              {expandedAgent === agent.agentNickname ? (
                <ChevronDown className="h-4 w-4 text-gray-400" />
              ) : (
                <ChevronRight className="h-4 w-4 text-gray-400" />
              )}
            </button>

            {/* Action Buttons */}
            {expandedAgent === agent.agentNickname && (
              <div className="mt-2 ml-2 space-y-1">
                {agent.actions.map((action, idx) => (
                  <button
                    key={idx}
                    onClick={() => onCommandSelect(action.command)}
                    className="w-full text-left px-3 py-2 rounded text-xs bg-[var(--mc-bg-primary)]/50 hover:bg-[var(--mc-hover)] text-[var(--mc-text-secondary)] hover:text-[var(--mc-text-primary)] transition-colors border border-[var(--mc-border)]/50 hover:border-[var(--mc-accent-blue)]/30"
                  >
                    {action.label}
                  </button>
                ))}
              </div>
            )}
          </div>
        ))}
      </div>

      {/* Footer Tip */}
      <div className="flex-shrink-0 p-4 border-t border-[var(--mc-border)]">
        <p className="text-xs text-gray-500 text-center">
          💡 Click any action to auto-fill the command
        </p>
      </div>
    </div>
  );
}
