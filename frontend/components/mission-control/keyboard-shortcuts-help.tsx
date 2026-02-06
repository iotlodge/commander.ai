"use client";

import { useState, useEffect } from "react";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Keyboard } from "lucide-react";

interface Shortcut {
  keys: string[];
  description: string;
}

const shortcuts: Shortcut[] = [
  { keys: ["⌘", "K"], description: "Focus command input" },
  { keys: ["Esc"], description: "Clear agent filter" },
  { keys: ["⌘", "V"], description: "Toggle view mode" },
  { keys: ["⌘", "⇧", "G"], description: "Scroll to bottom" },
  { keys: ["↵"], description: "Send command" },
  { keys: ["⇧", "↵"], description: "New line in command" },
];

export function KeyboardShortcutsHelp() {
  const [isOpen, setIsOpen] = useState(false);

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key === "/") {
        e.preventDefault();
        setIsOpen(true);
      }
    };

    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, []);

  return (
    <>
      {/* Trigger Button */}
      <button
        onClick={() => setIsOpen(true)}
        className="text-xs text-gray-500 hover:text-gray-300 flex items-center gap-1 transition-colors"
        title="Keyboard shortcuts (⌘/)"
      >
        <Keyboard className="h-3 w-3" />
        <span>⌘/</span>
      </button>

      {/* Shortcuts Modal */}
      <Dialog open={isOpen} onOpenChange={setIsOpen}>
        <DialogContent className="bg-[var(--mc-bg-secondary)] border-[var(--mc-border)] max-w-md">
          <DialogHeader>
            <DialogTitle className="text-[var(--mc-text-primary)] flex items-center gap-2">
              <Keyboard className="h-5 w-5 text-[var(--mc-accent-blue)]" />
              Keyboard Shortcuts
            </DialogTitle>
          </DialogHeader>

          <div className="space-y-3">
            {shortcuts.map((shortcut, i) => (
              <div
                key={i}
                className="flex items-center justify-between py-2 border-b border-[var(--mc-border)] last:border-0"
              >
                <span className="text-sm text-[var(--mc-text-primary)]">{shortcut.description}</span>
                <div className="flex items-center gap-1">
                  {shortcut.keys.map((key, j) => (
                    <kbd
                      key={j}
                      className="px-2 py-1 text-xs font-semibold bg-[var(--mc-bg-primary)] border border-[var(--mc-border)] rounded text-[var(--mc-text-secondary)]"
                    >
                      {key}
                    </kbd>
                  ))}
                </div>
              </div>
            ))}
          </div>

          <div className="mt-4 text-xs text-gray-500 text-center">
            Press <kbd className="px-1.5 py-0.5 bg-[var(--mc-bg-primary)] border border-[var(--mc-border)] rounded">⌘</kbd> + <kbd className="px-1.5 py-0.5 bg-[var(--mc-bg-primary)] border border-[var(--mc-border)] rounded">/</kbd> to view this help
          </div>
        </DialogContent>
      </Dialog>
    </>
  );
}
