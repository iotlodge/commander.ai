"""
PromptEngineer - Dynamic Prompt Generation Service

Generates optimized, agent-specific prompts based on:
- Agent context (role, capabilities, tools)
- Task requirements (complexity, output format, urgency)
- User preferences (tone, detail level)
- Historical performance (which prompts work best)

Architecture:
1. Pre-compilation: Load and compile prompts at agent startup
2. Caching: Store compiled prompts in memory for fast retrieval
3. Dynamic adaptation: Adapt cached prompts to specific task context at runtime
"""

import logging
import hashlib
from datetime import datetime
from typing import Any
from uuid import UUID

from backend.repositories.prompt_repository import PromptRepository
from backend.models.prompt_models import AgentPrompt

logger = logging.getLogger(__name__)


class PromptEngineerError(Exception):
    """Base exception for PromptEngineer errors"""
    pass


class PromptNotFoundError(PromptEngineerError):
    """Raised when a required prompt is not found"""
    pass


class PromptCompilationError(PromptEngineerError):
    """Raised when prompt compilation fails"""
    pass


class PromptEngineer:
    """
    Dynamic prompt generation service for Commander.ai agents

    Features:
    - Pre-compiles prompts with agent config at startup
    - Caches compiled prompts for fast retrieval
    - Adapts prompts to task context at runtime
    - Supports template variables and substitution
    - Tracks prompt versions for A/B testing
    """

    def __init__(self, prompt_repo: PromptRepository):
        """
        Initialize PromptEngineer

        Args:
            prompt_repo: Repository for accessing prompt database
        """
        self.prompt_repo = prompt_repo
        self.compiled_cache: dict[str, dict[str, str]] = {}
        self._compilation_timestamps: dict[str, datetime] = {}

    async def compile_agent_prompts(
        self,
        agent_id: str,
        agent_config: dict[str, Any]
    ) -> dict[str, str]:
        """
        Pre-compile prompts for an agent based on its configuration
        Called at agent startup or when config changes

        Args:
            agent_id: Agent identifier (e.g., "agent_a", "parent")
            agent_config: Agent configuration including:
                - tools: List of available tools
                - specialization: Agent's role description
                - capabilities: List of agent capabilities
                - output_formats: Supported output formats

        Returns:
            Dictionary with compiled prompts:
            {
                "system": "Compiled system prompt text",
                "human_template": "Template for user prompts with {variables}"
            }

        Raises:
            PromptNotFoundError: If no active prompts found for agent
            PromptCompilationError: If compilation fails
        """
        logger.info(f"Compiling prompts for agent: {agent_id}")

        try:
            # Load active prompts from database
            prompts = await self.prompt_repo.get_active_prompts(agent_id)

            if not prompts:
                logger.warning(f"No active prompts found for agent {agent_id}. Using fallback.")
                # Return empty compiled dict - agent will use hardcoded prompts
                return {}

            # Compile prompts by type
            compiled = {}

            for prompt in prompts:
                if prompt.prompt_type == "system":
                    compiled["system"] = self._compile_system_prompt(
                        base_text=prompt.prompt_text,
                        agent_config=agent_config,
                        variables=prompt.variables
                    )
                elif prompt.prompt_type == "human":
                    # Human prompts are templates, store as-is
                    compiled["human_template"] = prompt.prompt_text

            # Cache compiled prompts
            self.compiled_cache[agent_id] = compiled
            self._compilation_timestamps[agent_id] = datetime.utcnow()

            logger.info(
                f"Successfully compiled {len(compiled)} prompt(s) for {agent_id}: "
                f"{list(compiled.keys())}"
            )

            return compiled

        except Exception as e:
            logger.error(f"Failed to compile prompts for {agent_id}: {e}", exc_info=True)
            raise PromptCompilationError(f"Compilation failed for {agent_id}: {e}") from e

    async def generate_dynamic_prompt(
        self,
        agent_id: str,
        task_context: dict[str, Any],
        user_query: str
    ) -> tuple[str, str]:
        """
        Generate task-specific prompts at runtime
        Uses cached compiled prompts + task context for adaptation

        Args:
            agent_id: Agent identifier
            task_context: Task-specific context:
                - task_type: Type of task (e.g., "research", "compliance")
                - complexity: Task complexity ("simple", "moderate", "complex")
                - urgency: Task urgency ("low", "normal", "high")
                - token_budget: Optional max tokens for response
                - detail_level: Detail level ("brief", "standard", "comprehensive")
            user_query: User's original query

        Returns:
            Tuple of (system_prompt, user_prompt) ready for LLM

        Raises:
            PromptNotFoundError: If agent prompts not compiled
        """
        # Check if prompts are compiled
        if agent_id not in self.compiled_cache:
            logger.warning(
                f"Prompts not compiled for {agent_id}. "
                f"Call compile_agent_prompts() first or agent will use fallback."
            )
            # Return simple fallback prompts
            return self._generate_fallback_prompts(agent_id, user_query)

        compiled = self.compiled_cache[agent_id]

        # Adapt system prompt for task context
        system_prompt = self._adapt_system_prompt(
            base_system=compiled.get("system", ""),
            task_context=task_context
        )

        # Build user prompt from template
        user_prompt = self._build_user_prompt(
            template=compiled.get("human_template", ""),
            user_query=user_query,
            task_context=task_context
        )

        return system_prompt, user_prompt

    def _compile_system_prompt(
        self,
        base_text: str,
        agent_config: dict[str, Any],
        variables: dict[str, Any]
    ) -> str:
        """
        Compile base system prompt with agent configuration

        Args:
            base_text: Base prompt text from database
            agent_config: Agent configuration
            variables: Template variables from prompt

        Returns:
            Compiled system prompt
        """
        prompt = base_text

        # Replace agent tools list
        if "tools" in agent_config and "{tools_list}" in prompt:
            tools_list = self._format_tools_list(agent_config["tools"])
            prompt = prompt.replace("{tools_list}", tools_list)

        # Replace agent specialization
        if "specialization" in agent_config and "{specialization}" in prompt:
            prompt = prompt.replace("{specialization}", agent_config["specialization"])

        # Replace agent capabilities
        if "capabilities" in agent_config and "{capabilities}" in prompt:
            capabilities_text = ", ".join(agent_config["capabilities"])
            prompt = prompt.replace("{capabilities}", capabilities_text)

        # Replace custom variables
        for key, value in variables.items():
            placeholder = f"{{{key}}}"
            if placeholder in prompt:
                prompt = prompt.replace(placeholder, str(value))

        return prompt

    def _adapt_system_prompt(
        self,
        base_system: str,
        task_context: dict[str, Any]
    ) -> str:
        """
        Adapt compiled system prompt for specific task context

        Args:
            base_system: Compiled base system prompt
            task_context: Task-specific context

        Returns:
            Adapted system prompt
        """
        if not base_system:
            return ""

        adapted = base_system

        # Add urgency guidance
        if task_context.get("urgency") == "high":
            adapted += "\n\nIMPORTANT: This is a high-priority task. Prioritize speed and clarity."

        # Add token budget constraint
        if "token_budget" in task_context:
            adapted += f"\n\nToken budget: {task_context['token_budget']} tokens. Be concise."

        # Add complexity guidance
        if task_context.get("complexity") == "complex":
            adapted += "\n\nNote: This is a complex task. Break it down into clear steps and be thorough."

        # Add detail level guidance
        detail_level = task_context.get("detail_level", "standard")
        if detail_level == "brief":
            adapted += "\n\nProvide a brief, concise response. Focus on key points only."
        elif detail_level == "comprehensive":
            adapted += "\n\nProvide a comprehensive, detailed response. Cover all relevant aspects."

        return adapted

    def _build_user_prompt(
        self,
        template: str,
        user_query: str,
        task_context: dict[str, Any]
    ) -> str:
        """
        Build HumanMessage from template + context

        Args:
            template: User prompt template (may have {variables})
            user_query: User's original query
            task_context: Task context for variable substitution

        Returns:
            Compiled user prompt
        """
        if not template:
            # Fallback: simple query pass-through
            return user_query

        # Replace query variable
        prompt = template.replace("{query}", user_query)

        # Replace task context variables
        for key, value in task_context.items():
            placeholder = f"{{{key}}}"
            if placeholder in prompt:
                prompt = prompt.replace(placeholder, str(value))

        return prompt

    def _format_tools_list(self, tools: list[dict[str, str]]) -> str:
        """
        Format tools list for inclusion in system prompt

        Args:
            tools: List of tool dicts with 'name' and 'description'

        Returns:
            Formatted tools list string
        """
        if not tools:
            return "No tools available"

        lines = []
        for tool in tools:
            name = tool.get("name", "unknown")
            description = tool.get("description", "No description")
            lines.append(f"- {name}: {description}")

        return "\n".join(lines)

    def _generate_fallback_prompts(
        self,
        agent_id: str,
        user_query: str
    ) -> tuple[str, str]:
        """
        Generate simple fallback prompts when no compiled prompts available

        Args:
            agent_id: Agent identifier
            user_query: User's query

        Returns:
            Tuple of (system_prompt, user_prompt)
        """
        system_prompt = f"""You are an AI assistant for Commander.ai.
Agent ID: {agent_id}

Please help the user with their request to the best of your ability."""

        user_prompt = user_query

        return system_prompt, user_prompt

    def get_cache_status(self) -> dict[str, Any]:
        """
        Get current cache status for monitoring/debugging

        Returns:
            Dictionary with cache statistics
        """
        return {
            "cached_agents": list(self.compiled_cache.keys()),
            "cache_size": len(self.compiled_cache),
            "compilation_timestamps": {
                agent_id: ts.isoformat()
                for agent_id, ts in self._compilation_timestamps.items()
            }
        }

    def clear_cache(self, agent_id: str | None = None) -> None:
        """
        Clear cached prompts

        Args:
            agent_id: Optional agent ID to clear specific cache.
                     If None, clears all caches.
        """
        if agent_id:
            if agent_id in self.compiled_cache:
                del self.compiled_cache[agent_id]
                del self._compilation_timestamps[agent_id]
                logger.info(f"Cleared cache for agent: {agent_id}")
        else:
            self.compiled_cache.clear()
            self._compilation_timestamps.clear()
            logger.info("Cleared all prompt caches")

    def generate_prompt_version_hash(self, prompt_text: str) -> str:
        """
        Generate version hash for prompt (useful for A/B testing)

        Args:
            prompt_text: Prompt text to hash

        Returns:
            SHA256 hash (first 16 chars) for version tracking
        """
        hash_obj = hashlib.sha256(prompt_text.encode())
        return hash_obj.hexdigest()[:16]


# Singleton instance (will be initialized by dependency injection)
_prompt_engineer_instance: PromptEngineer | None = None


def get_prompt_engineer() -> PromptEngineer:
    """
    Get singleton PromptEngineer instance

    Returns:
        PromptEngineer instance

    Raises:
        RuntimeError: If PromptEngineer not initialized
    """
    if _prompt_engineer_instance is None:
        raise RuntimeError(
            "PromptEngineer not initialized. "
            "Call initialize_prompt_engineer() first."
        )
    return _prompt_engineer_instance


def initialize_prompt_engineer(prompt_repo: PromptRepository) -> PromptEngineer:
    """
    Initialize singleton PromptEngineer instance

    Args:
        prompt_repo: Prompt repository for database access

    Returns:
        Initialized PromptEngineer instance
    """
    global _prompt_engineer_instance
    _prompt_engineer_instance = PromptEngineer(prompt_repo)
    logger.info("PromptEngineer initialized")
    return _prompt_engineer_instance
