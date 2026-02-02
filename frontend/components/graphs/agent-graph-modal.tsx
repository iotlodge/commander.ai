"use client";

import { useState, useEffect } from 'react';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { X, Loader2 } from 'lucide-react';
import { Button } from '@/components/ui/button';
import mermaid from 'mermaid';

interface AgentGraph {
  agent_id: string;
  agent_nickname: string;
  mermaid_diagram: string;
  node_count: number;
  edge_count: number;
  last_updated: string;
}

interface AgentGraphModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export function AgentGraphModal({ isOpen, onClose }: AgentGraphModalProps) {
  const [graphs, setGraphs] = useState<AgentGraph[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedAgent, setSelectedAgent] = useState<string | null>(null);

  useEffect(() => {
    if (isOpen) {
      fetchGraphs();
    }
  }, [isOpen]);

  useEffect(() => {
    if (graphs.length > 0 && selectedAgent) {
      renderMermaid();
    }
  }, [selectedAgent, graphs]);

  async function fetchGraphs() {
    setLoading(true);
    setError(null);
    try {
      const response = await fetch('http://localhost:8000/api/graphs');

      if (!response.ok) {
        throw new Error(`API returned ${response.status}: ${response.statusText}`);
      }

      const data = await response.json();

      // Ensure data is an array
      if (!Array.isArray(data)) {
        console.error('API returned non-array data:', data);
        throw new Error('Invalid response format from API');
      }

      setGraphs(data);

      if (data.length > 0) {
        setSelectedAgent(data[0].agent_id);
      } else {
        setError('No agent graphs found. Agents may not be initialized yet.');
      }
    } catch (err) {
      console.error('Failed to fetch graphs:', err);
      setError(err instanceof Error ? err.message : 'Failed to fetch agent graphs');
      setGraphs([]);
    } finally {
      setLoading(false);
    }
  }

  async function renderMermaid() {
    if (!Array.isArray(graphs) || graphs.length === 0) return;

    const graph = graphs.find(g => g.agent_id === selectedAgent);
    if (!graph) return;

    try {
      // Initialize mermaid with dark theme and custom text colors
      mermaid.initialize({
        startOnLoad: false,
        theme: 'dark',
        flowchart: { curve: 'basis' },
        securityLevel: 'loose',
        themeVariables: {
          // Make node text much darker for better readability
          primaryTextColor: '#1a1a1a',      // Almost black for main text
          secondaryTextColor: '#2d3748',    // Dark gray for secondary text
          tertiaryTextColor: '#4a5568',     // Medium gray for tertiary text
          nodeTextColor: '#1a1a1a',         // Node label text (dark)
          labelTextColor: '#1a1a1a',        // Label text (dark)
          edgeLabelBackground: '#ffffff',   // White background for edge labels
        }
      });

      const element = document.getElementById('mermaid-diagram');
      if (element) {
        // Clear the element first
        element.innerHTML = '';

        // Create a unique ID for this render
        const uniqueId = `mermaid-${selectedAgent}-${Date.now()}`;

        // Render the diagram
        const { svg } = await mermaid.render(uniqueId, graph.mermaid_diagram);

        // Insert the rendered SVG
        element.innerHTML = svg;
      }
    } catch (error) {
      console.error('Mermaid rendering failed:', error);
      const element = document.getElementById('mermaid-diagram');
      if (element) {
        element.innerHTML = `<div class="text-red-400 p-4">Failed to render diagram: ${error instanceof Error ? error.message : 'Unknown error'}</div>`;
      }
    }
  }

  const selectedGraph = graphs.find(g => g.agent_id === selectedAgent);

  return (
    <Dialog open={isOpen} onOpenChange={(open) => !open && onClose()}>
      <DialogContent className="max-w-6xl max-h-[90vh] bg-[#1e2433] border-gray-700">
        <DialogHeader>
          <DialogTitle className="text-2xl font-bold text-white flex items-center justify-between">
            Agent Graph Visualizations
            <Button variant="ghost" size="sm" onClick={onClose}>
              <X className="h-5 w-5" />
            </Button>
          </DialogTitle>
        </DialogHeader>

        {loading ? (
          <div className="flex items-center justify-center py-20">
            <Loader2 className="h-8 w-8 animate-spin text-[#4a9eff]" />
            <span className="ml-3 text-gray-400">Loading agent graphs...</span>
          </div>
        ) : error ? (
          <div className="flex flex-col items-center justify-center py-20 text-center">
            <p className="text-red-400 mb-4">{error}</p>
            <Button
              onClick={fetchGraphs}
              variant="outline"
              size="sm"
              className="text-[#4a9eff] border-[#4a9eff]/30 hover:bg-[#4a9eff]/10"
            >
              Retry
            </Button>
            <p className="text-xs text-gray-500 mt-4">
              Make sure the backend is running and agents are initialized
            </p>
          </div>
        ) : graphs.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-20 text-center">
            <p className="text-gray-400 mb-2">No agent graphs available</p>
            <p className="text-xs text-gray-500">
              Restart the backend to generate agent graphs
            </p>
          </div>
        ) : (
          <div className="flex gap-4">
            {/* Agent selector sidebar */}
            <div className="w-48 space-y-2">
              {graphs.map((graph) => (
                <button
                  key={graph.agent_id}
                  onClick={() => setSelectedAgent(graph.agent_id)}
                  className={`w-full px-4 py-3 rounded-lg text-left transition-colors ${
                    selectedAgent === graph.agent_id
                      ? 'bg-[#4a9eff] text-white'
                      : 'bg-[#2a3444] text-gray-300 hover:bg-[#3a4454]'
                  }`}
                >
                  <div className="font-semibold">@{graph.agent_nickname}</div>
                  <div className="text-xs opacity-70">{graph.node_count} nodes</div>
                </button>
              ))}
            </div>

            {/* Graph display area */}
            <div className="flex-1 bg-[#2a3444] rounded-lg p-6 overflow-auto">
              {selectedGraph && (
                <>
                  <div className="mb-4 flex items-center justify-between">
                    <div>
                      <h3 className="text-xl font-bold text-white">
                        @{selectedGraph.agent_nickname}
                      </h3>
                      <p className="text-sm text-gray-400">
                        {selectedGraph.node_count} nodes • {selectedGraph.edge_count} edges
                      </p>
                    </div>
                    <div className="text-xs text-gray-500">
                      Updated: {new Date(selectedGraph.last_updated).toLocaleString()}
                    </div>
                  </div>

                  <div
                    id="mermaid-diagram"
                    className="mermaid bg-white/5 rounded-lg p-4 min-h-[400px]"
                  />
                </>
              )}
            </div>
          </div>
        )}
      </DialogContent>
    </Dialog>
  );
}
