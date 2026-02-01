"""
Test script for Phase 3A: Backend Task Management + WebSocket
"""
import asyncio
import json
from uuid import UUID, uuid4
from datetime import datetime

from backend.repositories.task_repository import TaskRepository, get_session_factory
from backend.models.task_models import TaskCreate, TaskUpdate, TaskStatus
from backend.api.websocket import get_ws_manager
from backend.core.task_callback import TaskProgressCallback
from backend.agents.base.agent_interface import AgentExecutionContext
from backend.agents.base.agent_registry import initialize_default_agents, AgentRegistry


async def test_task_repository():
    """Test task repository CRUD operations"""
    print("\n=== Testing Task Repository ===")

    session_factory = get_session_factory()
    async with session_factory() as session:
        repo = TaskRepository(session)

        # Test create task
        user_id = UUID("00000000-0000-0000-0000-000000000001")
        thread_id = uuid4()

        task_create = TaskCreate(
            user_id=user_id,
            agent_id="agent_a",
            thread_id=thread_id,
            command_text="@bob research climate change"
        )

        task = await repo.create_task(task_create)
        print(f"✅ Created task: {task.id}")
        print(f"   Agent: {task.agent_nickname} ({task.agent_id})")
        print(f"   Status: {task.status}")
        print(f"   Progress: {task.progress_percentage}%")

        # Test get task
        retrieved_task = await repo.get_task(task.id)
        assert retrieved_task is not None
        assert retrieved_task.id == task.id
        print(f"✅ Retrieved task: {retrieved_task.id}")

        # Test update progress
        await repo.update_progress(task.id, 50, "processing")
        updated_task = await repo.get_task(task.id)
        assert updated_task.progress_percentage == 50
        assert updated_task.current_node == "processing"
        print(f"✅ Updated progress: {updated_task.progress_percentage}%")

        # Test set status
        await repo.set_status(
            task.id,
            TaskStatus.COMPLETED,
            completed_at=datetime.utcnow()
        )
        completed_task = await repo.get_task(task.id)
        assert completed_task.status == TaskStatus.COMPLETED
        assert completed_task.completed_at is not None
        print(f"✅ Set status to: {completed_task.status}")

        # Test get user tasks
        user_tasks = await repo.get_user_tasks(user_id, limit=10)
        assert len(user_tasks) > 0
        print(f"✅ Retrieved {len(user_tasks)} user tasks")

        return task.id


async def test_websocket_manager():
    """Test WebSocket manager"""
    print("\n=== Testing WebSocket Manager ===")

    ws_manager = get_ws_manager()

    # Create a mock WebSocket class
    class MockWebSocket:
        def __init__(self):
            self.messages = []

        async def accept(self):
            pass

        async def send_json(self, data):
            self.messages.append(data)
            print(f"   Sent message: {data['type']}")

    # Test connection
    user_id = UUID("00000000-0000-0000-0000-000000000001")
    mock_ws = MockWebSocket()

    await ws_manager.connect(mock_ws, user_id)
    assert user_id in ws_manager.active_connections
    print(f"✅ Connected user: {user_id}")

    # Test broadcast
    from backend.models.task_models import TaskStatusChangeEvent

    event = TaskStatusChangeEvent(
        task_id=uuid4(),
        old_status=TaskStatus.QUEUED,
        new_status=TaskStatus.IN_PROGRESS,
        timestamp=datetime.utcnow()
    )

    await ws_manager.broadcast_task_event(event)
    assert len(mock_ws.messages) == 1
    assert mock_ws.messages[0]["type"] == "task_status_changed"
    print(f"✅ Broadcast event received")

    # Test disconnect
    ws_manager.disconnect(user_id)
    assert user_id not in ws_manager.active_connections
    print(f"✅ Disconnected user: {user_id}")


