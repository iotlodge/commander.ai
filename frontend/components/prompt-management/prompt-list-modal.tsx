"use client";

import { useState, useEffect } from "react";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { usePrompts, AgentPrompt } from "@/lib/hooks/use-prompts";
import { PromptCard } from "./prompt-card";
import { PromptEditorModal } from "./prompt-editor-modal";
import { Search, Plus, Filter } from "lucide-react";

interface PromptListModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  agentId: string;
  agentNickname: string;
  agentName: string;
}

export function PromptListModal({
  open,
  onOpenChange,
  agentId,
  agentNickname,
  agentName,
}: PromptListModalProps) {
  const { prompts, isLoading, error, fetchPrompts, deletePrompt } = usePrompts(agentId);

  const [searchQuery, setSearchQuery] = useState("");
  const [filterType, setFilterType] = useState<string | undefined>(undefined);
  const [filterActive, setFilterActive] = useState<boolean>(true);
  const [selectedPrompt, setSelectedPrompt] = useState<AgentPrompt | null>(null);
  const [showEditor, setShowEditor] = useState(false);
  const [isCreating, setIsCreating] = useState(false);

  // Fetch prompts when modal opens
  useEffect(() => {
    if (open) {
      fetchPrompts({
        agent_id: agentId,
        active: filterActive,
        prompt_type: filterType,
        search: searchQuery || undefined,
      });
    }
  }, [open, agentId, filterActive, filterType, searchQuery, fetchPrompts]);

  // Filtered prompts (client-side additional filtering)
  const filteredPrompts = prompts.filter((p) => {
    if (searchQuery) {
      const query = searchQuery.toLowerCase();
      return (
        p.description.toLowerCase().includes(query) ||
        p.prompt_text.toLowerCase().includes(query)
      );
    }
    return true;
  });

  const handleCreateNew = () => {
    setSelectedPrompt(null);
    setIsCreating(true);
    setShowEditor(true);
  };

  const handleEditPrompt = (prompt: AgentPrompt) => {
    setSelectedPrompt(prompt);
    setIsCreating(false);
    setShowEditor(true);
  };

  const handleDeletePrompt = async (promptId: string) => {
    if (confirm("Are you sure you want to deactivate this prompt?")) {
      const success = await deletePrompt(promptId);
      if (success) {
        // Refresh list
        fetchPrompts({
          agent_id: agentId,
          active: filterActive,
          prompt_type: filterType,
        });
      }
    }
  };

  const handleEditorClose = () => {
    setShowEditor(false);
    setSelectedPrompt(null);
    setIsCreating(false);
    // Refresh list
    fetchPrompts({
      agent_id: agentId,
      active: filterActive,
      prompt_type: filterType,
    });
  };

  return (
    <>
      <Dialog open={open} onOpenChange={onOpenChange}>
        <DialogContent className="max-w-5xl max-h-[80vh] overflow-y-auto bg-[var(--mc-bg-secondary)] border-[var(--mc-border)]">
          <DialogHeader>
            <DialogTitle className="text-[var(--mc-text-primary)] text-xl">
              Manage Prompts - @{agentNickname} ({agentName})
            </DialogTitle>
          </DialogHeader>

          {/* Search & Filters */}
          <div className="space-y-3">
            {/* Search Bar */}
            <div className="flex items-center gap-2">
              <div className="flex-1 relative">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-[var(--mc-text-tertiary)]" />
                <Input
                  placeholder="Search prompts..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="pl-10 bg-[var(--mc-bg-primary)] border-[var(--mc-border)] text-[var(--mc-text-primary)]"
                />
              </div>
              <Button
                onClick={handleCreateNew}
                className="bg-[var(--mc-accent-blue)] hover:opacity-90 text-white"
              >
                <Plus className="h-4 w-4 mr-2" />
                New
              </Button>
            </div>

            {/* Filter Controls */}
            <div className="flex items-center gap-2 flex-wrap">
              <span className="text-xs text-[var(--mc-text-secondary)] flex items-center gap-1">
                <Filter className="h-3 w-3" />
                Filters:
              </span>

              {/* Type Filter */}
              <select
                value={filterType || "all"}
                onChange={(e) =>
                  setFilterType(e.target.value === "all" ? undefined : e.target.value)
                }
                className="text-xs bg-[var(--mc-bg-primary)] border border-[var(--mc-border)] rounded px-2 py-1 text-[var(--mc-text-primary)]"
              >
                <option value="all">All Types</option>
                <option value="system">System</option>
                <option value="human">Human</option>
                <option value="ai">AI</option>
              </select>

              {/* Active Filter */}
              <label className="flex items-center gap-1.5 text-xs text-[var(--mc-text-secondary)] cursor-pointer">
                <input
                  type="checkbox"
                  checked={filterActive}
                  onChange={(e) => setFilterActive(e.target.checked)}
                  className="rounded"
                />
                Active Only
              </label>

              {/* Results Count */}
              <span className="ml-auto text-xs text-[var(--mc-text-tertiary)]">
                Showing {filteredPrompts.length} of {prompts.length} prompts
              </span>
            </div>
          </div>

          {/* Prompt List */}
          <div className="space-y-2 min-h-[300px]">
            {isLoading && (
              <div className="text-center py-8 text-[var(--mc-text-secondary)]">
                Loading prompts...
              </div>
            )}

            {error && (
              <div className="text-center py-8 text-red-400">
                Error: {error}
              </div>
            )}

            {!isLoading && !error && filteredPrompts.length === 0 && (
              <div className="text-center py-8 text-[var(--mc-text-secondary)]">
                No prompts found. Click "New" to create one.
              </div>
            )}

            {!isLoading &&
              !error &&
              filteredPrompts.map((prompt) => (
                <PromptCard
                  key={prompt.id}
                  prompt={prompt}
                  onEdit={handleEditPrompt}
                  onDelete={handleDeletePrompt}
                />
              ))}
          </div>

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
        </DialogContent>
      </Dialog>

      {/* Editor Modal (nested) */}
      {showEditor && (
        <PromptEditorModal
          open={showEditor}
          onOpenChange={setShowEditor}
          agentId={agentId}
          agentNickname={agentNickname}
          prompt={selectedPrompt}
          isCreating={isCreating}
          onSuccess={handleEditorClose}
        />
      )}
    </>
  );
}
