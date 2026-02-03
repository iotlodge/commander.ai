# commander.ai

An interactive multi-agent AI system for delegating work through natural language commands. Chat with specialized AI agents by name, role, or context using @mentions or natural greetings.

![Commander.ai UI](images/architecture.png)

### Cache, Short, and Long-term Memory
![Commander.ai UI](images/memory.png)

## Overview

**commander.ai** enables seamless collaboration with AI agents through an intuitive Kanban-style interface. Submit commands via natural language, mention specific agents, and watch tasks progress in real-time as agents work together to complete your requests.

## Screenshots

### Main Interface
Real-time Kanban board with task tracking across all agent workflows:

![Commander.ai Landing Page](images/landing-page.png)

### Agent Graph Visualization
Interactive workflow visualization showing agent decision trees and execution paths:

![Agent Graph Visualization](images/agent-graph.png)

### Agent Selection
Intelligent autocomplete with agent specializations - just click or type `@`:

![Agent Autocomplete](images/agent-autocomplete.png)

Key Features

✅ **Natural Language Commands** - Type commands like `@bob research quantum computing` or `hello sue, review this policy`

✅ **Real-Time Task Tracking** - Watch tasks move through stages (Queued → In Progress → Tool Call → Completed/Failed)

✅ **Agent Specialization** - Delegate to specialized agents:
- **@bob** (Research Specialist) - Deep research and information synthesis
- **@sue** (Compliance Specialist) - Regulatory compliance and policy adherence
- **@rex** (Data Analyst) - Data analysis and visualization
- **@leo** (Orchestrator) - Workflow coordination and task delegation

✅ **Live WebSocket Updates** - UI updates automatically without page refreshes

✅ **Task Management** - Purge completed/failed tasks with one click

## Current Status

**Phase 4A Completed** - End-to-end command input and task execution working

**What's Working:**
- ✅ Backend task management API with PostgreSQL
- ✅ WebSocket server for real-time updates
- ✅ Command parsing with @mention detection
- ✅ Dark-themed Kanban board UI with optimized column widths
- ✅ Background agent execution
- ✅ Task purge functionality (completed/failed)
- ✅ Real-time UI updates via WebSocket
- ✅ Agent graph visualization with interactive workflow display
- ✅ Intelligent agent autocomplete (works with or without typing @)
- ✅ Comprehensive button controls (Purge, Batch Tasks, View Graphs)

**In Development:**
- ⏳ Memory system (Short-Term + Long-Term)
- ⏳ Advanced agent logic with LLM integration
- ⏳ User authentication
- ⏳ Command history

## Tech Stack

### Backend
- **Python 3.12+** - Modern async/await support
- **FastAPI** - High-performance async web framework
- **PostgreSQL** - Task and conversation storage
- **SQLAlchemy (async)** - ORM with async support
- **LangGraph** - Agent orchestration framework
- **LangChain** - LLM integration
- **WebSockets** - Real-time event broadcasting

### Frontend
- **Next.js 14** - React framework with App Router
- **TypeScript** - Type-safe development
- **Tailwind CSS** - Utility-first styling
- **shadcn/ui** - High-quality component library
- **Zustand** - Lightweight state management
- **WebSocket Client** - Real-time updates

### Infrastructure
- **Docker Compose** - PostgreSQL, Redis, Qdrant
- **Redis** - Short-term memory cache (planned)
- **Qdrant** - Vector store for semantic search (planned)

## Installation

### Prerequisites

- Python 3.12+
- Node.js 18+
- PostgreSQL 14+ (or use Docker Compose)
- Redis (optional, via Docker Compose)
- Qdrant (optional, via Docker Compose)

