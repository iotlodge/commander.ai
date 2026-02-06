"""
Pytest configuration and shared fixtures for commander.ai tests

This file is automatically loaded by pytest and makes fixtures available
to all test files without needing to import them.
"""

import asyncio
import pytest
from uuid import UUID, uuid4
from typing import AsyncGenerator, Dict
from unittest.mock import MagicMock, AsyncMock
from httpx import AsyncClient, ASGITransport

from backend.core.config import get_settings
from backend.memory.document_store import DocumentStore
from backend.core.dependencies import reset_document_store
from backend.core.database import get_session_maker, close_db_connections
from backend.auth.models import User, Base as AuthBase
from backend.auth.security import get_password_hash, create_access_token
from sqlalchemy.ext.asyncio import AsyncSession


# Test user ID (consistent across all tests)
TEST_USER_ID = UUID("00000000-0000-0000-0000-000000000001")


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def test_user_id() -> UUID:
    """Fixture providing consistent test user ID"""
    return TEST_USER_ID


@pytest.fixture
def random_user_id() -> UUID:
    """Fixture providing random user ID for tests needing isolation"""
    return uuid4()


@pytest.fixture
def mock_settings():
    """Mock settings with test configuration"""
    settings = MagicMock()
    settings.openai_api_key = "test_openai_key"
    settings.tavily_api_key = "test_tavily_key"
    settings.openai_embedding_model = "text-embedding-ada-002"
    settings.tavily_max_results = 10
    settings.tavily_rate_limit_per_minute = 60
    settings.tavily_timeout_seconds = 30
    settings.tavily_retry_attempts = 3
    settings.web_cache_ttl_hours = 24
    settings.web_cache_news_ttl_hours = 1
    settings.web_cache_similarity_threshold = 0.85
    settings.web_cache_collection_prefix = "web_cache"
    settings.qdrant_url = "http://localhost:6333"
    settings.qdrant_api_key = None
    return settings


@pytest.fixture
async def document_store() -> AsyncGenerator[DocumentStore, None]:
    """
    Fixture providing DocumentStore instance for tests

    Note: This creates a real DocumentStore instance. For unit tests,
    prefer mocking. Use this only for integration tests.
    """
    # Reset singleton before test
    reset_document_store()

    store = DocumentStore()
    await store.connect()

    yield store

    # Cleanup
    await store.disconnect()
    reset_document_store()


@pytest.fixture
def mock_document_store():
    """Mock DocumentStore for unit tests (no real connections)"""
    store = MagicMock(spec=DocumentStore)
    store.qdrant_client = AsyncMock()
    store.openai_client = AsyncMock()
    store.embedding_dimension = 1536

    # Mock common methods
    store.connect = AsyncMock()
    store.disconnect = AsyncMock()
    store.create_collection = AsyncMock()
    store.delete_collection = AsyncMock()
    store.generate_embedding = AsyncMock(return_value=[0.1] * 1536)
    store.store_chunks = AsyncMock()
    store.search_collection = AsyncMock(return_value=[])
    store.search_all_collections = AsyncMock(return_value=[])

    return store


@pytest.fixture
def mock_tavily_client():
    """Mock Tavily client for testing web search"""
    client = AsyncMock()
    client.search = AsyncMock(return_value={
        "results": [
            {
                "title": "Test Result 1",
                "content": "Test content 1",
                "url": "https://example.com/1",
                "score": 0.95,
            },
            {
                "title": "Test Result 2",
                "content": "Test content 2",
                "url": "https://example.com/2",
                "score": 0.90,
            },
        ],
        "answer": "Test answer",
    })
    return client


@pytest.fixture
def sample_search_results():
    """Sample search results for testing"""
    return [
        {
            "title": "Python Async Programming",
            "content": "Guide to async programming in Python",
            "url": "https://example.com/async",
            "score": 0.95,
        },
        {
            "title": "FastAPI Tutorial",
            "content": "Building APIs with FastAPI",
            "url": "https://example.com/fastapi",
            "score": 0.90,
        },
        {
            "title": "LangGraph Guide",
            "content": "Agent orchestration with LangGraph",
            "url": "https://example.com/langgraph",
            "score": 0.85,
        },
    ]


