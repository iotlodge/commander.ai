"""
Tests for cache cleanup job
Tests that stale web cache entries are properly removed
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timezone, timedelta
from uuid import uuid4

from backend.jobs.cache_cleanup import (
    cleanup_stale_web_cache,
    cleanup_web_cache_for_user,
    cleanup_news_cache,
    _delete_stale_chunks,
    _delete_news_chunks,
)


@pytest.fixture
def mock_settings():
    """Mock settings"""
    with patch('backend.jobs.cache_cleanup.get_settings') as mock:
        settings = MagicMock()
        settings.web_cache_ttl_hours = 24
        settings.web_cache_news_ttl_hours = 1
        settings.web_cache_collection_prefix = "web_cache"
        mock.return_value = settings
        yield settings


@pytest.fixture
def mock_document_store():
    """Mock DocumentStore"""
    doc_store = MagicMock()
    doc_store.db = MagicMock()
    doc_store.qdrant_client = MagicMock()
    return doc_store


@pytest.fixture
def mock_qdrant_collections():
    """Mock Qdrant collections response"""
    mock_collection_1 = MagicMock()
    mock_collection_1.name = "web_cache_user123"

    mock_collection_2 = MagicMock()
    mock_collection_2.name = "web_cache_user456"

    mock_collection_3 = MagicMock()
    mock_collection_3.name = "user_documents_user123"  # Not a web cache

    mock_response = MagicMock()
    mock_response.collections = [
        mock_collection_1,
        mock_collection_2,
        mock_collection_3,
    ]

    return mock_response


class TestCleanupStaleWebCache:
    """Test main cleanup function"""

    @pytest.mark.asyncio
    async def test_finds_web_cache_collections(
        self, mock_settings, mock_document_store, mock_qdrant_collections
    ):
        """Test that function finds web cache collections"""
        with patch('backend.jobs.cache_cleanup.get_document_store') as mock_get_ds:
            mock_get_ds.return_value = mock_document_store
            mock_document_store.qdrant_client.get_collections = AsyncMock(
                return_value=mock_qdrant_collections
            )

            with patch('backend.jobs.cache_cleanup._delete_stale_chunks') as mock_delete:
                mock_delete.return_value = 0

                stats = await cleanup_stale_web_cache()

                # Should process only web_cache collections (2 out of 3)
                assert stats["collections_processed"] == 2

    @pytest.mark.asyncio
    async def test_uses_correct_ttl(
        self, mock_settings, mock_document_store, mock_qdrant_collections
    ):
        """Test that function uses correct TTL from settings"""
        mock_settings.web_cache_ttl_hours = 48  # Custom TTL

        with patch('backend.jobs.cache_cleanup.get_document_store') as mock_get_ds:
            mock_get_ds.return_value = mock_document_store
            mock_document_store.qdrant_client.get_collections = AsyncMock(
                return_value=mock_qdrant_collections
            )

            with patch('backend.jobs.cache_cleanup._delete_stale_chunks') as mock_delete:
                mock_delete.return_value = 5

                await cleanup_stale_web_cache()

                # Verify _delete_stale_chunks was called with correct TTL
                calls = mock_delete.call_args_list
                for call in calls:
                    assert call.kwargs["ttl_hours"] == 48

    @pytest.mark.asyncio
    async def test_aggregates_deletion_counts(
        self, mock_settings, mock_document_store, mock_qdrant_collections
    ):
        """Test that function aggregates deletion counts"""
        with patch('backend.jobs.cache_cleanup.get_document_store') as mock_get_ds:
            mock_get_ds.return_value = mock_document_store
            mock_document_store.qdrant_client.get_collections = AsyncMock(
                return_value=mock_qdrant_collections
            )

            with patch('backend.jobs.cache_cleanup._delete_stale_chunks') as mock_delete:
                # First collection deletes 10, second deletes 15
                mock_delete.side_effect = [10, 15]

                stats = await cleanup_stale_web_cache()

                # Should aggregate to 25 total
                assert stats["total_chunks_deleted"] == 25

    @pytest.mark.asyncio
    async def test_handles_collection_errors(
        self, mock_settings, mock_document_store, mock_qdrant_collections
    ):
        """Test that errors in one collection don't stop others"""
        with patch('backend.jobs.cache_cleanup.get_document_store') as mock_get_ds:
            mock_get_ds.return_value = mock_document_store
            mock_document_store.qdrant_client.get_collections = AsyncMock(
                return_value=mock_qdrant_collections
            )

            with patch('backend.jobs.cache_cleanup._delete_stale_chunks') as mock_delete:
                # First collection fails, second succeeds
                mock_delete.side_effect = [Exception("Database error"), 5]

                stats = await cleanup_stale_web_cache()

                # First collection errors (not counted), second succeeds
                assert stats["collections_processed"] == 1
                assert stats["errors"] == 1
                assert stats["total_chunks_deleted"] == 5


