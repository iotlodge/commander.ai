// Task status enum
export enum TaskStatus {
  QUEUED = "queued",
  IN_PROGRESS = "in_progress",
  TOOL_CALL = "tool_call",
  COMPLETED = "completed",
  FAILED = "failed",
}

// Agent task type
export interface AgentTask {
  id: string;
  user_id: string;
  agent_id: string;
  agent_nickname: string;
  thread_id: string;
  command_text: string;
  status: TaskStatus;
  progress_percentage: number;
  current_node: string | null;
  consultation_target_id: string | null;
  consultation_target_nickname: string | null;
  result: string | null;
  error_message: string | null;
  metadata: Record<string, any>;
  created_at: string;
  started_at: string | null;
  completed_at: string | null;

  // Metrics (basic placeholders - backend instrumentation TODO)
  tool_calls_count?: number;      // Number of tool invocations
  agent_calls_count?: number;     // Number of agent consultations
  total_tokens?: number;          // LLM token usage
}

// WebSocket event types
export interface TaskStatusChangeEvent {
  type: "task_status_changed";
  task_id: string;
  old_status: TaskStatus | null;
  new_status: TaskStatus;
  timestamp: string;
}

export interface TaskProgressEvent {
  type: "task_progress";
  task_id: string;
  progress_percentage: number;
  current_node: string;
  timestamp: string;
}

export interface ConsultationStartedEvent {
  type: "consultation_started";
  task_id: string;
  requesting_agent_id: string;
  target_agent_id: string;
  target_agent_nickname: string;
  timestamp: string;
}

export interface ConsultationCompletedEvent {
  type: "consultation_completed";
  task_id: string;
  timestamp: string;
}

export interface TaskDeletedEvent {
  type: "task_deleted";
  task_id: string;
  timestamp: string;
}

export interface TaskCompletedEvent {
  type: "task_completed";
  task_id: string;
  status: TaskStatus;
  result?: string | null;
  error_message?: string | null;
  timestamp: string;
}

export type WebSocketEvent =
  | TaskStatusChangeEvent
  | TaskProgressEvent
  | TaskCompletedEvent
  | ConsultationStartedEvent
  | ConsultationCompletedEvent
  | TaskDeletedEvent;

// Command submission types
export interface CommandSubmission {
  text: string;
  parsedAgents: string[];
  targetAgent: string;
}

export interface AgentInfo {
  id: string;
  nickname: string;
  specialization: string;
  description: string;
}
