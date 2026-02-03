"""
Collection repository for database operations
"""

from datetime import datetime
from uuid import UUID

from sqlalchemy import select, update, desc, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import Column, String, Text, DateTime, Integer
from sqlalchemy.dialects.postgresql import UUID as PGUUID, JSONB

from backend.models.base import Base
from backend.models.document_models import DocumentCollection, CollectionCreate, CollectionUpdate


class DocumentCollectionModel(Base):
    """SQLAlchemy model for document_collections table"""

    __tablename__ = "document_collections"

    id = Column(PGUUID(as_uuid=True), primary_key=True, server_default="gen_random_uuid()")
    user_id = Column(PGUUID(as_uuid=True), nullable=False, index=True)
    collection_name = Column(String(255), nullable=False)
    qdrant_collection_name = Column(String(255), nullable=False, unique=True)
    description = Column(Text, nullable=True)
    chunk_count = Column(Integer, nullable=False, server_default="0")
    created_at = Column(DateTime, nullable=False, server_default="NOW()")
    updated_at = Column(DateTime, nullable=False, server_default="NOW()", onupdate=func.now())
    meta_data = Column("metadata", JSONB, nullable=False, server_default="{}")  # Renamed to avoid SQLAlchemy reserved name


class CollectionRepository:
    """Data access layer for document collections"""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_collection(self, collection: CollectionCreate) -> DocumentCollection:
        """Create new collection in database"""
        # Generate Qdrant collection name (user_id prefix + collection_name)
        user_id_prefix = str(collection.user_id).split("-")[0]
        qdrant_collection_name = f"{user_id_prefix}_{collection.collection_name}"

        model = DocumentCollectionModel(
            user_id=collection.user_id,
            collection_name=collection.collection_name,
            qdrant_collection_name=qdrant_collection_name,
            description=collection.description,
            chunk_count=0,
            meta_data={},
        )
        self.session.add(model)
        await self.session.commit()
        await self.session.refresh(model)

        return self._model_to_pydantic(model)

    async def get_collection(self, collection_id: UUID) -> DocumentCollection | None:
        """Get collection by ID"""
        stmt = select(DocumentCollectionModel).where(DocumentCollectionModel.id == collection_id)
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()

        if not model:
            return None

        return self._model_to_pydantic(model)

    async def get_collection_by_name(
        self, user_id: UUID, collection_name: str
    ) -> DocumentCollection | None:
        """Get collection by user_id and collection_name"""
        stmt = select(DocumentCollectionModel).where(
            DocumentCollectionModel.user_id == user_id,
            DocumentCollectionModel.collection_name == collection_name,
        )
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()

        if not model:
            return None

        return self._model_to_pydantic(model)

    async def list_user_collections(
        self, user_id: UUID, limit: int = 100
    ) -> list[DocumentCollection]:
        """Get all collections for a user"""
        stmt = (
            select(DocumentCollectionModel)
            .where(DocumentCollectionModel.user_id == user_id)
            .order_by(desc(DocumentCollectionModel.created_at))
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        models = result.scalars().all()

        return [self._model_to_pydantic(m) for m in models]

    async def update_collection(
        self, collection_id: UUID, collection_update: CollectionUpdate
    ) -> DocumentCollection:
        """Update collection metadata"""
        update_data = {}
        if collection_update.description is not None:
            update_data["description"] = collection_update.description
        if collection_update.metadata is not None:
            update_data["meta_data"] = collection_update.metadata

        if update_data:
            update_data["updated_at"] = datetime.utcnow()
            stmt = (
                update(DocumentCollectionModel)
                .where(DocumentCollectionModel.id == collection_id)
                .values(**update_data)
            )
            await self.session.execute(stmt)
            await self.session.commit()

        return await self.get_collection(collection_id)

    async def increment_chunk_count(self, collection_id: UUID, increment: int = 1) -> None:
        """Increment chunk count for a collection"""
        stmt = (
            update(DocumentCollectionModel)
            .where(DocumentCollectionModel.id == collection_id)
            .values(
                chunk_count=DocumentCollectionModel.chunk_count + increment,
                updated_at=datetime.utcnow(),
            )
        )
        await self.session.execute(stmt)
        await self.session.commit()

    async def delete_collection(self, collection_id: UUID) -> None:
        """Delete collection (cascades to chunks)"""
        from sqlalchemy import delete as sql_delete

        stmt = sql_delete(DocumentCollectionModel).where(
            DocumentCollectionModel.id == collection_id
        )
        await self.session.execute(stmt)
        await self.session.commit()

    def _model_to_pydantic(self, model: DocumentCollectionModel) -> DocumentCollection:
        """Convert SQLAlchemy model to Pydantic model"""
        return DocumentCollection(
            id=model.id,
            user_id=model.user_id,
            collection_name=model.collection_name,
            qdrant_collection_name=model.qdrant_collection_name,
            description=model.description,
            chunk_count=model.chunk_count,
            created_at=model.created_at,
            updated_at=model.updated_at,
            metadata=model.meta_data or {},
        )