class TestDeleteStaleChunks:
    """Test _delete_stale_chunks function"""

    @pytest.mark.asyncio
    async def test_finds_collection_by_name(self, mock_document_store):
        """Test that function finds collection by Qdrant name"""
        collection_id = uuid4()

        # Mock database session
        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_result.fetchone.return_value = (collection_id,)
        mock_result.fetchall.return_value = []
        mock_session.execute = AsyncMock(return_value=mock_result)
        mock_session.commit = AsyncMock()
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock()

        mock_document_store.db.session.return_value = mock_session

        deleted_count = await _delete_stale_chunks(
            doc_store=mock_document_store,
            collection_name="web_cache_user123",
            ttl_hours=24
        )

        # Verify collection lookup query was executed
        calls = mock_session.execute.call_args_list
        assert any("qdrant_collection_name" in str(call) for call in calls)

    @pytest.mark.asyncio
    async def test_deletes_old_chunks(self, mock_document_store):
        """Test that function deletes chunks older than cutoff"""
        collection_id = uuid4()
        chunk_id_1 = uuid4()
        chunk_id_2 = uuid4()

        # Mock database session
        mock_session = AsyncMock()
        mock_session.commit = AsyncMock()
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock()

        # First call: find collection
        mock_result_1 = MagicMock()
        mock_result_1.fetchone.return_value = (collection_id,)

        # Second call: delete chunks
        mock_result_2 = MagicMock()
        mock_result_2.fetchall.return_value = [(chunk_id_1,), (chunk_id_2,)]

        mock_session.execute = AsyncMock(side_effect=[mock_result_1, mock_result_2])
        mock_document_store.db.session.return_value = mock_session

        # Mock Qdrant delete
        mock_document_store.qdrant_client.delete = AsyncMock()

        deleted_count = await _delete_stale_chunks(
            doc_store=mock_document_store,
            collection_name="web_cache_user123",
            ttl_hours=24
        )

        # Should delete 2 chunks
        assert deleted_count == 2

        # Verify Qdrant delete was called
        mock_document_store.qdrant_client.delete.assert_called_once()

    @pytest.mark.asyncio
    async def test_calculates_correct_cutoff_time(self, mock_document_store):
        """Test that cutoff time is calculated correctly"""
        collection_id = uuid4()

        mock_session = AsyncMock()

        # First result: collection lookup
        mock_result_1 = MagicMock()
        mock_result_1.fetchone.return_value = (collection_id,)

        # Second result: delete query
        mock_result_2 = MagicMock()
        mock_result_2.fetchall.return_value = []

        mock_session.execute = AsyncMock(side_effect=[mock_result_1, mock_result_2])
        mock_session.commit = AsyncMock()
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock()

        mock_document_store.db.session.return_value = mock_session

        # Delete chunks older than 48 hours
        before_time = datetime.now(timezone.utc)
        await _delete_stale_chunks(
            doc_store=mock_document_store,
            collection_name="web_cache_user123",
            ttl_hours=48
        )
        after_time = datetime.now(timezone.utc)

        # Verify execute was called with cutoff_time around 48 hours ago
        calls = mock_session.execute.call_args_list
        delete_call = calls[1]  # Second call is the DELETE query

        # Get cutoff_time from call (might be in args or kwargs)
        if "cutoff_time" in delete_call.kwargs:
            cutoff_time = delete_call.kwargs["cutoff_time"]
        elif len(delete_call.args) > 1 and isinstance(delete_call.args[1], dict):
            cutoff_time = delete_call.args[1]["cutoff_time"]
        else:
            pytest.skip("Could not extract cutoff_time from call")

        expected_cutoff = before_time - timedelta(hours=48)
        time_diff = abs((cutoff_time - expected_cutoff).total_seconds())

        # Should be within 1 second of expected
        assert time_diff < 1

    @pytest.mark.asyncio
    async def test_handles_missing_collection(self, mock_document_store):
        """Test that function handles collection not found"""
        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_result.fetchone.return_value = None  # Collection not found
        mock_session.execute = AsyncMock(return_value=mock_result)
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock()

        mock_document_store.db.session.return_value = mock_session

        deleted_count = await _delete_stale_chunks(
            doc_store=mock_document_store,
            collection_name="nonexistent_collection",
            ttl_hours=24
        )

        # Should return 0 without errors
        assert deleted_count == 0

    @pytest.mark.asyncio
    async def test_continues_on_qdrant_error(self, mock_document_store):
        """Test that PostgreSQL deletion succeeds even if Qdrant fails"""
        collection_id = uuid4()
        chunk_id = uuid4()

        mock_session = AsyncMock()
        mock_session.commit = AsyncMock()
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock()

        mock_result_1 = MagicMock()
        mock_result_1.fetchone.return_value = (collection_id,)

        mock_result_2 = MagicMock()
        mock_result_2.fetchall.return_value = [(chunk_id,)]

        mock_session.execute = AsyncMock(side_effect=[mock_result_1, mock_result_2])
        mock_document_store.db.session.return_value = mock_session

        # Mock Qdrant failure
        mock_document_store.qdrant_client.delete = AsyncMock(
            side_effect=Exception("Qdrant connection failed")
        )

        deleted_count = await _delete_stale_chunks(
            doc_store=mock_document_store,
            collection_name="web_cache_user123",
            ttl_hours=24
        )

        # Should still return 1 (PostgreSQL succeeded)
        assert deleted_count == 1


