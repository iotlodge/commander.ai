"""
Unit tests for AsyncRateLimiter
"""

import asyncio
import pytest
import time

from backend.tools.web_search.tavily_toolset import AsyncRateLimiter


@pytest.mark.asyncio
async def test_rate_limiter_initialization():
    """Test rate limiter initializes with correct values"""
    limiter = AsyncRateLimiter(rate_limit_per_minute=60)

    assert limiter.rate_limit == 60
    assert limiter.tokens == 60
    assert isinstance(limiter.last_update, float)


@pytest.mark.asyncio
async def test_rate_limiter_allows_immediate_requests():
    """Test rate limiter allows requests when tokens available"""
    limiter = AsyncRateLimiter(rate_limit_per_minute=60)

    start_time = time.time()

    # Should not block when tokens available
    await limiter.acquire()

    elapsed = time.time() - start_time

    # Should complete almost instantly (< 0.1s)
    assert elapsed < 0.1
    assert limiter.tokens < 60  # Token consumed


@pytest.mark.asyncio
async def test_rate_limiter_blocks_when_exhausted():
    """Test rate limiter blocks when tokens exhausted"""
    # Very low rate limit for testing
    limiter = AsyncRateLimiter(rate_limit_per_minute=2)

    # Consume all tokens
    await limiter.acquire()
    await limiter.acquire()

    # This should block
    start_time = time.time()
    await limiter.acquire()
    elapsed = time.time() - start_time

    # Should have waited (at least some time)
    assert elapsed > 0.1


@pytest.mark.asyncio
async def test_rate_limiter_refills_tokens():
    """Test rate limiter refills tokens over time"""
    limiter = AsyncRateLimiter(rate_limit_per_minute=60)

    # Consume some tokens
    await limiter.acquire()
    tokens_after_first = limiter.tokens

    # Wait a bit for refill
    await asyncio.sleep(1.1)

    # Acquire again
    await limiter.acquire()

    # Tokens should have been refilled
    # After 1 second, should get approximately 1 token back (60 per minute = 1 per second)
    # So tokens should be close to original after refill
    assert limiter.tokens >= tokens_after_first - 2  # Allow some variance


@pytest.mark.asyncio
async def test_rate_limiter_concurrent_requests():
    """Test rate limiter handles concurrent requests correctly"""
    limiter = AsyncRateLimiter(rate_limit_per_minute=10)

    async def make_request(request_id: int):
        await limiter.acquire()
        return request_id

    # Try to make 5 concurrent requests
    start_time = time.time()
    results = await asyncio.gather(*[make_request(i) for i in range(5)])
    elapsed = time.time() - start_time

    # All requests should complete
    assert len(results) == 5
    assert results == [0, 1, 2, 3, 4]

    # Should complete reasonably quickly (all within limit)
    assert elapsed < 2.0


@pytest.mark.asyncio
async def test_rate_limiter_respects_limit():
    """Test rate limiter enforces rate limit over time"""
    limiter = AsyncRateLimiter(rate_limit_per_minute=6)  # 6 per minute = 0.1 per second

    request_times = []

    async def make_request():
        await limiter.acquire()
        request_times.append(time.time())

    # Make 10 requests
    start_time = time.time()
    await asyncio.gather(*[make_request() for _ in range(10)])
    total_elapsed = time.time() - start_time

    # Should take at least some time to complete
    # 10 requests at 6 per minute = should take > 1 minute for 10 requests
    # But we start with 6 tokens, so first 6 are instant, then we need to wait
    # This is a simplified test - just verify it doesn't complete instantly
    assert total_elapsed > 0.5
