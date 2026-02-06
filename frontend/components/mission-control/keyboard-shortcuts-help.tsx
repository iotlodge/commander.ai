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
        <DialogContent className="bg-[#1e2433] border-[#2a3444] max-w-md">
          <DialogHeader>
            <DialogTitle className="text-white flex items-center gap-2">
              <Keyboard className="h-5 w-5 text-[#4a9eff]" />
              Keyboard Shortcuts
            </DialogTitle>
          </DialogHeader>

          <div className="space-y-3">
            {shortcuts.map((shortcut, i) => (
              <div
                key={i}
                className="flex items-center justify-between py-2 border-b border-[#2a3444] last:border-0"
              >
                <span className="text-sm text-gray-300">{shortcut.description}</span>
                <div className="flex items-center gap-1">
                  {shortcut.keys.map((key, j) => (
                    <kbd
                      key={j}
                      className="px-2 py-1 text-xs font-semibold bg-[#1a1f2e] border border-[#2a3444] rounded text-gray-400"
                    >
                      {key}
                    </kbd>
                  ))}
                </div>
              </div>
            ))}
          </div>

          <div className="mt-4 text-xs text-gray-500 text-center">
            Press <kbd className="px-1.5 py-0.5 bg-[#1a1f2e] border border-[#2a3444] rounded">⌘</kbd> + <kbd className="px-1.5 py-0.5 bg-[#1a1f2e] border border-[#2a3444] rounded">/</kbd> to view this help
          </div>
        </DialogContent>
      </Dialog>
    </>
  );
}