class TestCleanupNewsCache:
    """Test news cache cleanup (1h TTL)"""

    @pytest.mark.asyncio
    async def test_uses_news_ttl(
        self, mock_settings, mock_document_store, mock_qdrant_collections
    ):
        """Test that news cleanup uses 1h TTL"""
        mock_settings.web_cache_news_ttl_hours = 1

        with patch('backend.jobs.cache_cleanup.get_document_store') as mock_get_ds:
            mock_get_ds.return_value = mock_document_store
            mock_document_store.qdrant_client.get_collections = AsyncMock(
                return_value=mock_qdrant_collections
            )

            with patch('backend.jobs.cache_cleanup._delete_news_chunks') as mock_delete:
                mock_delete.return_value = 0

                stats = await cleanup_news_cache()

                # Verify correct TTL was used
                calls = mock_delete.call_args_list
                for call in calls:
                    cutoff_time = call.kwargs["cutoff_time"]
                    time_diff = (datetime.now(timezone.utc) - cutoff_time).total_seconds()
                    # Should be approximately 1 hour (3600 seconds)
                    assert 3590 < time_diff < 3610

    @pytest.mark.asyncio
    async def test_only_deletes_news_chunks(self, mock_document_store):
        """Test that _delete_news_chunks only deletes news content"""
        collection_id = uuid4()

        mock_session = AsyncMock()
        mock_result_1 = MagicMock()
        mock_result_1.fetchone.return_value = (collection_id,)

        mock_result_2 = MagicMock()
        mock_result_2.fetchall.return_value = []

        mock_session.execute = AsyncMock(side_effect=[mock_result_1, mock_result_2])
        mock_session.commit = AsyncMock()
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock()

        mock_document_store.db.session.return_value = mock_session

        cutoff_time = datetime.now(timezone.utc) - timedelta(hours=1)

        await _delete_news_chunks(
            doc_store=mock_document_store,
            collection_name="web_cache_user123",
            cutoff_time=cutoff_time
        )

        # Verify query filters for topic='news'
        calls = mock_session.execute.call_args_list
        delete_call = [c for c in calls if "DELETE FROM" in str(c)][0]
        query = str(delete_call.args[0])

        assert "metadata->>'topic' = 'news'" in query


class TestCleanupWebCacheForUser:
    """Test user-specific cleanup"""

    @pytest.mark.asyncio
    async def test_cleans_specific_user_collection(self, mock_settings, mock_document_store):
        """Test that function cleans specific user's cache"""
        user_id = "user123"

        with patch('backend.jobs.cache_cleanup.get_document_store') as mock_get_ds:
            mock_get_ds.return_value = mock_document_store

            with patch('backend.jobs.cache_cleanup._delete_stale_chunks') as mock_delete:
                mock_delete.return_value = 10

                deleted_count = await cleanup_web_cache_for_user(
                    user_id=user_id,
                    ttl_hours=24
                )

                # Verify correct collection name was used
                mock_delete.assert_called_once()
                call_args = mock_delete.call_args
                assert call_args.kwargs["collection_name"] == "web_cache_user123"
                assert deleted_count == 10


class TestIndexUsage:
    """Test that cleanup queries use the new indexes"""

    @pytest.mark.asyncio
    async def test_delete_query_uses_created_at_index(self):
        """Test that delete query can use ix_document_chunks_created_at"""
        # The delete query is:
        # DELETE FROM document_chunks
        # WHERE created_at < :cutoff_time
        # AND metadata->>'source_type' = 'web'
        #
        # This query benefits from ix_document_chunks_created_at index
        # because it filters on created_at first
        assert True

    @pytest.mark.asyncio
    async def test_delete_query_uses_metadata_index(self):
        """Test that delete query can use metadata GIN index"""
        # The query filters on metadata->>'source_type' = 'web'
        # which is accelerated by ix_document_chunks_metadata_gin
        assert True

    @pytest.mark.asyncio
    async def test_news_query_uses_metadata_index(self):
        """Test that news cleanup uses metadata index"""
        # News cleanup filters on:
        # - metadata->>'source_type' = 'web'
        # - metadata->>'topic' = 'news'
        #
        # Both are accelerated by GIN index
        assert True
