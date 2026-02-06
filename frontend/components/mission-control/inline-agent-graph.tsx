"use client";

import { useState, useEffect } from 'react';
import { Loader2, ZoomIn, ZoomOut, Maximize2 } from 'lucide-react';
import mermaid from 'mermaid';
import { useTheme } from '@/components/providers/theme-provider';

interface AgentGraph {
  agent_id: string;
  agent_nickname: string;
  mermaid_diagram: string;
  node_count: number;
  edge_count: number;
  last_updated: string;
}

interface InlineAgentGraphProps {
  agentNickname: string;
}

const MVP_USER_ID = "00000000-0000-0000-0000-000000000001";

export function InlineAgentGraph({ agentNickname }: InlineAgentGraphProps) {
  const [graph, setGraph] = useState<AgentGraph | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [zoom, setZoom] = useState(0.7); // Start at 70% for better initial view
  const { resolvedTheme } = useTheme();

  useEffect(() => {
    fetchGraph();
  }, [agentNickname]);

  useEffect(() => {
    if (graph) {
      renderMermaid();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [graph, resolvedTheme]);

  async function fetchGraph() {
    setLoading(true);
    setError(null);
    try {
      const response = await fetch(`http://localhost:8000/api/graphs?user_id=${MVP_USER_ID}`);

      if (!response.ok) {
        throw new Error(`Failed to fetch graphs: ${response.status}`);
      }

      const data = await response.json();

      if (!Array.isArray(data)) {
        throw new Error('Invalid response format');
      }

      // Find the graph for this agent
      const agentGraph = data.find(g => g.agent_nickname === agentNickname);

      if (!agentGraph) {
        setError(`No graph found for @${agentNickname}`);
      } else {
        setGraph(agentGraph);
      }
    } catch (err) {
      console.error('Failed to fetch agent graph:', err);
      setError(err instanceof Error ? err.message : 'Failed to load graph');
    } finally {
      setLoading(false);
    }
  }

  async function renderMermaid() {
    if (!graph) return;

    try {
      const isDark = resolvedTheme === 'dark';

      mermaid.initialize({
        startOnLoad: false,
        theme: isDark ? 'dark' : 'default',
        flowchart: {
          curve: 'basis',
          padding: 15,
          nodeSpacing: 60,
          rankSpacing: 60,
        },
        securityLevel: 'loose',
        themeVariables: isDark ? {
          primaryTextColor: '#1a1a1a',
          secondaryTextColor: '#2d3748',
          tertiaryTextColor: '#4a5568',
          nodeTextColor: '#1a1a1a',
          labelTextColor: '#1a1a1a',
          edgeLabelBackground: '#ffffff',
        } : {
          primaryTextColor: '#1a1a1a',
          secondaryTextColor: '#2d3748',
          tertiaryTextColor: '#4a5568',
          nodeTextColor: '#1a1a1a',
          labelTextColor: '#1a1a1a',
          edgeLabelBackground: '#ffffff',
        }
      });

      const element = document.getElementById(`mermaid-inline-${agentNickname}`);
      if (element) {
        element.innerHTML = '';

        const uniqueId = `mermaid-inline-${agentNickname}-${Date.now()}`;
        const { svg } = await mermaid.render(uniqueId, graph.mermaid_diagram);

        element.innerHTML = svg;

        const svgElement = element.querySelector('svg');
        if (svgElement) {
          svgElement.style.maxWidth = '100%';
          svgElement.style.height = 'auto';
          svgElement.removeAttribute('height');
          svgElement.setAttribute('preserveAspectRatio', 'xMidYMid meet');
        }
      }
    } catch (error) {
      console.error('Mermaid rendering failed:', error);
      setError('Failed to render graph diagram');
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center py-8 bg-[var(--mc-bg-primary)] rounded-lg border border-[var(--mc-border)]">
        <Loader2 className="h-5 w-5 animate-spin text-[var(--mc-accent-blue)] mr-2" />
        <span className="text-sm text-gray-400">Loading graph...</span>
      </div>
    );
  }

  if (error) {
    return (
      <div className="py-8 bg-[var(--mc-bg-primary)] rounded-lg border border-red-500/30">
        <p className="text-sm text-red-400 text-center">{error}</p>
      </div>
    );
  }

  if (!graph) {
    return null;
  }

  const handleZoomIn = () => setZoom(prev => Math.min(prev + 0.1, 2.0));
  const handleZoomOut = () => setZoom(prev => Math.max(prev - 0.1, 0.3));
  const handleResetZoom = () => setZoom(0.7);

  return (
    <div className="bg-[var(--mc-bg-primary)] rounded-lg border border-[var(--mc-border)] overflow-hidden">
      <div className="px-4 py-3 bg-[var(--mc-hover)] border-b border-[var(--mc-border)]">
        <div className="flex items-center justify-between">
          <div>
            <h4 className="text-sm font-semibold text-[var(--mc-text-primary)]">
              Agent Graph: @{agentNickname}
            </h4>
            <p className="text-xs text-[var(--mc-text-secondary)]">
              {graph.node_count} nodes • {graph.edge_count} edges
            </p>
          </div>
          {/* Zoom Controls */}
          <div className="flex items-center gap-2">
            <button
              onClick={handleZoomOut}
              className="p-1.5 bg-[var(--mc-bg-primary)] hover:bg-[var(--mc-bg-secondary)] border border-[var(--mc-border)] rounded text-gray-400 hover:text-white transition-colors"
              title="Zoom out"
            >
              <ZoomOut className="h-3 w-3" />
            </button>
            <button
              onClick={handleResetZoom}
              className="px-2 py-1 bg-[var(--mc-bg-primary)] hover:bg-[var(--mc-bg-secondary)] border border-[var(--mc-border)] rounded text-xs text-gray-400 hover:text-white transition-colors"
              title="Reset zoom"
            >
              {Math.round(zoom * 100)}%
            </button>
            <button
              onClick={handleZoomIn}
              className="p-1.5 bg-[var(--mc-bg-primary)] hover:bg-[var(--mc-bg-secondary)] border border-[var(--mc-border)] rounded text-gray-400 hover:text-white transition-colors"
              title="Zoom in"
            >
              <ZoomIn className="h-3 w-3" />
            </button>
          </div>
        </div>
      </div>
      <div className="bg-white/5 dark:bg-white/5 p-4 overflow-auto max-h-[500px]">
        <div
          id={`mermaid-inline-${agentNickname}`}
          className="flex items-center justify-center min-h-[300px]"
          style={{
            transform: `scale(${zoom})`,
            transformOrigin: 'top left',
            transition: 'transform 0.2s ease-out'
          }}
        />
      </div>
    </div>
  );
}
