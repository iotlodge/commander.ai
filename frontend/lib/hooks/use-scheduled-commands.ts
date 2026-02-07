/**
 * React hooks for scheduled command management
 * Provides CRUD operations for agent schedules
 */

import { useState, useCallback } from "react";

const MVP_USER_ID = "00000000-0000-0000-0000-000000000001";
const API_BASE_URL = "http://localhost:8000";

// Get token from localStorage (or use MVP bypass)
const getAuthToken = () => {
  // For MVP, use hardcoded token
  return "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIwMDAwMDAwMC0wMDAwLTAwMDAtMDAwMC0wMDAwMDAwMDAwMDEiLCJ0eXBlIjoiYWNjZXNzIn0.uo-ChnSfZ3vQWTg_6KlxuggkhH2p_zJJa2G4HwLPx6E";
};

export interface ScheduledCommand {
  id: string;
  user_id: string;
  command_text: string;
  agent_id: string;
  agent_nickname: string;
  schedule_type: "cron" | "interval";
  cron_expression: string | null;
  interval_value: number | null;
  interval_unit: "minutes" | "hours" | "days" | null;
  timezone: string;
  enabled: boolean;
  next_run_at: string | null;
  last_run_at: string | null;
  last_run_status: string | null;
  max_retries: number;
  retry_delay_minutes: number;
  timeout_seconds: number;
  description: string | null;
  tags: string[];
  metadata: Record<string, any>;
  created_at: string;
  updated_at: string;
}

export interface ScheduledCommandCreate {
  command_text: string;
  agent_id: string;
  schedule_type: "cron" | "interval";
  cron_expression?: string;
  interval_value?: number;
  interval_unit?: "minutes" | "hours" | "days";
  timezone?: string;
  description?: string;
  enabled?: boolean;
  max_retries?: number;
  retry_delay_minutes?: number;
  timeout_seconds?: number;
  tags?: string[];
  metadata?: Record<string, any>;
}

export interface ScheduledCommandUpdate {
  command_text?: string;
  schedule_type?: "cron" | "interval";
  cron_expression?: string;
  interval_value?: number;
  interval_unit?: "minutes" | "hours" | "days";
  timezone?: string;
  description?: string;
  enabled?: boolean;
  max_retries?: number;
  retry_delay_minutes?: number;
  timeout_seconds?: number;
  tags?: string[];
  metadata?: Record<string, any>;
}

export interface ScheduleFilters {
  agent_id?: string;
  enabled?: boolean;
  limit?: number;
  offset?: number;
}

export interface ScheduledCommandExecution {
  id: string;
  scheduled_command_id: string;
  task_id: string | null;
  triggered_at: string;
  started_at: string | null;
  completed_at: string | null;
  status: "pending" | "running" | "success" | "failed" | "timeout";
  result_summary: string | null;
  error_message: string | null;
  retry_count: number;
  execution_duration_ms: number | null;
  tokens_used: number | null;
  llm_calls: number | null;
  metadata: Record<string, any>;
}

export interface SchedulerStatus {
  running: boolean;
  initialized: boolean;
  jobs_count: number;
  jobs: Array<{
    id: string;
    name: string;
    next_run: string | null;
    trigger: string;
  }>;
}

