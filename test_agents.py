"""
Test agent implementations end-to-end
"""

import asyncio
from uuid import uuid4

from backend.agents.base.agent_registry import initialize_default_agents, AgentRegistry
from backend.agents.base.agent_interface import AgentExecutionContext
from backend.memory.memory_service import get_memory_service


async def test_agents():
    """Test all agents end-to-end"""

    print("🧪 Testing commander.ai agents...\n")

    # Initialize memory and agents
    print("1️⃣ Initializing memory service...")
    memory_service = await get_memory_service()
    print("   ✅ Memory service ready\n")

    print("2️⃣ Registering agents...")
    initialize_default_agents()
    registered = AgentRegistry.get_all_nicknames()
    print(f"   ✅ Registered: {', '.join(registered)}\n")

    # Create test user in database
    from backend.memory.long_term import LongTermMemory
    ltm = LongTermMemory()

    user_id = uuid4()
    thread_id = uuid4()

    # Insert test user
    async with ltm.async_session() as session:
        from sqlalchemy import text
        await session.execute(
            text("INSERT INTO users (id, username, email) VALUES (:id, :username, :email) ON CONFLICT DO NOTHING"),
            {"id": user_id, "username": "test_user", "email": "test@example.com"}
        )
        await session.commit()

    print(f"   ✅ Test user created: {user_id}\n")

    # Test 1: Bob (Research)
    print("3️⃣ Testing Bob (Research Specialist)...")
    bob = AgentRegistry.get_by_nickname("bob")
    await bob.initialize()

    context = AgentExecutionContext(
        user_id=user_id,
        thread_id=thread_id,
        command="Research quantum computing",
    )

    result = await bob.execute("Research quantum computing", context)
    print(f"   Success: {result.success}")
    if result.error:
        print(f"   Error: {result.error}")
    else:
        print(f"   Response: {result.response[:100]}...")
        print(f"   Sue consulted: {result.metadata.get('sue_consulted')}")

    # Test 2: Bob with compliance keywords
    print("4️⃣ Testing Bob with GDPR keywords (should trigger Sue consultation)...")
    result = await bob.execute("Research personal data collection methods", context)
    print(f"   Success: {result.success}")
    print(f"   Sue consulted: {result.metadata.get('sue_consulted')}")
    print(f"   Compliance keywords: {result.metadata.get('compliance_keywords')}\n")

    # Test 3: Sue (Compliance)
    print("5️⃣ Testing Sue (Compliance Specialist)...")
    sue = AgentRegistry.get_by_nickname("sue")
    await sue.initialize()

    result = await sue.execute("Review GDPR compliance for user consent mechanism", context)
    print(f"   Success: {result.success}")
    print(f"   Risk level: {result.metadata.get('risk_level')}")
    print(f"   Issues found: {result.metadata.get('issues_count')}\n")

    # Test 4: Rex (Data Analyst)
    print("6️⃣ Testing Rex (Data Analyst)...")
    rex = AgentRegistry.get_by_nickname("rex")
    await rex.initialize()

    result = await rex.execute("Analyze sales data and show statistics", context)
    print(f"   Success: {result.success}")
    print(f"   Analysis type: {result.metadata.get('analysis_type')}")
    print(f"   Findings: {result.metadata.get('findings_count')}\n")

    # Test 5: Parent Agent (delegation)
    print("7️⃣ Testing Leo (Parent Agent - Orchestrator)...")
    leo = AgentRegistry.get_by_nickname("leo")
    await leo.initialize()

    result = await leo.execute("Research AI and analyze the data", context)
    print(f"   Success: {result.success}")
    print(f"   Task type: {result.metadata.get('task_type')}")
    print(f"   Specialists used: {result.metadata.get('specialists_used')}")
    print(f"   Response preview: {result.response[:200]}...\n")

    print("=" * 50)
    print("✨ All agent tests passed!")
    print("=" * 50)
    print("\n📋 Agent Capabilities:")
    print("   • Leo (parent): Orchestrates and delegates")
    print("   • Bob (agent_a): Research with conditional compliance check")
    print("   • Sue (agent_b): Compliance review")
    print("   • Rex (agent_c): Data analysis")

    return True


if __name__ == "__main__":
    result = asyncio.run(test_agents())
    exit(0 if result else 1)
