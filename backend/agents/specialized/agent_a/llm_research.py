"""
LLM-Powered Research Utilities for Bob (Research Specialist)
Uses OpenAI GPT-4o-mini for research analysis and synthesis
Web search powered by TavilyToolset with cache-first pattern
"""

import logging
from typing import Any
from uuid import UUID
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage

from backend.core.config import get_settings
from backend.core.dependencies import get_document_store
from backend.core.token_tracker import ExecutionMetrics, extract_token_usage_from_response
from backend.tools.web_search.tavily_toolset import TavilyToolset
from backend.tools.web_search.exceptions import (
    TavilyAPIError,
    TavilyRateLimitError,
    TavilyTimeoutError,
)

logger = logging.getLogger(__name__)


async def llm_web_search(
    query: str,
    user_id: UUID,
    metrics: ExecutionMetrics | None = None,
    use_cache: bool = True,
) -> list[dict[str, Any]]:
    """
    Perform web search using Tavily API with cache-first pattern

    Args:
        query: Search query
        user_id: User ID for cache scoping
        metrics: Optional execution metrics tracker
        use_cache: Whether to use cache-first pattern (default: True)

    Returns:
        List of search results with title, snippet, url, score
    """
    settings = get_settings()

    # Try Tavily if API key is configured
    if settings.tavily_api_key:
        try:
            # Get document store singleton
            doc_store = await get_document_store()

            # Initialize TavilyToolset with cache-first pattern
            tavily = TavilyToolset(
                api_key=settings.tavily_api_key,
                document_store=doc_store,
                enable_caching=True,
            )

            # Search with cache-first pattern
            result = await tavily.search(
                query=query,
                user_id=user_id,
                max_results=settings.tavily_max_results,
                use_cache=use_cache,
                search_depth="basic",
            )

            # Format results
            formatted_results = []
            for search_result in result.results:
                formatted_results.append({
                    "title": search_result.get("title", "No title"),
                    "snippet": search_result.get("content", "No content"),
                    "url": search_result.get("url", ""),
                    "score": search_result.get("score", 0.0),
                })

            # Log cache hit/miss
            cache_info = f"(from {result.source})" if result.source else ""
            logger.info(
                f"Web search completed: {len(formatted_results)} results {cache_info} "
                f"in {result.execution_time_ms:.2f}ms"
            )

            return formatted_results

        except TavilyRateLimitError as e:
            logger.warning(f"Tavily rate limit exceeded: {e}. Trying cache-only mode.")
            # Try cache-only as fallback
            try:
                tavily = TavilyToolset(
                    api_key=settings.tavily_api_key,
                    document_store=await get_document_store(),
                    enable_caching=True,
                )
                cached_result = await tavily._check_cache(query, user_id, ttl_hours=24)
                if cached_result:
                    logger.info("Using cached results due to rate limit")
                    formatted_results = []
                    for r in cached_result.results:
                        formatted_results.append({
                            "title": r.get("title", "No title"),
                            "snippet": r.get("content", "No content"),
                            "url": r.get("url", ""),
                            "score": r.get("score", 0.0),
                        })
                    return formatted_results
            except Exception as cache_error:
                logger.error(f"Cache fallback also failed: {cache_error}")

        except TavilyTimeoutError as e:
            logger.error(f"Tavily search timeout: {e}. Falling back to LLM knowledge.")

        except TavilyAPIError as e:
            logger.error(f"Tavily API error: {e}. Falling back to LLM knowledge.")

        except Exception as e:
            logger.error(
                f"Unexpected error during Tavily search: {e}. Falling back to LLM knowledge.",
                exc_info=True
            )

    else:
        logger.info("Tavily API key not configured, using LLM knowledge fallback")

    # Fallback: Use LLM's knowledge (no real web search)
    llm = ChatOpenAI(
        model="gpt-4o-mini",
        temperature=0.3,
        api_key=settings.openai_api_key,
    )

    system_prompt = """You are a research assistant. When given a search query, provide relevant information based on your knowledge.
Format your response as if you were presenting web search results.
Include key facts, recent developments, and important considerations."""

    user_prompt = f"""Research query: {query}

Provide 3-5 key points about this topic based on your knowledge."""

    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=user_prompt),
    ]

    response = await llm.ainvoke(messages)

    # Track token usage
    if metrics:
        prompt_tokens, completion_tokens = extract_token_usage_from_response(response)
        metrics.add_llm_call(
            model="gpt-4o-mini",
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            purpose="web_search_fallback"
        )

    # Format as simulated search result
    return [
        {
            "title": f"Research findings for: {query}",
            "snippet": response.content,
            "url": "knowledge-base",
            "score": 1.0,
        }
    ]


