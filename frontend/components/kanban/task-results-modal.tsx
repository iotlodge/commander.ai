"use client";

import { useState } from 'react';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { X, FileText, CheckCircle, AlertCircle, Copy, Check } from 'lucide-react';
import { AgentTask, TaskStatus } from '@/lib/types';

interface TaskResultsModalProps {
  task: AgentTask | null;
  isOpen: boolean;
  onClose: () => void;
}

export function TaskResultsModal({ task, isOpen, onClose }: TaskResultsModalProps) {
  const [copied, setCopied] = useState(false);

  if (!task) return null;

  const isSuccess = task.status === TaskStatus.COMPLETED;
  const hasResult = task.result && task.result.trim().length > 0;
  const hasError = task.error_message && task.error_message.trim().length > 0;

  const handleCopy = async () => {
    const textToCopy = task.result || task.error_message || '';
    try {
      await navigator.clipboard.writeText(textToCopy);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch (err) {
      console.error('Failed to copy:', err);
    }
  };

  return (
    <Dialog open={isOpen} onOpenChange={(open) => !open && onClose()}>
      <DialogContent className="max-w-4xl max-h-[85vh] bg-[#1e2433] border-gray-700 overflow-hidden flex flex-col">
        <DialogHeader className="flex-shrink-0">
          <DialogTitle className="text-2xl font-bold text-white flex items-center justify-between">
            <div className="flex items-center gap-3">
              {isSuccess ? (
                <CheckCircle className="h-6 w-6 text-green-400" />
              ) : (
                <AlertCircle className="h-6 w-6 text-red-400" />
              )}
              <span>Task Results</span>
            </div>
            <div className="flex items-center gap-2">
              {(hasResult || hasError) && (
                <Button
                  variant="outline"
                  size="sm"
                  onClick={handleCopy}
                  className="gap-1.5 bg-blue-500/10 hover:bg-blue-500/20 text-blue-400 border-blue-500/30"
                >
                  {copied ? (
                    <>
                      <Check className="h-4 w-4" />
                      Copied!
                    </>
                  ) : (
                    <>
                      <Copy className="h-4 w-4" />
                      Copy
                    </>
                  )}
                </Button>
              )}
              <Button variant="ghost" size="sm" onClick={onClose}>
                <X className="h-5 w-5" />
              </Button>
            </div>
          </DialogTitle>
        </DialogHeader>

        <div className="flex-1 overflow-y-auto space-y-4 pr-2">
          {/* Task Info */}
          <div className="bg-[#2a3444] rounded-lg p-4">
            <div className="flex items-start gap-3 mb-3">
              <FileText className="h-5 w-5 text-[#4a9eff] mt-0.5" />
              <div className="flex-1">
                <h3 className="text-sm font-semibold text-gray-400 mb-1">Command</h3>
                <p className="text-white">{task.command_text}</p>
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4 pt-3 border-t border-[#3a4454]">
              <div>
                <p className="text-xs text-gray-500">Agent</p>
                <p className="text-sm text-white">@{task.agent_nickname}</p>
              </div>
              <div>
                <p className="text-xs text-gray-500">Status</p>
                <p className={`text-sm font-medium ${
                  isSuccess ? 'text-green-400' : 'text-red-400'
                }`}>
                  {task.status.replace('_', ' ').toUpperCase()}
                </p>
              </div>
            </div>
          </div>

          {/* Results Section */}
          {hasResult && (
            <div className="bg-[#2a3444] rounded-lg p-4">
              <h3 className="text-sm font-semibold text-gray-400 mb-3 flex items-center gap-2">
                <CheckCircle className="h-4 w-4 text-green-400" />
                Result
              </h3>
              <div className="bg-[#1e2433] rounded-md p-4 border border-[#3a4454]">
                <pre className="text-sm text-gray-300 whitespace-pre-wrap font-mono">
                  {task.result}
                </pre>
              </div>
            </div>
          )}

          {/* Error Section */}
          {hasError && (
            <div className="bg-red-500/10 border border-red-500/30 rounded-lg p-4">
              <h3 className="text-sm font-semibold text-red-400 mb-3 flex items-center gap-2">
                <AlertCircle className="h-4 w-4" />
                Error
              </h3>
              <div className="bg-[#1e2433] rounded-md p-4 border border-red-500/20">
                <pre className="text-sm text-red-300 whitespace-pre-wrap font-mono">
                  {task.error_message}
                </pre>
              </div>
            </div>
          )}

          {/* Metadata Section */}
          {task.metadata && Object.keys(task.metadata).length > 0 && (
            <div className="bg-[#2a3444] rounded-lg p-4">
              <h3 className="text-sm font-semibold text-gray-400 mb-3">Metadata</h3>
              <div className="bg-[#1e2433] rounded-md p-4 border border-[#3a4454]">
                <pre className="text-xs text-gray-400 whitespace-pre-wrap font-mono">
                  {JSON.stringify(task.metadata, null, 2)}
                </pre>
              </div>
            </div>
          )}

          {/* Metrics */}
          <div className="bg-[#2a3444] rounded-lg p-4">
            <h3 className="text-sm font-semibold text-gray-400 mb-3">Performance Metrics</h3>
            <div className="grid grid-cols-3 gap-4">
              <div className="text-center p-3 bg-[#1e2433] rounded-md border border-[#3a4454]">
                <div className="text-xs text-gray-500 mb-1">LLM Calls</div>
                <div className="text-lg font-semibold text-[#4a9eff]">
                  {task.metadata?.execution_metrics?.llm_calls ?? 0}
                </div>
              </div>
              <div className="text-center p-3 bg-[#1e2433] rounded-md border border-[#3a4454]">
                <div className="text-xs text-gray-500 mb-1">Agent Calls</div>
                <div className="text-lg font-semibold text-purple-400">
                  {task.metadata?.execution_metrics?.agent_calls ?? 0}
                </div>
              </div>
              <div className="text-center p-3 bg-[#1e2433] rounded-md border border-[#3a4454]">
                <div className="text-xs text-gray-500 mb-1">Total Tokens</div>
                <div className="text-lg font-semibold text-green-400">
                  {task.metadata?.execution_metrics?.tokens?.total?.toLocaleString() ?? 0}
                </div>
              </div>
            </div>
          </div>

          {/* No Content Message */}
          {!hasResult && !hasError && (
            <div className="bg-[#2a3444] rounded-lg p-8 text-center">
              <FileText className="h-12 w-12 text-gray-600 mx-auto mb-3" />
              <p className="text-gray-400">No results or errors to display</p>
              <p className="text-sm text-gray-500 mt-2">
                This task completed without producing output
              </p>
            </div>
          )}
        </div>
      </DialogContent>
    </Dialog>
  );
}
