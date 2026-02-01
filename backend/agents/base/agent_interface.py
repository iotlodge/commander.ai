"""
Base agent interface and memory-aware mixin
Provides core functionality for all agents in the system
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any
from uuid import UUID

from langgraph.graph import StateGraph
from pydantic import BaseModel

from backend.memory.memory_service import MemoryService, get_memory_service
from backend.memory.schemas import (
    ConversationContext,
    ConversationMessage,
    ConversationRole,
    MemoryType,
    MemorySearchResult,
)


@dataclass
class AgentMetadata:
    """Metadata describing an agent"""

    id: str  # e.g., 'agent_a', 'agent_b', 'parent'
    nickname: str  # e.g., 'bob', 'sue', 'leo'
    specialization: str  # e.g., 'Research Specialist'
    description: str
    avatar_url: str | None = None


class AgentExecutionContext(BaseModel):
    """Context passed to agent during execution"""

    user_id: UUID
    thread_id: UUID
    command: str
    conversation_context: ConversationContext | None = None
    task_callback: Any = None  # TaskProgressCallback | None (avoid circular import)
    metadata: dict[str, Any] = {}

    model_config = {"arbitrary_types_allowed": True}


class AgentExecutionResult(BaseModel):
    """Result of agent execution"""

    success: bool
    response: str
    final_state: dict[str, Any] = {}
    error: str | None = None
    metadata: dict[str, Any] = {}


class MemoryAwareMixin:
    """
    Mixin providing memory capabilities to agents
    Agents can save memories, retrieve context, and query other agents' knowledge
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.memory_service: MemoryService | None = None

    async def _ensure_memory_service(self) -> None:
        """Lazy-load memory service"""
        if not self.memory_service:
            self.memory_service = await get_memory_service()

    async def load_context(
        self,
        agent_id: str,
        user_id: UUID,
        thread_id: UUID,
        current_query: str,
    ) -> ConversationContext:
        """Load complete execution context including conversation and memories"""
        await self._ensure_memory_service()
        return await self.memory_service.get_agent_context(
            agent_id=agent_id,
            user_id=user_id,
            thread_id=thread_id,
            current_query=current_query,
        )

    async def save_message(
        self,
        user_id: UUID,
        agent_id: str,
        thread_id: UUID,
        role: ConversationRole,
        content: str,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """Save a conversation message"""
        await self._ensure_memory_service()
        message = ConversationMessage(
            user_id=user_id,
            agent_id=agent_id,
            thread_id=thread_id,
            role=role,
            content=content,
            metadata=metadata or {},
        )
        await self.memory_service.save_interaction(
            user_id=user_id,
            agent_id=agent_id,
            thread_id=thread_id,
            message=message,
        )

    async def create_memory(
        self,
        agent_id: str,
        user_id: UUID | None,
        memory_type: MemoryType,
        content: str,
        importance_score: float = 0.5,
        metadata: dict[str, Any] | None = None,
    ) -> UUID:
        """Create a new memory"""
        await self._ensure_memory_service()
        return await self.memory_service.create_memory(
            agent_id=agent_id,
            user_id=user_id,
            memory_type=memory_type,
            content=content,
            importance_score=importance_score,
            metadata=metadata,
        )

    async def recall_agent_knowledge(
        self,
        target_agent_id: str,
        query: str,
        user_id: UUID | None = None,
    ) -> list[MemorySearchResult]:
        """
        Passive consultation: Query another agent's past knowledge
        Retrieves what the target agent has learned without invoking them
        """
        await self._ensure_memory_service()
        return await self.memory_service.recall_agent_knowledge(
            target_agent_id=target_agent_id,
            query=query,
            user_id=user_id,
            limit=5,
        )


class BaseAgent(ABC, MemoryAwareMixin):
    """
    Abstract base class for all agents
    Provides common interface and memory capabilities
    """

    def __init__(self, metadata: AgentMetadata):
        super().__init__()
        self.metadata = metadata
        self.graph: StateGraph | None = None

    @property
    def agent_id(self) -> str:
        """Get agent ID"""
        return self.metadata.id

    @property
    def nickname(self) -> str:
        """Get agent nickname"""
        return self.metadata.nickname

    @abstractmethod
    def create_graph(self) -> StateGraph:
        """
        Create the LangGraph state machine for this agent
        Must be implemented by subclasses
        """
        pass

    async def initialize(self) -> None:
        """Initialize agent (create graph, connect to memory)"""
        await self._ensure_memory_service()
        self.graph = self.create_graph()

    async def execute(
        self,
        command: str,
        context: AgentExecutionContext,
    ) -> AgentExecutionResult:
        """
        Execute agent with the given command and context
        This is the main entry point for agent invocation
        """
        try:
            # Notify task started
            if context.task_callback:
                from backend.models.task_models import TaskStatus
                await context.task_callback.on_status_change(
                    TaskStatus.QUEUED, TaskStatus.IN_PROGRESS
                )

            # Load conversation context if not provided
            if not context.conversation_context:
                context.conversation_context = await self.load_context(
                    agent_id=self.agent_id,
                    user_id=context.user_id,
                    thread_id=context.thread_id,
                    current_query=command,
                )

            # Save user message
            await self.save_message(
                user_id=context.user_id,
                agent_id=self.agent_id,
                thread_id=context.thread_id,
                role=ConversationRole.USER,
                content=command,
            )

            # Execute graph
            if not self.graph:
                await self.initialize()

            result = await self._execute_graph(command, context)

            # Save assistant response
            await self.save_message(
                user_id=context.user_id,
                agent_id=self.agent_id,
                thread_id=context.thread_id,
                role=ConversationRole.ASSISTANT,
                content=result.response,
            )

            # Notify completion
            if context.task_callback:
                from backend.models.task_models import TaskStatus
                await context.task_callback.on_status_change(
                    TaskStatus.IN_PROGRESS, TaskStatus.COMPLETED
                )

            return result

        except Exception as e:
            # Notify failure
            if context.task_callback:
                from backend.models.task_models import TaskStatus
                await context.task_callback.on_status_change(
                    TaskStatus.IN_PROGRESS, TaskStatus.FAILED
                )
            return AgentExecutionResult(
                success=False,
                response="",
                error=str(e),
            )

    @abstractmethod
    async def _execute_graph(
        self,
        command: str,
        context: AgentExecutionContext,
    ) -> AgentExecutionResult:
        """
        Execute the agent's graph (implemented by subclasses)
        """
        pass

    async def consult_agent(
        self,
        target_agent_id: str,
        query: str,
        consultation_context: AgentExecutionContext,
    ) -> AgentExecutionResult:
        """
        Active consultation: Invoke another agent for real-time analysis
        This is different from recall_agent_knowledge (passive) - it actually
        runs the target agent with a new query
        """
        from backend.agents.base.agent_registry import AgentRegistry

        # Get target agent from registry
        target_agent = AgentRegistry.get_specialist(target_agent_id)

        if not target_agent:
            return AgentExecutionResult(
                success=False,
                response="",
                error=f"Agent {target_agent_id} not found",
            )

        # Execute target agent
        result = await target_agent.execute(query, consultation_context)

        # Save consultation record (to be implemented in database)
        # This would save to agent_consultations table

        return result
