"use client";

import { useCallback } from "react";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
const MVP_USER_ID = "00000000-0000-0000-0000-000000000001";

interface TaskFeedback {
  user_rating: number;
  user_feedback?: string;
  user_id?: string;
}

interface AgentRanking {
  agent_id: string;
  nickname: string;
  rank: number;
  total_tasks: number;
  avg_overall_score: number;
  avg_user_rating: number | null;
  total_cost: number | null;
  cost_efficiency_score: number | null;
  days_active: number | null;
}

interface LeaderboardResponse {
  rankings: AgentRanking[];
  category: string | null;
  last_updated: string;
}

export function usePerformance() {
  /**
   * Submit user feedback for a completed task
   */
  const submitTaskFeedback = useCallback(
    async (taskId: string, rating: number, feedback?: string): Promise<void> => {
      const body: TaskFeedback = {
        user_rating: rating,
        user_feedback: feedback,
        user_id: MVP_USER_ID,
      };

      const response = await fetch(
        `${API_BASE_URL}/api/tasks/${taskId}/feedback?user_id=${MVP_USER_ID}`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify(body),
        }
      );

      if (!response.ok) {
        const error = await response.text();
        throw new Error(`Failed to submit feedback: ${error}`);
      }

      return await response.json();
    },
    []
  );

  /**
   * Fetch agent leaderboard
   */
  const fetchLeaderboard = useCallback(
    async (category?: string, limit: number = 10): Promise<LeaderboardResponse> => {
      const params = new URLSearchParams({ user_id: MVP_USER_ID });
      if (category) params.append("category", category);
      params.append("limit", limit.toString());

      const response = await fetch(
        `${API_BASE_URL}/api/agents/leaderboard?${params.toString()}`
      );

      if (!response.ok) {
        const error = await response.text();
        throw new Error(`Failed to fetch leaderboard: ${error}`);
      }

      return await response.json();
    },
    []
  );

  /**
   * Fetch performance history for a specific agent
   */
  const fetchAgentPerformance = useCallback(
    async (agentId: string, category?: string, limit: number = 100) => {
      const params = new URLSearchParams({ user_id: MVP_USER_ID });
      if (category) params.append("category", category);
      params.append("limit", limit.toString());

      const response = await fetch(
        `${API_BASE_URL}/api/agents/${agentId}/performance?${params.toString()}`
      );

      if (!response.ok) {
        const error = await response.text();
        throw new Error(`Failed to fetch agent performance: ${error}`);
      }

      return await response.json();
    },
    []
  );

  return {
    submitTaskFeedback,
    fetchLeaderboard,
    fetchAgentPerformance,
  };
}
