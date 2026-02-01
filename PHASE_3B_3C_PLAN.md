# Phase 3B-C Implementation Plan: Frontend Task Management UI

## Overview

Build a Next.js 14 frontend with a Kanban-style task board that displays agent tasks in real-time via WebSocket connection to the backend.

**Scope**: Frontend only
- Next.js 14 with App Router and TypeScript
- Tailwind CSS + shadcn/ui components
- WebSocket client for real-time updates
- Kanban board UI with task cards
- Basic drag-and-drop (optional for MVP)

**Estimated Time**: 2-3 days

---

## Current State

**Completed** (Phase 3A):
- ✅ Backend task management API
- ✅ WebSocket server at `/ws/{user_id}`
- ✅ Task models and events
- ✅ Progress tracking in agents

**Missing** (Phase 3B-C):
- Frontend application structure
- Kanban board UI components
- WebSocket client connection
- Real-time task updates

---

## Implementation Steps

### Step 1: Initialize Next.js 14 Frontend

**Create Next.js app with TypeScript**

```bash
# From project root
npx create-next-app@latest frontend --typescript --tailwind --app --no-src-dir --import-alias "@/*"
```

**Configuration options:**
- ✅ TypeScript
- ✅ ESLint
- ✅ Tailwind CSS
- ✅ App Router
- ✅ No src directory
- ✅ Import alias `@/*`

**Project structure:**
```
frontend/
├── app/
│   ├── layout.tsx        # Root layout
│   ├── page.tsx          # Home page (Kanban board)
│   └── globals.css       # Global styles
├── components/
│   ├── ui/               # shadcn/ui components
│   ├── kanban/
│   │   ├── kanban-board.tsx
│   │   ├── kanban-column.tsx
│   │   └── task-card.tsx
│   └── providers/
│       └── websocket-provider.tsx
├── lib/
│   ├── utils.ts          # Utility functions
│   ├── websocket.ts      # WebSocket client
│   └── types.ts          # TypeScript types
├── hooks/
│   └── use-websocket.ts  # WebSocket hook
├── public/
├── package.json
├── tsconfig.json
└── tailwind.config.ts
```

---

### Step 2: Install Dependencies

```bash
cd frontend

# shadcn/ui CLI
npx shadcn@latest init

# Additional dependencies
npm install zustand              # State management
npm install @tanstack/react-query  # Data fetching
npm install date-fns             # Date formatting
npm install clsx tailwind-merge  # Utility classes
```

**shadcn/ui components needed:**
```bash
npx shadcn@latest add card
npx shadcn@latest add badge
npx shadcn@latest add button
npx shadcn@latest add skeleton
npx shadcn@latest add toast
npx shadcn@latest add avatar
```

---

### Step 3: Define TypeScript Types

**File**: `frontend/lib/types.ts`

```typescript
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

export type WebSocketEvent =
  | TaskStatusChangeEvent
  | TaskProgressEvent
  | ConsultationStartedEvent
  | ConsultationCompletedEvent;
```

---

### Step 4: Create WebSocket Client

**File**: `frontend/lib/websocket.ts`

```typescript
import { WebSocketEvent } from "./types";

export class TaskWebSocketClient {
  private ws: WebSocket | null = null;
  private reconnectTimeout: NodeJS.Timeout | null = null;
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;
  private reconnectDelay = 1000;

  constructor(
    private userId: string,
    private onEvent: (event: WebSocketEvent) => void,
    private onConnect?: () => void,
    private onDisconnect?: () => void
  ) {}

  connect() {
    const wsUrl = `ws://localhost:8000/ws/${this.userId}`;

    try {
      this.ws = new WebSocket(wsUrl);

      this.ws.onopen = () => {
        console.log("✅ WebSocket connected");
        this.reconnectAttempts = 0;
        this.startHeartbeat();
        this.onConnect?.();
      };

      this.ws.onmessage = (event) => {
        if (event.data === "pong") {
          return; // Heartbeat response
        }

        try {
          const data = JSON.parse(event.data);
          this.onEvent(data);
        } catch (error) {
          console.error("Failed to parse WebSocket message:", error);
        }
      };

      this.ws.onclose = () => {
        console.log("❌ WebSocket disconnected");
        this.onDisconnect?.();
        this.handleReconnect();
      };

      this.ws.onerror = (error) => {
        console.error("WebSocket error:", error);
      };
    } catch (error) {
      console.error("Failed to create WebSocket:", error);
      this.handleReconnect();
    }
  }

  private startHeartbeat() {
    setInterval(() => {
      if (this.ws?.readyState === WebSocket.OPEN) {
        this.ws.send("ping");
      }
    }, 30000); // Every 30 seconds
  }

  private handleReconnect() {
    if (this.reconnectAttempts >= this.maxReconnectAttempts) {
      console.error("Max reconnect attempts reached");
      return;
    }

    this.reconnectAttempts++;
    const delay = this.reconnectDelay * Math.pow(2, this.reconnectAttempts - 1);

    console.log(`Reconnecting in ${delay}ms (attempt ${this.reconnectAttempts})...`);

    this.reconnectTimeout = setTimeout(() => {
      this.connect();
    }, delay);
  }

  disconnect() {
    if (this.reconnectTimeout) {
      clearTimeout(this.reconnectTimeout);
    }
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
  }
}
```

---

### Step 5: Create WebSocket Hook

**File**: `frontend/hooks/use-websocket.ts`

```typescript
"use client";

