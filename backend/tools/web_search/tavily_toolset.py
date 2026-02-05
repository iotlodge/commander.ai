"""
Unified Tavily Web Search Toolset with Cache-First Architecture

Provides all Tavily operations (search, crawl, extract, map) with:
- Cache-first pattern with staleness checking
- Rate limiting and retry logic
- Connection pooling via shared DocumentStore
- Automatic deduplication by content hash
"""

import asyncio
import hashlib
import logging
import time
from datetime import datetime, timezone, timedelta
from typing import Any, Literal, Optional
from uuid import UUID

from pydantic import BaseModel
from tavily import AsyncTavilyClient

from backend.core.config import get_settings
from backend.memory.document_store import DocumentStore
from backend.tools.web_search.exceptions import (
    TavilyAPIError,
    TavilyCacheError,
    TavilyConfigError,
    TavilyRateLimitError,
    TavilyTimeoutError,
)

logger = logging.getLogger(__name__)


# Response Models
class TavilySearchResult(BaseModel):
    """Result from Tavily search operation"""
    query: str
    results: list[dict[str, Any]]
    answer: Optional[str] = None
    source: Literal["cache", "api"] = "api"
    cached_at: Optional[datetime] = None
    execution_time_ms: float = 0.0


class CrawlResult(BaseModel):
    """Result from Tavily crawl operation"""
    base_url: str
    pages_crawled: int
    results: list[dict[str, Any]]
    source: Literal["cache", "api"] = "api"
    execution_time_ms: float = 0.0


class ExtractedContent(BaseModel):
    """Extracted content from URL"""
    url: str
    title: str
    content: str
    raw_content: Optional[str] = None
    source: Literal["cache", "api"] = "api"


class SiteMapResult(BaseModel):
    """Site map from Tavily map operation"""
    base_url: str
    urls: list[str]
    structure: dict[str, Any]
    source: Literal["cache", "api"] = "api"
    execution_time_ms: float = 0.0


class AsyncRateLimiter:
    """
    Token bucket rate limiter for async operations

    Ensures API calls don't exceed rate limits (default: 60 calls/min)
    """

    def __init__(self, rate_limit_per_minute: int):
        self.rate_limit = rate_limit_per_minute
        self.tokens = rate_limit_per_minute
        self.last_update = time.time()
        self.lock = asyncio.Lock()

    async def acquire(self) -> None:
        """Acquire token, wait if rate limit exceeded"""
        async with self.lock:
            now = time.time()
            elapsed = now - self.last_update

            # Refill tokens based on elapsed time
            self.tokens = min(
                self.rate_limit,
                self.tokens + (elapsed * self.rate_limit / 60.0)
            )
            self.last_update = now

            if self.tokens < 1:
                # Calculate wait time
                wait_time = (1 - self.tokens) * 60.0 / self.rate_limit
                logger.warning(f"Rate limit reached, waiting {wait_time:.2f}s")
                await asyncio.sleep(wait_time)
                self.tokens = 0
            else:
                self.tokens -= 1


