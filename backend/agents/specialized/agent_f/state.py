"""
Reflexion Agent State Definition
State for Kai (Reflexion Specialist)
"""

from typing import Any, TypedDict
from uuid import UUID


class ReflexionAgentState(TypedDict):
    """State for Reflexion Agent (@kai)"""

    # Input
    query: str  # Problem/task to solve with self-reflection
    user_id: UUID
    thread_id: UUID
    conversation_context: dict[str, Any]

    # Reflexion process
    iteration: int  # Current iteration number
    max_iterations: int  # Maximum iterations allowed
    reasoning_trace: list[dict[str, Any]]  # History of reasoning attempts

    initial_attempt: str | None  # First reasoning attempt
    self_critique: str | None  # Self-critique of reasoning
    identified_flaws: list[str]  # Flaws in reasoning
    improvement_strategy: str | None  # How to improve
    refined_reasoning: str | None  # Improved reasoning

    # Output
    final_response: str | None
    improvement_score: float | None  # How much reasoning improved
    error: str | None

    # Metadata
    current_step: str
    should_iterate: bool  # Whether to continue iterating
    task_callback: Any  # TaskProgressCallback
    metrics: Any  # ExecutionMetrics for tracking token usage
