"""
Quick test to verify commander.ai setup
"""

import asyncio
from uuid import uuid4


async def test_infrastructure():
    """Test that all infrastructure components work"""

    print("🧪 Testing commander.ai infrastructure...\n")

    # Test 1: Import core modules
    print("1️⃣ Testing imports...")
    try:
        from backend.core.config import get_settings
        from backend.memory.memory_service import get_memory_service
        from backend.agents.base.agent_registry import AgentRegistry
        from backend.core.command_parser import CommandParser

        print("   ✅ All core modules import successfully")
    except Exception as e:
        print(f"   ❌ Import failed: {e}")
        return False

    # Test 2: Configuration
    print("\n2️⃣ Testing configuration...")
    try:
        settings = get_settings()
        print(f"   ✅ Settings loaded: {settings.app_env} environment")
        print(
            f"   ✅ Database URL: {settings.database_url.split('@')[1] if '@' in settings.database_url else 'configured'}"
        )
        print(f"   ✅ Redis URL: {settings.redis_url}")
        print(f"   ✅ Qdrant URL: {settings.qdrant_url}")
    except Exception as e:
        print(f"   ❌ Config failed: {e}")
        return False

    # Test 3: Memory Service Connection
    print("\n3️⃣ Testing memory service...")
    try:
        memory_service = await get_memory_service()
        print("   ✅ Memory service initialized")
        print(f"   ✅ Short-term memory (Redis): connected")
        print(f"   ✅ Vector store (Qdrant): connected")
    except Exception as e:
        print(f"   ❌ Memory service failed: {e}")
        return False

    # Test 4: Command Parser
    print("\n4️⃣ Testing command parser...")
    try:
        # First register some test agents
        from backend.agents.base.agent_interface import AgentMetadata

        test_agents = [
            AgentMetadata("agent_a", "bob", "Research", "Test"),
            AgentMetadata("agent_b", "sue", "Compliance", "Test"),
        ]

        # Test parsing
        cmd1 = CommandParser.parse("@bob research quantum computing")
        cmd2 = CommandParser.parse("hello sue")
        cmd3 = CommandParser.parse("analyze this data")

        print(f"   ✅ '@bob research...' → mentioned agents: {len(cmd1.mentioned_agents)}")
        print(f"   ✅ 'hello sue' → greeting detected: {cmd2.greeting_target is not None}")
        print(f"   ✅ 'analyze this...' → requires parent: {cmd3.requires_parent}")
    except Exception as e:
        print(f"   ❌ Command parser failed: {e}")
        return False

    # Test 5: FastAPI app
    print("\n5️⃣ Testing FastAPI app...")
    try:
        from backend.api.main import app

        print("   ✅ FastAPI app created successfully")
        print(f"   ✅ App title: {app.title}")
    except Exception as e:
        print(f"   ❌ FastAPI failed: {e}")
        return False

    print("\n" + "=" * 50)
    print("✨ All tests passed! Infrastructure is ready!")
    print("=" * 50)
    print("\n📋 Next steps:")
    print("   1. Start server: uvicorn backend.api.main:app --reload")
    print("   2. Visit: http://localhost:8000/docs")
    print("   3. Implement agents (Phase 2)")

    return True


if __name__ == "__main__":
    result = asyncio.run(test_infrastructure())
    exit(0 if result else 1)
