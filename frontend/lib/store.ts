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
    const { updateTask, removeTask, addTask, tasks } = get();
    console.log("🔄 Handling WebSocket event:", event.type, event);

    switch (event.type) {
      case "task_status_changed":
        console.log("  → Updating task status:", event.task_id, event.new_status);
        // If task doesn't exist and old_status is null (new task), fetch it from API
        if (!tasks.has(event.task_id) && event.old_status === null) {
          console.log("  → New task detected, fetching from API...");
          fetch(`http://localhost:8000/api/tasks/${event.task_id}`)
            .then((res) => res.json())
            .then((task) => {
              console.log("  → Adding new task to store:", task);
              addTask(task);
            })
            .catch((err) => console.error("Failed to fetch new task:", err));
        } else {
          updateTask(event.task_id, { status: event.new_status });
        }
        break;

      case "task_progress":
        console.log("  → Updating task progress:", event.task_id, event.progress_percentage);
        updateTask(event.task_id, {
          progress_percentage: event.progress_percentage,
          current_node: event.current_node,
        });
        break;

      case "consultation_started":
        console.log("  → Starting consultation:", event.task_id);
        updateTask(event.task_id, {
          status: TaskStatus.TOOL_CALL,
          consultation_target_id: event.target_agent_id,
          consultation_target_nickname: event.target_agent_nickname,
        });
        break;

      case "consultation_completed":
        console.log("  → Consultation completed:", event.task_id);
        // Status will be updated by task_status_changed event
        break;

      case "task_deleted":
        console.log("  → Removing task:", event.task_id);
        removeTask(event.task_id);
        break;

      default:
        console.warn("  ⚠️ Unknown event type:", event.type);
    }
  },

  getTasksByStatus: (status) => {
    const tasks = Array.from(get().tasks.values());
    return tasks.filter((task) => task.status === status);
  },
}));
