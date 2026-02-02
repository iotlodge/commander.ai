"use client";

import { useState, useEffect } from "react";
import {
  Command,
  CommandEmpty,
  CommandGroup,
  CommandInput,
  CommandItem,
  CommandList,
} from "@/components/ui/command";
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/components/ui/popover";
import { AgentInfo } from "@/lib/types";

interface AgentMentionAutocompleteProps {
  children: React.ReactNode;
  agents: AgentInfo[];
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onAgentSelect: (nickname: string) => void;
  searchQuery?: string;
}

export function AgentMentionAutocomplete({
  children,
  agents,
  open,
  onOpenChange,
  onAgentSelect,
  searchQuery = "",
}: AgentMentionAutocompleteProps) {
  const [filteredAgents, setFilteredAgents] = useState<AgentInfo[]>(agents);

  useEffect(() => {
    if (!searchQuery) {
      setFilteredAgents(agents);
      return;
    }

    const query = searchQuery.toLowerCase();
    const filtered = agents.filter(
      (agent) =>
        agent.nickname.toLowerCase().includes(query) ||
        agent.specialization.toLowerCase().includes(query) ||
        agent.description.toLowerCase().includes(query)
    );
    setFilteredAgents(filtered);
  }, [searchQuery, agents]);

  return (
    <Popover open={open} onOpenChange={onOpenChange}>
      <PopoverTrigger asChild>{children}</PopoverTrigger>
      <PopoverContent className="w-[400px] p-0 bg-[#2a3444] border-[#3a4454]" align="start">
        <Command className="bg-[#2a3444]" shouldFilter={false}>
          <CommandInput
            placeholder="Search agents..."
            value={searchQuery}
            className="bg-[#2a3444] text-white border-[#3a4454]"
            readOnly
          />
          <CommandList className="bg-[#2a3444]">
            <CommandEmpty className="text-gray-400">No agents found.</CommandEmpty>
            <CommandGroup heading="Available Agents" className="text-gray-400">
              {filteredAgents.map((agent) => (
                <CommandItem
                  key={agent.id}
                  value={agent.nickname}
                  onSelect={() => {
                    onAgentSelect(agent.nickname);
                    onOpenChange(false);
                  }}
                  onMouseDown={(e) => {
                    e.preventDefault(); // Prevent focus loss from textarea
                  }}
                  onClick={() => {
                    onAgentSelect(agent.nickname);
                    onOpenChange(false);
                  }}
                  className="cursor-pointer hover:bg-[#3a4454] aria-selected:bg-white/95 aria-selected:text-gray-900"
                >
                  <div className="flex items-center gap-3 w-full">
                    <div className="flex h-8 w-8 items-center justify-center rounded-full bg-[#4a9eff]/20 text-[#4a9eff] font-semibold aria-selected:bg-[#4a9eff] aria-selected:text-white">
                      {agent.nickname.charAt(0).toUpperCase()}
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2">
                        <span className="font-medium text-sm text-white aria-selected:text-gray-900">
                          @{agent.nickname}
                        </span>
                        <span className="text-xs text-gray-400 aria-selected:text-gray-700">
                          {agent.specialization}
                        </span>
                      </div>
                      <p className="text-xs text-gray-500 truncate aria-selected:text-gray-600">
                        {agent.description}
                      </p>
                    </div>
                  </div>
                </CommandItem>
              ))}
            </CommandGroup>
          </CommandList>
        </Command>
      </PopoverContent>
    </Popover>
  );
}
