import { create } from "zustand";
import { AgentTask, TaskStatus, WebSocketEvent } from "./types";

interface TaskStore {
  tasks: Map<string, AgentTask>;
  addTask: (task: AgentTask) => void;
  updateTask: (taskId: string, updates: Partial<AgentTask>) => void;
  removeTask: (taskId: string) => void;
  handleWebSocketEvent: (event: WebSocketEvent) => void;
  getTasksByStatus: (status: TaskStatus) => AgentTask[];
}

export const useTaskStore = create<TaskStore>((set, get) => ({
  tasks: new Map(),

  addTask: (task) =>
    set((state) => {
      const newTasks = new Map(state.tasks);
      newTasks.set(task.id, task);
      return { tasks: newTasks };
    }),

  updateTask: (taskId, updates) =>
    set((state) => {
      const newTasks = new Map(state.tasks);
      const task = newTasks.get(taskId);
      if (task) {
        newTasks.set(taskId, { ...task, ...updates });
      }
      return { tasks: newTasks };
    }),

  removeTask: (taskId) =>
    set((state) => {
      const newTasks = new Map(state.tasks);
      newTasks.delete(taskId);
      return { tasks: newTasks };
    }),

  handleWebSocketEvent: (event) => {
    const { updateTask, removeTask } = get();

    switch (event.type) {
      case "task_status_changed":
        updateTask(event.task_id, { status: event.new_status });
        break;

      case "task_progress":
        updateTask(event.task_id, {
          progress_percentage: event.progress_percentage,
          current_node: event.current_node,
        });
        break;

      case "consultation_started":
        updateTask(event.task_id, {
          status: TaskStatus.TOOL_CALL,
          consultation_target_id: event.target_agent_id,
          consultation_target_nickname: event.target_agent_nickname,
        });
        break;

      case "consultation_completed":
        // Status will be updated by task_status_changed event
        break;

      case "task_deleted":
        removeTask(event.task_id);
        break;
    }
  },

  getTasksByStatus: (status) => {
    const tasks = Array.from(get().tasks.values());
    return tasks.filter((task) => task.status === status);
  },
}));
