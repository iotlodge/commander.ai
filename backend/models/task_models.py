"""
Task models for Kanban tracking
"""

from datetime import datetime
from enum import Enum
from uuid import UUID

from pydantic import BaseModel, Field


class TaskStatus(str, Enum):
    """Task lifecycle statuses"""

    QUEUED = "queued"
    IN_PROGRESS = "in_progress"
    TOOL_CALL = "tool_call"  # Agent is calling tools or consulting
    COMPLETED = "completed"
    FAILED = "failed"


class AgentTask(BaseModel):
    """
    Represents a task in the Kanban board
    One task per agent invocation
    """

    id: UUID
    user_id: UUID
    agent_id: str
    agent_nickname: str
    thread_id: UUID
    command_text: str
    status: TaskStatus = TaskStatus.QUEUED
    progress_percentage: int = Field(default=0, ge=0, le=100)
    current_node: str | None = None
    consultation_target_id: str | None = None  # Non-null when status = TOOL_CALL
    consultation_target_nickname: str | None = None
    result: str | None = None
    error_message: str | None = None
    metadata: dict = Field(default_factory=dict)
    created_at: datetime
    started_at: datetime | None = None
    completed_at: datetime | None = None


class TaskCreate(BaseModel):
    """Request to create a new task"""

    user_id: UUID
    agent_id: str
    thread_id: UUID
    command_text: str


class TaskUpdate(BaseModel):
    """Update to a task"""

    status: TaskStatus | None = None
    progress_percentage: int | None = Field(default=None, ge=0, le=100)
    current_node: str | None = None
    consultation_target_id: str | None = None
    result: str | None = None
    error_message: str | None = None


class TaskStatusChangeEvent(BaseModel):
    """WebSocket event for task status change"""

    type: str = "task_status_changed"
    task_id: UUID
    old_status: TaskStatus | None
    new_status: TaskStatus
    timestamp: datetime


class TaskProgressEvent(BaseModel):
    """WebSocket event for task progress update"""

    type: str = "task_progress"
    task_id: UUID
    progress_percentage: int
    current_node: str
    timestamp: datetime


class ConsultationStartedEvent(BaseModel):
    """WebSocket event when consultation begins"""

    type: str = "consultation_started"
    task_id: UUID
    requesting_agent_id: str
    target_agent_id: str
    target_agent_nickname: str
    timestamp: datetime


class ConsultationCompletedEvent(BaseModel):
    """WebSocket event when consultation completes"""

    type: str = "consultation_completed"
    task_id: UUID
    timestamp: datetime
