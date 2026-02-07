# Phase 2: Evaluation Engine - Setup Guide

**Status**: ✅ Complete (v0.5.0 Phase 2)
**Branch**: `feature/agent-performance-system`
**Commit**: `8e87701`

---

## What Was Built

### Intelligent Evaluation System

**PerformanceEvaluator** (`backend/core/performance_evaluator.py`)
- LLM-based quality scoring using GPT-4o-mini
- **4 Evaluation Dimensions**:
  - Accuracy (35%): Factual correctness, no hallucinations
  - Relevance (25%): On-topic, addresses the query
  - Completeness (25%): Covers all aspects, sufficient detail
  - Clarity (15%): Well-structured, easy to understand
- Weighted overall score calculation
- Graceful error handling (fallback to 0.5 scores)

**PeerEvaluationJob** (`backend/jobs/peer_evaluation.py`)
- **Kai's Critical Evaluation**:
  - Accuracy, depth, critical thinking, evidence quality
  - Thorough, critical, constructive feedback
- **Maya's Holistic Evaluation**:
  - Relevance, usefulness, completeness, user experience
  - Empathetic, big-picture perspective
- Parallel execution (both agents review simultaneously)
- JSON-based evaluation format
- Fallback parsing for malformed JSON

**RewardSystem** (`backend/core/reward_system.py`)
- **Rewards** (Total: 0-175 points):
  - Base completion: 10 points
  - Quality bonus: 0-50 points (overall_score × 50)
  - Speed bonus: 0-20 points (faster = more)
  - Cost efficiency: 0-30 points (cheap + quality)
  - User satisfaction: 0-40 points (5-star rating)
  - Peer recognition: 0-25 points (avg peer eval)
- **Penalties**:
  - Failed task: 30 points
  - Excessive cost (>$0.50): 10 points per $0.10 over
  - Timeout (>2 min): 5 points per 10 seconds over
  - Poor rating (<3 stars): 15 points per star below 3
- Net reward can be negative!

**StatsAggregationJob** (`backend/jobs/stats_aggregation.py`)
- Aggregates all performance data per agent
- **Calculates**:
  - Total tasks, success rate, failed tasks
  - Average overall score, user rating
  - Total cost, avg cost per task, cost efficiency
  - Average duration (speed)
  - Category performance (research, analysis, etc.)
  - Model performance (track LLM changes)
- **Rankings**:
  - Overall rank (based on avg score, tasks, efficiency)
  - Per-category ranks (TODO: Phase 3)
- Updates `agent_performance_stats` table

---

## Integration Points

### ExecutionTracker Enhancement

**Updated** `on_task_complete()` method:
- Now requires: `agent_name`, `original_command`, `agent_output`
- Uses `PerformanceEvaluator` for quality scores
- Triggers `PeerEvaluationJob` in background (async)
- Combines quality (80%) + efficiency (20%) for overall score

**Example Usage**:
```python
from backend.core.execution_tracker import ExecutionTracker

tracker = ExecutionTracker()

# After task completes
scores = await tracker.on_task_complete(
    task_id=task_id,
    agent_id="agent_a",
    agent_name="Bob",
    original_command="@bob research quantum computing",
    agent_output="Quantum computing is...",
    final_state=final_state,
    task_metadata=task_metadata,
    run_peer_eval=True  # Trigger Kai + Maya reviews
)

# scores = {
#     "accuracy_score": 0.85,
#     "relevance_score": 0.90,
#     "completeness_score": 0.75,
#     "efficiency_score": 0.80,
#     "overall_score": 0.83
# }
```

---

## API Endpoints

### Manual Stats Aggregation

**POST** `/api/jobs/aggregate-stats`

Manually trigger stats aggregation (normally runs hourly).

```bash
curl -X POST "http://localhost:8000/api/jobs/aggregate-stats?user_id=00000000-0000-0000-0000-000000000001"
```

