# Prompt Architecture - Commander.ai

**Purpose**: Document the complete prompt architecture for Commander.ai to enable dynamic, agent-specific prompt engineering.

**Last Updated**: February 6, 2026

---

## Table of Contents

1. [Overview](#overview)
2. [Current Prompt Infrastructure](#current-prompt-infrastructure)
3. [Message Types & Patterns](#message-types--patterns)
4. [Agent-Specific Prompts](#agent-specific-prompts)
5. [Prompt Storage & Retrieval](#prompt-storage--retrieval)
6. [Dynamic Prompt Generation Strategy](#dynamic-prompt-generation-strategy)
7. [PromptEngineer Node Design](#promptengineer-node-design)
8. [Prompt Management UI & API](#prompt-management-ui--api)

---

## Overview

### Current State

Commander.ai uses **hardcoded prompts** embedded directly in agent code:
- **SystemMessage**: Agent personality, role, guidelines
- **HumanMessage**: User queries and formatted instructions
- **AIMessage**: Previous responses (conversation history)
- **ToolMessage**: Tool execution results (in agentic loops)

### Target State (PromptEngineer)

**Goal**: Dynamic prompt generation that:
1. **Adapts to agent context** - Each agent's role, capabilities, and constraints
2. **Considers task requirements** - Query complexity, available tools, expected output
3. **Maintains consistency** - Brand voice, formatting standards, quality guidelines
4. **Enables experimentation** - A/B testing, prompt optimization, performance tracking

---

## Current Prompt Infrastructure

### Database Schema

**Table**: `agent_prompts`

```sql
CREATE TABLE agent_prompts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    agent_id VARCHAR(50) NOT NULL,           -- e.g., "parent", "agent_a"
    nickname VARCHAR(50) NOT NULL,            -- e.g., "leo", "bob"
    description TEXT NOT NULL,                -- Human-readable purpose
    prompt_text TEXT NOT NULL,                -- The actual prompt content
    active BOOLEAN NOT NULL DEFAULT true,     -- Enable/disable without deletion
    prompt_type VARCHAR(50) DEFAULT 'system', -- 'system', 'human', 'ai'
    variables JSONB NOT NULL DEFAULT '{}',    -- Template variables
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_agent_prompts_agent_id ON agent_prompts(agent_id);
```

### Pydantic Models

**Location**: `backend/models/prompt_models.py`

```python
class AgentPrompt(BaseModel):
    id: UUID
    agent_id: str                    # Agent identifier
    nickname: str                    # Agent nickname (e.g., "bob")
    description: str                 # What this prompt does
    prompt_text: str                 # The prompt content
    active: bool = True              # Is this prompt active?
    prompt_type: str = "system"      # Message type: system/human/ai
    variables: dict = Field(default_factory=dict)  # Template variables
    created_at: datetime
    updated_at: datetime
```

### Repository

**Location**: `backend/repositories/prompt_repository.py`

**Methods**:
```python
async def create_prompt(prompt: PromptCreate) -> AgentPrompt
async def get_prompt(prompt_id: UUID) -> AgentPrompt | None
async def get_active_prompts(agent_id: str) -> list[AgentPrompt]
async def update_prompt(prompt_id: UUID, update: PromptUpdate) -> AgentPrompt
```

**Key Features**:
- Active/inactive prompts (soft delete pattern)
- Agent-scoped retrieval
- Template variable support (JSONB field)

---

## Message Types & Patterns

### 1. SystemMessage - Agent Personality & Guidelines

**Purpose**: Define the agent's role, capabilities, constraints, and output format.

**Pattern**:
```python
system_prompt = """You are {agent_name}, a {specialization} at Commander.ai.
Your role is to {primary_responsibility}.

Available tools:
{tools_list}

Guidelines:
- {guideline_1}
- {guideline_2}
- Use markdown formatting
- Be {tone_adjective} and {tone_adjective_2}

Output format:
{expected_output_structure}
"""

messages = [SystemMessage(content=system_prompt)]
```

**Current Usage**:
- Every agent has 1 SystemMessage at message list start
- Defines personality, tone, capabilities
- Lists available tools and when to use them
- Specifies output format (JSON, markdown, structured)

**Examples**:
- **Bob (Research)**: "You are Bob, a Research Specialist... synthesize information from multiple sources..."
- **Sue (Compliance)**: "You are Sue, a Compliance Specialist... analyze for GDPR, HIPAA..."
- **Chat**: "You are a helpful AI assistant... use web_search tool when appropriate..."

### 2. HumanMessage - User Queries & Instructions

**Purpose**: User input or system-generated instructions for the agent.

**Pattern**:
```python
user_prompt = f"""Research query: {query}

Available sources:
{sources_text}

Synthesize these sources into a comprehensive response with:
1. Executive summary
2. Key findings
3. Analysis and implications
"""

messages.append(HumanMessage(content=user_prompt))
```

**Current Usage**:
- User's original query
- Formatted instructions with context
- Structured data to process
- Multi-step task breakdowns

**Examples**:
- **Task Decomposition**: "Analyze this research request and decompose it into subtasks..."
- **Research Synthesis**: "Synthesize these sources into a comprehensive response..."
- **Compliance Check**: "Analyze this text for compliance concerns..."

### 3. AIMessage - Conversation History

**Purpose**: Previous agent responses to maintain context.

**Pattern**:
```python
# From conversation history
if conversation_history:
    for msg in conversation_history:
        if msg["role"] == "assistant":
            messages.append(AIMessage(content=msg["content"]))
```

**Current Usage**:
- Multi-turn conversations (@chat agent)
- Context preservation across interactions
- Agentic loops (LLM response → tool → LLM response)

**Examples**:
- **Chat Agent**: Full conversation history for context
- **Reflexion Agent**: Previous reasoning attempts for self-improvement

### 4. ToolMessage - Tool Execution Results

**Purpose**: Results from tool calls to feed back into LLM.

**Pattern**:
```python
# After tool execution
tool_message = ToolMessage(
    content=search_results,
    tool_call_id=tool_call["id"]
)
messages.append(tool_message)

# LLM invoked again with tool results
response = await llm.ainvoke(messages)
```

**Current Usage**:
- Agentic tool execution loops
- Web search results → synthesis
- Document retrieval → analysis
- API calls → interpretation

**Examples**:
- **Web Search**: Search results formatted as ToolMessage
- **Document Search**: Retrieved documents as context
- **Data Analysis**: Processed data visualization results

---

## Agent-Specific Prompts

### Parent Agent (Leo - Orchestrator)

**Files**:
- `backend/agents/parent_agent/llm_reasoning.py` - Task decomposition
- `backend/agents/parent_agent/llm_aggregation.py` - Result synthesis

**SystemMessage Pattern**:
```python
"""You are an intelligent task orchestrator for Commander.ai.
Your job is to analyze research requests and decompose them into targeted subtasks.

Available specialist agents:
- bob (Research Specialist): Web research, synthesis
- sue (Compliance Specialist): Legal/regulatory review
- rex (Data Analyst): Statistical analysis, visualization
- alice (Document Manager): Document storage, retrieval

For research tasks:
1. Identify main investigation areas
2. Create 1-5 focused subtasks (prefer 3-4)
3. Assign to appropriate agent(s)
4. Refine into clear, specific prompts
5. Consider parallel execution
"""
```

**HumanMessage Pattern**:
```python
f"""Analyze this research request and decompose it into subtasks:

REQUEST: {query}

Provide your decomposition in JSON format."""
```

**Output Format**: JSON with `task_type`, `reasoning`, `subtasks[]`

**Variables Needed**:
- `{query}` - User's original request
- `{available_agents}` - Dynamic list of configured agents
- `{agent_capabilities}` - Each agent's specializations

### Agent A (Bob - Research Specialist)

**Files**:
- `backend/agents/specialized/agent_a/llm_research.py`

**Key Functions**:
1. **Web Search** (`llm_web_search`) - Tavily API + fallback
2. **Research Synthesis** (`llm_synthesize_research`) - Multi-source analysis
3. **Compliance Detection** (`llm_check_compliance_keywords`) - Auto-flagging

**SystemMessage Pattern** (Synthesis):
```python
"""You are Bob, a Research Specialist at Commander.ai.
Your role is to synthesize information from multiple sources into clear, comprehensive research responses.

Guidelines:
- Provide well-structured, informative analysis
- Cite key findings from sources
- Highlight important insights and implications
- Use clear section headings
- Be objective and factual
- Note limitations or uncertainties
- Format using markdown for readability
"""
```

**HumanMessage Pattern** (Synthesis):
```python
f"""Research query: {query}

Available sources:
{sources_text}

Synthesize these sources into a comprehensive response with:
1. Executive summary (2-3 sentences)
2. Key findings (3-5 main points)
3. Analysis and implications
4. Recommendations or next steps (if applicable)
"""
```

**Variables Needed**:
- `{query}` - Research question
- `{sources_text}` - Formatted search results
- `{max_sources}` - Number of sources to include
- `{output_style}` - "comprehensive" | "executive" | "technical"

### Agent B (Sue - Compliance Specialist)

**Files**:
- Currently uses Bob's `llm_check_compliance_keywords` function
- Needs dedicated compliance analysis prompts

**SystemMessage Pattern** (Needed):
```python
"""You are Sue, a Compliance Specialist at Commander.ai.
Your role is to analyze content for legal, regulatory, and privacy compliance.

Focus areas:
- GDPR (General Data Protection Regulation)
- HIPAA (Health Insurance Portability and Accountability Act)
- CCPA (California Consumer Privacy Act)
- PII (Personally Identifiable Information)
- Data protection and consent mechanisms

Guidelines:
- Identify specific compliance concerns
- Cite relevant regulations and clauses
- Assess severity (critical, high, medium, low)
- Suggest remediation steps
- Be thorough but practical
"""
```

**Variables Needed**:
- `{content}` - Text to analyze
- `{jurisdiction}` - "EU" | "US" | "global"
- `{regulations}` - Specific regs to check (e.g., ["GDPR", "HIPAA"])
- `{severity_threshold}` - Minimum severity to report

### Agent C (Rex - Data Analyst)

**Files**:
- `backend/agents/specialized/agent_c/nodes.py` - Data processing nodes

**SystemMessage Pattern** (Needed):
```python
"""You are Rex, a Data Analyst at Commander.ai.
Your role is to analyze data, identify patterns, and create visualizations.

Capabilities:
- Statistical analysis (mean, median, correlation, regression)
- Pattern detection and trend analysis
- Data visualization with Matplotlib
- CSV/JSON data processing

Guidelines:
- Explain analysis methodology
- Highlight key insights and outliers
- Recommend visualization types
- Provide statistical confidence levels
- Note data quality issues or limitations
"""
```

**Variables Needed**:
- `{data_source}` - Raw data or data description
- `{analysis_type}` - "descriptive" | "diagnostic" | "predictive" | "prescriptive"
- `{visualization_preference}` - Chart types requested
- `{statistical_confidence}` - Required confidence level

### Agent D (Alice - Document Manager)

**Files**:
- `backend/agents/specialized/agent_d/nodes.py` - Document operations

**SystemMessage Pattern** (Needed):
```python
"""You are Alice, a Document Manager at Commander.ai.
Your role is to store, retrieve, and manage documents with semantic search.

Capabilities:
- PDF processing with OCR
- Vector embeddings via Qdrant
- Semantic search across collections
- Collection creation and management
- Web search → persistent storage

Guidelines:
- Create descriptive collection names
- Use relevant metadata for searchability
- Explain retrieval relevance scores
- Suggest collection organization strategies
- Handle multi-document queries intelligently
"""
```

**Variables Needed**:
- `{operation}` - "store" | "search" | "retrieve" | "create_collection"
- `{collection_name}` - Target collection
- `{search_query}` - Semantic search query
- `{max_results}` - Number of results to return

### Agent E (Maya - Reflection Specialist)

**Files**:
- `backend/agents/specialized/agent_e/graph.py`

**Nodes**:
1. `analyze_content_node` - Initial analysis
2. `identify_issues_node` - Find gaps/problems
3. `generate_improvements_node` - Suggest refinements
4. `finalize_reflection_node` - Synthesize insights

**SystemMessage Pattern** (Needed):
```python
"""You are Maya, a Reflection Specialist at Commander.ai.
Your role is to review content, identify issues, and suggest improvements.

Reflection process:
1. Analyze content thoroughly
2. Identify gaps, inconsistencies, or weaknesses
3. Generate specific improvement suggestions
4. Synthesize actionable recommendations

Guidelines:
- Be constructive and specific
- Highlight both strengths and weaknesses
- Suggest concrete, actionable improvements
- Consider multiple perspectives
- Prioritize most impactful changes
"""
```

**Variables Needed**:
- `{content}` - Content to reflect upon
- `{reflection_depth}` - "quick" | "standard" | "deep"
- `{focus_areas}` - Specific aspects to review
- `{output_format}` - "suggestions" | "critique" | "comparison"

### Agent F (Kai - Reflexion Specialist)

**Files**:
- `backend/agents/specialized/agent_f/graph.py`

**Nodes**:
1. `initial_reasoning_node` - First attempt at problem
2. `self_critique_node` - Evaluate own reasoning
3. `refine_reasoning_node` - Improve based on critique
4. `finalize_reflexion_node` - Final optimized solution

**SystemMessage Pattern** (Needed):
```python
"""You are Kai, a Reflexion Specialist at Commander.ai.
Your role is to solve problems through iterative self-reflection and improvement.

Reflexion process:
1. Attempt initial solution
2. Critique your own reasoning
3. Refine approach based on critique
4. Iterate until optimal solution

Guidelines:
- Be honest about limitations in initial attempts
- Identify flaws in reasoning explicitly
- Show clear improvement in iterations
- Explain why refined approach is better
- Know when to stop iterating
"""
```

**Variables Needed**:
- `{problem}` - Problem statement
- `{max_iterations}` - Maximum refinement cycles
- `{quality_threshold}` - When to stop iterating
- `{evaluation_criteria}` - How to judge solution quality

### Agent G (Chat - Interactive Assistant)

**Files**:
- `backend/agents/specialized/agent_g/llm_chat.py`

**SystemMessage Pattern** (Current):
```python
"""You are a helpful AI assistant in the Commander.ai system.
Your role is to have natural, informative conversations with users.

You have access to a web search tool for current information.
Use web_search when users ask about:
- Recent events or current news
- Information that may have changed since training
- Specific facts that need verification
- Time-sensitive information

Guidelines:
- Be conversational and friendly
- Provide clear, helpful responses
- Ask clarifying questions when needed
- Use markdown formatting
- Be concise but thorough
- Admit when you don't know something
- Use web search appropriately
"""
```

**HumanMessage Pattern**:
```python
f"""Current user message: {current_message}

[Conversation history included in AIMessage objects]
"""
```

**Agentic Loop**: Uses ToolMessage for web_search results

**Variables Needed**:
- `{current_message}` - User's latest message
- `{conversation_history}` - Previous turns
- `{personality}` - Tone adjustment ("friendly" | "professional" | "technical")
- `{max_tool_iterations}` - Tool usage limit

---

## Prompt Storage & Retrieval

### Current Implementation

**Storage**: PostgreSQL with JSONB for variables

**Retrieval Pattern**:
```python
# Get all active prompts for an agent
repo = PromptRepository(session)
prompts = await repo.get_active_prompts(agent_id="agent_a")

# Filter by type
system_prompts = [p for p in prompts if p.prompt_type == "system"]
```

**Challenges**:
1. **No integration with agent code** - Prompts in DB are not used
2. **No templating engine** - Variables field exists but unused
3. **No versioning** - Can't track prompt evolution or A/B test
4. **No performance tracking** - No link between prompts and task outcomes

### Needed Enhancements

1. **Template Engine Integration**
   - Use Jinja2 or f-strings for variable substitution
   - Support conditional blocks (if agent has tool X, include Y)
   - Nested templates (reusable prompt fragments)

2. **Prompt Versioning**
   - Track prompt changes over time
   - A/B testing infrastructure
   - Rollback to previous versions

3. **Performance Metrics**
   - Link prompts to task success/failure rates
   - Track token usage per prompt version
   - User satisfaction scoring

4. **Caching & Optimization**
   - Cache compiled templates
   - Lazy-load prompts per agent
   - Precompile common prompt patterns

---

## Dynamic Prompt Generation Strategy

### PromptEngineer Node/Tool Concept

**Purpose**: Generate optimized prompts dynamically based on:
1. **Agent context** (role, capabilities, constraints)
2. **Task requirements** (complexity, expected output, urgency)
3. **Available tools** (what the agent can actually do)
4. **User preferences** (tone, detail level, format)
5. **Historical performance** (which prompts worked well)

### Architecture Options

#### Option 1: PromptEngineer as LangGraph Node

**Integration**: Runs before main agent execution

```
User Query → PromptEngineer Node → Agent Node → Response
              ↓
        Generates optimized
        SystemMessage +
        HumanMessage
```

**Pros**:
- Full LangGraph integration
- Can use state for context
- Execution tracking built-in

**Cons**:
- Adds latency to every request
- Extra LLM call per task

#### Option 2: PromptEngineer as Standalone Tool

**Integration**: Called on-demand when needed

```
Agent Node → [Decides prompt needs optimization]
    ↓
PromptEngineer Tool → Returns optimized prompt
    ↓
Agent continues with new prompt
```

**Pros**:
- Only used when needed
- Can be invoked mid-execution
- Lower overhead

**Cons**:
- Requires agent to know when to use it
- More complex integration

#### Option 3: Pre-Execution Prompt Compilation (Recommended)

**Integration**: Compile prompts when agent initializes

```
Agent Startup → Load base prompts from DB
    ↓
PromptEngineer compiles with agent context
    ↓
Agent uses compiled prompts for all tasks
    ↓
Periodic re-compilation (hourly/daily)
```

**Pros**:
- No per-request latency
- Prompts can be cached
- Still dynamic based on agent config

**Cons**:
- Less adaptive to specific task context
- Requires restart or trigger to update

### PromptEngineer Input Schema

```python
class PromptEngineerInput(BaseModel):
    """Input for PromptEngineer"""

    # Agent context
    agent_id: str                           # "agent_a", "parent", etc.
    agent_nickname: str                     # "bob", "leo"
    agent_specialization: str               # "Research Specialist"
    agent_capabilities: list[str]           # ["web_search", "synthesis"]

    # Task context
    task_type: str                          # "research", "compliance", "chat"
    task_complexity: str                    # "simple", "moderate", "complex"
    expected_output_format: str             # "markdown", "json", "structured"

    # Tools & constraints
    available_tools: list[dict]             # Tool descriptions
    token_budget: int | None                # Max tokens for response
    response_time_target: str               # "fast", "balanced", "thorough"

    # User preferences
    tone: str                               # "friendly", "professional", "technical"
    detail_level: str                       # "brief", "standard", "comprehensive"

    # Optional overrides
    base_prompt_id: UUID | None             # Start from existing prompt
    custom_instructions: str | None         # Additional user-specific guidance
```

### PromptEngineer Output Schema

```python
class PromptEngineerOutput(BaseModel):
    """Output from PromptEngineer"""

    # Generated prompts
    system_prompt: str                      # SystemMessage content
    user_prompt_template: str               # HumanMessage template with {variables}

    # Metadata
    variables: dict[str, str]               # Required template variables
    estimated_tokens: int                   # Token count estimate
    optimization_applied: list[str]         # ["tool_descriptions_added", "tone_adjusted"]

    # Performance tracking
    prompt_version: str                     # Version identifier for A/B testing
    base_prompt_id: UUID | None             # Source prompt if derived
    generated_at: datetime                  # When compiled
```

### Prompt Generation Algorithm (Pseudocode)

```python
async def generate_optimized_prompt(input: PromptEngineerInput) -> PromptEngineerOutput:
    """
    Generate optimized prompts for an agent + task combination
    """

    # 1. Load base prompt from database
    base_prompt = await prompt_repo.get_active_prompts(input.agent_id)

    # 2. Extract agent role & capabilities
    role_description = f"You are {input.agent_nickname}, a {input.agent_specialization}"

    # 3. Build tool descriptions dynamically
    tools_section = ""
    if input.available_tools:
        tools_section = "Available tools:\n"
        for tool in input.available_tools:
            tools_section += f"- {tool['name']}: {tool['description']}\n"

    # 4. Adjust tone based on user preference
    tone_guidelines = get_tone_guidelines(input.tone)  # "friendly" → "Be warm and conversational"

    # 5. Add task-specific guidance
    task_guidance = get_task_guidance(input.task_type)  # "research" → "Cite sources, be objective"

    # 6. Format output structure instructions
    format_instructions = get_format_instructions(input.expected_output_format)

    # 7. Assemble system prompt
    system_prompt = f"""
{role_description}.
Your role is to {get_role_description(input.agent_specialization)}.

{tools_section}

Guidelines:
{tone_guidelines}
{task_guidance}
- Use {input.detail_level} level of detail
- Target response time: {input.response_time_target}

{format_instructions}

{base_prompt.prompt_text if base_prompt else ""}
{input.custom_instructions if input.custom_instructions else ""}
""".strip()

    # 8. Create user prompt template
    user_prompt_template = create_user_prompt_template(
        task_type=input.task_type,
        expected_format=input.expected_output_format
    )

    # 9. Estimate token usage
    estimated_tokens = estimate_tokens(system_prompt + user_prompt_template)

    # 10. Return compiled prompt
    return PromptEngineerOutput(
        system_prompt=system_prompt,
        user_prompt_template=user_prompt_template,
        variables=extract_variables(user_prompt_template),
        estimated_tokens=estimated_tokens,
        optimization_applied=["tone_adjusted", "tools_added", "format_specified"],
        prompt_version=generate_version_hash(system_prompt),
        base_prompt_id=base_prompt.id if base_prompt else None,
        generated_at=datetime.utcnow()
    )
```

---

## PromptEngineer Node Design

### Implementation Approach

**Recommended**: Hybrid approach combining pre-compilation with runtime flexibility

```python
class PromptEngineer:
    """
    Dynamic prompt generation service for Commander.ai agents
    """

    def __init__(self, prompt_repo: PromptRepository):
        self.prompt_repo = prompt_repo
        self.compiled_cache = {}  # Cache compiled prompts

    async def compile_agent_prompts(
        self,
        agent_id: str,
        agent_config: dict
    ) -> dict[str, str]:
        """
        Pre-compile prompts for an agent based on its configuration
        Called at agent startup or config change
        """
        # Load base prompts from database
        base_prompts = await self.prompt_repo.get_active_prompts(agent_id)

        # Compile with agent context
        compiled = {}
        for prompt in base_prompts:
            if prompt.prompt_type == "system":
                compiled["system"] = self._compile_system_prompt(
                    base_text=prompt.prompt_text,
                    agent_config=agent_config,
                    variables=prompt.variables
                )
            elif prompt.prompt_type == "human":
                compiled["human_template"] = prompt.prompt_text

        # Cache for fast retrieval
        self.compiled_cache[agent_id] = compiled

        return compiled

    async def generate_dynamic_prompt(
        self,
        agent_id: str,
        task_context: dict,
        user_query: str
    ) -> tuple[str, str]:
        """
        Generate task-specific prompts at runtime
        Uses cached compiled prompts + task context
        """
        # Get cached compiled prompts
        if agent_id not in self.compiled_cache:
            raise ValueError(f"Agent {agent_id} prompts not compiled")

        compiled = self.compiled_cache[agent_id]

        # Adapt system prompt for task
        system_prompt = self._adapt_system_prompt(
            base_system=compiled["system"],
            task_context=task_context
        )

        # Build user prompt from template
        user_prompt = self._build_user_prompt(
            template=compiled.get("human_template", ""),
            user_query=user_query,
            task_context=task_context
        )

        return system_prompt, user_prompt

    def _compile_system_prompt(
        self,
        base_text: str,
        agent_config: dict,
        variables: dict
    ) -> str:
        """Compile base prompt with agent config"""
        # Replace variables in template
        prompt = base_text

        # Add agent capabilities
        if "tools" in agent_config:
            tools_list = "\n".join([
                f"- {tool['name']}: {tool['description']}"
                for tool in agent_config["tools"]
            ])
            prompt = prompt.replace("{tools_list}", tools_list)

        # Add agent-specific variables
        for key, value in variables.items():
            prompt = prompt.replace(f"{{{key}}}", str(value))

        return prompt

    def _adapt_system_prompt(
        self,
        base_system: str,
        task_context: dict
    ) -> str:
        """Adapt compiled prompt for specific task"""
        adapted = base_system

        # Add task-specific guidance
        if task_context.get("urgency") == "high":
            adapted += "\n\nIMPORTANT: This is a high-priority task. Prioritize speed and clarity."

        # Add token budget constraint
        if "token_budget" in task_context:
            adapted += f"\n\nToken budget: {task_context['token_budget']} tokens. Be concise."

        return adapted

    def _build_user_prompt(
        self,
        template: str,
        user_query: str,
        task_context: dict
    ) -> str:
        """Build HumanMessage from template + context"""
        if not template:
            # Fallback: simple query pass-through
            return user_query

        # Replace query variable
        prompt = template.replace("{query}", user_query)

        # Add context variables
        for key, value in task_context.items():
            prompt = prompt.replace(f"{{{key}}}", str(value))

        return prompt
```

### Integration with Existing Agents

**Step 1**: Add PromptEngineer to agent initialization

```python
class ResearchAgent(Agent):
    def __init__(self, agent_id: str, nickname: str):
        super().__init__(agent_id, nickname)

        # Initialize PromptEngineer
        self.prompt_engineer = get_prompt_engineer()

        # Compile prompts at startup
        asyncio.create_task(self._compile_prompts())

    async def _compile_prompts(self):
        """Compile prompts for this agent"""
        agent_config = {
            "tools": [
                {"name": "web_search", "description": "Search the web for current information"},
                {"name": "synthesize", "description": "Combine multiple sources into coherent analysis"}
            ],
            "specialization": "Research Specialist",
            "output_formats": ["markdown", "json"]
        }

        await self.prompt_engineer.compile_agent_prompts(
            agent_id=self.agent_id,
            agent_config=agent_config
        )
```

**Step 2**: Use dynamic prompts in nodes

```python
async def research_node(state: ResearchAgentState) -> dict:
    """Research node with dynamic prompting"""

    # Get dynamic prompts from PromptEngineer
    prompt_engineer = get_prompt_engineer()

    task_context = {
        "task_type": "research",
        "complexity": "moderate",
        "expected_output": "markdown",
        "token_budget": 2000,
        "detail_level": "comprehensive"
    }

    system_prompt, user_prompt = await prompt_engineer.generate_dynamic_prompt(
        agent_id="agent_a",
        task_context=task_context,
        user_query=state["query"]
    )

    # Use generated prompts
    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=user_prompt)
    ]

    response = await llm.ainvoke(messages)

    return {"result": response.content}
```

---

## Prompt Management UI & API

### Overview

**Purpose**: Enable non-technical users and prompt engineers to manage prompts through an intuitive UI without touching code or database directly.

**Key Features**:
1. **CRUD Operations**: Create, Read, Update, Delete prompts
2. **Smart Search**: Find prompts by agent, type, keywords, performance
3. **Version History**: Track changes, rollback to previous versions
4. **Live Preview**: Test prompts before saving
5. **Performance Metrics**: See which prompts perform best
6. **A/B Testing**: Compare prompt variants side-by-side

### API Endpoints Design

**Base Path**: `/api/prompts`

#### 1. List Prompts (with Search & Filters)

```http
GET /api/prompts?agent_id=agent_a&prompt_type=system&active=true&search=research
```

**Query Parameters**:
- `agent_id` (optional): Filter by agent (e.g., "parent", "agent_a")
- `prompt_type` (optional): Filter by type ("system", "human", "ai")
- `active` (optional): Filter by active status (true/false)
- `search` (optional): Keyword search in description/prompt_text
- `limit` (optional): Max results (default: 50)
- `offset` (optional): Pagination offset (default: 0)

**Response**:
```json
{
  "prompts": [
    {
      "id": "123e4567-e89b-12d3-a456-426614174000",
      "agent_id": "agent_a",
      "nickname": "bob",
      "description": "Research synthesis system prompt",
      "prompt_text": "You are Bob, a Research Specialist...",
      "active": true,
      "prompt_type": "system",
      "variables": {"max_sources": "5", "output_style": "comprehensive"},
      "created_at": "2026-02-06T10:00:00Z",
      "updated_at": "2026-02-06T15:30:00Z",
      "performance_metrics": {
        "usage_count": 142,
        "success_rate": 0.94,
        "avg_tokens": 1850,
        "avg_response_time_ms": 3200
      }
    }
  ],
  "total": 1,
  "limit": 50,
  "offset": 0
}
```

#### 2. Get Single Prompt (with Version History)

```http
GET /api/prompts/{prompt_id}?include_versions=true
```

**Response**:
```json
{
  "prompt": {
    "id": "123e4567-e89b-12d3-a456-426614174000",
    "agent_id": "agent_a",
    "nickname": "bob",
    "description": "Research synthesis system prompt",
    "prompt_text": "You are Bob, a Research Specialist...",
    "active": true,
    "prompt_type": "system",
    "variables": {"max_sources": "5"},
    "created_at": "2026-02-06T10:00:00Z",
    "updated_at": "2026-02-06T15:30:00Z"
  },
  "versions": [
    {
      "version": 3,
      "prompt_text": "You are Bob, a Research Specialist...",
      "changed_by": "user@example.com",
      "changed_at": "2026-02-06T15:30:00Z",
      "change_note": "Added emphasis on citing sources"
    },
    {
      "version": 2,
      "prompt_text": "You are Bob, Research Specialist...",
      "changed_by": "user@example.com",
      "changed_at": "2026-02-05T14:20:00Z",
      "change_note": "Improved tone guidelines"
    }
  ]
}
```

#### 3. Create New Prompt

```http
POST /api/prompts
```

**Request Body**:
```json
{
  "agent_id": "agent_a",
  "nickname": "bob",
  "description": "New research prompt for technical documentation",
  "prompt_text": "You are Bob, a Research Specialist focusing on technical documentation...",
  "active": true,
  "prompt_type": "system",
  "variables": {
    "documentation_type": "API",
    "detail_level": "comprehensive"
  }
}
```

**Response**: Created prompt object (same as GET single prompt)

#### 4. Update Existing Prompt

```http
PATCH /api/prompts/{prompt_id}
```

**Request Body**:
```json
{
  "prompt_text": "Updated prompt text...",
  "active": true,
  "variables": {"max_sources": "10"},
  "change_note": "Increased max sources from 5 to 10 for better coverage"
}
```

**Response**: Updated prompt object

#### 5. Delete Prompt (Soft Delete)

```http
DELETE /api/prompts/{prompt_id}
```

**Response**:
```json
{
  "message": "Prompt deactivated successfully",
  "prompt_id": "123e4567-e89b-12d3-a456-426614174000"
}
```

**Note**: Soft delete (sets `active=false`) to preserve version history

#### 6. Test Prompt (Live Preview)

```http
POST /api/prompts/test
```

**Request Body**:
```json
{
  "agent_id": "agent_a",
  "prompt_text": "You are Bob, a Research Specialist...",
  "prompt_type": "system",
  "test_query": "Research quantum computing applications",
  "test_context": {
    "task_type": "research",
    "expected_output": "markdown"
  }
}
```

**Response**:
```json
{
  "generated_response": "# Quantum Computing Applications\n\n...",
  "metrics": {
    "prompt_tokens": 250,
    "completion_tokens": 420,
    "total_tokens": 670,
    "response_time_ms": 2800
  },
  "compiled_messages": [
    {
      "role": "system",
      "content": "You are Bob, a Research Specialist..."
    },
    {
      "role": "user",
      "content": "Research quantum computing applications"
    }
  ]
}
```

#### 7. Clone Prompt (Create Variant)

```http
POST /api/prompts/{prompt_id}/clone
```

**Request Body**:
```json
{
  "description": "Variant for faster responses",
  "modifications": {
    "prompt_text": "Modified version...",
    "variables": {"detail_level": "brief"}
  }
}
```

**Response**: New prompt object (cloned with modifications)

#### 8. Get Prompt Performance Metrics

```http
GET /api/prompts/{prompt_id}/metrics?days=30
```

**Response**:
```json
{
  "prompt_id": "123e4567-e89b-12d3-a456-426614174000",
  "time_period": "30 days",
  "metrics": {
    "total_uses": 450,
    "success_rate": 0.94,
    "avg_tokens": {
      "prompt": 250,
      "completion": 1600,
      "total": 1850
    },
    "avg_response_time_ms": 3200,
    "user_satisfaction": 4.2,
    "comparison_to_baseline": {
      "tokens_saved": 120,
      "response_time_improvement_ms": -400
    }
  },
  "usage_over_time": [
    {"date": "2026-02-01", "uses": 15, "success_rate": 0.93},
    {"date": "2026-02-02", "uses": 18, "success_rate": 0.95}
  ]
}
```

### UI Design (Mission Control Integration)

#### Modal-Based Prompt Editor

**Location**: Accessible from Mission Control → Agent Panel → Agent Card → "⚙️ Manage Prompts"

**Modal Layout**:

```
┌────────────────────────────────────────────────────────────┐
│  Manage Prompts - @bob (Research Specialist)           [X] │
├────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────────────────────────────────────────────┐  │
│  │ 🔍 Search prompts...                    [+ New]     │  │
│  └─────────────────────────────────────────────────────┘  │
│                                                             │
│  Filters: [All Types ▼] [Active Only ☑] [Sort: Recent ▼]  │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐  │
│  │ 📝 Research Synthesis System Prompt         [Edit]  │  │
│  │ Type: System  |  Active: ✓  |  Uses: 142           │  │
│  │ Last updated: Feb 6, 2026 3:30 PM                  │  │
│  │ Performance: 94% success  |  1,850 avg tokens      │  │
│  │                                                      │  │
│  │ You are Bob, a Research Specialist at Commander...  │  │
│  │ [Show full prompt ▼]                                │  │
│  ├─────────────────────────────────────────────────────┤  │
│  │ 📝 Quick Research Prompt (Brief)            [Edit]  │  │
│  │ Type: System  |  Active: ✓  |  Uses: 67            │  │
│  │ Last updated: Feb 5, 2026 10:15 AM                 │  │
│  │ Performance: 91% success  |  980 avg tokens        │  │
│  ├─────────────────────────────────────────────────────┤  │
│  │ 📝 Technical Documentation Research         [Edit]  │  │
│  │ Type: System  |  Inactive                           │  │
│  │ Last updated: Jan 28, 2026 2:45 PM                 │  │
│  └─────────────────────────────────────────────────────┘  │
│                                                             │
│  Showing 3 of 5 prompts                    [Load More...]  │
│                                                             │
└────────────────────────────────────────────────────────────┘
```

#### Prompt Editor Modal

**Opened when**: Click "Edit" or "+ New"

```
┌────────────────────────────────────────────────────────────┐
│  Edit Prompt: Research Synthesis System Prompt        [X]  │
├────────────────────────────────────────────────────────────┤
│                                                             │
│  Description:                                               │
│  ┌─────────────────────────────────────────────────────┐  │
│  │ Research synthesis system prompt                    │  │
│  └─────────────────────────────────────────────────────┘  │
│                                                             │
│  Prompt Type: [System Message ▼]                           │
│                                                             │
│  Prompt Text:                         [🔍 Test] [📊 Perf]  │
│  ┌─────────────────────────────────────────────────────┐  │
│  │ You are Bob, a Research Specialist at Commander.ai. │  │
│  │ Your role is to synthesize information from         │  │
│  │ multiple sources into clear, comprehensive...       │  │
│  │                                                      │  │
│  │ Guidelines:                                          │  │
│  │ - Provide well-structured analysis                  │  │
│  │ - Cite key findings from sources                    │  │
│  │ ...                                                  │  │
│  │                                                      │  │
│  │ [20 lines tall, scrollable]                         │  │
│  └─────────────────────────────────────────────────────┘  │
│                                                             │
│  Variables (Template Placeholders):                         │
│  ┌─────────────────────────────────────────────────────┐  │
│  │ max_sources: 5                              [+ Add] │  │
│  │ output_style: comprehensive                         │  │
│  │ detail_level: standard                              │  │
│  └─────────────────────────────────────────────────────┘  │
│                                                             │
│  Active: [✓] Enable this prompt                            │
│                                                             │
│  Change Note (optional):                                    │
│  ┌─────────────────────────────────────────────────────┐  │
│  │ Improved citation guidelines                        │  │
│  └─────────────────────────────────────────────────────┘  │
│                                                             │
│  [Cancel]  [Save Draft]  [Save & Activate]                 │
│                                                             │
└────────────────────────────────────────────────────────────┘
```

#### Test Prompt Modal

**Opened when**: Click "🔍 Test" button

```
┌────────────────────────────────────────────────────────────┐
│  Test Prompt                                           [X]  │
├────────────────────────────────────────────────────────────┤
│                                                             │
│  Test Query:                                                │
│  ┌─────────────────────────────────────────────────────┐  │
│  │ Research quantum computing applications             │  │
│  └─────────────────────────────────────────────────────┘  │
│                                                             │
│  Test Context (optional):                                   │
│  Task Type: [Research ▼]  Output: [Markdown ▼]            │
│                                                             │
│  [Run Test]                                                 │
│                                                             │
│  ───────────────────────── Results ─────────────────────── │
│                                                             │
│  ⚡ Response Time: 2.8s  |  📊 Tokens: 670 (250 + 420)     │
│                                                             │
│  Generated Response:                                        │
│  ┌─────────────────────────────────────────────────────┐  │
│  │ # Quantum Computing Applications                    │  │
│  │                                                      │  │
│  │ Quantum computing represents a paradigm shift...    │  │
│  │                                                      │  │
│  │ [Scrollable preview]                                │  │
│  └─────────────────────────────────────────────────────┘  │
│                                                             │
│  Compiled Messages (Debug):            [Show Details ▼]    │
│                                                             │
│  [Close]                                                    │
│                                                             │
└────────────────────────────────────────────────────────────┘
```

#### Performance Dashboard Modal

**Opened when**: Click "📊 Perf" button

```
┌────────────────────────────────────────────────────────────┐
│  Prompt Performance - Last 30 Days                     [X]  │
├────────────────────────────────────────────────────────────┤
│                                                             │
│  Overall Metrics:                                           │
│  ┌──────────────┬──────────────┬──────────────┬──────────┐│
│  │ 450 Uses     │ 94% Success  │ 1,850 Tokens │ 3.2s     ││
│  │              │              │ (avg)        │ (avg)    ││
│  └──────────────┴──────────────┴──────────────┴──────────┘│
│                                                             │
│  Usage Over Time:                                           │
│  ┌─────────────────────────────────────────────────────┐  │
│  │         📈 Line chart showing daily usage           │  │
│  │                                                      │  │
│  │  [Chart visualization]                               │  │
│  │                                                      │  │
│  └─────────────────────────────────────────────────────┘  │
│                                                             │
│  Success Rate Trend:                                        │
│  ┌─────────────────────────────────────────────────────┐  │
│  │         📊 Bar chart showing daily success rate     │  │
│  │                                                      │  │
│  │  [Chart visualization]                               │  │
│  │                                                      │  │
│  └─────────────────────────────────────────────────────┘  │
│                                                             │
│  Comparison to Baseline:                                    │
│  • Tokens saved: 120 per request (-6%)                     │
│  • Response time improved: 400ms faster                     │
│  • Success rate: +2.5% vs previous version                 │
│                                                             │
│  [Export Data]  [Close]                                     │
│                                                             │
└────────────────────────────────────────────────────────────┘
```

### Frontend Component Structure

**New Components** (to create):

```
frontend/components/prompt-management/
├── prompt-list-modal.tsx              # Main modal with search & list
├── prompt-editor-modal.tsx            # Create/Edit prompt modal
├── prompt-test-modal.tsx              # Test prompt with live preview
├── prompt-performance-modal.tsx       # Performance metrics dashboard
├── prompt-card.tsx                    # Individual prompt card in list
├── prompt-variable-editor.tsx         # Variables (key-value) editor
└── index.ts                           # Barrel export
```

**State Management**:

```typescript
// lib/hooks/use-prompts.ts
export function usePrompts(agentId?: string) {
  const [prompts, setPrompts] = useState<AgentPrompt[]>([]);
  const [isLoading, setIsLoading] = useState(false);

  const fetchPrompts = async (filters?: PromptFilters) => {
    // GET /api/prompts with filters
  };

  const createPrompt = async (data: PromptCreate) => {
    // POST /api/prompts
  };

  const updatePrompt = async (id: UUID, data: PromptUpdate) => {
    // PATCH /api/prompts/{id}
  };

  const testPrompt = async (data: PromptTestRequest) => {
    // POST /api/prompts/test
  };

  return { prompts, isLoading, fetchPrompts, createPrompt, updatePrompt, testPrompt };
}
```

### User Workflows

#### Workflow 1: Create New Prompt

1. User clicks agent card → "⚙️ Manage Prompts"
2. Click "+ New" button
3. Fill in description, prompt text, variables
4. Click "🔍 Test" to preview response
5. Iterate on prompt based on test results
6. Click "Save & Activate"
7. Prompt immediately available to PromptEngineer

#### Workflow 2: Tune Existing Prompt

1. User clicks agent card → "⚙️ Manage Prompts"
2. Search for relevant prompt (e.g., "synthesis")
3. Click "Edit" on prompt card
4. Modify prompt text (e.g., add emphasis on citations)
5. Add change note: "Improved citation guidelines"
6. Test changes with sample query
7. Compare performance metrics before/after
8. Save changes
9. Monitor performance dashboard over next few days

#### Workflow 3: A/B Test Prompt Variants

1. Find high-performing prompt
2. Click "Clone" to create variant
3. Modify variant (e.g., more concise version)
4. Activate both prompts
5. PromptEngineer randomly selects between variants
6. After 100+ uses, compare metrics
7. Deactivate lower-performing variant
8. Iterate on winner

### Database Schema Extensions

**New Tables for Version History & Metrics**:

```sql
-- Prompt version history
CREATE TABLE prompt_versions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    prompt_id UUID NOT NULL REFERENCES agent_prompts(id) ON DELETE CASCADE,
    version INT NOT NULL,
    prompt_text TEXT NOT NULL,
    variables JSONB NOT NULL DEFAULT '{}',
    changed_by VARCHAR(255),
    changed_at TIMESTAMP NOT NULL DEFAULT NOW(),
    change_note TEXT
);

CREATE INDEX idx_prompt_versions_prompt_id ON prompt_versions(prompt_id);

-- Prompt usage metrics
CREATE TABLE prompt_metrics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    prompt_id UUID NOT NULL REFERENCES agent_prompts(id) ON DELETE CASCADE,
    task_id UUID NOT NULL,
    success BOOLEAN NOT NULL,
    prompt_tokens INT NOT NULL,
    completion_tokens INT NOT NULL,
    total_tokens INT NOT NULL,
    response_time_ms INT NOT NULL,
    user_feedback INT,  -- 1-5 star rating (optional)
    recorded_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_prompt_metrics_prompt_id ON prompt_metrics(prompt_id);
CREATE INDEX idx_prompt_metrics_recorded_at ON prompt_metrics(recorded_at);
```

### Implementation Priority

**Phase 1: API Foundation** ✅
- Create REST API endpoints (CRUD operations)
- Add version history tracking
- Implement search & filtering

**Phase 2: Basic UI** ✅
- Prompt list modal with search
- Prompt editor modal (create/edit)
- Integration with agent panel

**Phase 3: Testing & Metrics** ✅
- Test prompt functionality
- Performance dashboard
- Metrics collection integration

**Phase 4: Advanced Features** 🔮
- A/B testing infrastructure
- Prompt cloning/variants
- Auto-optimization suggestions

---

## Next Steps

### Phase 1: Foundation (Week 1)
- [x] Document current prompt architecture ← **YOU ARE HERE**
- [ ] Create PromptEngineer base class
- [ ] Implement prompt compilation logic
- [ ] Add prompt caching mechanism
- [ ] Unit tests for prompt generation

### Phase 2: Database Integration (Week 2)
- [ ] Seed database with existing prompts
- [ ] Add prompt versioning to schema
- [ ] Create prompt management API endpoints
- [ ] Build admin UI for prompt editing

### Phase 3: Agent Integration (Week 3)
- [ ] Integrate PromptEngineer with Parent Agent
- [ ] Integrate with Agent A (Bob)
- [ ] Integrate with Agent G (Chat)
- [ ] Add execution metrics tracking

### Phase 4: Optimization & Testing (Week 4)
- [ ] A/B testing infrastructure
- [ ] Performance metrics dashboard
- [ ] Prompt optimization recommendations
- [ ] Load testing with dynamic prompts

### Phase 5: Advanced Features (Future)
- [ ] Multi-language prompt support
- [ ] Prompt inheritance (base → specialized)
- [ ] Auto-optimization using LLM feedback
- [ ] Prompt marketplace/sharing

---

## Key Design Principles

1. **Agent-Centric**: Prompts must reflect each agent's unique role and capabilities
2. **Context-Aware**: Task complexity, urgency, and user preferences inform prompt generation
3. **Performance-Driven**: Track which prompts produce best results, iterate accordingly
4. **Maintainable**: Centralized prompt management, not scattered across codebase
5. **Flexible**: Easy to experiment, A/B test, and optimize without code changes
6. **Traceable**: Link prompts to task outcomes for continuous improvement

---

**End of Document**
