"use client";

import { useEffect, useState } from "react";
import { Trophy, TrendingUp, Zap, DollarSign, Star } from "lucide-react";
import { usePerformance } from "@/lib/hooks/use-performance";

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

const AGENT_COLORS: Record<string, string> = {
  leo: "#fbbf24",
  chat: "#4a9eff",
  bob: "#10b981",
  sue: "#f59e0b",
  rex: "#8b5cf6",
  alice: "#ec4899",
  maya: "#06b6d4",
  kai: "#f97316"
};

export function LeaderboardPanel() {
  const { fetchLeaderboard } = usePerformance();
  const [rankings, setRankings] = useState<AgentRanking[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [lastUpdated, setLastUpdated] = useState<string>("");

  useEffect(() => {
    loadLeaderboard();
    // Refresh every 30 seconds
    const interval = setInterval(loadLeaderboard, 30000);
    return () => clearInterval(interval);
  }, []);

  const loadLeaderboard = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await fetchLeaderboard(undefined, 10);
      setRankings(data.rankings);
      setLastUpdated(new Date(data.last_updated).toLocaleTimeString());
    } catch (err) {
      setError("Failed to load leaderboard");
      console.error("Leaderboard error:", err);
    } finally {
      setLoading(false);
    }
  };

  const getAgentColor = (nickname: string) => {
    return AGENT_COLORS[nickname.toLowerCase()] || "#9ca3af";
  };

  const getMedalIcon = (rank: number) => {
    if (rank === 1) return "🥇";
    if (rank === 2) return "🥈";
    if (rank === 3) return "🥉";
    return null;
  };

  if (loading && rankings.length === 0) {
    return (
      <div className="h-full flex items-center justify-center">
        <div className="text-center">
          <TrendingUp className="h-12 w-12 text-gray-600 mx-auto mb-3 animate-pulse" />
          <p className="text-sm text-gray-400">Loading leaderboard...</p>
        </div>
      </div>
    );
  }

  if (error && rankings.length === 0) {
    return (
      <div className="h-full flex items-center justify-center">
        <div className="text-center">
          <Trophy className="h-12 w-12 text-gray-600 mx-auto mb-3" />
          <p className="text-sm text-red-400">{error}</p>
          <button
            onClick={loadLeaderboard}
            className="mt-3 text-xs text-blue-400 hover:text-blue-300"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  const top3 = rankings.slice(0, 3);
  const others = rankings.slice(3);

  return (
    <div className="h-full flex flex-col bg-[var(--mc-bg-primary)]">
      {/* Header */}
      <div className="px-4 py-3 border-b border-[var(--mc-border)]">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Trophy className="h-5 w-5 text-yellow-500" />
            <h2 className="text-sm font-semibold text-[var(--mc-text-primary)]">
              Leaderboard
            </h2>
          </div>
          {lastUpdated && (
            <span className="text-xs text-gray-500">
              {lastUpdated}
            </span>
          )}
        </div>
        <p className="text-xs text-gray-400 mt-1">
          Agent performance rankings
        </p>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto px-4 py-3">
        {rankings.length === 0 ? (
          <div className="text-center py-8">
            <Trophy className="h-12 w-12 text-gray-600 mx-auto mb-3" />
            <p className="text-sm text-gray-400">No rankings yet</p>
            <p className="text-xs text-gray-500 mt-1">
              Complete some tasks to see rankings
            </p>
          </div>
        ) : (
          <div className="space-y-4">
            {/* Top 3 - Highlighted */}
            {top3.length > 0 && (
              <div className="space-y-2">
                <h3 className="text-xs font-semibold text-gray-400 uppercase tracking-wide">
                  Top Performers
                </h3>
                {top3.map((agent) => (
                  <div
                    key={agent.agent_id}
                    className="relative p-3 rounded-lg border border-[var(--mc-border)] bg-[var(--mc-bg-secondary)] hover:bg-[var(--mc-hover)] transition-colors"
                  >
                    {/* Rank Medal */}
                    <div className="absolute -top-2 -left-2 text-2xl">
                      {getMedalIcon(agent.rank)}
                    </div>

                    {/* Agent Info */}
                    <div className="flex items-start justify-between mb-2">
                      <div className="flex items-center gap-2">
                        <div
                          className="w-2 h-2 rounded-full"
                          style={{ backgroundColor: getAgentColor(agent.nickname) }}
                        />
                        <span className="text-sm font-medium text-[var(--mc-text-primary)]">
                          @{agent.nickname}
                        </span>
                      </div>
                      <div className="flex items-center gap-1">
                        <Star className="h-3 w-3 text-yellow-500 fill-yellow-500" />
                        <span className="text-sm font-bold text-[var(--mc-text-primary)]">
                          {agent.avg_overall_score.toFixed(2)}
                        </span>
                      </div>
                    </div>

                    {/* Stats Grid */}
                    <div className="grid grid-cols-2 gap-2 text-xs">
                      <div className="flex items-center gap-1 text-gray-400">
                        <Zap className="h-3 w-3" />
                        <span>{agent.total_tasks} tasks</span>
                      </div>
                      {agent.cost_efficiency_score !== null && (
                        <div className="flex items-center gap-1 text-gray-400">
                          <DollarSign className="h-3 w-3" />
                          <span>{agent.cost_efficiency_score.toFixed(2)} eff</span>
                        </div>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            )}

            {/* Others - Compact List */}
            {others.length > 0 && (
              <div className="space-y-2">
                <h3 className="text-xs font-semibold text-gray-400 uppercase tracking-wide">
                  Other Agents
                </h3>
                <div className="space-y-1">
                  {others.map((agent) => (
                    <div
                      key={agent.agent_id}
                      className="flex items-center justify-between p-2 rounded hover:bg-[var(--mc-bg-secondary)] transition-colors"
                    >
                      <div className="flex items-center gap-2">
                        <span className="text-xs font-mono text-gray-500 w-6">
                          #{agent.rank}
                        </span>
                        <div
                          className="w-1.5 h-1.5 rounded-full"
                          style={{ backgroundColor: getAgentColor(agent.nickname) }}
                        />
                        <span className="text-sm text-[var(--mc-text-secondary)]">
                          @{agent.nickname}
                        </span>
                      </div>
                      <div className="flex items-center gap-3 text-xs text-gray-400">
                        <span>{agent.avg_overall_score.toFixed(2)}</span>
                        <span className="text-gray-500">{agent.total_tasks}t</span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}
      </div>

      {/* Footer - Refresh Hint */}
      <div className="px-4 py-2 border-t border-[var(--mc-border)]">
        <p className="text-xs text-gray-500 text-center">
          Updates every 30 seconds
        </p>
      </div>
    </div>
  );
}
