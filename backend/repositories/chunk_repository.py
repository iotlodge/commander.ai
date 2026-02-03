"""
Chunk repository for database operations
"""

from uuid import UUID

from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import Column, String, Text, DateTime, Integer, ForeignKey
from sqlalchemy.dialects.postgresql import UUID as PGUUID, JSONB

from backend.models.base import Base
from backend.models.document_models import DocumentChunk, ChunkCreate


class DocumentChunkModel(Base):
    """SQLAlchemy model for document_chunks table"""

    __tablename__ = "document_chunks"

    id = Column(PGUUID(as_uuid=True), primary_key=True, server_default="gen_random_uuid()")
    collection_id = Column(
        PGUUID(as_uuid=True),
        ForeignKey("document_collections.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_id = Column(PGUUID(as_uuid=True), nullable=False, index=True)
    content = Column(Text, nullable=False)
    chunk_index = Column(Integer, nullable=False)
    source_type = Column(String(50), nullable=False)
    source_file_path = Column(Text, nullable=True)
    file_name = Column(String(255), nullable=True)
    meta_data = Column("metadata", JSONB, nullable=False, server_default="{}")  # Renamed to avoid SQLAlchemy reserved name
    created_at = Column(DateTime, nullable=False, server_default="NOW()")
    vector_id = Column(PGUUID(as_uuid=True), nullable=False, index=True)


class ChunkRepository:
    """Data access layer for document chunks"""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_chunks(self, chunks: list[ChunkCreate]) -> list[DocumentChunk]:
        """Bulk create chunks"""
        models = [
            DocumentChunkModel(
                collection_id=chunk.collection_id,
                user_id=chunk.user_id,
                content=chunk.content,
                chunk_index=chunk.chunk_index,
                source_type=chunk.source_type,
                source_file_path=chunk.source_file_path,
                file_name=chunk.file_name,
                meta_data=chunk.metadata,
                vector_id=chunk.vector_id,
            )
            for chunk in chunks
        ]

        self.session.add_all(models)
        await self.session.commit()

        # Refresh all models to get generated IDs
        for model in models:
            await self.session.refresh(model)

        return [self._model_to_pydantic(m) for m in models]

    async def get_chunk(self, chunk_id: UUID) -> DocumentChunk | None:
        """Get chunk by ID"""
        stmt = select(DocumentChunkModel).where(DocumentChunkModel.id == chunk_id)
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()

        if not model:
            return None

        return self._model_to_pydantic(model)

    async def get_chunks_by_collection(
        self, collection_id: UUID, limit: int = 1000
    ) -> list[DocumentChunk]:
        """Get all chunks for a collection"""
        stmt = (
            select(DocumentChunkModel)
            .where(DocumentChunkModel.collection_id == collection_id)
            .order_by(DocumentChunkModel.chunk_index)
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        models = result.scalars().all()

        return [self._model_to_pydantic(m) for m in models]

    async def get_chunk_by_vector_id(self, vector_id: UUID) -> DocumentChunk | None:
        """Get chunk by Qdrant vector ID"""
        stmt = select(DocumentChunkModel).where(DocumentChunkModel.vector_id == vector_id)
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()

        if not model:
            return None

        return self._model_to_pydantic(model)

    async def delete_chunks(self, collection_id: UUID) -> None:
        """Delete all chunks for a collection"""
        from sqlalchemy import delete as sql_delete

        stmt = sql_delete(DocumentChunkModel).where(
            DocumentChunkModel.collection_id == collection_id
        )
        await self.session.execute(stmt)
        await self.session.commit()

    def _model_to_pydantic(self, model: DocumentChunkModel) -> DocumentChunk:
        """Convert SQLAlchemy model to Pydantic model"""
        return DocumentChunk(
            id=model.id,
            collection_id=model.collection_id,
            user_id=model.user_id,
            content=model.content,
            chunk_index=model.chunk_index,
            source_type=model.source_type,
            source_file_path=model.source_file_path,
            file_name=model.file_name,
            metadata=model.meta_data or {},
            created_at=model.created_at,
            vector_id=model.vector_id,
        )
