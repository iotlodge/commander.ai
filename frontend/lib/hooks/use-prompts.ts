/**
 * React hooks for prompt management
 * Provides CRUD operations, search, filtering, and testing
 */

import { useState, useCallback } from "react";

const MVP_USER_ID = "00000000-0000-0000-0000-000000000001";
const API_BASE_URL = "http://localhost:8000";

// Get token from localStorage (or use MVP bypass)
const getAuthToken = () => {
  // For MVP, use hardcoded token
  return "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIwMDAwMDAwMC0wMDAwLTAwMDAtMDAwMC0wMDAwMDAwMDAwMDEiLCJ0eXBlIjoiYWNjZXNzIn0.uo-ChnSfZ3vQWTg_6KlxuggkhH2p_zJJa2G4HwLPx6E";
};

export interface AgentPrompt {
  id: string;
  agent_id: string;
  nickname: string;
  description: string;
  prompt_text: string;
  active: boolean;
  prompt_type: "system" | "human" | "ai";
  variables: Record<string, string>;
  created_at: string;
  updated_at: string;
}

export interface PromptFilters {
  agent_id?: string;
  prompt_type?: string;
  active?: boolean;
  search?: string;
  limit?: number;
  offset?: number;
}

export interface PromptCreate {
  agent_id: string;
  nickname: string;
  description: string;
  prompt_text: string;
  active?: boolean;
  prompt_type?: "system" | "human" | "ai";
  variables?: Record<string, string>;
}

export interface PromptUpdate {
  prompt_text?: string;
  active?: boolean;
  variables?: Record<string, string>;
}

export interface PromptTestRequest {
  agent_id: string;
  prompt_text: string;
  prompt_type?: string;
  test_query: string;
  test_context?: Record<string, any>;
}

export interface PromptTestResponse {
  generated_response: string;
  metrics: {
    prompt_tokens: number;
    completion_tokens: number;
    total_tokens: number;
    response_time_ms: number;
  };
  compiled_messages: Array<{
    role: string;
    content: string;
  }>;
}

