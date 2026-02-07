<!--
SEO Keywords: multi-agent AI, AI orchestration, LangGraph agents, agent framework,
real-time AI dashboard, AI mission control, autonomous agents, LLM orchestration,
AI agent metrics, agent workflow, LangChain multi-agent, GPT-4 agents, agentic AI,
AI workflow automation, agent observability, AI team collaboration, FastAPI agents,
Next.js AI dashboard, real-time agent monitoring, AI agent visualization
-->

# Commander.ai

> **Mission Control for your AI team.** Watch specialized agents collaborate in real-time, executing complex tasks with complete visibility and maximum control.

<div align="center">

[![Python](https://img.shields.io/badge/Python-3.12+-blue.svg)](https://www.python.org/)
[![Next.js](https://img.shields.io/badge/Next.js-14-black.svg)](https://nextjs.org/)
[![LangGraph](https://img.shields.io/badge/LangGraph-Latest-green.svg)](https://github.com/langchain-ai/langgraph)
[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](LICENSE)

[![GitHub Stars](https://img.shields.io/github/stars/iotlodge/commander.ai?style=social)](https://github.com/iotlodge/commander.ai/stargazers)
[![GitHub Forks](https://img.shields.io/github/forks/iotlodge/commander.ai?style=social)](https://github.com/iotlodge/commander.ai/network/members)
[![GitHub Issues](https://img.shields.io/github/issues/iotlodge/commander.ai)](https://github.com/iotlodge/commander.ai/issues)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](CONTRIBUTING.md)

</div>

---

## 🎯 Why Commander.ai?

**Single AI assistants give you one perspective. Commander.ai gives you a specialized team you can tune in real-time.**

Unlike chatbots that force you to wait and guess, Commander.ai shows you **exactly what's happening** as your AI team works—and lets you **engineer their behavior on the fly**:

- 🔴 **Live Agent Activity** - Watch tokens flow and LLM calls execute in real-time
- 🧠 **Live Prompt Engineering** - Edit agent prompts, test with real LLM, see instant results ✨ **NEW in v0.3.0**
- ⚡ **One-Click Commands** - Quick Actions panel for instant delegation
- 📊 **Complete Visibility** - See every node, tool call, and decision
- 🎯 **Maximum Control** - Clear completed tasks, zoom agent graphs, filter by agent
- 🚀 **True Parallelization** - Multiple agents working simultaneously

**This isn't a chat interface with agents bolted on. It's Mission Control with a prompt engineering workshop built in.**

<div align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="images/dark_landing_page.png">
    <source media="(prefers-color-scheme: light)" srcset="images/light_landing_page.png">
    <img alt="Commander.ai Mission Control" src="images/dark_landing_page.png" width="100%">
  </picture>
  <p><em>Mission Control: Real-time visibility into your AI team</em></p>
</div>

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

### Agent Interaction

**Single-Click Agent Selection:**
- Click any agent tile → Auto-fills command input with `@agent `
- Instant delegation - just add your task and press Enter
- Example: Click @bob → type "latest AI news" → Send

**Multi-Select with Modifier Keys:**
- Hold **⌘ (Command)** or **Shift** while clicking agents
- Build multi-agent commands effortlessly
- Example workflow:
  ```
  1. Click @bob → "@bob "
  2. Hold ⌘ + Click @alice → "@bob @alice "
  3. Hold Shift + Click @kai → "@bob @alice @kai "
  4. Add task: "research and document quantum computing"
  5. Send → @leo orchestrates all three agents
  ```

**Smart Command Routing:**
- **Single @mention** → Direct to that agent
- **Multiple @mentions** → @leo orchestrates the team
- **No @mention** → Defaults to @leo

*💡 Tip: Look for the hint "Hold ⌘ / Shift to select multiple agents" in the Agent Panel*

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

## 🧠 Live Prompt Engineering - **NEW in v0.3.0**

### **Tune Your AI Team's Intelligence in Real-Time**

**The breakthrough**: You're not stuck with pre-programmed agent behavior. Commander.ai v0.3.0 introduces **live prompt engineering**—edit how your agents think, test changes instantly, and optimize AI orchestration outcomes on the fly.

### 🎛️ **What You Can Do**

**Access the Workshop:**
- Hover over any agent card
- Click the ⚙️ Settings icon
- Enter the Prompt Management UI

![Agent Settings Icon](images/agent_system_settings.png)
*Hover over any agent card to reveal the ⚙️ Settings icon. Click to access Prompt Management.*

**Inside the Prompt Engineer:**

1. **📋 Browse & Search**
   - View all prompts for the selected agent
   - Search by keyword across descriptions and prompt text
   - Filter by type (system, human, ai) and active status
   - See creation/update timestamps

![Manage Prompts Modal](images/manage_prompt_modal.png)
*Prompt List Modal showing search, filters, and prompt cards with type badges, active status, and update timestamps.*

2. **✏️ Create & Edit**
   - Write new prompts with rich template variables
   - Edit existing prompts while preserving version history
   - Add dynamic variables: `{query}`, `{token_budget}`, `{urgency}`, `{tools_list}`
   - Toggle active/inactive for A/B testing

![Edit Prompt Interface](images/edit_live_prompts.png)
*Prompt Editor with description, prompt text area, template variables section, and Test button for live LLM validation.*

3. **🧪 Test with Real LLM**
   - Click "Test" on any prompt
   - Enter a test query
   - See **live GPT-4o-mini response** with your custom prompt
   - View performance metrics:
     - Response time (ms)
     - Token usage (prompt + completion)
     - Total cost estimation
   - Debug compiled messages (system + user prompts)

4. **🔄 Iterate & Optimize**
   - See results instantly
   - Compare prompt variations
   - Measure impact on token efficiency
   - Optimize for speed vs. quality

### 🎨 **Visual Workflow**

The prompt engineering interface follows an intuitive three-step process:

1. **Access** - Hover over any agent → Click ⚙️ Settings
2. **Browse** - Search/filter prompts → View details → Click Edit
3. **Edit & Test** - Modify prompt → Add variables → Test with GPT-4o-mini → Save

Each step is designed for speed and clarity, making prompt optimization feel natural.

### 💡 **Why This Changes Everything**

**Before v0.3.0:**
- Agent behavior was hardcoded
- Tuning required backend changes and redeployment
- No way to test prompt modifications
- One-size-fits-all approach

**With v0.3.0 Prompt Engineering:**
- ✅ Tune agents **without touching code**
- ✅ Test prompts **with real LLM** before activating
- ✅ See metrics: tokens, time, cost
- ✅ A/B test different approaches (toggle active/inactive)
- ✅ Dynamic variables adapt to task context
- ✅ Version history tracks all changes

### 🎯 **Real-World Use Cases**

**Scenario 1: Reduce Token Usage**
```
Problem: @bob uses too many tokens for simple queries
Solution:
  1. Open @bob's prompts
  2. Edit system prompt to be more concise
  3. Test with "latest AI news"
  4. Compare tokens: 1,234 → 856 (31% reduction!)
  5. Activate optimized prompt
```

**Scenario 2: Improve Response Quality**
```
Problem: @maya's reflections lack depth
Solution:
  1. Clone existing system prompt
  2. Add: "Provide 3 specific examples for each issue"
  3. Test with sample content
  4. See richer, more actionable feedback
  5. Switch to new prompt
```

**Scenario 3: Task-Specific Behavior**
```
Problem: Need @alice to prioritize speed over accuracy for demos
Solution:
  1. Create new "demo_mode" prompt
  2. Add variable: {mode} = "demo" | "production"
  3. Adjust system instructions for speed
  4. Test and activate for demos
  5. Switch back to production mode after
```

### 🚀 **The Meta-Programming Advantage**

You're not just using AI—you're **engineering how AI thinks**.

- **Frontend teams** can optimize agent behavior without backend deploys
- **Prompt engineers** can iterate 10x faster with live testing
- **Product teams** can A/B test different agent personalities
- **Operations** can tune for cost vs. performance in real-time

**This is the workshop that turns Commander.ai from a tool into a platform.**

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

## 📊 Performance & Intelligence System

**Commander.ai learns and optimizes agent performance automatically.**

The system tracks, evaluates, and routes tasks intelligently using:

- **🎯 Multi-Perspective Scoring** - Objective metrics, LLM self-assessment, peer reviews, user feedback, category performance
- **🏆 Reward System** - Gamification with bonuses/penalties based on quality, efficiency, speed, and innovation
- **🤖 Peer Evaluation** - Agents (Kai + Maya) review each other's work for continuous improvement
- **🧠 Intelligent Routing** - Auto-classify tasks and select best agent based on historical performance
- **📈 Real-Time Stats** - Aggregated performance data drives routing decisions (~$0.001/task for full intelligence)

**📘 [Complete Performance System Guide →](PERFORMANCE_SYSTEM_GUIDE.md)**

Learn how to monitor, tune, and optimize the entire intelligence layer built across Phases 1-3.

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
│   │   └── specialized/       # 8 specialist agents
│   │       ├── parent/        # @leo (Orchestrator)
│   │       ├── agent_a/       # @bob (Research)
│   │       ├── agent_b/       # @sue (Compliance)
│   │       ├── agent_c/       # @rex (Data Analysis)
│   │       ├── agent_d/       # @alice (Documents)
│   │       ├── agent_e/       # @maya (Reflection)
│   │       ├── agent_f/       # @kai (Reflexion)
│   │       └── agent_g/       # @chat (Chat Assistant)
│   ├── core/
│   │   └── prompt_engineer.py # 🧠 NEW - Dynamic prompt compilation & testing
│   ├── repositories/
│   │   └── prompt_repository.py # Database access for prompts
│   ├── models/
│   │   └── prompt_models.py    # Pydantic schemas for prompts
│   ├── memory/               # Document store & embeddings
│   ├── tools/                # Web search, data analysis, PDF processing
│   └── api/
│       └── routes/
│           └── prompts.py    # 🧠 NEW - REST API for prompt management
└── frontend/
    ├── components/
    │   ├── mission-control/  # Three-panel UI
    │   │   ├── agent-team-panel.tsx      # Live agent metrics + ⚙️ Settings
    │   │   ├── conversation-stream.tsx   # Command/response flow
    │   │   ├── quick-actions-panel.tsx   # One-click commands
    │   │   ├── inline-execution-flow.tsx # Metrics timeline
    │   │   └── inline-agent-graph.tsx    # Workflow visualization
    │   └── prompt-management/  # 🧠 NEW - Prompt Engineering UI
    │       ├── prompt-list-modal.tsx     # Browse & search prompts
    │       ├── prompt-editor-modal.tsx   # Create/edit prompts
    │       ├── prompt-test-modal.tsx     # Live LLM testing
    │       └── prompt-card.tsx           # Individual prompt display
    ├── lib/
    │   └── hooks/
    │       └── use-prompts.ts  # 🧠 NEW - Prompt CRUD operations
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

**✅ v0.3.0 - Live Prompt Engineering** (February 2026) 🔥 **MAJOR RELEASE**

**🧠 Revolutionary New Feature:**
- ✅ **Live Prompt Engineering** - Edit, test, and optimize agent behavior in real-time
  - Full CRUD for agent prompts via UI
  - Live LLM testing with GPT-4o-mini
  - Performance metrics (tokens, time, cost)
  - Template variables for dynamic context
  - A/B testing with active/inactive toggles
  - Search, filter, and version tracking
  - ⚙️ Settings icon on every agent card

**Core Features (Stable):**
- ✅ **Mission Control UI** - Three-panel interface with real-time metrics
- ✅ **8 Specialized Agents** - Leo (orchestrator), Chat, Research, Compliance, Data, Documents, Reflection, Reflexion
- ✅ **Quick Actions Panel** - One-click command delegation
- ✅ **Live Agent Metrics** - Token counts, LLM calls, tool usage, current node
- ✅ **Execution Flow Tracking** - Complete observability into every step
- ✅ **Graph Visualization** - Agent workflow diagrams with zoom controls
- ✅ **Completed Task Management** - Track and clear finished work
- ✅ **Light/Dark Mode** - Theme toggle with system preference detection
- ✅ **Three-Tier Memory** - Redis/PostgreSQL/Qdrant
- ✅ **Web Search Cache** - 24h general, 1h news TTL
- ✅ **JWT Authentication** - Production-ready security (94% test coverage)
- ✅ **DocumentStore Singleton** - Prevents connection pool exhaustion
- ✅ **Agentic Tool Execution** - Chat agent executes web searches automatically

**What's New in v0.3.0:**
- 🧠 **PROMPT ENGINEERING WORKSHOP** - The game-changer
  - In-UI prompt editor with live testing
  - Real GPT-4o-mini responses with metrics
  - Template variables: `{query}`, `{token_budget}`, `{urgency}`
  - Search across 10+ seeded prompts
  - No backend deploy needed for tuning
- 🔧 **PromptEngineer Service** - Backend architecture for dynamic prompt compilation
- 📊 **Prompt Testing API** - `/api/prompts/test` with full metrics
- 🎨 **Nested Modal System** - Browse → Edit → Test workflow
- 🔍 **Prompt Search** - Find and filter prompts by agent, type, keywords

**Previous Releases:**
- **v0.2.0** (Feb 5, 2026) - Light/dark mode, agent status indicators, Leo orchestrator UI
- **v0.1.0** (Feb 1, 2026) - Mission Control UI, 7 agents, real-time metrics

**Roadmap:**
- 📅 **Prompt Marketplace** - Share and discover optimized prompts
- 📅 **Agent Integration** - Auto-use PromptEngineer for all agent initialization
- 📅 **Cost Analytics** - Track prompt efficiency and ROI
- 📅 **Vision Agent** - Image analysis and generation
- 📅 **CLI Interface** - Terminal workflows for power users
- 📅 **Code Execution** - Sandboxed Python/JS agents
- 📅 **Plugin System** - Custom tools and integrations
- 📅 **Enterprise SSO** - SAML/OAuth integration

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

**🚀 Status**: v0.3.0 Production - Live Prompt Engineering
**📅 Last Updated**: February 6, 2026