async def llm_synthesize_research(
    query: str,
    search_results: list[dict[str, Any]],
    context: dict[str, Any] | None = None,
    metrics: ExecutionMetrics | None = None
) -> str:
    """
    Use LLM to synthesize search results into coherent research response

    Args:
        query: Original research query
        search_results: List of search results to synthesize
        context: Optional conversation context
        metrics: Optional execution metrics tracker

    Returns:
        Synthesized research response
    """
    settings = get_settings()

    llm = ChatOpenAI(
        model="gpt-4o-mini",
        temperature=0.3,
        api_key=settings.openai_api_key,
        max_tokens=2000,
    )

    # TODO: Add image generation capability for complex research synthesis
    # Use image_generate_analyze_upscale.py to create visualizations when:
    # - Illustrating trends or timelines from research findings
    # - Creating comparison charts between different sources
    # - Visualizing concept relationships and hierarchies
    # - Generating infographics for complex data patterns
    # Example: python image_generate_analyze_upscale.py generate \
    #   --prompt "Timeline showing evolution of quantum computing from 2020-2025 based on research findings" \
    #   --output output/research_timeline.png

    system_prompt = """You are Bob, a Research Specialist at Commander.ai.
Your role is to synthesize information from multiple sources into clear, comprehensive research responses.

Guidelines:
- Provide well-structured, informative analysis
- Cite key findings from the sources
- Highlight important insights and implications
- Use clear section headings when appropriate
- Be objective and factual
- Note any limitations or uncertainties
- Format using markdown for readability"""

    # Build sources context
    sources_text = "\n\n".join([
        f"**Source {i+1}** ({result.get('url', 'N/A')}):\n{result.get('snippet', 'No content')}"
        for i, result in enumerate(search_results)
    ])

    user_prompt = f"""Research query: {query}

Available sources:
{sources_text}

Synthesize these sources into a comprehensive research response. Structure your response with:
1. Executive summary (2-3 sentences)
2. Key findings (3-5 main points)
3. Analysis and implications
4. Recommendations or next steps (if applicable)"""

    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=user_prompt),
    ]

    response = await llm.ainvoke(messages)

    # Track token usage
    if metrics:
        prompt_tokens, completion_tokens = extract_token_usage_from_response(response)
        metrics.add_llm_call(
            model="gpt-4o-mini",
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            purpose="research_synthesis"
        )

    return response.content


async def llm_check_compliance_keywords(text: str, metrics: ExecutionMetrics | None = None) -> tuple[bool, list[str]]:
    """
    Use LLM to intelligently detect compliance/regulatory concerns

    Args:
        text: Text to analyze for compliance concerns
        metrics: Optional execution metrics tracker

    Returns:
        Tuple of (needs_review: bool, concerns: list[str])
    """
    settings = get_settings()

    llm = ChatOpenAI(
        model="gpt-4o-mini",
        temperature=0,
        api_key=settings.openai_api_key,
    )

    system_prompt = """You are a compliance detection assistant.
Analyze text for mentions of:
- Privacy regulations (GDPR, CCPA, HIPAA)
- Personal data handling
- Security concerns
- Legal or regulatory requirements
- Data protection
- Consent mechanisms

Output JSON:
{
    "needs_review": true/false,
    "concerns": ["list", "of", "specific", "concerns"],
    "severity": "high" | "medium" | "low" | "none"
}"""

    user_prompt = f"""Analyze this text for compliance concerns:

{text}

Provide your analysis in JSON format."""

    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=user_prompt),
    ]

    try:
        response = await llm.ainvoke(messages)

        # Track token usage
        if metrics:
            prompt_tokens, completion_tokens = extract_token_usage_from_response(response)
            metrics.add_llm_call(
                model="gpt-4o-mini",
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                purpose="compliance_check"
            )

        # Parse JSON response
        import json
        content = response.content

        if "```json" in content:
            content = content.split("```json")[1].split("```")[0].strip()
        elif "```" in content:
            content = content.split("```")[1].split("```")[0].strip()

        result = json.loads(content)

        needs_review = result.get("needs_review", False)
        concerns = result.get("concerns", [])

        return needs_review, concerns

    except Exception as e:
        logger.error(f"LLM compliance check failed: {e}. Using keyword fallback.", exc_info=True)

        # Fallback: simple keyword matching
        compliance_keywords = [
            "privacy", "personal data", "gdpr", "hipaa", "pii",
            "data protection", "consent", "regulation", "compliance"
        ]

        text_lower = text.lower()
        found = [kw for kw in compliance_keywords if kw in text_lower]

        return len(found) > 0, found