export function usePrompts(initialAgentId?: string) {
  const [prompts, setPrompts] = useState<AgentPrompt[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchPrompts = useCallback(async (filters?: PromptFilters) => {
    setIsLoading(true);
    setError(null);

    try {
      // Build query string
      const params = new URLSearchParams();
      params.append("user_id", MVP_USER_ID); // MVP development bypass
      if (filters?.agent_id) params.append("agent_id", filters.agent_id);
      if (filters?.prompt_type) params.append("prompt_type", filters.prompt_type);
      if (filters?.active !== undefined) params.append("active", String(filters.active));
      if (filters?.search) params.append("search", filters.search);
      if (filters?.limit) params.append("limit", String(filters.limit));
      if (filters?.offset) params.append("offset", String(filters.offset));

      const response = await fetch(
        `${API_BASE_URL}/api/prompts?${params.toString()}`,
        {
          headers: {
            Authorization: `Bearer ${getAuthToken()}`,
          },
        }
      );

      if (!response.ok) {
        throw new Error(`Failed to fetch prompts: ${response.statusText}`);
      }

      const data = await response.json();
      setPrompts(data.prompts || []);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : "Failed to fetch prompts";
      setError(errorMessage);
      console.error("Error fetching prompts:", err);
    } finally {
      setIsLoading(false);
    }
  }, []);

  const createPrompt = useCallback(async (data: PromptCreate): Promise<AgentPrompt | null> => {
    setIsLoading(true);
    setError(null);

    try {
      const response = await fetch(`${API_BASE_URL}/api/prompts?user_id=${MVP_USER_ID}`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${getAuthToken()}`,
        },
        body: JSON.stringify(data),
      });

      if (!response.ok) {
        throw new Error(`Failed to create prompt: ${response.statusText}`);
      }

      const newPrompt = await response.json();

      // Add to local state
      setPrompts((prev) => [...prev, newPrompt]);

      return newPrompt;
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : "Failed to create prompt";
      setError(errorMessage);
      console.error("Error creating prompt:", err);
      return null;
    } finally {
      setIsLoading(false);
    }
  }, []);

  const updatePrompt = useCallback(
    async (id: string, data: PromptUpdate): Promise<AgentPrompt | null> => {
      setIsLoading(true);
      setError(null);

      try {
        const response = await fetch(`${API_BASE_URL}/api/prompts/${id}?user_id=${MVP_USER_ID}`, {
          method: "PATCH",
          headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${getAuthToken()}`,
          },
          body: JSON.stringify(data),
        });

        if (!response.ok) {
          throw new Error(`Failed to update prompt: ${response.statusText}`);
        }

        const updatedPrompt = await response.json();

        // Update local state
        setPrompts((prev) =>
          prev.map((p) => (p.id === id ? updatedPrompt : p))
        );

        return updatedPrompt;
      } catch (err) {
        const errorMessage = err instanceof Error ? err.message : "Failed to update prompt";
        setError(errorMessage);
        console.error("Error updating prompt:", err);
        return null;
      } finally {
        setIsLoading(false);
      }
    },
    []
  );

  const deletePrompt = useCallback(async (id: string): Promise<boolean> => {
    setIsLoading(true);
    setError(null);

    try {
      const response = await fetch(`${API_BASE_URL}/api/prompts/${id}?user_id=${MVP_USER_ID}`, {
        method: "DELETE",
        headers: {
          Authorization: `Bearer ${getAuthToken()}`,
        },
      });

      if (!response.ok) {
        throw new Error(`Failed to delete prompt: ${response.statusText}`);
      }

      // Remove from local state
      setPrompts((prev) => prev.filter((p) => p.id !== id));

      return true;
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : "Failed to delete prompt";
      setError(errorMessage);
      console.error("Error deleting prompt:", err);
      return false;
    } finally {
      setIsLoading(false);
    }
  }, []);

  const testPrompt = useCallback(
    async (request: PromptTestRequest): Promise<PromptTestResponse | null> => {
      setIsLoading(true);
      setError(null);

      try {
        const response = await fetch(`${API_BASE_URL}/api/prompts/test?user_id=${MVP_USER_ID}`, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${getAuthToken()}`,
          },
          body: JSON.stringify(request),
        });

        if (!response.ok) {
          throw new Error(`Failed to test prompt: ${response.statusText}`);
        }

        const result = await response.json();
        return result;
      } catch (err) {
        const errorMessage = err instanceof Error ? err.message : "Failed to test prompt";
        setError(errorMessage);
        console.error("Error testing prompt:", err);
        return null;
      } finally {
        setIsLoading(false);
      }
    },
    []
  );

  const clonePrompt = useCallback(
    async (
      id: string,
      description: string,
      modifications?: Partial<PromptCreate>
    ): Promise<AgentPrompt | null> => {
      setIsLoading(true);
      setError(null);

      try {
        const response = await fetch(`${API_BASE_URL}/api/prompts/${id}/clone?user_id=${MVP_USER_ID}`, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${getAuthToken()}`,
          },
          body: JSON.stringify({
            description,
            modifications: modifications || {},
          }),
        });

        if (!response.ok) {
          throw new Error(`Failed to clone prompt: ${response.statusText}`);
        }

        const clonedPrompt = await response.json();

        // Add to local state
        setPrompts((prev) => [...prev, clonedPrompt]);

        return clonedPrompt;
      } catch (err) {
        const errorMessage = err instanceof Error ? err.message : "Failed to clone prompt";
        setError(errorMessage);
        console.error("Error cloning prompt:", err);
        return null;
      } finally {
        setIsLoading(false);
      }
    },
    []
  );

  return {
    prompts,
    isLoading,
    error,
    fetchPrompts,
    createPrompt,
    updatePrompt,
    deletePrompt,
    testPrompt,
    clonePrompt,
  };
}
