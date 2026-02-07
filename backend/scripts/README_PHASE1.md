# Phase 1: Performance Tracking Foundation - Setup Guide

**Status**: ✅ Complete (v0.5.0 Phase 1)
**Branch**: `feature/agent-performance-system`
**Commit**: `7d63581`

---

## What Was Built

### Database Infrastructure

**5 New Tables**:
1. `agent_performance_scores` - Core performance tracking for each task
2. `agent_peer_evaluations` - Peer evaluations (agents rating each other)
3. `agent_node_performance` - Node-level performance within agents
4. `agent_performance_stats` - Aggregated statistics (updated hourly)
5. `objective_templates` - Task objective classification templates

### Backend Components

- **PerformanceRepository** (`backend/repositories/performance_repository.py`)
  - Full CRUD operations for all 5 tables
  - Leaderboard queries
  - Agent statistics aggregation

- **ExecutionTracker Enhancement** (`backend/core/execution_tracker.py`)
  - `on_task_complete()` method for automatic scoring
  - Basic efficiency calculation (tokens × duration)
  - Automatic performance record creation

- **API Endpoints** (`backend/api/routes/performance.py`)
  - `POST /api/tasks/{task_id}/feedback` - User ratings
  - `GET /api/agents/leaderboard` - Agent rankings
  - `GET /api/agents/{agent_id}/performance` - Agent history

### Frontend Components

- **TaskFeedbackWidget** (`frontend/components/mission-control/task-feedback-widget.tsx`)
  - 5-star rating system
  - Optional text feedback
  - Keyboard shortcuts (Enter to submit)
  - Dismissible UI

- **usePerformance Hook** (`frontend/lib/hooks/use-performance.ts`)
  - `submitTaskFeedback()` - Submit ratings
  - `fetchLeaderboard()` - Get rankings
  - `fetchAgentPerformance()` - Get agent history

---

## Setup Instructions

### 1. Create Database Tables

Run the initialization script to create the new tables:

```bash
# From project root
python -m backend.scripts.init_performance_tables
```

**Expected Output**:
```
🔧 Initializing performance tracking tables...
📍 Database: localhost:5432/commander_ai
✅ Performance tracking tables created successfully!

Created tables:
  - agent_performance_scores
  - agent_peer_evaluations
  - agent_node_performance
  - agent_performance_stats
  - objective_templates
```

### 2. Verify Tables Created

```bash
# Connect to PostgreSQL
psql -d commander_ai

# List new tables
\dt agent_*
\dt objective_*

# Check schema
\d agent_performance_scores
```

You should see all 5 new tables.

### 3. Restart Backend

The new API routes are automatically loaded, but restart to ensure clean state:

```bash
# Stop backend (Ctrl+C)
# Start backend
cd backend
uvicorn backend.api.main:app --reload
```

### 4. Test API Endpoints

**Test Leaderboard Endpoint**:
```bash
curl "http://localhost:8000/api/agents/leaderboard?user_id=00000000-0000-0000-0000-000000000001"
```

Expected: `{"rankings": [], ...}` (empty initially)

**Test Feedback Submission** (requires a completed task):
```bash
curl -X POST "http://localhost:8000/api/tasks/YOUR_TASK_ID/feedback?user_id=00000000-0000-0000-0000-000000000001" \
  -H "Content-Type: application/json" \
  -d '{"user_rating": 5, "user_feedback": "Great job!"}'
```

Expected: `{"success": true, "message": "Feedback submitted successfully"}`

---

## Testing the Full Flow

### Manual Test

1. **Submit a Task**:
   - Open Mission Control
   - Submit a command: `@bob research quantum computing`

2. **Task Completes**:
   - `ExecutionTracker.on_task_complete()` automatically creates performance record
   - Check backend logs for: `"Performance score saved for task ..."`

3. **Submit Feedback** (TODO: Integrate widget in Phase 4):
   - For now, use API directly:
   ```bash
   curl -X POST "http://localhost:8000/api/tasks/YOUR_TASK_ID/feedback?user_id=00000000-0000-0000-0000-000000000001" \
     -H "Content-Type: application/json" \
     -d '{"user_rating": 5, "user_feedback": "Excellent research!"}'
   ```

4. **Check Leaderboard**:
   ```bash
   curl "http://localhost:8000/api/agents/leaderboard?user_id=00000000-0000-0000-0000-000000000001"
   ```

---

## Database Schema Details

### agent_performance_scores

