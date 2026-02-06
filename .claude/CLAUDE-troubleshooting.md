# Troubleshooting Guide - Commander.ai

**Last Updated**: 2026-01-31

---

## Phase 3B-C: Frontend Issues

### TypeScript Build Error: Missing 'title' Property

**Error**:
```
Type '{ status: TaskStatus; tasks: AgentTask[]; count: number; }' is not assignable to type 'IntrinsicAttributes & KanbanColumnProps'.
  Property 'title' is missing in type '{ status: TaskStatus; tasks: AgentTask[]; count: number; }' but required in type 'KanbanColumnProps'.
```

**Root Cause**:
KanbanColumnProps interface had unused `title` prop that wasn't being passed from parent component.

**Solution**:
```typescript
// Before (WRONG)
interface KanbanColumnProps {
  status: TaskStatus;
  tasks: AgentTask[];
  count: number;
  title: string;  // ❌ Not being passed, not used
}

// After (CORRECT)
interface KanbanColumnProps {
  status: TaskStatus;
  tasks: AgentTask[];
  count: number;
}

// Title is derived from statusConfig instead
const config = statusConfig[status];
<h2>{config.title}</h2>
```

**Prevention**:
- Remove unused props from interfaces
- Use TypeScript strict mode to catch these issues early
- Derive data from configs instead of passing redundant props

---

### Next.js Module Not Found: @/components/ui/*

**Error**:
```
Module not found: Can't resolve '@/components/ui/card'
```

**Root Cause**:
shadcn/ui components not installed or path alias not configured.

**Solution**:
1. Ensure `tsconfig.json` has path alias:
```json
{
  "compilerOptions": {
    "paths": {
      "@/*": ["./*"]
    }
  }
}
```

2. Install shadcn/ui components:
```bash
npx shadcn@latest init
npx shadcn@latest add card badge avatar
```

**Prevention**:
- Always run `npx shadcn@latest init` before adding components
- Verify `components.json` exists in project root

---

## Phase 3A: Backend Issues

### SQLAlchemy Reserved Name: 'metadata'

**Error**:
```
sqlalchemy.exc.InvalidRequestError: Attribute name 'metadata' is reserved when using the Declarative API
```

**Root Cause**:
SQLAlchemy reserves `metadata` attribute for internal table metadata. Cannot use it as column name.

**Solution**:
Use column name mapping to use different Python attribute name:

```python
# WRONG
class AgentTaskModel(Base):
    metadata = Column(JSONB)  # ❌ Conflicts with SQLAlchemy

# CORRECT
class AgentTaskModel(Base):
    meta_data = Column("metadata", JSONB)  # ✅ Python attr ≠ DB column
```

**Files Affected**:
- `backend/models/task_models.py` - SQLAlchemy model
- `backend/repositories/task_repository.py` - Update references to `meta_data`

**Prevention**:
- Avoid Python reserved words and framework-reserved names
- Use column name mapping when DB schema requires reserved words
- Apply consistently across all models

---

### Alembic Migration: Table Already Exists

**Error**:
```
sqlalchemy.exc.ProgrammingError: (psycopg2.errors.DuplicateTable) relation "agent_tasks" already exists
```

**Root Cause**:
Old SQL migration created table before switching to Alembic. Alembic doesn't know about it.

**Solution**:
1. Drop existing table and clear Alembic version:
```sql
DROP TABLE IF EXISTS agent_tasks CASCADE;
DELETE FROM alembic_version;
```

2. Run Alembic migration:
```bash
alembic upgrade head
```

