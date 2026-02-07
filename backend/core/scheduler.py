"""
Command Scheduler Service
APScheduler-based scheduler for executing NLP commands on a schedule
"""

import logging
from datetime import datetime
from uuid import UUID

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from apscheduler.executors.asyncio import AsyncIOExecutor
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from croniter import croniter
import pytz

from backend.core.config import get_settings
from backend.core.database import get_session_maker
from backend.repositories.scheduled_command_repository import ScheduledCommandRepository
from backend.models.scheduled_command_models import ScheduleType, IntervalUnit

logger = logging.getLogger(__name__)


class CommandSchedulerService:
    """
    Service for managing scheduled command execution using APScheduler
    """

    def __init__(self):
        self.scheduler: AsyncIOScheduler | None = None
        self._initialized = False

    async def initialize(self):
        """Initialize the scheduler with database-backed job store"""
        if self._initialized:
            logger.warning("Scheduler already initialized")
            return

        settings = get_settings()

        # Configure job stores (use SQLAlchemy to persist jobs)
        jobstores = {
            'default': SQLAlchemyJobStore(url=settings.database_url.replace('+asyncpg', ''))
        }

        # Configure executors
        executors = {
            'default': AsyncIOExecutor()
        }

        # Configure job defaults
        job_defaults = {
            'coalesce': True,  # Combine multiple missed runs into one
            'max_instances': 1,  # Only one instance of each job at a time
            'misfire_grace_time': 300,  # 5 minutes grace period for missed jobs
        }

        # Create scheduler
        self.scheduler = AsyncIOScheduler(
            jobstores=jobstores,
            executors=executors,
            job_defaults=job_defaults,
            timezone=pytz.UTC,
        )

        logger.info("Scheduler initialized")
        self._initialized = True

    async def start(self):
        """Start the scheduler and load all enabled schedules"""
        if not self._initialized:
            await self.initialize()

        if self.scheduler and not self.scheduler.running:
            self.scheduler.start()
            logger.info("Scheduler started")

            # Load all enabled schedules from database
            await self._load_enabled_schedules()
        else:
            logger.warning("Scheduler already running")

    async def shutdown(self):
        """Shutdown the scheduler gracefully"""
        if self.scheduler and self.scheduler.running:
            self.scheduler.shutdown(wait=True)
            logger.info("Scheduler shutdown complete")
            self._initialized = False

    async def _load_enabled_schedules(self):
        """Load all enabled schedules from database and add to scheduler"""
        session_maker = get_session_maker()
        async with session_maker() as session:
            repo = ScheduledCommandRepository(session)
            schedules = await repo.get_enabled_scheduled_commands()

            logger.info(f"Loading {len(schedules)} enabled schedules")

            for schedule in schedules:
                try:
                    await self.add_schedule(schedule.id)
                except Exception as e:
                    logger.error(f"Failed to load schedule {schedule.id}: {e}", exc_info=True)

    async def add_schedule(self, schedule_id: UUID) -> bool:
        """
        Add a schedule to the scheduler

        Args:
            schedule_id: UUID of the scheduled command

        Returns:
            True if successfully added, False otherwise
        """
        if not self.scheduler:
            logger.error("Scheduler not initialized")
            return False

        session_maker = get_session_maker()
        async with session_maker() as session:
            repo = ScheduledCommandRepository(session)
            schedule = await repo.get_scheduled_command(schedule_id)

            if not schedule:
                logger.error(f"Schedule {schedule_id} not found")
                return False

            if not schedule.enabled:
                logger.warning(f"Schedule {schedule_id} is disabled, not adding to scheduler")
                return False

            # Create appropriate trigger
            trigger = self._create_trigger(schedule)
            if not trigger:
                logger.error(f"Failed to create trigger for schedule {schedule_id}")
                return False

            # Calculate and update next_run_at
            next_run = self._calculate_next_run(schedule)
            if next_run:
                await repo.update_next_run(schedule_id, next_run)

            # Add job to scheduler
            job_id = f"scheduled_command_{schedule_id}"

            # Import here to avoid circular import
            from backend.jobs.scheduled_command_job import execute_scheduled_command

            self.scheduler.add_job(
                execute_scheduled_command,
                trigger=trigger,
                id=job_id,
                name=f"{schedule.agent_nickname}: {schedule.command_text[:50]}",
                args=[str(schedule_id)],
                replace_existing=True,
            )

            logger.info(f"Added schedule {schedule_id} to scheduler (next run: {next_run})")
            return True

    async def remove_schedule(self, schedule_id: UUID) -> bool:
        """
        Remove a schedule from the scheduler

        Args:
            schedule_id: UUID of the scheduled command

        Returns:
            True if successfully removed, False otherwise
        """
        if not self.scheduler:
            logger.error("Scheduler not initialized")
            return False

        job_id = f"scheduled_command_{schedule_id}"

        try:
            self.scheduler.remove_job(job_id)
            logger.info(f"Removed schedule {schedule_id} from scheduler")
            return True
        except Exception as e:
            logger.error(f"Failed to remove schedule {schedule_id}: {e}")
            return False

    async def update_schedule(self, schedule_id: UUID) -> bool:
        """
        Update a schedule in the scheduler (remove and re-add)

        Args:
            schedule_id: UUID of the scheduled command

        Returns:
            True if successfully updated, False otherwise
        """
        # Remove existing job
        await self.remove_schedule(schedule_id)

        # Add updated job
        return await self.add_schedule(schedule_id)

    async def pause_schedule(self, schedule_id: UUID) -> bool:
        """
        Pause a schedule (keeps it in scheduler but won't execute)

        Args:
            schedule_id: UUID of the scheduled command

        Returns:
            True if successfully paused, False otherwise
        """
        if not self.scheduler:
            logger.error("Scheduler not initialized")
            return False

        job_id = f"scheduled_command_{schedule_id}"

        try:
            self.scheduler.pause_job(job_id)
            logger.info(f"Paused schedule {schedule_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to pause schedule {schedule_id}: {e}")
            return False

    async def resume_schedule(self, schedule_id: UUID) -> bool:
        """
        Resume a paused schedule

        Args:
            schedule_id: UUID of the scheduled command

        Returns:
            True if successfully resumed, False otherwise
        """
        if not self.scheduler:
            logger.error("Scheduler not initialized")
            return False

        job_id = f"scheduled_command_{schedule_id}"

        try:
            self.scheduler.resume_job(job_id)
            logger.info(f"Resumed schedule {schedule_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to resume schedule {schedule_id}: {e}")
            return False

    def _create_trigger(self, schedule):
        """
        Create an APScheduler trigger from a ScheduledCommand

        Args:
            schedule: ScheduledCommand object

        Returns:
            CronTrigger or IntervalTrigger
        """
        if schedule.schedule_type == ScheduleType.CRON:
            # Parse cron expression
            if not schedule.cron_expression:
                logger.error(f"Schedule {schedule.id} has no cron expression")
                return None

            try:
                # Parse timezone
                tz = pytz.timezone(schedule.timezone)

                # Create cron trigger
                return CronTrigger.from_crontab(schedule.cron_expression, timezone=tz)
            except Exception as e:
                logger.error(f"Failed to parse cron expression '{schedule.cron_expression}': {e}")
                return None

        elif schedule.schedule_type == ScheduleType.INTERVAL:
            # Create interval trigger
            if not schedule.interval_value or not schedule.interval_unit:
                logger.error(f"Schedule {schedule.id} missing interval configuration")
                return None

            # Convert interval unit to kwargs for IntervalTrigger
            interval_kwargs = {}
            if schedule.interval_unit == IntervalUnit.MINUTES:
                interval_kwargs['minutes'] = schedule.interval_value
            elif schedule.interval_unit == IntervalUnit.HOURS:
                interval_kwargs['hours'] = schedule.interval_value
            elif schedule.interval_unit == IntervalUnit.DAYS:
                interval_kwargs['days'] = schedule.interval_value
            else:
                logger.error(f"Unknown interval unit: {schedule.interval_unit}")
                return None

            return IntervalTrigger(**interval_kwargs)

        else:
            logger.error(f"Unknown schedule type: {schedule.schedule_type}")
            return None

    def _calculate_next_run(self, schedule) -> datetime | None:
        """
        Calculate the next run time for a schedule

        Args:
            schedule: ScheduledCommand object

        Returns:
            Next run datetime (UTC) or None if error
        """
        try:
            if schedule.schedule_type == ScheduleType.CRON:
                # Use croniter to calculate next run
                tz = pytz.timezone(schedule.timezone)
                now = datetime.now(tz)

                cron = croniter(schedule.cron_expression, now)
                next_run_local = cron.get_next(datetime)

                # Convert to UTC
                return next_run_local.astimezone(pytz.UTC)

            elif schedule.schedule_type == ScheduleType.INTERVAL:
                # For intervals, next run is now + interval
                from datetime import timedelta

                now_utc = datetime.now(pytz.UTC)

                if schedule.interval_unit == IntervalUnit.MINUTES:
                    delta = timedelta(minutes=schedule.interval_value)
                elif schedule.interval_unit == IntervalUnit.HOURS:
                    delta = timedelta(hours=schedule.interval_value)
                elif schedule.interval_unit == IntervalUnit.DAYS:
                    delta = timedelta(days=schedule.interval_value)
                else:
                    return None

                return now_utc + delta

        except Exception as e:
            logger.error(f"Failed to calculate next run for schedule {schedule.id}: {e}")
            return None

    def get_scheduler_status(self) -> dict:
        """
        Get current scheduler status

        Returns:
            Dictionary with scheduler status information
        """
        if not self.scheduler:
            return {
                "running": False,
                "initialized": self._initialized,
                "jobs_count": 0,
                "jobs": []
            }

        jobs = []
        for job in self.scheduler.get_jobs():
            jobs.append({
                "id": job.id,
                "name": job.name,
                "next_run": job.next_run_time.isoformat() if job.next_run_time else None,
            })

        return {
            "running": self.scheduler.running,
            "initialized": self._initialized,
            "jobs_count": len(jobs),
            "jobs": jobs,
        }


# Global scheduler instance
_scheduler_service: CommandSchedulerService | None = None


def get_scheduler_service() -> CommandSchedulerService:
    """Get or create the global scheduler service instance"""
    global _scheduler_service

    if _scheduler_service is None:
        _scheduler_service = CommandSchedulerService()

    return _scheduler_service
