"""
LLM Factory for creating provider-agnostic LLM instances
Supports OpenAI, Anthropic, and future providers
"""

from dataclasses import dataclass
from typing import Any

from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic

from backend.core.config import get_settings

settings = get_settings()


@dataclass
class ModelConfig:
    """Configuration for an LLM model"""

    provider: str  # 'openai', 'anthropic', 'huggingface'
    model_name: str
    temperature: float = 0.7
    max_tokens: int = 2000
    model_params: dict[str, Any] | None = None

    def __post_init__(self):
        if self.model_params is None:
            self.model_params = {}


# Default model configurations for all 8 agents
# These are used as fallbacks if no database config exists
DEFAULT_CONFIGS = {
    "parent": ModelConfig(
        provider="openai",
        model_name="gpt-4o-mini",
        temperature=0.7,
        max_tokens=2000,
    ),
    "agent_a": ModelConfig(
        provider="openai",
        model_name="gpt-4o-mini",
        temperature=0.7,
        max_tokens=2000,
    ),
    "agent_b": ModelConfig(
        provider="openai",
        model_name="gpt-4o-mini",
        temperature=0.7,
        max_tokens=2000,
    ),
    "agent_c": ModelConfig(
        provider="openai",
        model_name="gpt-4o-mini",
        temperature=0.7,
        max_tokens=2000,
    ),
    "agent_d": ModelConfig(
        provider="openai",
        model_name="gpt-4o-mini",
        temperature=0.7,
        max_tokens=2000,
    ),
    "agent_e": ModelConfig(
        provider="openai",
        model_name="gpt-4o-mini",
        temperature=0.7,
        max_tokens=2000,
    ),
    "agent_f": ModelConfig(
        provider="openai",
        model_name="gpt-4o-mini",
        temperature=0.7,
        max_tokens=2000,
    ),
    "agent_g": ModelConfig(
        provider="openai",
        model_name="gpt-4o-mini",
        temperature=0.7,
        max_tokens=2000,
    ),
}


def create_llm(
    config: ModelConfig,
    temperature: float | None = None,
    max_tokens: int | None = None,
    streaming: bool = False,
    **kwargs
) -> ChatOpenAI | ChatAnthropic:
    """
    Create an LLM instance based on the provided configuration.

    Args:
        config: ModelConfig specifying provider and model details
        temperature: Override config temperature (optional)
        max_tokens: Override config max_tokens (optional)
        streaming: Enable streaming responses
        **kwargs: Additional provider-specific parameters

    Returns:
        LLM instance (ChatOpenAI or ChatAnthropic)

    Raises:
        ValueError: If provider is unsupported
    """
    effective_temperature = temperature if temperature is not None else config.temperature
    effective_max_tokens = max_tokens if max_tokens is not None else config.max_tokens

    # Merge config params with kwargs (kwargs take precedence)
    merged_params = {**(config.model_params or {}), **kwargs}

    if config.provider == "openai":
        return ChatOpenAI(
            model=config.model_name,
            temperature=effective_temperature,
            max_tokens=effective_max_tokens,
            api_key=settings.openai_api_key,
            streaming=streaming,
            **merged_params
        )

    elif config.provider == "anthropic":
        return ChatAnthropic(
            model=config.model_name,
            temperature=effective_temperature,
            max_tokens=effective_max_tokens,
            anthropic_api_key=settings.anthropic_api_key,
            streaming=streaming,
            **merged_params
        )

    elif config.provider == "huggingface":
        # Future implementation for HuggingFace models
        raise NotImplementedError("HuggingFace provider is not yet implemented")

    else:
        raise ValueError(f"Unsupported LLM provider: {config.provider}")


def get_default_config(agent_id: str) -> ModelConfig:
    """
    Get the default model configuration for an agent.

    Args:
        agent_id: Agent identifier (e.g., 'agent_a', 'parent')

    Returns:
        Default ModelConfig for the agent

    Raises:
        ValueError: If agent_id is not recognized
    """
    if agent_id not in DEFAULT_CONFIGS:
        raise ValueError(f"Unknown agent_id: {agent_id}")

    return DEFAULT_CONFIGS[agent_id]
