"""
Rex (Data Analyst) State Definition
"""

from typing import Any, TypedDict
from uuid import UUID


class DataAgentState(TypedDict):
    """State for Rex - Data Analyst"""

    # User input
    query: str
    user_id: UUID
    thread_id: UUID

    # Context
    conversation_context: dict[str, Any]

    # Analysis process
    data_source: str | None
    analysis_type: str | None  # "descriptive", "statistical", "visualization"
    findings: list[str]

    # Output
    final_response: str | None
    error: str | None

    # Metadata
    current_step: str
