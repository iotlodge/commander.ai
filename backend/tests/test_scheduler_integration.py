"""
Integration test for the complete scheduler system
Tests the full flow from API → Database → Scheduler → Execution

Usage:
    python -m backend.tests.test_scheduler_integration
"""

import asyncio
import time
from uuid import uuid4
from datetime import datetime

from backend.core.scheduler import get_scheduler_service
from backend.core.database import get_session_maker
from backend.repositories.scheduled_command_repository import ScheduledCommandRepository
from backend.models.scheduled_command_models import (
    ScheduledCommandCreate,
    ScheduledCommandUpdate,
    ScheduledCommandExecutionCreate,
    ScheduleType,
    IntervalUnit,
)


async def test_complete_integration():
    """Test the complete scheduler integration flow"""
    print("\n" + "=" * 70)
    print("SCHEDULER INTEGRATION TEST - Full End-to-End Validation")
    print("=" * 70 + "\n")

    test_results = {
        "passed": 0,
        "failed": 0,
        "tests": []
    }

    def log_test(name: str, passed: bool, message: str = ""):
        status = "✅ PASS" if passed else "❌ FAIL"
        test_results["tests"].append({"name": name, "passed": passed, "message": message})
        if passed:
            test_results["passed"] += 1
            print(f"{status} - {name}")
        else:
            test_results["failed"] += 1
            print(f"{status} - {name}")
            if message:
                print(f"       {message}")

    # Setup
    scheduler = get_scheduler_service()
    session_maker = get_session_maker()
    test_user_id = uuid4()

    # Track created schedules for cleanup
    created_schedule_ids = []

    try:
        # Test 1: Initialize Scheduler
        print("\n📋 Test 1: Scheduler Initialization")
        await scheduler.initialize()
        await scheduler.start()
        status = scheduler.get_scheduler_status()
        log_test(
            "Scheduler initializes and starts",
            status["running"] and status["initialized"]
        )

        # Test 2: Create Interval Schedule
        print("\n📋 Test 2: Create Interval Schedule")
        async with session_maker() as session:
            repo = ScheduledCommandRepository(session)

            # Mock agent registry
            from unittest.mock import patch, MagicMock
            with patch('backend.agents.base.agent_registry.AgentRegistry.get_specialist') as mock_get:
                mock_agent = MagicMock()
                mock_agent.nickname = "alice"
                mock_get.return_value = mock_agent

                schedule_data = ScheduledCommandCreate(
                    user_id=test_user_id,
                    command_text="@alice test integration",
                    agent_id="agent_alice",
                    schedule_type=ScheduleType.INTERVAL,
                    interval_value=5,
                    interval_unit=IntervalUnit.MINUTES,
                    description="Integration test interval schedule",
                    enabled=True,
                )

                schedule = await repo.create_scheduled_command(schedule_data)
                created_schedule_ids.append(schedule.id)

                log_test(
                    "Interval schedule created in database",
                    schedule.id is not None and schedule.enabled
                )

        # Test 3: Add Schedule to Scheduler
        print("\n📋 Test 3: Add to Scheduler")
        success = await scheduler.add_schedule(schedule.id)
        log_test("Schedule added to APScheduler", success)

        # Test 4: Verify Schedule in Scheduler
        print("\n📋 Test 4: Verify in Scheduler")
        status = scheduler.get_scheduler_status()
        job_id = f"scheduled_command_{schedule.id}"
        job_exists = any(job["id"] == job_id for job in status["jobs"])
        log_test("Schedule appears in scheduler jobs", job_exists)

        # Test 5: Create Cron Schedule
        print("\n📋 Test 5: Create Cron Schedule")
        async with session_maker() as session:
            repo = ScheduledCommandRepository(session)

            with patch('backend.agents.base.agent_registry.AgentRegistry.get_specialist') as mock_get:
                mock_agent = MagicMock()
                mock_agent.nickname = "bob"
                mock_get.return_value = mock_agent

                cron_schedule_data = ScheduledCommandCreate(
                    user_id=test_user_id,
                    command_text="@bob test cron",
                    agent_id="agent_bob",
                    schedule_type=ScheduleType.CRON,
                    cron_expression="0 9 * * *",
                    timezone="UTC",
                    description="Integration test cron schedule",
                    enabled=True,
                )

                cron_schedule = await repo.create_scheduled_command(cron_schedule_data)
                created_schedule_ids.append(cron_schedule.id)

                log_test(
                    "Cron schedule created in database",
                    cron_schedule.id is not None
                )

        # Test 6: Add Cron to Scheduler
        print("\n📋 Test 6: Add Cron to Scheduler")
        success = await scheduler.add_schedule(cron_schedule.id)
        log_test("Cron schedule added to APScheduler", success)

        # Test 7: List User Schedules
        print("\n📋 Test 7: List User Schedules")
        async with session_maker() as session:
            repo = ScheduledCommandRepository(session)
            schedules = await repo.get_user_scheduled_commands(
                user_id=test_user_id,
                enabled_only=True
            )
            log_test(
                "List returns both schedules",
                len(schedules) == 2,
                f"Expected 2, got {len(schedules)}"
            )

        # Test 8: Update Schedule
        print("\n📋 Test 8: Update Schedule")
        async with session_maker() as session:
            repo = ScheduledCommandRepository(session)
            update = ScheduledCommandUpdate(
                interval_value=10,
                description="Updated description"
            )
            updated = await repo.update_scheduled_command(schedule.id, update)
            log_test(
                "Schedule updated successfully",
                updated.interval_value == 10 and updated.description == "Updated description"
            )

        # Test 9: Update in Scheduler
        print("\n📋 Test 9: Update in Scheduler")
        await scheduler.update_schedule(schedule.id)
        status = scheduler.get_scheduler_status()
        job_exists = any(job["id"] == job_id for job in status["jobs"])
        log_test("Updated schedule still in scheduler", job_exists)

        # Test 10: Disable Schedule
        print("\n📋 Test 10: Disable Schedule")
        async with session_maker() as session:
            repo = ScheduledCommandRepository(session)
            disable_update = ScheduledCommandUpdate(enabled=False)
            disabled = await repo.update_scheduled_command(schedule.id, disable_update)
            log_test("Schedule disabled in database", not disabled.enabled)

        # Test 11: Remove from Scheduler
        print("\n📋 Test 11: Remove from Scheduler")
        await scheduler.remove_schedule(schedule.id)
        status = scheduler.get_scheduler_status()
        job_removed = not any(job["id"] == job_id for job in status["jobs"])
        log_test("Disabled schedule removed from scheduler", job_removed)

        # Test 12: Re-enable Schedule
        print("\n📋 Test 12: Re-enable Schedule")
        async with session_maker() as session:
            repo = ScheduledCommandRepository(session)
            enable_update = ScheduledCommandUpdate(enabled=True)
            enabled = await repo.update_scheduled_command(schedule.id, enable_update)
            log_test("Schedule re-enabled in database", enabled.enabled)

        # Test 13: Re-add to Scheduler
        print("\n📋 Test 13: Re-add to Scheduler")
        success = await scheduler.add_schedule(schedule.id)
        status = scheduler.get_scheduler_status()
        job_back = any(job["id"] == job_id for job in status["jobs"])
        log_test("Re-enabled schedule back in scheduler", success and job_back)

        # Test 14: Count User Schedules
        print("\n📋 Test 14: Count User Schedules")
        async with session_maker() as session:
            repo = ScheduledCommandRepository(session)
            count = await repo.count_user_schedules(test_user_id)
            log_test("Count returns correct number", count == 2)

        # Test 15: Filter by Agent
        print("\n📋 Test 15: Filter by Agent")
        async with session_maker() as session:
            repo = ScheduledCommandRepository(session)
            alice_schedules = await repo.get_user_scheduled_commands(
                user_id=test_user_id,
                agent_id="agent_alice"
            )
            log_test(
                "Filter by agent works",
                len(alice_schedules) == 1 and alice_schedules[0].agent_id == "agent_alice"
            )

        # Test 16: Next Run Calculation
        print("\n📋 Test 16: Next Run Calculation")
        async with session_maker() as session:
            repo = ScheduledCommandRepository(session)
            schedule_with_next = await repo.get_scheduled_command(schedule.id)
            log_test(
                "Next run time is calculated",
                schedule_with_next.next_run_at is not None,
                f"Next run: {schedule_with_next.next_run_at}"
            )

        # Test 17: Scheduler Status
        print("\n📋 Test 17: Scheduler Status")
        status = scheduler.get_scheduler_status()
        log_test(
            "Scheduler status contains all info",
            "running" in status and "jobs_count" in status and "jobs" in status
        )

        # Test 18: Create Execution Record
        print("\n📋 Test 18: Create Execution Record")
        async with session_maker() as session:
            repo = ScheduledCommandRepository(session)
            execution_create = ScheduledCommandExecutionCreate(
                scheduled_command_id=schedule.id,
                triggered_at=datetime.utcnow()
            )
            execution = await repo.create_execution(execution_create)
            log_test(
                "Execution record created",
                execution.id is not None and str(execution.scheduled_command_id) == str(schedule.id)
            )

        # Test 19: Get Execution History
        print("\n📋 Test 19: Get Execution History")
        async with session_maker() as session:
            repo = ScheduledCommandRepository(session)
            executions = await repo.get_command_executions(schedule.id, limit=10)
            log_test(
                "Execution history retrieved",
                len(executions) > 0,
                f"Found {len(executions)} execution(s)"
            )

        # Test 20: Delete Schedule
        print("\n📋 Test 20: Delete Schedule")
        async with session_maker() as session:
            repo = ScheduledCommandRepository(session)
            success = await repo.delete_scheduled_command(cron_schedule.id)
            log_test("Schedule deleted from database", success)
            created_schedule_ids.remove(cron_schedule.id)

    except Exception as e:
        print(f"\n❌ TEST FAILED WITH EXCEPTION: {e}")
        import traceback
        traceback.print_exc()
        test_results["failed"] += 1

    finally:
        # Cleanup
        print("\n🧹 Cleaning up...")

        # Remove from scheduler
        for schedule_id in created_schedule_ids:
            try:
                await scheduler.remove_schedule(schedule_id)
                print(f"   Removed schedule {schedule_id} from scheduler")
            except Exception as e:
                print(f"   Warning: Could not remove schedule {schedule_id}: {e}")

        # Delete from database
        async with session_maker() as session:
            repo = ScheduledCommandRepository(session)
            for schedule_id in created_schedule_ids:
                try:
                    await repo.delete_scheduled_command(schedule_id)
                    print(f"   Deleted schedule {schedule_id} from database")
                except Exception as e:
                    print(f"   Warning: Could not delete schedule {schedule_id}: {e}")

        # Shutdown scheduler
        await scheduler.shutdown()
        print("   Scheduler shut down")

    # Summary
    print("\n" + "=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)
    print(f"✅ Passed: {test_results['passed']}")
    print(f"❌ Failed: {test_results['failed']}")
    print(f"📊 Total:  {test_results['passed'] + test_results['failed']}")

    if test_results['failed'] == 0:
        print("\n🎉 ALL TESTS PASSED! The scheduler system is working correctly.")
    else:
        print("\n⚠️  SOME TESTS FAILED. Review the output above.")
        print("\nFailed tests:")
        for test in test_results['tests']:
            if not test['passed']:
                print(f"  - {test['name']}")
                if test['message']:
                    print(f"    {test['message']}")

    print("=" * 70 + "\n")

    return test_results['failed'] == 0


async def main():
    """Main entry point"""
    try:
        success = await test_complete_integration()
        exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ FATAL ERROR: {e}")
        import traceback
        traceback.print_exc()
        exit(1)


if __name__ == "__main__":
    asyncio.run(main())
