"""
Dependency management for commander.ai
Provides singleton instances and dependency injection
"""

import logging
from typing import Optional

from backend.memory.document_store import DocumentStore

logger = logging.getLogger(__name__)

# Global singleton instance
_document_store: Optional[DocumentStore] = None
_instance_count = 0


async def get_document_store() -> DocumentStore:
    """
    Get singleton DocumentStore instance with connection pooling

    This ensures only one DocumentStore instance exists per application lifecycle,
    preventing connection pool exhaustion and reducing resource usage.

    Returns:
        Shared DocumentStore instance (connected and ready to use)

    Usage:
        ```python
        from backend.core.dependencies import get_document_store

        doc_store = await get_document_store()
        # Use doc_store (no disconnect needed)
        results = await doc_store.search_collection(...)
        ```
    """
    global _document_store, _instance_count

    if _document_store is None:
        logger.info("Initializing DocumentStore singleton")
        _document_store = DocumentStore()
        await _document_store.connect()
        _instance_count = 1
        logger.info("DocumentStore singleton initialized successfully")
    else:
        _instance_count += 1
        if _instance_count > 10:
            logger.warning(
                f"DocumentStore singleton accessed {_instance_count} times. "
                "This is expected behavior (shared instance)."
            )

    return _document_store


async def shutdown_document_store() -> None:
    """
    Cleanup DocumentStore singleton on application shutdown

    Should be called during application lifecycle shutdown event.

    Usage:
        ```python
        # In FastAPI app
        @app.on_event("shutdown")
        async def on_shutdown():
            from backend.core.dependencies import shutdown_document_store
            await shutdown_document_store()
        ```
    """
    global _document_store, _instance_count

    if _document_store is not None:
        logger.info("Shutting down DocumentStore singleton")
        await _document_store.disconnect()
        _document_store = None
        _instance_count = 0
        logger.info("DocumentStore singleton shut down successfully")


def reset_document_store() -> None:
    """
    Reset DocumentStore singleton (for testing only)

    WARNING: Only use this in test cleanup!
    """
    global _document_store, _instance_count
    _document_store = None
    _instance_count = 0
