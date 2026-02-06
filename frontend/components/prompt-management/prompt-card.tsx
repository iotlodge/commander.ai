"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { AgentPrompt } from "@/lib/hooks/use-prompts";
import { Edit, Trash2, ChevronDown, ChevronUp } from "lucide-react";

interface PromptCardProps {
  prompt: AgentPrompt;
  onEdit: (prompt: AgentPrompt) => void;
  onDelete: (promptId: string) => void;
}

export function PromptCard({ prompt, onEdit, onDelete }: PromptCardProps) {
  const [isExpanded, setIsExpanded] = useState(false);

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString("en-US", {
      month: "short",
      day: "numeric",
      year: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    });
  };

  const getTypeColor = (type: string) => {
    switch (type) {
      case "system":
        return "bg-blue-500/10 text-blue-400 border-blue-500/30";
      case "human":
        return "bg-green-500/10 text-green-400 border-green-500/30";
      case "ai":
        return "bg-purple-500/10 text-purple-400 border-purple-500/30";
      default:
        return "bg-gray-500/10 text-gray-400 border-gray-500/30";
    }
  };

  return (
    <div className="w-full bg-[var(--mc-bg-primary)] border border-[var(--mc-border)] rounded-lg p-4 hover:bg-[var(--mc-hover)] transition-colors">
      {/* Header */}
      <div className="flex items-start justify-between gap-3 mb-2">
        <div className="flex-1 min-w-0">
          <h3 className="text-sm font-semibold text-[var(--mc-text-primary)] truncate">
            📝 {prompt.description}
          </h3>
        </div>
        <Button
          onClick={() => onEdit(prompt)}
          size="sm"
          variant="outline"
          className="border-[var(--mc-border)] text-[var(--mc-text-secondary)] hover:text-[var(--mc-text-primary)]"
        >
          <Edit className="h-3 w-3 mr-1" />
          Edit
        </Button>
      </div>

      {/* Metadata */}
      <div className="flex items-center gap-2 flex-wrap mb-2 text-xs">
        <Badge variant="outline" className={getTypeColor(prompt.prompt_type)}>
          Type: {prompt.prompt_type}
        </Badge>

        <Badge
          variant="outline"
          className={
            prompt.active
              ? "bg-green-500/10 text-green-400 border-green-500/30"
              : "bg-gray-500/10 text-gray-400 border-gray-500/30"
          }
        >
          {prompt.active ? "✓ Active" : "Inactive"}
        </Badge>

        <span className="text-[var(--mc-text-tertiary)]">
          Updated: {formatDate(prompt.updated_at)}
        </span>

        {/* Variable count */}
        {Object.keys(prompt.variables).length > 0 && (
          <span className="text-[var(--mc-text-tertiary)]">
            {Object.keys(prompt.variables).length} variable
            {Object.keys(prompt.variables).length !== 1 ? "s" : ""}
          </span>
        )}
      </div>

      {/* Preview (first 150 chars) */}
      <div className="text-xs text-[var(--mc-text-secondary)] mb-2">
        {isExpanded ? (
          <pre className="whitespace-pre-wrap break-words font-mono bg-[var(--mc-bg-secondary)] p-2 rounded border border-[var(--mc-border)] max-h-64 overflow-y-auto overflow-x-hidden">
            {prompt.prompt_text}
          </pre>
        ) : (
          <p className="line-clamp-2">
            {prompt.prompt_text.substring(0, 200)}
            {prompt.prompt_text.length > 200 && "..."}
          </p>
        )}
      </div>

      {/* Footer Actions */}
      <div className="flex items-center justify-between gap-2">
        <button
          onClick={() => setIsExpanded(!isExpanded)}
          className="text-xs text-[var(--mc-accent-blue)] hover:underline flex items-center gap-1"
        >
          {isExpanded ? (
            <>
              <ChevronUp className="h-3 w-3" />
              Show less
            </>
          ) : (
            <>
              <ChevronDown className="h-3 w-3" />
              Show full prompt
            </>
          )}
        </button>

        <button
          onClick={() => onDelete(prompt.id)}
          className="text-xs text-red-400 hover:text-red-300 flex items-center gap-1"
        >
          <Trash2 className="h-3 w-3" />
          Delete
        </button>
      </div>
    </div>
  );
}
