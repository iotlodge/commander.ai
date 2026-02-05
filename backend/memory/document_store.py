"""
Document Store implementation using Qdrant for multi-collection management
Handles document vector storage and semantic search across collections

IMPORTANT: Use the singleton pattern via get_document_store() instead of
creating instances directly to prevent connection pool exhaustion.

Recommended:
    from backend.core.dependencies import get_document_store
    doc_store = await get_document_store()

Discouraged:
    doc_store = DocumentStore()  # Creates new connection pool!
    await doc_store.connect()
"""

import logging
from typing import Any
from uuid import UUID, uuid4

from openai import AsyncOpenAI
from qdrant_client import AsyncQdrantClient
from qdrant_client.models import (
    Distance,
    VectorParams,
    PointStruct,
    Filter,
    FieldCondition,
    MatchValue,
)

from backend.core.config import get_settings
from backend.models.document_models import DocumentChunk, ChunkCreate, SearchResult

logger = logging.getLogger(__name__)

# Track instance count for debugging
_instance_count = 0


class DocumentStore:
    """
    Multi-collection document vector store using Qdrant
    Manages user-scoped document collections for semantic search

    IMPORTANT: Prefer using the singleton pattern via get_document_store()
    to avoid creating multiple instances and exhausting connection pools.
    """

    def __init__(self):
        global _instance_count
        _instance_count += 1

        if _instance_count > 1:
            logger.warning(
                f"Multiple DocumentStore instances detected ({_instance_count}). "
                "Consider using get_document_store() singleton to reduce resource usage."
            )

        self.settings = get_settings()
        self.qdrant_client: AsyncQdrantClient | None = None
        self.openai_client = AsyncOpenAI(api_key=self.settings.openai_api_key)
        self.embedding_dimension = 1536  # OpenAI ada-002 dimension

    async def connect(self) -> None:
        """
        Initialize Qdrant client with connection pooling

        Note: If using singleton pattern (recommended), connection is managed
        by the singleton instance and should not be disconnected manually.
        """
        if self.qdrant_client is not None:
            logger.debug("DocumentStore already connected, reusing connection")
            return

        try:
            logger.info(f"Connecting to Qdrant at {self.settings.qdrant_url}")
            self.qdrant_client = AsyncQdrantClient(
                url=self.settings.qdrant_url,
                api_key=self.settings.qdrant_api_key,
            )
            logger.info("DocumentStore Qdrant client connected successfully")
        except Exception as e:
            logger.error(f"Failed to connect to Qdrant: {e}", exc_info=True)
            self.qdrant_client = None
            raise

    async def disconnect(self) -> None:
        """
        Close Qdrant client

        Note: If using singleton pattern, this should only be called during
        application shutdown via shutdown_document_store().
        """
        if self.qdrant_client:
            await self.qdrant_client.close()
            self.qdrant_client = None
            logger.info("DocumentStore Qdrant client disconnected")

    async def create_collection(
        self, qdrant_collection_name: str, user_id: UUID
    ) -> None:
        """
        Create new Qdrant collection for documents

        Args:
            qdrant_collection_name: Name for the Qdrant collection
            user_id: User ID for metadata filtering

        Raises:
            RuntimeError: If qdrant_client is not initialized (call connect() first)
        """
        if self.qdrant_client is None:
            raise RuntimeError(
                "DocumentStore.qdrant_client is None. "
                "Ensure connect() has been called before creating collections. "
                "Use get_document_store() singleton for proper initialization."
            )

        # Check if collection already exists
        collections = await self.qdrant_client.get_collections()
        collection_names = [c.name for c in collections.collections]

        if qdrant_collection_name not in collection_names:
            await self.qdrant_client.create_collection(
                collection_name=qdrant_collection_name,
                vectors_config=VectorParams(
                    size=self.embedding_dimension,
                    distance=Distance.COSINE,
                ),
            )

    async def delete_collection(self, qdrant_collection_name: str) -> None:
        """
        Delete Qdrant collection and all vectors

        Args:
            qdrant_collection_name: Name of the Qdrant collection to delete
        """
        await self.qdrant_client.delete_collection(collection_name=qdrant_collection_name)

    async def generate_embedding(self, text: str) -> list[float]:
        """
        Generate embedding using OpenAI

        Args:
            text: Text to embed

        Returns:
            Embedding vector
        """
        response = await self.openai_client.embeddings.create(
            model=self.settings.openai_embedding_model,
            input=text,
        )
        return response.data[0].embedding

    async def store_chunks(
        self,
        qdrant_collection_name: str,
        chunks: list[ChunkCreate],
    ) -> None:
        """
        Store document chunks with embeddings in Qdrant

        Args:
            qdrant_collection_name: Target Qdrant collection
            chunks: List of chunks to store (must have vector_id set)

        Raises:
            RuntimeError: If qdrant_client is not initialized (call connect() first)
        """
        if self.qdrant_client is None:
            raise RuntimeError(
                "DocumentStore.qdrant_client is None. "
                "Ensure connect() has been called before storing chunks. "
                "Use get_document_store() singleton for proper initialization."
            )

        points = []
        for chunk in chunks:
            # Generate embedding for chunk content
            embedding = await self.generate_embedding(chunk.content)

            # Create Qdrant point
            point = PointStruct(
                id=str(chunk.vector_id),
                vector=embedding,
                payload={
                    "user_id": str(chunk.user_id),
                    "collection_id": str(chunk.collection_id),
                    "chunk_index": chunk.chunk_index,
                    "source_type": chunk.source_type,
                    "source_file_path": chunk.source_file_path,
                    "file_name": chunk.file_name,
                    "metadata": chunk.metadata,
                },
            )
            points.append(point)

        # Batch upsert all points
        await self.qdrant_client.upsert(
            collection_name=qdrant_collection_name,
            points=points,
        )

    async def search_collection(
        self,
        qdrant_collection_name: str,
        user_id: UUID,
        query: str,
        limit: int = 10,
        score_threshold: float = 0.7,
    ) -> list[tuple[UUID, float]]:
        """
        Search specific collection for relevant chunks

        Args:
            qdrant_collection_name: Collection to search
            user_id: User ID for filtering
            query: Search query text
            limit: Maximum number of results
            score_threshold: Minimum similarity score

        Returns:
            List of (vector_id, similarity_score) tuples
        """
        # Generate query embedding
        query_embedding = await self.generate_embedding(query)

        # Build filter for user_id
        search_filter = Filter(
            must=[
                FieldCondition(
                    key="user_id",
                    match=MatchValue(value=str(user_id)),
                )
            ]
        )

        # Perform search
        search_results = await self.qdrant_client.query_points(
            collection_name=qdrant_collection_name,
            query=query_embedding,
            query_filter=search_filter,
            limit=limit,
            score_threshold=score_threshold,
        )

        # Extract vector IDs and scores
        results = []
        for hit in search_results.points:
            vector_id = UUID(hit.id)
            score = hit.score
            results.append((vector_id, score))

        return results

    async def search_all_collections(
        self,
        collection_names: list[str],
        user_id: UUID,
        query: str,
        limit: int = 10,
        score_threshold: float = 0.7,
    ) -> list[tuple[str, UUID, float]]:
        """
        Search across multiple collections

        Args:
            collection_names: List of Qdrant collection names to search
            user_id: User ID for filtering
            query: Search query text
            limit: Maximum results per collection
            score_threshold: Minimum similarity score

        Returns:
            List of (qdrant_collection_name, vector_id, similarity_score) tuples
        """
        all_results = []

        for collection_name in collection_names:
            try:
                collection_results = await self.search_collection(
                    qdrant_collection_name=collection_name,
                    user_id=user_id,
                    query=query,
                    limit=limit,
                    score_threshold=score_threshold,
                )

                # Add collection name to results
                for vector_id, score in collection_results:
                    all_results.append((collection_name, vector_id, score))

            except Exception as e:
                # Skip collections that don't exist or have errors
                print(f"Error searching collection {collection_name}: {e}")
                continue

        # Sort by score descending
        all_results.sort(key=lambda x: x[2], reverse=True)

        # Limit total results
        return all_results[:limit]
