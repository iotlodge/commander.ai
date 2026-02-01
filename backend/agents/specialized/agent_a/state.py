"""
Bob (Research Specialist) State Definition
"""

from typing import Any, TypedDict
from uuid import UUID


class ResearchAgentState(TypedDict):
    """State for Bob - Research Specialist"""

    # User input
    query: str
    user_id: UUID
    thread_id: UUID

    # Context
    conversation_context: dict[str, Any]

    # Research process
    search_results: list[dict[str, Any]]
    synthesis: str | None

    # Compliance check
    needs_compliance_review: bool
    compliance_keywords_found: list[str]
    sue_consulted: bool
    compliance_review: str | None

    # Output
    final_response: str | None
    error: str | None

    # Metadata
    current_step: str
    task_callback: Any | None  # TaskProgressCallback (avoid circular import)
