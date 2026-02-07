"""
State definition for DocumentManager agent
"""

from typing import Any, TypedDict
from uuid import UUID


class DocumentManagerState(TypedDict):
    """State for document management workflow"""

    # Input
    query: str
    user_id: UUID
    thread_id: UUID
    conversation_context: dict[str, Any]

    # Action routing
    action_type: str  # "load_file", "search_collection", "search_all", "create_collection", "delete_collection", "list_collections"
    action_params: dict[str, Any]

    # Collection management
    collection_id: str | None
    collection_name: str | None
    collection_list: list[dict] | None

    # Document processing
    file_path: str | None
    raw_content: str | None
    chunks: list[dict] | None

    # Web search
    search_query: str | None
    web_documents: list[dict] | None  # Tavily search results formatted for storage

    # Search results (semantic search in collections)
    search_results: list[dict] | None

    # Output
    final_response: str | None
    error: str | None
    current_step: str
    task_callback: Any | None
    model_config: Any | None  # ModelConfig for LLM instantiation