import { useEffect, useState } from "react";
import { TaskWebSocketClient } from "@/lib/websocket";
import { WebSocketEvent } from "@/lib/types";

export function useWebSocket(userId: string) {
  const [isConnected, setIsConnected] = useState(false);
  const [events, setEvents] = useState<WebSocketEvent[]>([]);
  const [client, setClient] = useState<TaskWebSocketClient | null>(null);

  useEffect(() => {
    const wsClient = new TaskWebSocketClient(
      userId,
      (event) => {
        setEvents((prev) => [...prev, event]);
      },
      () => setIsConnected(true),
      () => setIsConnected(false)
    );

    wsClient.connect();
    setClient(wsClient);

    return () => {
      wsClient.disconnect();
    };
  }, [userId]);

  return { isConnected, events, client };
}
```

---

### Step 6: Create Zustand Store for Tasks

**File**: `frontend/lib/store.ts`

```typescript
import { create } from "zustand";
import { AgentTask, TaskStatus, WebSocketEvent } from "./types";

interface TaskStore {
  tasks: Map<string, AgentTask>;
  addTask: (task: AgentTask) => void;
  updateTask: (taskId: string, updates: Partial<AgentTask>) => void;
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

  handleWebSocketEvent: (event) => {
    const { updateTask } = get();

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
    }
  },

  getTasksByStatus: (status) => {
    const tasks = Array.from(get().tasks.values());
    return tasks.filter((task) => task.status === status);
  },
}));
```

---

### Step 7: Create Task Card Component

**File**: `frontend/components/kanban/task-card.tsx`

```typescript
"use client";

import { AgentTask, TaskStatus } from "@/lib/types";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { formatDistanceToNow } from "date-fns";
import { cn } from "@/lib/utils";

interface TaskCardProps {
  task: AgentTask;
}

const statusColors = {
  [TaskStatus.QUEUED]: "bg-gray-100 text-gray-800",
  [TaskStatus.IN_PROGRESS]: "bg-blue-100 text-blue-800",
  [TaskStatus.TOOL_CALL]: "bg-purple-100 text-purple-800",
  [TaskStatus.COMPLETED]: "bg-green-100 text-green-800",
  [TaskStatus.FAILED]: "bg-red-100 text-red-800",
};

export function TaskCard({ task }: TaskCardProps) {
  return (
    <Card className="mb-3 hover:shadow-md transition-shadow">
      <CardHeader className="pb-3">
        <div className="flex items-start justify-between">
          <div className="flex items-center gap-2">
            <Avatar className="h-8 w-8">
              <AvatarFallback className="text-xs bg-blue-500 text-white">
                {task.agent_nickname.slice(0, 2).toUpperCase()}
              </AvatarFallback>
            </Avatar>
            <div>
              <CardTitle className="text-sm font-medium">
                @{task.agent_nickname}
              </CardTitle>
              <p className="text-xs text-muted-foreground">
                {task.agent_id}
              </p>
            </div>
          </div>
          <Badge variant="secondary" className={cn("text-xs", statusColors[task.status])}>
            {task.status.replace("_", " ")}
          </Badge>
        </div>
      </CardHeader>

      <CardContent>
        <p className="text-sm mb-3">{task.command_text}</p>

        {/* Progress bar */}
        {task.status === TaskStatus.IN_PROGRESS && (
          <div className="mb-3">
            <div className="flex justify-between text-xs text-muted-foreground mb-1">
              <span>{task.current_node || "Processing"}</span>
              <span>{task.progress_percentage}%</span>
            </div>
            <div className="w-full bg-gray-200 rounded-full h-2">
              <div
                className="bg-blue-500 h-2 rounded-full transition-all duration-300"
                style={{ width: `${task.progress_percentage}%` }}
              />
            </div>
          </div>
        )}

        {/* Consultation indicator */}
        {task.status === TaskStatus.TOOL_CALL && task.consultation_target_nickname && (
          <Badge variant="outline" className="text-xs mb-2">
            Consulting @{task.consultation_target_nickname}
          </Badge>
        )}

        {/* Timestamps */}
        <div className="flex justify-between text-xs text-muted-foreground pt-2 border-t">
          <span>
            Created {formatDistanceToNow(new Date(task.created_at), { addSuffix: true })}
          </span>
          {task.completed_at && (
            <span>
              Completed {formatDistanceToNow(new Date(task.completed_at), { addSuffix: true })}
            </span>
          )}
        </div>
      </CardContent>
    </Card>
  );
}
```

---

### Step 8: Create Kanban Column Component

**File**: `frontend/components/kanban/kanban-column.tsx`

```typescript
"use client";

