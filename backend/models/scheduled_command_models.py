"""
Scheduled Command models for NLP command scheduling
"""

from datetime import datetime
from enum import Enum
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


class ScheduleType(str, Enum):
    """Schedule type enumeration"""
    CRON = "cron"
    INTERVAL = "interval"


class IntervalUnit(str, Enum):
    """Interval unit enumeration"""
    MINUTES = "minutes"
    HOURS = "hours"
    DAYS = "days"


class ExecutionStatus(str, Enum):
    """Execution status enumeration"""
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    TIMEOUT = "timeout"


class ScheduledCommand(BaseModel):
    """Represents a scheduled command"""
    id: UUID
    user_id: UUID

    # Command details
    command_text: str
    agent_id: str
    agent_nickname: str

    # Schedule configuration
    schedule_type: ScheduleType
    cron_expression: str | None = None
    interval_value: int | None = None
    interval_unit: IntervalUnit | None = None
    timezone: str = "UTC"

    # Status
    enabled: bool = True
    next_run_at: datetime | None = None
    last_run_at: datetime | None = None
    last_run_status: ExecutionStatus | None = None

    # Configuration
    max_retries: int = 3
    retry_delay_minutes: int = 5
    timeout_seconds: int = 300
    description: str | None = None
    tags: list[str] = Field(default_factory=list)
    metadata: dict = Field(default_factory=dict)

    # Audit
    created_at: datetime
    updated_at: datetime


class ScheduledCommandCreate(BaseModel):
    """Request to create a scheduled command"""
    user_id: UUID
    command_text: str
    agent_id: str

    # Schedule configuration
    schedule_type: ScheduleType
    cron_expression: str | None = None
    interval_value: int | None = None
    interval_unit: IntervalUnit | None = None
    timezone: str = "UTC"

    # Status
    enabled: bool = True

    # Optional configuration
    max_retries: int = Field(default=3, ge=0, le=10)
    retry_delay_minutes: int = Field(default=5, ge=1, le=60)
    timeout_seconds: int = Field(default=300, ge=30, le=3600)
    description: str | None = None
    tags: list[str] = Field(default_factory=list)
    metadata: dict = Field(default_factory=dict)

    @field_validator("interval_value")
    @classmethod
    def validate_interval_value(cls, v: int | None, info) -> int | None:
        """Validate interval value meets minimum requirements"""
        if v is not None:
            schedule_type = info.data.get("schedule_type")
            interval_unit = info.data.get("interval_unit")

            if schedule_type == ScheduleType.INTERVAL:
                # Enforce 5-minute minimum interval
                if interval_unit == IntervalUnit.MINUTES and v < 5:
                    raise ValueError("Interval must be at least 5 minutes")
                if v < 1:
                    raise ValueError("Interval must be at least 1")

        return v

    @field_validator("cron_expression")
    @classmethod
    def validate_cron_expression(cls, v: str | None, info) -> str | None:
        """Validate cron expression syntax"""
        if v is not None:
            schedule_type = info.data.get("schedule_type")
            if schedule_type == ScheduleType.CRON:
                # Import croniter to validate syntax
                try:
                    from croniter import croniter
                    if not croniter.is_valid(v):
                        raise ValueError("Invalid cron expression")
                except ImportError:
                    # If croniter not installed, skip validation
                    pass

        return v


class ScheduledCommandUpdate(BaseModel):
    """Update to a scheduled command"""
    command_text: str | None = None

    # Schedule configuration
    schedule_type: ScheduleType | None = None
    cron_expression: str | None = None
    interval_value: int | None = None
    interval_unit: IntervalUnit | None = None
    timezone: str | None = None

    # Configuration
    enabled: bool | None = None
    max_retries: int | None = Field(default=None, ge=0, le=10)
    retry_delay_minutes: int | None = Field(default=None, ge=1, le=60)
    timeout_seconds: int | None = Field(default=None, ge=30, le=3600)
    description: str | None = None
    tags: list[str] | None = None
    metadata: dict | None = None


class ScheduledCommandExecution(BaseModel):
    """Represents a single execution of a scheduled command"""
    id: UUID
    scheduled_command_id: UUID
    task_id: UUID | None = None

    triggered_at: datetime
    started_at: datetime | None = None
    completed_at: datetime | None = None
    status: ExecutionStatus = ExecutionStatus.PENDING

    result_summary: str | None = None
    error_message: str | None = None
    retry_count: int = 0
    execution_duration_ms: int | None = None
    tokens_used: int | None = None
    llm_calls: int | None = None

    metadata: dict = Field(default_factory=dict)


class ScheduledCommandExecutionCreate(BaseModel):
    """Request to create an execution record"""
    scheduled_command_id: UUID
    task_id: UUID | None = None
    triggered_at: datetime | None = None


class ScheduledCommandExecutionUpdate(BaseModel):
    """Update to an execution record"""
    task_id: UUID | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None
    status: ExecutionStatus | None = None
    result_summary: str | None = None
    error_message: str | None = None
    retry_count: int | None = None
    execution_duration_ms: int | None = None
    tokens_used: int | None = None
    llm_calls: int | None = None
    metadata: dict | None = None
