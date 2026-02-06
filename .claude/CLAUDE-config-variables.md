# Configuration Variables - Commander.ai

**Last Updated**: 2026-01-31

---

## Backend Configuration

### Environment Variables

**File**: `backend/core/config.py`

```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Application
    app_name: str = "commander.ai"
    debug: bool = False

    # Database
    database_url: str = "postgresql+asyncpg://user:password@localhost:5432/commander_ai"

    # Redis (Short-Term Memory)
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_db: int = 0
    redis_password: str | None = None

    # Qdrant (Vector Store)
    qdrant_host: str = "localhost"
    qdrant_port: int = 6333
    qdrant_collection: str = "semantic_memory"

    # LLM
    openai_api_key: str
    anthropic_api_key: str | None = None

    # MVP User (Phase 3)
    mvp_user_id: str = "00000000-0000-0000-0000-000000000001"

    # CORS
    cors_origins: list[str] = ["http://localhost:3000"]

    # API
    api_prefix: str = "/api"

    class Config:
        env_file = ".env"
```

### .env File Template

```bash
# Application
APP_NAME=commander.ai
DEBUG=True

# Database
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/commander_ai

# Redis
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
REDIS_PASSWORD=

# Qdrant
QDRANT_HOST=localhost
QDRANT_PORT=6333
QDRANT_COLLECTION=semantic_memory

# LLM API Keys
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...

# MVP User
MVP_USER_ID=00000000-0000-0000-0000-000000000001

# CORS
CORS_ORIGINS=["http://localhost:3000"]
```

---

## Frontend Configuration

### Environment Variables

**File**: `frontend/.env.local`

```bash
# Backend API
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_WS_URL=ws://localhost:8000

# MVP User
NEXT_PUBLIC_MVP_USER_ID=00000000-0000-0000-0000-000000000001

# Feature Flags (future)
NEXT_PUBLIC_ENABLE_ANALYTICS=false
NEXT_PUBLIC_ENABLE_DEBUG=true
```

### Next.js Configuration

**File**: `frontend/next.config.ts`

```typescript
import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Strict mode for better development experience
  reactStrictMode: true,

  // Disable TypeScript errors blocking build (for CI/CD)
  typescript: {
    ignoreBuildErrors: false,
  },

  // Disable ESLint errors blocking build
  eslint: {
    ignoreDuringBuilds: false,
  },

  // Output standalone for Docker
  output: "standalone",
};

export default nextConfig;
```

### TypeScript Configuration

**File**: `frontend/tsconfig.json`

```json
{
  "compilerOptions": {
    "target": "ES2017",
    "lib": ["dom", "dom.iterable", "esnext"],
    "allowJs": true,
    "skipLibCheck": true,
    "strict": true,
    "noEmit": true,
    "esModuleInterop": true,
    "module": "esnext",
    "moduleResolution": "bundler",
    "resolveJsonModule": true,
    "isolatedModules": true,
    "jsx": "preserve",
    "incremental": true,
    "plugins": [
      {
        "name": "next"
      }
    ],
    "paths": {
      "@/*": ["./*"]
    }
  },
  "include": ["next-env.d.ts", "**/*.ts", "**/*.tsx", ".next/types/**/*.ts"],
  "exclude": ["node_modules"]
}
```

### Tailwind Configuration

**File**: `frontend/tailwind.config.ts`

