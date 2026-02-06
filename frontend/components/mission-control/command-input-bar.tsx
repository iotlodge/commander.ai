"use client";

import { useState, useRef, useEffect, KeyboardEvent, forwardRef, useImperativeHandle } from "react";
import { Textarea } from "@/components/ui/textarea";
import { Button } from "@/components/ui/button";
import { useAgents } from "@/lib/hooks/use-agents";
import { useCommandSubmit } from "@/lib/hooks/use-command-submit";
import { Loader2, Send, Sparkles } from "lucide-react";

export interface CommandInputBarRef {
  focus: () => void;
  insertMention: (nickname: string) => void;
  setCommand: (command: string) => void;
}

interface CommandInputBarProps {
  chatMode?: boolean;
}

const CommandInputBarComponent = forwardRef<CommandInputBarRef, CommandInputBarProps>(({ chatMode = false }, ref) => {
  const { agents, isLoading: agentsLoading } = useAgents();
  const { submitCommand, isLoading, error } = useCommandSubmit({ agents });

  const [input, setInput] = useState("");
  const [showAutocomplete, setShowAutocomplete] = useState(false);
  const [mentionQuery, setMentionQuery] = useState("");
  const [cursorPosition, setCursorPosition] = useState(0);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  // Expose focus, insertMention, and setCommand methods to parent
  useImperativeHandle(ref, () => ({
    focus: () => textareaRef.current?.focus(),
    insertMention: (nickname: string) => {
      setInput(`@${nickname} `);
      setCursorPosition(nickname.length + 2);
      setTimeout(() => textareaRef.current?.focus(), 0);
    },
    setCommand: (command: string) => {
      setInput(command);
      setCursorPosition(command.length);
      setTimeout(() => textareaRef.current?.focus(), 0);
    },
  }));

  // Detect @mentions
  useEffect(() => {
    if (!textareaRef.current) return;

    const text = input;
    const position = cursorPosition;
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
    const beforeCursor = text.substring(0, position);
    const mentionStart = beforeCursor.lastIndexOf("@");

    let newText: string;
    let newPosition: number;

    if (mentionStart === -1) {
      newText = text.substring(0, position) + `@${nickname} ` + text.substring(position);
      newPosition = position + nickname.length + 2;
    } else {
      newText = text.substring(0, mentionStart) + `@${nickname} ` + text.substring(position);
      newPosition = mentionStart + nickname.length + 2;
    }

    setInput(newText);
    setShowAutocomplete(false);

    setTimeout(() => {
      textareaRef.current?.setSelectionRange(newPosition, newPosition);
      textareaRef.current?.focus();
      setCursorPosition(newPosition);
    }, 0);
  };

  const handleSubmit = async () => {
    if (!input.trim() || isLoading) return;

    try {
      if (chatMode) {
        // Send to chat API (simplified for now - just use regular command with @chat)
        await submitCommand(`@chat ${input}`);
      } else {
        await submitCommand(input);
      }
      setInput("");
      setCursorPosition(0);
      textareaRef.current?.focus();
    } catch (err) {
      console.error("Failed to submit command:", err);
    }
  };

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  return (
    <div className="relative p-4">
      {/* Autocomplete (disabled in chat mode) */}
      {showAutocomplete && !chatMode && (
        <div className="absolute bottom-full left-4 right-4 mb-2 bg-[var(--mc-hover)] border border-[var(--mc-border)] rounded-lg shadow-lg max-h-64 overflow-y-auto">
          {agents
            .filter(
              (agent) =>
                agent.nickname.toLowerCase().includes(mentionQuery.toLowerCase()) ||
                agent.specialization.toLowerCase().includes(mentionQuery.toLowerCase())
            )
            .map((agent) => (
              <button
                key={agent.id}
                onClick={() => handleAgentSelect(agent.nickname)}
                onMouseDown={(e) => e.preventDefault()}
                className="w-full px-4 py-2 text-left hover:bg-[var(--mc-border)] flex items-center gap-3 border-b border-[var(--mc-border)] last:border-b-0"
              >
                <div className="flex h-8 w-8 items-center justify-center rounded-full bg-[var(--mc-accent-blue)]/20 text-[var(--mc-accent-blue)] font-semibold">
                  {agent.nickname.charAt(0).toUpperCase()}
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2">
                    <span className="font-medium text-sm text-[var(--mc-text-primary)]">
                      @{agent.nickname}
                    </span>
                    <span className="text-xs text-[var(--mc-text-secondary)]">
                      {agent.specialization}
                    </span>
                  </div>
                  <p className="text-xs text-[var(--mc-text-tertiary)] truncate">
                    {agent.description}
                  </p>
                </div>
              </button>
            ))}
          {agents.filter(
            (agent) =>
              agent.nickname.toLowerCase().includes(mentionQuery.toLowerCase()) ||
              agent.specialization.toLowerCase().includes(mentionQuery.toLowerCase())
          ).length === 0 && (
            <div className="px-4 py-3 text-sm text-gray-400">
              No agents found
            </div>
          )}
        </div>
      )}

      {/* Input Area */}
      <div className="flex items-end gap-3">
        <div className="flex-1 relative">
          <Textarea
            ref={textareaRef}
            value={input}
            onChange={handleInputChange}
            onKeyDown={handleKeyDown}
            placeholder={
              chatMode
                ? "Chat with LLM... (natural conversation, no @mention needed)"
                : "Type your command... (@agent to mention an AI agent)"
            }
            className="min-h-[60px] max-h-[200px] resize-none bg-[var(--mc-bg-primary)] border-[var(--mc-border)] text-[var(--mc-text-primary)] placeholder:text-[var(--mc-text-tertiary)] focus:border-[var(--mc-accent-blue)] focus:ring-1 focus:ring-[var(--mc-accent-blue)] pr-10"
            disabled={isLoading || agentsLoading}
          />
          <div className="absolute bottom-2 right-2 text-xs text-[var(--mc-text-tertiary)]">
            ↵ Send • ⇧↵ New line
          </div>
        </div>

        <Button
          onClick={handleSubmit}
          disabled={!input.trim() || isLoading || agentsLoading}
          size="lg"
          className="bg-[var(--mc-accent-blue)] hover:opacity-90 text-white h-[60px] px-6"
        >
          {isLoading ? (
            <>
              <Loader2 className="h-5 w-5 animate-spin mr-2" />
              Sending...
            </>
          ) : (
            <>
              <Send className="h-5 w-5 mr-2" />
              Send
            </>
          )}
        </Button>
      </div>

      {/* Error */}
      {error && (
        <div className="mt-2 text-sm text-red-400 flex items-center gap-2">
          <span>⚠️ {error}</span>
        </div>
      )}

      {/* Quick suggestions */}
      {!input && (
        <div className="mt-3 space-y-2">
          <div className="flex items-center gap-2 flex-wrap">
            <span className="text-xs text-gray-500 flex items-center gap-1">
              <Sparkles className="h-3 w-3" />
              Try:
            </span>
            {["@chat what's the weather?", "@bob research quantum computing", "@alice search web for AI news"].map(
              (suggestion, i) => (
                <button
                  key={i}
                  onClick={() => setInput(suggestion)}
                  className="text-xs bg-[var(--mc-bg-primary)] hover:bg-[var(--mc-bg-secondary)] border border-[var(--mc-border)] rounded px-2 py-1 text-[var(--mc-text-secondary)] hover:text-[var(--mc-text-primary)] transition-colors"
                >
                  {suggestion}
                </button>
              )
            )}
          </div>

          {/* Helpful hints */}
          <div className="text-[10px] text-[var(--mc-text-tertiary)] space-y-0.5">
            <div className="flex items-start gap-1.5">
              <span className="text-[var(--mc-accent-blue)] mt-0.5">💡</span>
              <span>
                <strong className="text-[var(--mc-text-secondary)]">Single @mention</strong> → Direct to that agent •
                <strong className="text-[var(--mc-text-secondary)] ml-1">Multiple @mentions</strong> → @leo orchestrates •
                <strong className="text-[var(--mc-text-secondary)] ml-1">No @mention</strong> → Defaults to @leo
              </span>
            </div>
          </div>
        </div>
      )}
    </div>
  );
});

CommandInputBarComponent.displayName = "CommandInputBar";

export const CommandInputBar = CommandInputBarComponent;