async def test_task_callback():
    """Test task callback integration"""
    print("\n=== Testing Task Callback ===")

    session_factory = get_session_factory()
    async with session_factory() as session:
        repo = TaskRepository(session)
        ws_manager = get_ws_manager()

        # Create a task
        user_id = UUID("00000000-0000-0000-0000-000000000001")
        thread_id = uuid4()

        task_create = TaskCreate(
            user_id=user_id,
            agent_id="agent_a",
            thread_id=thread_id,
            command_text="@bob test callback"
        )

        task = await repo.create_task(task_create)
        print(f"✅ Created task: {task.id}")

        # Create callback
        callback = TaskProgressCallback(task.id, repo, ws_manager)

        # Test status change
        await callback.on_status_change(TaskStatus.QUEUED, TaskStatus.IN_PROGRESS)
        updated_task = await repo.get_task(task.id)
        assert updated_task.status == TaskStatus.IN_PROGRESS
        assert updated_task.started_at is not None
        print(f"✅ Status changed to: {updated_task.status}")

        # Test progress update
        await callback.on_progress_update(25, "searching")
        updated_task = await repo.get_task(task.id)
        assert updated_task.progress_percentage == 25
        assert updated_task.current_node == "searching"
        print(f"✅ Progress updated: {updated_task.progress_percentage}% ({updated_task.current_node})")

        # Test completion
        await callback.on_status_change(TaskStatus.IN_PROGRESS, TaskStatus.COMPLETED)
        completed_task = await repo.get_task(task.id)
        assert completed_task.status == TaskStatus.COMPLETED
        assert completed_task.completed_at is not None
        print(f"✅ Task completed")


async def test_agent_with_callback():
    """Test agent execution with callback integration"""
    print("\n=== Testing Agent Execution with Callback ===")

    # Initialize agents
    initialize_default_agents()
    bob = AgentRegistry.get_specialist("agent_a")

    if not bob:
        print("❌ Bob agent not found")
        return

    # Initialize Bob's graph
    await bob.initialize()

    session_factory = get_session_factory()
    async with session_factory() as session:
        repo = TaskRepository(session)
        ws_manager = get_ws_manager()

        # Create a task
        user_id = UUID("00000000-0000-0000-0000-000000000001")
        thread_id = uuid4()

        task_create = TaskCreate(
            user_id=user_id,
            agent_id="agent_a",
            thread_id=thread_id,
            command_text="research artificial intelligence"
        )

        task = await repo.create_task(task_create)
        print(f"✅ Created task: {task.id}")

        # Create callback
        callback = TaskProgressCallback(task.id, repo, ws_manager)

        # Create execution context with callback
        context = AgentExecutionContext(
            user_id=user_id,
            thread_id=thread_id,
            command="research artificial intelligence",
            task_callback=callback
        )

        # Execute agent
        print(f"   Executing Bob with callback...")
        result = await bob.execute("research artificial intelligence", context)

        # Check result
        if not result.success:
            print(f"❌ Agent execution failed: {result.error}")
            return

        assert result.success
        print(f"✅ Agent executed successfully")
        print(f"   Response: {result.response[:100]}...")

        # Check final task status
        final_task = await repo.get_task(task.id)
        assert final_task.status == TaskStatus.COMPLETED
        print(f"✅ Final task status: {final_task.status}")
        print(f"   Progress: {final_task.progress_percentage}%")
        print(f"   Started: {final_task.started_at}")
        print(f"   Completed: {final_task.completed_at}")


async def main():
    """Run all tests"""
    print("=" * 60)
    print("Phase 3A: Backend Task Management + WebSocket Tests")
    print("=" * 60)

    try:
        # Test 1: Task Repository
        await test_task_repository()

        # Test 2: WebSocket Manager
        await test_websocket_manager()

        # Test 3: Task Callback
        await test_task_callback()

        # Test 4: Agent with Callback
        await test_agent_with_callback()

        print("\n" + "=" * 60)
        print("✅ All tests passed!")
        print("=" * 60)

    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