```sql
CREATE TABLE agent_performance_scores (
    id UUID PRIMARY KEY,
    task_id UUID NOT NULL,
    agent_id VARCHAR(50) NOT NULL,

    -- Quality Scores (0-1 scale)
    accuracy_score NUMERIC(3,2),
    relevance_score NUMERIC(3,2),
    completeness_score NUMERIC(3,2),
    efficiency_score NUMERIC(3,2),
    overall_score NUMERIC(3,2),

    -- User Feedback
    user_rating INTEGER,  -- 1-5 stars
    user_feedback TEXT,

    -- Cost Metrics
    total_tokens INTEGER,
    estimated_cost NUMERIC(10,6),

    created_at TIMESTAMP DEFAULT NOW()
);
```

### agent_performance_stats

```sql
CREATE TABLE agent_performance_stats (
    agent_id VARCHAR(50) PRIMARY KEY,
    nickname VARCHAR(50) NOT NULL,

    -- Overall Stats
    total_tasks INTEGER DEFAULT 0,
    successful_tasks INTEGER DEFAULT 0,
    avg_overall_score NUMERIC(3,2),
    avg_user_rating NUMERIC(3,2),

    -- Rankings
    overall_rank INTEGER,

    last_updated TIMESTAMP DEFAULT NOW()
);
```

---

## Current Limitations (Phase 1)

### What's Working
- ✅ Database tables created
- ✅ Performance records auto-created on task completion
- ✅ User feedback API endpoint
- ✅ Basic efficiency scoring
- ✅ Leaderboard API endpoint

### What's NOT Yet Implemented
- ❌ Automatic quality scoring (accuracy, relevance, completeness)
  - **Reason**: Requires LLM-based evaluation (Phase 2)
  - **Current**: Only efficiency_score is calculated

- ❌ Peer evaluations (Kai/Maya reviews)
  - **Reason**: Requires background job (Phase 2)

- ❌ Leaderboard UI in Mission Control
  - **Reason**: Frontend component (Phase 4)

- ❌ Task feedback widget integration
  - **Reason**: Needs conversation stream integration (Phase 4)

- ❌ Stats aggregation job
  - **Reason**: Scheduled job implementation (Phase 3)

---

## Next Steps

### Phase 2: Evaluation Engine (Week 2)
- Build `PerformanceEvaluator` class (LLM-based quality scoring)
- Create `PeerEvaluationJob` (Kai + Maya review outputs)
- Implement `RewardSystem` class
- Add scheduled job for stats aggregation

### Phase 3: Intelligence Layer (Week 3)
- Build `IntelligentRouter` for Leo
- Implement agent selection algorithm
- Add objective category classification

### Phase 4: Visualization (Week 4)
- Build `AgentLeaderboardPanel` component
- Add toggle for Quick Actions ↔ Leaderboard
- Integrate `TaskFeedbackWidget` into conversation stream

---

## Troubleshooting

### Tables Already Exist Error

If you get "table already exists", drop and recreate:

```sql
-- WARNING: This deletes all performance data!
DROP TABLE IF EXISTS agent_performance_scores CASCADE;
DROP TABLE IF EXISTS agent_peer_evaluations CASCADE;
DROP TABLE IF EXISTS agent_node_performance CASCADE;
DROP TABLE IF EXISTS agent_performance_stats CASCADE;
DROP TABLE IF EXISTS objective_templates CASCADE;

-- Then rerun:
python -m backend.scripts.init_performance_tables
```

### No Performance Records Created

Check:
1. Is `on_task_complete()` being called? (Add logging)
2. Is database connection working? (Check backend logs)
3. Did task actually complete successfully?

### Leaderboard Returns Empty

This is normal initially! Rankings require:
1. At least one completed task
2. Stats aggregation job (Phase 3)

For testing, manually insert a stats record:
```sql
INSERT INTO agent_performance_stats (agent_id, nickname, total_tasks, avg_overall_score, overall_rank)
VALUES ('agent_a', 'bob', 10, 0.85, 1);
```

---

## Files Changed (8 files, 1,675 lines)

**Backend**:
- `backend/repositories/performance_repository.py` (NEW - 445 lines)
- `backend/scripts/init_performance_tables.py` (NEW - 68 lines)
- `backend/api/routes/performance.py` (NEW - 212 lines)
- `backend/core/execution_tracker.py` (MODIFIED - added 78 lines)
- `backend/api/main.py` (MODIFIED - added 1 line)

**Frontend**:
- `frontend/components/mission-control/task-feedback-widget.tsx` (NEW - 115 lines)
- `frontend/lib/hooks/use-performance.ts` (NEW - 94 lines)

**Documentation**:
- `NEXT.md` (MODIFIED - full v0.5.0 plan)

---

**Last Updated**: February 6, 2026
**Phase 1 Status**: ✅ Complete and Committed
