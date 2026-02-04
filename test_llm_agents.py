"""
Simple test script for LLM-powered multi-agent system
Tests basic functionality without the UI
"""

import asyncio
from uuid import uuid4

from backend.agents.base.agent_registry import initialize_default_agents, AgentRegistry
from backend.agents.base.agent_interface import AgentExecutionContext


async def test_simple_research():
    """Test @bob with a simple research query"""
    print("\n" + "="*80)
    print("🧪 TEST 1: Simple Research with @bob")
    print("="*80)

    # Initialize agents
    print("\n📦 Initializing agents...")
    await initialize_default_agents()

    # Get Bob
    bob = AgentRegistry.get_by_nickname("bob")
    print(f"✅ Found @bob: {bob.metadata.specialization}")

    # Create context
    context = AgentExecutionContext(
        user_id=uuid4(),
        thread_id=uuid4(),
        command="research the benefits of async programming in Python",
        conversation_context=None,
    )

    # Execute
    print(f"\n🚀 Executing: {context.command}")
    print("⏳ Please wait... (this may take 10-15 seconds)")

    result = await bob.execute(context.command, context)

    # Display results
    print("\n" + "-"*80)
    if result.success:
        print("✅ SUCCESS!")
        print("\n📄 Response:")
        print(result.response)
        print(f"\n📊 Metadata: {result.metadata}")
    else:
        print("❌ FAILED!")
        print(f"Error: {result.error}")
    print("-"*80)


async def test_llm_decomposition():
    """Test Leo's LLM-powered task decomposition"""
    print("\n" + "="*80)
    print("🧪 TEST 2: LLM Task Decomposition with @leo")
    print("="*80)

    # Get Leo
    leo = AgentRegistry.get_by_nickname("leo")
    print(f"✅ Found @leo: {leo.metadata.specialization}")

    # Create a complex query that should be decomposed
    context = AgentExecutionContext(
        user_id=uuid4(),
        thread_id=uuid4(),
        command='research "Python async frameworks" investigate performance scalability and ease of use',
        conversation_context=None,
    )

    print(f"\n🚀 Executing: {context.command}")
    print("⏳ Please wait... (LLM decomposition + parallel execution)")

    result = await leo.execute(context.command, context)

    # Display results
    print("\n" + "-"*80)
    if result.success:
        print("✅ SUCCESS!")
        print("\n📊 Task Decomposition:")
        if "task_type" in result.metadata:
            print(f"   Task Type: {result.metadata['task_type']}")
        if "specialists_used" in result.metadata:
            print(f"   Specialists Used: {result.metadata['specialists_used']}")
        if "subtask_count" in result.metadata:
            print(f"   Subtasks: {result.metadata['subtask_count']}")

        print("\n📄 Aggregated Response:")
        # Print first 500 chars
        response_preview = result.response[:500] + "..." if len(result.response) > 500 else result.response
        print(response_preview)
    else:
        print("❌ FAILED!")
        print(f"Error: {result.error}")
    print("-"*80)


async def test_reflection():
    """Test @maya reflection agent"""
    print("\n" + "="*80)
    print("🧪 TEST 3: Reflection with @maya")
    print("="*80)

    # Get Maya
    maya = AgentRegistry.get_by_nickname("maya")
    print(f"✅ Found @maya: {maya.metadata.specialization}")

    # Test content to review
    test_content = """
    Python is a good programming language. It has many features.
    People use it for various things. It is popular.
    You should learn Python if you want to code.
    """

    context = AgentExecutionContext(
        user_id=uuid4(),
        thread_id=uuid4(),
        command=f"Review this content:\n{test_content}",
        conversation_context=None,
    )

    print(f"\n🚀 Reviewing content...")
    print("⏳ Please wait... (analyzing quality)")

    result = await maya.execute(context.command, context)

    # Display results
    print("\n" + "-"*80)
    if result.success:
        print("✅ SUCCESS!")
        if "reflection_score" in result.metadata:
            print(f"\n⭐ Quality Score: {result.metadata['reflection_score']:.2f}/1.00")
        if "issues_count" in result.metadata:
            print(f"🔍 Issues Found: {result.metadata['issues_count']}")

        print("\n📄 Reflection Report (preview):")
        response_preview = result.response[:600] + "..." if len(result.response) > 600 else result.response
        print(response_preview)
    else:
        print("❌ FAILED!")
        print(f"Error: {result.error}")
    print("-"*80)


async def main():
    """Run all tests"""
    print("\n" + "="*80)
    print("🚀 COMMANDER.AI - LLM AGENT TESTING")
    print("="*80)
    print("\nThis will test:")
    print("  1. @bob - LLM-powered research")
    print("  2. @leo - LLM task decomposition & aggregation")
    print("  3. @maya - Reflection & quality assessment")
    print("\nTotal estimated time: ~30-45 seconds")
    print("="*80)

    try:
        # Test 1: Simple research
        await test_simple_research()

        # Test 2: LLM decomposition
        await test_llm_decomposition()

        # Test 3: Reflection
        await test_reflection()

        print("\n" + "="*80)
        print("✅ ALL TESTS COMPLETED!")
        print("="*80)

    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
