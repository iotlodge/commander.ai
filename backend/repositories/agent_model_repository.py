"""
Agent model configuration repository for database operations
"""

from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import select, update, desc, func, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import Column, String, Integer, Float, DateTime, Boolean, Text, Numeric
from sqlalchemy.dialects.postgresql import UUID as PGUUID, JSONB

from backend.models.base import Base
from backend.models.agent_model_models import (
    AgentModelConfig,
    AgentModelUpdate,
    ApprovedModel,
)


class ApprovedModelProviderModel(Base):
    """SQLAlchemy model for approved_models_provider table"""

    __tablename__ = "approved_models_provider"

    id = Column(PGUUID(as_uuid=True), primary_key=True, server_default="gen_random_uuid()")
    provider = Column(String(50), nullable=False)
    model_name = Column(String(100), nullable=False)
    model_display_name = Column(String(150), nullable=True)
    mode = Column(String(50), nullable=True)
    context_window = Column(Integer, nullable=True)
    supports_function_calling = Column(Boolean, nullable=False, server_default="false")
    approved = Column(Boolean, nullable=False, server_default="false")
    version = Column(String(50), nullable=True)
    deprecated = Column(Boolean, nullable=False, server_default="false")
    replacement_model_id = Column(PGUUID(as_uuid=True), nullable=True)
    cost_per_1k_input = Column(Numeric(10, 6), nullable=True)
    cost_per_1k_output = Column(Numeric(10, 6), nullable=True)
    default_params = Column(JSONB, nullable=False, server_default="{}")
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=False, server_default="NOW()")
    updated_at = Column(DateTime, nullable=False, server_default="NOW()", onupdate=func.now())


class AgentModelConfigModel(Base):
    """SQLAlchemy model for agent_model_configs table"""

    __tablename__ = "agent_model_configs"

    id = Column(PGUUID(as_uuid=True), primary_key=True, server_default="gen_random_uuid()")
    agent_id = Column(String(50), nullable=False, index=True)
    nickname = Column(String(50), nullable=False)
    provider = Column(String(50), nullable=False)
    model_name = Column(String(100), nullable=False)
    temperature = Column(Float, nullable=False, server_default="0.7")
    max_tokens = Column(Integer, nullable=False, server_default="2000")
    model_params = Column(JSONB, nullable=False, server_default="{}")
    version = Column(Integer, nullable=False, server_default="1")
    active = Column(Boolean, nullable=False, server_default="true")
    created_at = Column(DateTime, nullable=False, server_default="NOW()")
    updated_at = Column(DateTime, nullable=False, server_default="NOW()", onupdate=func.now())
    created_by = Column(PGUUID(as_uuid=True), nullable=True)
    updated_by = Column(PGUUID(as_uuid=True), nullable=True)


