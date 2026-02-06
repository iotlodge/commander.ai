# Code Patterns - Commander.ai

**Last Updated**: 2026-01-31

---

## Frontend Patterns (Phase 3B-C)

### Next.js App Router Structure

```typescript
// app/page.tsx - Server Component (default)
import { KanbanBoard } from "@/components/kanban/kanban-board";

export default function Home() {
  return (
    <main className="min-h-screen bg-background">
      <KanbanBoard />
    </main>
  );
}
```

**Pattern**: Use Server Components by default, only add `"use client"` when needed for:
- State (`useState`, `useReducer`)
- Effects (`useEffect`, `useLayoutEffect`)
- Event handlers (`onClick`, `onChange`)
- Browser APIs (`localStorage`, `WebSocket`)
- Context providers

### Client Components with Hooks

```typescript
// components/kanban/kanban-board.tsx
"use client";

import { useEffect } from "react";
import { useTaskStore } from "@/lib/store";
import { useWebSocket } from "@/hooks/use-websocket";

export function KanbanBoard() {
  const { tasks, handleWebSocketEvent, addTask } = useTaskStore();
  const { isConnected, events } = useWebSocket(MVP_USER_ID);

  // Handle WebSocket events
  useEffect(() => {
    if (events.length > 0) {
      const latestEvent = events[events.length - 1];
      handleWebSocketEvent(latestEvent);
    }
  }, [events, handleWebSocketEvent]);

  return (/* JSX */);
}
```

**Pattern**: Mark components with `"use client"` at the top when using React hooks or browser APIs.

### TypeScript Type Definitions

```typescript
// lib/types.ts - Match backend Pydantic models exactly
export enum TaskStatus {
  QUEUED = "queued",
  IN_PROGRESS = "in_progress",
  TOOL_CALL = "tool_call",
  COMPLETED = "completed",
  FAILED = "failed",
}

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
  metadata: Record<string, unknown>;
  created_at: string;
  started_at: string | null;
  completed_at: string | null;
}
```

**Pattern**: Keep frontend types synchronized with backend Pydantic models. Use enums for string literals.

### Zustand Store Pattern

```typescript
// lib/store.ts
import { create } from "zustand";
import type { AgentTask, WebSocketEvent } from "./types";

interface TaskStore {
  tasks: Map<string, AgentTask>;
  addTask: (task: AgentTask) => void;
  updateTask: (id: string, updates: Partial<AgentTask>) => void;
  getTasksByStatus: (status: TaskStatus) => AgentTask[];
  handleWebSocketEvent: (event: WebSocketEvent) => void;
}

export const useTaskStore = create<TaskStore>((set, get) => ({
  tasks: new Map(),

  addTask: (task) =>
    set((state) => {
      const newTasks = new Map(state.tasks);
      newTasks.set(task.id, task);
      return { tasks: newTasks };
    }),

  updateTask: (id, updates) =>
    set((state) => {
      const task = state.tasks.get(id);
      if (!task) return state;

      const newTasks = new Map(state.tasks);
      newTasks.set(id, { ...task, ...updates });
      return { tasks: newTasks };
    }),

  getTasksByStatus: (status) => {
    const { tasks } = get();
    return Array.from(tasks.values()).filter((t) => t.status === status);
  },

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
      // ... other cases
    }
  },
}));
```

**Pattern**:
- Use `Map` for keyed collections (faster lookups than arrays)
- Immutable updates (create new Map instead of mutating)
- Separate concerns (getters, setters, event handlers)
- Type-safe with TypeScript interfaces

### WebSocket Client Pattern

