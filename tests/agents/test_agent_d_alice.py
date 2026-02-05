"""
Unit tests for Agent D (alice) - Document Manager
Tests Phase 2 migration: TavilyToolset integration and DocumentStore singleton
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

from backend.agents.specialized.agent_d.nodes import (
    fetch_web_node,
    crawl_site_node,
    extract_urls_node,
    map_site_node,
    create_collection_node,
    store_chunks_node,
)
from backend.tools.web_search.tavily_toolset import (
    TavilySearchResult,
    CrawlResult,
    ExtractedContent,
    SiteMapResult,
)


@pytest.fixture
def mock_settings():
    """Mock settings"""
    with patch('backend.agents.specialized.agent_d.nodes.get_settings') as mock:
        settings = MagicMock()
        settings.tavily_api_key = "test_api_key"
        settings.tavily_max_results = 10
        mock.return_value = settings
        yield settings


@pytest.fixture
def mock_document_store():
    """Mock DocumentStore singleton"""
    with patch('backend.agents.specialized.agent_d.nodes.get_document_store') as mock:
        doc_store = AsyncMock()
        doc_store.create_collection = AsyncMock()
        doc_store.delete_collection = AsyncMock()
        doc_store.store_chunks = AsyncMock()
        doc_store.search_collection = AsyncMock(return_value=[])
        mock.return_value = doc_store
        yield doc_store


@pytest.fixture
def mock_tavily_toolset():
    """Mock TavilyToolset"""
    with patch('backend.agents.specialized.agent_d.nodes.TavilyToolset') as mock:
        toolset = AsyncMock()
        mock.return_value = toolset
        yield toolset


@pytest.fixture
def base_state():
    """Base state for testing"""
    return {
        "query": "test query",
        "user_id": uuid4(),
        "thread_id": uuid4(),
        "conversation_context": {},
        "action_type": "",
        "action_params": {},
        "collection_id": None,
        "collection_name": None,
        "file_path": None,
        "raw_content": None,
        "chunks": None,
        "search_query": None,
        "web_documents": None,
        "search_results": None,
        "final_response": None,
        "error": None,
        "current_step": "starting",
        "task_callback": None,
    }


class TestFetchWebNode:
    """Test fetch_web_node with TavilyToolset"""

    @pytest.mark.asyncio
    async def test_fetch_web_cache_hit(self, base_state, mock_settings, mock_document_store, mock_tavily_toolset):
        """Test web search with cache hit"""
        state = {
            **base_state,
            "action_params": {"query": "Python async patterns"},
        }

        # Mock cache hit result
        mock_result = TavilySearchResult(
            query="Python async patterns",
            results=[
                {
                    "title": "Python Async Guide",
                    "content": "Comprehensive guide to Python async...",
                    "url": "https://example.com/async",
                    "score": 0.95,
                }
            ],
            source="cache",
            execution_time_ms=87.23,
        )
        mock_tavily_toolset.search = AsyncMock(return_value=mock_result)

        result = await fetch_web_node(state)

        # Verify web documents created
        assert "web_documents" in result
        assert len(result["web_documents"]) == 1
        assert "Python Async Guide" in result["web_documents"][0]["content"]
        assert result["web_documents"][0]["metadata"]["source_type"] == "web"
        assert result["web_documents"][0]["metadata"]["cache_source"] == "cache"

        # Verify response includes cache info
        assert "(from cache)" in result["final_response"]

    @pytest.mark.asyncio
    async def test_fetch_web_api_call(self, base_state, mock_settings, mock_document_store, mock_tavily_toolset):
        """Test web search with API call"""
        state = {
            **base_state,
            "action_params": {"query": "New AI regulations"},
        }

        # Mock API call result
        mock_result = TavilySearchResult(
            query="New AI regulations",
            results=[
                {
                    "title": "EU AI Act",
                    "content": "New regulations...",
                    "url": "https://example.com/ai-act",
                    "score": 0.98,
                }
            ],
            source="api",
            execution_time_ms=1847.56,
        )
        mock_tavily_toolset.search = AsyncMock(return_value=mock_result)

        result = await fetch_web_node(state)

        # Verify TavilyToolset was initialized correctly
        mock_tavily_toolset.search.assert_called_once()
        call_kwargs = mock_tavily_toolset.search.call_args.kwargs
        assert call_kwargs["use_cache"] is True
        assert call_kwargs["query"] == "New AI regulations"

    @pytest.mark.asyncio
    async def test_fetch_web_no_query(self, base_state, mock_settings, mock_document_store):
        """Test fetch_web with missing query"""
        state = {
            **base_state,
            "action_params": {},  # No query
        }

        result = await fetch_web_node(state)

        # Verify error handling
        assert result["error"] == "No search query provided"
        assert "Please provide a search query" in result["final_response"]

    @pytest.mark.asyncio
    async def test_fetch_web_no_results(self, base_state, mock_settings, mock_document_store, mock_tavily_toolset):
        """Test fetch_web with empty results"""
        state = {
            **base_state,
            "action_params": {"query": "nonexistent topic"},
        }

        # Mock empty results
        mock_result = TavilySearchResult(
            query="nonexistent topic",
            results=[],
            source="api",
            execution_time_ms=500.0,
        )
        mock_tavily_toolset.search = AsyncMock(return_value=mock_result)

        result = await fetch_web_node(state)

        # Verify empty results handled
        assert result["web_documents"] == []
        assert "No web results found" in result["final_response"]


class TestCrawlSiteNode:
    """Test crawl_site_node"""

    @pytest.mark.asyncio
    async def test_crawl_site_success(self, base_state, mock_settings, mock_document_store, mock_tavily_toolset):
        """Test successful site crawl"""
        state = {
            **base_state,
            "action_params": {"base_url": "https://docs.python.org"},
        }

        # Mock crawl result
        mock_result = CrawlResult(
            base_url="https://docs.python.org",
            pages_crawled=25,
            results=[
                {"url": "https://docs.python.org/page1", "title": "Page 1", "content": "Content 1"},
                {"url": "https://docs.python.org/page2", "title": "Page 2", "content": "Content 2"},
            ],
            source="api",
            execution_time_ms=3500.0,
        )
        mock_tavily_toolset.crawl = AsyncMock(return_value=mock_result)

        result = await crawl_site_node(state)

        # Verify crawl was called
        mock_tavily_toolset.crawl.assert_called_once()
        call_kwargs = mock_tavily_toolset.crawl.call_args.kwargs
        assert call_kwargs["base_url"] == "https://docs.python.org"
        assert call_kwargs["max_depth"] == 2
        assert call_kwargs["max_breadth"] == 20
        assert call_kwargs["limit"] == 50

        # Verify web documents created
        assert len(result["web_documents"]) == 2
        assert result["web_documents"][0]["metadata"]["source_type"] == "web_crawl"

    @pytest.mark.asyncio
    async def test_crawl_site_no_url(self, base_state, mock_settings, mock_document_store):
        """Test crawl with missing URL"""
        state = {
            **base_state,
            "action_params": {},  # No URL
        }

        result = await crawl_site_node(state)

        # Verify error handling
        assert result["error"] == "No base URL provided"


class TestExtractUrlsNode:
    """Test extract_urls_node"""

    @pytest.mark.asyncio
    async def test_extract_urls_success(self, base_state, mock_settings, mock_document_store, mock_tavily_toolset):
        """Test successful URL extraction"""
        state = {
            **base_state,
            "action_params": {
                "urls": ["https://example.com/page1", "https://example.com/page2"]
            },
        }

        # Mock extract result
        mock_results = [
            ExtractedContent(
                url="https://example.com/page1",
                title="Page 1",
                content="Extracted content from page 1",
                source="api",
            ),
            ExtractedContent(
                url="https://example.com/page2",
                title="Page 2",
                content="Extracted content from page 2",
                source="api",
            ),
        ]
        mock_tavily_toolset.extract = AsyncMock(return_value=mock_results)

        result = await extract_urls_node(state)

        # Verify extract was called
        mock_tavily_toolset.extract.assert_called_once()
        call_kwargs = mock_tavily_toolset.extract.call_args.kwargs
        assert call_kwargs["urls"] == ["https://example.com/page1", "https://example.com/page2"]
        assert call_kwargs["extract_depth"] == "advanced"

        # Verify web documents created
        assert len(result["web_documents"]) == 2
        assert result["web_documents"][0]["metadata"]["source_type"] == "web_extract"

    @pytest.mark.asyncio
    async def test_extract_urls_no_urls(self, base_state, mock_settings, mock_document_store):
        """Test extract with no URLs"""
        state = {
            **base_state,
            "action_params": {"urls": []},
        }

        result = await extract_urls_node(state)

        # Verify error handling
        assert result["error"] == "No URLs provided"


class TestMapSiteNode:
    """Test map_site_node"""

    @pytest.mark.asyncio
    async def test_map_site_success(self, base_state, mock_settings, mock_document_store, mock_tavily_toolset):
        """Test successful site mapping"""
        state = {
            **base_state,
            "action_params": {"base_url": "https://example.com"},
        }

        # Mock map result
        mock_result = SiteMapResult(
            base_url="https://example.com",
            urls=[
                "https://example.com/",
                "https://example.com/about",
                "https://example.com/contact",
            ],
            structure={"homepage": "https://example.com/", "pages": ["about", "contact"]},
            source="api",
            execution_time_ms=2500.0,
        )
        mock_tavily_toolset.map_site = AsyncMock(return_value=mock_result)

        result = await map_site_node(state)

        # Verify map was called
        mock_tavily_toolset.map_site.assert_called_once()

        # Verify response contains URL list
        assert "https://example.com/" in result["final_response"]
        assert "https://example.com/about" in result["final_response"]
        assert "Total URLs: 3" in result["final_response"]


class TestDocumentStoreSingleton:
    """Test DocumentStore singleton usage"""

    @pytest.mark.asyncio
    async def test_get_document_store_called_in_fetch_web(
        self, base_state, mock_settings, mock_document_store, mock_tavily_toolset
    ):
        """Test that get_document_store is called in fetch_web_node"""
        state = {
            **base_state,
            "action_params": {"query": "test"},
        }

        mock_result = TavilySearchResult(
            query="test",
            results=[{"title": "Test", "content": "Content", "url": "https://test.com", "score": 0.9}],
            source="api",
            execution_time_ms=1000.0,
        )
        mock_tavily_toolset.search = AsyncMock(return_value=mock_result)

        with patch('backend.agents.specialized.agent_d.nodes.get_document_store') as mock_get_ds:
            mock_get_ds.return_value = mock_document_store

            await fetch_web_node(state)

            # Verify get_document_store was called (singleton pattern)
            mock_get_ds.assert_called_once()


class TestTavilyToolsetInitialization:
    """Test TavilyToolset initialization in nodes"""

    @pytest.mark.asyncio
    async def test_fetch_web_initializes_toolset_correctly(
        self, base_state, mock_settings, mock_document_store, mock_tavily_toolset
    ):
        """Test fetch_web initializes TavilyToolset with correct params"""
        state = {
            **base_state,
            "action_params": {"query": "test"},
        }

        mock_result = TavilySearchResult(
            query="test",
            results=[{"title": "Test", "content": "Content", "url": "https://test.com", "score": 0.9}],
            source="api",
            execution_time_ms=1000.0,
        )
        mock_tavily_toolset.search = AsyncMock(return_value=mock_result)

        with patch('backend.agents.specialized.agent_d.nodes.TavilyToolset') as MockToolset:
            MockToolset.return_value = mock_tavily_toolset

            await fetch_web_node(state)

            # Verify TavilyToolset initialization
            MockToolset.assert_called_once_with(
                api_key="test_api_key",
                document_store=mock_document_store,
                enable_caching=True,
            )

    @pytest.mark.asyncio
    async def test_crawl_site_initializes_toolset(
        self, base_state, mock_settings, mock_document_store, mock_tavily_toolset
    ):
        """Test crawl_site initializes TavilyToolset"""
        state = {
            **base_state,
            "action_params": {"base_url": "https://example.com"},
        }

        mock_result = CrawlResult(
            base_url="https://example.com",
            pages_crawled=2,
            results=[],
            source="api",
            execution_time_ms=1000.0,
        )
        mock_tavily_toolset.crawl = AsyncMock(return_value=mock_result)

        with patch('backend.agents.specialized.agent_d.nodes.TavilyToolset') as MockToolset:
            MockToolset.return_value = mock_tavily_toolset

            await crawl_site_node(state)

            # Verify initialization
            MockToolset.assert_called_once_with(
                api_key="test_api_key",
                document_store=mock_document_store,
                enable_caching=True,
            )


class TestMetadataStructure:
    """Test metadata structure in web documents"""

    @pytest.mark.asyncio
    async def test_fetch_web_metadata_includes_cache_source(
        self, base_state, mock_settings, mock_document_store, mock_tavily_toolset
    ):
        """Test fetch_web includes cache_source in metadata"""
        state = {
            **base_state,
            "action_params": {"query": "test"},
        }

        mock_result = TavilySearchResult(
            query="test",
            results=[{"title": "Test", "content": "Content", "url": "https://test.com", "score": 0.9}],
            source="cache",
            execution_time_ms=50.0,
        )
        mock_tavily_toolset.search = AsyncMock(return_value=mock_result)

        result = await fetch_web_node(state)

        # Verify metadata structure
        doc = result["web_documents"][0]
        assert doc["metadata"]["source_type"] == "web"
        assert doc["metadata"]["cache_source"] == "cache"
        assert doc["metadata"]["url"] == "https://test.com"
        assert doc["metadata"]["title"] == "Test"
        assert doc["metadata"]["score"] == 0.9
        assert doc["metadata"]["result_index"] == 0

    @pytest.mark.asyncio
    async def test_crawl_site_metadata_structure(
        self, base_state, mock_settings, mock_document_store, mock_tavily_toolset
    ):
        """Test crawl_site metadata structure"""
        state = {
            **base_state,
            "action_params": {"base_url": "https://example.com"},
        }

        mock_result = CrawlResult(
            base_url="https://example.com",
            pages_crawled=1,
            results=[{"url": "https://example.com/page", "title": "Page", "content": "Content"}],
            source="api",
            execution_time_ms=1000.0,
        )
        mock_tavily_toolset.crawl = AsyncMock(return_value=mock_result)

        result = await crawl_site_node(state)

        # Verify metadata
        doc = result["web_documents"][0]
        assert doc["metadata"]["source_type"] == "web_crawl"
        assert doc["metadata"]["base_url"] == "https://example.com"
        assert doc["metadata"]["url"] == "https://example.com/page"
