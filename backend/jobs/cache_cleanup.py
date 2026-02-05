"""
Web Cache Cleanup Job

Removes stale web cache entries based on TTL
Run daily via cron or APScheduler
"""

import logging
from datetime import datetime, timezone, timedelta

from backend.core.dependencies import get_document_store
from backend.core.config import get_settings

logger = logging.getLogger(__name__)


async def cleanup_stale_web_cache() -> dict[str, int]:
    """
    Remove web cache entries older than TTL

    Returns:
        Dictionary with cleanup statistics:
        {
            "collections_processed": int,
            "total_chunks_deleted": int,
            "errors": int
        }

    Usage:
        ```python
        # In APScheduler or cron job
        from backend.jobs.cache_cleanup import cleanup_stale_web_cache

        stats = await cleanup_stale_web_cache()
        logger.info(f"Cache cleanup completed: {stats}")
        ```
    """
    settings = get_settings()
    doc_store = await get_document_store()

    stats = {
        "collections_processed": 0,
        "total_chunks_deleted": 0,
        "errors": 0,
    }

    try:
        # Get all collections
        collections = await doc_store.qdrant_client.get_collections()

        # Filter for web_cache collections
        cache_prefix = settings.web_cache_collection_prefix
        cache_collections = [
            c for c in collections.collections
            if c.name.startswith(cache_prefix)
        ]

        logger.info(f"Found {len(cache_collections)} web cache collections")

        for collection in cache_collections:
            try:
                deleted_count = await _delete_stale_chunks(
                    doc_store=doc_store,
                    collection_name=collection.name,
                    ttl_hours=settings.web_cache_ttl_hours,
                )

                stats["collections_processed"] += 1
                stats["total_chunks_deleted"] += deleted_count

                logger.info(
                    f"Cleaned {deleted_count} stale chunks from {collection.name}"
                )

            except Exception as e:
                logger.error(
                    f"Error cleaning collection {collection.name}: {e}",
                    exc_info=True
                )
                stats["errors"] += 1

        logger.info(
            f"Cache cleanup completed: "
            f"{stats['total_chunks_deleted']} chunks deleted from "
            f"{stats['collections_processed']} collections, "
            f"{stats['errors']} errors"
        )

        return stats

    except Exception as e:
        logger.error(f"Cache cleanup failed: {e}", exc_info=True)
        stats["errors"] += 1
        return stats


async def _delete_stale_chunks(
    doc_store,
    collection_name: str,
    ttl_hours: int,
) -> int:
    """
    Delete stale chunks from a specific collection

    Uses the new database indexes (ix_document_chunks_created_at,
    ix_document_chunks_metadata_gin) for efficient staleness queries.

    Args:
        doc_store: DocumentStore instance
        collection_name: Qdrant collection name
        ttl_hours: Time-to-live in hours

    Returns:
        Number of chunks deleted
    """
    cutoff_time = datetime.now(timezone.utc) - timedelta(hours=ttl_hours)

    logger.info(
        f"Deleting chunks older than {cutoff_time.isoformat()} "
        f"from {collection_name}"
    )

    # Step 1: Find the collection ID from Qdrant collection name
    get_collection_query = """
        SELECT id FROM document_collections
        WHERE qdrant_collection_name = :collection_name
    """

    async with doc_store.db.session() as session:
        result = await session.execute(
            get_collection_query,
            {"collection_name": collection_name}
        )
        row = result.fetchone()

    if not row:
        logger.warning(f"Collection not found: {collection_name}")
        return 0

    collection_id = row[0]

    # Step 2: Delete stale chunks using indexed query
    # This query uses:
    # - ix_document_chunks_created_at for efficient time filtering
    # - ix_document_chunks_source_type for web content filtering
    delete_query = """
        DELETE FROM document_chunks
        WHERE collection_id = :collection_id
        AND metadata->>'source_type' = 'web'
        AND created_at < :cutoff_time
        RETURNING id
    """

    async with doc_store.db.session() as session:
        result = await session.execute(
            delete_query,
            {
                "collection_id": collection_id,
                "cutoff_time": cutoff_time
            }
        )
        deleted_ids = [row[0] for row in result.fetchall()]
        await session.commit()

    deleted_count = len(deleted_ids)

    if deleted_count > 0:
        # Step 3: Delete corresponding vectors from Qdrant
        try:
            from qdrant_client.models import PointIdsList

            await doc_store.qdrant_client.delete(
                collection_name=collection_name,
                points_selector=PointIdsList(
                    points=[str(chunk_id) for chunk_id in deleted_ids]
                )
            )

            logger.info(
                f"Deleted {deleted_count} chunks from {collection_name} "
                f"(PostgreSQL + Qdrant)"
            )
        except Exception as e:
            logger.error(
                f"Failed to delete vectors from Qdrant: {e}. "
                f"PostgreSQL cleanup succeeded ({deleted_count} chunks).",
                exc_info=True
            )
            # Continue - PostgreSQL is source of truth

    return deleted_count


