"use client";

import { useEffect, useState } from "react";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { Badge } from "@/components/ui/badge";
import { useTaskStore } from "@/lib/store";
import { useWebSocket } from "@/hooks/use-websocket";
import { TaskStatus } from "@/lib/types";
import { Activity, Brain } from "lucide-react";

const MVP_USER_ID = "00000000-0000-0000-0000-000000000001";

interface AgentInfo {
  id: string;
  nickname: string;
  specialization: string;
  color: string;
}

const AGENTS: AgentInfo[] = [
  { id: "agent_g", nickname: "chat", specialization: "Interactive Chat", color: "#4a9eff" },
  { id: "agent_a", nickname: "bob", specialization: "Research Specialist", color: "#10b981" },
  { id: "agent_b", nickname: "sue", specialization: "Compliance Specialist", color: "#f59e0b" },
  { id: "agent_c", nickname: "rex", specialization: "Data Analyst", color: "#8b5cf6" },
  { id: "agent_d", nickname: "alice", specialization: "Document Manager", color: "#ec4899" },
  { id: "agent_e", nickname: "maya", specialization: "Reflection Specialist", color: "#06b6d4" },
  { id: "agent_f", nickname: "kai", specialization: "Reflexion Specialist", color: "#f97316" },
];

interface AgentTeamPanelProps {
  selectedAgent: string | null;
  onSelectAgent: (agentNickname: string | null) => void;
}

export function AgentTeamPanel({ selectedAgent, onSelectAgent }: AgentTeamPanelProps) {
  const { tasks, getTasksByStatus } = useTaskStore();
  const { isConnected } = useWebSocket(MVP_USER_ID);

  // Calculate agent activity
  const getAgentActivity = (nickname: string) => {
    const agentTasks = Array.from(tasks.values()).filter(
      (task) => task.agent_nickname === nickname
    );

    const active = agentTasks.filter(
      (task) =>
        task.status === TaskStatus.IN_PROGRESS ||
        task.status === TaskStatus.TOOL_CALL
    ).length;

    const queued = agentTasks.filter(
      (task) => task.status === TaskStatus.QUEUED
    ).length;

    return { active, queued };
  };

  // Calculate total metrics
  const totalActive = Array.from(tasks.values()).filter(
    (task) =>
      task.status === TaskStatus.IN_PROGRESS ||
      task.status === TaskStatus.TOOL_CALL
  ).length;

  const totalQueued = getTasksByStatus(TaskStatus.QUEUED).length;

  return (
    <div className="h-full flex flex-col">
      {/* Header */}
      <div className="flex-shrink-0 p-4 border-b border-[#2a3444]">
        <div className="flex items-center gap-2 mb-2">
          <Brain className="h-5 w-5 text-[#4a9eff]" />
          <h2 className="text-sm font-bold text-white uppercase tracking-wide">
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
              onClick={() =>
                onSelectAgent(isSelected ? null : agent.nickname)
              }
              className={`w-full p-3 mb-2 rounded-lg transition-all ${
                isSelected
                  ? "bg-[#4a9eff]/10 border border-[#4a9eff]/30"
                  : "bg-[#1a1f2e] hover:bg-[#1e2433] border border-transparent"
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
                    <div className="absolute -top-1 -right-1 w-3 h-3 bg-green-400 rounded-full border-2 border-[#141824] animate-pulse" />
                  )}
                </div>

                {/* Info */}
                <div className="flex-1 text-left">
                  <div className="text-sm font-semibold text-white">
                    @{agent.nickname}
                  </div>
                  <div className="text-xs text-gray-400">
                    {agent.specialization}
                  </div>

                  {/* Activity */}
                  {(activity.active > 0 || activity.queued > 0) && (
                    <div className="flex items-center gap-2 mt-1">
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
                  )}
                </div>
              </div>
            </button>
          );
        })}
      </div>

      {/* Footer Stats */}
      <div className="flex-shrink-0 p-4 pb-20 border-t border-[#2a3444]">
        <div className="flex items-center gap-2 text-xs text-gray-500 mb-2">
          <Activity className="h-3 w-3" />
          <span>System Activity</span>
        </div>
        <div className="grid grid-cols-2 gap-2">
          <div className="bg-[#1a1f2e] p-2 rounded">
            <div className="text-xl font-bold text-green-400">{totalActive}</div>
            <div className="text-xs text-gray-500">Active</div>
          </div>
          <div className="bg-[#1a1f2e] p-2 rounded">
            <div className="text-xl font-bold text-gray-400">{totalQueued}</div>
            <div className="text-xs text-gray-500">Queued</div>
          </div>
        </div>
      </div>
    </div>
  );
}
