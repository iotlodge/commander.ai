import { KanbanBoard } from "@/components/kanban/kanban-board";
import { CommandInputContainer } from "@/components/command/command-input-container";

export default function Home() {
  return (
    <main className="h-screen bg-[#1a1f2e] flex flex-col overflow-hidden">
      {/* Kanban Board - fills available space above input */}
      <div className="flex-1 overflow-y-auto">
        <KanbanBoard />
      </div>

      {/* Command Input - fixed at bottom */}
      <div className="flex-shrink-0 bg-[#1e2433] border-t border-[#2a3444]">
        <CommandInputContainer />
      </div>
    </main>
  );
}
