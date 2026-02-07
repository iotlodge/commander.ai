# Deferred Features - Agent Performance System

## Peer Evaluation (Phase 2)

**Status**: ⏸️ Temporarily Disabled
**Location**: `backend/core/command_executor.py:111`
**Disabled on**: February 6, 2026

### What is it?
Agents evaluating each other's work output. After @bob completes a research task, @maya and @kai would review the output and score it based on quality, completeness, accuracy, etc.

### Why disabled?
JSON parsing errors when Kai and Maya generate evaluation responses:
```
Failed to parse Maya's evaluation JSON: Expecting value: line 1 column 1 (char 0)
Failed to parse Kai's evaluation JSON: Expecting value: line 1 column 1 (char 0)
```

**Root cause**: LLM responses returning empty or malformed JSON. The peer evaluation prompt needs refinement to ensure structured JSON output.

### When to re-enable?
When testing multi-agent collaboration scenarios where agents work together on complex tasks. Not needed for single-agent task completion.

### How to re-enable?
In `backend/core/command_executor.py`, change:
```python
run_peer_eval=False  # Currently disabled
```
to:
```python
run_peer_eval=True
```

Then debug the prompt in `backend/jobs/peer_evaluation.py` to ensure valid JSON responses.

### Current impact?
**None**. The system still tracks:
- ✅ LLM self-assessment scores
- ✅ User feedback ratings
- ✅ Objective metrics (tokens, cost, duration)
- ✅ Category classification
- ✅ Performance rankings

Peer evaluation adds a third opinion but isn't critical for basic performance tracking.

---

## Notes
- All other Phase 2, 3, and 4 features are **fully functional**
- Performance system complete: evaluation, routing, rewards, leaderboard, charts
- Only peer eval needs prompt engineering work before production use
