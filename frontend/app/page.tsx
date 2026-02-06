"use client";

import { useState, useEffect } from "react";
import { MissionControlLayout } from "@/components/mission-control";
import { KanbanBoard } from "@/components/kanban/kanban-board";
import { CommandInputContainer } from "@/components/command/command-input-container";
import { Button } from "@/components/ui/button";
import { LayoutGrid, MessageSquare } from "lucide-react";

type ViewMode = "mission-control" | "kanban";

export default function Home() {
  const [viewMode, setViewMode] = useState<ViewMode>("mission-control");

  // Load saved view preference
  useEffect(() => {
    const saved = localStorage.getItem("commander-view-mode");
    if (saved === "kanban" || saved === "mission-control") {
      setViewMode(saved);
    }
  }, []);

  // Save view preference
  const handleViewChange = (mode: ViewMode) => {
    setViewMode(mode);
    localStorage.setItem("commander-view-mode", mode);
  };

  // Mission Control View (default)
  if (viewMode === "mission-control") {
    return (
      <>
        <MissionControlLayout />

        {/* View Switcher - Floating button */}
        <div className="fixed bottom-4 right-4 z-50">
          <Button
            onClick={() => handleViewChange("kanban")}
            variant="outline"
            size="sm"
            className="bg-[#1e2433]/90 backdrop-blur-sm border-[#2a3444] text-gray-400 hover:text-white hover:bg-[#2a3444] shadow-lg"
          >
            <LayoutGrid className="h-4 w-4 mr-2" />
            Switch to Classic View
          </Button>
        </div>
      </>
    );
  }

  // Classic Kanban View
  return (
    <>
      <main className="h-screen bg-[#1a1f2e] flex flex-col overflow-hidden">
        {/* Kanban Board */}
        <div className="flex-1 overflow-y-auto">
          <KanbanBoard />
        </div>

        {/* Command Input */}
        <div className="flex-shrink-0 bg-[#1e2433] border-t border-[#2a3444]">
          <CommandInputContainer />
        </div>
      </main>

      {/* View Switcher - Floating button */}
      <div className="fixed bottom-4 right-4 z-50">
        <Button
          onClick={() => handleViewChange("mission-control")}
          variant="outline"
          size="sm"
          className="bg-[#1e2433]/90 backdrop-blur-sm border-[#2a3444] text-gray-400 hover:text-white hover:bg-[#2a3444] shadow-lg"
        >
          <MessageSquare className="h-4 w-4 mr-2" />
          Switch to Mission Control
        </Button>
      </div>
    </>
  );
}