```typescript
import type { Config } from "tailwindcss";

export default {
  darkMode: ["class"],
  content: [
    "./pages/**/*.{ts,tsx}",
    "./components/**/*.{ts,tsx}",
    "./app/**/*.{ts,tsx}",
    "./src/**/*.{ts,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        border: "hsl(var(--border))",
        input: "hsl(var(--input))",
        ring: "hsl(var(--ring))",
        background: "hsl(var(--background))",
        foreground: "hsl(var(--foreground))",
        primary: {
          DEFAULT: "hsl(var(--primary))",
          foreground: "hsl(var(--primary-foreground))",
        },
        secondary: {
          DEFAULT: "hsl(var(--secondary))",
          foreground: "hsl(var(--secondary-foreground))",
        },
        destructive: {
          DEFAULT: "hsl(var(--destructive))",
          foreground: "hsl(var(--destructive-foreground))",
        },
        muted: {
          DEFAULT: "hsl(var(--muted))",
          foreground: "hsl(var(--muted-foreground))",
        },
        accent: {
          DEFAULT: "hsl(var(--accent))",
          foreground: "hsl(var(--accent-foreground))",
        },
        popover: {
          DEFAULT: "hsl(var(--popover))",
          foreground: "hsl(var(--popover-foreground))",
        },
        card: {
          DEFAULT: "hsl(var(--card))",
          foreground: "hsl(var(--card-foreground))",
        },
      },
      borderRadius: {
        lg: "var(--radius)",
        md: "calc(var(--radius) - 2px)",
        sm: "calc(var(--radius) - 4px)",
      },
    },
  },
  plugins: [require("tailwindcss-animate")],
} satisfies Config;
```

---

## Database Configuration

### PostgreSQL Settings

**Connection String Format**:
```
postgresql+asyncpg://user:password@host:port/database
```

**Recommended Settings** (for development):
```sql
-- Max connections
max_connections = 100

-- Shared buffers (25% of RAM)
shared_buffers = 256MB

-- Work memory
work_mem = 4MB

-- Maintenance work memory
maintenance_work_mem = 64MB
```

### Alembic Configuration

**File**: `alembic.ini`

```ini
[alembic]
script_location = migrations
file_template = %%(year)d%%(month).2d%%(day).2d_%%(hour).2d%%(minute).2d_%%(rev)s_%%(slug)s
truncate_slug_length = 40

sqlalchemy.url = postgresql+asyncpg://postgres:postgres@localhost:5432/commander_ai

[loggers]
keys = root,sqlalchemy,alembic

[handlers]
keys = console

[formatters]
keys = generic

[logger_root]
level = WARN
handlers = console
qualname =

[logger_sqlalchemy]
level = WARN
handlers =
qualname = sqlalchemy.engine

[logger_alembic]
level = INFO
handlers =
qualname = alembic

[handler_console]
class = StreamHandler
args = (sys.stderr,)
level = NOTSET
formatter = generic

[formatter_generic]
format = %(levelname)-5.5s [%(name)s] %(message)s
datefmt = %H:%M:%S
```

---

## Redis Configuration

### Connection Settings

**Python Client**:
```python
from redis.asyncio import Redis

redis_client = Redis(
    host="localhost",
    port=6379,
    db=0,
    decode_responses=True,  # Auto-decode bytes to strings
    socket_timeout=5,
    socket_connect_timeout=5,
)
```

### Key Naming Convention

```
checkpoint:{thread_id}:{checkpoint_id}  # Conversation checkpoints
stm:{user_id}:{thread_id}               # Short-term memory
cache:{resource_type}:{resource_id}     # Generic cache
```

### TTL Settings

```python
CHECKPOINT_TTL = 3600      # 1 hour
STM_TTL = 86400            # 24 hours
CACHE_TTL = 300            # 5 minutes
```

---

## Qdrant Configuration

### Collection Settings

**Semantic Memory Collection**:
```python
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams

client = QdrantClient(host="localhost", port=6333)

client.create_collection(
    collection_name="semantic_memory",
    vectors_config=VectorParams(
        size=1536,              # OpenAI text-embedding-ada-002
        distance=Distance.COSINE,
    ),
)
```

### Vector Dimensions by Model

```python
EMBEDDING_DIMENSIONS = {
    "text-embedding-ada-002": 1536,
    "text-embedding-3-small": 1536,
    "text-embedding-3-large": 3072,
}
```

---

## WebSocket Configuration