async def cleanup_web_cache_for_user(user_id: str, ttl_hours: int = 24) -> int:
    """
    Clean up web cache for specific user

    Args:
        user_id: User ID
        ttl_hours: Time-to-live in hours

    Returns:
        Number of chunks deleted
    """
    settings = get_settings()
    doc_store = await get_document_store()

    collection_name = f"{settings.web_cache_collection_prefix}_{user_id}"

    try:
        deleted_count = await _delete_stale_chunks(
            doc_store=doc_store,
            collection_name=collection_name,
            ttl_hours=ttl_hours,
        )

        logger.info(
            f"Cleaned {deleted_count} stale chunks for user {user_id}"
        )

        return deleted_count

    except Exception as e:
        logger.error(f"Failed to clean cache for user {user_id}: {e}", exc_info=True)
        return 0


async def cleanup_news_cache() -> dict[str, int]:
    """
    Specialized cleanup for news cache (1 hour TTL)

    News content becomes stale faster than general content,
    so we use a shorter TTL (default 1 hour vs 24 hours).

    Returns:
        Dictionary with cleanup statistics
    """
    settings = get_settings()
    news_ttl_hours = settings.web_cache_news_ttl_hours
    doc_store = await get_document_store()

    stats = {
        "collections_processed": 0,
        "total_chunks_deleted": 0,
        "errors": 0,
    }

    logger.info(f"Starting news cache cleanup (TTL: {news_ttl_hours}h)")

    try:
        # Get all collections
        collections = await doc_store.qdrant_client.get_collections()

        # Filter for web_cache collections
        cache_prefix = settings.web_cache_collection_prefix
        cache_collections = [
            c for c in collections.collections
            if c.name.startswith(cache_prefix)
        ]

        cutoff_time = datetime.now(timezone.utc) - timedelta(hours=news_ttl_hours)

        for collection in cache_collections:
            try:
                deleted_count = await _delete_news_chunks(
                    doc_store=doc_store,
                    collection_name=collection.name,
                    cutoff_time=cutoff_time,
                )

                stats["collections_processed"] += 1
                stats["total_chunks_deleted"] += deleted_count

                if deleted_count > 0:
                    logger.info(
                        f"Cleaned {deleted_count} stale news chunks from {collection.name}"
                    )

            except Exception as e:
                logger.error(
                    f"Error cleaning news from {collection.name}: {e}",
                    exc_info=True
                )
                stats["errors"] += 1

        logger.info(
            f"News cache cleanup completed: "
            f"{stats['total_chunks_deleted']} chunks deleted from "
            f"{stats['collections_processed']} collections"
        )

        return stats

    except Exception as e:
        logger.error(f"News cache cleanup failed: {e}", exc_info=True)
        stats["errors"] += 1
        return stats


async def _delete_news_chunks(
    doc_store,
    collection_name: str,
    cutoff_time: datetime,
) -> int:
    """
    Delete stale news chunks (topic='news') from collection

    Uses metadata index to efficiently filter news content.

    Args:
        doc_store: DocumentStore instance
        collection_name: Qdrant collection name
        cutoff_time: Delete chunks created before this time

    Returns:
        Number of chunks deleted
    """
    # Find collection ID
    get_collection_query = """
        SELECT id FROM document_collections
        WHERE qdrant_collection_name = :collection_name
    """

    async with doc_store.db.session() as session:
        result = await session.execute(
            get_collection_query,
            {"collection_name": collection_name}
        )
        row = result.fetchone()

    if not row:
        return 0

    collection_id = row[0]

    # Delete news chunks using metadata index
    # This query uses ix_document_chunks_metadata_gin for efficient filtering
    delete_query = """
        DELETE FROM document_chunks
        WHERE collection_id = :collection_id
        AND metadata->>'source_type' = 'web'
        AND metadata->>'topic' = 'news'
        AND created_at < :cutoff_time
        RETURNING id
    """

    async with doc_store.db.session() as session:
        result = await session.execute(
            delete_query,
            {
                "collection_id": collection_id,
                "cutoff_time": cutoff_time
            }
        )
        deleted_ids = [row[0] for row in result.fetchall()]
        await session.commit()

    deleted_count = len(deleted_ids)

    if deleted_count > 0:
        # Delete from Qdrant
        try:
            from qdrant_client.models import PointIdsList

            await doc_store.qdrant_client.delete(
                collection_name=collection_name,
                points_selector=PointIdsList(
                    points=[str(chunk_id) for chunk_id in deleted_ids]
                )
            )
        except Exception as e:
            logger.error(f"Failed to delete news vectors from Qdrant: {e}")

    return deleted_count
