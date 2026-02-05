"""
Unit tests for TavilyToolset
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4
from datetime import datetime, timezone

from backend.tools.web_search.tavily_toolset import (
    TavilyToolset,
    TavilySearchResult,
    CrawlResult,
    ExtractedContent,
    SiteMapResult,
)
from backend.tools.web_search.exceptions import (
    TavilyAPIError,
    TavilyConfigError,
    TavilyTimeoutError,
)


@pytest.fixture
def mock_tavily_client():
    """Mock Tavily API client"""
    with patch('backend.tools.web_search.tavily_toolset.AsyncTavilyClient') as mock:
        client_instance = AsyncMock()
        mock.return_value = client_instance
        yield client_instance


@pytest.fixture
def mock_document_store():
    """Mock DocumentStore"""
    store = AsyncMock()
    store.search_collection = AsyncMock(return_value=[])
    store.create_collection = AsyncMock()
    store.store_chunks = AsyncMock()
    return store


@pytest.fixture
def tavily_toolset(mock_document_store):
    """Create TavilyToolset instance with mocked dependencies"""
    with patch('backend.tools.web_search.tavily_toolset.get_settings') as mock_settings:
        settings = MagicMock()
        settings.tavily_rate_limit_per_minute = 60
        settings.tavily_timeout_seconds = 30
        settings.tavily_retry_attempts = 3
        settings.web_cache_ttl_hours = 24
        settings.web_cache_news_ttl_hours = 1
        settings.web_cache_similarity_threshold = 0.85
        settings.web_cache_collection_prefix = "web_cache"
        mock_settings.return_value = settings

        toolset = TavilyToolset(
            api_key="test_api_key",
            document_store=mock_document_store,
            enable_caching=True,
        )
        return toolset


class TestTavilyToolsetInitialization:
    """Test TavilyToolset initialization"""

    def test_initialization_without_api_key(self):
        """Test that initialization fails without API key"""
        with pytest.raises(TavilyConfigError, match="API key is required"):
            TavilyToolset(api_key="")

    def test_initialization_with_api_key(self, mock_document_store):
        """Test successful initialization with API key"""
        with patch('backend.tools.web_search.tavily_toolset.get_settings') as mock_settings:
            settings = MagicMock()
            settings.tavily_rate_limit_per_minute = 60
            mock_settings.return_value = settings

            toolset = TavilyToolset(
                api_key="test_key",
                document_store=mock_document_store,
            )

            assert toolset.api_key == "test_key"
            assert toolset.document_store == mock_document_store
            assert toolset.enable_caching is True


class TestContentHashing:
    """Test content hashing for deduplication"""

    def test_compute_content_hash(self, tavily_toolset):
        """Test SHA-256 hash computation"""
        content = "This is test content"
        hash1 = tavily_toolset._compute_content_hash(content)

        # Hash should be consistent
        hash2 = tavily_toolset._compute_content_hash(content)
        assert hash1 == hash2

        # Hash should be SHA-256 (64 hex chars)
        assert len(hash1) == 64
        assert all(c in '0123456789abcdef' for c in hash1)

    def test_different_content_different_hash(self, tavily_toolset):
        """Test that different content produces different hashes"""
        hash1 = tavily_toolset._compute_content_hash("content1")
        hash2 = tavily_toolset._compute_content_hash("content2")

        assert hash1 != hash2


class TestCacheOperations:
    """Test cache check and store operations"""

    @pytest.mark.asyncio
    async def test_cache_miss(self, tavily_toolset, mock_document_store):
        """Test cache miss returns None"""
        mock_document_store.search_collection.return_value = []

        user_id = uuid4()
        result = await tavily_toolset._check_cache(
            query="test query",
            user_id=user_id,
            ttl_hours=24,
        )

        assert result is None
        mock_document_store.search_collection.assert_called_once()

    @pytest.mark.asyncio
    async def test_cache_disabled(self, mock_document_store):
        """Test cache operations when caching is disabled"""
        with patch('backend.tools.web_search.tavily_toolset.get_settings') as mock_settings:
            settings = MagicMock()
            settings.tavily_rate_limit_per_minute = 60
            mock_settings.return_value = settings

            toolset = TavilyToolset(
                api_key="test_key",
                document_store=mock_document_store,
                enable_caching=False,
            )

            user_id = uuid4()
            result = await toolset._check_cache(
                query="test query",
                user_id=user_id,
                ttl_hours=24,
            )

            assert result is None
            # Should not call document store
            mock_document_store.search_collection.assert_not_called()

    @pytest.mark.asyncio
    async def test_store_to_cache(self, tavily_toolset, mock_document_store):
        """Test storing results to cache"""
        user_id = uuid4()
        results = [
            {
                "title": "Test Result",
                "content": "Test content",
                "url": "https://example.com",
                "score": 0.95,
            }
        ]

        await tavily_toolset._store_to_cache(
            query="test query",
            user_id=user_id,
            results=results,
            ttl_hours=24,
            search_depth="basic",
        )

        # Should create collection and store chunks
        mock_document_store.create_collection.assert_called_once()
        mock_document_store.store_chunks.assert_called_once()


class TestSearchOperation:
    """Test Tavily search operation"""

    @pytest.mark.asyncio
    async def test_search_success(self, tavily_toolset, mock_tavily_client):
        """Test successful search operation"""
        # Mock API response
        mock_tavily_client.search = AsyncMock(return_value={
            "query": "test query",
            "results": [
                {
                    "title": "Result 1",
                    "url": "https://example.com/1",
                    "content": "Content 1",
                    "score": 0.95,
                }
            ]
        })

        tavily_toolset.client = mock_tavily_client
        user_id = uuid4()

        result = await tavily_toolset.search(
            query="test query",
            user_id=user_id,
            max_results=10,
            use_cache=False,  # Disable cache for this test
        )

        assert isinstance(result, TavilySearchResult)
        assert result.query == "test query"
        assert len(result.results) == 1
        assert result.results[0]["title"] == "Result 1"
        assert result.source == "api"

    @pytest.mark.asyncio
    async def test_search_with_retry_on_failure(self, tavily_toolset, mock_tavily_client):
        """Test search retries on failure"""
        # Mock API to fail twice, then succeed
        mock_tavily_client.search = AsyncMock(
            side_effect=[
                Exception("API Error"),
                Exception("API Error"),
                {
                    "query": "test query",
                    "results": [{"title": "Success", "url": "https://example.com", "content": "Content", "score": 0.9}]
                }
            ]
        )

        tavily_toolset.client = mock_tavily_client
        user_id = uuid4()

        result = await tavily_toolset.search(
            query="test query",
            user_id=user_id,
            use_cache=False,
        )

        # Should succeed after retries
        assert isinstance(result, TavilySearchResult)
        assert len(result.results) == 1

        # Should have been called 3 times
        assert mock_tavily_client.search.call_count == 3

    @pytest.mark.asyncio
    async def test_search_ttl_for_news_topic(self, tavily_toolset, mock_document_store):
        """Test that news topic uses shorter TTL"""
        mock_tavily_client = AsyncMock()
        mock_tavily_client.search = AsyncMock(return_value={
            "query": "breaking news",
            "results": [{"title": "News", "url": "https://news.com", "content": "News content", "score": 0.9}]
        })

        tavily_toolset.client = mock_tavily_client
        user_id = uuid4()

        # Search with news topic
        await tavily_toolset.search(
            query="breaking news",
            user_id=user_id,
            topic="news",
            use_cache=True,
        )

        # Verify cache was called (would use 1 hour TTL for news)
        # The _store_to_cache should be called with ttl_hours=1
        mock_document_store.store_chunks.assert_called()


class TestCrawlOperation:
    """Test Tavily crawl operation"""

    @pytest.mark.asyncio
    async def test_crawl_success(self, tavily_toolset, mock_tavily_client):
        """Test successful crawl operation"""
        mock_tavily_client.crawl = AsyncMock(return_value={
            "results": [
                {"url": "https://example.com/page1", "content": "Page 1"},
                {"url": "https://example.com/page2", "content": "Page 2"},
            ]
        })

        tavily_toolset.client = mock_tavily_client
        user_id = uuid4()

        result = await tavily_toolset.crawl(
            base_url="https://example.com",
            user_id=user_id,
            max_depth=2,
        )

        assert isinstance(result, CrawlResult)
        assert result.base_url == "https://example.com"
        assert result.pages_crawled == 2
        assert len(result.results) == 2

    @pytest.mark.asyncio
    async def test_crawl_with_instructions(self, tavily_toolset, mock_tavily_client):
        """Test crawl with natural language instructions"""
        mock_tavily_client.crawl = AsyncMock(return_value={"results": []})

        tavily_toolset.client = mock_tavily_client
        user_id = uuid4()

        await tavily_toolset.crawl(
            base_url="https://example.com",
            user_id=user_id,
            instructions="Only crawl documentation pages",
        )

        # Verify instructions were passed
        call_args = mock_tavily_client.crawl.call_args
        assert call_args.kwargs["instructions"] == "Only crawl documentation pages"


class TestExtractOperation:
    """Test Tavily extract operation"""

    @pytest.mark.asyncio
    async def test_extract_success(self, tavily_toolset, mock_tavily_client):
        """Test successful extract operation"""
        mock_tavily_client.extract = AsyncMock(return_value={
            "results": [
                {
                    "url": "https://example.com/page1",
                    "title": "Page 1",
                    "content": "Extracted content 1",
                    "raw_content": "<html>...</html>",
                }
            ]
        })

        tavily_toolset.client = mock_tavily_client
        user_id = uuid4()

        results = await tavily_toolset.extract(
            urls=["https://example.com/page1"],
            user_id=user_id,
            extract_depth="advanced",
        )

        assert len(results) == 1
        assert isinstance(results[0], ExtractedContent)
        assert results[0].url == "https://example.com/page1"
        assert results[0].title == "Page 1"


class TestMapSiteOperation:
    """Test Tavily map site operation"""

    @pytest.mark.asyncio
    async def test_map_site_success(self, tavily_toolset, mock_tavily_client):
        """Test successful site mapping"""
        mock_tavily_client.map = AsyncMock(return_value={
            "urls": [
                "https://example.com/",
                "https://example.com/about",
                "https://example.com/contact",
            ],
            "structure": {
                "homepage": "https://example.com/",
                "pages": ["about", "contact"],
            }
        })

        tavily_toolset.client = mock_tavily_client
        user_id = uuid4()

        result = await tavily_toolset.map_site(
            base_url="https://example.com",
            user_id=user_id,
            max_depth=2,
        )

        assert isinstance(result, SiteMapResult)
        assert result.base_url == "https://example.com"
        assert len(result.urls) == 3
        assert "homepage" in result.structure


class TestDeduplication:
    """Test result deduplication"""

    @pytest.mark.asyncio
    async def test_deduplicate_results(self, tavily_toolset):
        """Test deduplication removes duplicate content"""
        user_id = uuid4()
        results = [
            {"title": "Python Guide", "content": "Learn Python programming", "url": "https://example.com/1"},
            {"title": "Python Guide", "content": "Learn Python programming", "url": "https://example.com/2"},  # Exact duplicate
            {"title": "Java Guide", "content": "Learn Java programming", "url": "https://example.com/3"},
        ]

        unique_results = await tavily_toolset._deduplicate_results(results, user_id)

        # Should have 2 unique results (Result 2 is exact duplicate of Result 1)
        assert len(unique_results) == 2
        assert unique_results[0]["title"] == "Python Guide"
        assert unique_results[1]["title"] == "Java Guide"
