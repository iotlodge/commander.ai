"""
Document models for vector store management
"""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class DocumentCollection(BaseModel):
    """Represents a named collection of documents"""

    id: UUID
    user_id: UUID
    collection_name: str
    qdrant_collection_name: str
    description: str | None = None
    chunk_count: int = 0
    created_at: datetime
    updated_at: datetime
    metadata: dict = Field(default_factory=dict)


class CollectionCreate(BaseModel):
    """Request to create a new collection"""

    user_id: UUID
    collection_name: str
    description: str | None = None


class CollectionUpdate(BaseModel):
    """Update collection metadata"""

    description: str | None = None
    metadata: dict | None = None


class DocumentChunk(BaseModel):
    """Represents a chunk of a document with metadata"""

    id: UUID
    collection_id: UUID
    user_id: UUID
    content: str
    chunk_index: int
    source_type: str  # 'file'
    source_file_path: str | None = None
    file_name: str | None = None
    metadata: dict = Field(default_factory=dict)
    created_at: datetime
    vector_id: UUID  # Qdrant point ID


class ChunkCreate(BaseModel):
    """Request to create document chunks"""

    collection_id: UUID
    user_id: UUID
    content: str
    chunk_index: int
    source_type: str
    source_file_path: str | None = None
    file_name: str | None = None
    metadata: dict = Field(default_factory=dict)
    vector_id: UUID


class SearchResult(BaseModel):
    """Search result with chunk content and metadata"""

    chunk: DocumentChunk
    similarity_score: float
    collection_name: str | None = None
