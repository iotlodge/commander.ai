"""
LLM-Powered Research Utilities for Bob (Research Specialist)
Uses OpenAI GPT-4o-mini for research analysis and synthesis
"""

from typing import Any
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage

from backend.core.config import get_settings


async def llm_web_search(query: str) -> list[dict[str, Any]]:
    """
    Perform web search using Tavily API (if configured) or simulate

    Args:
        query: Search query

    Returns:
        List of search results with title, snippet, url
    """
    settings = get_settings()

    # Try Tavily if API key is configured
    if settings.tavily_api_key:
        try:
            from langchain_community.tools.tavily_search import TavilySearchResults

            search = TavilySearchResults(
                api_key=settings.tavily_api_key,
                max_results=settings.tavily_max_results,
            )

            results = await search.ainvoke({"query": query})

            # Format results
            formatted_results = []
            for result in results:
                formatted_results.append({
                    "title": result.get("title", "No title"),
                    "snippet": result.get("content", "No content"),
                    "url": result.get("url", ""),
                    "score": result.get("score", 0.0),
                })

            return formatted_results

        except Exception as e:
            print(f"Tavily search failed: {e}. Using LLM knowledge.")

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
    context: dict[str, Any] | None = None
) -> str:
    """
    Use LLM to synthesize search results into coherent research response

    Args:
        query: Original research query
        search_results: List of search results to synthesize
        context: Optional conversation context

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

    return response.content


async def llm_check_compliance_keywords(text: str) -> tuple[bool, list[str]]:
    """
    Use LLM to intelligently detect compliance/regulatory concerns

    Args:
        text: Text to analyze for compliance concerns

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
        print(f"LLM compliance check failed: {e}. Using fallback.")

        # Fallback: simple keyword matching
        compliance_keywords = [
            "privacy", "personal data", "gdpr", "hipaa", "pii",
            "data protection", "consent", "regulation", "compliance"
        ]

        text_lower = text.lower()
        found = [kw for kw in compliance_keywords if kw in text_lower]

        return len(found) > 0, found