@pytest.fixture
def sample_document_chunks():
    """Sample document chunks for testing"""
    from backend.models.document_models import ChunkCreate

    return [
        ChunkCreate(
            user_id=TEST_USER_ID,
            collection_id=uuid4(),
            vector_id=uuid4(),
            content="This is chunk 1",
            chunk_index=0,
            source_type="web",
            source_file_path="",
            file_name="test_doc",
            metadata={"url": "https://example.com/1"},
        ),
        ChunkCreate(
            user_id=TEST_USER_ID,
            collection_id=uuid4(),
            vector_id=uuid4(),
            content="This is chunk 2",
            chunk_index=1,
            source_type="web",
            source_file_path="",
            file_name="test_doc",
            metadata={"url": "https://example.com/2"},
        ),
    ]


@pytest.fixture
def mock_task_callback():
    """Mock task callback for agent progress tracking"""
    callback = AsyncMock()
    callback.on_progress_update = AsyncMock()
    callback.on_node_enter = AsyncMock()
    callback.on_node_exit = AsyncMock()
    callback.on_error = AsyncMock()
    return callback


@pytest.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Fixture providing database session for tests

    Creates tables before tests and drops them after
    """
    from sqlalchemy import create_engine
    from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

    # Use test database URL or in-memory
    settings = get_settings()
    engine = create_async_engine(
        settings.database_url,
        echo=False,
    )

    # Create tables
    async with engine.begin() as conn:
        await conn.run_sync(AuthBase.metadata.create_all)

    # Create session
    async_session = async_sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    async with async_session() as session:
        yield session
        await session.rollback()

    # Drop tables
    async with engine.begin() as conn:
        await conn.run_sync(AuthBase.metadata.drop_all)

    await engine.dispose()


@pytest.fixture
async def test_client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """
    Fixture providing async HTTP client for API testing

    Overrides database dependency to use test database
    """
    from backend.api.main import app
    from backend.core.database import get_db_session

    # Override database dependency
    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db_session] = override_get_db

    # Create test client
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client

    # Clean up overrides
    app.dependency_overrides.clear()


@pytest.fixture
async def test_user(db_session: AsyncSession) -> User:
    """
    Fixture providing test user

    Creates a user in the test database
    """
    user = User(
        email="test@example.com",
        hashed_password=get_password_hash("testpassword123"),
        is_active=True,
        is_superuser=False,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.fixture
async def other_user(db_session: AsyncSession) -> User:
    """
    Fixture providing another test user for authorization tests
    """
    user = User(
        email="other@example.com",
        hashed_password=get_password_hash("otherpassword123"),
        is_active=True,
        is_superuser=False,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.fixture
def auth_headers(test_user: User) -> Dict[str, str]:
    """
    Fixture providing authentication headers with JWT token

    Creates access token for test_user
    """
    access_token = create_access_token(subject=str(test_user.id), token_type="access")
    return {"Authorization": f"Bearer {access_token}"}


@pytest.fixture
def other_user_auth_headers(other_user: User) -> Dict[str, str]:
    """
    Fixture providing authentication headers for other_user
    """
    access_token = create_access_token(subject=str(other_user.id), token_type="access")
    return {"Authorization": f"Bearer {access_token}"}


@pytest.fixture
async def other_user_task_id(
    test_client: AsyncClient,
    other_user_auth_headers: Dict[str, str],
) -> str:
    """
    Fixture providing task ID created by other_user

    Used for testing cross-user authorization
    """
    response = await test_client.post(
        "/api/tasks",
        json={
            "user_id": str(uuid4()),
            "agent_id": "agent_a",
            "thread_id": str(uuid4()),
            "command": "other user task",
        },
        headers=other_user_auth_headers,
    )
    return response.json()["id"]


# Pytest configuration
def pytest_configure(config):
    """Configure pytest with custom markers"""
    config.addinivalue_line(
        "markers", "integration: mark test as integration test (requires external services)"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow running"
    )
    config.addinivalue_line(
        "markers", "api: mark test as API integration test"
    )
    config.addinivalue_line(
        "markers", "auth: mark test as authentication/authorization test"
    )
