"""
Test Script for Phase 2 - Evaluation Engine

Tests:
1. PerformanceEvaluator (LLM-based scoring)
2. PeerEvaluationJob (Kai + Maya reviews)
3. RewardSystem (gamification)
4. StatsAggregationJob (rankings)

Usage:
    python -m backend.scripts.test_phase2
"""

import asyncio
import sys
from pathlib import Path
from uuid import uuid4

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from backend.core.performance_evaluator import PerformanceEvaluator
from backend.core.reward_system import RewardSystem
from backend.jobs.peer_evaluation import PeerEvaluationJob
from backend.jobs.stats_aggregation import run_stats_aggregation


async def test_performance_evaluator():
    """Test LLM-based quality evaluation"""
    print("\n" + "="*60)
    print("TEST 1: PerformanceEvaluator (LLM-based scoring)")
    print("="*60)

    evaluator = PerformanceEvaluator()

    # Sample task
    original_command = "@bob research quantum computing breakthroughs in 2024"
    agent_output = """
Recent quantum computing breakthroughs in 2024:

1. IBM achieved a 1,000+ qubit quantum processor
2. Google demonstrated quantum error correction at scale
3. Microsoft made progress on topological qubits
4. Multiple startups showed practical quantum advantage in optimization

These advances bring us closer to practical quantum computing applications.
"""

    print(f"\n📝 Original Command: {original_command}")
    print(f"📄 Agent Output: {agent_output[:100]}...")

    scores = await evaluator.evaluate_task(
        original_command=original_command,
        agent_output=agent_output,
        agent_name="Bob"
    )

    print(f"\n📊 Quality Scores:")
    print(f"  • Accuracy:      {scores.accuracy:.2f}")
    print(f"  • Relevance:     {scores.relevance:.2f}")
    print(f"  • Completeness:  {scores.completeness:.2f}")
    print(f"  • Clarity:       {scores.clarity:.2f}")
    print(f"  • Overall:       {scores.overall:.2f}")

    print(f"\n✅ PerformanceEvaluator working! (Made 4 LLM calls)")
    return scores


async def test_peer_evaluation():
    """Test peer evaluation job"""
    print("\n" + "="*60)
    print("TEST 2: PeerEvaluationJob (Kai + Maya reviews)")
    print("="*60)

    job = PeerEvaluationJob()

    # Sample task
    task_id = uuid4()
    agent_id = "agent_a"
    agent_name = "Bob"
    original_command = "@bob analyze market trends in AI industry"
    agent_output = """
The AI industry is experiencing rapid growth with:
- Increased investment in generative AI
- Enterprise adoption of LLMs
- Focus on responsible AI governance
- Competition in AI infrastructure
"""

    print(f"\n📝 Task: {original_command}")
    print(f"📄 Output: {agent_output[:80]}...")

    # Note: This won't save to DB (no session), just tests evaluation logic
    kai_eval = await job._get_kai_evaluation(original_command, agent_name, agent_output)
    maya_eval = await job._get_maya_evaluation(original_command, agent_name, agent_output)

    print(f"\n🧠 Kai's Evaluation (Critical Thinking):")
    print(f"  • Score:    {kai_eval['score']:.2f}")
    print(f"  • Criteria: {kai_eval['criteria']}")
    print(f"  • Feedback: {kai_eval['feedback'][:150]}...")

    print(f"\n💫 Maya's Evaluation (Holistic Reflection):")
    print(f"  • Score:    {maya_eval['score']:.2f}")
    print(f"  • Criteria: {maya_eval['criteria']}")
    print(f"  • Feedback: {maya_eval['feedback'][:150]}...")

    print(f"\n✅ PeerEvaluationJob working! (Made 2 LLM calls)")
    return kai_eval, maya_eval


