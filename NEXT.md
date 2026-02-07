# NEXT: Agent Intelligence & Performance System (v0.5.0)

**Vision**: Build ecosystem intelligence that learns which agents, models, and approaches work best for different tasks.

**Status**: Planning / Design Phase
**Branch Strategy**: Feature branch recommended (`feature/agent-performance-system`)
**Estimated Timeline**: 3-4 weeks

---

## Core Concept

Multi-level performance tracking with rewards/penalties system to optimize agent selection, model usage, and task routing.

### Measurement Dimensions

1. **Task Execution Metrics** (already captured via `execution_tracker.py`)
   - Tokens, LLM calls, tool calls, duration, nodes executed

2. **Outcome Quality** (NEW)
   - Accuracy, relevance, completeness, efficiency scores (0-1 scale)
   - User feedback (star rating + optional comments)
   - Peer evaluations (Kai + Maya review agent outputs)

3. **Agent Capabilities Profile** (NEW)
   - Task-specific performance (research, analysis, writing, etc.)
   - Model performance (which models work best for which agents)
   - Node performance (which nodes within agents perform best)

---

## Database Schema

### New Tables (PostgreSQL)

```sql
-- Core performance tracking
CREATE TABLE agent_performance_scores (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    task_id UUID REFERENCES agent_tasks(id),
    agent_id VARCHAR(50) NOT NULL,

    -- Objective Classification
    objective_category VARCHAR(50),  -- 'research', 'analysis', 'writing', etc.
    task_complexity INTEGER,         -- 1-5 scale

    -- Quality Scores (0-1 scale)
    accuracy_score DECIMAL(3,2),
    relevance_score DECIMAL(3,2),
    completeness_score DECIMAL(3,2),
    efficiency_score DECIMAL(3,2),
    overall_score DECIMAL(3,2),      -- Weighted average

    -- User Feedback
    user_rating INTEGER,             -- 1-5 stars
    user_feedback TEXT,              -- User's optional comment
    user_id UUID,

    -- Cost Metrics
    total_tokens INTEGER,
    estimated_cost DECIMAL(10,6),
    cost_per_quality_point DECIMAL(10,6),  -- cost / overall_score

    -- Execution Metadata
    model_used VARCHAR(100),
    temperature FLOAT,
    duration_seconds DECIMAL(10,2),

    created_at TIMESTAMP NOT NULL DEFAULT NOW(),

    INDEX idx_agent_objective (agent_id, objective_category),
    INDEX idx_task_scores (task_id, overall_score)
);

-- Peer evaluations (agents rating each other)
CREATE TABLE agent_peer_evaluations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    task_id UUID REFERENCES agent_tasks(id),
    evaluated_agent_id VARCHAR(50) NOT NULL,
    evaluator_agent_id VARCHAR(50) NOT NULL,

    evaluation_score DECIMAL(3,2),   -- 0-1 scale
    evaluation_feedback TEXT,        -- Evaluator's notes (saved for future NLP analysis)
    evaluation_criteria JSONB,       -- {"clarity": 0.9, "depth": 0.8, ...}

    created_at TIMESTAMP NOT NULL DEFAULT NOW(),

    INDEX idx_evaluations (evaluated_agent_id, evaluator_agent_id)
);

-- Node-level performance (within agents)
CREATE TABLE agent_node_performance (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    task_id UUID REFERENCES agent_tasks(id),
    agent_id VARCHAR(50) NOT NULL,
    node_name VARCHAR(100) NOT NULL,

    -- Node Metrics
    execution_time_seconds DECIMAL(10,2),
    tokens_used INTEGER,
    success BOOLEAN,
    error_message TEXT,

    -- Quality (if evaluable)
    output_quality_score DECIMAL(3,2),

    created_at TIMESTAMP NOT NULL DEFAULT NOW(),

    INDEX idx_node_performance (agent_id, node_name)
);

-- Aggregated agent statistics (updated hourly via scheduled job)
CREATE TABLE agent_performance_stats (
    agent_id VARCHAR(50) PRIMARY KEY,
    nickname VARCHAR(50) NOT NULL,

    -- Agent Lifecycle
    created_at TIMESTAMP NOT NULL,   -- When agent was first deployed
    days_active INTEGER,              -- Age of agent (for probation/maturity)

    -- Overall Stats
    total_tasks INTEGER DEFAULT 0,
    successful_tasks INTEGER DEFAULT 0,
    failed_tasks INTEGER DEFAULT 0,
    avg_overall_score DECIMAL(3,2),
    avg_user_rating DECIMAL(3,2),

    -- Cost Efficiency
    total_cost DECIMAL(10,2),
    avg_cost_per_task DECIMAL(10,6),
    cost_efficiency_score DECIMAL(3,2),  -- Quality per dollar

    -- Speed
    avg_duration_seconds DECIMAL(10,2),

    -- Task Category Performance (JSONB for flexibility)
    category_performance JSONB,  -- {"research": {"count": 100, "avg_score": 0.87}, ...}

    -- Model Performance (track when LLM changes affect performance)
    model_performance JSONB,     -- {"gpt-4o": {"count": 50, "avg_score": 0.90, "since": "2026-02-01"}, ...}

    -- Rankings
    overall_rank INTEGER,
    category_ranks JSONB,        -- {"research": 1, "analysis": 3, ...}

    last_updated TIMESTAMP NOT NULL DEFAULT NOW()
);

-- Objective templates (for classifying tasks)
CREATE TABLE objective_templates (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    category VARCHAR(50) NOT NULL UNIQUE,
    description TEXT,
    evaluation_criteria JSONB,   -- What makes a good response for this category
    recommended_agents VARCHAR[] -- ["agent_a", "agent_e"]
);
```

