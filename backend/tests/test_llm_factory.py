"""
Unit tests for LLM Factory
Tests model configuration and LLM instantiation
"""

import pytest
from unittest.mock import patch, MagicMock

from backend.core.llm_factory import (
    ModelConfig,
    create_llm,
    get_default_config,
    DEFAULT_CONFIGS,
)


class TestModelConfig:
    """Tests for ModelConfig dataclass"""

    def test_create_with_all_params(self):
        """Should create ModelConfig with all parameters"""
        config = ModelConfig(
            provider="openai",
            model_name="gpt-4o-mini",
            temperature=0.7,
            max_tokens=2000,
            model_params={"top_p": 0.9},
        )

        assert config.provider == "openai"
        assert config.model_name == "gpt-4o-mini"
        assert config.temperature == 0.7
        assert config.max_tokens == 2000
        assert config.model_params == {"top_p": 0.9}

    def test_create_with_defaults(self):
        """Should use default values for optional parameters"""
        config = ModelConfig(
            provider="anthropic",
            model_name="claude-3-5-sonnet-20241022",
        )

        assert config.temperature == 0.7
        assert config.max_tokens == 2000
        assert config.model_params == {}

    def test_model_params_defaults_to_empty_dict(self):
        """Should initialize model_params as empty dict if None"""
        config = ModelConfig(
            provider="openai",
            model_name="gpt-4o-mini",
            model_params=None,
        )

        assert config.model_params == {}


class TestDefaultConfigs:
    """Tests for DEFAULT_CONFIGS dictionary"""

    def test_all_agents_have_default_configs(self):
        """Should have default configs for all 8 agents"""
        expected_agents = [
            "parent",
            "agent_a",
            "agent_b",
            "agent_c",
            "agent_d",
            "agent_e",
            "agent_f",
            "agent_g",
        ]

        for agent_id in expected_agents:
            assert agent_id in DEFAULT_CONFIGS, f"Missing config for {agent_id}"

    def test_default_configs_are_valid(self):
        """Should have valid ModelConfig objects for all agents"""
        for agent_id, config in DEFAULT_CONFIGS.items():
            assert isinstance(config, ModelConfig)
            assert config.provider in ["openai", "anthropic"]
            assert config.model_name
            assert 0 <= config.temperature <= 1
            assert config.max_tokens > 0

    def test_default_configs_use_gpt_4o_mini(self):
        """All default configs should use gpt-4o-mini (MVP default)"""
        for agent_id, config in DEFAULT_CONFIGS.items():
            assert config.provider == "openai"
            assert config.model_name == "gpt-4o-mini"


class TestGetDefaultConfig:
    """Tests for get_default_config function"""

    def test_get_valid_agent_config(self):
        """Should return config for valid agent_id"""
        config = get_default_config("agent_a")

        assert isinstance(config, ModelConfig)
        assert config.provider == "openai"
        assert config.model_name == "gpt-4o-mini"

    def test_get_parent_config(self):
        """Should return config for parent agent"""
        config = get_default_config("parent")

        assert isinstance(config, ModelConfig)
        assert config.provider == "openai"

    def test_invalid_agent_raises_error(self):
        """Should raise ValueError for invalid agent_id"""
        with pytest.raises(ValueError, match="Unknown agent_id"):
            get_default_config("invalid_agent")


