"use client";

import { useState, useRef, useEffect, KeyboardEvent } from "react";
import { Textarea } from "@/components/ui/textarea";
import { Button } from "@/components/ui/button";
import { AgentMentionAutocomplete } from "./agent-mention-autocomplete";
import { AgentInfo } from "@/lib/types";
import { Loader2, Send, Package, GitBranch } from "lucide-react";
import { AgentGraphModal } from "@/components/graphs/agent-graph-modal";
import { useGraphModal } from "@/lib/hooks/use-graph-modal";

// Mock agent data - this should come from an API endpoint in production
const MOCK_AGENTS: AgentInfo[] = [
  {
    id: "agent_a",
    nickname: "bob",
    specialization: "Research Specialist",
    description: "Deep research and information synthesis",
  },
  {
    id: "agent_b",
    nickname: "sue",
    specialization: "Compliance Specialist",
    description: "Regulatory compliance and policy adherence",
  },
  {
    id: "agent_c",
    nickname: "rex",
    specialization: "Data Analyst",
    description: "Data analysis and visualization",
  },
  {
    id: "parent",
    nickname: "leo",
    specialization: "Orchestrator",
    description: "Workflow coordination and task delegation",
  },
];

interface CommandInputProps {
  onSubmit?: (command: string) => Promise<void>;
  isLoading?: boolean;
  error?: string | null;
}

export function CommandInput({
  onSubmit,
  isLoading = false,
  error = null,
}: CommandInputProps) {
  const [input, setInput] = useState("");
  const [showAutocomplete, setShowAutocomplete] = useState(false);
  const [mentionQuery, setMentionQuery] = useState("");
  const [cursorPosition, setCursorPosition] = useState(0);
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const { isOpen, openModal, closeModal } = useGraphModal();

  // Detect @mentions and show autocomplete
  useEffect(() => {
    if (!textareaRef.current) return;

    const text = input;
    const position = cursorPosition;

    // Find if we're in the middle of an @mention
    const beforeCursor = text.substring(0, position);
    const match = beforeCursor.match(/@(\w*)$/);

    if (match) {
      setMentionQuery(match[1]);
      setShowAutocomplete(true);
    } else {
      setShowAutocomplete(false);
      setMentionQuery("");
    }
  }, [input, cursorPosition]);

  const handleInputChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setInput(e.target.value);
    setCursorPosition(e.target.selectionStart);
  };

  const handleAgentSelect = (nickname: string) => {
    if (!textareaRef.current) return;

    const text = input;
    const position = cursorPosition;

    // Find the @ symbol before cursor
    const beforeCursor = text.substring(0, position);
    const mentionStart = beforeCursor.lastIndexOf("@");

    if (mentionStart === -1) return;

    // Replace @partial with @nickname
    const newText =
      text.substring(0, mentionStart) +
      `@${nickname} ` +
      text.substring(position);

    setInput(newText);
    setShowAutocomplete(false);

    // Set cursor position after the inserted mention
    setTimeout(() => {
      const newPosition = mentionStart + nickname.length + 2; // +2 for @ and space
      textareaRef.current?.setSelectionRange(newPosition, newPosition);
      textareaRef.current?.focus();
      setCursorPosition(newPosition);
    }, 0);
  };

  const handleSubmit = async () => {
    if (!input.trim() || isLoading) return;

    try {
      await onSubmit?.(input);
      setInput("");
    } catch (err) {
      console.error("Command submission error:", err);
    }
  };

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    // Submit on Cmd+Enter or Ctrl+Enter
    if ((e.metaKey || e.ctrlKey) && e.key === "Enter") {
      e.preventDefault();
      handleSubmit();
    }
  };

  return (
    <div className="w-full max-w-6xl mx-auto p-4 bg-[#1e2433]">
      <div className="space-y-3">
        {/* Buttons row */}
        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            size="sm"
            disabled={true}
            className="text-gray-400 border-gray-600 hover:bg-gray-700/50"
            title="Batch multiple commands (coming soon)"
          >
            <Package className="h-4 w-4 mr-2" />
            Batch Tasks
          </Button>

          <Button
            variant="outline"
            size="sm"
            onClick={openModal}
            className="text-[#4a9eff] border-[#4a9eff]/30 hover:bg-[#4a9eff]/10"
          >
            <GitBranch className="h-4 w-4 mr-2" />
            View Agent Graphs
          </Button>
        </div>

        <div className="relative">
          <AgentMentionAutocomplete
            agents={MOCK_AGENTS}
            open={showAutocomplete}
            onOpenChange={setShowAutocomplete}
            onAgentSelect={handleAgentSelect}
            searchQuery={mentionQuery}
          >
            <Textarea
              ref={textareaRef}
              value={input}
              onChange={handleInputChange}
              onKeyDown={handleKeyDown}
              onClick={(e) =>
                setCursorPosition(
                  (e.target as HTMLTextAreaElement).selectionStart
                )
              }
              placeholder="Type a command or @mention an agent..."
              className="min-h-[80px] resize-none bg-[#2a3444] border-[#3a4454] text-white placeholder:text-gray-400 focus-visible:ring-[#4a9eff] focus-visible:border-[#4a9eff]"
              disabled={isLoading}
            />
          </AgentMentionAutocomplete>
        </div>

        <div className="flex items-center justify-between gap-4">
          <div className="text-xs text-gray-400">
            <span className="hidden sm:inline">
              Tip: <span className="text-[#4a9eff]">@bob</span> for research, <span className="text-[#4a9eff]">@sue</span> for compliance, <span className="text-[#4a9eff]">@rex</span> for data, <span className="text-[#4a9eff]">@leo</span> for orchestration
            </span>
            <span className="sm:hidden">Use @ to mention agents</span>
          </div>

          <Button
            onClick={handleSubmit}
            disabled={!input.trim() || isLoading}
            size="sm"
            className="gap-2 bg-[#4a9eff] hover:bg-[#3a8eef] text-white border-none"
          >
            {isLoading ? (
              <>
                <Loader2 className="h-4 w-4 animate-spin" />
                Submitting...
              </>
            ) : (
              <>
                <Send className="h-4 w-4" />
                Submit
              </>
            )}
          </Button>
        </div>

        {error && (
          <div className="text-sm text-red-400 bg-red-500/10 border border-red-500/20 rounded-md p-3">
            {error}
          </div>
        )}

        <div className="text-xs text-gray-500">
          <kbd className="pointer-events-none inline-flex h-5 select-none items-center gap-1 rounded border border-gray-600 bg-[#2a3444] px-1.5 font-mono text-[10px] font-medium text-gray-400">
            <span className="text-xs">⌘</span>Enter
          </kbd>{" "}
          to submit
        </div>
      </div>

      {/* Graph Modal */}
      <AgentGraphModal isOpen={isOpen} onClose={closeModal} />
    </div>
  );
}