**Note on Cost**: The `approved_models_provider` table (v0.4.0) already has `cost_per_1k_input` and `cost_per_1k_output` fields. We'll use these to calculate `estimated_cost` based on total token counts.

---

## Measurement & Collection Points

### 1. Task Completion Hook
**Location**: `backend/core/execution_tracker.py`

Add `on_task_complete()` method:
- Calculate efficiency scores
- Auto-evaluate output quality (LLM-based)
- Store performance record to `agent_performance_scores`

### 2. User Feedback Widget (NEW)
**Location**: `frontend/components/mission-control/task-feedback-widget.tsx`

After task completes, show optional rating widget:
- 1-5 star rating
- Optional text feedback
- "Skip" button (not required)

### 3. Peer Evaluation Job (NEW)
**Location**: `backend/jobs/peer_evaluation.py`

Background job triggered after task completion:
- Kai (critical analysis) evaluates accuracy, depth, clarity
- Maya (holistic reflection) evaluates relevance, completeness, usefulness
- Store evaluations with full feedback text (for future NLP analysis)

### 4. Node-Level Tracking
**Location**: `backend/core/execution_tracker.py` (already captures this)

Use existing `on_chain_start()` and `on_chain_end()` callbacks:
- Store node execution time, tokens, success/failure
- Save to `agent_node_performance` table

---

## Scoring & Rewards System

### Reward Calculation

```python
class RewardSystem:
    """Gamification for agent optimization"""

    REWARD_WEIGHTS = {
        "task_completion": 10,     # Base points for completing task
        "quality_bonus": 50,       # Up to 50 points for quality (0-1 score * 50)
        "speed_bonus": 20,         # Fast execution bonus
        "cost_efficiency": 30,     # Low cost bonus
        "user_satisfaction": 40,   # User rating * 8
        "peer_recognition": 25,    # Peer eval score * 25
    }

    def calculate_reward(self, task, scores) -> int:
        """Calculate total reward points"""
        reward = 0

        # Base completion
        reward += self.REWARD_WEIGHTS["task_completion"]

        # Quality bonus (0-50 points)
        reward += scores.overall * self.REWARD_WEIGHTS["quality_bonus"]

        # Speed bonus (inverse of duration, capped)
        speed_score = min(1.0, 10 / task.duration_seconds)
        reward += speed_score * self.REWARD_WEIGHTS["speed_bonus"]

        # Cost efficiency
        reward += scores.efficiency * self.REWARD_WEIGHTS["cost_efficiency"]

        # User satisfaction (if rated)
        if task.user_rating:
            reward += (task.user_rating / 5.0) * self.REWARD_WEIGHTS["user_satisfaction"]

        # Peer recognition (average peer eval)
        if task.peer_evaluations:
            avg_peer = sum(e.score for e in task.peer_evaluations) / len(task.peer_evaluations)
            reward += avg_peer * self.REWARD_WEIGHTS["peer_recognition"]

        return int(reward)

    def calculate_penalties(self, task) -> int:
        """Deduct points for poor performance"""
        penalty = 0

        # Failed tasks
        if task.status == "FAILED":
            penalty += 30

        # Excessive cost (> $0.50)
        if task.estimated_cost > 0.50:
            penalty += int((task.estimated_cost - 0.50) * 100)

        # Timeout (> 2 minutes)
        if task.duration_seconds > 120:
            penalty += int((task.duration_seconds - 120) / 10)

        # Poor user rating (< 3 stars)
        if task.user_rating and task.user_rating < 3:
            penalty += (3 - task.user_rating) * 15

        return penalty
```