### Backend (FastAPI)

**File**: `backend/api/main.py`

```python
from fastapi import WebSocket

@app.websocket("/ws/{user_id}")
async def task_websocket(websocket: WebSocket, user_id: UUID):
    ws_manager = get_ws_manager()
    await ws_manager.connect(websocket, user_id)

    try:
        while True:
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        ws_manager.disconnect(user_id)
```

**Settings**:
- **Heartbeat interval**: 30 seconds
- **Max message size**: 10MB (default)
- **Connection timeout**: No timeout (keep alive)

### Frontend

**File**: `frontend/lib/websocket.ts`

```typescript
const WS_CONFIG = {
  url: process.env.NEXT_PUBLIC_WS_URL || "ws://localhost:8000",
  heartbeatInterval: 30000,      // 30 seconds
  reconnectDelay: 1000,          // 1 second base delay
  maxReconnectAttempts: 5,       // Max retry attempts
  reconnectBackoffFactor: 2,     // Exponential backoff
};
```

---

## API Configuration

### FastAPI CORS

**File**: `backend/api/main.py`

```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",    # Next.js dev
        "http://localhost:3001",    # Alternative port
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### API Endpoints

```
# Tasks
GET    /api/tasks?user_id={uuid}              # List tasks
POST   /api/tasks                             # Create task
GET    /api/tasks/{task_id}                   # Get task
PATCH  /api/tasks/{task_id}                   # Update task

# WebSocket
WS     /ws/{user_id}                          # Real-time updates

# Health
GET    /health                                # Health check
```

---

## Development vs Production

### Development Settings

**Backend**:
```python
debug: bool = True
reload: bool = True  # uvicorn --reload
log_level: str = "DEBUG"
```

**Frontend**:
```bash
NODE_ENV=development
NEXT_PUBLIC_ENABLE_DEBUG=true
```

### Production Settings

**Backend**:
```python
debug: bool = False
reload: bool = False
log_level: str = "INFO"
workers: int = 4  # uvicorn --workers 4
```

**Frontend**:
```bash
NODE_ENV=production
NEXT_PUBLIC_ENABLE_DEBUG=false
npm run build
npm run start
```

---

## Port Assignments

```
3000    Frontend (Next.js dev server)
8000    Backend API (FastAPI/uvicorn)
5432    PostgreSQL
6379    Redis
6333    Qdrant
```

---

## MVP Hardcoded Values

### User ID
```
00000000-0000-0000-0000-000000000001
```

**Used in**:
- Backend settings (`backend/core/config.py`)
- Frontend constants (`frontend/components/kanban/kanban-board.tsx`)
- API requests
- WebSocket connections

**Migration Path**:
Replace with proper authentication system in Phase 4+.

---

## Logging Configuration

### Backend (Python)

```python
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("app.log"),
        logging.StreamHandler(),
    ]
)
```

### Frontend (Browser)

```typescript
// lib/logger.ts
const logger = {
  debug: (...args: any[]) => {
    if (process.env.NEXT_PUBLIC_ENABLE_DEBUG === "true") {
      console.log("[DEBUG]", ...args);
    }
  },
  info: (...args: any[]) => console.log("[INFO]", ...args),
  warn: (...args: any[]) => console.warn("[WARN]", ...args),
  error: (...args: any[]) => console.error("[ERROR]", ...args),
};
```

---

## Quick Reference

### Start All Services

```bash
# PostgreSQL
pg_ctl -D /usr/local/var/postgres start

# Redis
brew services start redis

# Qdrant
docker run -p 6333:6333 qdrant/qdrant

# Backend
uv run uvicorn backend.api.main:app --reload

# Frontend
cd frontend && npm run dev
```

### Environment Setup

```bash
# Backend
cp .env.example .env
# Edit .env with your values
uv sync

# Frontend
cp frontend/.env.example frontend/.env.local
# Edit .env.local with your values
cd frontend && npm install
```