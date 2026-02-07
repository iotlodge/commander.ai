"""
Sue (Compliance Specialist) State Definition
"""

from typing import Any, TypedDict
from uuid import UUID


class ComplianceAgentState(TypedDict):
    """State for Sue - Compliance Specialist"""

    # User input
    query: str
    user_id: UUID
    thread_id: UUID

    # Context
    conversation_context: dict[str, Any]

    # Compliance review process
    policies_to_check: list[str]
    compliance_issues: list[dict[str, str]]
    recommendations: list[str]

    # Output
    final_response: str | None
    error: str | None

    # Metadata
    current_step: str
    risk_level: str | None  # "low", "medium", "high"
    model_config: Any | None  # ModelConfig for LLM instantiation