**Response**:
```json
{
  "status": "completed",
  "updated_agents": ["agent_a", "agent_b", "agent_c", ...],
  "updated_count": 8,
  "duration_seconds": 1.23,
  "timestamp": "2026-02-06T12:00:00"
}
```

---

## Testing Phase 2

### Full Flow Test

1. **Submit a Task**:
   ```
   @bob research quantum computing breakthroughs 2024
   ```

2. **Task Completes**:
   - `ExecutionTracker.on_task_complete()` called
   - `PerformanceEvaluator` scores output (4 API calls to GPT-4o-mini)
   - Performance record saved with quality scores
   - Peer evaluation job triggered (background)

3. **Check Performance Score**:
   ```bash
   curl "http://localhost:8000/api/agents/agent_a/performance?user_id=00000000-0000-0000-0000-000000000001"
   ```

   **Expected** (after a few seconds):
   ```json
   {
     "agent_id": "agent_a",
     "stats": {
       "avg_overall_score": 0.83,
       "total_tasks": 1,
       "rank": null  // Not ranked yet
     },
     "recent_scores": [
       {
         "task_id": "...",
         "overall_score": 0.83,
         "category": null,
         "created_at": "2026-02-06T12:00:00"
       }
     ]
   }
   ```

4. **Check Peer Evaluations** (via database):
   ```sql
   SELECT * FROM agent_peer_evaluations
   WHERE evaluated_agent_id = 'agent_a'
   ORDER BY created_at DESC
   LIMIT 2;
   ```

   **Expected**: 2 rows (Kai + Maya evaluations)

5. **Run Stats Aggregation**:
   ```bash
   curl -X POST "http://localhost:8000/api/jobs/aggregate-stats?user_id=00000000-0000-0000-0000-000000000001"
   ```

6. **Check Leaderboard**:
   ```bash
   curl "http://localhost:8000/api/agents/leaderboard?user_id=00000000-0000-0000-0000-000000000001"
   ```

   **Expected**:
   ```json
   {
     "rankings": [
       {
         "agent_id": "agent_a",
         "nickname": "bob",
         "rank": 1,
         "total_tasks": 1,
         "avg_overall_score": 0.83,
         "avg_user_rating": null,
         "total_cost": 0.02,
         "cost_efficiency_score": 0.65,
         "days_active": 0
       }
     ],
     "category": null,
     "last_updated": "2026-02-06T12:05:00"
   }
   ```

---

## Evaluation Costs

### PerformanceEvaluator Costs

**Per Task**: 4 API calls to GPT-4o-mini
- Accuracy evaluation (~200 tokens)
- Relevance evaluation (~200 tokens)
- Completeness evaluation (~200 tokens)
- Clarity evaluation (~150 tokens)

**Total**: ~750 tokens input, ~50 tokens output
**Cost**: ~$0.0001 per task evaluation (negligible)

### PeerEvaluationJob Costs

**Per Task**: 2 API calls to GPT-4o-mini
- Kai evaluation (~300 tokens input, ~200 tokens output)
- Maya evaluation (~300 tokens input, ~200 tokens output)

**Total**: ~600 tokens input, ~400 tokens output
**Cost**: ~$0.0002 per task peer review (negligible)

### Combined

**Total per task**: ~$0.0003 for full evaluation + peer review
**100 tasks**: ~$0.03
**1000 tasks**: ~$0.30

**Negligible cost for comprehensive quality scoring!**

---

## Database Changes

### agent_performance_scores Table

**New Fields Populated** (Phase 1 → Phase 2):
- `accuracy_score` (now populated via LLM)
- `relevance_score` (now populated via LLM)
- `completeness_score` (now populated via LLM)
- `overall_score` (now weighted: 80% quality + 20% efficiency)

### agent_peer_evaluations Table

**Now Actively Used**:
- Kai and Maya evaluate every completed task
- Stores evaluation score + detailed feedback
- Evaluation criteria stored as JSONB

