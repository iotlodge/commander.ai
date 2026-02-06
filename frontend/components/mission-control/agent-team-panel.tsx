"use client";

import { useEffect, useState } from "react";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { Badge } from "@/components/ui/badge";
import { useTaskStore } from "@/lib/store";
import { useWebSocket } from "@/hooks/use-websocket";
import { useAgents } from "@/lib/hooks/use-agents";
import { TaskStatus } from "@/lib/types";
import { Activity, Brain, AlertCircle } from "lucide-react";

const MVP_USER_ID = "00000000-0000-0000-0000-000000000001";

interface AgentInfo {
  id: string;
  nickname: string;
  specialization: string;
  color: string;
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

const AGENTS: AgentInfo[] = [
  { id: "parent", nickname: "leo", specialization: "Orchestrator", color: getAgentColor("leo") },
  { id: "agent_g", nickname: "chat", specialization: "Interactive Chat", color: getAgentColor("chat") },
  { id: "agent_a", nickname: "bob", specialization: "Research Specialist", color: getAgentColor("bob") },
  { id: "agent_b", nickname: "sue", specialization: "Compliance Specialist", color: getAgentColor("sue") },
  { id: "agent_c", nickname: "rex", specialization: "Data Analyst", color: getAgentColor("rex") },
  { id: "agent_d", nickname: "alice", specialization: "Document Manager", color: getAgentColor("alice") },
  { id: "agent_e", nickname: "maya", specialization: "Reflection Specialist", color: getAgentColor("maya") },
  { id: "agent_f", nickname: "kai", specialization: "Reflexion Specialist", color: getAgentColor("kai") },
];

interface AgentTeamPanelProps {
  selectedAgent: string | null;
  onSelectAgent: (agentNickname: string | null) => void;
  onAgentClick?: (agentNickname: string) => void;
}

export function AgentTeamPanel({ selectedAgent, onSelectAgent, onAgentClick }: AgentTeamPanelProps) {
  const { tasks, getTasksByStatus, clearCompletedTasks } = useTaskStore();
  const { isConnected } = useWebSocket(MVP_USER_ID);
  const { agents: apiAgents, isLoading: agentsLoading } = useAgents();

  // Calculate agent activity and metrics
  const getAgentActivity = (nickname: string) => {
    const agentTasks = Array.from(tasks.values()).filter(
      (task) => task.agent_nickname === nickname
    );

    const activeTasks = agentTasks.filter(
      (task) =>
        task.status === TaskStatus.IN_PROGRESS ||
        task.status === TaskStatus.TOOL_CALL
    );

    const queued = agentTasks.filter(
      (task) => task.status === TaskStatus.QUEUED
    ).length;

    // Aggregate metrics from active tasks
    let totalTokens = 0;
    let totalLlmCalls = 0;
    let totalToolCalls = 0;
    let currentNode = "";

    activeTasks.forEach((task) => {
      if (task.metadata?.execution_metrics) {
        const metrics = task.metadata.execution_metrics as any;
        if (metrics.tokens?.total) {
          totalTokens += metrics.tokens.total;
        }
        if (metrics.llm_calls !== undefined) {
          totalLlmCalls += metrics.llm_calls;
        }
        if (metrics.tool_calls !== undefined) {
          totalToolCalls += metrics.tool_calls;
        }
      }
      // Get current node from the most recent active task
      if (task.current_node && !currentNode) {
        currentNode = task.current_node;
      }
    });

    return {
      active: activeTasks.length,
      queued,
      metrics: {
        tokens: totalTokens,
        llmCalls: totalLlmCalls,
        toolCalls: totalToolCalls,
        currentNode,
      },
    };
  };

  // Calculate total metrics
  const totalActive = Array.from(tasks.values()).filter(
    (task) =>
      task.status === TaskStatus.IN_PROGRESS ||
      task.status === TaskStatus.TOOL_CALL
  ).length;

  const totalQueued = getTasksByStatus(TaskStatus.QUEUED).length;
  const totalCompleted = getTasksByStatus(TaskStatus.COMPLETED).length + getTasksByStatus(TaskStatus.FAILED).length;

  // Calculate agent status (configured vs active)
  const configuredAgentsCount = apiAgents.length;
  const displayAgentsCount = AGENTS.length;
  const activeAgentsCount = Math.min(configuredAgentsCount, displayAgentsCount);
  const hasOfflineAgents = configuredAgentsCount !== displayAgentsCount || agentsLoading;

  return (
    <div className="h-full flex flex-col">
      {/* Header */}
      <div className="flex-shrink-0 p-4 border-b border-[var(--mc-border)]">
        <div className="flex items-center gap-2 mb-2">
          <Brain className="h-5 w-5 text-[var(--mc-accent-blue)]" />
          <h2 className="text-sm font-bold text-[var(--mc-text-primary)] uppercase tracking-wide">
            AI Agents
          </h2>
        </div>
        <div className="flex items-center gap-2">
          <Badge
            variant={isConnected ? "default" : "destructive"}
            className={
              isConnected
                ? "bg-green-500/20 text-green-400 border-green-500/30 text-xs"
                : "text-xs"
            }
          >
            {isConnected ? "🟢 Live" : "🔴 Offline"}
          </Badge>

          {/* Agent Status Indicator */}
          {!agentsLoading && (
            <Badge
              variant="outline"
              className={`text-xs ${
                hasOfflineAgents
                  ? "bg-orange-500/10 text-orange-400 border-orange-500/30"
                  : "bg-blue-500/10 text-blue-400 border-blue-500/30"
              }`}
            >
              <Activity className="h-3 w-3 mr-1" />
              {activeAgentsCount}/{configuredAgentsCount} agents
              {hasOfflineAgents && (
                <AlertCircle className="h-3 w-3 ml-1 text-orange-400" />
              )}
            </Badge>
          )}
        </div>
      </div>

      {/* Agent List */}
      <div className="flex-1 overflow-y-auto p-2">
        {AGENTS.map((agent) => {
          const activity = getAgentActivity(agent.nickname);
          const isActive = activity.active > 0;
          const isSelected = selectedAgent === agent.nickname;

          return (
            <button
              key={agent.id}
              onClick={() => {
                if (onAgentClick) {
                  onAgentClick(agent.nickname);
                } else {
                  onSelectAgent(isSelected ? null : agent.nickname);
                }
              }}
              className={`w-full p-3 mb-2 rounded-lg transition-all ${
                isSelected
                  ? "bg-[var(--mc-accent-blue)]/10 border border-[var(--mc-accent-blue)]/30"
                  : "bg-[var(--mc-bg-primary)] hover:bg-[var(--mc-bg-secondary)] border border-transparent"
              }`}
            >
              <div className="flex items-start gap-3">
                {/* Avatar */}
                <div className="relative">
                  <Avatar
                    className="h-10 w-10"
                    style={{ backgroundColor: agent.color }}
                  >
                    <AvatarFallback
                      className="text-white text-sm font-bold"
                      style={{ backgroundColor: agent.color }}
                    >
                      {agent.nickname.slice(0, 2).toUpperCase()}
                    </AvatarFallback>
                  </Avatar>
                  {isActive && (
                    <div className="absolute -top-1 -right-1 w-3 h-3 bg-green-400 rounded-full border-2 border-[var(--mc-bg-tertiary)] animate-pulse" />
                  )}
                </div>

                {/* Info */}
                <div className="flex-1 text-left">
                  <div className="text-sm font-semibold text-[var(--mc-text-primary)]">
                    @{agent.nickname}
                  </div>
                  <div className="text-xs text-[var(--mc-text-secondary)]">
                    {agent.specialization}
                  </div>

                  {/* Activity */}
                  {(activity.active > 0 || activity.queued > 0) && (
                    <div className="mt-1 space-y-1">
                      <div className="flex items-center gap-2">
                        {activity.active > 0 && (
                          <Badge
                            variant="outline"
                            className="text-xs bg-green-500/10 text-green-400 border-green-500/30"
                          >
                            {activity.active} active
                          </Badge>
                        )}
                        {activity.queued > 0 && (
                          <Badge
                            variant="outline"
                            className="text-xs bg-gray-500/10 text-gray-400 border-gray-500/30"
                          >
                            {activity.queued} queued
                          </Badge>
                        )}
                      </div>

                      {/* Real-time metrics for active tasks */}
                      {activity.active > 0 && activity.metrics && (
                        <div className="flex flex-wrap items-center gap-1.5 text-[10px]">
                          {activity.metrics.tokens > 0 && (
                            <span className="text-[var(--metric-tokens)] font-mono">
                              {activity.metrics.tokens.toLocaleString()} tok
                            </span>
                          )}
                          {activity.metrics.llmCalls > 0 && (
                            <span className="text-[var(--metric-llm)]">
                              {activity.metrics.llmCalls} LLM
                            </span>
                          )}
                          {activity.metrics.toolCalls > 0 && (
                            <span className="text-[var(--metric-tools)]">
                              {activity.metrics.toolCalls} tools
                            </span>
                          )}
                          {activity.metrics.currentNode && (
                            <span className="text-[var(--metric-duration)] truncate max-w-[120px]">
                              → {activity.metrics.currentNode}
                            </span>
                          )}
                        </div>
                      )}
                    </div>
                  )}
                </div>
              </div>
            </button>
          );
        })}
      </div>

      {/* Footer Stats */}
      <div className="flex-shrink-0 p-4 pb-20 border-t border-[var(--mc-border)] space-y-3">
        <div className="flex items-center gap-2 text-xs text-gray-500">
          <Activity className="h-3 w-3" />
          <span>System Activity</span>
        </div>

        {/* Stats Grid */}
        <div className="grid grid-cols-3 gap-2">
          <div className="bg-[var(--mc-bg-primary)] p-2 rounded">
            <div className="text-lg font-bold text-[var(--metric-tokens)]">{totalActive}</div>
            <div className="text-[10px] text-gray-500">Active</div>
          </div>
          <div className="bg-[var(--mc-bg-primary)] p-2 rounded">
            <div className="text-lg font-bold text-gray-400">{totalQueued}</div>
            <div className="text-[10px] text-gray-500">Queued</div>
          </div>
          <div className="bg-[var(--mc-bg-primary)] p-2 rounded">
            <div className="text-lg font-bold text-[var(--metric-duration)]">{totalCompleted}</div>
            <div className="text-[10px] text-gray-500">Done</div>
          </div>
        </div>

        {/* Clear Completed Button */}
        {totalCompleted > 0 && (
          <button
            onClick={() => {
              if (confirm(`Clear ${totalCompleted} completed task${totalCompleted === 1 ? '' : 's'}?`)) {
                clearCompletedTasks();
              }
            }}
            className="w-full flex items-center justify-center gap-2 px-3 py-2 text-xs bg-blue-500/10 text-blue-400 border border-blue-500/30 rounded hover:bg-blue-500/20 transition-colors"
          >
            <svg className="h-3 w-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
            </svg>
            Clear Completed ({totalCompleted})
          </button>
        )}
      </div>
    </div>
  );
}