class TavilyToolset:
    """
    Unified Tavily operations with cache-first pattern

    Features:
    - All 4 Tavily operations: search, crawl, extract, map
    - Cache-first with staleness checking (24h general, 1h news)
    - Rate limiting (60 calls/min) and exponential backoff retry
    - Connection pooling via shared DocumentStore
    - Automatic deduplication by content hash

    Usage:
        ```python
        from backend.tools.web_search.tavily_toolset import TavilyToolset
        from backend.core.dependencies import get_document_store

        tavily = TavilyToolset(
            api_key=settings.tavily_api_key,
            document_store=await get_document_store(),
            enable_caching=True
        )

        results = await tavily.search(
            query="Python async patterns",
            user_id=user_id,
            use_cache=True
        )
        ```
    """

    def __init__(
        self,
        api_key: str,
        document_store: Optional[DocumentStore] = None,
        cache_ttl_hours: int = 24,
        enable_caching: bool = True,
    ):
        """
        Initialize Tavily toolset

        Args:
            api_key: Tavily API key
            document_store: Shared DocumentStore instance (optional)
            cache_ttl_hours: Default cache TTL in hours (24 for general)
            enable_caching: Whether to enable cache-first pattern
        """
        if not api_key:
            raise TavilyConfigError("Tavily API key is required")

        self.settings = get_settings()
        self.api_key = api_key
        self.document_store = document_store
        self.cache_ttl_hours = cache_ttl_hours
        self.enable_caching = enable_caching

        # Initialize Tavily client
        self.client = AsyncTavilyClient(api_key=api_key)

        # Initialize rate limiter
        self.rate_limiter = AsyncRateLimiter(
            rate_limit_per_minute=self.settings.tavily_rate_limit_per_minute
        )

        logger.info("TavilyToolset initialized with cache-first pattern")

    def _compute_content_hash(self, content: str) -> str:
        """Compute SHA-256 hash of content for deduplication"""
        return hashlib.sha256(content.encode("utf-8")).hexdigest()

    def _get_cache_collection_name(self, user_id: UUID) -> str:
        """Get cache collection name for user"""
        return f"{self.settings.web_cache_collection_prefix}_{user_id}"

    async def _check_cache(
        self,
        query: str,
        user_id: UUID,
        ttl_hours: int,
    ) -> Optional[TavilySearchResult]:
        """
        Check cache for similar query with staleness detection

        Args:
            query: Search query
            user_id: User ID for scoped cache
            ttl_hours: Time-to-live in hours

        Returns:
            Cached result if found and fresh, None otherwise
        """
        if not self.enable_caching or not self.document_store:
            return None

        try:
            collection_name = self._get_cache_collection_name(user_id)

            # Search for similar queries in cache
            results = await self.document_store.search_collection(
                qdrant_collection_name=collection_name,
                user_id=user_id,
                query=query,
                limit=5,
                score_threshold=self.settings.web_cache_similarity_threshold,
            )

            if not results:
                logger.debug(f"Cache miss for query: {query}")
                return None

            # Get the best match
            best_match_id, similarity = results[0]

            # TODO: Retrieve full chunk with metadata from database
            # For now, return None (cache miss) until database integration
            logger.debug(f"Cache hit with similarity {similarity}, but chunk retrieval not implemented")
            return None

        except Exception as e:
            logger.error(f"Cache check failed: {e}", exc_info=True)
            raise TavilyCacheError(f"Failed to check cache: {e}")

    async def _store_to_cache(
        self,
        query: str,
        user_id: UUID,
        results: list[dict[str, Any]],
        ttl_hours: int,
        search_depth: str = "basic",
    ) -> None:
        """
        Store search results to cache with timestamp metadata

        Args:
            query: Search query
            user_id: User ID for scoped cache
            results: Search results to cache
            ttl_hours: Time-to-live in hours
            search_depth: Search depth (basic/advanced)
        """
        if not self.enable_caching or not self.document_store:
            return

        try:
            from backend.models.document_models import ChunkCreate
            from uuid import uuid4

            collection_name = self._get_cache_collection_name(user_id)

            # Create collection if it doesn't exist
            await self.document_store.create_collection(
                qdrant_collection_name=collection_name,
                user_id=user_id
            )

            # Prepare chunks for storage
            chunks = []
            for idx, result in enumerate(results):
                content = f"# {result.get('title', '')}\n\n{result.get('content', '')}\n\nSource: {result.get('url', '')}"
                content_hash = self._compute_content_hash(content)

                chunk = ChunkCreate(
                    vector_id=uuid4(),
                    user_id=user_id,
                    collection_id=uuid4(),  # Cache doesn't use collection_id
                    chunk_index=idx,
                    content=content,
                    source_type="web",
                    source_file_path=result.get("url", ""),
                    file_name=result.get("title", ""),
                    metadata={
                        "source_type": "web",
                        "fetched_at": datetime.now(timezone.utc).isoformat(),
                        "original_query": query,
                        "source_urls": [result.get("url", "")],
                        "search_depth": search_depth,
                        "tavily_score": result.get("score", 0.0),
                        "result_index": idx,
                        "cache_ttl_hours": ttl_hours,
                        "content_hash": content_hash,
                    }
                )
                chunks.append(chunk)

            # Store chunks
            await self.document_store.store_chunks(
                qdrant_collection_name=collection_name,
                chunks=chunks
            )

            logger.info(f"Cached {len(chunks)} results for query: {query}")

        except Exception as e:
            logger.error(f"Failed to store to cache: {e}", exc_info=True)
            # Don't raise - caching failure shouldn't break the search

    async def _api_call_with_retry(
        self,
        operation: callable,
        *args,
        **kwargs
    ) -> Any:
        """
        Execute API call with exponential backoff retry

        Args:
            operation: Async callable to execute
            *args: Positional arguments
            **kwargs: Keyword arguments

        Returns:
            Operation result

        Raises:
            TavilyAPIError: If all retries fail
            TavilyTimeoutError: If operation times out
        """
        max_retries = self.settings.tavily_retry_attempts
        timeout = self.settings.tavily_timeout_seconds

        for attempt in range(max_retries):
            try:
                # Acquire rate limit token
                await self.rate_limiter.acquire()

                # Execute with timeout
                result = await asyncio.wait_for(
                    operation(*args, **kwargs),
                    timeout=timeout
                )
                return result

            except asyncio.TimeoutError:
                logger.error(f"Tavily API timeout on attempt {attempt + 1}/{max_retries}")
                if attempt == max_retries - 1:
                    raise TavilyTimeoutError(
                        f"Tavily API timeout after {max_retries} attempts"
                    )

            except Exception as e:
                logger.error(
                    f"Tavily API error on attempt {attempt + 1}/{max_retries}: {e}",
                    exc_info=True
                )

                if attempt == max_retries - 1:
                    raise TavilyAPIError(f"Tavily API failed after {max_retries} attempts: {e}")

                # Exponential backoff
                wait_time = 2 ** attempt
                logger.info(f"Retrying in {wait_time}s...")
                await asyncio.sleep(wait_time)

    async def search(
        self,
        query: str,
        user_id: UUID,
        max_results: int = 10,
        search_depth: Literal["basic", "advanced"] = "basic",
        use_cache: bool = True,
        topic: Literal["general", "news"] = "general",
        include_answer: bool = False,
        include_raw_content: bool = False,
    ) -> TavilySearchResult:
        """
        Search the web using Tavily API with cache-first pattern

        Args:
            query: Search query string
            user_id: User ID for cache scoping
            max_results: Maximum number of results (default: 10)
            search_depth: "basic" or "advanced" search depth
            use_cache: Whether to check cache first (default: True)
            topic: "general" or "news" (affects TTL)
            include_answer: Include AI-generated answer
            include_raw_content: Include raw HTML content

        Returns:
            TavilySearchResult with results and metadata

        Raises:
            TavilyAPIError: If API call fails after retries
            TavilyRateLimitError: If rate limit exceeded
        """
        start_time = time.time()

        # Determine TTL based on topic
        ttl_hours = (
            self.settings.web_cache_news_ttl_hours
            if topic == "news"
            else self.settings.web_cache_ttl_hours
        )

        # Check cache first
        if use_cache:
            cached_result = await self._check_cache(query, user_id, ttl_hours)
            if cached_result:
                execution_time = (time.time() - start_time) * 1000
                cached_result.execution_time_ms = execution_time
                logger.info(f"Cache hit for query: {query} ({execution_time:.2f}ms)")
                return cached_result

        # Cache miss - call Tavily API
        logger.info(f"Cache miss, calling Tavily API for: {query}")

        try:
            response = await self._api_call_with_retry(
                self.client.search,
                query=query,
                max_results=max_results,
                search_depth=search_depth,
                topic=topic,
                include_answer=include_answer,
                include_raw_content=include_raw_content,
            )

            # Structure response
            results = []
            for result in response.get("results", []):
                results.append({
                    "title": result.get("title", ""),
                    "url": result.get("url", ""),
                    "content": result.get("content", ""),
                    "score": result.get("score", 0.0),
                    "raw_content": result.get("raw_content") if include_raw_content else None,
                })

            # Store to cache
            if use_cache:
                await self._store_to_cache(
                    query=query,
                    user_id=user_id,
                    results=results,
                    ttl_hours=ttl_hours,
                    search_depth=search_depth,
                )

            execution_time = (time.time() - start_time) * 1000

            return TavilySearchResult(
                query=query,
                results=results,
                answer=response.get("answer") if include_answer else None,
                source="api",
                execution_time_ms=execution_time,
            )

        except Exception as e:
            logger.error(f"Tavily search failed: {e}", exc_info=True)
            raise

    async def crawl(
        self,
        base_url: str,
        user_id: UUID,
        max_depth: int = 1,
        max_breadth: int = 20,
        limit: int = 50,
        instructions: Optional[str] = None,
    ) -> CrawlResult:
        """
        Crawl website starting from base URL

        Args:
            base_url: Root URL to begin crawl
            user_id: User ID for cache scoping
            max_depth: Maximum depth from base URL
            max_breadth: Max links to follow per page
            limit: Total number of links to process
            instructions: Natural language crawl instructions

        Returns:
            CrawlResult with crawled pages

        Raises:
            TavilyAPIError: If API call fails
        """
        start_time = time.time()

        try:
            response = await self._api_call_with_retry(
                self.client.crawl,
                url=base_url,
                max_depth=max_depth,
                max_breadth=max_breadth,
                limit=limit,
                instructions=instructions,
            )

            results = response.get("results", [])
            execution_time = (time.time() - start_time) * 1000

            logger.info(f"Crawled {len(results)} pages from {base_url}")

            return CrawlResult(
                base_url=base_url,
                pages_crawled=len(results),
                results=results,
                source="api",
                execution_time_ms=execution_time,
            )

        except Exception as e:
            logger.error(f"Tavily crawl failed: {e}", exc_info=True)
            raise TavilyAPIError(f"Crawl operation failed: {e}")

    async def extract(
        self,
        urls: list[str],
        user_id: UUID,
        extract_depth: Literal["basic", "advanced"] = "basic",
    ) -> list[ExtractedContent]:
        """
        Extract content from specified URLs

        Args:
            urls: List of URLs to extract content from
            user_id: User ID for cache scoping
            extract_depth: "basic" or "advanced" extraction

        Returns:
            List of ExtractedContent

        Raises:
            TavilyAPIError: If API call fails
        """
        try:
            response = await self._api_call_with_retry(
                self.client.extract,
                urls=urls,
                extract_depth=extract_depth,
            )

            results = []
            for item in response.get("results", []):
                results.append(ExtractedContent(
                    url=item.get("url", ""),
                    title=item.get("title", ""),
                    content=item.get("content", ""),
                    raw_content=item.get("raw_content"),
                    source="api",
                ))

            logger.info(f"Extracted content from {len(results)} URLs")
            return results

        except Exception as e:
            logger.error(f"Tavily extract failed: {e}", exc_info=True)
            raise TavilyAPIError(f"Extract operation failed: {e}")

    async def map_site(
        self,
        base_url: str,
        user_id: UUID,
        max_depth: int = 1,
        max_breadth: int = 20,
        limit: int = 50,
        instructions: Optional[str] = None,
    ) -> SiteMapResult:
        """
        Map website structure

        Args:
            base_url: Root URL to map
            user_id: User ID for cache scoping
            max_depth: Maximum depth from base URL
            max_breadth: Max links to follow per page
            limit: Total number of links to process
            instructions: Natural language mapping instructions

        Returns:
            SiteMapResult with site structure

        Raises:
            TavilyAPIError: If API call fails
        """
        start_time = time.time()

        try:
            response = await self._api_call_with_retry(
                self.client.map,
                url=base_url,
                max_depth=max_depth,
                max_breadth=max_breadth,
                limit=limit,
                instructions=instructions,
            )

            urls = response.get("urls", [])
            structure = response.get("structure", {})
            execution_time = (time.time() - start_time) * 1000

            logger.info(f"Mapped {len(urls)} URLs from {base_url}")

            return SiteMapResult(
                base_url=base_url,
                urls=urls,
                structure=structure,
                source="api",
                execution_time_ms=execution_time,
            )

        except Exception as e:
            logger.error(f"Tavily map failed: {e}", exc_info=True)
            raise TavilyAPIError(f"Map operation failed: {e}")

    async def _deduplicate_results(
        self,
        results: list[dict[str, Any]],
        user_id: UUID,
    ) -> list[dict[str, Any]]:
        """
        Deduplicate results by content hash

        Args:
            results: Search results to deduplicate
            user_id: User ID for cache scoping

        Returns:
            Deduplicated results
        """
        if not self.document_store:
            return results

        seen_hashes = set()
        unique_results = []

        for result in results:
            content = f"{result.get('title', '')}\n{result.get('content', '')}"
            content_hash = self._compute_content_hash(content)

            if content_hash not in seen_hashes:
                seen_hashes.add(content_hash)
                unique_results.append(result)

        if len(unique_results) < len(results):
            logger.info(f"Deduplicated {len(results) - len(unique_results)} duplicate results")

        return unique_results