import { TaskStatus, AgentTask } from "@/lib/types";
import { TaskCard } from "./task-card";

interface KanbanColumnProps {
  title: string;
  status: TaskStatus;
  tasks: AgentTask[];
  count: number;
}

const statusConfig = {
  [TaskStatus.QUEUED]: {
    title: "Queued",
    color: "bg-gray-100 border-gray-300",
  },
  [TaskStatus.IN_PROGRESS]: {
    title: "In Progress",
    color: "bg-blue-50 border-blue-300",
  },
  [TaskStatus.TOOL_CALL]: {
    title: "Tool Call",
    color: "bg-purple-50 border-purple-300",
  },
  [TaskStatus.COMPLETED]: {
    title: "Completed",
    color: "bg-green-50 border-green-300",
  },
  [TaskStatus.FAILED]: {
    title: "Failed",
    color: "bg-red-50 border-red-300",
  },
};

export function KanbanColumn({ status, tasks, count }: KanbanColumnProps) {
  const config = statusConfig[status];

  return (
    <div className="flex-1 min-w-[300px]">
      <div className={`rounded-lg border-2 ${config.color} p-4 h-full`}>
        <div className="flex items-center justify-between mb-4">
          <h2 className="font-semibold text-lg">{config.title}</h2>
          <span className="text-sm text-muted-foreground bg-white px-2 py-1 rounded-full">
            {count}
          </span>
        </div>

        <div className="space-y-3 max-h-[calc(100vh-200px)] overflow-y-auto">
          {tasks.length === 0 ? (
            <p className="text-sm text-muted-foreground text-center py-8">
              No tasks
            </p>
          ) : (
            tasks.map((task) => <TaskCard key={task.id} task={task} />)
          )}
        </div>
      </div>
    </div>
  );
}
```

---

### Step 9: Create Kanban Board Component

**File**: `frontend/components/kanban/kanban-board.tsx`

```typescript
"use client";

import { useEffect } from "react";
import { useTaskStore } from "@/lib/store";
import { useWebSocket } from "@/hooks/use-websocket";
import { TaskStatus } from "@/lib/types";
import { KanbanColumn } from "./kanban-column";
import { Badge } from "@/components/ui/badge";

const MVP_USER_ID = "00000000-0000-0000-0000-000000000001";

export function KanbanBoard() {
  const { tasks, getTasksByStatus, handleWebSocketEvent } = useTaskStore();
  const { isConnected, events } = useWebSocket(MVP_USER_ID);

  // Handle WebSocket events
  useEffect(() => {
    if (events.length > 0) {
      const latestEvent = events[events.length - 1];
      handleWebSocketEvent(latestEvent);
    }
  }, [events, handleWebSocketEvent]);

  // Fetch initial tasks
  useEffect(() => {
    async function fetchTasks() {
      try {
        const response = await fetch(
          `http://localhost:8000/api/tasks?user_id=${MVP_USER_ID}`
        );
        const data = await response.json();

        data.forEach((task: any) => {
          useTaskStore.getState().addTask(task);
        });
      } catch (error) {
        console.error("Failed to fetch tasks:", error);
      }
    }

    fetchTasks();
  }, []);

  const columns = [
    { status: TaskStatus.QUEUED, tasks: getTasksByStatus(TaskStatus.QUEUED) },
    { status: TaskStatus.IN_PROGRESS, tasks: getTasksByStatus(TaskStatus.IN_PROGRESS) },
    { status: TaskStatus.TOOL_CALL, tasks: getTasksByStatus(TaskStatus.TOOL_CALL) },
    { status: TaskStatus.COMPLETED, tasks: getTasksByStatus(TaskStatus.COMPLETED) },
    { status: TaskStatus.FAILED, tasks: getTasksByStatus(TaskStatus.FAILED) },
  ];

  return (
    <div className="p-6">
      {/* Header */}
      <div className="mb-6 flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Agent Tasks</h1>
          <p className="text-muted-foreground">
            Real-time task monitoring and management
          </p>
        </div>
        <Badge variant={isConnected ? "default" : "destructive"}>
          {isConnected ? "🟢 Connected" : "🔴 Disconnected"}
        </Badge>
      </div>

      {/* Kanban Board */}
      <div className="flex gap-4 overflow-x-auto pb-4">
        {columns.map((column) => (
          <KanbanColumn
            key={column.status}
            status={column.status}
            tasks={column.tasks}
            count={column.tasks.length}
          />
        ))}
      </div>

      {/* Stats */}
      <div className="mt-6 text-sm text-muted-foreground">
        Total tasks: {tasks.size} | Events received: {events.length}
      </div>
    </div>
  );
}
```

---

### Step 10: Update Main Page

**File**: `frontend/app/page.tsx`

```typescript
import { KanbanBoard } from "@/components/kanban/kanban-board";

