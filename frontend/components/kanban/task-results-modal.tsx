"use client";

import { useState } from 'react';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { X, FileText, CheckCircle, AlertCircle, Copy, Check, Maximize2, Minimize2, GitBranch, ChevronDown, ChevronRight, Clock, Zap } from 'lucide-react';
import { AgentTask, TaskStatus } from '@/lib/types';
import { MarkdownRenderer } from '@/components/ui/markdown-renderer';

interface TaskResultsModalProps {
  task: AgentTask | null;
  isOpen: boolean;
  onClose: () => void;
}

export function TaskResultsModal({ task, isOpen, onClose }: TaskResultsModalProps) {
  const [copied, setCopied] = useState(false);
  const [isMaximized, setIsMaximized] = useState(false);
  const [showExecutionTrace, setShowExecutionTrace] = useState(false);
  const [showMetadata, setShowMetadata] = useState(false); // Collapsed by default

  if (!task) return null;

  const isSuccess = task.status === TaskStatus.COMPLETED;
  const hasResult = task.result && task.result.trim().length > 0;
  const hasError = task.error_message && task.error_message.trim().length > 0;
  const executionTrace = task.metadata?.execution_trace as Array<{
    type: string;
    name: string;
    timestamp: string;
    duration_ms?: number;
    metadata?: Record<string, any>;
  }> | undefined;

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
      <DialogContent className={`${isMaximized ? 'w-[95vw] max-w-[95vw] max-h-[92vh] sm:max-w-[95vw]' : 'w-full max-w-6xl max-h-[85vh] sm:max-w-6xl'} bg-[#1e2433] border-gray-700 overflow-hidden flex flex-col transition-all duration-200`}>
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
              <Button
                variant="ghost"
                size="sm"
                onClick={() => setIsMaximized(!isMaximized)}
                className="hover:bg-gray-700/50"
                title={isMaximized ? "Restore size" : "Maximize"}
              >
                {isMaximized ? (
                  <Minimize2 className="h-5 w-5" />
                ) : (
                  <Maximize2 className="h-5 w-5" />
                )}
              </Button>
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

            <div className="pt-3 border-t border-[#3a4454]">
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
              <div className="bg-[#1e2433] rounded-md border border-[#3a4454]">
                <MarkdownRenderer
                  content={task.result}
                  variant="default"
                  className="p-4"
                />
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
              <div className="bg-[#1e2433] rounded-md border border-red-500/20">
                <MarkdownRenderer
                  content={task.error_message}
                  variant="error"
                  className="p-4"
                />
              </div>
            </div>
          )}

          {/* Execution Trace (Phase 1 - Simple Timeline) - MOVED UP */}
          {executionTrace && executionTrace.length > 0 && (
            <div className="bg-[#2a3444] rounded-lg p-4">
              <div
                className="flex items-center justify-between cursor-pointer mb-3"
                onClick={() => setShowExecutionTrace(!showExecutionTrace)}
              >
                <h3 className="text-sm font-semibold text-gray-400 flex items-center gap-2">
                  <GitBranch className="h-4 w-4 text-purple-400" />
                  Execution Flow
                  <span className="text-xs text-gray-500">
                    ({executionTrace.length} steps)
                  </span>
                </h3>
                <Button
                  variant="ghost"
                  size="sm"
                  className="hover:bg-gray-700/50"
                >
                  {showExecutionTrace ? (
                    <ChevronDown className="h-4 w-4" />
                  ) : (
                    <ChevronRight className="h-4 w-4" />
                  )}
                </Button>
              </div>

              {showExecutionTrace && (
                <div className="bg-[#1e2433] rounded-md border border-[#3a4454] p-4 space-y-3">
                  {executionTrace.map((step, index) => {
                    const stepIcon = step.type === 'node' ? (
                      <GitBranch className="h-4 w-4 text-blue-400" />
                    ) : step.type === 'tool' ? (
                      <Zap className="h-4 w-4 text-yellow-400" />
                    ) : (
                      <FileText className="h-4 w-4 text-purple-400" />
                    );

                    const stepColor = step.type === 'node'
                      ? 'border-blue-500/30 bg-blue-500/5'
                      : step.type === 'tool'
                      ? 'border-yellow-500/30 bg-yellow-500/5'
                      : 'border-purple-500/30 bg-purple-500/5';

                    return (
                      <div
                        key={index}
                        className={`flex items-start gap-3 p-3 rounded-md border ${stepColor}`}
                      >
                        <div className="mt-0.5">{stepIcon}</div>
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center justify-between gap-2 mb-1">
                            <span className="text-sm font-medium text-white truncate">
                              {step.name}
                            </span>
                            {step.duration_ms !== undefined && (
                              <div className="flex items-center gap-1 text-xs text-gray-400 flex-shrink-0">
                                <Clock className="h-3 w-3" />
                                {step.duration_ms < 1000
                                  ? `${Math.round(step.duration_ms)}ms`
                                  : `${(step.duration_ms / 1000).toFixed(2)}s`
                                }
                              </div>
                            )}
                          </div>
                          <div className="flex items-center gap-2 text-xs text-gray-500">
                            <span className="px-1.5 py-0.5 rounded bg-gray-700/50">
                              {step.type}
                            </span>
                            {step.metadata?.status === 'failed' && (
                              <span className="text-red-400">✗ Failed</span>
                            )}
                            {step.metadata?.tokens && (
                              <span className="text-green-400">
                                {step.metadata.tokens.total_tokens || step.metadata.tokens.total} tokens
                              </span>
                            )}
                          </div>
                          {step.metadata?.error && (
                            <div className="mt-2 text-xs text-red-400 bg-red-500/10 p-2 rounded">
                              Error: {step.metadata.error}
                            </div>
                          )}
                        </div>
                      </div>
                    );
                  })}
                </div>
              )}
            </div>
          )}

          {/* Performance Metrics */}
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

          {/* Metadata Section - MOVED TO BOTTOM, COLLAPSIBLE */}
          {task.metadata && Object.keys(task.metadata).length > 0 && (
            <div className="bg-[#2a3444] rounded-lg p-4">
              <div
                className="flex items-center justify-between cursor-pointer mb-3"
                onClick={() => setShowMetadata(!showMetadata)}
              >
                <h3 className="text-sm font-semibold text-gray-400 flex items-center gap-2">
                  <FileText className="h-4 w-4 text-gray-400" />
                  Metadata
                  <span className="text-xs text-gray-500">
                    (Full task details)
                  </span>
                </h3>
                <Button
                  variant="ghost"
                  size="sm"
                  className="hover:bg-gray-700/50"
                >
                  {showMetadata ? (
                    <ChevronDown className="h-4 w-4" />
                  ) : (
                    <ChevronRight className="h-4 w-4" />
                  )}
                </Button>
              </div>

              {showMetadata && (
                <div className="bg-[#1e2433] rounded-md p-4 border border-[#3a4454]">
                  <pre className="text-xs text-gray-400 whitespace-pre-wrap font-mono">
                    {JSON.stringify(task.metadata, null, 2)}
                  </pre>
                </div>
              )}
            </div>
          )}

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
