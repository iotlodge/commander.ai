"""
Memory Service - Central coordinator for all memory systems
Combines Short-Term Memory (Redis), Long-Term Memory (PostgreSQL), and Semantic Memory (Qdrant)
"""

from typing import Any
from uuid import UUID

from backend.core.config import get_settings
from backend.memory.short_term import ShortTermMemory, RedisCheckpointSaver
from backend.memory.long_term import LongTermMemory
from backend.memory.vector_store import SemanticMemory
from backend.memory.schemas import (
    ConversationMessage,
    ConversationContext,
    AgentMemory,
    MemoryType,
    CheckpointData,
    MemorySearchResult,
)


class MemoryService:
    """
    Unified memory service that coordinates STM, LTM, and semantic search
    This is the main interface agents use to interact with memory systems
    """

    def __init__(self):
        self.settings = get_settings()
        self.stm = ShortTermMemory()
        self.ltm = LongTermMemory()
        self.vector_store = SemanticMemory()
        self._initialized = False

    async def initialize(self) -> None:
        """Initialize all memory components"""
        if not self._initialized:
            await self.stm.connect()
            await self.vector_store.connect()
            self._initialized = True

    async def shutdown(self) -> None:
        """Shutdown all memory components"""
        if self._initialized:
            await self.stm.disconnect()
            await self.vector_store.disconnect()
            self._initialized = False

    def get_checkpoint_saver(self) -> RedisCheckpointSaver:
        """Get LangGraph checkpoint saver for agent graphs"""
        return RedisCheckpointSaver(self.stm)

    async def save_interaction(
        self,
        user_id: UUID,
        agent_id: str,
        thread_id: UUID,
        message: ConversationMessage,
    ) -> None:
        """
        Save a conversation message to both STM and LTM
        """
        # Save to Redis (fast, temporary)
        await self.stm.save_message(user_id, agent_id, thread_id, message)

        # Save to PostgreSQL (persistent)
        await self.ltm.save_conversation(message)

    async def get_agent_context(
        self,
        agent_id: str,
        user_id: UUID,
        thread_id: UUID,
        current_query: str,
    ) -> ConversationContext:
        """
        Load complete context for an agent's execution:
        1. Recent conversation from STM (Redis)
        2. Graph state from latest checkpoint
        3. Relevant memories from semantic search (Qdrant)
        """
        # Get recent conversation from STM (fast)
        recent_conversation = await self.stm.get_conversation_context(
            user_id=user_id,
            agent_id=agent_id,
            thread_id=thread_id,
            limit=20,
        )

        # If STM is empty, fall back to LTM
        if not recent_conversation:
            recent_conversation = await self.ltm.get_conversation_history(
                user_id=user_id,
                agent_id=agent_id,
                thread_id=thread_id,
                limit=20,
            )

        # Get latest checkpoint state
        checkpoint = await self.ltm.get_latest_checkpoint(
            agent_id=agent_id,
            user_id=user_id,
            thread_id=thread_id,
        )

        graph_state = checkpoint.state_data if checkpoint else None

        # Perform semantic search for relevant memories
        relevant_memories = await self.vector_store.search_similar_memories(
            query=current_query,
            agent_id=agent_id,
            user_id=user_id,
            limit=10,
        )

        # Update access counts for retrieved memories
        for result in relevant_memories:
            if result.memory.id:
                await self.ltm.update_memory_access(result.memory.id)

        return ConversationContext(
            graph_state=graph_state,
            recent_conversation=recent_conversation,
            relevant_memories=relevant_memories,
            thread_id=thread_id,
            user_id=user_id,
            agent_id=agent_id,
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
        """
        Create a new memory for an agent
        Stores in both PostgreSQL and Qdrant with embedding
        """
        # Generate embedding
        embedding = await self.vector_store.generate_embedding(content)

        # Create memory object
        memory = AgentMemory(
            agent_id=agent_id,
            user_id=user_id,
            memory_type=memory_type,
            content=content,
            embedding=embedding,
            importance_score=importance_score,
            metadata=metadata or {},
        )

        # Save to PostgreSQL
        memory_id = await self.ltm.save_memory(memory)
        memory.id = memory_id

        # Store in Qdrant for semantic search
        await self.vector_store.store_memory(memory)

        return memory_id

    async def retrieve_relevant_memories(
        self,
        agent_id: str,
        query: str,
        user_id: UUID | None = None,
        limit: int = 10,
    ) -> list[MemorySearchResult]:
        """
        Retrieve semantically relevant memories for a query
        """
        return await self.vector_store.search_similar_memories(
            query=query,
            agent_id=agent_id,
            user_id=user_id,
            limit=limit,
        )

    async def recall_agent_knowledge(
        self,
        target_agent_id: str,
        query: str,
        user_id: UUID | None = None,
        limit: int = 5,
    ) -> list[MemorySearchResult]:
        """
        Query another agent's past knowledge (passive consultation)
        Used when an agent wants to recall what another agent learned
        """
        return await self.retrieve_relevant_memories(
            agent_id=target_agent_id,
            query=query,
            user_id=user_id,
            limit=limit,
        )

    async def save_checkpoint(
        self,
        checkpoint_data: CheckpointData,
        persist_to_ltm: bool = False,
    ) -> None:
        """
        Save a LangGraph checkpoint
        Always saves to Redis (STM), optionally persists to PostgreSQL (LTM)
        """
        # Always save to Redis for active sessions
        await self.stm.save_checkpoint(checkpoint_data)

        # Optionally persist important checkpoints to PostgreSQL
        if persist_to_ltm:
            await self.ltm.save_checkpoint_persistent(checkpoint_data)

    async def consolidate_memories(
        self,
        agent_id: str,
        user_id: UUID,
        thread_id: UUID,
    ) -> None:
        """
        Memory consolidation: Convert important conversation exchanges into memories
        This should be run periodically (e.g., after task completion or hourly)
        """
        # Get recent conversation
        conversation = await self.ltm.get_conversation_history(
            user_id=user_id,
            agent_id=agent_id,
            thread_id=thread_id,
            limit=50,
        )

        if len(conversation) < 2:
            return

        # Simple consolidation: Create episodic memory from conversation summary
        # In production, you'd use an LLM to extract key learnings
        conversation_text = "\n".join(
            [f"{msg.role.value}: {msg.content}" for msg in conversation[-10:]]
        )

        await self.create_memory(
            agent_id=agent_id,
            user_id=user_id,
            memory_type=MemoryType.EPISODIC,
            content=f"Conversation summary: {conversation_text[:500]}",
            importance_score=0.6,
            metadata={
                "thread_id": str(thread_id),
                "message_count": len(conversation),
                "consolidated": True,
            },
        )

    async def clear_thread(
        self,
        user_id: UUID,
        agent_id: str,
        thread_id: UUID,
    ) -> None:
        """Clear conversation thread from STM (Redis only)"""
        await self.stm.clear_conversation(user_id, agent_id, thread_id)


# Global instance (singleton pattern)
_memory_service: MemoryService | None = None


async def get_memory_service() -> MemoryService:
    """Get or create global memory service instance"""
    global _memory_service
    if _memory_service is None:
        _memory_service = MemoryService()
        await _memory_service.initialize()
    return _memory_service
