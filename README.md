# commander.ai

> **Your personal AI research team.** Delegate complex work to specialized AI agents that think, collaborate, and deliver results - all through natural conversation.

[![Python](https://img.shields.io/badge/Python-3.12+-blue.svg)](https://www.python.org/)
[![Next.js](https://img.shields.io/badge/Next.js-14-black.svg)](https://nextjs.org/)
[![LangGraph](https://img.shields.io/badge/LangGraph-Latest-green.svg)](https://github.com/langchain-ai/langgraph)
[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](LICENSE)

---

## 🎯 What Makes Commander.ai Different?

Most AI assistants give you one perspective. Commander.ai gives you a **team of specialists** working in parallel, each bringing unique expertise, then intelligently synthesizing their insights into comprehensive answers.

**Think of it as:**
- 🧠 A research team that never sleeps
- 🤝 Agents that actually collaborate (not just relay messages)
- 🚀 Parallel execution - multiple agents working simultaneously
- 🎯 Intelligent orchestration - the system decides the best approach
- 📊 Real-time visibility into what's happening

![Commander.ai Landing Page](images/landing-page.png?v=2025-02)

### Memory System: Context That Persists

Every conversation is remembered. Every insight is retained. Commander.ai uses a three-tier memory architecture:

- **🔥 Hot Layer (Redis)**: Active conversations, instant access
- **💾 Warm Layer (PostgreSQL)**: Complete conversation history
- **🎯 Smart Layer (Qdrant)**: Semantic search across all agent knowledge

---

## 🤖 Meet Your AI Team

### Conversational Agent

**💬 @chat** - *Interactive Chat Assistant*
- Natural conversation with GPT-4o-mini
- Web search integration via Tavily
- Context-aware responses
- Maintains conversation history
- *Your go-to for quick questions and casual chat*

### Specialist Agents

**🔬 @bob** - *Research Specialist*
- Deep research using Tavily web search + LLM synthesis
- Intelligent content analysis
- Automatic compliance flagging
- Multi-source information synthesis
- Cache-first search (24h TTL for general, 1h for news)
- *Bob is your investigative journalist*

**⚖️ @sue** - *Compliance Specialist*
- Regulatory compliance analysis
- GDPR, HIPAA, data protection review
- Policy adherence checking
- Risk assessment
- *Sue keeps you out of legal trouble*

**📊 @rex** - *Data Analyst*
- Statistical analysis
- Data visualization (matplotlib charts)
- Pattern detection
- Trend analysis
- *Rex turns data into insights*

**📚 @alice** - *Document Manager*
- PDF and document processing
- Collection management (create, delete, list)
- **Web search with persistent storage** (NEW!)
- Semantic search across documents
- Multi-document analysis
- Vector embeddings via Qdrant
- *Alice is your librarian with superpowers*

### Reasoning Specialists

**✨ @maya** - *Reflection Specialist*
- Reviews and critiques content
- Identifies issues by severity (critical/important/minor)
- Provides constructive feedback
- Generates improved versions
- Quality scoring (0-1.0)
- *Maya is your editor and quality control*

**🔄 @kai** - *Reflexion Specialist*
- Self-reflective reasoning with iteration (up to 3 cycles)
- Self-critique and improvement
- Shows reasoning evolution
- Iterative problem solving
- *Kai thinks deeply and improves through reflection*

---

## 🚀 Quick Start in 5 Minutes

### Prerequisites

```bash
Python 3.12+, Node.js 18+, Docker (recommended)
```

### Installation

1. **Clone and setup**
   ```bash
   git clone https://github.com/iotlodge/commander.ai.git
   cd commander.ai
   cp .env.example .env
   # Add your OPENAI_API_KEY and TAVILY_API_KEY to .env
   ```

2. **Start infrastructure**
   ```bash
   docker-compose up -d  # PostgreSQL, Redis, Qdrant
   ```

3. **Backend setup**
   ```bash
   uv sync                    # Install dependencies (or: pip install -r requirements.txt)
   alembic upgrade head       # Run migrations
   python -m uvicorn backend.api.main:app --reload
   ```

4. **Frontend setup** (new terminal)
   ```bash
   cd frontend
   npm install
   npm run dev
   ```

5. **Open browser** → http://localhost:3000

---

## 💬 How to Talk to Your AI Team

### Simple Commands

```bash
# Chat naturally
@chat what's the weather like in Paris?

# Direct to an agent
@bob research the latest quantum computing breakthroughs

# Natural conversation
hey sue, review this privacy policy for GDPR compliance

# Web search with storage
@alice search web for "PayPal company news that is negative" into paypal_research

# Document search
@alice search for "machine learning" in research_papers
```

### Alice's Web Search Workflow

When you ask Alice to search the web, here's what happens:

```
User: @alice search web for "quantum computing breakthroughs" into quantum_research
    ↓
1️⃣ Parse Input (extract query + collection name)
    ↓
2️⃣ Fetch Web Content (TavilyToolset with cache-first)
    ├─ Check cache (Qdrant web_cache_{user_id} collection)
    ├─ If stale/miss: Call Tavily API (rate-limited, retries)
    └─ Store results in cache with timestamp metadata
    ↓
3️⃣ Chunk Documents (DocumentChunker)
    ├─ Split content into semantic chunks
    ├─ Preserve metadata (URL, title, score, query)
    └─ Generate embeddings (OpenAI ada-002)
    ↓
4️⃣ Store in Collection (PostgreSQL + Qdrant)
    ├─ Create collection if doesn't exist
    ├─ Deduplicate by content hash
    ├─ Store in PostgreSQL (document_chunks table)
    └─ Store vectors in Qdrant (semantic search)
    ↓
5️⃣ Return Formatted Results
    ✓ Success message with chunk count
    📊 Top 5 results with titles, URLs, relevance scores
    🔗 Source links for user verification
```

**Cache Behavior:**
- General searches: **24 hour TTL**
- News searches: **1 hour TTL**
- Content hashing prevents duplicates
- Rate limiting: 60 API calls/minute
- Automatic retry with exponential backoff

---

## 🏗️ Architecture Deep Dive

### Project Structure

```
commander.ai/
├── backend/
│   ├── agents/
│   │   ├── base/              # Agent interface & registry
│   │   ├── parent_agent/      # @leo orchestrator (future)
│   │   └── specialized/
│   │       ├── agent_a/       # @bob (Research)
│   │       ├── agent_b/       # @sue (Compliance)
│   │       ├── agent_c/       # @rex (Data Analysis)
│   │       ├── agent_d/       # @alice (Document Manager)
│   │       │   ├── graph.py           # LangGraph workflow
│   │       │   ├── nodes.py           # 15 workflow nodes
│   │       │   ├── state.py           # State management
│   │       │   └── llm_classifier.py  # Intent classification
│   │       ├── agent_e/       # @maya (Reflection)
│   │       ├── agent_f/       # @kai (Reflexion)
│   │       └── agent_g/       # @chat (Chat Assistant)
│   ├── memory/
│   │   ├── document_store.py  # Qdrant + embeddings (SINGLETON!)
│   │   └── document_models.py # Data models
│   ├── models/
│   │   ├── collections.py     # Collection ORM
│   │   └── document_chunks.py # Chunk ORM
│   ├── repositories/          # Database access layer
│   ├── tools/
│   │   ├── web_search/
│   │   │   ├── tavily_toolset.py  # Unified Tavily API
│   │   │   └── exceptions.py      # Custom exceptions
│   │   ├── data_analysis/     # Charts, stats
│   │   └── document_processing/ # PDF, chunking
│   ├── core/
│   │   ├── config.py          # Settings (Pydantic)
│   │   └── dependencies.py    # Singleton management
│   └── api/                   # FastAPI app + WebSocket
└── frontend/                  # Next.js 14 App Router
```

### Alice's 15-Node Workflow Graph

Alice uses LangGraph to orchestrate complex document operations:

```
parse_input_node (classify intent)
    ↓
├─→ create_collection_node
├─→ delete_collection_node
├─→ list_collections_node
├─→ load_file_node → chunk_and_embed_node → store_chunks_node
├─→ fetch_web_node → chunk_and_embed_node → store_chunks_node
├─→ search_collection_node
├─→ search_all_collections_node
├─→ crawl_site_node (Tavily crawl)
├─→ extract_urls_node (Tavily extract)
└─→ map_site_node (Tavily site map)
    ↓
format_response_node (final output)
```

### DocumentStore Singleton Pattern ⚠️

**CRITICAL**: `DocumentStore` uses a singleton pattern to prevent connection pool exhaustion:

```python
# ✅ CORRECT - Use singleton
from backend.core.dependencies import get_document_store

doc_store = await get_document_store()
# Use doc_store (no disconnect needed - shared instance!)

# ❌ WRONG - Creates new connection pool
doc_store = DocumentStore()
await doc_store.connect()
await doc_store.disconnect()  # Breaks singleton for all agents!
```

**Why singleton?**
- Qdrant connection pooling (shared across agents)
- Prevents resource exhaustion
- Only disconnected during app shutdown
- TavilyToolset, alice, and other agents share the same instance

---

## 🔧 Integrating a New Agent

### Step 1: Create Agent Directory

```bash
mkdir -p backend/agents/specialized/agent_h
cd backend/agents/specialized/agent_h
touch __init__.py graph.py state.py nodes.py
```

### Step 2: Define Agent State

```python
# state.py
from typing import TypedDict, Annotated, Sequence
from operator import add

class MyAgentState(TypedDict):
    """State for your custom agent"""
    query: str
    user_id: str
    results: list[str]
    error: str | None
    # Add custom fields as needed
```

### Step 3: Implement Workflow Nodes

```python
# nodes.py
async def process_query_node(state: MyAgentState) -> dict:
    """Process user query"""
    # Your logic here
    return {
        **state,
        "results": ["processed results"],
    }

async def format_response_node(state: MyAgentState) -> dict:
    """Format final response"""
    return {
        **state,
        "final_response": "Formatted output for user",
    }
```

### Step 4: Build LangGraph Workflow

```python
# graph.py
from langgraph.graph import StateGraph, END
from backend.agents.base.agent_interface import (
    BaseAgent,
    AgentMetadata,
    AgentExecutionContext,
    AgentExecutionResult,
)
from backend.agents.specialized.agent_h.state import MyAgentState
from backend.agents.specialized.agent_h.nodes import (
    process_query_node,
    format_response_node,
)

class MyCustomAgent(BaseAgent):
    """Your Custom Agent"""

    def __init__(self):
        metadata = AgentMetadata(
            id="agent_h",
            nickname="yourname",  # e.g., "vision" for image analysis
            specialization="Your Specialization",
            description="What this agent does",
        )
        super().__init__(metadata)

    def _build_graph(self) -> StateGraph:
        """Build the agent workflow"""
        graph = StateGraph(MyAgentState)

        # Add nodes
        graph.add_node("process_query", process_query_node)
        graph.add_node("format_response", format_response_node)

        # Define edges
        graph.set_entry_point("process_query")
        graph.add_edge("process_query", "format_response")
        graph.add_edge("format_response", END)

        return graph

    async def execute(
        self, context: AgentExecutionContext
    ) -> AgentExecutionResult:
        """Execute the agent"""
        # Standard execution logic
        initial_state = MyAgentState(
            query=context.command,
            user_id=str(context.user_id),
            results=[],
            error=None,
        )

        # Run graph
        result = await self.graph.ainvoke(initial_state)

        return AgentExecutionResult(
            agent_id=self.metadata.id,
            user_id=context.user_id,
            result=result.get("final_response", ""),
            metadata={},
        )
```

### Step 5: Register Agent

```python
# backend/agents/base/agent_registry.py
from backend.agents.specialized.agent_h.graph import MyCustomAgent

# Add to registry
_registry["agent_h"] = MyCustomAgent()
```

### Step 6: Test

```bash
# In UI
@yourname do something amazing

# Or via API
curl -X POST http://localhost:8000/api/v1/tasks \
  -H "Content-Type: application/json" \
  -d '{"command": "@yourname test query", "user_id": "..."}'
```

---

## 📊 Real-Time Execution Metrics

Commander.ai provides **complete visibility** into agent execution with live metrics tracking:

**What you see:**
- 🔢 **LLM Calls**: Number of AI model invocations
- 🤝 **Agent Calls**: Nested agent consultations
- 🎯 **Tokens**: Total token consumption (prompt + completion)
- ⏱️ **Duration**: Live execution time
- 📈 **Progress**: Visual progress bar with current node

**Token Tracking Example (Alice web search):**
```
LLM Calls: 4
├─ embedding_generation: 856 tokens (3 calls)
├─ tavily_search_fallback: 362 tokens (1 call)
Total: 1,218 tokens
Duration: 12 seconds
Cache: HIT (saved API call!)
```

---

## 🛠️ Tech Stack

### Backend (Python)
- **LangGraph** - Agent orchestration framework
- **LangChain** - LLM integration layer
- **FastAPI** - Async web framework
- **PostgreSQL** - Persistent storage (documents, chunks, collections)
- **Redis** - Hot memory layer (active sessions)
- **Qdrant** - Vector database for semantic search
- **OpenAI** - GPT-4o-mini (intelligence), ada-002 (embeddings)
- **Tavily** - Web search API (research + cache)

### Frontend (TypeScript)
- **Next.js 14** - React with App Router
- **Tailwind CSS** - Utility-first styling
- **shadcn/ui** - Beautiful component library
- **Zustand** - State management
- **WebSocket** - Real-time updates

### Infrastructure
- **Docker Compose** - One-command setup
- **Alembic** - Database migrations
- **Async Python** - Non-blocking I/O

---

## ⚙️ Configuration

### Required Environment Variables

```bash
# Core - REQUIRED
OPENAI_API_KEY=sk-...                # GPT-4o-mini + ada-002 embeddings
TAVILY_API_KEY=tvly-...              # Web search for @bob and @alice

# Database - Auto-configured by Docker
DATABASE_URL=postgresql+asyncpg://commander:changeme@localhost:5432/commander_ai
REDIS_URL=redis://localhost:6379/0
QDRANT_URL=http://localhost:6333

# Web Cache Configuration (Optional - uses defaults)
WEB_CACHE_TTL_HOURS=24               # General content cache TTL
WEB_CACHE_NEWS_TTL_HOURS=1           # News content cache TTL
TAVILY_RATE_LIMIT_PER_MINUTE=60      # API rate limit
```

### Docker Services

```bash
docker-compose up -d
```

This starts:
- **PostgreSQL 16** (pgvector extension for embeddings)
- **Redis 7** (Alpine - lightweight)
- **Qdrant** (Latest vector DB)

All services have health checks and auto-restart.

---

## 🚦 Current Status

**✅ Production Ready (v1.1)**
- ✅ 7 specialized agents (chat, research, compliance, data, documents, reflection, reflexion)
- ✅ Three-tier memory system (Redis/PostgreSQL/Qdrant)
- ✅ Real-time Kanban UI with WebSocket
- ✅ Agent graph visualization with zoom/pan
- ✅ Document management with semantic search
- ✅ **Web search with cache-first architecture** (NEW!)
- ✅ **TavilyToolset integration** - unified search/crawl/extract/map (NEW!)
- ✅ **Automatic cache cleanup** - removes stale entries (NEW!)
- ✅ **DocumentStore singleton pattern** - prevents connection pool exhaustion (NEW!)

**🚧 In Active Development**
- ⏳ Vision/image analysis agent (in progress - image processing skill)
- ⏳ User authentication & multi-user support
- ⏳ CLI interface for terminal lovers
- ⏳ Agent performance metrics dashboard

**📅 Roadmap**
- Code execution agents (sandboxed)
- Plugin system for custom tools
- Agent marketplace
- Enterprise SSO integration

---

## 🤝 Contributing

Contributions are welcome! If you're excited about multi-agent systems, LangGraph, or making AI more useful:

**Ways to contribute:**
- 🐛 Report bugs or UX issues
- 💡 Suggest new agent specializations
- 📝 Improve documentation or examples
- 🧪 Add test coverage
- ⚡ Performance optimizations

See [CONTRIBUTING.md](CONTRIBUTING.md) for details.

---

## 📜 License

This project is licensed under the Apache License 2.0 - see the [LICENSE](LICENSE) file for details.

**Key Points:**
- ✅ Commercial use allowed
- ✅ Modification allowed
- ✅ Distribution allowed
- ✅ Patent use allowed

---

## 🙏 Acknowledgments

Built on the shoulders of giants:
- **[LangGraph](https://github.com/langchain-ai/langgraph)** - The foundation for agent orchestration
- **[LangChain](https://github.com/langchain-ai/langchain)** - LLM integration made simple
- **[shadcn/ui](https://ui.shadcn.com/)** - Beautiful, accessible components
- **[Tavily](https://tavily.com/)** - Fast, reliable web search API
- **OpenAI** - GPT-4o-mini powers the intelligence layer

---

## 💬 Final Thoughts

Commander.ai isn't just another AI assistant. It's a glimpse into how we'll work with AI in the future - not as a single tool, but as a **team of specialists** that collaborate, reason, and deliver results that are greater than the sum of their parts.

The magic happens when:
- @bob finds information you didn't know to look for
- @alice stores and searches it semantically
- @maya catches issues before they become problems
- @kai reasons through complex problems iteratively
- @chat answers your quick questions with web context

**Try it yourself.** Watch the agents work. See the reasoning unfold. You'll never go back to single-agent assistants.

---

**Questions? Issues? Ideas?**
📧 Open an issue or discussion on GitHub
⭐ Star the repo if this excites you
🔔 Watch for updates - this is moving fast

---

*Built with ❤️ by developers who believe AI should augment human capability, not replace it.*

---

**Status**: 🚀 v1.1 - Production Ready with Web Search Cache
**Last Updated**: February 2026
