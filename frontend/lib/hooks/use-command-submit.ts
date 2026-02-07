"use client";

import { useState } from "react";
import { AgentInfo } from "@/lib/types";

// MVP hardcoded user ID (same as in task store)
const MVP_USER_ID = "00000000-0000-0000-0000-000000000001";

interface TaskCreateRequest {
  user_id: string;
  agent_id: string;
  thread_id: string;
  command_text: string;
}

interface UseCommandSubmitProps {
  agents: AgentInfo[];
}

export function useCommandSubmit({ agents }: UseCommandSubmitProps) {
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const parseCommand = (text: string): { targetAgentId: string } => {
    // Extract @mentions
    const mentionRegex = /@(\w+)/g;
    const mentions: string[] = [];
    let match;

    while ((match = mentionRegex.exec(text)) !== null) {
      mentions.push(match[1]);
    }

    // Map nicknames to agent IDs
    const mentionedAgentIds: string[] = [];
    mentions.forEach((nickname) => {
      const agent = agents.find(
        (a) => a.nickname.toLowerCase() === nickname.toLowerCase()
      );
      if (agent) {
        mentionedAgentIds.push(agent.id);
      }
    });

    // Check for greeting patterns
    const greetingRegex =
      /^(hello|hi|hey|greetings)\s+(\w+)/i;
    const greetingMatch = text.match(greetingRegex);

    if (greetingMatch) {
      const nickname = greetingMatch[2];
      const agent = agents.find(
        (a) => a.nickname.toLowerCase() === nickname.toLowerCase()
      );
      if (agent && !mentionedAgentIds.includes(agent.id)) {
        mentionedAgentIds.push(agent.id);
      }
    }

    // Determine target agent
    // Priority 1: Single mention -> direct to that agent
    // Priority 2: Multiple mentions or no mention -> parent agent
    let targetAgentId: string;

    if (mentionedAgentIds.length === 1) {
      targetAgentId = mentionedAgentIds[0];
    } else {
      targetAgentId = "agent_parent"; // Leo orchestrator handles complex/ambiguous tasks
    }

    return { targetAgentId };
  };

  const submitCommand = async (commandText: string): Promise<void> => {
    if (!commandText.trim()) {
      setError("Command cannot be empty");
      return;
    }

    setIsLoading(true);
    setError(null);

    try {
      // Submit to commands endpoint (which handles parsing + execution)
      const commandRequest = {
        user_id: MVP_USER_ID,
        text: commandText,
      };

      // Add user_id as query parameter for MVP user development bypass
      const response = await fetch(`http://localhost:8000/api/commands?user_id=${MVP_USER_ID}`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(commandRequest),
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(
          errorData.detail || `Failed to create task: ${response.status}`
        );
      }

      // Success! The task will appear in Mission Control via WebSocket
    } catch (err) {
      const errorMessage =
        err instanceof Error ? err.message : "Failed to submit command";
      setError(errorMessage);
      throw err;
    } finally {
      setIsLoading(false);
    }
  };

  return {
    submitCommand,
    isLoading,
    error,
  };
}