export default function Home() {
  return (
    <main className="min-h-screen bg-background">
      <KanbanBoard />
    </main>
  );
}
```

---

### Step 11: Update Root Layout

**File**: `frontend/app/layout.tsx`

```typescript
import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "Commander.ai - Task Management",
  description: "Real-time agent task monitoring and management",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className={inter.className}>{children}</body>
    </html>
  );
}
```

---

### Step 12: Configure CORS for Development

**Update**: `backend/core/config.py`

Make sure CORS includes the Next.js dev server:

```python
# CORS Configuration
cors_origins: str = "http://localhost:3000,http://localhost:3001"
```

---

## Testing

**1. Start Backend:**
```bash
# Terminal 1: Start backend
uvicorn backend.api.main:app --reload
```

**2. Start Frontend:**
```bash
# Terminal 2: Start frontend
cd frontend
npm run dev
```

**3. Test WebSocket Connection:**
- Open http://localhost:3000
- Check browser console for "✅ WebSocket connected"
- Verify badge shows "🟢 Connected"

**4. Test Task Display:**
```bash
# Terminal 3: Create test tasks
curl -X POST http://localhost:8000/api/tasks \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "00000000-0000-0000-0000-000000000001",
    "agent_id": "agent_a",
    "thread_id": "00000000-0000-0000-0000-000000000002",
    "command_text": "@bob research quantum computing"
  }'
```

**5. Test Real-Time Updates:**
- Create a task via API
- Watch it appear in the Kanban board immediately
- No page refresh needed

---

## File Checklist

**Frontend Structure:**
- [ ] `frontend/` - Next.js app created
- [ ] `frontend/lib/types.ts` - TypeScript types
- [ ] `frontend/lib/websocket.ts` - WebSocket client
- [ ] `frontend/lib/store.ts` - Zustand store
- [ ] `frontend/lib/utils.ts` - Utility functions (from shadcn)
- [ ] `frontend/hooks/use-websocket.ts` - WebSocket hook
- [ ] `frontend/components/ui/` - shadcn components
- [ ] `frontend/components/kanban/kanban-board.tsx` - Board component
- [ ] `frontend/components/kanban/kanban-column.tsx` - Column component
- [ ] `frontend/components/kanban/task-card.tsx` - Card component
- [ ] `frontend/app/page.tsx` - Main page
- [ ] `frontend/app/layout.tsx` - Root layout

**Configuration:**
- [ ] `frontend/package.json` - Dependencies installed
- [ ] `frontend/tailwind.config.ts` - Tailwind configured
- [ ] `frontend/components.json` - shadcn config
- [ ] `backend/core/config.py` - CORS updated

---

## Optional Enhancements (Post-MVP)

1. **Drag and Drop**
   - Install `@dnd-kit/core`
   - Enable task status changes via drag

2. **Task Filtering**
   - Filter by agent
   - Search by command text
   - Date range filters

3. **Task Actions**
   - Retry failed tasks
   - Cancel running tasks
   - View task details modal

4. **Notifications**
   - Toast notifications for events
   - Sound alerts for failures
   - Desktop notifications

5. **Performance**
   - Virtual scrolling for large task lists
   - Task pagination
   - Optimistic updates

---

## Success Criteria

- ✅ Frontend displays tasks in 5 columns (queued, in_progress, tool_call, completed, failed)
- ✅ WebSocket connection established and maintained
- ✅ Real-time task status updates without refresh
- ✅ Progress bars animate during task execution
- ✅ Consultation indicators show when agents consult each other
- ✅ Responsive design works on desktop and tablet
- ✅ No console errors in browser
- ✅ Clean, professional UI using shadcn components

---

## Next Steps After Phase 3B-C

1. **Phase 4**: User authentication and multi-user support
2. **Phase 5**: Command input interface
3. **Phase 6**: Agent conversation history viewer
4. **Phase 7**: Production deployment
