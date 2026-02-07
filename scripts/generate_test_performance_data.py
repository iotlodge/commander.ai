"""
Generate Test Performance Data

Creates dummy performance records for all agents to test metrics, leaderboards, and charts.
Saves $$$ by avoiding thousands of real LLM calls.

Usage:
    python scripts/generate_test_performance_data.py --tasks 50 --reset
    python scripts/generate_test_performance_data.py --scenario varied --tasks 100
    python scripts/generate_test_performance_data.py --reset-only

Scenarios:
    - realistic: Mixed performance across agents (default)
    - varied: High variance in scores
    - competitive: Close rankings
    - bob-dominates: Bob scores highest
    - trending: Scores improve over time
"""

import asyncio
import argparse
import random
from datetime import datetime, timedelta
from uuid import uuid4
from decimal import Decimal

from sqlalchemy import text
from backend.core.database import get_session_maker
from backend.repositories.performance_repository import PerformanceRepository
from backend.jobs.stats_aggregation import StatsAggregationJob


# Agent configurations
AGENTS = {
    "agent_parent": "leo",
    "agent_a": "bob",
    "agent_b": "sue",
    "agent_c": "rex",
    "agent_d": "kai",
    "agent_e": "maya",
    "agent_f": "alice",
    "agent_g": "chat",
}

CATEGORIES = [
    "research",
    "analysis",
    "compliance",
    "data_processing",
    "document_management",
    "reflection",
    "conversation",
    "planning",
]

# Cost per 1K tokens (approximate)
COST_PER_1K_INPUT = 0.00003
COST_PER_1K_OUTPUT = 0.00006


