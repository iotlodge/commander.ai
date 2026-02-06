import { useEffect } from "react";

export interface KeyboardShortcut {
  key: string;
  ctrlKey?: boolean;
  metaKey?: boolean;
  shiftKey?: boolean;
  altKey?: boolean;
  action: () => void;
  description: string;
}

export function useKeyboardShortcuts(shortcuts: KeyboardShortcut[], enabled = true) {
  useEffect(() => {
    if (!enabled) return;

    const handleKeyDown = (event: KeyboardEvent) => {
      for (const shortcut of shortcuts) {
        const ctrlOrMeta = (shortcut.ctrlKey && event.ctrlKey) || (shortcut.metaKey && event.metaKey);
        const shift = shortcut.shiftKey ? event.shiftKey : !event.shiftKey;
        const alt = shortcut.altKey ? event.altKey : !event.altKey;

        // Check if just the key matches (for simple shortcuts like Escape)
        const simpleKeyMatch =
          !shortcut.ctrlKey && !shortcut.metaKey && !shortcut.shiftKey && !shortcut.altKey &&
          event.key.toLowerCase() === shortcut.key.toLowerCase() &&
          !event.ctrlKey && !event.metaKey && !event.shiftKey && !event.altKey;

        // Check if modified key matches
        const modifiedKeyMatch =
          (shortcut.ctrlKey || shortcut.metaKey) &&
          event.key.toLowerCase() === shortcut.key.toLowerCase() &&
          ctrlOrMeta && shift && alt;

        if (simpleKeyMatch || modifiedKeyMatch) {
          event.preventDefault();
          shortcut.action();
          break;
        }
      }
    };

    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [shortcuts, enabled]);
}

export const SHORTCUTS = {
  FOCUS_INPUT: { key: "k", metaKey: true, description: "Focus command input" },
  CLEAR_FILTER: { key: "Escape", description: "Clear agent filter" },
  TOGGLE_VIEW: { key: "v", metaKey: true, description: "Toggle view mode" },
  SCROLL_TO_BOTTOM: { key: "g", metaKey: true, shiftKey: true, description: "Scroll to bottom" },
};