### agent_performance_stats Table

**Now Updated Hourly**:
- All fields populated after first stats aggregation
- Rankings calculated
- Category and model performance tracked

---

## Quick Action Integration

**@alice** now has a new quick action:
- "Aggregate performance stats" → `@alice run agent performance stats aggregation`

This manually triggers the stats aggregation job.

---

## Phase 2 Architecture

```
Task Completes
    ↓
ExecutionTracker.on_task_complete()
    ↓
    ├─→ PerformanceEvaluator (4 LLM calls)
    │   ├─ Accuracy score
    │   ├─ Relevance score
    │   ├─ Completeness score
    │   └─ Clarity score
    │
    ├─→ Save performance_scores (with quality metrics)
    │
    └─→ PeerEvaluationJob (background, async)
        ├─ Kai's critical evaluation
        └─ Maya's holistic evaluation
            ↓
        Save peer_evaluations


Hourly Schedule
    ↓
StatsAggregationJob
    ↓
    ├─→ Aggregate data per agent
    ├─→ Calculate avg scores, costs, speed
    ├─→ Track category performance
    ├─→ Track model performance
    └─→ Calculate rankings
        ↓
    Update agent_performance_stats
        ↓
    Leaderboard reflects new rankings
```

---

## Troubleshooting

### Peer Evaluations Not Appearing

**Check**:
1. Is peer evaluation job running? (check logs)
2. Did it error? (check `agent_peer_evaluations` table)
3. Is JSON parsing working? (check for fallback scores)

**Common Issue**: JSON parsing fails if LLM returns markdown:
```
```json
{"score": 0.85}
```
```

**Solution**: Job has fallback regex parser that extracts scores from text.

### Quality Scores Still 0.5

**Check**:
1. Is `PerformanceEvaluator` being called? (check logs)
2. Did LLM calls error? (check logs for exceptions)
3. Is OpenAI API key valid?

**Fallback**: If evaluation fails, scores default to 0.5 (not 0).

### Rankings Not Updating

**Check**:
1. Has stats aggregation run? (check `agent_performance_stats.last_updated`)
2. Are there any performance scores? (check `agent_performance_scores` table)
3. Did stats job error? (check logs)

**Manual Trigger**:
```bash
curl -X POST "http://localhost:8000/api/jobs/aggregate-stats?user_id=00000000-0000-0000-0000-000000000001"
```

---

## Next Steps

### Phase 3: Intelligence Layer (Week 3)
- Build `IntelligentRouter` for Leo (performance-based agent selection)
- Implement objective category classification
- Add category-specific rankings
- Track routing decisions for transparency

### Phase 4: Visualization (Week 4)
- Build `AgentLeaderboardPanel` component (toggle with Quick Actions)
- Integrate `TaskFeedbackWidget` into conversation stream
- Create `AgentPerformanceChart` component
- Add performance badges to agent tiles

---

## Files Changed (4 new files, 1,388 lines)

**Backend Core**:
- `backend/core/performance_evaluator.py` (NEW - 297 lines)
- `backend/core/reward_system.py` (NEW - 300 lines)

**Backend Jobs**:
- `backend/jobs/peer_evaluation.py` (NEW - 340 lines)
- `backend/jobs/stats_aggregation.py` (NEW - 300 lines)
- `backend/jobs/__init__.py` (MODIFIED - exports)

**Backend API**:
- `backend/api/routes/jobs.py` (MODIFIED - stats endpoint)

**Backend Core** (modified):
- `backend/core/execution_tracker.py` (MODIFIED - uses evaluator)

**Frontend**:
- `frontend/components/mission-control/quick-actions-panel.tsx` (MODIFIED - @alice action)

---

**Last Updated**: February 6, 2026
**Phase 2 Status**: ✅ Complete and Committed
**Next Phase**: Phase 3 - Intelligence Layer (Intelligent Routing)
