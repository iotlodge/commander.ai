"""
Token Usage Tracking
Tracks LLM calls, tool calls, agent calls, and token consumption for cost monitoring
"""

from typing import Any
from dataclasses import dataclass, field, asdict


@dataclass
class TokenUsage:
    """Tracks token usage for a single LLM call"""
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0

    def __add__(self, other: "TokenUsage") -> "TokenUsage":
        """Add two TokenUsage objects together"""
        return TokenUsage(
            prompt_tokens=self.prompt_tokens + other.prompt_tokens,
            completion_tokens=self.completion_tokens + other.completion_tokens,
            total_tokens=self.total_tokens + other.total_tokens,
        )


@dataclass
class ExecutionMetrics:
    """Tracks execution metrics for an agent or task"""
    llm_calls: int = 0
    tool_calls: int = 0
    agent_calls: int = 0
    token_usage: TokenUsage = field(default_factory=TokenUsage)

    # Detailed breakdown
    llm_call_details: list[dict[str, Any]] = field(default_factory=list)
    tool_call_details: list[dict[str, Any]] = field(default_factory=list)
    agent_call_details: list[dict[str, Any]] = field(default_factory=list)

    def add_llm_call(
        self,
        model: str,
        prompt_tokens: int,
        completion_tokens: int,
        purpose: str | None = None
    ) -> None:
        """Record an LLM call"""
        self.llm_calls += 1
        usage = TokenUsage(
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=prompt_tokens + completion_tokens
        )
        self.token_usage = self.token_usage + usage

        self.llm_call_details.append({
            "model": model,
            "purpose": purpose,
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "total_tokens": prompt_tokens + completion_tokens,
        })

    def add_tool_call(self, tool_name: str, success: bool = True) -> None:
        """Record a tool call"""
        self.tool_calls += 1
        self.tool_call_details.append({
            "tool": tool_name,
            "success": success,
        })

    def add_agent_call(
        self,
        agent_id: str,
        agent_nickname: str,
        success: bool = True,
        child_metrics: "ExecutionMetrics | None" = None
    ) -> None:
        """Record an agent call and merge child metrics"""
        self.agent_calls += 1
        self.agent_call_details.append({
            "agent_id": agent_id,
            "agent_nickname": agent_nickname,
            "success": success,
        })

        # Merge child agent metrics into parent
        if child_metrics:
            self.llm_calls += child_metrics.llm_calls
            self.tool_calls += child_metrics.tool_calls
            self.agent_calls += child_metrics.agent_calls
            self.token_usage = self.token_usage + child_metrics.token_usage

            # Merge detailed lists
            self.llm_call_details.extend(child_metrics.llm_call_details)
            self.tool_call_details.extend(child_metrics.tool_call_details)
            self.agent_call_details.extend(child_metrics.agent_call_details)

    def to_dict(self, include_details: bool = False) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        result = {
            "llm_calls": self.llm_calls,
            "tool_calls": self.tool_calls,
            "agent_calls": self.agent_calls,
            "tokens": {
                "prompt": self.token_usage.prompt_tokens,
                "completion": self.token_usage.completion_tokens,
                "total": self.token_usage.total_tokens,
            }
        }

        if include_details:
            result["details"] = {
                "llm_calls": self.llm_call_details,
                "tool_calls": self.tool_call_details,
                "agent_calls": self.agent_call_details,
            }

        return result

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ExecutionMetrics":
        """Create from dictionary"""
        metrics = cls()
        metrics.llm_calls = data.get("llm_calls", 0)
        metrics.tool_calls = data.get("tool_calls", 0)
        metrics.agent_calls = data.get("agent_calls", 0)

        tokens = data.get("tokens", {})
        metrics.token_usage = TokenUsage(
            prompt_tokens=tokens.get("prompt", 0),
            completion_tokens=tokens.get("completion", 0),
            total_tokens=tokens.get("total", 0),
        )

        details = data.get("details", {})
        metrics.llm_call_details = details.get("llm_calls", [])
        metrics.tool_call_details = details.get("tool_calls", [])
        metrics.agent_call_details = details.get("agent_calls", [])

        return metrics


def extract_token_usage_from_response(response: Any) -> tuple[int, int]:
    """
    Extract token usage from LangChain/OpenAI/Anthropic response

    Returns:
        tuple[prompt_tokens, completion_tokens]
    """
    try:
        # LangChain response with response_metadata
        if hasattr(response, "response_metadata"):
            metadata = response.response_metadata

            # OpenAI format
            usage = metadata.get("token_usage", {})
            if usage:
                return (
                    usage.get("prompt_tokens", 0),
                    usage.get("completion_tokens", 0)
                )

            # Anthropic format (in response_metadata.usage)
            usage = metadata.get("usage", {})
            if usage:
                return (
                    usage.get("input_tokens", 0),
                    usage.get("output_tokens", 0)
                )

        # Direct API response with usage attribute
        if hasattr(response, "usage"):
            usage = response.usage

            # OpenAI format
            if hasattr(usage, "prompt_tokens"):
                return (
                    usage.prompt_tokens,
                    usage.completion_tokens
                )

            # Anthropic format
            if hasattr(usage, "input_tokens"):
                return (
                    usage.input_tokens,
                    usage.output_tokens
                )

        # Fallback
        return (0, 0)

    except Exception:
        return (0, 0)
