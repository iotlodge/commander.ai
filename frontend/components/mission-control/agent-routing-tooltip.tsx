"use client";

import { useEffect, useState } from "react";
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/components/ui/popover";
import { Info, Target, Star, Zap } from "lucide-react";
import { usePerformance } from "@/lib/hooks/use-performance";

interface AgentRoutingTooltipProps {
  agentId: string;
  agentNickname: string;
  specialization: string;
}

export function AgentRoutingTooltip({
  agentId,
  agentNickname,
  specialization,
}: AgentRoutingTooltipProps) {
  const { fetchAgentPerformance } = usePerformance();
  const [stats, setStats] = useState<any>(null);
  const [loading, setLoading] = useState(false);

  const loadStats = async () => {
    try {
      setLoading(true);
      const data = await fetchAgentPerformance(agentId, undefined, 100);
      setStats(data.stats);
    } catch (err) {
      console.error("Failed to load agent stats:", err);
    } finally {
      setLoading(false);
    }
  };

  // Agent specialization insights
  const getSpecializationInsights = () => {
    const insights: Record<string, { description: string; strengths: string[] }> = {
      leo: {
        description: "Master orchestrator coordinating multi-agent workflows",
        strengths: [
          "Complex task decomposition",
          "Agent coordination",
          "Strategic planning",
        ],
      },
      chat: {
        description: "Conversational AI for natural interactions",
        strengths: [
          "Natural language understanding",
          "Quick responses",
          "User engagement",
        ],
      },
      bob: {
        description: "Research specialist with deep analysis capabilities",
        strengths: [
          "Information gathering",
          "Data synthesis",
          "Comprehensive research",
        ],
      },
      sue: {
        description: "Compliance and regulation expert",
        strengths: [
          "Regulatory analysis",
          "Compliance checking",
          "Policy interpretation",
        ],
      },
      rex: {
        description: "Data analysis and processing specialist",
        strengths: [
          "Statistical analysis",
          "Data visualization",
          "Pattern recognition",
        ],
      },
      alice: {
        description: "Document management and processing expert",
        strengths: [
          "Document analysis",
          "Content extraction",
          "File processing",
        ],
      },
      maya: {
        description: "Reflection and quality assurance specialist",
        strengths: [
          "Output validation",
          "Quality improvement",
          "Error detection",
        ],
      },
      kai: {
        description: "Reflexion and iterative refinement expert",
        strengths: [
          "Iterative improvement",
          "Self-correction",
          "Result optimization",
        ],
      },
    };

    return insights[agentNickname.toLowerCase()] || {
      description: specialization,
      strengths: [],
    };
  };

  const insights = getSpecializationInsights();

  return (
    <Popover onOpenChange={(open) => open && !stats && !loading && loadStats()}>
      <PopoverTrigger asChild>
        <button
          onClick={(e) => e.stopPropagation()}
          className="opacity-0 group-hover:opacity-100 hover:bg-[var(--mc-border)] p-1 rounded transition-opacity"
          title="Routing Insights"
        >
          <Info className="h-3 w-3 text-gray-500 dark:text-gray-400 hover:text-[var(--mc-accent-blue)]" />
        </button>
      </PopoverTrigger>
      <PopoverContent
        className="w-80 p-4 bg-[var(--mc-bg-tertiary)] border-[var(--mc-border)]"
        side="right"
      >
        <div className="space-y-3">
          {/* Header */}
          <div>
            <div className="flex items-center gap-2 mb-1">
              <Target className="h-4 w-4 text-[var(--mc-accent-blue)]" />
              <h4 className="font-semibold text-sm text-[var(--mc-text-primary)]">
                @{agentNickname}
              </h4>
            </div>
            <p className="text-xs text-gray-400">{insights.description}</p>
          </div>

          {/* Strengths */}
          {insights.strengths.length > 0 && (
            <div>
              <div className="flex items-center gap-1 mb-2">
                <Star className="h-3 w-3 text-yellow-500" />
                <span className="text-xs font-medium text-[var(--mc-text-secondary)]">
                  Key Strengths
                </span>
              </div>
              <ul className="space-y-1">
                {insights.strengths.map((strength, index) => (
                  <li
                    key={index}
                    className="text-xs text-gray-400 flex items-start gap-1"
                  >
                    <span className="text-[var(--mc-accent-blue)] mt-0.5">•</span>
                    <span>{strength}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* Category Performance */}
          {stats?.category_performance &&
            Object.keys(stats.category_performance).length > 0 && (
              <div>
                <div className="flex items-center gap-1 mb-2">
                  <Zap className="h-3 w-3 text-[var(--metric-tokens)]" />
                  <span className="text-xs font-medium text-[var(--mc-text-secondary)]">
                    Top Categories
                  </span>
                </div>
                <div className="space-y-1">
                  {Object.entries(stats.category_performance)
                    .sort(
                      ([, a]: any, [, b]: any) => b.avg_score - a.avg_score
                    )
                    .slice(0, 3)
                    .map(([category, data]: any) => (
                      <div
                        key={category}
                        className="flex items-center justify-between text-xs"
                      >
                        <span className="text-gray-400 capitalize">
                          {category}
                        </span>
                        <div className="flex items-center gap-2">
                          <div className="w-12 h-1.5 bg-[var(--mc-bg-primary)] rounded-full overflow-hidden">
                            <div
                              className="h-full bg-[var(--metric-tokens)]"
                              style={{ width: `${data.avg_score * 100}%` }}
                            />
                          </div>
                          <span className="text-[var(--mc-text-tertiary)] w-8 text-right">
                            {data.avg_score.toFixed(2)}
                          </span>
                        </div>
                      </div>
                    ))}
                </div>
              </div>
            )}

          {/* Performance Summary */}
          {stats && (
            <div className="pt-2 border-t border-[var(--mc-border)]">
              <div className="grid grid-cols-2 gap-2 text-xs">
                <div>
                  <div className="text-gray-500">Total Tasks</div>
                  <div className="text-[var(--mc-text-primary)] font-semibold">
                    {stats.total_tasks}
                  </div>
                </div>
                <div>
                  <div className="text-gray-500">Avg Score</div>
                  <div className="text-[var(--mc-text-primary)] font-semibold">
                    {stats.avg_overall_score?.toFixed(2) || "N/A"}
                  </div>
                </div>
              </div>
            </div>
          )}

          {loading && (
            <div className="text-center py-2">
              <span className="text-xs text-gray-500">Loading stats...</span>
            </div>
          )}
        </div>
      </PopoverContent>
    </Popover>
  );
}
