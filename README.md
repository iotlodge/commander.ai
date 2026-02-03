# commander.ai

> **Your personal AI research team.** Delegate complex work to specialized AI agents that think, collaborate, and deliver results - all through natural conversation.

[![Python](https://img.shields.io/badge/Python-3.12+-blue.svg)](https://www.python.org/)
[![Next.js](https://img.shields.io/badge/Next.js-14-black.svg)](https://nextjs.org/)
[![LangGraph](https://img.shields.io/badge/LangGraph-Latest-green.svg)](https://github.com/langchain-ai/langgraph)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

---

## 🎯 What Makes Commander.ai Different?

Most AI assistants give you one perspective. Commander.ai gives you a **team of specialists** working in parallel, each bringing unique expertise, then intelligently synthesizing their insights into comprehensive answers.

**Think of it as:**
- 🧠 A research team that never sleeps
- 🤝 Agents that actually collaborate (not just relay messages)
- 🚀 Parallel execution - multiple agents working simultaneously
- 🎯 Intelligent orchestration - the system decides the best approach
- 📊 Real-time visibility into what's happening

![Commander.ai Architecture](images/architecture.png)

### Memory System: Context That Persists

Every conversation is remembered. Every insight is retained. Commander.ai uses a three-tier memory architecture:

![Memory Architecture](images/memory.png)

- **🔥 Hot Layer (Redis)**: Active conversations, instant access
- **💾 Warm Layer (PostgreSQL)**: Complete conversation history
- **🎯 Smart Layer (Qdrant)**: Semantic search across all agent knowledge

---

## 🎬 See It In Action

### Real-Time Kanban Board
Watch your tasks flow through the system. See exactly which agent is doing what, when:

![Commander.ai Landing Page](images/landing-page.png)

### Agent Intelligence Visualized
Ever wondered how AI agents actually think? See their decision trees and execution paths:

![Agent Graph Visualization](images/agent-graph.png)

### Deep Dive into Complex Workflows
Some agents have sophisticated reasoning paths. Zoom in to see how @alice manages her 15-node document workflow:

<p align="center">
  <img src="images/@aliceGraph.png" alt="Full-Screen Graph Viewer - @alice" width="800">
</p>

**Graph Viewer Features:**
- 🔍 Zoom up to 8x for detailed node inspection
- 🖱️ Click-and-drag panning for navigation
- 🎯 Fit-to-screen button for instant overview
- ⌨️ Mouse wheel zoom support
- 📊 Optimized spacing for complex graphs (10+ nodes)

### Intelligent Agent Selection
Type `@` and get instant autocomplete with agent specializations:

![Agent Autocomplete](images/agent-autocomplete.png)

---

## 🤖 Meet Your AI Team

### Core Orchestration

**🎭 @leo** - *The Orchestrator*
- Uses GPT-4o-mini to analyze your requests
- Decomposes complex tasks into specialized subtasks
- Coordinates parallel agent execution
- Synthesizes results into coherent final answers
- *Think of Leo as your project manager*

### Specialist Agents

**🔬 @bob** - *Research Specialist*
- Deep research using Tavily web search + LLM synthesis
- Intelligent content analysis
- Automatic compliance flagging
- Multi-source information synthesis
- *Bob is your investigative journalist*

**⚖️ @sue** - *Compliance Specialist*
- Regulatory compliance analysis
- GDPR, HIPAA, data protection review
- Policy adherence checking
- Risk assessment
- *Sue keeps you out of legal trouble*

**📊 @rex** - *Data Analyst*
- Statistical analysis
- Data visualization
- Pattern detection
- Trend analysis
- *Rex turns data into insights*

**📚 @alice** - *Document Manager*
- PDF and document processing
- Collection management
- Semantic search across documents
- Multi-document analysis
- *Alice is your librarian with superpowers*

### Reasoning Specialists (NEW! 🎉)

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
   # Add your OPENAI_API_KEY to .env
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

**Optional but recommended:** Add `TAVILY_API_KEY` for web search capabilities.

---

## 💬 How to Talk to Your AI Team

### Simple Commands

```bash
# Direct to an agent
@bob research the latest quantum computing breakthroughs

# Natural conversation
hey sue, review this privacy policy for GDPR compliance

# Get document help
@alice search for "machine learning" in research_papers
```

### Complex Multi-Agent Workflows

Here's where it gets interesting. Leo (the orchestrator) uses GPT-4o-mini to intelligently decompose your request:

```bash
research "Designing a Quantum Accelerator" investigate ['quantum computing fundamentals', 'accelerator architectures', 'power efficiency', 'cooling systems']
```

**What happens behind the scenes:**

1. 🧠 Leo analyzes your request with LLM reasoning
2. 🎯 Decomposes it into focused subtasks
3. 🚀 Launches multiple agents **in parallel**
4. 📊 Each agent investigates their area deeply
5. ✨ Leo synthesizes all findings into one coherent report

### Advanced Use Cases

**Content Review & Improvement**
```bash
@maya review this report: [paste your content]

# Maya will:
# - Analyze overall quality
# - Identify issues (critical/important/minor)
# - Suggest specific improvements
# - Generate a refined version
# - Provide a quality score
```

**Self-Reflective Problem Solving**
```bash
@kai solve: How can we optimize database queries for a social media platform with 1M+ concurrent users?

# Kai will:
# - Generate initial reasoning
# - Self-critique the approach
# - Identify flaws in logic
# - Refine reasoning iteratively
# - Show you the evolution of thinking
```

**Document Management**
```bash
# Create a collection
@alice create collection research_papers

# Load documents
@alice load ~/Documents/quantum_paper.pdf into research_papers

# Semantic search
@alice search for "error correction algorithms" in research_papers

# Cross-collection search
@alice search for "quantum gates" in [papers, articles, books]
```

---

## 🏗️ Architecture That Scales

### Intelligent Task Flow

```
User Query
    ↓
🎭 @leo (Orchestrator)
    ├─→ GPT-4o-mini analyzes request
    ├─→ Decomposes into subtasks
    └─→ Assigns to specialists
         ↓
   🚀 Parallel Execution (asyncio.gather)
    ├─→ @bob (Research)
    ├─→ @maya (Reflection)
    ├─→ @kai (Reflexion)
    └─→ [@sue, @rex, @alice...]
         ↓
   ✨ LLM-Powered Aggregation
    ├─→ Synthesizes all findings
    ├─→ Executive summary
    ├─→ Key insights from each specialist
    └─→ Actionable recommendations
         ↓
   📄 Final Response (Markdown)
```

### What Makes This Fast?

**Parallel Execution**: When Leo determines you need research from multiple areas, all agents run simultaneously using `asyncio.gather()`. A 3-agent task completes in ~10 seconds instead of ~30 seconds sequential.

**Smart Caching**: Redis keeps recent conversations hot. PostgreSQL stores everything. Qdrant enables semantic search across millions of data points.

**LLM Optimization**: Uses GPT-4o-mini for reasoning tasks (fast + cost-effective). Automatically falls back to pattern matching if needed.

---

## 🛠️ Tech Stack

### Backend (Python)
- **LangGraph** - Agent orchestration framework
- **LangChain** - LLM integration layer
- **FastAPI** - Async web framework
- **PostgreSQL** - Persistent storage
- **Redis** - Hot memory layer (active sessions)
- **Qdrant** - Vector database for semantic search
- **OpenAI GPT-4o-mini** - Intelligence layer

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

## 📊 Project Structure

```
commander.ai/
├── backend/
│   ├── agents/
│   │   ├── base/           # Agent interface & registry
│   │   ├── parent_agent/   # @leo orchestrator
│   │   │   ├── llm_reasoning.py      # GPT-4o-mini decomposition
│   │   │   ├── llm_aggregation.py    # Result synthesis
│   │   │   ├── nodes.py              # Graph nodes (parallel exec)
│   │   │   └── graph.py              # LangGraph workflow
│   │   └── specialized/
│   │       ├── agent_a/    # @bob (Research) - LLM-powered
│   │       ├── agent_b/    # @sue (Compliance)
│   │       ├── agent_c/    # @rex (Data Analysis)
│   │       ├── agent_d/    # @alice (Documents)
│   │       ├── agent_e/    # @maya (Reflection) ⚡ NEW
│   │       └── agent_f/    # @kai (Reflexion) ⚡ NEW
│   ├── memory/             # Three-tier memory system
│   │   ├── short_term.py   # Redis (hot layer)
│   │   ├── long_term.py    # PostgreSQL (warm layer)
│   │   ├── vector_store.py # Qdrant (semantic layer)
│   │   └── memory_service.py
│   ├── api/                # FastAPI app + WebSocket
│   └── core/               # Config, parsers, executors
├── frontend/
│   ├── app/                # Next.js 14 App Router
│   ├── components/         # React components
│   │   ├── kanban/        # Real-time task board
│   │   ├── graphs/        # Agent visualization
│   │   └── command/       # Input with autocomplete
│   └── lib/               # WebSocket, state, types
└── migrations/            # Database schema versions
```

---

## ⚙️ Configuration

### Required Environment Variables

```bash
# Core - REQUIRED
OPENAI_API_KEY=sk-...                # GPT-4o-mini for reasoning

# Database - Auto-configured by Docker
DATABASE_URL=postgresql+asyncpg://commander:changeme@localhost:5432/commander_ai
REDIS_URL=redis://localhost:6379/0
QDRANT_URL=http://localhost:6333

# Optional - Enhances Capabilities
TAVILY_API_KEY=tvly-...              # Web search for @bob
ANTHROPIC_API_KEY=sk-ant-...         # Alternative LLM provider
```

### Docker Services (Included)

```bash
docker-compose up -d
```

This starts:
- **PostgreSQL 16** (pgvector extension)
- **Redis 7** (Alpine - lightweight)
- **Qdrant** (Latest vector DB)

All services have health checks and auto-restart.

---

## 💡 Real-World Examples

### Example 1: Market Research

**Command:**
```bash
research "AI Agent Frameworks 2025" investigate ['current market leaders', 'emerging technologies', 'adoption trends', 'cost comparison']
```

**What you get:**
- 🔬 @bob researches each area in parallel
- 📊 Comprehensive findings from multiple sources
- 🎯 Executive summary with key insights
- 💡 Recommendations based on trends
- ⏱️ Complete in ~10 seconds (vs 40s sequential)

### Example 2: Content Quality Control

**Command:**
```bash
@maya review this article: [paste 2000-word article]
```

**What you get:**
- 📝 Overall quality assessment (0-1.0 score)
- 🔴 Critical issues that must be fixed
- 🟡 Important improvements
- 🟢 Minor polish suggestions
- ✨ Refined version with improvements applied

### Example 3: Deep Problem Solving

**Command:**
```bash
@kai analyze: Why are our API response times degrading under load?
```

**What you get:**
- 🧠 Initial hypothesis and reasoning
- 🔍 Self-critique of the analysis
- 🔄 Refined reasoning (iteration 2)
- 🔍 Another self-critique
- ✅ Final comprehensive analysis (iteration 3)
- 📈 Shows evolution of thinking

### Example 4: Document Intelligence

**Command:**
```bash
@alice load research_papers/*.pdf into quantum_research
@alice search for "topological qubits" in quantum_research
@alice summarize findings about error correction
```

**What you get:**
- 📚 All PDFs indexed with vector embeddings
- 🎯 Semantic search (not just keywords)
- 📊 Cross-document synthesis
- 💡 Connections you might have missed

---

## 🎮 Keyboard Shortcuts

- `Cmd/Ctrl + Enter` - Submit command
- `@` - Trigger agent autocomplete
- `Esc` - Close modals/dialogs

---

## 🚦 Current Status

**✅ Production Ready (v1.0)**
- ✅ LLM-powered task decomposition (GPT-4o-mini)
- ✅ Parallel multi-agent execution (asyncio.gather)
- ✅ Intelligent result aggregation
- ✅ 7 specialized agents (including @maya and @kai)
- ✅ Three-tier memory system (Redis/PostgreSQL/Qdrant)
- ✅ Real-time Kanban UI with WebSocket
- ✅ Agent graph visualization
- ✅ Full-screen graph viewer with zoom/pan
- ✅ Document management with semantic search

**🚧 In Active Development**
- ⏳ User authentication & multi-user support
- ⏳ CLI interface for terminal lovers
- ⏳ Export to .docx/.pdf (currently markdown)
- ⏳ Agent performance metrics dashboard
- ⏳ Custom agent creation wizard

**📅 Roadmap**
- Vision/image analysis agents
- Code execution agents (sandboxed)
- Plugin system for custom tools
- Agent marketplace
- Enterprise SSO integration

---

## 🤝 Contributing

This started as a personal project to explore what's possible when you give AI agents the ability to truly collaborate. If you're excited about multi-agent systems, LangGraph, or just want to make AI more useful, contributions are welcome!

**Ways to contribute:**
- 🐛 Report bugs or UX issues
- 💡 Suggest new agent specializations
- 📝 Improve documentation or examples
- 🧪 Add test coverage
- ⚡ Performance optimizations

**Before submitting a PR:**
1. Run tests: `pytest`
2. Check linting: `ruff check .`
3. Ensure type safety: `mypy backend/`

---

## 📜 License

[Choose your license] - This project is open source and available for modification.

---

## 🙏 Acknowledgments

Built on the shoulders of giants:
- **[LangGraph](https://github.com/langchain-ai/langgraph)** - The foundation for agent orchestration
- **[LangChain](https://github.com/langchain-ai/langchain)** - LLM integration made simple
- **[shadcn/ui](https://ui.shadcn.com/)** - Beautiful, accessible components
- **[Lucide Icons](https://lucide.dev/)** - Clean, consistent icons
- **OpenAI** - GPT-4o-mini powers the intelligence layer

---

## 📚 Further Reading

- [IMPLEMENTATION_SUMMARY.md](IMPLEMENTATION_SUMMARY.md) - Deep dive into the LLM system
- [Commander_ai_Project_Plan.md](Commander_ai_Project_Plan.md) - Original vision and requirements
- [PLAN.md](PLAN.md) - Detailed development roadmap

---

## 💬 Final Thoughts

Commander.ai isn't just another AI assistant. It's a glimpse into how we'll work with AI in the future - not as a single tool, but as a **team of specialists** that collaborate, reason, and deliver results that are greater than the sum of their parts.

The magic happens when:
- @bob finds information you didn't know to look for
- @maya catches issues before they become problems
- @kai reasons through complex problems iteratively
- @leo brings it all together into actionable insights

**Try it yourself.** Watch the agents work. See the reasoning unfold. You'll never go back to single-agent assistants.

---

**Questions? Issues? Ideas?**
📧 Open an issue or discussion on GitHub
⭐ Star the repo if this excites you
🔔 Watch for updates - this is moving fast

---

*Built with ❤️ by developers who believe AI should augment human capability, not replace it.*

---

**Status**: 🚀 v1.0 - Production Ready
**Last Updated**: February 2025
