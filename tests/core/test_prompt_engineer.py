"""
Unit tests for PromptEngineer
"""

import pytest
from datetime import datetime
from uuid import uuid4
from unittest.mock import AsyncMock, MagicMock

from backend.core.prompt_engineer import (
    PromptEngineer,
    PromptEngineerError,
    PromptNotFoundError,
    PromptCompilationError,
    initialize_prompt_engineer,
    get_prompt_engineer
)
from backend.models.prompt_models import AgentPrompt


@pytest.fixture
def mock_prompt_repo():
    """Mock PromptRepository"""
    return AsyncMock()


@pytest.fixture
def prompt_engineer(mock_prompt_repo):
    """PromptEngineer instance with mocked repository"""
    return PromptEngineer(mock_prompt_repo)


@pytest.fixture
def sample_system_prompt():
    """Sample system prompt from database"""
    return AgentPrompt(
        id=uuid4(),
        agent_id="agent_a",
        nickname="bob",
        description="Research synthesis system prompt",
        prompt_text="""You are {agent_nickname}, a {specialization} at Commander.ai.
Your role is to synthesize information from multiple sources.

Available tools:
{tools_list}

Guidelines:
- Provide well-structured analysis
- Cite key findings
- Use markdown formatting""",
        active=True,
        prompt_type="system",
        variables={"agent_nickname": "Bob"},
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )


@pytest.fixture
def sample_human_prompt():
    """Sample human prompt template from database"""
    return AgentPrompt(
        id=uuid4(),
        agent_id="agent_a",
        nickname="bob",
        description="Research query template",
        prompt_text="""Research query: {query}

Task type: {task_type}
Expected output: {expected_output}

Provide comprehensive research on the topic above.""",
        active=True,
        prompt_type="human",
        variables={},
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )


@pytest.fixture
def agent_config():
    """Sample agent configuration"""
    return {
        "tools": [
            {"name": "web_search", "description": "Search the web for current information"},
            {"name": "synthesize", "description": "Combine multiple sources"}
        ],
        "specialization": "Research Specialist",
        "capabilities": ["web_search", "synthesis", "analysis"],
        "output_formats": ["markdown", "json"]
    }


class TestPromptCompilation:
    """Test prompt compilation functionality"""

    @pytest.mark.asyncio
    async def test_compile_agent_prompts_success(
        self,
        prompt_engineer,
        mock_prompt_repo,
        sample_system_prompt,
        sample_human_prompt,
        agent_config
    ):
        """Test successful prompt compilation"""
        # Setup mock to return prompts
        mock_prompt_repo.get_active_prompts.return_value = [
            sample_system_prompt,
            sample_human_prompt
        ]

        # Compile prompts
        compiled = await prompt_engineer.compile_agent_prompts("agent_a", agent_config)

        # Verify repository was called
        mock_prompt_repo.get_active_prompts.assert_called_once_with("agent_a")

        # Verify compiled prompts exist
        assert "system" in compiled
        assert "human_template" in compiled

        # Verify system prompt has tools list injected
        assert "web_search" in compiled["system"]
        assert "Search the web" in compiled["system"]

        # Verify variables were replaced
        assert "Bob" in compiled["system"]
        assert "Research Specialist" in compiled["system"]

        # Verify human template is stored as-is
        assert "{query}" in compiled["human_template"]

    @pytest.mark.asyncio
    async def test_compile_agent_prompts_no_prompts_found(
        self,
        prompt_engineer,
        mock_prompt_repo,
        agent_config
    ):
        """Test compilation when no prompts found (returns empty dict)"""
        # Setup mock to return empty list
        mock_prompt_repo.get_active_prompts.return_value = []

        # Compile prompts
        compiled = await prompt_engineer.compile_agent_prompts("agent_a", agent_config)

        # Should return empty dict (agent will use hardcoded prompts)
        assert compiled == {}

    @pytest.mark.asyncio
    async def test_compile_agent_prompts_caching(
        self,
        prompt_engineer,
        mock_prompt_repo,
        sample_system_prompt,
        agent_config
    ):
        """Test that compiled prompts are cached"""
        mock_prompt_repo.get_active_prompts.return_value = [sample_system_prompt]

        # Compile prompts
        await prompt_engineer.compile_agent_prompts("agent_a", agent_config)

        # Verify cache was populated
        assert "agent_a" in prompt_engineer.compiled_cache
        assert "system" in prompt_engineer.compiled_cache["agent_a"]

        # Verify timestamp was recorded
        assert "agent_a" in prompt_engineer._compilation_timestamps

    @pytest.mark.asyncio
    async def test_compile_multiple_agents(
        self,
        prompt_engineer,
        mock_prompt_repo,
        sample_system_prompt,
        agent_config
    ):
        """Test compiling prompts for multiple agents"""
        mock_prompt_repo.get_active_prompts.return_value = [sample_system_prompt]

        # Compile for multiple agents
        await prompt_engineer.compile_agent_prompts("agent_a", agent_config)
        await prompt_engineer.compile_agent_prompts("agent_b", agent_config)

        # Verify both cached
        assert "agent_a" in prompt_engineer.compiled_cache
        assert "agent_b" in prompt_engineer.compiled_cache