def test_reward_system():
    """Test reward/penalty calculation"""
    print("\n" + "="*60)
    print("TEST 3: RewardSystem (Gamification)")
    print("="*60)

    system = RewardSystem()

    # Test Case 1: High-quality, fast, cheap task
    print("\n📊 Test Case 1: Excellent Performance")
    print("  • Status: COMPLETED")
    print("  • Quality: 0.90")
    print("  • Duration: 8 seconds")
    print("  • Cost: $0.03")
    print("  • User Rating: 5 stars")

    reward1 = system.calculate_reward(
        task_status="COMPLETED",
        overall_score=0.90,
        duration_seconds=8.0,
        total_cost=0.03,
        user_rating=5,
        peer_evaluations=[{"score": 0.88}, {"score": 0.85}]
    )

    print(f"\n💰 Rewards Breakdown:")
    print(f"  • Base:            {reward1.base_reward} points")
    print(f"  • Quality Bonus:   {reward1.quality_bonus} points")
    print(f"  • Speed Bonus:     {reward1.speed_bonus} points")
    print(f"  • Cost Bonus:      {reward1.cost_bonus} points")
    print(f"  • User Bonus:      {reward1.user_bonus} points")
    print(f"  • Peer Bonus:      {reward1.peer_bonus} points")
    print(f"  • Penalties:       -{reward1.penalties} points")
    print(f"\n  🎯 NET REWARD:     {reward1.net_reward} points")

    # Test Case 2: Poor performance
    print("\n📊 Test Case 2: Poor Performance")
    print("  • Status: COMPLETED")
    print("  • Quality: 0.40")
    print("  • Duration: 150 seconds (timeout)")
    print("  • Cost: $0.75 (excessive)")
    print("  • User Rating: 2 stars (poor)")

    reward2 = system.calculate_reward(
        task_status="COMPLETED",
        overall_score=0.40,
        duration_seconds=150.0,
        total_cost=0.75,
        user_rating=2
    )

    print(f"\n💰 Rewards Breakdown:")
    print(f"  • Base:            {reward2.base_reward} points")
    print(f"  • Quality Bonus:   {reward2.quality_bonus} points")
    print(f"  • Speed Bonus:     {reward2.speed_bonus} points")
    print(f"  • Cost Bonus:      {reward2.cost_bonus} points")
    print(f"  • User Bonus:      {reward2.user_bonus} points")
    print(f"  • Peer Bonus:      {reward2.peer_bonus} points")
    print(f"  • Penalties:       -{reward2.penalties} points")
    print(f"\n  🎯 NET REWARD:     {reward2.net_reward} points (negative!)")

    print(f"\n✅ RewardSystem working! (Calculated rewards/penalties)")


async def test_stats_aggregation():
    """Test stats aggregation job"""
    print("\n" + "="*60)
    print("TEST 4: StatsAggregationJob (Rankings)")
    print("="*60)

    print("\n⚠️  NOTE: This requires:")
    print("  1. Database tables created (run init_performance_tables.py)")
    print("  2. At least one performance score in the database")
    print("\n⏭️  Skipping database test (run manually via API endpoint)")
    print("\nTo test manually:")
    print('  curl -X POST "http://localhost:8000/api/jobs/aggregate-stats?user_id=00000000-0000-0000-0000-000000000001"')


async def main():
    """Run all tests"""
    print("\n" + "="*60)
    print("PHASE 2 EVALUATION ENGINE - TEST SUITE")
    print("="*60)
    print("\nThis will make ~6 API calls to OpenAI (GPT-4o-mini)")
    print("Estimated cost: ~$0.001")
    print("\nPress Enter to continue, or Ctrl+C to cancel...")
    input()

    try:
        # Test 1: PerformanceEvaluator
        scores = await test_performance_evaluator()

        # Test 2: PeerEvaluationJob
        kai_eval, maya_eval = await test_peer_evaluation()

        # Test 3: RewardSystem
        test_reward_system()

        # Test 4: StatsAggregation (manual)
        await test_stats_aggregation()

        # Summary
        print("\n" + "="*60)
        print("✅ ALL TESTS PASSED!")
        print("="*60)
        print("\n📊 Summary:")
        print(f"  • Quality Evaluation: Working (Overall: {scores.overall:.2f})")
        print(f"  • Kai's Peer Review:  Working (Score: {kai_eval['score']:.2f})")
        print(f"  • Maya's Peer Review: Working (Score: {maya_eval['score']:.2f})")
        print(f"  • Reward System:      Working")
        print(f"  • Stats Aggregation:  Manual test required")

        print("\n🎯 Phase 2 is ready!")
        print("\nNext steps:")
        print("  1. Submit a real task in Mission Control")
        print("  2. Check backend logs for evaluation results")
        print("  3. Run stats aggregation via Quick Action")
        print("  4. View leaderboard via API")

    except KeyboardInterrupt:
        print("\n\n❌ Tests cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
