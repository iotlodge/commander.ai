"""
Agent prompt models
"""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class AgentPrompt(BaseModel):
    """Represents a system prompt for an agent"""

    id: UUID
    agent_id: str
    nickname: str
    description: str
    prompt_text: str
    active: bool = True
    prompt_type: str = "system"
    variables: dict = Field(default_factory=dict)
    created_at: datetime
    updated_at: datetime


class PromptCreate(BaseModel):
    """Request to create a new prompt"""

    agent_id: str
    nickname: str
    description: str
    prompt_text: str
    active: bool = True
    prompt_type: str = "system"
    variables: dict = Field(default_factory=dict)


class PromptUpdate(BaseModel):
    """Update prompt"""

    prompt_text: str | None = None
    active: bool | None = None
    variables: dict | None = None
