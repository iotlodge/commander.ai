"use client";

import { useMemo } from "react";
import {
  LineChart,
  Line,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from "recharts";
import { TrendingUp, BarChart3, Target } from "lucide-react";

interface PerformanceScore {
  task_id: string;
  created_at: string;
  overall_score: number;
  user_rating?: number | null;
  category?: string | null;
  accuracy_score?: number;
  relevance_score?: number;
  completeness_score?: number;
  efficiency_score?: number;
}

interface AgentStats {
  total_tasks: number;
  successful_tasks?: number;
  failed_tasks?: number;
  avg_overall_score: number;
  avg_user_rating?: number;
  rank?: number;
  category_performance?: Record<string, { count: number; avg_score: number }>;
}

interface PerformanceChartsProps {
  scores: PerformanceScore[];
  stats: AgentStats;
  agentNickname: string;
}

export function PerformanceCharts({ scores, stats, agentNickname }: PerformanceChartsProps) {
  // Prepare score trend data (chronological)
  const scoreTrendData = useMemo(() => {
    return scores
      .slice()
      .sort((a, b) => new Date(a.created_at).getTime() - new Date(b.created_at).getTime())
      .map((score, index) => ({
        task: `#${index + 1}`,
        score: score.overall_score,
        accuracy: score.accuracy_score || 0,
        relevance: score.relevance_score || 0,
        completeness: score.completeness_score || 0,
        efficiency: score.efficiency_score || 0,
      }));
  }, [scores]);

  // Prepare category performance data
  const categoryData = useMemo(() => {
    if (!stats.category_performance) return [];
    return Object.entries(stats.category_performance).map(([category, data]) => ({
      category: category.charAt(0).toUpperCase() + category.slice(1),
      score: data.avg_score,
      tasks: data.count,
    }));
  }, [stats.category_performance]);

  // Prepare task completion data (if available)
  const completionData = stats.successful_tasks !== undefined && stats.failed_tasks !== undefined
    ? [
        {
          name: "Completed",
          count: stats.successful_tasks,
          fill: "var(--metric-tokens)",
        },
        {
          name: "Failed",
          count: stats.failed_tasks,
          fill: "var(--metric-duration)",
        },
      ]
    : [];

  const getAgentColor = (nickname: string) => {
    const colors: Record<string, string> = {
      leo: "#fbbf24",
      chat: "#4a9eff",
      bob: "#10b981",
      sue: "#f59e0b",
      rex: "#8b5cf6",
      alice: "#ec4899",
      maya: "#06b6d4",
      kai: "#f97316",
    };
    return colors[nickname.toLowerCase()] || "#9ca3af";
  };

  const agentColor = getAgentColor(agentNickname);

  return (
    <div className="space-y-6">
      {/* Score Trends Over Time */}
      {scoreTrendData.length > 0 && (
        <div className="space-y-3">
          <div className="flex items-center gap-2">
            <TrendingUp className="h-4 w-4 text-[var(--mc-accent-blue)]" />
            <h3 className="text-sm font-semibold text-[var(--mc-text-primary)]">
              Score Trends
            </h3>
          </div>
          <div className="bg-[var(--mc-bg-secondary)] border border-[var(--mc-border)] rounded-lg p-4">
            <ResponsiveContainer width="100%" height={200}>
              <LineChart data={scoreTrendData}>
                <CartesianGrid strokeDasharray="3 3" stroke="var(--mc-border)" />
                <XAxis
                  dataKey="task"
                  stroke="var(--mc-text-tertiary)"
                  style={{ fontSize: "12px" }}
                />
                <YAxis
                  domain={[0, 1]}
                  stroke="var(--mc-text-tertiary)"
                  style={{ fontSize: "12px" }}
                />
                <Tooltip
                  contentStyle={{
                    backgroundColor: "var(--mc-bg-tertiary)",
                    border: "1px solid var(--mc-border)",
                    borderRadius: "6px",
                    fontSize: "12px",
                  }}
                />
                <Legend wrapperStyle={{ fontSize: "12px" }} />
                <Line
                  type="monotone"
                  dataKey="score"
                  stroke={agentColor}
                  strokeWidth={2}
                  dot={{ fill: agentColor, r: 4 }}
                  name="Overall Score"
                />
                <Line
                  type="monotone"
                  dataKey="accuracy"
                  stroke="var(--metric-tokens)"
                  strokeWidth={1}
                  strokeDasharray="5 5"
                  dot={false}
                  name="Accuracy"
                />
                <Line
                  type="monotone"
                  dataKey="relevance"
                  stroke="var(--metric-llm-calls)"
                  strokeWidth={1}
                  strokeDasharray="5 5"
                  dot={false}
                  name="Relevance"
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>
      )}

      {/* Category Performance */}
      {categoryData.length > 0 && (
        <div className="space-y-3">
          <div className="flex items-center gap-2">
            <Target className="h-4 w-4 text-[var(--mc-accent-blue)]" />
            <h3 className="text-sm font-semibold text-[var(--mc-text-primary)]">
              Category Performance
            </h3>
          </div>
          <div className="bg-[var(--mc-bg-secondary)] border border-[var(--mc-border)] rounded-lg p-4">
            <ResponsiveContainer width="100%" height={200}>
              <BarChart data={categoryData}>
                <CartesianGrid strokeDasharray="3 3" stroke="var(--mc-border)" />
                <XAxis
                  dataKey="category"
                  stroke="var(--mc-text-tertiary)"
                  style={{ fontSize: "12px" }}
                />
                <YAxis
                  domain={[0, 1]}
                  stroke="var(--mc-text-tertiary)"
                  style={{ fontSize: "12px" }}
                />
                <Tooltip
                  contentStyle={{
                    backgroundColor: "var(--mc-bg-tertiary)",
                    border: "1px solid var(--mc-border)",
                    borderRadius: "6px",
                    fontSize: "12px",
                  }}
                />
                <Bar dataKey="score" fill={agentColor} name="Avg Score" />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      )}

      {/* Task Completion Stats */}
      <div className="space-y-3">
        <div className="flex items-center gap-2">
          <BarChart3 className="h-4 w-4 text-[var(--mc-accent-blue)]" />
          <h3 className="text-sm font-semibold text-[var(--mc-text-primary)]">
            Performance Summary
          </h3>
        </div>
        <div className="bg-[var(--mc-bg-secondary)] border border-[var(--mc-border)] rounded-lg p-4">
          {completionData.length > 0 && (
            <ResponsiveContainer width="100%" height={150}>
              <BarChart data={completionData}>
                <CartesianGrid strokeDasharray="3 3" stroke="var(--mc-border)" />
                <XAxis
                  dataKey="name"
                  stroke="var(--mc-text-tertiary)"
                  style={{ fontSize: "12px" }}
                />
                <YAxis stroke="var(--mc-text-tertiary)" style={{ fontSize: "12px" }} />
                <Tooltip
                  contentStyle={{
                    backgroundColor: "var(--mc-bg-tertiary)",
                    border: "1px solid var(--mc-border)",
                    borderRadius: "6px",
                    fontSize: "12px",
                  }}
                />
                <Bar dataKey="count" name="Tasks" />
              </BarChart>
            </ResponsiveContainer>
          )}
          <div className={completionData.length > 0 ? "mt-3 flex justify-around text-center" : "flex justify-around text-center"}>
            <div>
              <div className="text-2xl font-bold text-[var(--mc-text-primary)]">
                {stats.total_tasks}
              </div>
              <div className="text-xs text-gray-400">Total</div>
            </div>
            {stats.successful_tasks !== undefined && (
              <div>
                <div className="text-2xl font-bold text-green-400">
                  {stats.successful_tasks}
                </div>
                <div className="text-xs text-gray-400">Success</div>
              </div>
            )}
            {stats.failed_tasks !== undefined && (
              <div>
                <div className="text-2xl font-bold text-blue-400">
                  {stats.failed_tasks}
                </div>
                <div className="text-xs text-gray-400">Failed</div>
              </div>
            )}
            <div>
              <div className="text-2xl font-bold text-yellow-400">
                {stats.avg_overall_score !== null ? stats.avg_overall_score.toFixed(2) : "N/A"}
              </div>
              <div className="text-xs text-gray-400">Avg Score</div>
            </div>
            {stats.rank !== undefined && (
              <div>
                <div className="text-2xl font-bold text-[var(--mc-accent-blue)]">
                  #{stats.rank}
                </div>
                <div className="text-xs text-gray-400">Rank</div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
