"""
Parent Agent State Definition
State for the orchestrator that delegates to specialist agents
"""

from typing import Any, TypedDict
from uuid import UUID


class ParentAgentState(TypedDict):
    """State for Parent Agent (Orchestrator)"""

    # User input
    query: str  # Original user command
    user_id: UUID
    thread_id: UUID

    # Context from memory
    conversation_context: dict[str, Any]

    # Decomposition
    task_type: str | None  # "research", "compliance", "data_analysis", "multi_specialist"
    subtasks: list[dict[str, Any]]  # List of subtasks with assigned agents
    decomposition_reasoning: str | None  # LLM reasoning for decomposition

    # Delegation
    specialist_assignments: dict[str, str]  # agent_nickname -> subtask
    specialist_results: dict[str, dict[str, Any]]  # agent_nickname -> result

    # Aggregation
    final_response: str | None
    error: str | None

    # Metadata
    current_step: str  # Track progress
    requires_consultation: bool  # If multiple specialists needed
    metrics: Any | None  # ExecutionMetrics for tracking token usage
