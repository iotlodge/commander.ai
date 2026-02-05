"""
Chat Agent State Definition
"""

from typing import Any, TypedDict
from uuid import UUID


class ChatAgentState(TypedDict):
    """State for Chat Assistant"""

    # Input
    query: str  # Current user message
    user_id: UUID
    thread_id: UUID

    # Context
    conversation_context: dict[str, Any]
    messages: list[dict[str, str]]  # [{role: "user/assistant", content: "..."}]

    # Output
    response: str | None
    error: str | None

    # Metadata
    current_step: str
    task_callback: Any | None  # TaskProgressCallback (avoid circular import)
    metrics: Any | None  # ExecutionMetrics for tracking token usage