class TestDynamicPromptGeneration:
    """Test dynamic prompt generation at runtime"""

    @pytest.mark.asyncio
    async def test_generate_dynamic_prompt_success(
        self,
        prompt_engineer,
        mock_prompt_repo,
        sample_system_prompt,
        sample_human_prompt,
        agent_config
    ):
        """Test generating dynamic prompts from cached compiled prompts"""
        # Setup: compile prompts first
        mock_prompt_repo.get_active_prompts.return_value = [
            sample_system_prompt,
            sample_human_prompt
        ]
        await prompt_engineer.compile_agent_prompts("agent_a", agent_config)

        # Generate dynamic prompt
        task_context = {
            "task_type": "research",
            "complexity": "moderate",
            "expected_output": "markdown",
            "detail_level": "comprehensive"
        }
        user_query = "Research quantum computing applications"

        system_prompt, user_prompt = await prompt_engineer.generate_dynamic_prompt(
            agent_id="agent_a",
            task_context=task_context,
            user_query=user_query
        )

        # Verify system prompt contains base content
        assert "Bob" in system_prompt
        assert "Research Specialist" in system_prompt

        # Verify system prompt has task-specific adaptations
        assert "comprehensive" in system_prompt

        # Verify user prompt has variables replaced
        assert "Research quantum computing applications" in user_prompt
        assert "research" in user_prompt
        assert "markdown" in user_prompt

    @pytest.mark.asyncio
    async def test_generate_dynamic_prompt_high_urgency(
        self,
        prompt_engineer,
        mock_prompt_repo,
        sample_system_prompt,
        agent_config
    ):
        """Test urgency adds guidance to system prompt"""
        mock_prompt_repo.get_active_prompts.return_value = [sample_system_prompt]
        await prompt_engineer.compile_agent_prompts("agent_a", agent_config)

        task_context = {"urgency": "high"}
        system_prompt, _ = await prompt_engineer.generate_dynamic_prompt(
            "agent_a", task_context, "Test query"
        )

        assert "high-priority" in system_prompt
        assert "speed and clarity" in system_prompt

    @pytest.mark.asyncio
    async def test_generate_dynamic_prompt_token_budget(
        self,
        prompt_engineer,
        mock_prompt_repo,
        sample_system_prompt,
        agent_config
    ):
        """Test token budget adds constraint to system prompt"""
        mock_prompt_repo.get_active_prompts.return_value = [sample_system_prompt]
        await prompt_engineer.compile_agent_prompts("agent_a", agent_config)

        task_context = {"token_budget": 500}
        system_prompt, _ = await prompt_engineer.generate_dynamic_prompt(
            "agent_a", task_context, "Test query"
        )

        assert "500 tokens" in system_prompt
        assert "concise" in system_prompt

    @pytest.mark.asyncio
    async def test_generate_dynamic_prompt_not_compiled(
        self,
        prompt_engineer
    ):
        """Test generating prompt when agent not compiled (uses fallback)"""
        system_prompt, user_prompt = await prompt_engineer.generate_dynamic_prompt(
            agent_id="agent_unknown",
            task_context={},
            user_query="Test query"
        )

        # Should return fallback prompts
        assert "AI assistant" in system_prompt
        assert "agent_unknown" in system_prompt
        assert user_prompt == "Test query"