---

## Visualization & UI

### Toggle Panel (Right Side)

**Current**: Quick Actions Panel
**New**: Toggle between Quick Actions and Agent Leaderboard

```typescript
// mission-control-layout.tsx
const [rightPanel, setRightPanel] = useState<'actions' | 'leaderboard'>('actions');

// Toggle button in header
<button onClick={() => setRightPanel(prev => prev === 'actions' ? 'leaderboard' : 'actions')}>
  {rightPanel === 'actions' ? <BarChart3 /> : <Zap />}
</button>

// Conditional rendering
{rightPanel === 'actions' && <QuickActionsPanel />}
{rightPanel === 'leaderboard' && <AgentLeaderboardPanel />}
```

### Agent Leaderboard Panel (NEW)

**Location**: `frontend/components/mission-control/agent-leaderboard-panel.tsx`

Features:
- View selector: Overall / Research / Analysis / Cost Efficiency
- Rank badges (gold/silver/bronze for top 3)
- Agent metrics: Points, avg score, task count
- Trend indicators (up/down/stable week-over-week)
- Score bars (visual representation of performance)

### Task Feedback Widget (NEW)

**Location**: `frontend/components/mission-control/task-feedback-widget.tsx`

Appears after task completion:
- 5-star rating system
- Optional text feedback
- Submit or Skip buttons
- Dismissible (doesn't block workflow)

### Agent Performance Charts (NEW)

**Location**: `frontend/components/mission-control/agent-performance-chart.tsx`

Added to agent settings modal:
- Line chart: Score over time (30-day trend)
- Category breakdown: Performance by task type
- Model comparison: Which models work best for this agent

---

## Intelligent Routing (Leo's Enhancement)

### Agent Selection Algorithm

**Location**: `backend/agents/parent_agent/intelligent_router.py` (NEW)

Leo uses historical performance to select best agent for each task:

```python
async def select_best_agent(
    task_description: str,
    objective_category: str,
    constraints: dict = None
) -> str:
    """
    Select optimal agent based on performance history

    Args:
        task_description: What the user wants
        objective_category: "research", "analysis", etc.
        constraints: {"max_cost": 0.10, "max_duration": 30}

    Returns:
        agent_id of best agent
    """

    # 1. Get all agents capable of this objective
    capable_agents = await self._get_capable_agents(objective_category)

    # 2. Score each agent based on historical performance
    scores = {}
    for agent_id in capable_agents:
        score = await self._score_agent_for_task(
            agent_id=agent_id,
            objective_category=objective_category,
            constraints=constraints
        )
        scores[agent_id] = score

    # 3. Check current load (don't overload high performers)
    for agent_id in scores:
        load_penalty = await self._get_load_penalty(agent_id)
        scores[agent_id] *= (1 - load_penalty)

    # 4. Select best
    best_agent = max(scores.items(), key=lambda x: x[1])[0]

    # 5. Log decision (save for future transparency/NLP analysis)
    await self._log_routing_decision(
        task=task_description,
        selected=best_agent,
        scores=scores,
        timestamp=datetime.utcnow()
    )

    return best_agent
```

**Note**: Not showing routing reasoning to users yet, but capturing all data (task, scores, reasoning, timestamp) for future NLP-based transparency.

---

## Design Decisions (Based on Your Feedback)

### 1. Privacy & Visibility
**Decision**: ALL agent scores are public within Mission Control
- **Rationale**: This is performance metrics, not PII/PCI data
- **Implementation**: No access controls on leaderboard endpoints

### 2. Gaming Prevention
**Decision**: No special measures for gaming prevention
- **Rationale**: Trust the system design to be fair
- **Note**: Monitor during beta for unexpected behavior

### 3. Cold Start Problem
**Decision**: Track agent age and add "probation" period
- **Implementation**:
  - Add `created_at` and `days_active` to `agent_performance_stats`
  - Display agent age in UI (e.g., "🆕 New Agent" badge if < 7 days old)
  - Maybe add `probation_status` field (monitoring duration of metrics)
- **Start Simple**: Just show creation date initially

### 4. Recent vs Historical Performance
**Decision**: Start simple, but track model changes
- **Implementation**:
  - Track when LLM model changes in `model_performance` JSONB
  - Store `since` timestamp for each model
  - Compare performance before/after model change
- **Future**: Weight recent performance more heavily (e.g., 70% last 30 days, 30% older)

### 5. Routing Transparency
**Decision**: Not yet, but capture all data for future NLP analysis
- **Implementation**:
  - Save all routing decisions with full context (task, scores, reasoning, timestamp)
  - Store agent notes and user feedback as TEXT (not processed yet)
  - Future: NLP analysis of aggregated feedback to build "memories" and legacy risk views
- **Example Use Case**: "Bad memories made by agents about agents" - detect patterns in peer evaluations

### 6. Cost vs Quality Balance
**Decision**: Use existing cost structure from `approved_models_provider` table
- **Implementation**:
  - Calculate total cost from `cost_per_1k_input * (input_tokens / 1000) + cost_per_1k_output * (output_tokens / 1000)`
  - Add total token count tracking (on the todo list)
  - Calculate `cost_per_quality_point` = `total_cost / overall_score`
- **Verification**: Check v0.4.0 schema has cost fields (yes: `cost_per_1k_input`, `cost_per_1k_output`)

---

## Implementation Phases

### Phase 1: Foundation (Week 1)
**Goal**: Basic performance tracking and data collection

**Tasks**:
- [ ] Create database migrations for 4 new tables
- [ ] Extend `ExecutionTracker` with `on_task_complete()` method
- [ ] Build `PerformanceRepository` (CRUD for performance tables)
- [ ] Create Task Feedback Widget component
- [ ] Add API endpoint: `POST /api/tasks/{id}/feedback` (user rating)
- [ ] Simple leaderboard API: `GET /api/agents/leaderboard`

**Deliverable**: Performance data starts collecting, users can rate tasks

---

### Phase 2: Evaluation Engine (Week 2)
**Goal**: Auto-scoring and peer evaluation

**Tasks**:
- [ ] Build `PerformanceEvaluator` class (auto-scoring algorithms)
- [ ] Implement LLM-based quality evaluation (accuracy, relevance, completeness)
- [ ] Create `PeerEvaluationJob` (Kai + Maya review outputs)
- [ ] Build `RewardSystem` class (calculate rewards/penalties)
- [ ] Add scheduled job: Hourly stats aggregation
- [ ] Calculate and store rankings

**Deliverable**: Every completed task gets auto-evaluated and scored

---

### Phase 3: Intelligence Layer (Week 3)
**Goal**: Intelligent routing and recommendations

**Tasks**:
- [ ] Build `IntelligentRouter` for Leo
- [ ] Implement agent selection algorithm (performance-based)
- [ ] Add objective category classification (research, analysis, etc.)
- [ ] Track routing decisions (log for future analysis)
- [ ] Build performance trend analysis
- [ ] Add agent capability profiles

**Deliverable**: Leo selects agents based on performance history

---

### Phase 4: Visualization (Week 4)
**Goal**: UI for leaderboards and performance insights

**Tasks**:
- [ ] Build `AgentLeaderboardPanel` component
- [ ] Add toggle button for Quick Actions ↔ Leaderboard
- [ ] Create `AgentPerformanceChart` component (line charts)
- [ ] Add performance badges to agent tiles (rank, trend)
- [ ] Build view selector (Overall / Research / Analysis / Cost)
- [ ] Add agent-specific dashboard (Settings modal → Performance tab)

**Deliverable**: Full leaderboard UI with charts and insights

---

### Phase 5: Polish & Optimization (Optional)
**Goal**: Refinements based on real usage

**Tasks**:
- [ ] A/B testing for scoring weights
- [ ] Performance-based auto-tuning recommendations
- [ ] Alerting for performance degradation
- [ ] Export leaderboard data (CSV/JSON)
- [ ] Add filters (date range, category, model)

**Deliverable**: Production-ready performance system

---

## Branching Strategy

### Recommendation: Feature Branch

**Branch Name**: `feature/agent-performance-system`

**Rationale**:
- Fair amount of moving pieces (4 new tables, multiple components, background jobs)
- Want to test thoroughly before merging to main
- Allows incremental commits without breaking main
- Can deploy to staging environment for validation

**Workflow**:
```bash
# Create feature branch from main
git checkout main
git pull origin main
git checkout -b feature/agent-performance-system

# Work in phases, commit frequently
git add .
git commit -m "feat(perf): Phase 1 - Database schema and performance tracking"

# Push to remote for backup/collaboration
git push -u origin feature/agent-performance-system

# When ready, create PR to main
gh pr create --title "feat: Agent Intelligence & Performance System (v0.5.0)" \
  --body "Implements multi-level performance tracking, rewards system, and leaderboards"

# After review and testing, merge to main
```

**Alternative**: If you prefer trunk-based development, use feature flags to hide incomplete features.

---

## Testing Strategy

### Unit Tests
- `test_performance_evaluator.py` - Scoring algorithms
- `test_reward_system.py` - Reward/penalty calculation
- `test_intelligent_router.py` - Agent selection logic
- `test_performance_repository.py` - Database operations

### Integration Tests
- End-to-end task flow with performance tracking
- User feedback submission
- Peer evaluation job execution
- Leaderboard ranking accuracy

### Manual Testing
- Submit various tasks, rate them, verify scores
- Check leaderboard updates in real-time
- Test toggle between Quick Actions and Leaderboard
- Verify agent selection improves over time

---

## Open Questions for Discussion

1. **Peer Evaluation Frequency**: Should Kai/Maya review every task, or sample (e.g., 20%)?
2. **User Feedback Incentives**: Should we incentivize users to rate tasks? (e.g., "Rate 5 tasks, unlock advanced features")
3. **Probation Period**: How long should "new agent" probation last? 7 days? 30 days? 50 tasks?
4. **Ranking Algorithm**: Weighted average of recent (70%) + historical (30%), or pure cumulative?
5. **Cost Alerting**: Should we alert if an agent's avg cost suddenly spikes?
6. **Performance Reports**: Weekly email summaries of agent performance?

---

## Success Metrics (How We Know It's Working)

1. **Routing Accuracy**: Leo's agent selection success rate > 85%
2. **User Engagement**: >50% of tasks get user ratings
3. **Quality Improvement**: Avg overall_score increases month-over-month
4. **Cost Efficiency**: Cost per quality point decreases over time
5. **Speed**: Avg task duration decreases as agents optimize

---

## Future Enhancements (Post v0.5.0)

- **NLP Analysis**: Process aggregated feedback to identify patterns ("Bob is great at research but slow")
- **Agent Memories**: Store "legacy risk views" (bad memories agents have about each other)
- **Auto-Tuning**: Automatically adjust temperature/max_tokens based on performance
- **Multi-Model Orchestration**: Leo dynamically assigns different models within same task
- **User Personas**: Track which agents work best for which users
- **Real-Time Dashboards**: Live performance metrics during task execution

---

**Next Steps**:

1. **Review this plan** - Does the scope feel right? Anything missing?
2. **Create feature branch** - `git checkout -b feature/agent-performance-system`
3. **Start Phase 1** - Database schema and basic tracking
4. **Iterate based on data** - Real usage will inform what matters most

Ready to start building when you are! 🚀
