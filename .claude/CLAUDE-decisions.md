# Architecture Decision Records - Commander.ai

**Last Updated**: 2026-01-31

---

## ADR-023: Next.js 14 App Router

**Status**: Accepted (2026-01-31)

**Context**:
Phase 3B-C requires a modern React-based frontend for the Kanban task board. Next.js offers both App Router (new) and Pages Router (legacy) architectures.

**Decision**:
Use Next.js 14 App Router for the frontend implementation.

**Rationale**:
- **Server Components by default**: Better performance with less JavaScript sent to client
- **Streaming and Suspense**: Native support for progressive rendering
- **Simplified routing**: File-system based routing with layouts and nested routes
- **Future-proof**: App Router is the recommended approach for new Next.js projects
- **TypeScript integration**: First-class TypeScript support

**Consequences**:
- ✅ Improved performance (Server Components reduce client bundle size)
- ✅ Better developer experience (simpler mental model)
- ✅ Future-proof architecture (aligned with React's direction)
- ⚠️ Learning curve for developers familiar with Pages Router
- ⚠️ Must explicitly mark client components with "use client"

**Alternatives Considered**:
- **Pages Router**: Rejected - legacy approach, more boilerplate
- **Vite + React**: Rejected - no SSR/SSG capabilities, more manual setup
- **Create React App**: Rejected - deprecated, no longer maintained

---

## ADR-024: Zustand for State Management

**Status**: Accepted (2026-01-31)

**Context**:
Phase 3B-C requires client-side state management for Kanban board task data, WebSocket events, and UI state.

**Decision**:
Use Zustand for global state management.

**Rationale**:
- **Minimal boilerplate**: Simple API, less code than Redux
- **TypeScript-first**: Excellent type inference
- **No providers**: Works without React Context (less wrapper hell)
- **DevTools support**: Integrates with Redux DevTools
- **Small bundle size**: ~1KB gzipped
- **Hook-based**: Natural fit with React hooks

**Consequences**:
- ✅ Less boilerplate code (faster development)
- ✅ Better TypeScript experience (strong type inference)
- ✅ Easier testing (no provider wrappers needed)
- ✅ Smaller bundle size (better performance)
- ⚠️ Less opinionated than Redux (need to establish patterns)
- ⚠️ Smaller ecosystem than Redux (fewer middleware options)

**Alternatives Considered**:
- **Redux Toolkit**: Rejected - too much boilerplate for simple state
- **React Context**: Rejected - performance issues with frequent updates
- **Jotai**: Rejected - atomic state model too complex for this use case
- **Recoil**: Rejected - larger bundle, still experimental

---

## ADR-025: shadcn/ui Component Library

**Status**: Accepted (2026-01-31)

**Context**:
Phase 3B-C requires UI components for the Kanban board (cards, badges, avatars, progress bars).

**Decision**:
Use shadcn/ui component library built on Radix UI primitives.

**Rationale**:
- **Copy-paste approach**: Components live in your codebase (full control)
- **Built on Radix UI**: Accessible, unstyled primitives
- **Tailwind CSS**: Consistent styling with utility classes
- **TypeScript-native**: Full type safety
- **Customizable**: Easy to modify since code is local
- **Modern design**: Professional, polished aesthetics
- **No runtime overhead**: Components are local files, not package dependency

**Consequences**:
- ✅ Full ownership of component code (can modify freely)
- ✅ Accessibility built-in (Radix UI primitives)
- ✅ Consistent Tailwind styling
- ✅ No version lock-in (components are local)
- ⚠️ Must manually update components (no npm update)
- ⚠️ Slightly larger codebase (components in repo)

**Alternatives Considered**:
- **Material-UI**: Rejected - heavy bundle, opinionated design
- **Ant Design**: Rejected - less customizable, different design system
- **Chakra UI**: Rejected - runtime style generation, larger bundle
- **Headless UI**: Rejected - unstyled only, would need more work

---

## ADR-026: Custom WebSocket Client

**Status**: Accepted (2026-01-31)

**Context**:
Phase 3B-C requires WebSocket connection for real-time task updates from backend.

**Decision**:
Implement custom WebSocket client class with auto-reconnect and exponential backoff.

**Rationale**:
- **Native WebSocket API**: Browser built-in, no dependencies
- **Full control**: Custom reconnection logic, heartbeat, error handling
- **Type-safe**: TypeScript wrapper around native API
- **Lightweight**: No external library overhead
- **Simple requirements**: Basic WebSocket features sufficient for our use case

**Consequences**:
- ✅ Zero dependencies (smaller bundle)
- ✅ Full control over behavior (reconnection, heartbeat)
- ✅ Custom to our needs (no unused features)
- ✅ TypeScript type safety
- ⚠️ Must implement reconnection logic ourselves
- ⚠️ No advanced features (rooms, namespaces, etc.)

**Alternatives Considered**:
- **socket.io-client**: Rejected - overkill for simple WebSocket, larger bundle
- **ws library**: Rejected - Node.js only, not for browser
- **reconnecting-websocket**: Rejected - adds dependency for simple feature

**Implementation Details**:
```typescript
class TaskWebSocketClient {
  // Auto-reconnect with exponential backoff
  // Heartbeat every 30 seconds
  // Max 5 reconnection attempts
  // Callback-based event handling
}
```

---

## ADR-027: TypeScript Strict Mode

**Status**: Accepted (2026-01-31)

**Context**:
Phase 3B-C TypeScript frontend needs type checking configuration.

**Decision**:
Enable TypeScript strict mode in `tsconfig.json`.

**Rationale**:
- **Type safety**: Catch errors at compile time
- **Better IDE support**: More accurate autocomplete and refactoring
- **Code quality**: Forces explicit typing, reduces bugs
- **Industry standard**: Most modern TypeScript projects use strict mode
- **Next.js default**: Aligned with Next.js best practices

**Consequences**:
- ✅ Fewer runtime errors (caught at compile time)
- ✅ Better refactoring safety (type errors surface immediately)
- ✅ Improved documentation (types serve as inline docs)
- ✅ Better team collaboration (explicit contracts)
- ⚠️ More verbose code (explicit types required)
- ⚠️ Slightly slower development (must satisfy type checker)

**Configuration**:
```json
{
  "compilerOptions": {
    "strict": true,
    "noUncheckedIndexedAccess": true,
    "noImplicitOverride": true,
    "strictNullChecks": true,
    "strictFunctionTypes": true,
    "strictBindCallApply": true,
    "strictPropertyInitialization": true
  }
}
```

---

## ADR-022: Repository Pattern for Data Access

**Status**: Accepted (2026-01-31)

**Context**:
Phase 3A requires database operations for agent tasks (CRUD operations).

**Decision**:
Use Repository pattern to separate data access logic from business logic.

**Rationale**:
- **Separation of concerns**: Data access isolated from API routes
- **Testability**: Easy to mock repositories for unit tests
- **Consistency**: Standardized data access patterns
- **Reusability**: Repositories can be used across multiple API endpoints
- **Type safety**: Pydantic models at repository boundaries

**Consequences**:
- ✅ Better testability (mock repositories in tests)
- ✅ Cleaner API routes (thin controllers)
- ✅ Easier to change database layer (swap SQLAlchemy for another ORM)
- ⚠️ Additional abstraction layer (more files)

**Implementation**:
```python
class TaskRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_task(self, task: TaskCreate) -> AgentTask:
        # Data access logic here
        pass
```

---

## ADR-021: MVP User ID in Settings

**Status**: Accepted (2026-01-31)

**Context**:
Phase 3A requires user identification for task management, but full authentication is not in scope for MVP.

**Decision**:
Use hardcoded MVP user ID in backend settings and frontend constants.

**Rationale**:
- **Simplicity**: No authentication system needed for MVP
- **Testability**: Consistent user ID for testing
- **Iteration speed**: Focus on core features first
- **Future migration path**: Easy to swap with real authentication later

**Consequences**:
- ✅ Faster MVP development (no auth system)
- ✅ Simpler testing (predictable user ID)
- ✅ Single-user mode sufficient for proof of concept
- ⚠️ Not production-ready (no multi-user support)
- ⚠️ Must add auth system before production

**Configuration**:
```python
# backend/core/config.py
class Settings(BaseSettings):
    mvp_user_id: str = "00000000-0000-0000-0000-000000000001"
```

```typescript
// frontend/components/kanban/kanban-board.tsx
const MVP_USER_ID = "00000000-0000-0000-0000-000000000001";
```

---

## ADR-020: Progress Callbacks via State Passing

**Status**: Accepted (2026-01-31)

**Context**:
Phase 3A requires agent execution progress tracking for UI updates.

**Decision**:
Pass progress callbacks through agent state (not constructor) to maintain stateless agents.

**Rationale**:
- **Stateless agents**: Agents remain pure, reusable
- **Flexible**: Different executions can have different callbacks
- **LangGraph compatible**: State-based approach aligns with LangGraph patterns
- **Testability**: Easy to test agents with/without callbacks

**Consequences**:
- ✅ Agents remain stateless (better for testing)
- ✅ Callbacks are optional (agents work without them)
- ✅ Flexible per-execution behavior
- ⚠️ Must check if callback exists before calling
- ⚠️ Callback must be passed through state to each node

**Implementation**:
```python
class AgentExecutionContext(BaseModel):
    user_id: UUID
    thread_id: UUID
    command: str
    task_callback: Any = None  # Optional callback

async def search_node(state: ResearchAgentState):
    callback = state.get("task_callback")
    if callback:
        await callback.on_progress_update(25, "searching")
```

---

## ADR-019: WebSocket Singleton Pattern

**Status**: Accepted (2026-01-31)

**Context**:
Phase 3A requires WebSocket manager to broadcast task updates to connected clients.

**Decision**:
Implement WebSocket manager as singleton to maintain single instance across all requests.

**Rationale**:
- **Shared state**: All routes need access to same connection pool
- **Memory efficiency**: Single manager instance
- **Consistency**: All broadcasts go through same manager
- **FastAPI compatibility**: Works with FastAPI dependency injection

**Consequences**:
- ✅ Single source of truth for connections
- ✅ Memory efficient (one instance)
- ✅ Thread-safe (Python GIL handles concurrent access)
- ⚠️ Global state (must be careful with testing)

**Implementation**:
```python
_ws_manager: TaskWebSocketManager | None = None

def get_ws_manager() -> TaskWebSocketManager:
    global _ws_manager
    if _ws_manager is None:
        _ws_manager = TaskWebSocketManager()
    return _ws_manager
```

---

## ADR-018: Alembic for Python-Based Migrations

**Status**: Accepted (2026-01-31)

**Context**:
Phase 3A requires database schema migrations for agent_tasks table. Previously used raw SQL migrations.

**Decision**:
Use Alembic for Python-based schema migrations.

**Rationale**:
- **Version control**: Track schema changes in code
- **Reversibility**: Auto-generated downgrade functions
- **Type safety**: Python code instead of raw SQL
- **SQLAlchemy integration**: Shares models with application code
- **Team collaboration**: Clear migration history

**Consequences**:
- ✅ Better version control (Python files in git)
- ✅ Reversible migrations (auto-generated downgrade)
- ✅ Type-safe (Python instead of SQL)
- ✅ Easier collaboration (clear migration order)
- ⚠️ Additional dependency (alembic package)
- ⚠️ Learning curve (Alembic CLI and concepts)

**Implementation**:
```bash
# Create migration
alembic revision --autogenerate -m "add agent tasks table"

# Apply migration
alembic upgrade head

# Rollback migration
alembic downgrade -1
```

---

## ADR-017: LangGraph for Agent Orchestration

**Status**: Accepted (Phase 2)

**Context**:
Agent system requires orchestration of multi-step workflows with conditional logic and state management.

**Decision**:
Use LangGraph as the orchestration layer for agent workflows.

**Rationale**:
- **Graph-based**: Natural fit for complex, non-linear workflows
- **Stateful**: Built-in state management with checkpointing
- **LangChain integration**: Works seamlessly with LangChain tools
- **Debugging**: Visual graph representation aids debugging
- **Flexibility**: Easy to add/modify nodes and edges

**Consequences**:
- ✅ Clear workflow visualization (graph structure)
- ✅ Built-in state management (checkpointing)
- ✅ Easy to extend (add new nodes/edges)
- ⚠️ Learning curve (graph concepts)
- ⚠️ Newer library (smaller community)

---

## ADR-016: Dual Memory Architecture (STM + LTM)

**Status**: Accepted (Phase 1)

**Context**:
Agents need both ephemeral conversation state and long-term knowledge retrieval.

**Decision**:
Implement dual-layer memory: Short-Term Memory (Redis) + Long-Term Memory (PostgreSQL + Qdrant).

**Rationale**:
- **STM**: Fast, ephemeral conversation state with Redis
- **LTM**: Persistent, searchable knowledge with PostgreSQL + vector store
- **Separation**: Different access patterns and lifetimes
- **Performance**: Redis for hot data, PostgreSQL for cold data

**Consequences**:
- ✅ Fast conversation context (Redis)
- ✅ Semantic search (Qdrant)
- ✅ Persistent history (PostgreSQL)
- ⚠️ Complexity (multiple data stores)
- ⚠️ Synchronization (keeping stores consistent)

---

## Previous ADRs (Phase 0-1)

See git history for earlier decisions:
- ADR-001 through ADR-015: Foundation, memory system, agent registry decisions

---

## Decision Template

```markdown
## ADR-XXX: [Title]

**Status**: [Proposed | Accepted | Deprecated | Superseded]

**Context**:
[What is the issue we're trying to solve?]

**Decision**:
[What is the change we're proposing?]

**Rationale**:
[Why this decision? What are the benefits?]

**Consequences**:
- ✅ Positive consequence 1
- ✅ Positive consequence 2
- ⚠️ Negative consequence 1
- ⚠️ Negative consequence 2

**Alternatives Considered**:
- **Alternative 1**: Rejected because...
- **Alternative 2**: Rejected because...
```