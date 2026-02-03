"use client";

import { useState, useEffect, useRef } from 'react';
import { Button } from '@/components/ui/button';
import { ZoomIn, ZoomOut, Maximize2, Loader2 } from 'lucide-react';
import mermaid from 'mermaid';

interface AgentGraph {
  agent_id: string;
  agent_nickname: string;
  mermaid_diagram: string;
  node_count: number;
  edge_count: number;
  last_updated: string;
}

interface FullGraphViewerProps {
  agentId: string;
}

export function FullGraphViewer({ agentId }: FullGraphViewerProps) {
  const [graph, setGraph] = useState<AgentGraph | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [scale, setScale] = useState(1);
  const [position, setPosition] = useState({ x: 0, y: 0 });
  const [isDragging, setIsDragging] = useState(false);
  const [dragStart, setDragStart] = useState({ x: 0, y: 0 });

  const containerRef = useRef<HTMLDivElement>(null);
  const contentRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    fetchGraph();
  }, [agentId]);

  useEffect(() => {
    if (graph) {
      renderMermaid();
    }
  }, [graph]);

  async function fetchGraph() {
    setLoading(true);
    setError(null);
    try {
      const response = await fetch('http://localhost:8000/api/graphs');
      if (!response.ok) {
        throw new Error(`API returned ${response.status}: ${response.statusText}`);
      }
      const data = await response.json();

      // Find the graph for this agent by nickname or ID
      const foundGraph = data.find(
        (g: AgentGraph) => g.agent_nickname === agentId || g.agent_id === agentId
      );

      if (!foundGraph) {
        throw new Error(`Graph not found for agent: ${agentId}`);
      }

      setGraph(foundGraph);
    } catch (err) {
      console.error('Failed to fetch graph:', err);
      setError(err instanceof Error ? err.message : 'Failed to fetch agent graph');
    } finally {
      setLoading(false);
    }
  }

  async function renderMermaid() {
    if (!graph) return;

    try {
      // Initialize mermaid
      mermaid.initialize({
        startOnLoad: false,
        theme: 'dark',
        flowchart: {
          curve: 'basis',
          padding: 30,
          nodeSpacing: 100,
          rankSpacing: 100,
        },
        securityLevel: 'loose',
        themeVariables: {
          primaryTextColor: '#1a1a1a',
          secondaryTextColor: '#2d3748',
          tertiaryTextColor: '#4a5568',
          nodeTextColor: '#1a1a1a',
          labelTextColor: '#1a1a1a',
          edgeLabelBackground: '#ffffff',
        }
      });

      const element = document.getElementById('full-mermaid-diagram');
      if (element) {
        element.innerHTML = '';
        const uniqueId = `full-mermaid-${graph.agent_id}-${Date.now()}`;
        const { svg } = await mermaid.render(uniqueId, graph.mermaid_diagram);
        element.innerHTML = svg;

        // Center the graph initially
        centerGraph();
      }
    } catch (error) {
      console.error('Mermaid rendering failed:', error);
      setError('Failed to render diagram');
    }
  }

  function centerGraph() {
    if (!containerRef.current || !contentRef.current) return;

    const container = containerRef.current;
    const content = contentRef.current;
    const svg = content.querySelector('svg');

    if (!svg) return;

    // Get dimensions
    const containerRect = container.getBoundingClientRect();
    const svgRect = svg.getBoundingClientRect();

    // Calculate center position
    const x = (containerRect.width - svgRect.width * scale) / 2;
    const y = (containerRect.height - svgRect.height * scale) / 2;

    setPosition({ x, y });
  }

  function handleZoomIn() {
    setScale(prev => Math.min(prev + 0.2, 3));
  }

  function handleZoomOut() {
    setScale(prev => Math.max(prev - 0.2, 0.3));
  }

  function handleFitToScreen() {
    if (!containerRef.current || !contentRef.current) return;

    const container = containerRef.current;
    const svg = contentRef.current.querySelector('svg');
    if (!svg) return;

    const containerRect = container.getBoundingClientRect();
    const svgRect = svg.getBoundingClientRect();

    // Calculate scale to fit
    const scaleX = (containerRect.width - 40) / svgRect.width;
    const scaleY = (containerRect.height - 40) / svgRect.height;
    const newScale = Math.min(scaleX, scaleY, 1.5);

    setScale(newScale);

    // Center after fitting
    setTimeout(() => centerGraph(), 0);
  }

  function handleMouseDown(e: React.MouseEvent) {
    setIsDragging(true);
    setDragStart({
      x: e.clientX - position.x,
      y: e.clientY - position.y,
    });
  }

  function handleMouseMove(e: React.MouseEvent) {
    if (!isDragging) return;

    setPosition({
      x: e.clientX - dragStart.x,
      y: e.clientY - dragStart.y,
    });
  }

  function handleMouseUp() {
    setIsDragging(false);
  }

  function handleWheel(e: React.WheelEvent) {
    e.preventDefault();
    const delta = e.deltaY > 0 ? -0.1 : 0.1;
    setScale(prev => Math.max(0.3, Math.min(3, prev + delta)));
  }

  if (loading) {
    return (
      <div className="h-full flex items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin text-[#4a9eff]" />
        <span className="ml-3 text-gray-400">Loading agent graph...</span>
      </div>
    );
  }

  if (error) {
    return (
      <div className="h-full flex flex-col items-center justify-center">
        <p className="text-red-400 mb-4">{error}</p>
        <Button
          onClick={fetchGraph}
          variant="outline"
          size="sm"
          className="text-[#4a9eff] border-[#4a9eff]/30 hover:bg-[#4a9eff]/10"
        >
          Retry
        </Button>
      </div>
    );
  }

  if (!graph) {
    return (
      <div className="h-full flex items-center justify-center">
        <p className="text-gray-400">No graph data available</p>
      </div>
    );
  }

  return (
    <div className="h-full flex flex-col bg-[#1e2433]">
      {/* Graph Info Header */}
      <div className="px-6 py-3 bg-[#2a3444] border-b border-gray-700 flex items-center justify-between">
        <div>
          <h2 className="text-xl font-bold text-white">@{graph.agent_nickname}</h2>
          <p className="text-sm text-gray-400">
            {graph.node_count} nodes • {graph.edge_count} edges
          </p>
        </div>
        <div className="text-xs text-gray-500">
          Updated: {new Date(graph.last_updated).toLocaleString()}
        </div>
      </div>

      {/* Zoom Controls */}
      <div className="absolute bottom-6 right-6 z-10 flex flex-col gap-2">
        <Button
          onClick={handleZoomIn}
          size="sm"
          className="bg-slate-700 hover:bg-slate-600"
          title="Zoom In"
        >
          <ZoomIn className="h-4 w-4" />
        </Button>
        <Button
          onClick={handleZoomOut}
          size="sm"
          className="bg-slate-700 hover:bg-slate-600"
          title="Zoom Out"
        >
          <ZoomOut className="h-4 w-4" />
        </Button>
        <Button
          onClick={handleFitToScreen}
          size="sm"
          className="bg-slate-700 hover:bg-slate-600"
          title="Fit to Screen"
        >
          <Maximize2 className="h-4 w-4" />
        </Button>
        <div className="text-center text-xs text-gray-400 mt-1">
          {Math.round(scale * 100)}%
        </div>
      </div>

      {/* Graph Container */}
      <div
        ref={containerRef}
        className="flex-1 overflow-hidden relative bg-[#1a1f2e] cursor-grab active:cursor-grabbing"
        onMouseDown={handleMouseDown}
        onMouseMove={handleMouseMove}
        onMouseUp={handleMouseUp}
        onMouseLeave={handleMouseUp}
        onWheel={handleWheel}
      >
        <div
          ref={contentRef}
          style={{
            transform: `translate(${position.x}px, ${position.y}px) scale(${scale})`,
            transformOrigin: '0 0',
            transition: isDragging ? 'none' : 'transform 0.1s ease-out',
          }}
          className="absolute"
        >
          <div
            id="full-mermaid-diagram"
            className="p-8"
          />
        </div>
      </div>

      {/* Help Text */}
      <div className="px-6 py-2 bg-[#2a3444] border-t border-gray-700 text-xs text-gray-500 text-center">
        Use mouse wheel to zoom • Click and drag to pan • Click buttons to zoom or fit to screen
      </div>
    </div>
  );
}