class TestCreateLLM:
    """Tests for create_llm function"""

    @patch("backend.core.llm_factory.ChatOpenAI")
    def test_create_openai_llm(self, mock_chat_openai):
        """Should create ChatOpenAI instance for OpenAI provider"""
        config = ModelConfig(
            provider="openai",
            model_name="gpt-4o-mini",
            temperature=0.7,
            max_tokens=2000,
        )

        llm = create_llm(config)

        mock_chat_openai.assert_called_once()
        call_kwargs = mock_chat_openai.call_args[1]

        assert call_kwargs["model"] == "gpt-4o-mini"
        assert call_kwargs["temperature"] == 0.7
        assert call_kwargs["max_tokens"] == 2000
        assert "api_key" in call_kwargs

    @patch("backend.core.llm_factory.ChatAnthropic")
    def test_create_anthropic_llm(self, mock_chat_anthropic):
        """Should create ChatAnthropic instance for Anthropic provider"""
        config = ModelConfig(
            provider="anthropic",
            model_name="claude-3-5-sonnet-20241022",
            temperature=0.5,
            max_tokens=3000,
        )

        llm = create_llm(config)

        mock_chat_anthropic.assert_called_once()
        call_kwargs = mock_chat_anthropic.call_args[1]

        assert call_kwargs["model"] == "claude-3-5-sonnet-20241022"
        assert call_kwargs["temperature"] == 0.5
        assert call_kwargs["max_tokens"] == 3000
        assert "anthropic_api_key" in call_kwargs

    @patch("backend.core.llm_factory.ChatOpenAI")
    def test_override_temperature(self, mock_chat_openai):
        """Should override config temperature when provided"""
        config = ModelConfig(
            provider="openai",
            model_name="gpt-4o-mini",
            temperature=0.7,
        )

        llm = create_llm(config, temperature=0.3)

        call_kwargs = mock_chat_openai.call_args[1]
        assert call_kwargs["temperature"] == 0.3

    @patch("backend.core.llm_factory.ChatOpenAI")
    def test_override_max_tokens(self, mock_chat_openai):
        """Should override config max_tokens when provided"""
        config = ModelConfig(
            provider="openai",
            model_name="gpt-4o-mini",
            max_tokens=2000,
        )

        llm = create_llm(config, max_tokens=4000)

        call_kwargs = mock_chat_openai.call_args[1]
        assert call_kwargs["max_tokens"] == 4000

    @patch("backend.core.llm_factory.ChatOpenAI")
    def test_streaming_parameter(self, mock_chat_openai):
        """Should pass streaming parameter"""
        config = ModelConfig(provider="openai", model_name="gpt-4o-mini")

        llm = create_llm(config, streaming=True)

        call_kwargs = mock_chat_openai.call_args[1]
        assert call_kwargs["streaming"] is True

    @patch("backend.core.llm_factory.ChatAnthropic")
    def test_merge_model_params_with_kwargs(self, mock_chat_anthropic):
        """Should merge model_params with kwargs, kwargs take precedence"""
        config = ModelConfig(
            provider="anthropic",
            model_name="claude-3-5-sonnet-20241022",
            model_params={"top_p": 0.9, "top_k": 40},
        )

        llm = create_llm(config, top_p=0.95)

        call_kwargs = mock_chat_anthropic.call_args[1]
        assert call_kwargs["top_p"] == 0.95  # kwargs override
        assert call_kwargs["top_k"] == 40  # from model_params

    def test_huggingface_not_implemented(self):
        """Should raise NotImplementedError for HuggingFace provider"""
        config = ModelConfig(
            provider="huggingface",
            model_name="meta-llama/Llama-2-7b",
        )

        with pytest.raises(NotImplementedError, match="HuggingFace provider"):
            create_llm(config)

    def test_unsupported_provider_raises_error(self):
        """Should raise ValueError for unsupported provider"""
        config = ModelConfig(
            provider="unknown",
            model_name="some-model",
        )

        with pytest.raises(ValueError, match="Unsupported LLM provider"):
            create_llm(config)


class TestIntegrationScenarios:
    """Integration tests for common usage patterns"""

    @patch("backend.core.llm_factory.ChatOpenAI")
    def test_agent_using_default_config(self, mock_chat_openai):
        """Simulate agent using default config"""
        agent_id = "agent_a"
        config = get_default_config(agent_id)
        llm = create_llm(config)

        mock_chat_openai.assert_called_once()
        call_kwargs = mock_chat_openai.call_args[1]
        assert call_kwargs["model"] == "gpt-4o-mini"

    @patch("backend.core.llm_factory.ChatAnthropic")
    def test_agent_switching_to_claude(self, mock_chat_anthropic):
        """Simulate agent switching from OpenAI to Anthropic"""
        # Start with default
        old_config = get_default_config("agent_a")
        assert old_config.provider == "openai"

        # Switch to Claude
        new_config = ModelConfig(
            provider="anthropic",
            model_name="claude-3-5-sonnet-20241022",
            temperature=0.7,
            max_tokens=2000,
        )

        llm = create_llm(new_config)

        mock_chat_anthropic.assert_called_once()
        call_kwargs = mock_chat_anthropic.call_args[1]
        assert call_kwargs["model"] == "claude-3-5-sonnet-20241022"
