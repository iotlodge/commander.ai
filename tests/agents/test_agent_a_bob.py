"""
Unit tests for Agent A (bob) - Research Specialist
Tests Phase 3 migration: TavilyToolset integration and error handling
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

from backend.agents.specialized.agent_a.llm_research import llm_web_search
from backend.tools.web_search.tavily_toolset import TavilySearchResult
from backend.tools.web_search.exceptions import (
    TavilyAPIError,
    TavilyRateLimitError,
    TavilyTimeoutError,
)


@pytest.fixture
def mock_settings():
    """Mock settings with Tavily API key"""
    with patch('backend.agents.specialized.agent_a.llm_research.get_settings') as mock:
        settings = MagicMock()
        settings.tavily_api_key = "test_api_key"
        settings.tavily_max_results = 10
        settings.openai_api_key = "test_openai_key"
        mock.return_value = settings
        yield settings


@pytest.fixture
def mock_document_store():
    """Mock DocumentStore singleton"""
    with patch('backend.agents.specialized.agent_a.llm_research.get_document_store') as mock:
        doc_store = AsyncMock()
        mock.return_value = doc_store
        yield doc_store


@pytest.fixture
def mock_tavily_toolset():
    """Mock TavilyToolset"""
    with patch('backend.agents.specialized.agent_a.llm_research.TavilyToolset') as mock:
        toolset = AsyncMock()
        mock.return_value = toolset
        yield toolset


class TestLLMWebSearchCacheHit:
    """Test cache hit scenarios"""

    @pytest.mark.asyncio
    async def test_cache_hit_fast_response(self, mock_settings, mock_document_store, mock_tavily_toolset):
        """Test that cache hit returns results quickly"""
        # Mock successful cache hit
        mock_result = TavilySearchResult(
            query="Python async patterns",
            results=[
                {
                    "title": "Async Guide",
                    "content": "Python async guide content",
                    "url": "https://example.com/async",
                    "score": 0.95,
                }
            ],
            source="cache",  # Cache hit
            execution_time_ms=87.23,
        )
        mock_tavily_toolset.search = AsyncMock(return_value=mock_result)

        user_id = uuid4()
        results = await llm_web_search(
            query="Python async patterns",
            user_id=user_id,
            use_cache=True,
        )

        # Verify results
        assert len(results) == 1
        assert results[0]["title"] == "Async Guide"
        assert results[0]["snippet"] == "Python async guide content"
        assert results[0]["url"] == "https://example.com/async"
        assert results[0]["score"] == 0.95

        # Verify cache was enabled
        mock_tavily_toolset.search.assert_called_once()
        call_kwargs = mock_tavily_toolset.search.call_args.kwargs
        assert call_kwargs["use_cache"] is True
        assert call_kwargs["user_id"] == user_id

    @pytest.mark.asyncio
    async def test_cache_miss_api_call(self, mock_settings, mock_document_store, mock_tavily_toolset):
        """Test that cache miss calls Tavily API"""
        # Mock cache miss → API call
        mock_result = TavilySearchResult(
            query="New AI regulations 2026",
            results=[
                {
                    "title": "EU AI Act 2026",
                    "content": "New regulations...",
                    "url": "https://example.com/ai-act",
                    "score": 0.98,
                }
            ],
            source="api",  # API call
            execution_time_ms=1847.56,
        )
        mock_tavily_toolset.search = AsyncMock(return_value=mock_result)

        user_id = uuid4()
        results = await llm_web_search(
            query="New AI regulations 2026",
            user_id=user_id,
            use_cache=True,
        )

        # Verify API was called
        assert len(results) == 1
        mock_tavily_toolset.search.assert_called_once()


class TestLLMWebSearchErrorHandling:
    """Test error handling scenarios"""

    @pytest.mark.asyncio
    async def test_rate_limit_cache_fallback(self, mock_settings, mock_document_store, mock_tavily_toolset):
        """Test rate limit triggers cache-only fallback"""
        # Mock rate limit error
        mock_tavily_toolset.search = AsyncMock(
            side_effect=TavilyRateLimitError("Rate limit exceeded")
        )

        # Mock cache fallback returns results
        cached_result = TavilySearchResult(
            query="test query",
            results=[
                {
                    "title": "Cached Result",
                    "content": "Cached content",
                    "url": "https://example.com/cached",
                    "score": 0.9,
                }
            ],
            source="cache",
            cached_at="2024-02-05T10:00:00Z",
            execution_time_ms=50.0,
        )
        mock_tavily_toolset._check_cache = AsyncMock(return_value=cached_result)

        user_id = uuid4()
        results = await llm_web_search(
            query="test query",
            user_id=user_id,
            use_cache=True,
        )

        # Verify cache fallback was attempted
        mock_tavily_toolset._check_cache.assert_called_once_with(
            "test query", user_id, ttl_hours=24
        )

        # Verify results from cache
        assert len(results) == 1
        assert results[0]["title"] == "Cached Result"

    @pytest.mark.asyncio
    async def test_timeout_llm_fallback(self, mock_settings, mock_document_store, mock_tavily_toolset):
        """Test timeout triggers LLM fallback"""
        # Mock timeout error
        mock_tavily_toolset.search = AsyncMock(
            side_effect=TavilyTimeoutError("Request timeout")
        )

        # Mock LLM fallback
        with patch('backend.agents.specialized.agent_a.llm_research.ChatOpenAI') as mock_llm_class:
            mock_llm = AsyncMock()
            mock_response = MagicMock()
            mock_response.content = "LLM-generated research about Python async..."
            mock_llm.ainvoke = AsyncMock(return_value=mock_response)
            mock_llm_class.return_value = mock_llm

            user_id = uuid4()
            results = await llm_web_search(
                query="Python async patterns",
                user_id=user_id,
                use_cache=True,
            )

            # Verify LLM fallback was used
            assert len(results) == 1
            assert results[0]["url"] == "knowledge-base"
            assert "Python async" in results[0]["snippet"]

    @pytest.mark.asyncio
    async def test_api_error_llm_fallback(self, mock_settings, mock_document_store, mock_tavily_toolset):
        """Test API error triggers LLM fallback"""
        # Mock API error
        mock_tavily_toolset.search = AsyncMock(
            side_effect=TavilyAPIError("API connection failed")
        )

        # Mock LLM fallback
        with patch('backend.agents.specialized.agent_a.llm_research.ChatOpenAI') as mock_llm_class:
            mock_llm = AsyncMock()
            mock_response = MagicMock()
            mock_response.content = "Research findings based on knowledge..."
            mock_llm.ainvoke = AsyncMock(return_value=mock_response)
            mock_llm_class.return_value = mock_llm

            user_id = uuid4()
            results = await llm_web_search(
                query="test query",
                user_id=user_id,
                use_cache=True,
            )

            # Verify LLM fallback
            assert len(results) == 1
            assert results[0]["url"] == "knowledge-base"

    @pytest.mark.asyncio
    async def test_no_api_key_llm_fallback(self, mock_document_store):
        """Test missing API key uses LLM fallback"""
        with patch('backend.agents.specialized.agent_a.llm_research.get_settings') as mock_settings:
            settings = MagicMock()
            settings.tavily_api_key = ""  # No API key
            settings.openai_api_key = "test_openai_key"
            mock_settings.return_value = settings

            with patch('backend.agents.specialized.agent_a.llm_research.ChatOpenAI') as mock_llm_class:
                mock_llm = AsyncMock()
                mock_response = MagicMock()
                mock_response.content = "LLM knowledge fallback..."
                mock_llm.ainvoke = AsyncMock(return_value=mock_response)
                mock_llm_class.return_value = mock_llm

                user_id = uuid4()
                results = await llm_web_search(
                    query="test query",
                    user_id=user_id,
                    use_cache=True,
                )

                # Verify LLM fallback used
                assert len(results) == 1
                assert results[0]["url"] == "knowledge-base"


class TestLLMWebSearchLogging:
    """Test logging behavior"""

    @pytest.mark.asyncio
    async def test_cache_hit_logged(self, mock_settings, mock_document_store, mock_tavily_toolset):
        """Test cache hit is logged"""
        mock_result = TavilySearchResult(
            query="test",
            results=[{"title": "Test", "content": "Content", "url": "https://test.com", "score": 0.9}],
            source="cache",
            execution_time_ms=50.0,
        )
        mock_tavily_toolset.search = AsyncMock(return_value=mock_result)

        with patch('backend.agents.specialized.agent_a.llm_research.logger') as mock_logger:
            user_id = uuid4()
            await llm_web_search("test", user_id, use_cache=True)

            # Verify info log for cache hit
            mock_logger.info.assert_called_once()
            log_message = mock_logger.info.call_args[0][0]
            assert "from cache" in log_message
            assert "50.00ms" in log_message

    @pytest.mark.asyncio
    async def test_rate_limit_logged_as_warning(self, mock_settings, mock_document_store, mock_tavily_toolset):
        """Test rate limit is logged as warning"""
        mock_tavily_toolset.search = AsyncMock(
            side_effect=TavilyRateLimitError("Rate limit")
        )
        mock_tavily_toolset._check_cache = AsyncMock(return_value=None)

        with patch('backend.agents.specialized.agent_a.llm_research.logger') as mock_logger:
            with patch('backend.agents.specialized.agent_a.llm_research.ChatOpenAI') as mock_llm_class:
                # Mock LLM for fallback
                mock_llm = AsyncMock()
                mock_response = MagicMock()
                mock_response.content = "LLM fallback content"
                mock_llm.ainvoke = AsyncMock(return_value=mock_response)
                mock_llm_class.return_value = mock_llm

                user_id = uuid4()
                await llm_web_search("test", user_id, use_cache=True)

                # Verify warning log for rate limit
                mock_logger.warning.assert_called_once()
                log_message = mock_logger.warning.call_args[0][0]
                assert "Rate limit" in log_message

    @pytest.mark.asyncio
    async def test_api_error_logged_as_error(self, mock_settings, mock_document_store, mock_tavily_toolset):
        """Test API error is logged as error"""
        mock_tavily_toolset.search = AsyncMock(
            side_effect=TavilyAPIError("API error")
        )

        with patch('backend.agents.specialized.agent_a.llm_research.logger') as mock_logger:
            with patch('backend.agents.specialized.agent_a.llm_research.ChatOpenAI') as mock_llm_class:
                # Mock LLM for fallback
                mock_llm = AsyncMock()
                mock_response = MagicMock()
                mock_response.content = "LLM fallback content"
                mock_llm.ainvoke = AsyncMock(return_value=mock_response)
                mock_llm_class.return_value = mock_llm

                user_id = uuid4()
                await llm_web_search("test", user_id, use_cache=True)

                # Verify error log for API failure
                mock_logger.error.assert_called()
                log_message = mock_logger.error.call_args[0][0]
                assert "API error" in log_message


class TestLLMWebSearchConfiguration:
    """Test configuration and parameters"""

    @pytest.mark.asyncio
    async def test_cache_disabled(self, mock_settings, mock_document_store, mock_tavily_toolset):
        """Test use_cache=False bypasses cache"""
        mock_result = TavilySearchResult(
            query="test",
            results=[{"title": "Test", "content": "Content", "url": "https://test.com", "score": 0.9}],
            source="api",
            execution_time_ms=1500.0,
        )
        mock_tavily_toolset.search = AsyncMock(return_value=mock_result)

        user_id = uuid4()
        await llm_web_search(
            query="test",
            user_id=user_id,
            use_cache=False,  # Explicitly disable cache
        )

        # Verify use_cache=False was passed
        call_kwargs = mock_tavily_toolset.search.call_args.kwargs
        assert call_kwargs["use_cache"] is False

    @pytest.mark.asyncio
    async def test_max_results_from_settings(self, mock_settings, mock_document_store, mock_tavily_toolset):
        """Test max_results comes from settings"""
        mock_settings.tavily_max_results = 15  # Custom value

        mock_result = TavilySearchResult(
            query="test",
            results=[{"title": "Test", "content": "Content", "url": "https://test.com", "score": 0.9}],
            source="api",
            execution_time_ms=1500.0,
        )
        mock_tavily_toolset.search = AsyncMock(return_value=mock_result)

        user_id = uuid4()
        await llm_web_search("test", user_id, use_cache=True)

        # Verify max_results=15 was passed
        call_kwargs = mock_tavily_toolset.search.call_args.kwargs
        assert call_kwargs["max_results"] == 15

    @pytest.mark.asyncio
    async def test_search_depth_basic(self, mock_settings, mock_document_store, mock_tavily_toolset):
        """Test search depth is set to basic"""
        mock_result = TavilySearchResult(
            query="test",
            results=[{"title": "Test", "content": "Content", "url": "https://test.com", "score": 0.9}],
            source="api",
            execution_time_ms=1500.0,
        )
        mock_tavily_toolset.search = AsyncMock(return_value=mock_result)

        user_id = uuid4()
        await llm_web_search("test", user_id, use_cache=True)

        # Verify search_depth="basic"
        call_kwargs = mock_tavily_toolset.search.call_args.kwargs
        assert call_kwargs["search_depth"] == "basic"


class TestLLMWebSearchIntegration:
    """Test integration with TavilyToolset"""

    @pytest.mark.asyncio
    async def test_toolset_initialized_correctly(self, mock_settings, mock_document_store, mock_tavily_toolset):
        """Test TavilyToolset is initialized with correct parameters"""
        mock_result = TavilySearchResult(
            query="test",
            results=[{"title": "Test", "content": "Content", "url": "https://test.com", "score": 0.9}],
            source="api",
            execution_time_ms=1500.0,
        )
        mock_tavily_toolset.search = AsyncMock(return_value=mock_result)

        with patch('backend.agents.specialized.agent_a.llm_research.TavilyToolset') as MockToolset:
            MockToolset.return_value = mock_tavily_toolset

            user_id = uuid4()
            await llm_web_search("test", user_id, use_cache=True)

            # Verify TavilyToolset initialization
            MockToolset.assert_called_once_with(
                api_key="test_api_key",
                document_store=mock_document_store,
                enable_caching=True,
            )

    @pytest.mark.asyncio
    async def test_document_store_singleton_used(self, mock_settings, mock_document_store, mock_tavily_toolset):
        """Test that DocumentStore singleton is used"""
        mock_result = TavilySearchResult(
            query="test",
            results=[{"title": "Test", "content": "Content", "url": "https://test.com", "score": 0.9}],
            source="api",
            execution_time_ms=1500.0,
        )
        mock_tavily_toolset.search = AsyncMock(return_value=mock_result)

        with patch('backend.agents.specialized.agent_a.llm_research.get_document_store') as mock_get_ds:
            mock_get_ds.return_value = mock_document_store

            user_id = uuid4()
            await llm_web_search("test", user_id, use_cache=True)

            # Verify get_document_store was called
            mock_get_ds.assert_called_once()
