"""
LLM-Powered Chat Utilities for Chat Assistant
Uses OpenAI GPT-4o-mini for conversational interactions
Web search powered by TavilyToolset with cache-first pattern
"""

import logging
from typing import Any
from uuid import UUID
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from langchain_core.tools import StructuredTool
from pydantic import BaseModel, Field

from backend.core.config import get_settings
from backend.core.dependencies import get_document_store
from backend.core.token_tracker import ExecutionMetrics, extract_token_usage_from_response
from backend.tools.web_search.tavily_toolset import TavilyToolset

logger = logging.getLogger(__name__)


# Pydantic model for search input
class SearchInput(BaseModel):
    """Input for web search tool"""
    query: str = Field(..., description="The search query to look up on the web")


async def _create_web_search_tool(user_id: UUID) -> StructuredTool:
    """
    Create web search tool using TavilyToolset

    Args:
        user_id: User ID for cache scoping

    Returns:
        StructuredTool configured for web search
    """
    settings = get_settings()

    # Get DocumentStore singleton
    doc_store = await get_document_store()

    # Initialize TavilyToolset with cache-first pattern
    tavily = TavilyToolset(
        api_key=settings.tavily_api_key,
        document_store=doc_store,
        enable_caching=True,
    )

    async def search_web(query: str) -> str:
        """
        Search the web for current information

        Use this tool when you need to find recent information, news,
        or facts that may not be in your training data.

        Args:
            query: Search query string

        Returns:
            Formatted search results
        """
        try:
            # Search with cache-first pattern
            result = await tavily.search(
                query=query,
                user_id=user_id,
                max_results=5,
                use_cache=True,
                search_depth="basic",
                topic="general",
            )

            # Format results for LLM consumption
            if not result.results:
                return "No search results found."

            formatted_results = []
            for idx, search_result in enumerate(result.results[:5], 1):
                formatted_results.append(
                    f"{idx}. **{search_result['title']}**\n"
                    f"   {search_result['content']}\n"
                    f"   Source: {search_result['url']}"
                )

            cache_info = f" (from cache)" if result.source == "cache" else ""
            header = f"Web search results for '{query}'{cache_info}:\n\n"

            return header + "\n\n".join(formatted_results)

        except Exception as e:
            logger.error(f"Web search failed: {e}", exc_info=True)
            return f"Web search encountered an error: {str(e)}. Using my knowledge instead."

    # Create StructuredTool
    return StructuredTool.from_function(
        coroutine=search_web,
        name="web_search",
        description=(
            "Search the web for current information, recent events, or facts. "
            "Use this when the user asks about recent events, current news, "
            "or information that may have changed since your training data. "
            "Returns relevant search results from the web."
        ),
        args_schema=SearchInput,
    )


async def llm_generate_chat_response(
    current_message: str,
    user_id: UUID,
    conversation_history: list[dict[str, str]] | None = None,
    metrics: ExecutionMetrics | None = None
) -> str:
    """
    Generate chat response using LLM with web search capability

    Args:
        current_message: Current user message
        user_id: User ID for cache scoping
        conversation_history: Previous messages in format [{role: "user/assistant", content: "..."}]
        metrics: Optional execution metrics tracker

    Returns:
        Generated response string
    """
    settings = get_settings()

    # Create web search tool with cache-first pattern
    web_search_tool = await _create_web_search_tool(user_id)

    llm = ChatOpenAI(
        model="gpt-4o-mini",
        temperature=0.7,
        api_key=settings.openai_api_key,
        max_tokens=2000,
    ).bind_tools(tools=[web_search_tool])

    system_prompt = """You are a helpful AI assistant in the Commander.ai system.
Your role is to have natural, informative conversations with users.

You have access to a web search tool that can look up current information, recent events, and news.
Use the web_search tool when users ask about:
- Recent events or current news
- Information that may have changed since your training data
- Specific facts or data that need verification
- Time-sensitive information

Guidelines:
- Be conversational and friendly
- Provide clear, helpful responses
- Ask clarifying questions when needed
- Use markdown formatting for better readability
- Be concise but thorough
- Admit when you don't know something
- Use web search when appropriate for current/recent information"""

    # Build message list
    messages = [SystemMessage(content=system_prompt)]

    # Add conversation history if available
    if conversation_history:
        for msg in conversation_history:
            if msg["role"] == "user":
                messages.append(HumanMessage(content=msg["content"]))
            elif msg["role"] == "assistant":
                messages.append(AIMessage(content=msg["content"]))

    # Add current message
    messages.append(HumanMessage(content=current_message))

    # Generate response
    response = await llm.ainvoke(messages)

    # Track token usage
    if metrics:
        prompt_tokens, completion_tokens = extract_token_usage_from_response(response)
        metrics.add_llm_call(
            model="gpt-4o-mini",
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            purpose="chat_response"
        )

    return response.content
