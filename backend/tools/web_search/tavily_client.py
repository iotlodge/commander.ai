"""
Tavily Web Search Client - Async wrapper for Tavily API
"""

import logging
from typing import List, Dict, Any
from tavily import AsyncTavilyClient
from backend.core.config import get_settings

logger = logging.getLogger(__name__)


class TavilyClient:
    """
    Async client for Tavily web search API

    Provides structured web search with source retention for DocumentManager agent.
    """

    def __init__(self):
        self.settings = get_settings()
        self.client: AsyncTavilyClient | None = None

    async def connect(self):
        """Initialize Tavily client"""
        if not self.settings.tavily_api_key:
            raise ValueError("TAVILY_API_KEY not configured in settings")

        self.client = AsyncTavilyClient(api_key=self.settings.tavily_api_key)
        logger.info("Tavily client connected")

    async def disconnect(self):
        """Cleanup Tavily client"""
        self.client = None
        logger.info("Tavily client disconnected")

    async def search(
        self,
        query: str,
        max_results: int | None = None,
        include_answer: bool = False,
        include_raw_content: bool = False,
        search_depth: str = "basic"
    ) -> Dict[str, Any]:
        """
        Perform web search using Tavily API

        Args:
            query: Search query string
            max_results: Maximum number of results to return (default from settings)
            include_answer: Whether to include AI-generated answer
            include_raw_content: Whether to include raw HTML content
            search_depth: "basic" or "advanced" search depth

        Returns:
            {
                "query": str,
                "answer": str | None,
                "results": [
                    {
                        "title": str,
                        "url": str,
                        "content": str,
                        "score": float,
                        "raw_content": str | None
                    }
                ]
            }
        """
        if not self.client:
            await self.connect()

        max_results = max_results or self.settings.tavily_max_results

        try:
            logger.info(f"Tavily search: query='{query}', max_results={max_results}")

            response = await self.client.search(
                query=query,
                max_results=max_results,
                include_answer=include_answer,
                include_raw_content=include_raw_content,
                search_depth=search_depth
            )

            # Structure response
            structured_response = {
                "query": query,
                "answer": response.get("answer") if include_answer else None,
                "results": []
            }

            # Extract results
            for result in response.get("results", []):
                structured_response["results"].append({
                    "title": result.get("title", ""),
                    "url": result.get("url", ""),
                    "content": result.get("content", ""),
                    "score": result.get("score", 0.0),
                    "raw_content": result.get("raw_content") if include_raw_content else None
                })

            logger.info(f"Tavily search returned {len(structured_response['results'])} results")
            return structured_response

        except Exception as e:
            logger.error(f"Tavily search failed: {e}")
            raise

    async def search_and_format(
        self,
        query: str,
        max_results: int | None = None,
    ) -> List[Dict[str, Any]]:
        """
        Search and format results for document storage

        Returns list of documents ready for chunking:
        [
            {
                "content": str,  # Combined title + content
                "metadata": {
                    "source_type": "web",
                    "url": str,
                    "title": str,
                    "query": str,
                    "score": float
                }
            }
        ]
        """
        response = await self.search(
            query=query,
            max_results=max_results,
            include_answer=False,
            include_raw_content=False
        )

        documents = []
        for result in response["results"]:
            # Combine title and content for better context
            content = f"# {result['title']}\n\n{result['content']}\n\nSource: {result['url']}"

            documents.append({
                "content": content,
                "metadata": {
                    "source_type": "web",
                    "url": result["url"],
                    "title": result["title"],
                    "query": query,
                    "score": result["score"]
                }
            })

        return documents