class AgentModelRepository:
    """Data access layer for agent model configurations"""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_agent_model_config(self, agent_id: str) -> AgentModelConfig | None:
        """Get the active model configuration for an agent"""
        stmt = (
            select(AgentModelConfigModel)
            .where(
                and_(
                    AgentModelConfigModel.agent_id == agent_id,
                    AgentModelConfigModel.active == True
                )
            )
            .order_by(desc(AgentModelConfigModel.version))
            .limit(1)
        )
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()

        if not model:
            return None

        return self._config_model_to_pydantic(model)

    async def save_agent_model_config(
        self,
        agent_id: str,
        nickname: str,
        model_update: AgentModelUpdate,
        user_id: UUID | None = None
    ) -> AgentModelConfig:
        """
        Save a new model configuration for an agent.
        Creates a new version and marks the previous version as inactive.
        """
        # Get the current active config to determine the next version number
        current_config = await self.get_agent_model_config(agent_id)
        next_version = (current_config.version + 1) if current_config else 1

        # Mark current config as inactive (if exists)
        if current_config:
            stmt = (
                update(AgentModelConfigModel)
                .where(
                    and_(
                        AgentModelConfigModel.agent_id == agent_id,
                        AgentModelConfigModel.active == True
                    )
                )
                .values(active=False, updated_at=datetime.utcnow())
            )
            await self.session.execute(stmt)

        # Create new config version
        now = datetime.utcnow()
        new_config = AgentModelConfigModel(
            id=str(uuid4()),  # Generate UUID as string for SQLite compatibility
            agent_id=agent_id,
            nickname=nickname,
            provider=model_update.provider,
            model_name=model_update.model_name,
            temperature=model_update.temperature if model_update.temperature is not None else 0.7,
            max_tokens=model_update.max_tokens if model_update.max_tokens is not None else 2000,
            model_params=model_update.model_params or {},
            version=next_version,
            active=True,
            created_at=now,
            updated_at=now,
            created_by=user_id,
            updated_by=user_id,
        )
        self.session.add(new_config)
        await self.session.commit()
        await self.session.refresh(new_config)

        return self._config_model_to_pydantic(new_config)

    async def rollback_agent_model_config(self, agent_id: str) -> AgentModelConfig | None:
        """
        Rollback to the previous model configuration.
        Marks current config as inactive and reactivates the previous version.
        """
        # Get current active version
        current = await self.get_agent_model_config(agent_id)
        if not current or current.version == 1:
            return None  # Nothing to roll back to

        # Get previous version
        stmt = (
            select(AgentModelConfigModel)
            .where(
                and_(
                    AgentModelConfigModel.agent_id == agent_id,
                    AgentModelConfigModel.version == current.version - 1
                )
            )
        )
        result = await self.session.execute(stmt)
        previous = result.scalar_one_or_none()

        if not previous:
            return None

        # Mark current as inactive
        stmt = (
            update(AgentModelConfigModel)
            .where(AgentModelConfigModel.id == str(current.id))  # Convert UUID to string for SQLite
            .values(active=False, updated_at=datetime.utcnow())
        )
        await self.session.execute(stmt)

        # Reactivate previous version
        stmt = (
            update(AgentModelConfigModel)
            .where(AgentModelConfigModel.id == previous.id)  # previous is SQLAlchemy model, already string
            .values(active=True, updated_at=datetime.utcnow())
        )
        await self.session.execute(stmt)
        await self.session.commit()

        # Refresh the previous object to get updated state
        await self.session.refresh(previous)

        return self._config_model_to_pydantic(previous)

    async def get_approved_models(self, provider: str | None = None) -> list[ApprovedModel]:
        """Get all approved models, optionally filtered by provider"""
        stmt = select(ApprovedModelProviderModel).where(
            ApprovedModelProviderModel.approved == True
        )

        if provider:
            stmt = stmt.where(ApprovedModelProviderModel.provider == provider)

        stmt = stmt.order_by(
            ApprovedModelProviderModel.provider,
            ApprovedModelProviderModel.model_name
        )

        result = await self.session.execute(stmt)
        models = result.scalars().all()

        return [self._approved_model_to_pydantic(m) for m in models]

    async def is_model_approved(self, provider: str, model_name: str) -> bool:
        """Check if a specific model is approved"""
        stmt = select(ApprovedModelProviderModel).where(
            and_(
                ApprovedModelProviderModel.provider == provider,
                ApprovedModelProviderModel.model_name == model_name,
                ApprovedModelProviderModel.approved == True
            )
        )
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        return model is not None

    async def get_model_details(self, provider: str, model_name: str) -> ApprovedModel | None:
        """Get details for a specific approved model"""
        stmt = select(ApprovedModelProviderModel).where(
            and_(
                ApprovedModelProviderModel.provider == provider,
                ApprovedModelProviderModel.model_name == model_name,
                ApprovedModelProviderModel.approved == True
            )
        )
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()

        if not model:
            return None

        return self._approved_model_to_pydantic(model)

    def _config_model_to_pydantic(self, model: AgentModelConfigModel) -> AgentModelConfig:
        """Convert SQLAlchemy model to Pydantic model"""
        return AgentModelConfig(
            id=model.id,
            agent_id=model.agent_id,
            nickname=model.nickname,
            provider=model.provider,
            model_name=model.model_name,
            temperature=model.temperature,
            max_tokens=model.max_tokens,
            model_params=model.model_params or {},
            version=model.version,
            active=model.active,
            created_at=model.created_at,
            updated_at=model.updated_at,
            created_by=model.created_by,
            updated_by=model.updated_by,
        )

    def _approved_model_to_pydantic(self, model: ApprovedModelProviderModel) -> ApprovedModel:
        """Convert SQLAlchemy model to Pydantic model"""
        return ApprovedModel(
            id=model.id,
            provider=model.provider,
            model_name=model.model_name,
            model_display_name=model.model_display_name,
            mode=model.mode,
            context_window=model.context_window,
            supports_function_calling=model.supports_function_calling,
            approved=model.approved,
            version=model.version,
            deprecated=model.deprecated,
            replacement_model_id=model.replacement_model_id,
            cost_per_1k_input=float(model.cost_per_1k_input) if model.cost_per_1k_input else None,
            cost_per_1k_output=float(model.cost_per_1k_output) if model.cost_per_1k_output else None,
            default_params=model.default_params or {},
            description=model.description,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )
