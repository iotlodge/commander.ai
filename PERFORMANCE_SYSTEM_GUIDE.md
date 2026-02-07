# Performance System - Operator's Guide

**Master reference for commander.ai's intelligent performance, evaluation, and reward system**

This guide covers the entire ecosystem intelligence layer built across Phases 1-3, showing you how to monitor, tune, and optimize agent performance in real-time.

---

## Table of Contents

1. [System Overview](#system-overview)
2. [Scoring Perspectives](#scoring-perspectives)
3. [Reward System Deep Dive](#reward-system-deep-dive)
4. [Performance Evaluation Engine](#performance-evaluation-engine)
5. [Peer Evaluation System](#peer-evaluation-system)
6. [Intelligent Routing](#intelligent-routing)
7. [Tuning Parameters](#tuning-parameters)
8. [Monitoring & Observability](#monitoring--observability)
9. [Data Flow Maps](#data-flow-maps)
10. [Troubleshooting](#troubleshooting)

---

## System Overview

### The Big Picture

Commander.ai learns which agents are best for which tasks by tracking performance from **5 perspectives**:

1. **🎯 Objective Metrics** - Tokens, cost, duration, success/failure
2. **🤖 LLM Self-Assessment** - Agent evaluates its own performance (4 dimensions)
3. **👥 Peer Reviews** - Other agents evaluate the work
4. **👤 User Feedback** - Direct thumbs up/down + comments
5. **📊 Category Performance** - Historical success rates per task type

**Philosophy**: Multiple perspectives prevent gaming. An agent can't have high scores across all 5 unless it's genuinely performing well.

### Three-Phase Architecture

```
Phase 1: Foundation
├── Database tables (5 tables)
├── Performance Repository (CRUD operations)
├── API endpoints (/api/performance/*)
└── Task Feedback Widget (UI)

Phase 2: Intelligence
├── PerformanceEvaluator (4-dimension LLM scoring)
├── PeerEvaluationJob (agents review each other)
├── RewardSystem (gamification with penalties/bonuses)
└── StatsAggregationJob (rollup stats for routing)

Phase 3: Routing
├── CategoryClassifier (auto-detect task type)
├── IntelligentRouter (performance-based agent selection)
└── Routing API (recommendations, capabilities, leaderboards)
```

### Cost Structure

| Component | Cost | Frequency |
|-----------|------|-----------|
| Objective Metrics | $0.00 | Every task |
| Self-Assessment (LLM) | ~$0.0003 | Every task |
| Peer Review (2 agents) | ~$0.0006 | Background (async) |
| User Feedback | $0.00 | On demand |
| Category Classification | ~$0.00002 | Every task |
| Intelligent Routing | $0.00 | Every task |
| **Total per Task** | **~$0.00092** | **Evaluation + Routing + Peer** |

**At Scale**: 1,000 tasks/day = ~$0.92/day = ~$28/month for full intelligence

---

## Scoring Perspectives

### 1. Objective Metrics (Database Tracked)

**Source**: Automatically captured from `task.metadata.execution_metrics`

**Metrics**:
```python
{
    "tokens": 1234,              # Total tokens used
    "llm_calls": 3,              # Number of LLM API calls
    "tool_calls": 5,             # Number of tool invocations
    "duration_seconds": 45.2,    # Wall-clock time
    "cost": 0.0123,              # Total cost ($)
    "nodes_executed": ["reasoning", "tools", "response"],
    "model_name": "gpt-4o-mini"
}
```

**Stored In**: `performance_scores.objective_metrics` (JSONB)

**Use Cases**:
- Cost optimization (find expensive agents)
- Speed analysis (find slow agents)
- Resource utilization (tokens per task)

---

### 2. Self-Assessment (LLM Evaluation)

**Source**: `PerformanceEvaluator` analyzes task results using GPT-4o-mini

**4 Dimensions** (each scored 0.0-1.0):

#### a) Quality (0.0-1.0)
- Accuracy of information
- Completeness of response
- Relevance to user's request
- Depth of analysis

**Examples**:
- 0.9-1.0: Perfect answer, comprehensive, all requirements met
- 0.7-0.8: Good answer, minor gaps, mostly complete
- 0.5-0.6: Partial answer, missing key points
- 0.0-0.4: Poor answer, inaccurate, incomplete

#### b) Efficiency (0.0-1.0)
- Token usage relative to quality delivered
- Number of LLM calls needed
- Tool usage effectiveness
- Time to completion

**Formula**: `efficiency = quality / (normalized_tokens + normalized_calls)`

**Examples**:
- 0.9-1.0: High quality with minimal resources
- 0.7-0.8: Good quality, reasonable resource usage
- 0.5-0.6: Quality ok but wasteful
- 0.0-0.4: Poor quality and/or very wasteful

#### c) Helpfulness (0.0-1.0)
- Clarity of communication
- Actionability of response
- User experience quality
- Tone and professionalism

**Examples**:
- 0.9-1.0: Clear, actionable, professional, delightful
- 0.7-0.8: Clear and professional, could be more actionable
- 0.5-0.6: Understandable but not very helpful
- 0.0-0.4: Confusing, unhelpful, poor tone

#### d) Innovation (0.0-1.0)
- Creative problem-solving
- Novel approaches
- Going beyond basic requirements
- Unexpected insights

**Examples**:
- 0.9-1.0: Brilliant solution, unexpected insights
- 0.7-0.8: Creative approach, good thinking
- 0.5-0.6: Standard solution, no surprises
- 0.0-0.4: Basic/repetitive approach

**Overall Score**: `(quality + efficiency + helpfulness + innovation) / 4`

**Stored In**: `performance_scores.llm_evaluation` (JSONB)

**Prompt**: See `backend/core/performance_evaluator.py:_build_evaluation_prompt()`

---

### 3. Peer Reviews (Agent-to-Agent)

**Source**: `PeerEvaluationJob` - Kai and Maya review completed tasks

**When**: Background job runs every 5 minutes, reviews tasks completed in last hour

**Reviewers**:
- **Kai** (agent_d): Strategic analyst, focuses on approach and reasoning
- **Maya** (agent_e): Reflection specialist, focuses on quality and completeness

**Each Review Includes**:
```python
{
    "reviewer_agent_id": "agent_d",
    "reviewer_nickname": "kai",
    "score": 0.85,                    # 0.0-1.0
    "strengths": ["thorough analysis", "clear reasoning"],
    "weaknesses": ["could be more concise"],
    "suggestions": ["consider summarizing key points upfront"],
    "review_text": "Full review commentary...",
    "created_at": "2026-02-06T..."
}
```

**Stored In**: `peer_evaluations` table

**Aggregation**: Average of all peer scores contributes to overall agent score

**Why 2 Reviewers**: Different perspectives prevent bias (Kai = strategy, Maya = quality)

---

### 4. User Feedback (Direct Input)

**Source**: Task Feedback Widget in Mission Control UI

**Interface**:
```
┌─────────────────────────────────┐
│  How was this response?         │
│  👍 👎                           │
│  [Optional comment box]         │
│  [Submit]                       │
└─────────────────────────────────┘
```

**Data Captured**:
```python
{
    "user_id": "uuid",
    "task_id": "uuid",
    "agent_id": "agent_a",
    "rating": 1,              # 1 = thumbs up, -1 = thumbs down
    "comment": "Great work, very thorough!",
    "created_at": "2026-02-06T..."
}
```

**Stored In**: `performance_scores.user_feedback` (JSONB)

**Weight**: User feedback is **highest priority** (trumps LLM scores if conflict)

**Future NLP**: Comments stored for later analysis (sentiment, patterns, training data)

---

### 5. Category Performance (Historical)

**Source**: Aggregated stats from `StatsAggregationJob`

**Per Category Metrics**:
```python
{
    "research": {
        "count": 50,              # Tasks completed
        "avg_score": 0.87,        # Average overall score
        "success_rate": 0.94,     # % with score >= 0.6
        "avg_cost": 0.0234,       # Average cost
        "avg_duration": 32.5      # Average seconds
    },
    "analysis": {...},
    "writing": {...}
}
```

**Stored In**: `agent_performance_stats.category_performance` (JSONB)

**Use Case**: IntelligentRouter uses this to select best agent for each task type

---

## Reward System Deep Dive

**Location**: `backend/core/reward_system.py`

### Philosophy

Gamification with **meaningful rewards** and **smart penalties**:

- **Rewards**: Celebrate excellence, consistency, speed
- **Penalties**: Discourage poor quality, waste, errors
- **Balance**: Net score can be negative (bad performance), zero (baseline), or positive (excellent)

### Point Structure

#### Base Score (0.0-1.0)
```python
base_score = (
    quality * 0.30 +        # Quality is most important
    efficiency * 0.25 +
    helpfulness * 0.25 +
    innovation * 0.20
)
```

**Interpretation**:
- 0.9-1.0: Exceptional
- 0.8-0.89: Excellent
- 0.7-0.79: Good
- 0.6-0.69: Acceptable
- 0.0-0.59: Poor

#### Rewards (Additive Bonuses)

| Reward | Points | Trigger | Description |
|--------|--------|---------|-------------|
| **Excellence Bonus** | +0.10 | Score >= 0.9 | Exceptional performance |
| **Consistency Bonus** | +0.05 | 5+ tasks, stddev < 0.1 | Reliably good |
| **Speed Bonus** | +0.05 | Duration < median * 0.7 | Fast completion |
| **Efficiency Champion** | +0.05 | Efficiency >= 0.85 | Resource optimization |
| **Helpful Hero** | +0.05 | Helpfulness >= 0.9 | Outstanding UX |
| **Innovation Award** | +0.05 | Innovation >= 0.85 | Creative solutions |
| **First Success** | +0.10 | Agent's first task | Encouragement |

**Max Rewards**: +0.45 (all bonuses stacked)

#### Penalties (Subtractive)

| Penalty | Points | Trigger | Description |
|---------|--------|---------|-------------|
| **Poor Quality** | -0.15 | Quality < 0.5 | Unacceptable work |
| **Wasteful** | -0.10 | Efficiency < 0.4 | Resource abuse |
| **Too Slow** | -0.05 | Duration > median * 2.0 | Excessive time |
| **Error Penalty** | -0.20 | Task failed | Critical failure |
| **Incomplete** | -0.10 | Missing requirements | Partial work |

**Max Penalties**: -0.60 (all penalties stacked)

### Final Score Calculation

```python
final_score = base_score + sum(rewards) - sum(penalties)
final_score = max(-1.0, min(1.0, final_score))  # Clamp to [-1.0, 1.0]
```

**Examples**:

**Excellent Performance**:
```
base_score = 0.92
+ excellence_bonus = 0.10
+ efficiency_champion = 0.05
+ helpful_hero = 0.05
= 1.12 → clamped to 1.0
```

**Poor Performance**:
```
base_score = 0.45
- poor_quality = 0.15
- wasteful = 0.10
= 0.20 (net positive but low)
```

**Critical Failure**:
```
base_score = 0.30
- error_penalty = 0.20
- poor_quality = 0.15
= -0.05 (net negative!)
```

### Stored Data

**Table**: `performance_scores`

**Columns**:
```sql
final_score DECIMAL(3,2)           -- -1.0 to 1.0
rewards JSONB                      -- List of applied rewards
penalties JSONB                    -- List of applied penalties
reward_points DECIMAL(3,2)         -- Total reward points
penalty_points DECIMAL(3,2)        -- Total penalty points
```

**Query Example**:
```python
# Get agents with most excellence bonuses
SELECT agent_id, COUNT(*) as excellence_count
FROM performance_scores
WHERE rewards @> '[{"type": "excellence_bonus"}]'
GROUP BY agent_id
ORDER BY excellence_count DESC;
```

---

## Performance Evaluation Engine

**Location**: `backend/core/performance_evaluator.py`

### Evaluation Flow

```
Task Completed
    ↓
ExecutionTracker calls PerformanceEvaluator.evaluate()
    ↓
Extract task context (command, result, metadata)
    ↓
Build evaluation prompt (4 dimensions)
    ↓
GPT-4o-mini analyzes (~150 tokens in, ~200 tokens out)
    ↓
Parse JSON response → 4 scores
    ↓
RewardSystem calculates bonuses/penalties
    ↓
Save to performance_scores table
    ↓
Return PerformanceScore object
```

**Cost**: ~$0.0003 per evaluation

### Evaluation Prompt Template

**Structure**:
```
You are an expert evaluator for AI agent performance.

TASK DETAILS:
- Command: {command}
- Agent: {agent_nickname} ({agent_id})
- Model: {model_name}
- Category: {category}

RESULT:
{result_text}

METRICS:
- Tokens: {tokens}
- LLM Calls: {llm_calls}
- Duration: {duration}s
- Cost: ${cost}

Evaluate on 4 dimensions (0.0-1.0):
1. Quality: Accuracy, completeness, relevance
2. Efficiency: Resource usage vs. quality delivered
3. Helpfulness: Clarity, actionability, UX
4. Innovation: Creativity, insights, going beyond

Respond with JSON only:
{
  "quality": 0.0-1.0,
  "efficiency": 0.0-1.0,
  "helpfulness": 0.0-1.0,
  "innovation": 0.0-1.0,
  "reasoning": "Brief explanation"
}
```

**Key Parameters**:
- Temperature: 0.3 (consistent but not rigid)
- Max tokens: 300 (enough for scores + reasoning)
- Model: gpt-4o-mini (cost-effective)

### Customizing Evaluation

**File**: `backend/core/performance_evaluator.py`

**To Adjust Weights**:
```python
# Line ~180
base_score = (
    scores.quality * 0.30 +      # Change weights here
    scores.efficiency * 0.25 +
    scores.helpfulness * 0.25 +
    scores.innovation * 0.20
)
```

**To Change Dimensions**:
```python
# Line ~120
dimensions = [
    ("quality", "Accuracy, completeness, relevance"),
    ("efficiency", "Resource usage vs. quality"),
    ("helpfulness", "Clarity, actionability, UX"),
    ("innovation", "Creativity, insights, novelty"),
    # ADD NEW DIMENSION:
    # ("dimension_name", "Description for LLM")
]
```

**To Modify Prompt**:
```python
# Line ~85: _build_evaluation_prompt()
# Edit the prompt template directly
```

---

## Peer Evaluation System

**Location**: `backend/jobs/peer_evaluation.py`

### Job Schedule

**Trigger**: Every 5 minutes (configurable in job runner)

**Scope**: Reviews tasks completed in the last hour

**Reviewers**: Kai (agent_d) + Maya (agent_e)

### Review Process

```
PeerEvaluationJob.run()
    ↓
Query tasks completed in last hour, not yet reviewed
    ↓
For each task:
    ↓
    Request review from Kai (strategic perspective)
        ↓
        Kai analyzes: approach, reasoning, strategic thinking
        ↓
        Kai provides: score (0-1), strengths, weaknesses, suggestions
    ↓
    Request review from Maya (quality perspective)
        ↓
        Maya analyzes: completeness, clarity, quality
        ↓
        Maya provides: score (0-1), strengths, weaknesses, suggestions
    ↓
Save both reviews to peer_evaluations table
    ↓
Update agent_performance_stats with new peer scores
```

**Cost**: ~$0.0006 per task (2 reviews × ~$0.0003 each)

### Review Prompt Template

**For Kai (Strategic)**:
```
You are Kai, an expert strategic analyst.

Review this task from a STRATEGIC perspective:

TASK: {command}
AGENT: {agent_nickname}
RESULT: {result}

Evaluate:
1. Problem-solving approach
2. Strategic thinking
3. Reasoning quality
4. Efficiency of method

Provide:
- Score (0.0-1.0)
- 2-3 strengths
- 1-2 weaknesses (if any)
- 1-2 suggestions for improvement

JSON format:
{
  "score": 0.0-1.0,
  "strengths": ["...", "..."],
  "weaknesses": ["..."],
  "suggestions": ["..."]
}
```

**For Maya (Quality)**:
```
You are Maya, an expert quality reviewer.

Review this task from a QUALITY perspective:

TASK: {command}
AGENT: {agent_nickname}
RESULT: {result}

Evaluate:
1. Completeness
2. Clarity
3. Accuracy
4. Overall quality

Provide:
- Score (0.0-1.0)
- 2-3 strengths
- 1-2 weaknesses (if any)
- 1-2 suggestions for improvement

JSON format: {...}
```

### Stored Reviews

**Table**: `peer_evaluations`

**Columns**:
```sql
id UUID PRIMARY KEY
task_id UUID                   -- Task being reviewed
reviewer_agent_id VARCHAR(50)  -- "agent_d" or "agent_e"
reviewer_nickname VARCHAR(50)  -- "kai" or "maya"
reviewed_agent_id VARCHAR(50)  -- Agent whose work is reviewed
score DECIMAL(3,2)             -- 0.0-1.0
strengths TEXT[]               -- Array of strength strings
weaknesses TEXT[]              -- Array of weakness strings
suggestions TEXT[]             -- Array of suggestion strings
review_text TEXT               -- Full review commentary
created_at TIMESTAMP
```

**Query Examples**:
```sql
-- Get all reviews for an agent
SELECT * FROM peer_evaluations
WHERE reviewed_agent_id = 'agent_a'
ORDER BY created_at DESC;

-- Get Kai's harshest reviews
SELECT * FROM peer_evaluations
WHERE reviewer_agent_id = 'agent_d'
AND score < 0.6
ORDER BY score ASC;

-- Compare Kai vs Maya scoring
SELECT
    reviewed_agent_id,
    AVG(CASE WHEN reviewer_agent_id = 'agent_d' THEN score END) as kai_avg,
    AVG(CASE WHEN reviewer_agent_id = 'agent_e' THEN score END) as maya_avg
FROM peer_evaluations
GROUP BY reviewed_agent_id;
```

### Customizing Reviews

**Add More Reviewers**:
```python
# backend/jobs/peer_evaluation.py, line ~50
reviewers = [
    ("agent_d", "kai", "strategic analyst"),
    ("agent_e", "maya", "quality reviewer"),
    # ADD NEW REVIEWER:
    # ("agent_x", "nickname", "perspective"),
]
```

**Change Review Frequency**:
```python
# Job runner configuration
# Change from "every 5 minutes" to "every 15 minutes"
# Reduces API costs, slower feedback
```

**Adjust Review Window**:
```python
# Line ~60: Get tasks from last hour
hours_back = 1  # Change to 2, 4, 24, etc.
```

---

## Intelligent Routing

**Location**: `backend/core/intelligent_router.py`

### Routing Algorithm

**Step 1: Classify Task**
```python
CategoryClassifier.classify(command)
    ↓
Returns: TaskCategory (research, analysis, writing, etc.)
Cost: ~$0.00002
```

**Step 2: Get Capable Agents**
```python
# Agents with this category in specializations
capable_agents = ["agent_a", "agent_f"]  # for research
```

**Step 3: Score Each Agent**
```python
for agent in capable_agents:
    # Get stats from database
    stats = get_agent_stats(agent_id)

    # Extract category-specific performance
    base_score = stats.category_performance[category]["avg_score"]

    # Calculate success rate
    success_rate = stats.successful_tasks / stats.total_tasks

    # Get current load (TODO: implement in Phase 4)
    load_penalty = 0.0  # Placeholder

    # Calculate final score
    final_score = (base_score × success_rate) × (1 - load_penalty)
```

**Step 4: Select Best**
```python
best_agent = max(scores, key=lambda x: x.final_score)
```

**Step 5: Return Decision**
```python
return RoutingDecision(
    selected_agent_id=best_agent.agent_id,
    selected_nickname=best_agent.nickname,
    all_scores=scores,  # Show runner-ups for transparency
    reason="bob selected with score 0.87. Runner-up: alice (0.82, -0.05)",
    constraints=applied_constraints
)
```

### Agent Specializations

**Default Mapping** (hardcoded, overridden by performance data):

```python
AGENT_SPECIALIZATIONS = {
    "agent_a": ["research", "analysis"],      # Bob - Research specialist
    "agent_b": ["compliance", "analysis"],    # Sue - Compliance officer
    "agent_c": ["analysis", "writing"],       # Rex - Data analyst + writer
    "agent_d": ["planning", "analysis"],      # Kai - Strategic planner
    "agent_e": ["planning", "chat"],          # Maya - Reflection + chat
    "agent_f": ["writing", "research"],       # Alice - Document specialist
    "agent_g": ["chat"],                      # Chat - Conversational only
}
```

**Overrides**: If agent has 5+ tasks in a category with good performance, that becomes their specialization (even if not in defaults)

### Constraints Support

**Max Cost**:
```python
# User wants cheap task
decision = router.select_agent(
    command=command,
    category=category,
    constraints={"max_cost": 0.05}  # Only agents with avg_cost < $0.05
)
```

**Max Duration**:
```python
# User wants fast task
decision = router.select_agent(
    command=command,
    category=category,
    constraints={"max_duration": 30}  # Only agents with avg_duration < 30s
)
```

**Combined**:
```python
# User wants fast AND cheap
constraints = {
    "max_cost": 0.05,
    "max_duration": 30
}
```

### Fallback Behavior

**No Performance Data** → Use default specializations

**All Agents Fail Constraints** → Use best agent anyway, warn user

**Unknown Category** → Default to agent_a (bob) as general-purpose fallback

---

## Tuning Parameters

### 🎛️ Evaluation Weights

**File**: `backend/core/performance_evaluator.py`

```python
# Line ~180: Adjust dimension weights
base_score = (
    scores.quality * 0.30 +      # ← Increase for quality-first
    scores.efficiency * 0.25 +   # ← Increase for cost optimization
    scores.helpfulness * 0.25 +  # ← Increase for UX focus
    scores.innovation * 0.20     # ← Increase for creativity
)
```

**Example Tuning**:
```python
# Cost-conscious tuning (efficiency matters most)
base_score = (
    scores.quality * 0.25 +
    scores.efficiency * 0.40 +   # Doubled!
    scores.helpfulness * 0.20 +
    scores.innovation * 0.15
)
```

### 🎛️ Reward Thresholds

**File**: `backend/core/reward_system.py`

```python
# Line ~120: Excellence bonus
if base_score >= 0.9:  # ← Lower to 0.85 for more bonuses
    rewards.append({"type": "excellence_bonus", "points": 0.10})

# Line ~130: Speed bonus
if duration < median_duration * 0.7:  # ← Change to 0.8 for easier bonus
    rewards.append({"type": "speed_bonus", "points": 0.05})

# Line ~160: Poor quality penalty
if scores.quality < 0.5:  # ← Raise to 0.6 for stricter standards
    penalties.append({"type": "poor_quality", "points": 0.15})
```

### 🎛️ Peer Review Frequency

**File**: Job runner configuration (to be created)

```python
# Current: Every 5 minutes
peer_review_interval = 300  # seconds

# More frequent (higher cost, faster feedback):
peer_review_interval = 60   # Every minute

# Less frequent (lower cost, slower feedback):
peer_review_interval = 900  # Every 15 minutes
```

### 🎛️ Stats Aggregation Window

**File**: `backend/jobs/stats_aggregation.py`

```python
# Line ~40: Minimum tasks for reliable stats
MIN_TASKS_FOR_STATS = 5  # ← Lower to 3 for faster initial stats

# Line ~50: Time window for "recent" performance
RECENT_WINDOW_DAYS = 30  # ← Change to 7 for more responsive stats
```

### 🎛️ Routing Probation Period

**File**: `backend/core/intelligent_router.py`

```python
# Line ~99: Minimum tasks before trusting stats
MIN_TASKS_FOR_TRUST = 5  # ← Lower to 3 for faster agent promotion
```

### 🎛️ Category Classification Confidence

**File**: `backend/core/category_classifier.py`

```python
# Line ~64: Temperature for classification
self.llm = ChatOpenAI(
    model="gpt-4o-mini",
    temperature=0.0  # ← Increase to 0.1 for more variety
)
```

---

## Monitoring & Observability

### Key Metrics to Watch

#### 1. Agent Health Dashboard

**Query**:
```sql
SELECT
    agent_id,
    nickname,
    total_tasks,
    successful_tasks,
    ROUND(avg_overall_score, 2) as avg_score,
    ROUND(avg_cost_per_task, 4) as avg_cost,
    ROUND(avg_duration_seconds, 1) as avg_duration,
    overall_rank
FROM agent_performance_stats
ORDER BY overall_rank ASC;
```

**What to Watch**:
- **Avg Score** dropping below 0.7 → Agent struggling
- **Avg Cost** increasing → Resource usage creeping up
- **Avg Duration** increasing → Agent getting slower
- **Rank** changes → Competitive dynamics

#### 2. Category Performance Heatmap

**Query**:
```sql
SELECT
    agent_id,
    category_performance
FROM agent_performance_stats
WHERE category_performance IS NOT NULL;
```

**Visualization**: Heatmap of agent × category scores

**What to Watch**:
- Agents performing <0.6 in their specialty → Need retraining
- Unexpected high performers → Promote to new specializations
- Consistent 0.9+ scores → Excellence, reward visibly

#### 3. Reward/Penalty Distribution

**Query**:
```sql
SELECT
    jsonb_array_elements(rewards)->>'type' as reward_type,
    COUNT(*) as count,
    SUM((jsonb_array_elements(rewards)->>'points')::numeric) as total_points
FROM performance_scores
WHERE rewards IS NOT NULL
GROUP BY reward_type
ORDER BY count DESC;
```

**What to Watch**:
- Too many penalties → System too harsh, tune thresholds
- No bonuses → Thresholds too high, lower them
- Same reward repeatedly → One agent gaming system

#### 4. Peer Review Trends

**Query**:
```sql
SELECT
    reviewer_nickname,
    reviewed_agent_id,
    ROUND(AVG(score), 2) as avg_score,
    COUNT(*) as review_count
FROM peer_evaluations
GROUP BY reviewer_nickname, reviewed_agent_id
ORDER BY reviewer_nickname, avg_score DESC;
```

**What to Watch**:
- Kai vs Maya scoring divergence → Different standards
- One agent consistently low peer scores → Real quality issue
- All high scores → Reviewers too lenient, tune prompts

#### 5. User Feedback Sentiment

**Query**:
```sql
SELECT
    ps.agent_id,
    COUNT(*) FILTER (WHERE (ps.user_feedback->>'rating')::int = 1) as thumbs_up,
    COUNT(*) FILTER (WHERE (ps.user_feedback->>'rating')::int = -1) as thumbs_down,
    ROUND(
        COUNT(*) FILTER (WHERE (ps.user_feedback->>'rating')::int = 1)::numeric /
        NULLIF(COUNT(*), 0),
        2
    ) as approval_rate
FROM performance_scores ps
WHERE ps.user_feedback IS NOT NULL
GROUP BY ps.agent_id
ORDER BY approval_rate DESC;
```

**What to Watch**:
- Approval rate <60% → User dissatisfaction
- LLM scores high but user thumbs down → LLM evaluation miscalibrated
- Consistent negative feedback → Agent needs intervention

#### 6. Routing Efficiency

**Query** (requires routing decisions table - TODO Phase 4):
```sql
-- How often does the router pick the best agent?
-- Compare selected agent's actual performance vs. alternatives
```

**What to Watch**:
- Selected agent performs worse than runner-up → Algorithm needs tuning
- Always picking same agent → Not enough diversity, adjust load balancing

### Real-Time Monitoring (Phase 4)

**Planned Features**:

1. **Live Leaderboard** (Mission Control right panel toggle)
   - Top 3 agents overall
   - Top agent per category
   - Recent winners (last hour)
   - Reward streak counters

2. **Performance Charts**
   - Score trends over time (line chart)
   - Category heatmap (agent × category)
   - Cost vs. Quality scatter plot
   - Peer review radar chart

3. **Alert System**
   - Agent score drops >0.2 in 24h → Investigate
   - Peer review score <0.5 → Quality issue
   - User feedback <50% approval → User dissatisfaction
   - Cost spike >2x median → Resource problem

---

## Data Flow Maps

### Flow 1: Task Completion → Evaluation

```
User submits command
    ↓
Task created, assigned to agent
    ↓
Agent executes task
    ↓
ExecutionTracker collects metrics
    ↓
Task marked COMPLETED
    ↓
PerformanceEvaluator.evaluate() called
    ↓
    ├─→ Extract context (command, result, metadata)
    ├─→ Call GPT-4o-mini for 4D scores
    ├─→ Parse LLM response
    └─→ RewardSystem calculates bonuses/penalties
    ↓
PerformanceScore saved to database
    ↓
[Background] PeerEvaluationJob reviews task
    ↓
    ├─→ Kai reviews (strategic)
    └─→ Maya reviews (quality)
    ↓
Peer reviews saved to database
    ↓
[Background] StatsAggregationJob runs
    ↓
    ├─→ Aggregate all scores per agent
    ├─→ Calculate category performance
    ├─→ Rank agents
    └─→ Update agent_performance_stats
    ↓
Stats available for routing
```

### Flow 2: Command Routing

```
User submits command (e.g., "@bob research...")
    ↓
CategoryClassifier.classify(command)
    ↓
    └─→ LLM call: GPT-4o-mini (~$0.00002)
    ↓
Returns: TaskCategory.RESEARCH
    ↓
IntelligentRouter.select_agent(command, category)
    ↓
    ├─→ Get capable agents (default specializations)
    ├─→ Query agent_performance_stats for each
    ├─→ Calculate scores (base × success × availability)
    ├─→ Apply constraints (cost, duration)
    └─→ Select best agent
    ↓
Returns: RoutingDecision
    ↓
    ├─→ selected_agent_id: "agent_a"
    ├─→ all_scores: [agent_a: 0.87, agent_f: 0.82, ...]
    └─→ reason: "bob selected with score 0.87..."
    ↓
Task assigned to selected agent
    ↓
[Loop back to Flow 1]
```

### Flow 3: User Feedback

```
User views task result in Mission Control
    ↓
Task Feedback Widget displays
    ↓
User clicks 👍 or 👎
    ↓
(Optional) User adds comment
    ↓
User clicks Submit
    ↓
Frontend: POST /api/performance/scores/{task_id}/feedback
    ↓
Backend: Update performance_scores.user_feedback
    ↓
    └─→ {"rating": 1, "comment": "Great!", "created_at": "..."}
    ↓
[Background] StatsAggregationJob includes feedback in stats
    ↓
User feedback affects:
    ├─→ Agent overall score
    ├─→ Agent rank
    └─→ Routing decisions (high feedback = higher selection priority)
```

### Flow 4: Stats Aggregation

```
StatsAggregationJob runs (every 15 minutes)
    ↓
For each agent:
    ↓
    ├─→ Query all performance_scores for this agent
    ├─→ Calculate:
    │   ├─→ Total tasks
    │   ├─→ Successful tasks (score >= 0.6)
    │   ├─→ Average overall score
    │   ├─→ Average cost per task
    │   └─→ Average duration
    ├─→ Group by category:
    │   └─→ {"research": {"count": 50, "avg_score": 0.87}, ...}
    ├─→ Calculate rank (order by avg_overall_score)
    └─→ Upsert agent_performance_stats row
    ↓
Stats available for:
    ├─→ IntelligentRouter (routing decisions)
    ├─→ API endpoints (leaderboards, capabilities)
    └─→ UI (performance charts, dashboards)
```

---

## Troubleshooting

### Problem: Agent Scores Keep Dropping

**Symptoms**:
- Agent's avg_overall_score decreasing over days
- More penalties than rewards
- Peer reviews consistently low

**Diagnosis**:
```sql
-- Check recent scores
SELECT task_id, final_score, rewards, penalties
FROM performance_scores
WHERE agent_id = 'agent_a'
ORDER BY created_at DESC
LIMIT 20;

-- Check peer reviews
SELECT reviewer_nickname, score, weaknesses
FROM peer_evaluations
WHERE reviewed_agent_id = 'agent_a'
ORDER BY created_at DESC
LIMIT 10;
```

**Solutions**:
1. **LLM Model Change**: Agent's model might be underperforming → Switch model in Mission Control
2. **Prompt Tuning**: Agent's system prompt might need updating → Use Prompt Engineering UI
3. **Task Mismatch**: Agent being routed to wrong task types → Check category_performance
4. **Evaluation Miscalibration**: LLM evaluator might be too harsh → Lower penalty thresholds

### Problem: No Peer Reviews Appearing

**Symptoms**:
- `peer_evaluations` table empty
- No peer scores in agent stats

**Diagnosis**:
```bash
# Check if PeerEvaluationJob is running
# (Requires job runner implementation - Phase 4)
ps aux | grep peer_evaluation
```

**Solutions**:
1. **Job Not Scheduled**: Add PeerEvaluationJob to job runner
2. **No Completed Tasks**: Peer reviews only happen after task completion
3. **API Key Missing**: Check Kai/Maya have valid OpenAI API key
4. **Error in Job**: Check backend logs for exceptions

### Problem: Routing Always Picks Same Agent

**Symptoms**:
- IntelligentRouter always selects agent_a
- No variety in routing decisions
- Other agents never get tasks

**Diagnosis**:
```sql
-- Check category performance distribution
SELECT agent_id, category_performance
FROM agent_performance_stats;

-- Check if other agents have stats
SELECT agent_id, total_tasks
FROM agent_performance_stats
ORDER BY total_tasks DESC;
```

**Solutions**:
1. **New Agents in Probation**: Other agents have <5 tasks → Submit more tasks to build stats
2. **Load Balancing Off**: Load penalty is 0.0 (TODO Phase 4) → Implement active task tracking
3. **Dominant Agent**: agent_a genuinely best for everything → Lower MIN_TASKS_FOR_TRUST to promote others faster
4. **Category Mismatch**: All tasks are "research" → Diversify task types

### Problem: User Feedback Not Affecting Scores

**Symptoms**:
- Users give thumbs down, but agent scores stay high
- No correlation between feedback and scores

**Diagnosis**:
```sql
-- Compare LLM scores vs. user feedback
SELECT
    agent_id,
    ROUND(AVG(final_score), 2) as avg_llm_score,
    ROUND(AVG((user_feedback->>'rating')::int), 2) as avg_user_rating
FROM performance_scores
WHERE user_feedback IS NOT NULL
GROUP BY agent_id;
```

**Solutions**:
1. **Feedback Not Weighted**: User feedback currently stored but not used in final_score → **Enhancement needed**: Add user_feedback weight to scoring algorithm
2. **Sample Size Too Small**: Only 5% of tasks get user feedback → Encourage more feedback via UI prompts
3. **Feedback Delay**: Stats aggregation hasn't run yet → Wait for next aggregation cycle

### Problem: Costs Spiking Unexpectedly

**Symptoms**:
- Monthly bill higher than expected
- Agent avg_cost_per_task increasing

**Diagnosis**:
```sql
-- Find most expensive tasks
SELECT task_id, agent_id, objective_metrics->>'cost' as cost
FROM performance_scores
ORDER BY (objective_metrics->>'cost')::numeric DESC
LIMIT 20;

-- Find most expensive agents
SELECT agent_id, ROUND(avg_cost_per_task, 4) as avg_cost
FROM agent_performance_stats
ORDER BY avg_cost_per_task DESC;
```

**Solutions**:
1. **Peer Reviews Too Frequent**: Reduce from every 5 min to every 15 min
2. **Evaluation Model Too Expensive**: Already using gpt-4o-mini (cheapest) → Consider keyword-based evaluation for simple tasks
3. **Agent Using Expensive Model**: Check agent's LLM config → Switch from gpt-4o to gpt-4o-mini
4. **Add Cost Constraints**: Use routing constraints: `{"max_cost": 0.05}`

---

## Quick Reference

### Database Tables

| Table | Purpose | Key Columns |
|-------|---------|-------------|
| `performance_scores` | Individual task scores | `task_id`, `agent_id`, `final_score`, `rewards`, `penalties`, `llm_evaluation`, `user_feedback` |
| `peer_evaluations` | Agent-to-agent reviews | `task_id`, `reviewer_agent_id`, `reviewed_agent_id`, `score`, `strengths`, `weaknesses` |
| `node_performance` | Per-node execution stats | `task_id`, `node_name`, `duration_ms`, `tokens_used`, `success` |
| `agent_performance_stats` | Aggregated agent stats | `agent_id`, `total_tasks`, `avg_overall_score`, `category_performance`, `overall_rank` |
| `objective_templates` | Task category definitions | `category`, `description`, `success_criteria` |

### API Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/performance/scores` | POST | Save performance score |
| `/api/performance/scores/{task_id}` | GET | Get task score |
| `/api/performance/scores/{task_id}/feedback` | POST | Submit user feedback |
| `/api/performance/peer-reviews/{task_id}` | GET | Get peer reviews |
| `/api/performance/stats/{agent_id}` | GET | Get agent stats |
| `/api/performance/leaderboard` | GET | Get agent rankings |
| `/api/routing/classify` | POST | Classify command |
| `/api/routing/recommend-agent` | POST | Get routing recommendation |
| `/api/routing/agent-capabilities/{id}` | GET | Get agent profile |
| `/api/routing/best-agents-by-category` | GET | Category leaderboard |

### Cost Breakdown

| Component | Cost per Task | Frequency |
|-----------|---------------|-----------|
| Category Classification | $0.00002 | Every task |
| Self-Assessment (4D LLM) | $0.0003 | Every task |
| Peer Review (2 agents) | $0.0006 | Background (async) |
| Intelligent Routing | $0.00 | Every task |
| User Feedback | $0.00 | On demand |
| **Total** | **~$0.00092** | **Full intelligence** |

### Tuning Quick-Adjust

**Make agents more forgiving**:
```python
# reward_system.py
EXCELLENCE_THRESHOLD = 0.85  # Was 0.9
POOR_QUALITY_THRESHOLD = 0.4  # Was 0.5
```

**Prioritize cost over quality**:
```python
# performance_evaluator.py
base_score = (
    scores.efficiency * 0.40 +  # Doubled
    scores.quality * 0.25,      # Reduced
)
```

**Faster agent promotion**:
```python
# intelligent_router.py
MIN_TASKS_FOR_TRUST = 3  # Was 5
```

---

## Future Enhancements

### Phase 4 - Visualization (In Progress)
- [ ] Leaderboard UI in Mission Control (right panel toggle)
- [ ] Performance charts (scores over time)
- [ ] Category heatmap (agent × category performance)
- [ ] Routing decision visualization ("Why this agent?")

### Phase 5 - Advanced Intelligence
- [ ] User preference learning (user X prefers agent Y)
- [ ] Multi-agent collaboration scoring (which pairs work best)
- [ ] NLP analysis of peer review comments (extract patterns)
- [ ] Predictive routing (anticipate best agent for new task types)
- [ ] Load balancing integration (active task tracking)

### Phase 6 - Optimization
- [ ] Model-specific routing (GPT-4o vs Claude for different tasks)
- [ ] Dynamic prompt injection (customize system prompts based on performance)
- [ ] A/B testing framework (compare routing algorithms)
- [ ] Cost optimization strategies (use cheaper models for simple tasks)

---

## Appendix: Configuration Variables

**Environment Variables** (`.env`):
```bash
# OpenAI API (for evaluation and classification)
OPENAI_API_KEY=sk-...

# Database
DATABASE_URL=postgresql://user:pass@localhost:5432/commander

# Job Configuration (future)
PEER_REVIEW_INTERVAL_SECONDS=300
STATS_AGGREGATION_INTERVAL_SECONDS=900
```

**Python Constants**:
```python
# Evaluation
EVALUATION_MODEL = "gpt-4o-mini"
EVALUATION_TEMPERATURE = 0.3
EVALUATION_MAX_TOKENS = 300

# Rewards
EXCELLENCE_THRESHOLD = 0.9
SPEED_BONUS_MULTIPLIER = 0.7
POOR_QUALITY_THRESHOLD = 0.5

# Routing
MIN_TASKS_FOR_TRUST = 5
CLASSIFICATION_MODEL = "gpt-4o-mini"

# Stats
MIN_TASKS_FOR_STATS = 5
RECENT_WINDOW_DAYS = 30
```

---

**Last Updated**: February 6, 2026
**Version**: 1.0.0 (Phases 1-3 Complete)
**Maintainers**: Update this guide when tuning parameters or adding features!