```typescript
// lib/websocket.ts
export class TaskWebSocketClient {
  private ws: WebSocket | null = null;
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;
  private reconnectDelay = 1000; // 1 second base delay
  private heartbeatInterval: NodeJS.Timeout | null = null;

  constructor(
    private userId: string,
    private onMessage: (event: WebSocketEvent) => void,
    private onConnect?: () => void,
    private onDisconnect?: () => void
  ) {}

  connect() {
    try {
      this.ws = new WebSocket(`ws://localhost:8000/ws/${this.userId}`);

      this.ws.onopen = () => {
        console.log("✅ WebSocket connected");
        this.reconnectAttempts = 0;
        this.startHeartbeat();
        this.onConnect?.();
      };

      this.ws.onmessage = (event) => {
        const data = JSON.parse(event.data);
        this.onMessage(data);
      };

      this.ws.onerror = (error) => {
        console.error("❌ WebSocket error:", error);
      };

      this.ws.onclose = () => {
        console.log("🔌 WebSocket disconnected");
        this.stopHeartbeat();
        this.onDisconnect?.();
        this.handleReconnect();
      };
    } catch (error) {
      console.error("Failed to create WebSocket:", error);
      this.handleReconnect();
    }
  }

  private handleReconnect() {
    if (this.reconnectAttempts >= this.maxReconnectAttempts) {
      console.error("Max reconnection attempts reached");
      return;
    }

    this.reconnectAttempts++;
    const delay = this.reconnectDelay * Math.pow(2, this.reconnectAttempts - 1);

    console.log(`Reconnecting in ${delay}ms (attempt ${this.reconnectAttempts})`);
    setTimeout(() => this.connect(), delay);
  }

  private startHeartbeat() {
    this.heartbeatInterval = setInterval(() => {
      if (this.ws?.readyState === WebSocket.OPEN) {
        this.ws.send("ping");
      }
    }, 30000); // 30 seconds
  }

  private stopHeartbeat() {
    if (this.heartbeatInterval) {
      clearInterval(this.heartbeatInterval);
      this.heartbeatInterval = null;
    }
  }

  disconnect() {
    this.stopHeartbeat();
    this.ws?.close();
    this.ws = null;
  }
}
```

**Pattern**:
- Auto-reconnect with exponential backoff
- Heartbeat to keep connection alive
- Callback-based event handling
- Graceful error handling and cleanup

### Custom React Hook for WebSocket

```typescript
// hooks/use-websocket.ts
import { useEffect, useState } from "react";
import { TaskWebSocketClient } from "@/lib/websocket";
import type { WebSocketEvent } from "@/lib/types";

export function useWebSocket(userId: string) {
  const [isConnected, setIsConnected] = useState(false);
  const [events, setEvents] = useState<WebSocketEvent[]>([]);

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

    return () => {
      wsClient.disconnect();
    };
  }, [userId]);

  return { isConnected, events };
}
```

**Pattern**:
- Encapsulate WebSocket logic in custom hook
- Clean up on unmount (return cleanup function)
- Track connection state and events separately
- Re-create connection if userId changes

### shadcn/ui Component Usage

```typescript
// components/kanban/task-card.tsx
import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";

