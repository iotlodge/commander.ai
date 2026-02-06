"use client";

import { useState, useEffect } from "react";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Label } from "@/components/ui/label";
import { usePrompts, AgentPrompt, PromptCreate, PromptUpdate } from "@/lib/hooks/use-prompts";
import { PromptTestModal } from "./prompt-test-modal";
import { TestTube, Save, X } from "lucide-react";

interface PromptEditorModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  agentId: string;
  agentNickname: string;
  prompt?: AgentPrompt | null;
  isCreating: boolean;
  onSuccess: () => void;
}

export function PromptEditorModal({
  open,
  onOpenChange,
  agentId,
  agentNickname,
  prompt,
  isCreating,
  onSuccess,
}: PromptEditorModalProps) {
  const { createPrompt, updatePrompt, isLoading, error } = usePrompts();

  // Form state
  const [description, setDescription] = useState("");
  const [promptText, setPromptText] = useState("");
  const [promptType, setPromptType] = useState<"system" | "human" | "ai">("system");
  const [active, setActive] = useState(true);
  const [variables, setVariables] = useState<Record<string, string>>({});
  const [changeNote, setChangeNote] = useState("");

  // Test modal state
  const [showTestModal, setShowTestModal] = useState(false);

  // Initialize form when prompt changes
  useEffect(() => {
    if (prompt) {
      setDescription(prompt.description);
      setPromptText(prompt.prompt_text);
      setPromptType(prompt.prompt_type);
      setActive(prompt.active);
      setVariables(prompt.variables || {});
    } else {
      // Reset for new prompt
      setDescription("");
      setPromptText("");
      setPromptType("system");
      setActive(true);
      setVariables({});
      setChangeNote("");
    }
  }, [prompt]);

  const handleSave = async () => {
    if (!description.trim() || !promptText.trim()) {
      alert("Description and Prompt Text are required");
      return;
    }

    if (isCreating) {
      // Create new prompt
      const data: PromptCreate = {
        agent_id: agentId,
        nickname: agentNickname,
        description: description.trim(),
        prompt_text: promptText.trim(),
        active,
        prompt_type: promptType,
        variables,
      };

      const result = await createPrompt(data);
      if (result) {
        onSuccess();
      }
    } else if (prompt) {
      // Update existing prompt
      const data: PromptUpdate = {
        prompt_text: promptText.trim(),
        active,
        variables,
      };

      const result = await updatePrompt(prompt.id, data);
      if (result) {
        onSuccess();
      }
    }
  };

  const handleAddVariable = () => {
    const key = window.prompt(`Enter variable name (without curly braces):`);
    if (key && key.trim()) {
      const value = window.prompt(`Enter default value for {${key}}:`);
      setVariables((prev) => ({
        ...prev,
        [key.trim()]: value?.trim() || "",
      }));
    }
  };

  const handleRemoveVariable = (key: string) => {
    setVariables((prev) => {
      const newVars = { ...prev };
      delete newVars[key];
      return newVars;
    });
  };

  const handleUpdateVariable = (key: string, value: string) => {
    setVariables((prev) => ({
      ...prev,
      [key]: value,
    }));
  };

  return (
    <>
      <Dialog open={open} onOpenChange={onOpenChange}>
        <DialogContent className="max-w-5xl max-h-[90vh] overflow-y-auto bg-[var(--mc-bg-secondary)] border-[var(--mc-border)]">
          <DialogHeader>
            <DialogTitle className="text-[var(--mc-text-primary)] text-xl">
              {isCreating ? "Create New Prompt" : "Edit Prompt"}: @{agentNickname}
            </DialogTitle>
          </DialogHeader>

          <div className="space-y-4">
            {/* Description */}
            <div className="space-y-2">
              <Label htmlFor="description" className="text-[var(--mc-text-secondary)]">
                Description
              </Label>
              <Input
                id="description"
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                placeholder="Brief description of this prompt"
                className="bg-[var(--mc-bg-primary)] border-[var(--mc-border)] text-[var(--mc-text-primary)]"
              />
            </div>

            {/* Prompt Type */}
            <div className="space-y-2">
              <Label htmlFor="promptType" className="text-[var(--mc-text-secondary)]">
                Prompt Type
              </Label>
              <select
                id="promptType"
                value={promptType}
                onChange={(e) => setPromptType(e.target.value as any)}
                disabled={!isCreating} // Can't change type after creation
                className="w-full bg-[var(--mc-bg-primary)] border border-[var(--mc-border)] rounded px-3 py-2 text-[var(--mc-text-primary)] disabled:opacity-50"
              >
                <option value="system">System Message</option>
                <option value="human">Human Message</option>
                <option value="ai">AI Message</option>
              </select>
              {!isCreating && (
                <p className="text-xs text-[var(--mc-text-tertiary)]">
                  Prompt type cannot be changed after creation
                </p>
              )}
            </div>

            {/* Prompt Text */}
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <Label htmlFor="promptText" className="text-[var(--mc-text-secondary)]">
                  Prompt Text
                </Label>
                <Button
                  onClick={() => setShowTestModal(true)}
                  size="sm"
                  variant="outline"
                  className="border-[var(--mc-border)] text-[var(--mc-accent-blue)]"
                >
                  <TestTube className="h-3 w-3 mr-1" />
                  Test
                </Button>
              </div>
              <Textarea
                id="promptText"
                value={promptText}
                onChange={(e) => setPromptText(e.target.value)}
                placeholder="Enter prompt text here... Use {variable_name} for template variables"
                rows={15}
                className="font-mono text-xs bg-[var(--mc-bg-primary)] border-[var(--mc-border)] text-[var(--mc-text-primary)]"
              />
              <p className="text-xs text-[var(--mc-text-tertiary)]">
                Tip: Use {"{variable_name}"} for placeholders. Add variables below.
              </p>
            </div>

            {/* Variables */}
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <Label className="text-[var(--mc-text-secondary)]">
                  Variables (Template Placeholders)
                </Label>
                <Button
                  onClick={handleAddVariable}
                  size="sm"
                  variant="outline"
                  className="border-[var(--mc-border)] text-[var(--mc-text-secondary)]"
                >
                  + Add
                </Button>
              </div>

              {Object.keys(variables).length === 0 ? (
                <p className="text-xs text-[var(--mc-text-tertiary)] py-2">
                  No variables defined. Click "+ Add" to create one.
                </p>
              ) : (
                <div className="space-y-2 bg-[var(--mc-bg-primary)] p-3 rounded border border-[var(--mc-border)]">
                  {Object.entries(variables).map(([key, value]) => (
                    <div key={key} className="flex items-center gap-2">
                      <div className="flex-1 grid grid-cols-2 gap-2">
                        <Input
                          value={key}
                          disabled
                          className="bg-[var(--mc-bg-secondary)] border-[var(--mc-border)] text-[var(--mc-text-tertiary)] text-xs"
                        />
                        <Input
                          value={value}
                          onChange={(e) => handleUpdateVariable(key, e.target.value)}
                          placeholder="Default value"
                          className="bg-[var(--mc-bg-secondary)] border-[var(--mc-border)] text-[var(--mc-text-primary)] text-xs"
                        />
                      </div>
                      <button
                        onClick={() => handleRemoveVariable(key)}
                        className="text-red-400 hover:text-red-300 text-xs"
                      >
                        <X className="h-4 w-4" />
                      </button>
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* Active Toggle */}
            <div className="flex items-center gap-2">
              <input
                type="checkbox"
                id="active"
                checked={active}
                onChange={(e) => setActive(e.target.checked)}
                className="rounded"
              />
              <Label htmlFor="active" className="text-[var(--mc-text-secondary)] cursor-pointer">
                Active (Enable this prompt for use)
              </Label>
            </div>

            {/* Change Note (for updates) */}
            {!isCreating && (
              <div className="space-y-2">
                <Label htmlFor="changeNote" className="text-[var(--mc-text-secondary)]">
                  Change Note (optional)
                </Label>
                <Input
                  id="changeNote"
                  value={changeNote}
                  onChange={(e) => setChangeNote(e.target.value)}
                  placeholder="Briefly describe what you changed"
                  className="bg-[var(--mc-bg-primary)] border-[var(--mc-border)] text-[var(--mc-text-primary)]"
                />
              </div>
            )}

            {/* Error Display */}
            {error && (
              <div className="text-sm text-red-400 bg-red-500/10 border border-red-500/30 rounded p-3">
                ⚠️ {error}
              </div>
            )}

            {/* Footer Actions */}
            <div className="flex justify-end gap-2 pt-4 border-t border-[var(--mc-border)]">
              <Button
                onClick={() => onOpenChange(false)}
                variant="outline"
                className="border-[var(--mc-border)] text-[var(--mc-text-secondary)]"
                disabled={isLoading}
              >
                Cancel
              </Button>
              <Button
                onClick={handleSave}
                className="bg-[var(--mc-accent-blue)] hover:opacity-90 text-white"
                disabled={isLoading}
              >
                <Save className="h-4 w-4 mr-2" />
                {isLoading
                  ? "Saving..."
                  : isCreating
                  ? "Save & Activate"
                  : "Save Changes"}
              </Button>
            </div>
          </div>
        </DialogContent>
      </Dialog>

      {/* Test Modal (nested) */}
      {showTestModal && (
        <PromptTestModal
          open={showTestModal}
          onOpenChange={setShowTestModal}
          agentId={agentId}
          promptText={promptText}
          promptType={promptType}
        />
      )}
    </>
  );
}
