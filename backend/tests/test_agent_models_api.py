"""
Integration tests for Agent Model Configuration API endpoints
Tests the REST API for model management, including validation and reload mechanisms
"""

import pytest
from uuid import uuid4
from datetime import datetime
from httpx import AsyncClient, ASGITransport
from unittest.mock import patch, MagicMock, AsyncMock
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import StaticPool
from sqlalchemy.dialects.postgresql import JSONB, UUID as PGUUID
from sqlalchemy import JSON, String
from sqlalchemy.types import TypeDecorator, CHAR

from backend.models.base import Base
from backend.repositories.agent_model_repository import (
    AgentModelConfigModel,
    ApprovedModelProviderModel,
)
from backend.api.main import app
from backend.repositories.task_repository import get_db_session


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
                # Remove PostgreSQL-specific server defaults (NOW(), gen_random_uuid(), etc.)
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
async def test_client(test_session):
    """Create test HTTP client with database override"""
    async def override_get_db_session():
        yield test_session

    app.dependency_overrides[get_db_session] = override_get_db_session

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client

    app.dependency_overrides.clear()


@pytest.fixture
async def seed_approved_models(test_session):
    """Seed database with approved models"""
    now = datetime.utcnow()
    models = [
        ApprovedModelProviderModel(
            id=str(uuid4()),  # Generate UUID for SQLite
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
        id=str(uuid4()),  # Generate UUID for SQLite
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
    """Tests for GET /api/agents/{agent_id}/model endpoint"""

    async def test_get_existing_config(self, test_client, seed_agent_config, seed_approved_models):
        """Should return current model config for agent"""
        response = await test_client.get("/api/agents/agent_a/model")

        assert response.status_code == 200
        data = response.json()

        assert data["agent_id"] == "agent_a"
        assert data["nickname"] == "bob"
        assert data["provider"] == "openai"
        assert data["model_name"] == "gpt-4o-mini"
        assert data["model_display_name"] == "GPT-4o Mini"
        assert data["temperature"] == 0.7
        assert data["max_tokens"] == 2000
        assert data["version"] == 1

    async def test_get_nonexistent_config(self, test_client, seed_approved_models):
        """Should return 404 for nonexistent agent"""
        response = await test_client.get("/api/agents/agent_xyz/model")

        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    async def test_get_config_includes_model_details(self, test_client, seed_agent_config, seed_approved_models):
        """Should include model display name and details"""
        response = await test_client.get("/api/agents/agent_a/model")

        assert response.status_code == 200
        data = response.json()

        # Should have model display name from approved_models_provider
        assert data["model_display_name"] == "GPT-4o Mini"
        assert data["provider"] == "openai"


@pytest.mark.asyncio
class TestUpdateAgentModelConfig:
    """Tests for PATCH /api/agents/{agent_id}/model endpoint"""

    async def test_update_to_different_provider(self, test_client, seed_agent_config, seed_approved_models):
        """Should successfully update agent to Anthropic Claude"""
        with patch("backend.api.routes.agent_models._reload_agent_with_new_model") as mock_reload:
            mock_reload.return_value = None  # Successful reload

            response = await test_client.patch(
                "/api/agents/agent_a/model",
                json={
                    "provider": "anthropic",
                    "model_name": "claude-3-5-sonnet-20241022",
                    "temperature": 0.5,
                    "max_tokens": 3000,
                },
            )

            assert response.status_code == 200
            data = response.json()

            assert data["provider"] == "anthropic"
            assert data["model_name"] == "claude-3-5-sonnet-20241022"
            assert data["model_display_name"] == "Claude 3.5 Sonnet"
            assert data["temperature"] == 0.5
            assert data["max_tokens"] == 3000
            assert data["version"] == 2  # Incremented

            # Should have called reload
            mock_reload.assert_called_once()

    async def test_update_to_different_openai_model(self, test_client, test_session, seed_agent_config, seed_approved_models):
        """Should successfully update to different OpenAI model"""
        # Add gpt-4o to approved models
        test_session.add(
            ApprovedModelProviderModel(
                provider="openai",
                model_name="gpt-4o",
                model_display_name="GPT-4o",
                approved=True,
            )
        )
        await test_session.commit()

        with patch("backend.api.routes.agent_models._reload_agent_with_new_model") as mock_reload:
            mock_reload.return_value = None

            response = await test_client.patch(
                "/api/agents/agent_a/model",
                json={
                    "provider": "openai",
                    "model_name": "gpt-4o",
                },
            )

            assert response.status_code == 200
            data = response.json()

            assert data["model_name"] == "gpt-4o"
            assert data["version"] == 2

    async def test_update_with_unapproved_model_fails(self, test_client, seed_agent_config, seed_approved_models):
        """Should reject unapproved model"""
        response = await test_client.patch(
            "/api/agents/agent_a/model",
            json={
                "provider": "openai",
                "model_name": "gpt-4-unapproved",
            },
        )

        assert response.status_code == 400
        assert "not approved" in response.json()["detail"].lower()

    async def test_update_with_nonexistent_model_fails(self, test_client, seed_agent_config, seed_approved_models):
        """Should reject nonexistent model"""
        response = await test_client.patch(
            "/api/agents/agent_a/model",
            json={
                "provider": "openai",
                "model_name": "nonexistent-model",
            },
        )

        assert response.status_code == 400
        assert "not approved" in response.json()["detail"].lower()

    async def test_update_creates_new_version(self, test_client, test_session, seed_agent_config, seed_approved_models):
        """Should create new version and mark old as inactive"""
        with patch("backend.api.routes.agent_models._reload_agent_with_new_model") as mock_reload:
            mock_reload.return_value = None

            # First update
            response = await test_client.patch(
                "/api/agents/agent_a/model",
                json={
                    "provider": "anthropic",
                    "model_name": "claude-3-5-haiku-20241022",
                },
            )

            assert response.status_code == 200
            assert response.json()["version"] == 2

            # Check database has 2 versions
            from sqlalchemy import select
            result = await test_session.execute(
                select(AgentModelConfigModel)
                .where(AgentModelConfigModel.agent_id == "agent_a")
                .order_by(AgentModelConfigModel.version)
            )
            configs = result.scalars().all()

            assert len(configs) == 2
            assert configs[0].version == 1
            assert configs[0].active is False  # Old version inactive
            assert configs[1].version == 2
            assert configs[1].active is True  # New version active

    async def test_update_rollback_on_reload_failure(self, test_client, seed_agent_config, seed_approved_models):
        """Should rollback config if agent reload fails"""
        with patch("backend.api.routes.agent_models._reload_agent_with_new_model") as mock_reload:
            mock_reload.side_effect = Exception("Reload failed")

            response = await test_client.patch(
                "/api/agents/agent_a/model",
                json={
                    "provider": "anthropic",
                    "model_name": "claude-3-5-sonnet-20241022",
                },
            )

            assert response.status_code == 500
            assert "failed to reload" in response.json()["detail"].lower()

        # Verify config was rolled back
        response = await test_client.get("/api/agents/agent_a/model")
        assert response.status_code == 200
        data = response.json()

        # Should still be on original config
        assert data["provider"] == "openai"
        assert data["model_name"] == "gpt-4o-mini"
        assert data["version"] == 1

    async def test_update_nonexistent_agent_creates_config(self, test_client, seed_approved_models):
        """Should create new config for agent without existing config"""
        with patch("backend.api.routes.agent_models._reload_agent_with_new_model") as mock_reload:
            mock_reload.return_value = None

            response = await test_client.patch(
                "/api/agents/agent_new/model",
                json={
                    "provider": "openai",
                    "model_name": "gpt-4o-mini",
                },
            )

            assert response.status_code == 200
            data = response.json()

            assert data["agent_id"] == "agent_new"
            assert data["version"] == 1
            assert data["active"] is True


@pytest.mark.asyncio
class TestGetApprovedModels:
    """Tests for GET /api/models/approved endpoint"""

    async def test_get_all_approved_models(self, test_client, seed_approved_models):
        """Should return all approved models"""
        response = await test_client.get("/api/models/approved")

        assert response.status_code == 200
        data = response.json()

        assert "models" in data
        models = data["models"]

        # Should have 3 approved models (excluding unapproved one)
        assert len(models) == 3

        providers = {m["provider"] for m in models}
        assert providers == {"openai", "anthropic"}

        # Should not include unapproved model
        model_names = {m["model_name"] for m in models}
        assert "gpt-4-unapproved" not in model_names

    async def test_filter_by_provider_openai(self, test_client, seed_approved_models):
        """Should filter models by OpenAI provider"""
        response = await test_client.get("/api/models/approved?provider=openai")

        assert response.status_code == 200
        data = response.json()

        models = data["models"]
        assert len(models) == 1
        assert all(m["provider"] == "openai" for m in models)

    async def test_filter_by_provider_anthropic(self, test_client, seed_approved_models):
        """Should filter models by Anthropic provider"""
        response = await test_client.get("/api/models/approved?provider=anthropic")

        assert response.status_code == 200
        data = response.json()

        models = data["models"]
        assert len(models) == 2
        assert all(m["provider"] == "anthropic" for m in models)

    async def test_approved_models_include_metadata(self, test_client, seed_approved_models):
        """Should include model metadata in response"""
        response = await test_client.get("/api/models/approved")

        assert response.status_code == 200
        data = response.json()

        # Find Claude Sonnet model
        claude_model = next(
            m for m in data["models"]
            if m["model_name"] == "claude-3-5-sonnet-20241022"
        )

        assert claude_model["model_display_name"] == "Claude 3.5 Sonnet"
        assert claude_model["context_window"] == 200000
        assert claude_model["supports_function_calling"] is True
        assert claude_model["mode"] == "reasoning"


@pytest.mark.asyncio
class TestAgentReloadMechanism:
    """Tests for agent reload mechanism"""

    async def test_reload_updates_agent_instance(self, test_client, seed_agent_config, seed_approved_models):
        """Should update agent's model_config and recreate graph"""
        with patch("backend.api.routes.agent_models.AgentRegistry") as mock_registry:
            # Mock agent with graph
            mock_agent = MagicMock()
            mock_agent.model_config = None
            mock_agent.create_graph = MagicMock(return_value="new_graph")
            mock_registry.get_agent.return_value = mock_agent

            response = await test_client.patch(
                "/api/agents/agent_a/model",
                json={
                    "provider": "anthropic",
                    "model_name": "claude-3-5-sonnet-20241022",
                },
            )

            assert response.status_code == 200

            # Should have updated agent's model_config
            assert mock_agent.model_config is not None
            assert mock_agent.model_config.provider == "anthropic"
            assert mock_agent.model_config.model_name == "claude-3-5-sonnet-20241022"

            # Should have recreated graph
            mock_agent.create_graph.assert_called_once()
            assert mock_agent.graph == "new_graph"

    async def test_reload_broadcasts_websocket_event(self, test_client, seed_agent_config, seed_approved_models):
        """Should broadcast model update via WebSocket"""
        with patch("backend.api.routes.agent_models._reload_agent_with_new_model") as mock_reload, \
             patch("backend.api.routes.agent_models.broadcast_agent_model_update") as mock_broadcast:

            mock_reload.return_value = None

            response = await test_client.patch(
                "/api/agents/agent_a/model",
                json={
                    "provider": "anthropic",
                    "model_name": "claude-3-5-haiku-20241022",
                },
            )

            assert response.status_code == 200

            # Should have broadcasted update
            mock_broadcast.assert_called_once()
            args = mock_broadcast.call_args[0]
            assert args[0] == "agent_a"  # agent_id


@pytest.mark.asyncio
class TestValidationAndErrorHandling:
    """Tests for input validation and error handling"""

    async def test_missing_required_fields(self, test_client, seed_agent_config):
        """Should reject request with missing required fields"""
        response = await test_client.patch(
            "/api/agents/agent_a/model",
            json={
                "provider": "openai",
                # Missing model_name
            },
        )

        assert response.status_code == 422  # Validation error

    async def test_invalid_temperature_range(self, test_client, seed_agent_config, seed_approved_models):
        """Should reject invalid temperature values"""
        # Temperature > 1
        response = await test_client.patch(
            "/api/agents/agent_a/model",
            json={
                "provider": "openai",
                "model_name": "gpt-4o-mini",
                "temperature": 1.5,
            },
        )

        assert response.status_code == 422

        # Temperature < 0
        response = await test_client.patch(
            "/api/agents/agent_a/model",
            json={
                "provider": "openai",
                "model_name": "gpt-4o-mini",
                "temperature": -0.1,
            },
        )

        assert response.status_code == 422

    async def test_invalid_max_tokens(self, test_client, seed_agent_config, seed_approved_models):
        """Should reject invalid max_tokens values"""
        response = await test_client.patch(
            "/api/agents/agent_a/model",
            json={
                "provider": "openai",
                "model_name": "gpt-4o-mini",
                "max_tokens": -100,
            },
        )

        assert response.status_code == 422

    async def test_database_error_handling(self, test_client, seed_agent_config):
        """Should handle database errors gracefully"""
        with patch("backend.api.routes.agent_models.AgentModelRepository") as mock_repo:
            mock_repo.return_value.get_agent_model_config.side_effect = Exception("Database error")

            response = await test_client.get("/api/agents/agent_a/model")

            assert response.status_code == 500
            assert "error" in response.json()["detail"].lower()