class TestHelperMethods:
    """Test helper methods"""

    def test_format_tools_list(self, prompt_engineer):
        """Test tools list formatting"""
        tools = [
            {"name": "web_search", "description": "Search the web"},
            {"name": "calculator", "description": "Perform calculations"}
        ]

        formatted = prompt_engineer._format_tools_list(tools)

        assert "web_search" in formatted
        assert "Search the web" in formatted
        assert "calculator" in formatted
        assert "Perform calculations" in formatted

    def test_format_tools_list_empty(self, prompt_engineer):
        """Test formatting empty tools list"""
        formatted = prompt_engineer._format_tools_list([])
        assert formatted == "No tools available"

    def test_generate_prompt_version_hash(self, prompt_engineer):
        """Test prompt version hashing"""
        prompt1 = "You are a helpful assistant"
        prompt2 = "You are a helpful assistant"
        prompt3 = "You are a research specialist"

        hash1 = prompt_engineer.generate_prompt_version_hash(prompt1)
        hash2 = prompt_engineer.generate_prompt_version_hash(prompt2)
        hash3 = prompt_engineer.generate_prompt_version_hash(prompt3)

        # Same prompt = same hash
        assert hash1 == hash2

        # Different prompt = different hash
        assert hash1 != hash3

        # Hash is 16 characters
        assert len(hash1) == 16


class TestCacheManagement:
    """Test cache management functionality"""

    @pytest.mark.asyncio
    async def test_get_cache_status(
        self,
        prompt_engineer,
        mock_prompt_repo,
        sample_system_prompt,
        agent_config
    ):
        """Test getting cache status"""
        mock_prompt_repo.get_active_prompts.return_value = [sample_system_prompt]
        await prompt_engineer.compile_agent_prompts("agent_a", agent_config)
        await prompt_engineer.compile_agent_prompts("agent_b", agent_config)

        status = prompt_engineer.get_cache_status()

        assert "cached_agents" in status
        assert "agent_a" in status["cached_agents"]
        assert "agent_b" in status["cached_agents"]
        assert status["cache_size"] == 2

    @pytest.mark.asyncio
    async def test_clear_cache_specific_agent(
        self,
        prompt_engineer,
        mock_prompt_repo,
        sample_system_prompt,
        agent_config
    ):
        """Test clearing cache for specific agent"""
        mock_prompt_repo.get_active_prompts.return_value = [sample_system_prompt]
        await prompt_engineer.compile_agent_prompts("agent_a", agent_config)
        await prompt_engineer.compile_agent_prompts("agent_b", agent_config)

        # Clear specific agent
        prompt_engineer.clear_cache("agent_a")

        assert "agent_a" not in prompt_engineer.compiled_cache
        assert "agent_b" in prompt_engineer.compiled_cache

    @pytest.mark.asyncio
    async def test_clear_cache_all(
        self,
        prompt_engineer,
        mock_prompt_repo,
        sample_system_prompt,
        agent_config
    ):
        """Test clearing all caches"""
        mock_prompt_repo.get_active_prompts.return_value = [sample_system_prompt]
        await prompt_engineer.compile_agent_prompts("agent_a", agent_config)
        await prompt_engineer.compile_agent_prompts("agent_b", agent_config)

        # Clear all
        prompt_engineer.clear_cache()

        assert len(prompt_engineer.compiled_cache) == 0
        assert len(prompt_engineer._compilation_timestamps) == 0


class TestSingletonPattern:
    """Test singleton initialization and access"""

    def test_initialize_prompt_engineer(self, mock_prompt_repo):
        """Test initializing singleton"""
        from backend.core import prompt_engineer as pe_module

        # Clear any existing instance
        pe_module._prompt_engineer_instance = None

        # Initialize
        instance = initialize_prompt_engineer(mock_prompt_repo)

        assert instance is not None
        assert isinstance(instance, PromptEngineer)

    def test_get_prompt_engineer_success(self, mock_prompt_repo):
        """Test getting initialized singleton"""
        from backend.core import prompt_engineer as pe_module

        # Initialize first
        pe_module._prompt_engineer_instance = None
        initialize_prompt_engineer(mock_prompt_repo)

        # Get instance
        instance = get_prompt_engineer()

        assert instance is not None
        assert isinstance(instance, PromptEngineer)

    def test_get_prompt_engineer_not_initialized(self):
        """Test getting singleton before initialization raises error"""
        from backend.core import prompt_engineer as pe_module

        # Clear instance
        pe_module._prompt_engineer_instance = None

        # Should raise RuntimeError
        with pytest.raises(RuntimeError, match="not initialized"):
            get_prompt_engineer()
