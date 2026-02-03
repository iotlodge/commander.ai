"use client";

import { useState, useEffect } from "react";
import { AgentInfo } from "@/lib/types";

const API_BASE_URL = "http://localhost:8000";

export function useAgents() {
  const [agents, setAgents] = useState<AgentInfo[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchAgents = async () => {
      try {
        const response = await fetch(`${API_BASE_URL}/api/agents`);

        if (!response.ok) {
          throw new Error(`Failed to fetch agents: ${response.status}`);
        }

        const data = await response.json();
        setAgents(data);
        setError(null);
      } catch (err) {
        const errorMessage = err instanceof Error ? err.message : "Failed to fetch agents";
        setError(errorMessage);
        console.error("Error fetching agents:", err);

        // Fallback to hardcoded agents if API fails
        setAgents([
          { id: "agent_a", nickname: "bob", specialization: "Research Specialist", description: "Conducts research, synthesis, and information gathering" },
          { id: "agent_b", nickname: "sue", specialization: "Compliance Specialist", description: "Ensures compliance with regulations and policies" },
          { id: "agent_c", nickname: "rex", specialization: "Data Analyst", description: "Analyzes data and generates insights" },
          { id: "agent_d", nickname: "alice", specialization: "Document Management", description: "Manages documents, collections, and semantic search" },
          { id: "parent", nickname: "leo", specialization: "Orchestrator", description: "Coordinates complex multi-agent tasks" },
        ]);
      } finally {
        setIsLoading(false);
      }
    };

    fetchAgents();
  }, []);

  const getAgentById = (id: string): AgentInfo | undefined => {
    return agents.find(agent => agent.id === id);
  };

  const getAgentByNickname = (nickname: string): AgentInfo | undefined => {
    return agents.find(agent => agent.nickname.toLowerCase() === nickname.toLowerCase());
  };

  return {
    agents,
    isLoading,
    error,
    getAgentById,
    getAgentByNickname,
  };
}