export function useScheduledCommands(initialAgentId?: string) {
  const [schedules, setSchedules] = useState<ScheduledCommand[]>([]);
  const [executions, setExecutions] = useState<ScheduledCommandExecution[]>([]);
  const [schedulerStatus, setSchedulerStatus] = useState<SchedulerStatus | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchSchedules = useCallback(async (filters?: ScheduleFilters) => {
    setIsLoading(true);
    setError(null);

    try {
      // Build query string
      const params = new URLSearchParams();
      params.append("user_id", MVP_USER_ID);
      if (filters?.agent_id) params.append("agent_id", filters.agent_id);
      if (filters?.enabled !== undefined) params.append("enabled", String(filters.enabled));
      if (filters?.limit) params.append("limit", String(filters.limit));
      if (filters?.offset) params.append("offset", String(filters.offset));

      const response = await fetch(
        `${API_BASE_URL}/api/scheduled-commands?${params.toString()}`,
        {
          headers: {
            Authorization: `Bearer ${getAuthToken()}`,
          },
        }
      );

      if (!response.ok) {
        throw new Error(`Failed to fetch schedules: ${response.statusText}`);
      }

      const data = await response.json();
      setSchedules(data.schedules || []);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : "Failed to fetch schedules";
      setError(errorMessage);
      console.error("Error fetching schedules:", err);
    } finally {
      setIsLoading(false);
    }
  }, []);

  const createSchedule = useCallback(async (data: ScheduledCommandCreate): Promise<ScheduledCommand | null> => {
    setIsLoading(true);
    setError(null);

    try {
      const response = await fetch(`${API_BASE_URL}/api/scheduled-commands?user_id=${MVP_USER_ID}`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${getAuthToken()}`,
        },
        body: JSON.stringify({
          ...data,
          user_id: MVP_USER_ID,
        }),
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || `Failed to create schedule: ${response.statusText}`);
      }

      const newSchedule = await response.json();

      // Add to local state
      setSchedules((prev) => [...prev, newSchedule]);

      return newSchedule;
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : "Failed to create schedule";
      setError(errorMessage);
      console.error("Error creating schedule:", err);
      return null;
    } finally {
      setIsLoading(false);
    }
  }, []);

  const updateSchedule = useCallback(
    async (id: string, data: ScheduledCommandUpdate): Promise<ScheduledCommand | null> => {
      setIsLoading(true);
      setError(null);

      try {
        const response = await fetch(`${API_BASE_URL}/api/scheduled-commands/${id}?user_id=${MVP_USER_ID}`, {
          method: "PUT",
          headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${getAuthToken()}`,
          },
          body: JSON.stringify(data),
        });

        if (!response.ok) {
          const errorData = await response.json().catch(() => ({}));
          throw new Error(errorData.detail || `Failed to update schedule: ${response.statusText}`);
        }

        const updatedSchedule = await response.json();

        // Update local state
        setSchedules((prev) =>
          prev.map((s) => (s.id === id ? updatedSchedule : s))
        );

        return updatedSchedule;
      } catch (err) {
        const errorMessage = err instanceof Error ? err.message : "Failed to update schedule";
        setError(errorMessage);
        console.error("Error updating schedule:", err);
        return null;
      } finally {
        setIsLoading(false);
      }
    },
    []
  );

  const deleteSchedule = useCallback(async (id: string): Promise<boolean> => {
    setIsLoading(true);
    setError(null);

    try {
      const response = await fetch(`${API_BASE_URL}/api/scheduled-commands/${id}?user_id=${MVP_USER_ID}`, {
        method: "DELETE",
        headers: {
          Authorization: `Bearer ${getAuthToken()}`,
        },
      });

      if (!response.ok) {
        throw new Error(`Failed to delete schedule: ${response.statusText}`);
      }

      // Remove from local state
      setSchedules((prev) => prev.filter((s) => s.id !== id));

      return true;
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : "Failed to delete schedule";
      setError(errorMessage);
      console.error("Error deleting schedule:", err);
      return false;
    } finally {
      setIsLoading(false);
    }
  }, []);

  const enableSchedule = useCallback(async (id: string): Promise<boolean> => {
    setIsLoading(true);
    setError(null);

    try {
      const response = await fetch(`${API_BASE_URL}/api/scheduled-commands/${id}/enable?user_id=${MVP_USER_ID}`, {
        method: "POST",
        headers: {
          Authorization: `Bearer ${getAuthToken()}`,
        },
      });

      if (!response.ok) {
        throw new Error(`Failed to enable schedule: ${response.statusText}`);
      }

      const updatedSchedule = await response.json();

      // Update local state
      setSchedules((prev) =>
        prev.map((s) => (s.id === id ? updatedSchedule : s))
      );

      return true;
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : "Failed to enable schedule";
      setError(errorMessage);
      console.error("Error enabling schedule:", err);
      return false;
    } finally {
      setIsLoading(false);
    }
  }, []);

  const disableSchedule = useCallback(async (id: string): Promise<boolean> => {
    setIsLoading(true);
    setError(null);

    try {
      const response = await fetch(`${API_BASE_URL}/api/scheduled-commands/${id}/disable?user_id=${MVP_USER_ID}`, {
        method: "POST",
        headers: {
          Authorization: `Bearer ${getAuthToken()}`,
        },
      });

      if (!response.ok) {
        throw new Error(`Failed to disable schedule: ${response.statusText}`);
      }

      const updatedSchedule = await response.json();

      // Update local state
      setSchedules((prev) =>
        prev.map((s) => (s.id === id ? updatedSchedule : s))
      );

      return true;
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : "Failed to disable schedule";
      setError(errorMessage);
      console.error("Error disabling schedule:", err);
      return false;
    } finally {
      setIsLoading(false);
    }
  }, []);

  const executeScheduleNow = useCallback(async (id: string): Promise<boolean> => {
    // Don't set isLoading here - it causes the list to hide cards
    setError(null);

    try {
      const response = await fetch(`${API_BASE_URL}/api/scheduled-commands/${id}/execute?user_id=${MVP_USER_ID}`, {
        method: "POST",
        headers: {
          Authorization: `Bearer ${getAuthToken()}`,
        },
      });

      if (!response.ok) {
        throw new Error(`Failed to execute schedule: ${response.statusText}`);
      }

      return true;
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : "Failed to execute schedule";
      setError(errorMessage);
      console.error("Error executing schedule:", err);
      return false;
    }
  }, []);

  const fetchExecutions = useCallback(async (scheduleId: string, limit?: number) => {
    setIsLoading(true);
    setError(null);

    try {
      const params = new URLSearchParams();
      params.append("user_id", MVP_USER_ID);
      if (limit) params.append("limit", String(limit));

      const response = await fetch(
        `${API_BASE_URL}/api/scheduled-commands/${scheduleId}/executions?${params.toString()}`,
        {
          headers: {
            Authorization: `Bearer ${getAuthToken()}`,
          },
        }
      );

      if (!response.ok) {
        throw new Error(`Failed to fetch executions: ${response.statusText}`);
      }

      const data = await response.json();
      setExecutions(data.executions || []);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : "Failed to fetch executions";
      setError(errorMessage);
      console.error("Error fetching executions:", err);
    } finally {
      setIsLoading(false);
    }
  }, []);

  const fetchSchedulerStatus = useCallback(async () => {
    setIsLoading(true);
    setError(null);

    try {
      const response = await fetch(
        `${API_BASE_URL}/api/scheduled-commands/scheduler/status?user_id=${MVP_USER_ID}`,
        {
          headers: {
            Authorization: `Bearer ${getAuthToken()}`,
          },
        }
      );

      if (!response.ok) {
        throw new Error(`Failed to fetch scheduler status: ${response.statusText}`);
      }

      const data = await response.json();
      setSchedulerStatus(data);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : "Failed to fetch scheduler status";
      setError(errorMessage);
      console.error("Error fetching scheduler status:", err);
    } finally {
      setIsLoading(false);
    }
  }, []);

  return {
    schedules,
    executions,
    schedulerStatus,
    isLoading,
    error,
    fetchSchedules,
    createSchedule,
    updateSchedule,
    deleteSchedule,
    enableSchedule,
    disableSchedule,
    executeScheduleNow,
    fetchExecutions,
    fetchSchedulerStatus,
  };
}
