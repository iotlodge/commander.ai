"""
Pydantic schemas for memory system
"""

from datetime import datetime
from enum import Enum
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


class MemoryType(str, Enum):
    """Types of memories"""

    EPISODIC = "episodic"  # Specific events/interactions
    SEMANTIC = "semantic"  # Facts and knowledge
    PROCEDURAL = "procedural"  # How to do things


class ConversationRole(str, Enum):
    """Roles in conversation"""

    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class ConversationMessage(BaseModel):
    """A single message in conversation history"""

    id: UUID | None = None
    user_id: UUID
    agent_id: str
    thread_id: UUID
    role: ConversationRole
    content: str
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime | None = None


class AgentMemory(BaseModel):
    """A stored memory for an agent"""

    id: UUID | None = None
    agent_id: str
    user_id: UUID | None = None  # None for shared memories
    memory_type: MemoryType
    content: str
    embedding: list[float] | None = None
    importance_score: float = Field(default=0.5, ge=0.0, le=1.0)
    access_count: int = 0
    last_accessed_at: datetime | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime | None = None


class MemorySearchResult(BaseModel):
    """Result from semantic memory search"""

    memory: AgentMemory
    similarity_score: float = Field(ge=0.0, le=1.0)


class CheckpointData(BaseModel):
    """LangGraph checkpoint data"""

    checkpoint_id: str
    agent_id: str
    user_id: UUID
    thread_id: UUID
    state_data: dict[str, Any]
    node_name: str | None = None
    parent_checkpoint_id: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime | None = None


class ConversationContext(BaseModel):
    """Complete context for an agent's execution"""

    graph_state: dict[str, Any] | None = None  # Latest checkpoint state
    recent_conversation: list[ConversationMessage] = Field(default_factory=list)
    relevant_memories: list[MemorySearchResult] = Field(default_factory=list)
    thread_id: UUID
    user_id: UUID
    agent_id: str
