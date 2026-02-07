"""
Agent model configuration Pydantic models
"""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class ApprovedModel(BaseModel):
    """Represents an approved LLM model in the registry"""

    id: UUID
    provider: str  # 'openai', 'anthropic', 'huggingface'
    model_name: str
    model_display_name: str | None = None
    mode: str | None = None  # 'reasoning', 'chat', 'planning', etc.
    context_window: int | None = None
    supports_function_calling: bool = False
    approved: bool = False
    version: str | None = None
    deprecated: bool = False
    replacement_model_id: UUID | None = None
    cost_per_1k_input: float | None = None
    cost_per_1k_output: float | None = None
    default_params: dict = Field(default_factory=dict)
    description: str | None = None
    created_at: datetime
    updated_at: datetime


class AgentModelConfig(BaseModel):
    """Represents an agent's model configuration"""

    id: UUID
    agent_id: str
    nickname: str
    provider: str
    model_name: str
    temperature: float = 0.7
    max_tokens: int = 2000
    model_params: dict = Field(default_factory=dict)
    version: int = 1
    active: bool = True
    created_at: datetime
    updated_at: datetime
    created_by: UUID | None = None
    updated_by: UUID | None = None


class AgentModelUpdate(BaseModel):
    """Request to update an agent's model configuration"""

    provider: str
    model_name: str
    temperature: float | None = None
    max_tokens: int | None = None
    model_params: dict | None = None


class ModelConfigResponse(BaseModel):
    """Response containing agent's current model configuration"""

    agent_id: str
    nickname: str
    provider: str
    model_name: str
    model_display_name: str | None = None
    temperature: float
    max_tokens: int
    model_params: dict
    version: int
    supports_function_calling: bool = False
    context_window: int | None = None


class ApprovedModelsResponse(BaseModel):
    """Response containing list of approved models"""

    models: list[ApprovedModel]
    total: int