export function TaskCard({ task }: TaskCardProps) {
  const statusColor = {
    queued: "bg-gray-500",
    in_progress: "bg-blue-500",
    tool_call: "bg-purple-500",
    completed: "bg-green-500",
    failed: "bg-red-500",
  }[task.status];

  return (
    <Card className="cursor-pointer hover:shadow-lg transition-shadow">
      <CardHeader className="flex flex-row items-center gap-3 pb-3">
        <Avatar className="h-10 w-10">
          <AvatarFallback className={statusColor}>
            {task.agent_nickname.slice(0, 2).toUpperCase()}
          </AvatarFallback>
        </Avatar>
        <div className="flex-1">
          <h3 className="font-semibold text-sm">{task.agent_nickname}</h3>
          <Badge variant="outline" className="mt-1">
            {task.status}
          </Badge>
        </div>
      </CardHeader>
      <CardContent>
        <p className="text-sm text-muted-foreground line-clamp-2">
          {task.command_text}
        </p>
      </CardContent>
    </Card>
  );
}
```

**Pattern**:
- Import individual components from `@/components/ui/*`
- Use Tailwind utility classes for styling
- Combine shadcn components with custom logic
- Use `className` for conditional styling

---

## Backend Patterns (Phase 3A)

### Task Management Pattern

```python
# backend/repositories/task_repository.py
class TaskRepository:
    """Data access layer for agent tasks"""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_task(self, task: TaskCreate) -> AgentTask:
        """Create new task in database"""
        # Get agent nickname from registry
        agent = AgentRegistry.get_specialist(task.agent_id)
        agent_nickname = agent.nickname if agent else task.agent_id

        # Create SQLAlchemy model
        db_task = AgentTaskModel(
            id=uuid4(),
            user_id=task.user_id,
            agent_id=task.agent_id,
            agent_nickname=agent_nickname,
            thread_id=task.thread_id,
            command_text=task.command_text,
            status=TaskStatus.QUEUED,
            progress_percentage=0,
            meta_data={},  # Note: "metadata" is reserved in SQLAlchemy
        )

        self.session.add(db_task)
        await self.session.commit()
        await self.session.refresh(db_task)

        # Convert to Pydantic model
        return AgentTask.model_validate(db_task)
```

**Pattern**: Repository pattern separates data access from business logic. Always convert SQLAlchemy models to Pydantic models at repository boundaries.

### WebSocket Pattern

```python
# backend/api/websocket.py
class TaskWebSocketManager:
    """Singleton manager for WebSocket connections"""

    def __init__(self):
        self.active_connections: dict[UUID, WebSocket] = {}

    async def connect(self, websocket: WebSocket, user_id: UUID):
        """Accept and store WebSocket connection"""
        await websocket.accept()
        self.active_connections[user_id] = websocket

    async def broadcast_task_event(self, event: BaseModel):
        """Broadcast event to all connected clients"""
        message = event.model_dump(mode='json')

        disconnected = []
        for user_id, connection in self.active_connections.items():
            try:
                await connection.send_json(message)
            except Exception:
                disconnected.append(user_id)

        # Clean up failed connections
        for user_id in disconnected:
            self.disconnect(user_id)


# Singleton instance
_ws_manager: TaskWebSocketManager | None = None

def get_ws_manager() -> TaskWebSocketManager:
    """Get or create WebSocket manager singleton"""
    global _ws_manager
    if _ws_manager is None:
        _ws_manager = TaskWebSocketManager()
    return _ws_manager
```

**Pattern**: Use singleton pattern for WebSocket manager to maintain single instance across all requests.

### Progress Callback Pattern

```python
# backend/core/task_callback.py
class TaskProgressCallback:
    """Callback for tracking agent execution progress"""

    def __init__(
        self,
        task_id: UUID,
        repo: TaskRepository,
        ws_manager: TaskWebSocketManager
    ):
        self.task_id = task_id
        self.repo = repo
        self.ws_manager = ws_manager

    async def on_status_change(self, old_status: TaskStatus, new_status: TaskStatus):
        """Called when task status changes"""
        kwargs = {}
        if new_status == TaskStatus.IN_PROGRESS:
            kwargs['started_at'] = datetime.utcnow()
        elif new_status in (TaskStatus.COMPLETED, TaskStatus.FAILED):
            kwargs['completed_at'] = datetime.utcnow()

        await self.repo.set_status(self.task_id, new_status, **kwargs)

        event = TaskStatusChangeEvent(
            task_id=self.task_id,
            old_status=old_status,
            new_status=new_status,
            timestamp=datetime.utcnow()
        )
        await self.ws_manager.broadcast_task_event(event)
```

**Pattern**: Callbacks are passed through agent state (not constructor) to maintain stateless agents.

### Agent Execution with Callbacks

```python
# backend/agents/base/agent_interface.py
async def execute(
    self,
    command: str,
    context: AgentExecutionContext,
) -> AgentExecutionResult:
    """Execute agent graph with optional progress tracking"""

    # Notify task started
    if context.task_callback:
        await context.task_callback.on_status_change(
            TaskStatus.QUEUED, TaskStatus.IN_PROGRESS
        )

    try:
        # Execute graph
        result = await self._execute_graph(command, conversation_context)

        # Notify completion
        if context.task_callback:
            await context.task_callback.on_status_change(
                TaskStatus.IN_PROGRESS, TaskStatus.COMPLETED
            )

        return AgentExecutionResult(success=True, response=result)

    except Exception as e:
        # Notify failure
        if context.task_callback:
            await context.task_callback.on_status_change(
                TaskStatus.IN_PROGRESS, TaskStatus.FAILED
            )
        raise
```

**Pattern**: Check if callback exists before calling (optional callback pattern).

### Progress Reporting in Agent Nodes

```python
# backend/agents/specialized/agent_a/nodes.py
async def search_node(state: ResearchAgentState) -> dict:
    """Perform web search with progress reporting"""
    query = state["query"]

    # Report progress if callback exists
    callback = state.get("task_callback")
    if callback:
        await callback.on_progress_update(25, "searching")

    # Perform search
    search_results = await perform_search(query)

    return {
        **state,
        "search_results": search_results,
        "current_step": "searched",
    }
```

**Pattern**: Nodes report progress at key checkpoints (start, middle, end of operations).

---

## Memory System Patterns (Phase 1-2)

### LangGraph Checkpointer Pattern

```python
# backend/memory/short_term_memory.py
class ShortTermMemory:
    """Redis-backed STM with LangGraph integration"""

    def __init__(self, redis_client: Redis):
        self.redis = redis_client

    async def get_checkpoint(
        self, thread_id: str, checkpoint_id: str | None = None
    ) -> dict | None:
        """Get conversation checkpoint from Redis"""
        key = f"checkpoint:{thread_id}"
        if checkpoint_id:
            key = f"{key}:{checkpoint_id}"

        data = await self.redis.get(key)
        return json.loads(data) if data else None

    async def save_checkpoint(
        self, thread_id: str, checkpoint_id: str, data: dict
    ) -> None:
        """Save conversation checkpoint to Redis"""
        key = f"checkpoint:{thread_id}:{checkpoint_id}"
        await self.redis.setex(
            key,
            3600,  # 1 hour TTL
            json.dumps(data)
        )
```

**Pattern**: Use Redis for ephemeral conversation state with TTL expiration.

### Semantic Memory Pattern

```python
# backend/memory/long_term_memory.py
class LongTermMemory:
    """PostgreSQL + Qdrant LTM with semantic search"""

    async def store_memory(
        self,
        user_id: UUID,
        thread_id: UUID,
        content: str,
        memory_type: MemoryType,
        metadata: dict[str, Any] | None = None,
    ) -> SemanticMemory:
        """Store memory with vector embedding"""
        # Generate embedding
        embedding = await self.embedding_service.embed(content)

        # Store in PostgreSQL
        memory = SemanticMemoryModel(
            id=uuid4(),
            user_id=user_id,
            thread_id=thread_id,
            content=content,
            memory_type=memory_type,
            metadata=metadata or {},
        )
        self.session.add(memory)
        await self.session.commit()

        # Store in Qdrant
        await self.vector_store.upsert(
            collection_name="semantic_memory",
            points=[{
                "id": str(memory.id),
                "vector": embedding,
                "payload": {
                    "user_id": str(user_id),
                    "thread_id": str(thread_id),
                    "content": content,
                    "memory_type": memory_type,
                }
            }]
        )

        return SemanticMemory.model_validate(memory)
```

**Pattern**: Dual storage - PostgreSQL for structured data, Qdrant for vector search.

---

## API Patterns

### FastAPI Dependency Injection

```python
# backend/api/routes/tasks.py
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/api/tasks", tags=["tasks"])

@router.post("", response_model=AgentTask)
async def create_task(
    task: TaskCreate,
    repo: TaskRepository = Depends(get_task_repository),
):
    """Create new task with automatic dependency injection"""
    agent_task = await repo.create_task(task)

    # Broadcast via WebSocket
    ws_manager = get_ws_manager()
    await ws_manager.broadcast_task_event(
        TaskStatusChangeEvent(...)
    )

    return agent_task
```

**Pattern**: Use `Depends()` for dependency injection. Keep route handlers thin - delegate to repositories and services.

---

## Testing Patterns

### Async Test Fixtures

```python
# tests/conftest.py
import pytest
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession

@pytest.fixture
async def async_session():
    """Async database session for testing"""
    engine = create_async_engine("postgresql+asyncpg://...")
    async with AsyncSession(engine) as session:
        yield session
        await session.rollback()
```

**Pattern**: Use async fixtures with pytest-asyncio for async code testing.

---

## File Naming Conventions

### Backend
- `snake_case.py` for all Python files
- `*_repository.py` for data access layers
- `*_service.py` for business logic
- `*_models.py` for data models
- `test_*.py` for test files

### Frontend
- `kebab-case.tsx` for components (`task-card.tsx`)
- `camelCase.ts` for utilities (`websocket.ts`)
- `types.ts` for type definitions
- `store.ts` for state management

---

## Import Organization

### Backend Python
```python
# Standard library
import asyncio
from datetime import datetime
from uuid import UUID, uuid4

# Third-party
from fastapi import APIRouter, Depends
from sqlalchemy import select
from pydantic import BaseModel

# Local
from backend.core.config import get_settings
from backend.models.task_models import AgentTask
from backend.repositories.task_repository import TaskRepository
```

### Frontend TypeScript
```typescript
// React
import { useEffect, useState } from "react";

// Next.js
import type { Metadata } from "next";

// Third-party
import { create } from "zustand";

// Local components
import { KanbanBoard } from "@/components/kanban/kanban-board";
import { Badge } from "@/components/ui/badge";

// Local utilities
import type { AgentTask, TaskStatus } from "@/lib/types";
import { TaskWebSocketClient } from "@/lib/websocket";
```

**Pattern**: Group imports by category, sort alphabetically within each group.