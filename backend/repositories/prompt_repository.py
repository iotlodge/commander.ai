"""
Prompt repository for database operations
"""

from datetime import datetime
from uuid import UUID

from sqlalchemy import select, update, desc, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import Column, String, Text, DateTime, Boolean
from sqlalchemy.dialects.postgresql import UUID as PGUUID, JSONB

from backend.models.base import Base
from backend.models.prompt_models import AgentPrompt, PromptCreate, PromptUpdate


class AgentPromptModel(Base):
    """SQLAlchemy model for agent_prompts table"""

    __tablename__ = "agent_prompts"

    id = Column(PGUUID(as_uuid=True), primary_key=True, server_default="gen_random_uuid()")
    agent_id = Column(String(50), nullable=False, index=True)
    nickname = Column(String(50), nullable=False)
    description = Column(Text, nullable=False)
    prompt_text = Column(Text, nullable=False)
    active = Column(Boolean, nullable=False, server_default="true")
    prompt_type = Column(String(50), nullable=False, server_default="'system'")
    var_data = Column("variables", JSONB, nullable=False, server_default="{}")  # Renamed to avoid potential conflicts
    created_at = Column(DateTime, nullable=False, server_default="NOW()")
    updated_at = Column(DateTime, nullable=False, server_default="NOW()", onupdate=func.now())


class PromptRepository:
    """Data access layer for agent prompts"""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_prompt(self, prompt: PromptCreate) -> AgentPrompt:
        """Create new prompt in database"""
        model = AgentPromptModel(
            agent_id=prompt.agent_id,
            nickname=prompt.nickname,
            description=prompt.description,
            prompt_text=prompt.prompt_text,
            active=prompt.active,
            prompt_type=prompt.prompt_type,
            var_data=prompt.variables,
        )
        self.session.add(model)
        await self.session.commit()
        await self.session.refresh(model)

        return self._model_to_pydantic(model)

    async def get_prompt(self, prompt_id: UUID) -> AgentPrompt | None:
        """Get prompt by ID"""
        stmt = select(AgentPromptModel).where(AgentPromptModel.id == prompt_id)
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()

        if not model:
            return None

        return self._model_to_pydantic(model)

    async def get_active_prompts(self, agent_id: str) -> list[AgentPrompt]:
        """Get all active prompts for an agent"""
        stmt = (
            select(AgentPromptModel)
            .where(AgentPromptModel.agent_id == agent_id, AgentPromptModel.active == True)
            .order_by(desc(AgentPromptModel.created_at))
        )
        result = await self.session.execute(stmt)
        models = result.scalars().all()

        return [self._model_to_pydantic(m) for m in models]

    async def update_prompt(self, prompt_id: UUID, prompt_update: PromptUpdate) -> AgentPrompt:
        """Update prompt"""
        update_data = {}
        if prompt_update.prompt_text is not None:
            update_data["prompt_text"] = prompt_update.prompt_text
        if prompt_update.active is not None:
            update_data["active"] = prompt_update.active
        if prompt_update.variables is not None:
            update_data["var_data"] = prompt_update.variables

        if update_data:
            update_data["updated_at"] = datetime.utcnow()
            stmt = (
                update(AgentPromptModel)
                .where(AgentPromptModel.id == prompt_id)
                .values(**update_data)
            )
            await self.session.execute(stmt)
            await self.session.commit()

        return await self.get_prompt(prompt_id)

    def _model_to_pydantic(self, model: AgentPromptModel) -> AgentPrompt:
        """Convert SQLAlchemy model to Pydantic model"""
        return AgentPrompt(
            id=model.id,
            agent_id=model.agent_id,
            nickname=model.nickname,
            description=model.description,
            prompt_text=model.prompt_text,
            active=model.active,
            prompt_type=model.prompt_type,
            variables=model.var_data or {},
            created_at=model.created_at,
            updated_at=model.updated_at,
        )
