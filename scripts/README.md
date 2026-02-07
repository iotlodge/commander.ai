# Scripts

Utility scripts for development and testing.

## Performance Data Generator

Generate dummy performance data for testing without expensive API calls.

### Quick Start

```bash
# Generate 50 tasks per agent, reset existing data
python scripts/generate_test_performance_data.py --tasks 50 --reset

# Generate 100 tasks with high variance
python scripts/generate_test_performance_data.py --scenario varied --tasks 100

# Just reset all data
python scripts/generate_test_performance_data.py --reset-only
```

### Scenarios

**realistic** (default)
- Mixed performance across agents
- Bob (research) and Chat score highest
- Natural variance in scores
- Good for general testing

**varied**
- High variance in scores (2x normal)
- Erratic performance patterns
- Tests edge cases in charts

**competitive**
- All agents score close together (0.85-0.91)
- Tight leaderboard race
- Tests ranking tie-breakers

**bob-dominates**
- Bob scores 0.98 (perfect)
- Others score lower
- Clear winner scenario

**trending**
- Scores improve over time
- Good for testing trend charts
- Shows learning/improvement patterns

### What It Generates

For each agent:
- **Performance scores** (accuracy, relevance, completeness, efficiency)
- **Categories** (research, analysis, compliance, etc.)
- **User ratings** (1-5 stars, 70% of tasks)
- **Cost metrics** (tokens, estimated cost, duration)
- **Timestamps** (spread over 7 days)

### Options

```
--scenario {realistic,varied,competitive,bob-dominates,trending}
    Data generation scenario (default: realistic)

--tasks N
    Number of tasks per agent (default: 30)
    Total tasks = N × 8 agents

--reset
    Clear all existing data before generating

--reset-only
    Only reset data, don't generate new
```

### Examples

```bash
# Small dataset for quick testing
python scripts/generate_test_performance_data.py --tasks 10 --reset

# Large dataset for stress testing
python scripts/generate_test_performance_data.py --tasks 200 --reset

# Bob dominance scenario
python scripts/generate_test_performance_data.py --scenario bob-dominates --tasks 50 --reset

# Trending improvement over time
python scripts/generate_test_performance_data.py --scenario trending --tasks 100 --reset
```

### After Generation

Check Mission Control:
- **Leaderboard**: See rankings with medals
- **Performance Charts**: Click 📊 icon on agent tiles
- **Routing Insights**: Hover ⓘ icon to see category performance
- **Feedback Widgets**: Complete new tasks to see user ratings

### Cost Savings

Generating 100 tasks per agent (800 total) with real LLM calls would cost **~$2-5**.
This script generates realistic data for **$0** in **~2 seconds**! 💰

### Resetting

To start fresh:
```bash
python scripts/generate_test_performance_data.py --reset-only
```

This clears:
- ✅ Performance scores
- ✅ Peer evaluations
- ✅ Node performance
- ✅ Agent stats
- ✅ Rankings

Then generate new data with your preferred scenario.