### Quick Start

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/commander.ai.git
   cd commander.ai
   ```

2. **Set up environment variables**
   ```bash
   cp .env.example .env
   # Edit .env and add your API keys
   ```

3. **Start infrastructure (PostgreSQL, Redis, Qdrant)**
   ```bash
   docker-compose up -d
   ```

4. **Install Python dependencies**
   ```bash
   # Using uv (recommended)
   uv sync

   # Or using pip
   pip install -r requirements.txt
   ```

5. **Run database migrations**
   ```bash
   alembic upgrade head
   ```

6. **Start the backend**
   ```bash
   python -m uvicorn backend.api.main:app --reload
   ```

7. **Install frontend dependencies**
   ```bash
   cd frontend
   npm install
   ```

8. **Start the frontend**
   ```bash
   npm run dev
   ```

9. **Open your browser**
   ```
   http://localhost:3000
   ```

## Usage

### Submitting Commands

Type commands in the input box at the bottom of the screen:

**Direct Agent Mention:**
```
@bob research the latest AI safety developments
@sue check compliance for GDPR policy
@rex analyze this dataset
@alice create collection research_papers
@alice load ~/Documents/paper.pdf into research_papers
@alice search web for machine learning trends into ml_research
@alice search research_papers for "neural networks"
```

**Natural Greeting:**
```
hello bob, find information about LangGraph
hey sue, review this contract
```

**Complex Tasks (routed to Leo orchestrator):**
```
analyze sales data and create a compliance report
research market trends and summarize findings
```

### Keyboard Shortcuts

- `Cmd/Ctrl + Enter` - Submit command
- `@` - Trigger agent autocomplete

### Task Management

- **Purge Completed** - Remove all completed tasks
- **Purge Failed** - Remove all failed tasks
- **Real-time Updates** - Watch tasks progress automatically

## Project Structure

```
commander.ai/
├── backend/                  # Python FastAPI backend
│   ├── agents/              # Agent implementations
│   │   ├── base/           # Base agent interface and registry
│   │   ├── parent/         # Orchestrator agent (Leo)
│   │   ├── research/       # Research agent (Bob)
│   │   ├── compliance/     # Compliance agent (Sue)
│   │   └── data/           # Data analysis agent (Rex)
│   ├── api/                # FastAPI routes and WebSocket
│   │   ├── routes/        # REST API endpoints
│   │   ├── main.py        # FastAPI application
│   │   └── websocket.py   # WebSocket manager
│   ├── core/              # Core business logic
│   │   ├── command_parser.py    # @mention and greeting parsing
│   │   ├── command_executor.py  # Background task execution
│   │   └── config.py            # Settings and configuration
│   ├── models/            # Pydantic models
│   └── repositories/      # Database access layer
├── frontend/              # Next.js 14 frontend
│   ├── app/              # Next.js App Router
│   ├── components/       # React components
│   │   ├── command/     # Command input components
│   │   ├── kanban/      # Kanban board components
│   │   └── ui/          # shadcn/ui components
│   ├── hooks/           # React hooks
│   ├── lib/             # Utilities and stores
│   │   ├── store.ts         # Zustand state management
│   │   ├── types.ts         # TypeScript types
│   │   └── websocket.ts     # WebSocket client
│   └── styles/          # Global styles
├── migrations/          # Database migrations
├── docker-compose.yml  # Infrastructure setup
├── .env.example       # Environment template
└── PLAN.md           # Full project plan
```

## Configuration

Key environment variables in `.env`:

```bash
# Database
DATABASE_URL=postgresql+asyncpg://commander:changeme@localhost:5432/commander_ai

# Redis (Short-Term Memory)
REDIS_URL=redis://localhost:6379/0

# Qdrant (Vector Store)
QDRANT_URL=http://localhost:6333

# API Keys
OPENAI_API_KEY=sk-...           # Required for embeddings and LLM
ANTHROPIC_API_KEY=sk-ant-...    # Optional: for Claude models
TAVILY_API_KEY=tvly-...         # Required for @alice web search

# Application
APP_SECRET_KEY=dev-secret-key-change-in-production
APP_ENV=development
APP_DEBUG=true
```

## Architecture

### Command Flow

```
User Input
    ↓
Command Parser (@mention detection)
    ↓
Task Created (PostgreSQL)
    ↓
WebSocket Broadcast (task_status_changed)
    ↓
Background Agent Execution
    ↓
Task Updates (in_progress → tool_call → completed)
    ↓
WebSocket Broadcasts (real-time UI updates)
```

### Agent System

- **BaseAgent** - Common interface for all agents
- **LangGraph Integration** - Agents run as compiled graphs
- **TaskProgressCallback** - WebSocket event emission
- **AgentRegistry** - Centralized agent lookup

### Memory System (Planned)

- **Short-Term Memory (STM)** - Redis + LangGraph checkpointer
- **Long-Term Memory (LTM)** - PostgreSQL + Vector store
- **MemoryService** - Coordinates STM and LTM access

## Development

### Running Tests

```bash
# Backend tests
pytest

# Frontend tests
cd frontend
npm test
```

### Code Quality

```bash
# Python linting
ruff check .
ruff check --fix .

# Type checking
mypy backend/

# Formatting
black backend/
```

### Database Migrations

```bash
# Create new migration
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head

# Rollback migration
alembic downgrade -1
```

## Roadmap

See [PLAN.md](PLAN.md) for the complete development plan.

**Next Phases:**
1. **Phase 4B** - Basic Agent Logic (LLM integration, Tavily search)
2. **Phase 5** - Memory System (STM/LTM implementation)
3. **Phase 6** - User Authentication (multi-user support)
4. **Phase 7** - Production Readiness (monitoring, testing, deployment)

## Contributing

This is a personal project, but suggestions and feedback are welcome!

## License

[Add your license here]

## Acknowledgments

- Built with [LangGraph](https://github.com/langchain-ai/langgraph)
- UI components from [shadcn/ui](https://ui.shadcn.com/)
- Icons from [Lucide](https://lucide.dev/)

---

**Status**: 🚧 Active Development - Phase 4A Complete

For detailed implementation plans and decisions, see:
- [PLAN.md](PLAN.md) - Complete project roadmap
- [AGENTS.md](AGENTS.md) - Agent specifications
- [CLAUDE-patterns.md](CLAUDE-patterns.md) - Code patterns and conventions
