"""
Unit tests for Agent G (chat) - Chat Assistant
Tests Phase 4 migration: TavilyToolset integration with StructuredTool
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

from backend.agents.specialized.agent_g.llm_chat import (
    llm_generate_chat_response,
    _create_web_search_tool,
)
from backend.tools.web_search.tavily_toolset import TavilySearchResult
from backend.tools.web_search.exceptions import (
    TavilyAPIError,
    TavilyRateLimitError,
    TavilyTimeoutError,
)


@pytest.fixture
def mock_settings():
    """Mock settings with API keys"""
    with patch('backend.agents.specialized.agent_g.llm_chat.get_settings') as mock:
        settings = MagicMock()
        settings.tavily_api_key = "test_tavily_key"
        settings.openai_api_key = "test_openai_key"
        mock.return_value = settings
        yield settings


@pytest.fixture
def mock_document_store():
    """Mock DocumentStore singleton"""
    with patch('backend.agents.specialized.agent_g.llm_chat.get_document_store') as mock:
        doc_store = AsyncMock()
        mock.return_value = doc_store
        yield doc_store


@pytest.fixture
def mock_tavily_toolset():
    """Mock TavilyToolset"""
    with patch('backend.agents.specialized.agent_g.llm_chat.TavilyToolset') as mock:
        toolset = AsyncMock()
        mock.return_value = toolset
        yield toolset


class TestCreateWebSearchTool:
    """Test _create_web_search_tool function"""

    @pytest.mark.asyncio
    async def test_creates_structured_tool(self, mock_settings, mock_document_store, mock_tavily_toolset):
        """Test that _create_web_search_tool creates a valid StructuredTool"""
        user_id = uuid4()

        # Mock successful search
        mock_result = TavilySearchResult(
            query="test query",
            results=[
                {
                    "title": "Test Result",
                    "content": "Test content",
                    "url": "https://example.com",
                    "score": 0.95,
                }
            ],
            source="api",
            execution_time_ms=500.0,
        )
        mock_tavily_toolset.search = AsyncMock(return_value=mock_result)

        tool = await _create_web_search_tool(user_id)

        # Verify tool properties
        assert tool.name == "web_search"
        assert "Search the web" in tool.description
        assert callable(tool.coroutine)

    @pytest.mark.asyncio
    async def test_tool_initializes_tavily_correctly(self, mock_settings, mock_document_store, mock_tavily_toolset):
        """Test that tool initializes TavilyToolset with correct parameters"""
        user_id = uuid4()

        with patch('backend.agents.specialized.agent_g.llm_chat.TavilyToolset') as MockToolset:
            MockToolset.return_value = mock_tavily_toolset

            await _create_web_search_tool(user_id)

            # Verify TavilyToolset initialization
            MockToolset.assert_called_once_with(
                api_key="test_tavily_key",
                document_store=mock_document_store,
                enable_caching=True,
            )

    @pytest.mark.asyncio
    async def test_tool_search_uses_cache(self, mock_settings, mock_document_store, mock_tavily_toolset):
        """Test that web search tool uses cache-first pattern"""
        user_id = uuid4()

        mock_result = TavilySearchResult(
            query="test",
            results=[{"title": "Test", "content": "Content", "url": "https://test.com", "score": 0.9}],
            source="cache",
            execution_time_ms=50.0,
        )
        mock_tavily_toolset.search = AsyncMock(return_value=mock_result)

        tool = await _create_web_search_tool(user_id)

        # Invoke the tool
        result = await tool.coroutine("test query")

        # Verify cache was enabled
        mock_tavily_toolset.search.assert_called_once()
        call_kwargs = mock_tavily_toolset.search.call_args.kwargs
        assert call_kwargs["use_cache"] is True
        assert call_kwargs["max_results"] == 5
        assert call_kwargs["user_id"] == user_id

    @pytest.mark.asyncio
    async def test_tool_formats_results_for_llm(self, mock_settings, mock_document_store, mock_tavily_toolset):
        """Test that tool formats search results for LLM consumption"""
        user_id = uuid4()

        mock_result = TavilySearchResult(
            query="Python async",
            results=[
                {
                    "title": "Python Async Guide",
                    "content": "Guide to async programming",
                    "url": "https://example.com/async",
                    "score": 0.95,
                },
                {
                    "title": "AsyncIO Tutorial",
                    "content": "Learn asyncio",
                    "url": "https://example.com/asyncio",
                    "score": 0.90,
                },
            ],
            source="api",
            execution_time_ms=1500.0,
        )
        mock_tavily_toolset.search = AsyncMock(return_value=mock_result)

        tool = await _create_web_search_tool(user_id)
        result = await tool.coroutine("Python async")

        # Verify formatting
        assert "Web search results for 'Python async'" in result
        assert "1. **Python Async Guide**" in result
        assert "2. **AsyncIO Tutorial**" in result
        assert "https://example.com/async" in result

    @pytest.mark.asyncio
    async def test_tool_handles_cache_hit(self, mock_settings, mock_document_store, mock_tavily_toolset):
        """Test that tool indicates cache hits in response"""
        user_id = uuid4()

        mock_result = TavilySearchResult(
            query="test",
            results=[{"title": "Test", "content": "Content", "url": "https://test.com", "score": 0.9}],
            source="cache",  # Cache hit
            execution_time_ms=50.0,
        )
        mock_tavily_toolset.search = AsyncMock(return_value=mock_result)

        tool = await _create_web_search_tool(user_id)
        result = await tool.coroutine("test")

        # Verify cache indicator
        assert "(from cache)" in result

    @pytest.mark.asyncio
    async def test_tool_handles_empty_results(self, mock_settings, mock_document_store, mock_tavily_toolset):
        """Test that tool handles empty search results gracefully"""
        user_id = uuid4()

        mock_result = TavilySearchResult(
            query="nonexistent",
            results=[],
            source="api",
            execution_time_ms=500.0,
        )
        mock_tavily_toolset.search = AsyncMock(return_value=mock_result)

        tool = await _create_web_search_tool(user_id)
        result = await tool.coroutine("nonexistent")

        # Verify empty results handling
        assert "No search results found" in result

    @pytest.mark.asyncio
    async def test_tool_handles_search_error(self, mock_settings, mock_document_store, mock_tavily_toolset):
        """Test that tool handles search errors gracefully"""
        user_id = uuid4()

        mock_tavily_toolset.search = AsyncMock(
            side_effect=TavilyAPIError("API error")
        )

        tool = await _create_web_search_tool(user_id)
        result = await tool.coroutine("test")

        # Verify error handling
        assert "Web search encountered an error" in result
        assert "Using my knowledge instead" in result


class TestLLMGenerateChatResponse:
    """Test llm_generate_chat_response function"""

    @pytest.mark.asyncio
    async def test_generates_response_without_tool_use(self, mock_settings, mock_document_store, mock_tavily_toolset):
        """Test response generation without web search"""
        user_id = uuid4()

        with patch('backend.agents.specialized.agent_g.llm_chat.ChatOpenAI') as mock_llm_class:
            mock_llm = AsyncMock()
            mock_response = MagicMock()
            mock_response.content = "This is a test response."
            mock_llm.ainvoke = AsyncMock(return_value=mock_response)
            mock_llm.bind_tools = MagicMock(return_value=mock_llm)
            mock_llm_class.return_value = mock_llm

            response = await llm_generate_chat_response(
                current_message="Hello, how are you?",
                user_id=user_id,
            )

            # Verify response
            assert response == "This is a test response."
            mock_llm.ainvoke.assert_called_once()

    @pytest.mark.asyncio
    async def test_includes_conversation_history(self, mock_settings, mock_document_store, mock_tavily_toolset):
        """Test that conversation history is included in messages"""
        user_id = uuid4()

        conversation_history = [
            {"role": "user", "content": "First question"},
            {"role": "assistant", "content": "First answer"},
            {"role": "user", "content": "Second question"},
            {"role": "assistant", "content": "Second answer"},
        ]

        with patch('backend.agents.specialized.agent_g.llm_chat.ChatOpenAI') as mock_llm_class:
            mock_llm = AsyncMock()
            mock_response = MagicMock()
            mock_response.content = "Continuing conversation..."
            mock_llm.ainvoke = AsyncMock(return_value=mock_response)
            mock_llm.bind_tools = MagicMock(return_value=mock_llm)
            mock_llm_class.return_value = mock_llm

            response = await llm_generate_chat_response(
                current_message="Third question",
                user_id=user_id,
                conversation_history=conversation_history,
            )

            # Verify history was included
            mock_llm.ainvoke.assert_called_once()
            messages = mock_llm.ainvoke.call_args[0][0]

            # Should have: system + 4 history + current = 6 messages
            assert len(messages) >= 5

    @pytest.mark.asyncio
    async def test_llm_configured_correctly(self, mock_settings, mock_document_store, mock_tavily_toolset):
        """Test that LLM is configured with correct parameters"""
        user_id = uuid4()

        with patch('backend.agents.specialized.agent_g.llm_chat.ChatOpenAI') as mock_llm_class:
            mock_llm = AsyncMock()
            mock_response = MagicMock()
            mock_response.content = "Response"
            mock_llm.ainvoke = AsyncMock(return_value=mock_response)
            mock_llm.bind_tools = MagicMock(return_value=mock_llm)
            mock_llm_class.return_value = mock_llm

            await llm_generate_chat_response(
                current_message="test",
                user_id=user_id,
            )

            # Verify LLM initialization
            mock_llm_class.assert_called_once_with(
                model="gpt-4o-mini",
                temperature=0.7,
                api_key="test_openai_key",
                max_tokens=2000,
            )

    @pytest.mark.asyncio
    async def test_tracks_token_usage(self, mock_settings, mock_document_store, mock_tavily_toolset):
        """Test that token usage is tracked when metrics provided"""
        user_id = uuid4()

        with patch('backend.agents.specialized.agent_g.llm_chat.ChatOpenAI') as mock_llm_class:
            mock_llm = AsyncMock()
            mock_response = MagicMock()
            mock_response.content = "Response"
            # Mock token usage in response
            mock_response.response_metadata = {
                "token_usage": {
                    "prompt_tokens": 100,
                    "completion_tokens": 50,
                }
            }
            mock_llm.ainvoke = AsyncMock(return_value=mock_response)
            mock_llm.bind_tools = MagicMock(return_value=mock_llm)
            mock_llm_class.return_value = mock_llm

            # Mock metrics
            mock_metrics = MagicMock()
            mock_metrics.add_llm_call = MagicMock()

            await llm_generate_chat_response(
                current_message="test",
                user_id=user_id,
                metrics=mock_metrics,
            )

            # Verify token tracking
            mock_metrics.add_llm_call.assert_called_once_with(
                model="gpt-4o-mini",
                prompt_tokens=100,
                completion_tokens=50,
                purpose="chat_response"
            )

    @pytest.mark.asyncio
    async def test_system_prompt_includes_web_search_guidance(self, mock_settings, mock_document_store, mock_tavily_toolset):
        """Test that system prompt mentions web search capability"""
        user_id = uuid4()

        with patch('backend.agents.specialized.agent_g.llm_chat.ChatOpenAI') as mock_llm_class:
            mock_llm = AsyncMock()
            mock_response = MagicMock()
            mock_response.content = "Response"
            mock_llm.ainvoke = AsyncMock(return_value=mock_response)
            mock_llm.bind_tools = MagicMock(return_value=mock_llm)
            mock_llm_class.return_value = mock_llm

            await llm_generate_chat_response(
                current_message="test",
                user_id=user_id,
            )

            # Verify system prompt content
            messages = mock_llm.ainvoke.call_args[0][0]
            system_message = messages[0]

            assert "web search" in system_message.content.lower()
            assert "web_search tool" in system_message.content.lower()


class TestWebSearchToolIntegration:
    """Test web search tool integration with chat"""

    @pytest.mark.asyncio
    async def test_tool_binding(self, mock_settings, mock_document_store, mock_tavily_toolset):
        """Test that web search tool is properly bound to LLM"""
        user_id = uuid4()

        with patch('backend.agents.specialized.agent_g.llm_chat.ChatOpenAI') as mock_llm_class:
            mock_llm = AsyncMock()
            mock_response = MagicMock()
            mock_response.content = "Response"
            mock_llm.ainvoke = AsyncMock(return_value=mock_response)

            # Track bind_tools call
            bound_llm = AsyncMock()
            bound_llm.ainvoke = AsyncMock(return_value=mock_response)
            mock_llm.bind_tools = MagicMock(return_value=bound_llm)
            mock_llm_class.return_value = mock_llm

            await llm_generate_chat_response(
                current_message="test",
                user_id=user_id,
            )

            # Verify bind_tools was called
            mock_llm.bind_tools.assert_called_once()
            tools = mock_llm.bind_tools.call_args.kwargs["tools"]
            assert len(tools) == 1
            assert tools[0].name == "web_search"

    @pytest.mark.asyncio
    async def test_document_store_singleton_used(self, mock_settings, mock_document_store, mock_tavily_toolset):
        """Test that DocumentStore singleton is used"""
        user_id = uuid4()

        with patch('backend.agents.specialized.agent_g.llm_chat.get_document_store') as mock_get_ds:
            mock_get_ds.return_value = mock_document_store

            with patch('backend.agents.specialized.agent_g.llm_chat.ChatOpenAI') as mock_llm_class:
                mock_llm = AsyncMock()
                mock_response = MagicMock()
                mock_response.content = "Response"
                mock_llm.ainvoke = AsyncMock(return_value=mock_response)
                mock_llm.bind_tools = MagicMock(return_value=mock_llm)
                mock_llm_class.return_value = mock_llm

                await llm_generate_chat_response(
                    current_message="test",
                    user_id=user_id,
                )

                # Verify get_document_store was called
                mock_get_ds.assert_called_once()


class TestErrorHandling:
    """Test error handling in chat with web search"""

    @pytest.mark.asyncio
    async def test_tavily_error_logged(self, mock_settings, mock_document_store, mock_tavily_toolset):
        """Test that Tavily errors are logged in web search tool"""
        user_id = uuid4()

        mock_tavily_toolset.search = AsyncMock(
            side_effect=TavilyAPIError("API failed")
        )

        with patch('backend.agents.specialized.agent_g.llm_chat.logger') as mock_logger:
            tool = await _create_web_search_tool(user_id)
            result = await tool.coroutine("test")

            # Verify error was logged
            mock_logger.error.assert_called()
            log_message = mock_logger.error.call_args[0][0]
            assert "Web search failed" in log_message
