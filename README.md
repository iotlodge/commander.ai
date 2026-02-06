  # Commander.ai

> **Mission Control for your AI team.** Watch specialized agents collaborate in real-time, executing complex tasks with complete visibility and maximum control.

[![Python](https://img.shields.io/badge/Python-3.12+-blue.svg)](https://www.python.org/)
[![Next.js](https://img.shields.io/badge/Next.js-14-black.svg)](https://nextjs.org/)
[![LangGraph](https://img.shields.io/badge/LangGraph-Latest-green.svg)](https://github.com/langchain-ai/langgraph)
[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](LICENSE)

---

## 🎯 Why Commander.ai?

**Single AI assistants give you one perspective. Commander.ai gives you a specialized team.**

Unlike chatbots that force you to wait and guess, Commander.ai shows you **exactly what's happening** as your AI team works:

- 🔴 **Live Agent Activity** - Watch tokens flow and LLM calls execute in real-time
- ⚡ **One-Click Commands** - Quick Actions panel for instant delegation
- 📊 **Complete Visibility** - See every node, tool call, and decision
- 🎯 **Maximum Control** - Clear completed tasks, zoom agent graphs, filter by agent
- 🚀 **True Parallelization** - Multiple agents working simultaneously

**This isn't a chat interface with agents bolted on. It's Mission Control.**

![Commander.ai Mission Control](images/new_landing_page.png)
*Mission Control: Real-time visibility into your AI team*

---

## 🕹️ Mission Control Interface

### Three-Panel Command Center

**Left Panel: AI Agents**
- 7 specialized agents with real-time metrics
- Live token counts, LLM calls, tool usage
- Current processing node ("→ reasoning...")
- Active/queued task indicators
- System activity dashboard

**Center Panel: Conversation Stream**
- Chronological command/response flow
- Expandable metrics & execution flow
- Inline agent graph visualization with zoom
- Smooth, stable rendering (no animations to distract)

**Right Panel: Quick Actions**
- One-click pre-configured commands
- Organized by agent specialty
- Auto-fills command input
- Examples:
  - 📄 Alice: "List all documents", "Archive old files"
  - 🔍 Bob: "Latest AI news", "Market research"
  - 📊 Rex: "Analyze data", "Generate report"

![Live Agent Metrics](images/actve_agent_updates.png)
*Agent tiles showing real-time token counts, LLM calls, and current processing node*

![Multi-Agent Conversation Flow](images/mult-conversation_with_flow.png)
*Multiple agents working in parallel with complete execution visibility*

### Real-Time Visibility

**Watch Your Agents Work:**
```
@kai (Reflexion Specialist)
🟢 1 active
1,234 tok | 3 LLM | 2 tools | → reasoning
```

Every agent tile updates live as they:
- Consume tokens (green counter)
- Make LLM calls (purple counter)
- Use tools (yellow counter)
- Progress through workflow nodes (blue text)

**Completed Task Tracking:**
- "Done" counter in System Activity
- "Clear Completed" button (only shows when needed)
- Confirmation before clearing
- Keeps conversation focused on active work

![Metrics & Flow](images/sequence_and_metrics.png)
*Expandable metrics showing tokens, LLM calls, tool calls, duration, and step-by-step execution timeline*

---

## 🤖 Meet Your AI Team

### 💬 @chat - Interactive Chat Assistant
Your conversational interface with live web search.
- GPT-4o-mini for natural conversations
- **Automatic web search** when you ask current questions
- Agentic tool execution loop
- Context-aware responses

### 🔬 @bob - Research Specialist
Deep research with multi-source synthesis.
- Tavily web search + LLM analysis
- Automatic compliance flagging
- 24h cache for general queries, 1h for news
- *Your investigative journalist*

### ⚖️ @sue - Compliance Specialist
Keep your projects legally sound.
- GDPR, HIPAA, data protection review
- Regulatory compliance analysis
- Risk assessment and policy checks
- *Your legal safeguard*

### 📊 @rex - Data Analyst
Turn numbers into insights.
- Statistical analysis and visualization
- Pattern detection and trend analysis
- Matplotlib chart generation
- *Your data scientist*

### 📚 @alice - Document Manager
Semantic document search and storage.
- PDF processing with OCR
- **Web search → persistent storage**
- Vector embeddings via Qdrant
- Collection management (create/delete/search)
- *Your librarian with superpowers*

### ✨ @maya - Reflection Specialist
Quality control through critique.
- Content review with severity ratings
- Issue identification (critical/important/minor)
- Generates improved versions
- Quality scoring (0-1.0)
- *Your editor and QA team*

### 🔄 @kai - Reflexion Specialist
Iterative reasoning through self-reflection.
- Up to 3 self-improvement cycles
- Shows reasoning evolution
- Self-critique and refinement
- *Your deep thinker*

![Kai in Action](images/kai1.png)
*@kai executing reflexive reasoning with full execution trace*

---

## 🚀 Quick Start

### One-Command Setup

```bash
# 1. Clone and configure
git clone https://github.com/iotlodge/commander.ai.git
cd commander.ai
cp .env.example .env
# Add your OPENAI_API_KEY and TAVILY_API_KEY to .env

# 2. Start infrastructure (PostgreSQL, Redis, Qdrant)
docker-compose up -d

# 3. Backend
uv sync                    # or: pip install -r requirements.txt
alembic upgrade head
python -m uvicorn backend.api.main:app --reload

# 4. Frontend (new terminal)
cd frontend && npm install && npm run dev

# 5. Open Mission Control
open http://localhost:3000
```

**That's it.** You're in the command center.

---

## 💬 Command Examples

### Natural Delegation

```bash
# Quick questions with live web search
@chat what's the latest news about AI safety?

# Deep research
@bob research quantum computing breakthroughs in 2026

# Compliance review
@sue review this privacy policy for GDPR compliance

# Data analysis
@rex analyze sales trends from last quarter

# Document management
@alice search web for "climate change reports" into research_collection

# Quality assurance
@maya review this code for potential issues

# Complex problem solving
@kai solve: how can we reduce API latency by 50%?
```

### Quick Actions (One-Click)

Click any Quick Action button to auto-fill commands:
- **Alice**: "List all documents" → `@alice list all documents in the system`
- **Bob**: "Latest AI news" → `@bob what's the latest news in AI?`
- **Rex**: "Generate report" → `@rex generate a detailed analytical report on`

Edit the command, add context, hit Enter. Done.

---

## 🏗️ Architecture

### Tech Stack

**Backend (Python 3.12+)**
- **LangGraph** - Agent workflow orchestration
- **FastAPI** - High-performance async API
- **PostgreSQL** - Persistent storage with pgvector
- **Redis** - Hot memory layer (sessions)
- **Qdrant** - Vector database (semantic search)
- **OpenAI** - GPT-4o-mini + ada-002 embeddings
- **Tavily** - Web search API

**Frontend (TypeScript)**
- **Next.js 14** - App Router with React Server Components
- **Tailwind CSS** - Utility-first styling
- **shadcn/ui** - Accessible component library
- **Zustand** - Lightweight state management
- **WebSocket** - Real-time agent updates

### Three-Tier Memory System

```
┌─────────────┐
│ Redis       │ ← Hot Layer (active conversations)
├─────────────┤
│ PostgreSQL  │ ← Warm Layer (conversation history)
├─────────────┤
│ Qdrant      │ ← Smart Layer (semantic search)
└─────────────┘
```

Every conversation persists. Every insight is searchable. Agents can recall past knowledge and build on previous work.

### Project Structure

```
commander.ai/
├── backend/
│   ├── agents/
│   │   ├── base/              # Agent interface & registry
│   │   └── specialized/       # 7 specialist agents
│   │       ├── agent_a/       # @bob (Research)
│   │       ├── agent_b/       # @sue (Compliance)
│   │       ├── agent_c/       # @rex (Data Analysis)
│   │       ├── agent_d/       # @alice (Documents)
│   │       ├── agent_e/       # @maya (Reflection)
│   │       ├── agent_f/       # @kai (Reflexion)
│   │       └── agent_g/       # @chat (Chat Assistant)
│   ├── memory/               # Document store & embeddings
│   ├── tools/                # Web search, data analysis, PDF processing
│   ├── core/                 # Config, dependencies, tracking
│   └── api/                  # FastAPI + WebSocket
└── frontend/
    ├── components/
    │   └── mission-control/  # Three-panel UI
    │       ├── agent-team-panel.tsx      # Live agent metrics
    │       ├── conversation-stream.tsx   # Command/response flow
    │       ├── quick-actions-panel.tsx   # One-click commands
    │       ├── inline-execution-flow.tsx # Metrics timeline
    │       └── inline-agent-graph.tsx    # Workflow visualization
    ├── lib/                  # Store, hooks, types
    └── app/                  # Next.js routes
```

---

## 📊 Execution Metrics & Observability

### What You See in Real-Time

**Agent Tiles (Live Updates):**
- Token consumption as agents work
- LLM call counts
- Tool usage (web search, data analysis, etc.)
- Current workflow node
- Active/queued task status

**Metrics & Flow (Per Task):**
```
Total Tokens: 1,234
├─ 800 prompt + 434 completion

LLM Calls: 3
Tool Calls: 2
Duration: 12.4s

Execution Flow (5 steps):
├─ 1. parse_input         [210ms]
├─ 2. fetch_web           [8.2s] 856 tokens
├─ 3. chunk_and_embed     [2.1s] 362 tokens
├─ 4. store_chunks        [890ms]
└─ 5. format_response     [45ms]
```

**System Activity Dashboard:**
```
┌─────────┬─────────┬─────────┐
│ Active  │ Queued  │  Done   │
│   2     │   1     │   5     │
└─────────┴─────────┴─────────┘

[✓ Clear Completed (5)]
```

**Complete visibility.** No black boxes. See exactly what's happening.

---

## 🔧 Adding a New Agent

Commander.ai is designed for extensibility. Add your own specialist in 5 steps:

### 1. Create Agent Directory
```bash
mkdir -p backend/agents/specialized/agent_h
cd backend/agents/specialized/agent_h
touch __init__.py graph.py state.py nodes.py
```

### 2. Define State
```python
# state.py
from typing import TypedDict

class MyAgentState(TypedDict):
    query: str
    user_id: str
    results: list[str]
    error: str | None
```

### 3. Implement Nodes
```python
# nodes.py
async def process_query_node(state: MyAgentState) -> dict:
    # Your logic here
    return {**state, "results": ["processed"]}
```

### 4. Build Graph
```python
# graph.py
from langgraph.graph import StateGraph, END
from backend.agents.base.agent_interface import BaseAgent, AgentMetadata

class MyAgent(BaseAgent):
    def __init__(self):
        super().__init__(AgentMetadata(
            id="agent_h",
            nickname="vision",  # @vision in UI
            specialization="Image Analysis",
            description="Analyzes images and extracts insights"
        ))

    def create_graph(self) -> StateGraph:
        graph = StateGraph(MyAgentState)
        graph.add_node("process", process_query_node)
        graph.set_entry_point("process")
        graph.add_edge("process", END)
        return graph
```

### 5. Register
```python
# backend/agents/base/agent_registry.py
from backend.agents.specialized.agent_h.graph import MyAgent

_registry["agent_h"] = MyAgent()
```

**Done.** Your agent appears in Mission Control with live metrics, Quick Actions integration, and full observability.

---

## ⚙️ Configuration

### Required Environment Variables

```bash
# Core (Required)
OPENAI_API_KEY=sk-...      # GPT-4o-mini + embeddings
TAVILY_API_KEY=tvly-...    # Web search

# Database (Auto-configured by docker-compose)
DATABASE_URL=postgresql+asyncpg://commander:changeme@localhost:5432/commander_ai
REDIS_URL=redis://localhost:6379/0
QDRANT_URL=http://localhost:6333

# Optional Tuning
WEB_CACHE_TTL_HOURS=24          # General content cache
WEB_CACHE_NEWS_TTL_HOURS=1       # News content cache
TAVILY_RATE_LIMIT_PER_MINUTE=60  # API rate limit
```

### Docker Services

```bash
docker-compose up -d
```

Starts PostgreSQL 16 (with pgvector), Redis 7, and Qdrant with health checks and auto-restart.

---

## 🚦 Production Status

**✅ v2.0 - Mission Control** (February 2026)

**Core Features:**
- ✅ **Mission Control UI** - Three-panel interface with real-time metrics
- ✅ **7 Specialized Agents** - Chat, research, compliance, data, documents, reflection, reflexion
- ✅ **Quick Actions Panel** - One-click command delegation
- ✅ **Live Agent Metrics** - Token counts, LLM calls, tool usage, current node
- ✅ **Execution Flow Tracking** - Complete observability into every step
- ✅ **Graph Visualization** - Agent workflow diagrams with zoom controls
- ✅ **Completed Task Management** - Track and clear finished work
- ✅ **Three-Tier Memory** - Redis/PostgreSQL/Qdrant
- ✅ **Web Search Cache** - 24h general, 1h news TTL
- ✅ **JWT Authentication** - Production-ready security (94% test coverage)
- ✅ **DocumentStore Singleton** - Prevents connection pool exhaustion
- ✅ **Agentic Tool Execution** - Chat agent executes web searches automatically

**What's New in v2.0:**
- 🎨 **Complete UI Redesign** - From Kanban to Mission Control
- 🔴 **Real-Time Agent Metrics** - Watch your team work live
- ⚡ **Quick Actions** - 25+ pre-configured commands
- 📊 **Enhanced Metrics** - Tokens, calls, duration, timeline
- 🔍 **Graph Zoom** - Explore agent workflows in detail
- 🗑️ **Removed Kanban** - Focused, purpose-built interface

**Roadmap:**
- ⏳ Vision/image analysis agent (in progress)
- ⏳ CLI interface for terminal workflows
- 📅 Code execution agents (sandboxed)
- 📅 Plugin system for custom tools
- 📅 Agent marketplace
- 📅 Enterprise SSO integration

---

## 🎬 Getting Started Video

*(Coming soon - walkthrough of Mission Control interface, agent delegation, and Quick Actions)*

---

## 🤝 Contributing

We're building the future of AI collaboration. Join us!

**Ways to Contribute:**
- 🐛 Report bugs or UX improvements
- 💡 Suggest new agent specializations
- 📝 Improve documentation
- 🧪 Add test coverage
- ⚡ Performance optimizations
- 🎨 UI/UX enhancements

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

---

## 📜 License

Apache License 2.0 - Commercial use, modification, distribution, and patent use allowed.

See [LICENSE](LICENSE) for full details.

---

## 🙏 Built With

- **[LangGraph](https://github.com/langchain-ai/langgraph)** - Agent orchestration framework
- **[LangChain](https://github.com/langchain-ai/langchain)** - LLM integration layer
- **[shadcn/ui](https://ui.shadcn.com/)** - Beautiful, accessible components
- **[Tavily](https://tavily.com/)** - Fast, reliable web search API
- **OpenAI** - GPT-4o-mini powers the intelligence

---

## 💬 Why Mission Control?

Most AI tools hide what's happening. You ask, you wait, you hope.

**Commander.ai shows you everything:**
- Which agent is working
- What node they're on
- How many tokens they're using
- What tools they're calling
- How long it's taking

**You're not just using AI. You're commanding it.**

Try it. Watch @bob research while @alice stores results. See @maya catch issues before @kai refines the solution. Command, observe, control.

---

**Questions? Ideas? Issues?**

📧 [Open an issue](https://github.com/iotlodge/commander.ai/issues)
⭐ Star the repo if this excites you
🔔 Watch for updates - we ship fast

---

*Built by developers who believe AI should augment human capability, not replace it.*

**🚀 Status**: v2.0 Production - Mission Control
**📅 Last Updated**: February 5, 2026