class PerformanceDataGenerator:
    """Generate realistic test performance data"""

    def __init__(self, scenario: str = "realistic"):
        self.scenario = scenario
        self.session_maker = get_session_maker()

    async def reset_all_data(self):
        """Clear all performance data"""
        print("🗑️  Resetting all performance data...")

        async with self.session_maker() as session:
            # Delete in reverse order of dependencies
            await session.execute(text("DELETE FROM agent_peer_evaluations"))
            await session.execute(text("DELETE FROM agent_node_performance"))
            await session.execute(text("DELETE FROM agent_performance_scores"))
            await session.execute(text("DELETE FROM agent_performance_stats"))
            await session.commit()

        print("✅ All performance data cleared!")

    def _get_agent_baseline(self, agent_id: str, nickname: str) -> dict:
        """Get baseline performance characteristics for each agent"""
        baselines = {
            "leo": {"score": 0.85, "variance": 0.10, "category": "planning"},
            "bob": {"score": 0.92, "variance": 0.08, "category": "research"},
            "sue": {"score": 0.88, "variance": 0.09, "category": "compliance"},
            "rex": {"score": 0.86, "variance": 0.12, "category": "data_processing"},
            "kai": {"score": 0.83, "variance": 0.15, "category": "reflection"},
            "maya": {"score": 0.87, "variance": 0.11, "category": "reflection"},
            "alice": {"score": 0.90, "variance": 0.07, "category": "document_management"},
            "chat": {"score": 0.94, "variance": 0.06, "category": "conversation"},
        }

        # Apply scenario modifiers
        baseline = baselines.get(nickname, {"score": 0.85, "variance": 0.10, "category": "analysis"})

        if self.scenario == "bob-dominates":
            if nickname == "bob":
                baseline["score"] = 0.98
                baseline["variance"] = 0.02
            else:
                baseline["score"] *= 0.92  # Lower others

        elif self.scenario == "competitive":
            # Narrow the gap
            baseline["score"] = 0.88 + random.uniform(-0.03, 0.03)
            baseline["variance"] = 0.05

        elif self.scenario == "varied":
            baseline["variance"] *= 2.0  # More chaos

        return baseline

    def _generate_score_components(self, base_score: float, variance: float) -> dict:
        """Generate individual score components that average to base_score"""
        # Add some randomness
        variation = random.uniform(-variance, variance)
        overall = max(0.0, min(1.0, base_score + variation))

        # Component scores with slight variance
        accuracy = overall + random.uniform(-0.05, 0.05)
        relevance = overall + random.uniform(-0.05, 0.05)
        completeness = overall + random.uniform(-0.05, 0.05)
        efficiency = overall + random.uniform(-0.08, 0.08)

        # Clamp to [0, 1]
        return {
            "accuracy_score": max(0.0, min(1.0, accuracy)),
            "relevance_score": max(0.0, min(1.0, relevance)),
            "completeness_score": max(0.0, min(1.0, completeness)),
            "efficiency_score": max(0.0, min(1.0, efficiency)),
            "overall_score": overall,
        }

    def _generate_cost_metrics(self) -> dict:
        """Generate realistic cost metrics"""
        # Random token counts
        input_tokens = random.randint(500, 3000)
        output_tokens = random.randint(200, 1500)
        total_tokens = input_tokens + output_tokens

        # Calculate cost
        cost = (input_tokens / 1000 * COST_PER_1K_INPUT) + (output_tokens / 1000 * COST_PER_1K_OUTPUT)

        return {
            "total_tokens": total_tokens,
            "estimated_cost": cost,
            "duration_seconds": random.uniform(2.0, 15.0),
        }

    async def generate_agent_data(
        self,
        agent_id: str,
        nickname: str,
        num_tasks: int,
        start_date: datetime
    ):
        """Generate performance data for a single agent"""
        baseline = self._get_agent_baseline(agent_id, nickname)

        async with self.session_maker() as session:
            repo = PerformanceRepository(session)

            print(f"  📊 Generating {num_tasks} tasks for @{nickname}...")

            for i in range(num_tasks):
                # Time progression
                task_date = start_date + timedelta(hours=i * 2)

                # Trending scenario: scores improve over time
                if self.scenario == "trending":
                    progress = i / num_tasks
                    baseline["score"] = min(0.98, baseline["score"] + progress * 0.15)

                # Generate scores
                scores = self._generate_score_components(
                    baseline["score"],
                    baseline["variance"]
                )

                # Random category (favor agent's specialty)
                if random.random() < 0.6:
                    category = baseline["category"]
                else:
                    category = random.choice(CATEGORIES)

                # Add category and complexity
                scores["objective_category"] = category
                scores["task_complexity"] = random.randint(1, 5)

                # User rating (sometimes None)
                if random.random() < 0.7:  # 70% of tasks get rated
                    # Rating correlates with score but isn't perfect
                    rating_base = scores["overall_score"] * 5
                    rating = int(max(1, min(5, rating_base + random.uniform(-0.5, 0.5))))
                    scores["user_rating"] = rating

                # Cost metrics
                metadata = self._generate_cost_metrics()
                metadata["model_used"] = "gpt-4o-mini"  # Simulated
                metadata["temperature"] = 0.7

                # Save to database
                await repo.save_performance_score(
                    task_id=uuid4(),
                    agent_id=agent_id,
                    scores=scores,
                    metadata=metadata
                )

            await session.commit()
            print(f"  ✅ @{nickname}: {num_tasks} tasks generated")

    async def generate_all_agents(self, tasks_per_agent: int):
        """Generate data for all agents"""
        print(f"\n🎲 Generating test data with '{self.scenario}' scenario...")
        print(f"   {tasks_per_agent} tasks per agent × {len(AGENTS)} agents = {tasks_per_agent * len(AGENTS)} total\n")

        # Start date: 7 days ago
        start_date = datetime.utcnow() - timedelta(days=7)

        for agent_id, nickname in AGENTS.items():
            # Vary task count slightly per agent
            num_tasks = tasks_per_agent + random.randint(-5, 5)
            await self.generate_agent_data(agent_id, nickname, num_tasks, start_date)

        print("\n📈 Aggregating stats...")
        job = StatsAggregationJob()
        result = await job.run()

        print(f"✅ Stats aggregation complete!")
        print(f"   Updated {result['updated_count']} agents in {result['duration_seconds']:.2f}s\n")

    async def run(self, tasks_per_agent: int, reset: bool = False):
        """Main execution"""
        if reset:
            await self.reset_all_data()

        await self.generate_all_agents(tasks_per_agent)

        print("🎉 Test data generation complete!")
        print("\n💡 Now check Mission Control:")
        print("   - Leaderboard rankings")
        print("   - Performance charts (click 📊 on agent tiles)")
        print("   - Routing insights (hover ⓘ on agent tiles)")


async def main():
    parser = argparse.ArgumentParser(
        description="Generate test performance data for agents",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Scenarios:
  realistic      Mixed performance across agents (default)
  varied         High variance in scores
  competitive    Close rankings
  bob-dominates  Bob scores highest
  trending       Scores improve over time

Examples:
  # Generate 50 tasks per agent, reset first
  python scripts/generate_test_performance_data.py --tasks 50 --reset

  # Competitive scenario with 100 tasks
  python scripts/generate_test_performance_data.py --scenario competitive --tasks 100

  # Just reset, no generation
  python scripts/generate_test_performance_data.py --reset-only
        """
    )

    parser.add_argument(
        "--scenario",
        choices=["realistic", "varied", "competitive", "bob-dominates", "trending"],
        default="realistic",
        help="Data generation scenario"
    )

    parser.add_argument(
        "--tasks",
        type=int,
        default=30,
        help="Number of tasks per agent (default: 30)"
    )

    parser.add_argument(
        "--reset",
        action="store_true",
        help="Reset all data before generating"
    )

    parser.add_argument(
        "--reset-only",
        action="store_true",
        help="Only reset data, don't generate new"
    )

    args = parser.parse_args()

    generator = PerformanceDataGenerator(scenario=args.scenario)

    if args.reset_only:
        await generator.reset_all_data()
    else:
        await generator.run(tasks_per_agent=args.tasks, reset=args.reset)


if __name__ == "__main__":
    asyncio.run(main())
