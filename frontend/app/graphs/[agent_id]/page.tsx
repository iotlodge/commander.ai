"use client";

import { useParams, useRouter } from 'next/navigation';
import { FullGraphViewer } from '@/components/graphs/full-graph-viewer';
import { Button } from '@/components/ui/button';
import { ArrowLeft } from 'lucide-react';

export default function AgentGraphPage() {
  const params = useParams();
  const router = useRouter();
  const agentId = params.agent_id as string;

  return (
    <div className="h-screen w-screen bg-[#1e2433] flex flex-col">
      {/* Header */}
      <div className="flex items-center justify-between px-6 py-4 bg-[#2a3444] border-b border-gray-700">
        <div className="flex items-center gap-4">
          <Button
            variant="ghost"
            size="sm"
            onClick={() => router.push('/')}
            className="text-gray-300 hover:text-white"
          >
            <ArrowLeft className="h-4 w-4 mr-2" />
            Back to Dashboard
          </Button>
          <div className="text-sm text-gray-500">
            Commander.ai › Graphs › <span className="text-white">@{agentId}</span>
          </div>
        </div>
      </div>

      {/* Graph Viewer */}
      <div className="flex-1 overflow-hidden">
        <FullGraphViewer agentId={agentId} />
      </div>
    </div>
  );
}
