/**
 * React hook for managing agent model configurations
 * Provides CRUD operations for agent LLM models
 */

import { useState, useCallback } from 'react';
import type { AgentModelConfig, AgentModelUpdate, ApprovedModel } from '@/lib/types';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
const MVP_USER_ID = '00000000-0000-0000-0000-000000000001';

interface UseAgentModelsReturn {
  // State
  loading: boolean;
  error: string | null;

  // Actions
  fetchModelConfig: (agentId: string) => Promise<AgentModelConfig | null>;
  updateModelConfig: (agentId: string, update: AgentModelUpdate) => Promise<AgentModelConfig | null>;
  fetchApprovedModels: (provider?: string) => Promise<ApprovedModel[]>;
}

export function useAgentModels(): UseAgentModelsReturn {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchModelConfig = useCallback(async (agentId: string): Promise<AgentModelConfig | null> => {
    setLoading(true);
    setError(null);

    try {
      const response = await fetch(
        `${API_BASE_URL}/api/agents/${agentId}/model?user_id=${MVP_USER_ID}`,
        {
          method: 'GET',
          headers: {
            'Content-Type': 'application/json',
          },
        }
      );

      if (!response.ok) {
        if (response.status === 404) {
          throw new Error(`Model configuration not found for agent ${agentId}`);
        }
        throw new Error(`Failed to fetch model config: ${response.statusText}`);
      }

      const data: AgentModelConfig = await response.json();
      return data;
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Unknown error';
      setError(message);
      console.error('Error fetching model config:', err);
      return null;
    } finally {
      setLoading(false);
    }
  }, []);

  const updateModelConfig = useCallback(async (
    agentId: string,
    update: AgentModelUpdate
  ): Promise<AgentModelConfig | null> => {
    setLoading(true);
    setError(null);

    try {
      const response = await fetch(
        `${API_BASE_URL}/api/agents/${agentId}/model?user_id=${MVP_USER_ID}`,
        {
          method: 'PATCH',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify(update),
        }
      );

      if (!response.ok) {
        const errorData = await response.json().catch(() => null);
        const errorMessage = errorData?.detail || response.statusText;

        if (response.status === 409) {
          throw new Error(`Agent is busy: ${errorMessage}`);
        } else if (response.status === 400) {
          throw new Error(`Invalid model: ${errorMessage}`);
        } else if (response.status === 500) {
          throw new Error(`Reload failed: ${errorMessage}`);
        }
        throw new Error(`Failed to update model: ${errorMessage}`);
      }

      const data: AgentModelConfig = await response.json();
      return data;
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Unknown error';
      setError(message);
      console.error('Error updating model config:', err);
      return null;
    } finally {
      setLoading(false);
    }
  }, []);

  const fetchApprovedModels = useCallback(async (provider?: string): Promise<ApprovedModel[]> => {
    setLoading(true);
    setError(null);

    try {
      const url = new URL(`${API_BASE_URL}/api/agents/models/approved`);
      url.searchParams.append('user_id', MVP_USER_ID);
      if (provider) {
        url.searchParams.append('provider', provider);
      }

      const response = await fetch(url.toString(), {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        throw new Error(`Failed to fetch approved models: ${response.statusText}`);
      }

      const data = await response.json();
      return data.models || [];
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Unknown error';
      setError(message);
      console.error('Error fetching approved models:', err);
      return [];
    } finally {
      setLoading(false);
    }
  }, []);

  return {
    loading,
    error,
    fetchModelConfig,
    updateModelConfig,
    fetchApprovedModels,
  };
}
