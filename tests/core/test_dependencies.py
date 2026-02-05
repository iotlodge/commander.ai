"""
Unit tests for dependency management and singleton pattern
"""

import pytest
from unittest.mock import AsyncMock, patch

from backend.core.dependencies import (
    get_document_store,
    shutdown_document_store,
    reset_document_store,
)


@pytest.fixture(autouse=True)
async def cleanup_singleton():
    """Reset singleton after each test"""
    yield
    reset_document_store()


class TestDocumentStoreSingleton:
    """Test DocumentStore singleton pattern"""

    @pytest.mark.asyncio
    async def test_get_document_store_creates_instance(self):
        """Test that get_document_store creates instance on first call"""
        with patch('backend.core.dependencies.DocumentStore') as MockDocumentStore:
            mock_instance = AsyncMock()
            MockDocumentStore.return_value = mock_instance

            doc_store = await get_document_store()

            assert doc_store == mock_instance
            MockDocumentStore.assert_called_once()
            mock_instance.connect.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_document_store_returns_same_instance(self):
        """Test that subsequent calls return the same instance"""
        with patch('backend.core.dependencies.DocumentStore') as MockDocumentStore:
            mock_instance = AsyncMock()
            MockDocumentStore.return_value = mock_instance

            doc_store1 = await get_document_store()
            doc_store2 = await get_document_store()
            doc_store3 = await get_document_store()

            # All should be the same instance
            assert doc_store1 is doc_store2
            assert doc_store2 is doc_store3

            # Constructor should only be called once
            MockDocumentStore.assert_called_once()

            # Connect should only be called once
            mock_instance.connect.assert_called_once()

    @pytest.mark.asyncio
    async def test_shutdown_document_store(self):
        """Test shutdown disconnects and clears singleton"""
        with patch('backend.core.dependencies.DocumentStore') as MockDocumentStore:
            mock_instance = AsyncMock()
            MockDocumentStore.return_value = mock_instance

            # Get instance
            doc_store = await get_document_store()
            assert doc_store is not None

            # Shutdown
            await shutdown_document_store()

            # Disconnect should be called
            mock_instance.disconnect.assert_called_once()

            # Next call should create new instance
            doc_store2 = await get_document_store()

            # Should be a new call to constructor
            assert MockDocumentStore.call_count == 2

    @pytest.mark.asyncio
    async def test_reset_document_store(self):
        """Test reset clears singleton (for testing)"""
        with patch('backend.core.dependencies.DocumentStore') as MockDocumentStore:
            mock_instance = AsyncMock()
            MockDocumentStore.return_value = mock_instance

            # Get instance
            await get_document_store()

            # Reset (without disconnect - testing only)
            reset_document_store()

            # Next call should create new instance
            await get_document_store()

            # Constructor should be called twice
            assert MockDocumentStore.call_count == 2

    @pytest.mark.asyncio
    async def test_concurrent_access(self):
        """Test that concurrent access returns same instance"""
        import asyncio

        with patch('backend.core.dependencies.DocumentStore') as MockDocumentStore:
            mock_instance = AsyncMock()
            MockDocumentStore.return_value = mock_instance

            # Simulate concurrent access
            results = await asyncio.gather(*[
                get_document_store() for _ in range(10)
            ])

            # All should be the same instance
            assert all(r is results[0] for r in results)

            # Constructor should only be called once
            MockDocumentStore.assert_called_once()
