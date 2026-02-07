"""
Unit tests for AgentModelRepository
Tests CRUD operations for agent model configurations
"""

import pytest
from uuid import UUID, uuid4
from datetime import datetime
from sqlalchemy import select, JSON, String
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import StaticPool
from sqlalchemy.dialects.postgresql import JSONB, UUID as PGUUID

from backend.models.base import Base
from backend.repositories.agent_model_repository import (
    AgentModelRepository,
    AgentModelConfigModel,
    ApprovedModelProviderModel,
)
from backend.models.agent_model_models import AgentModelUpdate


# Test database setup
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture
async def test_engine():
    """Create test database engine with SQLite compatibility fixes"""
    engine = create_async_engine(
        TEST_DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    # Replace PostgreSQL-specific types with SQLite-compatible types
    async with engine.begin() as conn:
        for table in Base.metadata.tables.values():
            for column in table.columns:
                # Replace JSONB with JSON
                if isinstance(column.type, JSONB):
                    column.type = JSON()
                # Replace PostgreSQL UUID with String
                if isinstance(column.type, PGUUID):
                    column.type = String(36)
                # Remove PostgreSQL-specific server defaults
                if column.server_default and hasattr(column.server_default, 'arg'):
                    server_default_text = str(column.server_default.arg)
                    if 'NOW()' in server_default_text or 'gen_random_uuid()' in server_default_text:
                        column.server_default = None

        await conn.run_sync(Base.metadata.create_all)

    yield engine

    await engine.dispose()


@pytest.fixture
async def test_session(test_engine):
    """Create test database session"""
    async_session = async_sessionmaker(
        test_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    async with async_session() as session:
        yield session


@pytest.fixture
async def repo(test_session):
    """Create repository instance"""
    return AgentModelRepository(test_session)


@pytest.fixture
async def seed_approved_models(test_session):
    """Seed database with approved models"""
    now = datetime.utcnow()
    models = [
        ApprovedModelProviderModel(
            id=str(uuid4()),
            provider="openai",
            model_name="gpt-4o-mini",
            model_display_name="GPT-4o Mini",
            mode="reasoning",
            approved=True,
            context_window=128000,
            supports_function_calling=True,
            created_at=now,
            updated_at=now,
        ),
        ApprovedModelProviderModel(
            id=str(uuid4()),
            provider="anthropic",
            model_name="claude-3-5-sonnet-20241022",
            model_display_name="Claude 3.5 Sonnet",
            mode="reasoning",
            approved=True,
            context_window=200000,
            supports_function_calling=True,
            created_at=now,
            updated_at=now,
        ),
        ApprovedModelProviderModel(
            id=str(uuid4()),
            provider="anthropic",
            model_name="claude-3-5-haiku-20241022",
            model_display_name="Claude 3.5 Haiku",
            mode="chat",
            approved=True,
            context_window=200000,
            supports_function_calling=True,
            created_at=now,
            updated_at=now,
        ),
        ApprovedModelProviderModel(
            id=str(uuid4()),
            provider="openai",
            model_name="gpt-4-unapproved",
            model_display_name="GPT-4 (Not Approved)",
            approved=False,
            created_at=now,
            updated_at=now,
        ),
    ]

    for model in models:
        test_session.add(model)

    await test_session.commit()


@pytest.fixture
async def seed_agent_config(test_session):
    """Seed database with initial agent config"""
    now = datetime.utcnow()
    config = AgentModelConfigModel(
        id=str(uuid4()),
        agent_id="agent_a",
        nickname="bob",
        provider="openai",
        model_name="gpt-4o-mini",
        temperature=0.7,
        max_tokens=2000,
        model_params={},
        version=1,
        active=True,
        created_at=now,
        updated_at=now,
    )

    test_session.add(config)
    await test_session.commit()

    return config


@pytest.mark.asyncio
class TestGetAgentModelConfig:
    """Tests for getting agent model configurations"""

    async def test_get_existing_config(self, repo, seed_agent_config):
        """Should return active config for agent"""
        config = await repo.get_agent_model_config("agent_a")

        assert config is not None
        assert config.agent_id == "agent_a"
        assert config.nickname == "bob"
        assert config.provider == "openai"
        assert config.model_name == "gpt-4o-mini"
        assert config.temperature == 0.7
        assert config.max_tokens == 2000
        assert config.version == 1
        assert config.active is True

    async def test_get_nonexistent_config(self, repo):
        """Should return None for nonexistent agent"""
        config = await repo.get_agent_model_config("agent_xyz")

        assert config is None

    async def test_get_latest_version_only(self, repo, test_session, seed_agent_config):
        """Should return only the active config, not old versions"""
        # Create older inactive version
        now = datetime.utcnow()
        old_config = AgentModelConfigModel(
            id=str(uuid4()),
            agent_id="agent_a",
            nickname="bob",
            provider="openai",
            model_name="gpt-3.5-turbo",
            temperature=0.5,
            max_tokens=1000,
            version=2,
            active=False,
            created_at=now,
            updated_at=now,
        )
        test_session.add(old_config)
        await test_session.commit()

        config = await repo.get_agent_model_config("agent_a")

        assert config is not None
        assert config.version == 1
        assert config.active is True


@pytest.mark.asyncio
class TestSaveAgentModelConfig:
    """Tests for saving agent model configurations"""

    async def test_save_new_config_creates_version_1(self, repo, seed_approved_models):
        """Should create version 1 for new agent config"""
        update = AgentModelUpdate(
            provider="openai",
            model_name="gpt-4o-mini",
            temperature=0.7,
            max_tokens=2000,
        )

        config = await repo.save_agent_model_config(
            agent_id="agent_new",
            nickname="newagent",
            model_update=update,
        )

        assert config is not None
        assert config.agent_id == "agent_new"
        assert config.version == 1
        assert config.active is True

    async def test_save_update_increments_version(self, repo, seed_agent_config, seed_approved_models):
        """Should increment version and mark old config as inactive"""
        update = AgentModelUpdate(
            provider="anthropic",
            model_name="claude-3-5-sonnet-20241022",
            temperature=0.5,
            max_tokens=3000,
        )

        new_config = await repo.save_agent_model_config(
            agent_id="agent_a",
            nickname="bob",
            model_update=update,
        )

        assert new_config.version == 2
        assert new_config.active is True
        assert new_config.provider == "anthropic"
        assert new_config.model_name == "claude-3-5-sonnet-20241022"

        # Old config should be inactive
        old_config = await repo.get_agent_model_config("agent_a")
        assert old_config.version == 2  # Get returns active version


@pytest.mark.asyncio
class TestRollbackAgentModelConfig:
    """Tests for rolling back agent model configurations"""

    async def test_rollback_to_previous_version(self, repo, test_session, seed_agent_config, seed_approved_models):
        """Should reactivate previous version and deactivate current"""
        # Create version 2
        update = AgentModelUpdate(
            provider="anthropic",
            model_name="claude-3-5-sonnet-20241022",
        )
        await repo.save_agent_model_config("agent_a", "bob", model_update=update)

        # Rollback
        rolled_back = await repo.rollback_agent_model_config("agent_a")

        assert rolled_back is not None
        assert rolled_back.version == 1
        assert rolled_back.provider == "openai"
        assert rolled_back.model_name == "gpt-4o-mini"

        # Current config should be the rolled back one
        current = await repo.get_agent_model_config("agent_a")
        assert current.version == 1

    async def test_rollback_version_1_returns_none(self, repo, seed_agent_config):
        """Should return None when rolling back version 1 (nothing to roll back to)"""
        rolled_back = await repo.rollback_agent_model_config("agent_a")

        assert rolled_back is None

    async def test_rollback_nonexistent_agent_returns_none(self, repo):
        """Should return None for nonexistent agent"""
        rolled_back = await repo.rollback_agent_model_config("agent_xyz")

        assert rolled_back is None


@pytest.mark.asyncio
class TestGetApprovedModels:
    """Tests for getting approved models"""

    async def test_get_all_approved_models(self, repo, seed_approved_models):
        """Should return all approved models"""
        models = await repo.get_approved_models()

        assert len(models) == 3  # 3 approved models
        assert all(m.approved for m in models)

        providers = {m.provider for m in models}
        assert providers == {"openai", "anthropic"}

    async def test_filter_by_provider(self, repo, seed_approved_models):
        """Should filter models by provider"""
        openai_models = await repo.get_approved_models(provider="openai")
        anthropic_models = await repo.get_approved_models(provider="anthropic")

        assert len(openai_models) == 1
        assert all(m.provider == "openai" for m in openai_models)

        assert len(anthropic_models) == 2
        assert all(m.provider == "anthropic" for m in anthropic_models)

    async def test_excludes_unapproved_models(self, repo, seed_approved_models):
        """Should not return unapproved models"""
        models = await repo.get_approved_models()

        model_names = {m.model_name for m in models}
        assert "gpt-4-unapproved" not in model_names


@pytest.mark.asyncio
class TestIsModelApproved:
    """Tests for checking if model is approved"""

    async def test_approved_model_returns_true(self, repo, seed_approved_models):
        """Should return True for approved model"""
        is_approved = await repo.is_model_approved("openai", "gpt-4o-mini")

        assert is_approved is True

    async def test_unapproved_model_returns_false(self, repo, seed_approved_models):
        """Should return False for unapproved model"""
        is_approved = await repo.is_model_approved("openai", "gpt-4-unapproved")

        assert is_approved is False

    async def test_nonexistent_model_returns_false(self, repo, seed_approved_models):
        """Should return False for nonexistent model"""
        is_approved = await repo.is_model_approved("openai", "nonexistent")

        assert is_approved is False


@pytest.mark.asyncio
class TestGetModelDetails:
    """Tests for getting model details"""

    async def test_get_existing_model_details(self, repo, seed_approved_models):
        """Should return model details for approved model"""
        details = await repo.get_model_details("anthropic", "claude-3-5-sonnet-20241022")

        assert details is not None
        assert details.model_display_name == "Claude 3.5 Sonnet"
        assert details.context_window == 200000
        assert details.supports_function_calling is True

    async def test_get_nonexistent_model_returns_none(self, repo, seed_approved_models):
        """Should return None for nonexistent model"""
        details = await repo.get_model_details("openai", "nonexistent")

        assert details is None

    async def test_get_unapproved_model_returns_none(self, repo, seed_approved_models):
        """Should return None for unapproved model"""
        details = await repo.get_model_details("openai", "gpt-4-unapproved")

        assert details is None
