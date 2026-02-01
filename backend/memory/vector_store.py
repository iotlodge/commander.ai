"""
Vector Store implementation using Qdrant
Provides semantic search capabilities for agent memories
"""

from typing import Any
from uuid import UUID

from openai import AsyncOpenAI
from qdrant_client import AsyncQdrantClient
from qdrant_client.models import (
    Distance,
    VectorParams,
    PointStruct,
    SearchParams,
    Filter,
    FieldCondition,
    MatchValue,
)

from backend.core.config import get_settings
from backend.memory.schemas import AgentMemory, MemorySearchResult, MemoryType


class SemanticMemory:
    """
    Qdrant-backed vector store for semantic memory search
    """

    def __init__(self):
        self.settings = get_settings()
        self.qdrant_client: AsyncQdrantClient | None = None
        self.openai_client = AsyncOpenAI(api_key=self.settings.openai_api_key)
        self.collection_name = self.settings.qdrant_collection_name
        self.embedding_dimension = 1536  # OpenAI ada-002 dimension

    async def connect(self) -> None:
        """Initialize Qdrant client and ensure collection exists"""
        self.qdrant_client = AsyncQdrantClient(
            url=self.settings.qdrant_url,
            api_key=self.settings.qdrant_api_key,
        )

        # Check if collection exists, create if not
        collections = await self.qdrant_client.get_collections()
        collection_names = [c.name for c in collections.collections]

        if self.collection_name not in collection_names:
            await self.qdrant_client.create_collection(
                collection_name=self.collection_name,
                vectors_config=VectorParams(
                    size=self.embedding_dimension,
                    distance=Distance.COSINE,
                ),
            )

    async def disconnect(self) -> None:
        """Close Qdrant client"""
        if self.qdrant_client:
            await self.qdrant_client.close()

    async def generate_embedding(self, text: str) -> list[float]:
        """Generate embedding using OpenAI"""
        response = await self.openai_client.embeddings.create(
            model=self.settings.openai_embedding_model,
            input=text,
        )
        return response.data[0].embedding

    async def store_memory(self, memory: AgentMemory) -> None:
        """
        Store a memory with its embedding in Qdrant
        Assumes memory.id and memory.embedding are already set
        """
        if not memory.id or not memory.embedding:
            raise ValueError("Memory must have id and embedding set before storing")

        point = PointStruct(
            id=str(memory.id),
            vector=memory.embedding,
            payload={
                "agent_id": memory.agent_id,
                "user_id": str(memory.user_id) if memory.user_id else None,
                "memory_type": memory.memory_type.value,
                "content": memory.content,
                "importance_score": memory.importance_score,
                "access_count": memory.access_count,
                "metadata": memory.metadata,
            },
        )

        await self.qdrant_client.upsert(
            collection_name=self.collection_name,
            points=[point],
        )

    async def search_similar_memories(
        self,
        query: str,
        agent_id: str,
        user_id: UUID | None = None,
        limit: int = 10,
        score_threshold: float | None = None,
    ) -> list[MemorySearchResult]:
        """
        Search for semantically similar memories using vector search
        """
        # Generate query embedding
        query_embedding = await self.generate_embedding(query)

        # Build filter conditions
        must_conditions = [
            FieldCondition(
                key="agent_id",
                match=MatchValue(value=agent_id),
            )
        ]

        if user_id is not None:
            must_conditions.append(
                FieldCondition(
                    key="user_id",
                    match=MatchValue(value=str(user_id)),
                )
            )

        search_filter = Filter(must=must_conditions) if must_conditions else None

        # Perform search using query_points (new Qdrant API)
        search_results = await self.qdrant_client.query_points(
            collection_name=self.collection_name,
            query=query_embedding,
            query_filter=search_filter,
            limit=limit,
            score_threshold=score_threshold or self.settings.ltm_similarity_threshold,
        )

        # Convert to MemorySearchResult
        results = []
        for hit in search_results.points:
            memory = AgentMemory(
                id=UUID(hit.id),
                agent_id=hit.payload["agent_id"],
                user_id=UUID(hit.payload["user_id"]) if hit.payload.get("user_id") else None,
                memory_type=MemoryType(hit.payload["memory_type"]),
                content=hit.payload["content"],
                importance_score=hit.payload["importance_score"],
                access_count=hit.payload["access_count"],
                metadata=hit.payload.get("metadata", {}),
            )

            results.append(
                MemorySearchResult(
                    memory=memory,
                    similarity_score=hit.score,
                )
            )

        return results

    async def update_memory_payload(
        self,
        memory_id: UUID,
        updates: dict[str, Any],
    ) -> None:
        """Update memory payload (e.g., access_count)"""
        await self.qdrant_client.set_payload(
            collection_name=self.collection_name,
            payload=updates,
            points=[str(memory_id)],
        )

    async def delete_memory(self, memory_id: UUID) -> None:
        """Delete a memory from Qdrant"""
        await self.qdrant_client.delete(
            collection_name=self.collection_name,
            points_selector=[str(memory_id)],
        )

    async def count_memories(
        self,
        agent_id: str | None = None,
        user_id: UUID | None = None,
    ) -> int:
        """Count memories matching filters"""
        must_conditions = []

        if agent_id:
            must_conditions.append(
                FieldCondition(
                    key="agent_id",
                    match=MatchValue(value=agent_id),
                )
            )

        if user_id:
            must_conditions.append(
                FieldCondition(
                    key="user_id",
                    match=MatchValue(value=str(user_id)),
                )
            )

        search_filter = Filter(must=must_conditions) if must_conditions else None

        result = await self.qdrant_client.count(
            collection_name=self.collection_name,
            count_filter=search_filter,
        )

        return result.count
