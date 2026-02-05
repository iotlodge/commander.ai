"""
Exceptions for Tavily web search operations
"""


class TavilyError(Exception):
    """Base exception for all Tavily-related errors"""
    pass


class TavilyAPIError(TavilyError):
    """Raised when Tavily API call fails"""
    pass


class TavilyCacheError(TavilyError):
    """Raised when cache operations fail"""
    pass


class TavilyRateLimitError(TavilyError):
    """Raised when rate limit is exceeded"""
    pass


class TavilyTimeoutError(TavilyError):
    """Raised when Tavily API request times out"""
    pass


class TavilyConfigError(TavilyError):
    """Raised when Tavily configuration is invalid"""
    pass
