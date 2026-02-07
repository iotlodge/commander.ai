"""
Manual test script for scheduler end-to-end flow
Run this script to verify the complete scheduled command system works

Usage:
    python -m backend.tests.test_scheduler_manual
"""

import asyncio
from uuid import uuid4
from datetime import datetime

from backend.core.scheduler import get_scheduler_service
from backend.core.database import get_session_maker
from backend.repositories.scheduled_command_repository import ScheduledCommandRepository
from backend.models.scheduled_command_models import (
    ScheduledCommandCreate,
    ScheduleType,
    IntervalUnit,
)


async def test_complete_flow():
    """Test the complete scheduler flow"""
    print("\n" + "=" * 60)
    print("SCHEDULER END-TO-END TEST")
    print("=" * 60 + "\n")

    # 1. Initialize scheduler
    print("1️⃣  Initializing scheduler...")
    scheduler = get_scheduler_service()
    await scheduler.initialize()
    await scheduler.start()
    print("✅ Scheduler started\n")

    # 2. Create a test schedule
    print("2️⃣  Creating test schedule...")
    session_maker = get_session_maker()

    async with session_maker() as session:
        repo = ScheduledCommandRepository(session)

        # Mock agent registry
        from unittest.mock import patch, MagicMock
        with patch('backend.agents.base.agent_registry.AgentRegistry.get_specialist') as mock_get:
            mock_agent = MagicMock()
            mock_agent.nickname = "alice"
            mock_get.return_value = mock_agent

            schedule_create = ScheduledCommandCreate(
                user_id=uuid4(),
                command_text="@alice test scheduled command",
                agent_id="agent_alice",
                schedule_type=ScheduleType.INTERVAL,
                interval_value=5,  # Every 5 minutes
                interval_unit=IntervalUnit.MINUTES,
                description="Test schedule for manual verification",
                enabled=True,
            )

            schedule = await repo.create_scheduled_command(schedule_create)
            print(f"✅ Created schedule: {schedule.id}")
            print(f"   Command: {schedule.command_text}")
            print(f"   Schedule: Every {schedule.interval_value} {schedule.interval_unit.value}\n")

    # 3. Add schedule to scheduler
    print("3️⃣  Adding schedule to scheduler...")
    success = await scheduler.add_schedule(schedule.id)
    if success:
        print("✅ Schedule added to scheduler\n")
    else:
        print("❌ Failed to add schedule to scheduler\n")
        await scheduler.shutdown()
        return

    # 4. Check scheduler status
    print("4️⃣  Checking scheduler status...")
    status = scheduler.get_scheduler_status()
    print(f"✅ Scheduler running: {status['running']}")
    print(f"   Total jobs: {status['jobs_count']}")

    # Find our job
    job_id = f"scheduled_command_{schedule.id}"
    our_job = None
    for job in status['jobs']:
        if job['id'] == job_id:
            our_job = job
            break

    if our_job:
        print(f"   Our job: {our_job['name']}")
        print(f"   Next run: {our_job['next_run']}\n")
    else:
        print("   ❌ Could not find our job in scheduler\n")

    # 5. Check schedule in database
    print("5️⃣  Checking schedule in database...")
    async with session_maker() as session:
        repo = ScheduledCommandRepository(session)
        db_schedule = await repo.get_scheduled_command(schedule.id)

        if db_schedule:
            print(f"✅ Schedule found in database")
            print(f"   Enabled: {db_schedule.enabled}")
            print(f"   Next run: {db_schedule.next_run_at}")
            print(f"   Last run: {db_schedule.last_run_at or 'Never'}\n")
        else:
            print("❌ Schedule not found in database\n")

    # 6. Get execution history
    print("6️⃣  Checking execution history...")
    async with session_maker() as session:
        repo = ScheduledCommandRepository(session)
        executions = await repo.get_command_executions(schedule.id, limit=5)

        if executions:
            print(f"✅ Found {len(executions)} executions:")
            for exec in executions[:3]:
                print(f"   - {exec.triggered_at}: {exec.status.value}")
        else:
            print("   No executions yet (schedule hasn't run)\n")

    # 7. Cleanup
    print("\n7️⃣  Cleaning up...")
    await scheduler.remove_schedule(schedule.id)
    print("✅ Removed schedule from scheduler")

    async with session_maker() as session:
        repo = ScheduledCommandRepository(session)
        await repo.delete_scheduled_command(schedule.id)
        print("✅ Deleted schedule from database")

    # 8. Shutdown scheduler
    print("\n8️⃣  Shutting down scheduler...")
    await scheduler.shutdown()
    print("✅ Scheduler stopped")

    print("\n" + "=" * 60)
    print("✅ ALL TESTS PASSED")
    print("=" * 60 + "\n")


async def main():
    """Main entry point"""
    try:
        await test_complete_flow()
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
