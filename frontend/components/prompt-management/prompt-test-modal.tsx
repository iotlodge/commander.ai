"use client";

import { useState } from "react";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Label } from "@/components/ui/label";
import { usePrompts, PromptTestRequest, PromptTestResponse } from "@/lib/hooks/use-prompts";
import { MarkdownRenderer } from "@/components/ui/markdown-renderer";
import { Play, Loader2, ChevronDown, ChevronUp } from "lucide-react";

interface PromptTestModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  agentId: string;
  promptText: string;
  promptType: string;
}

export function PromptTestModal({
  open,
  onOpenChange,
  agentId,
  promptText,
  promptType,
}: PromptTestModalProps) {
  const { testPrompt, isLoading } = usePrompts();

  const [testQuery, setTestQuery] = useState("");
  const [testResult, setTestResult] = useState<PromptTestResponse | null>(null);
  const [showDebug, setShowDebug] = useState(false);

  const handleRunTest = async () => {
    if (!testQuery.trim()) {
      alert("Please enter a test query");
      return;
    }

    const request: PromptTestRequest = {
      agent_id: agentId,
      prompt_text: promptText,
      prompt_type: promptType,
      test_query: testQuery.trim(),
      test_context: {},
    };

    const result = await testPrompt(request);
    if (result) {
      setTestResult(result);
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-5xl max-h-[90vh] overflow-y-auto overflow-x-hidden bg-[var(--mc-bg-secondary)] border-[var(--mc-border)]">
        <DialogHeader>
          <DialogTitle className="text-[var(--mc-text-primary)] text-xl">
            Test Prompt
          </DialogTitle>
        </DialogHeader>

        <div className="space-y-4">
          {/* Test Query Input */}
          <div className="space-y-2">
            <Label htmlFor="testQuery" className="text-[var(--mc-text-secondary)]">
              Test Query
            </Label>
            <Textarea
              id="testQuery"
              value={testQuery}
              onChange={(e) => setTestQuery(e.target.value)}
              placeholder="Enter a test query to see how the LLM responds with this prompt..."
              rows={3}
              className="bg-[var(--mc-bg-primary)] border-[var(--mc-border)] text-[var(--mc-text-primary)]"
            />
          </div>

          {/* Run Test Button */}
          <Button
            onClick={handleRunTest}
            disabled={isLoading || !testQuery.trim()}
            className="bg-[var(--mc-accent-blue)] hover:opacity-90 text-white"
          >
            {isLoading ? (
              <>
                <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                Testing...
              </>
            ) : (
              <>
                <Play className="h-4 w-4 mr-2" />
                Run Test
              </>
            )}
          </Button>

          {/* Results Section */}
          {testResult && (
            <>
              {/* Divider */}
              <div className="border-t border-[var(--mc-border)] my-4" />

              {/* Metrics */}
              <div className="bg-[var(--mc-bg-primary)] border border-[var(--mc-border)] rounded-lg p-4">
                <h3 className="text-sm font-semibold text-[var(--mc-text-primary)] mb-3">
                  ⚡ Performance Metrics
                </h3>
                <div className="grid grid-cols-4 gap-4">
                  <div>
                    <div className="text-xs text-[var(--mc-text-tertiary)]">Response Time</div>
                    <div className="text-lg font-bold text-[var(--metric-duration)]">
                      {(testResult.metrics.response_time_ms / 1000).toFixed(1)}s
                    </div>
                  </div>
                  <div>
                    <div className="text-xs text-[var(--mc-text-tertiary)]">Total Tokens</div>
                    <div className="text-lg font-bold text-[var(--metric-tokens)]">
                      {testResult.metrics.total_tokens}
                    </div>
                  </div>
                  <div>
                    <div className="text-xs text-[var(--mc-text-tertiary)]">Prompt Tokens</div>
                    <div className="text-lg font-bold text-[var(--mc-text-secondary)]">
                      {testResult.metrics.prompt_tokens}
                    </div>
                  </div>
                  <div>
                    <div className="text-xs text-[var(--mc-text-tertiary)]">Completion Tokens</div>
                    <div className="text-lg font-bold text-[var(--mc-text-secondary)]">
                      {testResult.metrics.completion_tokens}
                    </div>
                  </div>
                </div>
              </div>

              {/* Generated Response */}
              <div className="space-y-2">
                <h3 className="text-sm font-semibold text-[var(--mc-text-primary)]">
                  Generated Response:
                </h3>
                <div className="bg-[var(--mc-bg-primary)] border border-[var(--mc-border)] rounded-lg p-4 max-h-96 overflow-y-auto">
                  <MarkdownRenderer content={testResult.generated_response} />
                </div>
              </div>

              {/* Debug: Compiled Messages */}
              <div className="space-y-2">
                <button
                  onClick={() => setShowDebug(!showDebug)}
                  className="text-sm text-[var(--mc-accent-blue)] hover:underline flex items-center gap-1"
                >
                  {showDebug ? (
                    <>
                      <ChevronUp className="h-4 w-4" />
                      Hide Debug Info
                    </>
                  ) : (
                    <>
                      <ChevronDown className="h-4 w-4" />
                      Show Debug Info (Compiled Messages)
                    </>
                  )}
                </button>

                {showDebug && (
                  <div className="bg-[var(--mc-bg-primary)] border border-[var(--mc-border)] rounded-lg p-4 max-h-64 overflow-y-auto">
                    {testResult.compiled_messages.map((msg, idx) => (
                      <div key={idx} className="mb-3">
                        <div className="text-xs font-semibold text-[var(--mc-accent-blue)] mb-1">
                          {msg.role.toUpperCase()}:
                        </div>
                        <pre className="text-xs text-[var(--mc-text-secondary)] whitespace-pre-wrap font-mono bg-[var(--mc-bg-secondary)] p-2 rounded">
                          {msg.content}
                        </pre>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </>
          )}

          {/* Footer */}
          <div className="flex justify-end pt-4 border-t border-[var(--mc-border)]">
            <Button
              onClick={() => onOpenChange(false)}
              variant="outline"
              className="border-[var(--mc-border)] text-[var(--mc-text-primary)]"
            >
              Close
            </Button>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
}
