"""
Reflection Agent State Definition
State for Maya (Reflection Specialist)
"""

from typing import Any, TypedDict
from uuid import UUID


class ReflectionAgentState(TypedDict):
    """State for Reflection Agent (@maya)"""

    # Input
    query: str  # Content to review/reflect upon
    user_id: UUID
    thread_id: UUID
    conversation_context: dict[str, Any]

    # Reflection process
    initial_analysis: str | None  # First pass analysis
    identified_issues: list[dict[str, Any]]  # Issues found
    suggested_improvements: list[str]  # Improvement suggestions
    refined_output: str | None  # Improved version

    # Output
    final_response: str | None
    reflection_score: float | None  # Quality score 0-1
    error: str | None

    # Metadata
    current_step: str
    task_callback: Any  # TaskProgressCallback
