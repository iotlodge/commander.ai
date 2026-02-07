"use client";

import { useEffect, useState } from "react";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { PerformanceCharts } from "./performance-charts";
import { usePerformance } from "@/lib/hooks/use-performance";
import { Loader2, TrendingUp } from "lucide-react";

interface AgentPerformanceModalProps {
  agentId: string | null;
  agentNickname: string;
  isOpen: boolean;
  onClose: () => void;
}

export function AgentPerformanceModal({
  agentId,
  agentNickname,
  isOpen,
  onClose,
}: AgentPerformanceModalProps) {
  const { fetchAgentPerformance } = usePerformance();
  const [loading, setLoading] = useState(false);
  const [data, setData] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (isOpen && agentId) {
      loadPerformanceData();
    }
  }, [isOpen, agentId]);

  const loadPerformanceData = async () => {
    if (!agentId) return;

    try {
      setLoading(true);
      setError(null);
      const result = await fetchAgentPerformance(agentId);
      setData(result);
    } catch (err) {
      setError("Failed to load performance data");
      console.error("Performance data error:", err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="max-w-4xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <TrendingUp className="h-5 w-5 text-[var(--mc-accent-blue)]" />
            <span>@{agentNickname} Performance Analytics</span>
          </DialogTitle>
        </DialogHeader>

        <div className="mt-4">
          {loading && (
            <div className="flex items-center justify-center py-12">
              <Loader2 className="h-8 w-8 animate-spin text-[var(--mc-accent-blue)]" />
              <span className="ml-3 text-sm text-gray-400">Loading performance data...</span>
            </div>
          )}

          {error && (
            <div className="text-center py-12">
              <p className="text-sm text-red-400">{error}</p>
              <button
                onClick={loadPerformanceData}
                className="mt-3 text-xs text-blue-400 hover:text-blue-300"
              >
                Retry
              </button>
            </div>
          )}

          {data && !loading && !error && (
            <>
              {data.scores.length === 0 ? (
                <div className="text-center py-12">
                  <p className="text-sm text-gray-400">
                    No performance data yet for @{agentNickname}
                  </p>
                  <p className="text-xs text-gray-500 mt-1">
                    Complete some tasks to see analytics
                  </p>
                </div>
              ) : (
                <PerformanceCharts
                  scores={data.scores}
                  stats={data.stats}
                  agentNickname={agentNickname}
                />
              )}
            </>
          )}
        </div>
      </DialogContent>
    </Dialog>
  );
}