**Prevention**:
- Use Alembic from the start (don't mix raw SQL and Alembic)
- If switching to Alembic, stamp existing schema first:
```bash
alembic stamp head  # Mark current state as migrated
```

---

### Database Column Missing: agent_nickname

**Error**:
```
sqlalchemy.exc.ProgrammingError: (psycopg2.errors.UndefinedColumn) column "agent_nickname" of relation "agent_tasks" does not exist
```

**Root Cause**:
Database schema created by old SQL migration didn't have `agent_nickname` column. Alembic migration includes it, but table wasn't recreated.

**Solution**:
1. Drop table created by old migration:
```sql
DROP TABLE IF EXISTS agent_tasks CASCADE;
```

2. Clear Alembic version tracking:
```sql
DELETE FROM alembic_version;
```

3. Run proper Alembic migration:
```bash
alembic upgrade head
```

**Verification**:
```sql
\d agent_tasks  -- Check table schema
SELECT column_name FROM information_schema.columns WHERE table_name = 'agent_tasks';
```

**Prevention**:
- Always use Alembic for schema changes after initial setup
- Never manually create tables that Alembic should manage
- Verify table schema after migration: `\d table_name` in psql

---

### WebSocket Connection Refused (Frontend)

**Error** (Browser console):
```
WebSocket connection to 'ws://localhost:8000/ws/...' failed: Connection refused
```

**Root Cause**:
Backend server not running or WebSocket endpoint not configured.

**Solution**:
1. Verify backend is running:
```bash
uv run uvicorn backend.api.main:app --reload
```

2. Check WebSocket endpoint exists in `backend/api/main.py`:
```python
@app.websocket("/ws/{user_id}")
async def task_websocket(websocket: WebSocket, user_id: UUID):
    # ...
```

3. Check CORS allows WebSocket:
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

**Prevention**:
- Start backend before frontend
- Use health check endpoint to verify backend is ready
- Check backend logs for WebSocket connection attempts

---

### Task Repository: Pydantic Validation Error

**Error**:
```
pydantic.error_wrappers.ValidationError: 1 validation error for AgentTask
  field required (type=value_error.missing)
```

**Root Cause**:
SQLAlchemy model fields don't match Pydantic model fields.

**Solution**:
Ensure SQLAlchemy and Pydantic models have same fields:

```python
# SQLAlchemy model
class AgentTaskModel(Base):
    __tablename__ = "agent_tasks"
    id = Column(UUID(as_uuid=True), primary_key=True)
    user_id = Column(UUID(as_uuid=True), nullable=False)
    agent_id = Column(String(50), nullable=False)
    agent_nickname = Column(String(50), nullable=False)
    # ... all fields

# Pydantic model
class AgentTask(BaseModel):
    id: UUID
    user_id: UUID
    agent_id: str
    agent_nickname: str
    # ... all fields

    model_config = ConfigDict(from_attributes=True)
```

**Prevention**:
- Keep SQLAlchemy and Pydantic models in sync
- Use `model_validate()` to convert SQLAlchemy → Pydantic
- Add tests to verify model compatibility

---

## Phase 2: Agent System Issues

### LangGraph State Not Persisting

**Symptom**:
Agent loses conversation context between messages.

**Root Cause**:
Checkpointer not configured or thread_id not passed correctly.

**Solution**:
1. Ensure checkpointer is configured:
```python
from langgraph.checkpoint.memory import MemorySaver

checkpointer = MemorySaver()
graph = workflow.compile(checkpointer=checkpointer)
```

2. Pass thread_id in config:
```python
result = await graph.ainvoke(
    state,
    config={"configurable": {"thread_id": str(thread_id)}}
)
```

**Prevention**:
- Always use checkpointer for stateful agents
- Use consistent thread_id for conversation continuity
- Test with multiple messages to verify state persistence

---

## Phase 1: Memory System Issues

### Redis Connection Failed

**Error**:
```
redis.exceptions.ConnectionError: Error 61 connecting to localhost:6379. Connection refused.
```

**Root Cause**:
Redis server not running.

**Solution**:
```bash
# macOS (Homebrew)
brew services start redis

# Linux (systemd)
sudo systemctl start redis

# Docker
docker run -d -p 6379:6379 redis:latest
```

**Verification**:
```bash
redis-cli ping  # Should return "PONG"
```

**Prevention**:
- Add Redis to startup services
- Use Docker Compose for local development
- Add health checks to application startup

---

### Qdrant Collection Not Found

**Error**:
```
qdrant_client.exceptions.UnexpectedResponse: Collection 'semantic_memory' not found
```

**Root Cause**:
Qdrant collection not created before first use.

**Solution**:
1. Create collection in memory service initialization:
```python
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams

client = QdrantClient(host="localhost", port=6333)

# Create collection if not exists
collections = client.get_collections().collections
if "semantic_memory" not in [c.name for c in collections]:
    client.create_collection(
        collection_name="semantic_memory",
        vectors_config=VectorParams(size=1536, distance=Distance.COSINE),
    )
```

**Prevention**:
- Create collections during service initialization
- Use migration scripts for collection setup
- Add existence checks before operations

---

## Common Development Issues

### Port Already in Use

**Error**:
```
Error: listen EADDRINUSE: address already in use :::8000
```

**Solution**:
```bash
# Find process using port
lsof -i :8000

# Kill process
kill -9 <PID>

# Or use different port
uvicorn backend.api.main:app --port 8001
```

---

### Poetry/UV Dependency Conflicts

**Error**:
```
Unable to find installation candidates for package_name
```

**Solution**:
```bash
# Clear cache and reinstall
uv cache clean
rm -rf .venv
uv sync

# Or use specific version
uv add "package_name>=1.0.0,<2.0.0"
```

---

### Frontend npm Install Failures

**Error**:
```
npm ERR! code ERESOLVE
npm ERR! ERESOLVE unable to resolve dependency tree
```

**Solution**:
```bash
# Clear npm cache
npm cache clean --force

# Delete node_modules and lock file
rm -rf node_modules package-lock.json

# Reinstall
npm install

# Or use --legacy-peer-deps if needed
npm install --legacy-peer-deps
```

---

## Debugging Tips

### Backend Debugging

**Enable SQL logging**:
```python
# backend/core/config.py
DATABASE_URL = "postgresql+asyncpg://...?echo=true"
```

**Enable verbose logging**:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

**Test API endpoints**:
```bash
# Create task
curl -X POST http://localhost:8000/api/tasks \
  -H "Content-Type: application/json" \
  -d '{"user_id": "...", "agent_id": "agent_a", ...}'

# List tasks
curl "http://localhost:8000/api/tasks?user_id=..."
```

### Frontend Debugging

**Check WebSocket in browser console**:
```javascript
// Open browser console (F12)
// WebSocket logs will show connection status
```

**Enable React DevTools**:
- Install React DevTools browser extension
- Inspect component state and props

**Check Zustand state**:
```typescript
// Add to store for debugging
useTaskStore.subscribe(console.log)
```

---

## Health Check Checklist

Before reporting an issue:

- [ ] Backend server running (`uvicorn backend.api.main:app --reload`)
- [ ] Frontend dev server running (`npm run dev`)
- [ ] PostgreSQL running and accessible
- [ ] Redis running (`redis-cli ping`)
- [ ] Qdrant running (`curl http://localhost:6333`)
- [ ] Database migrations applied (`alembic upgrade head`)
- [ ] Dependencies installed (`uv sync`, `npm install`)
- [ ] Environment variables set (`.env` file)
- [ ] No port conflicts (`lsof -i :8000`, `lsof -i :3000`)

---

## Quick Reference Commands

### Backend
```bash
# Start server
uv run uvicorn backend.api.main:app --reload

# Run tests
uv run pytest tests/ -v

# Database migration
alembic upgrade head

# Redis check
redis-cli ping
```

### Frontend
```bash
# Start dev server
npm run dev

# Build production
npm run build

# Type check
npx tsc --noEmit

# Lint
npm run lint
```

### Docker (if using)
```bash
# Start all services
docker-compose up -d

# Check logs
docker-compose logs -f

# Stop all services
docker-compose down
```
