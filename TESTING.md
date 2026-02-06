# Testing Guide for commander.ai

> Comprehensive guide for writing and running tests in commander.ai

---

## 🎯 Testing Philosophy

**We test to:**
1. Prevent regressions when adding features
2. Document expected behavior
3. Support confident refactoring
4. Enable rapid debugging

**Coverage targets:**
- Unit tests: 80%+ coverage
- Integration tests: Critical user flows
- API tests: All endpoints

---

## 📁 Test Structure

```
tests/
├── conftest.py              # Shared fixtures (auto-loaded by pytest)
├── __init__.py
├── agents/                  # Agent unit tests
│   ├── test_agent_a.py      # @bob tests
│   ├── test_agent_d.py      # @alice tests
│   └── test_agent_g_chat.py # @chat tests
├── tools/                   # Tool unit tests
│   └── web_search/
│       ├── test_tavily_toolset.py
│       └── test_exceptions.py
├── core/                    # Core functionality tests
│   └── test_dependencies.py
├── jobs/                    # Background job tests
│   └── test_cache_cleanup.py
├── migrations/              # Database migration tests
│   └── test_web_cache_indexes.py
├── integration/             # Integration tests
│   └── test_full_workflow.py
└── api/                     # UI<->Backend integration tests
    ├── test_task_api.py     # REST API endpoints
    └── test_websocket.py    # WebSocket real-time updates
```

---

## 🚀 Running Tests

### Run All Tests

```bash
pytest
```

### Run Specific Test File

```bash
pytest tests/agents/test_agent_g_chat.py
```

### Run Specific Test Class

```bash
pytest tests/agents/test_agent_g_chat.py::TestCreateWebSearchTool
```

### Run Specific Test

```bash
pytest tests/agents/test_agent_g_chat.py::TestCreateWebSearchTool::test_creates_structured_tool
```

### Run with Coverage

```bash
pytest --cov=backend --cov-report=html
open htmlcov/index.html
```

### Run Only Integration Tests

```bash
pytest -m integration
```

### Run Only API Tests

```bash
pytest -m api
```

### Run Fast Tests (Skip Slow)

```bash
pytest -m "not slow"
```

### Run with Verbose Output

```bash
pytest -v
pytest -vv  # Extra verbose
```

---

## ✍️ Writing Tests

### Test Naming Convention

```python
# File naming
test_<module_name>.py

# Class naming
class Test<FeatureName>:
    """Test <feature> functionality"""

# Method naming
def test_<specific_behavior>(self):
    """Test that <expected behavior>"""
```

### Unit Test Template

```python
"""
Unit tests for <module>
Tests <what is being tested>
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

from backend.<module> import <ClassUnderTest>


class Test<Feature>:
    """Test <feature> functionality"""

    @pytest.mark.asyncio
    async def test_<specific_behavior>(self, mock_settings):
        """Test that <expected outcome>"""
        # ARRANGE - Set up test data
        test_input = "sample input"
        expected_output = "expected result"

        # Mock dependencies
        mock_dependency = AsyncMock(return_value=expected_output)

        # ACT - Execute the code under test
        with patch('backend.module.dependency', mock_dependency):
            result = await function_under_test(test_input)

        # ASSERT - Verify the results
        assert result == expected_output
        mock_dependency.assert_called_once_with(test_input)
```

### Integration Test Template

```python
"""
Integration tests for <system>
Tests end-to-end workflows
"""

import pytest
from uuid import uuid4


@pytest.mark.integration
@pytest.mark.asyncio
class Test<WorkflowName>:
    """Test <workflow> end-to-end"""

    async def test_<workflow_scenario>(
        self,
        document_store,  # Real DocumentStore instance
        test_user_id
    ):
        """Test that <workflow> works end-to-end"""
        # ARRANGE - Set up real resources
        collection_id = uuid4()

        # ACT - Execute workflow
        await document_store.create_collection(
            qdrant_collection_name=f"test_{collection_id}",
            user_id=test_user_id
        )

        # ASSERT - Verify results
        # Cleanup happens automatically via fixture
```

### Using Fixtures

```python
# Use shared fixtures from conftest.py
def test_with_fixtures(
    test_user_id,           # Consistent UUID
    mock_settings,          # Mock settings
    mock_document_store,    # Mock DocumentStore
    sample_search_results   # Sample data
):
    """Fixtures are auto-injected by pytest"""
    # Use fixtures without importing
    assert test_user_id is not None
```

---

## 🎭 Common Testing Patterns

### Testing Async Functions

```python
@pytest.mark.asyncio
async def test_async_function():
    """Test async function"""
    result = await async_function()
    assert result == expected
```

### Mocking External Services

```python
@pytest.mark.asyncio
async def test_with_mocked_api(mock_tavily_client):
    """Test with mocked Tavily API"""
    with patch('backend.tools.web_search.tavily_toolset.AsyncTavilyClient') as MockClient:
        MockClient.return_value = mock_tavily_client

        result = await search_function("query")

        mock_tavily_client.search.assert_called_once()
```

### Testing Error Handling

```python
@pytest.mark.asyncio
async def test_handles_error_gracefully():
    """Test that errors are handled gracefully"""
    mock_service = AsyncMock(side_effect=Exception("API failed"))

    with patch('backend.module.service', mock_service):
        result = await function_that_handles_errors()

        # Should return error state, not crash
        assert result.error is not None
        assert "API failed" in str(result.error)
```

### Parameterized Tests

```python
@pytest.mark.parametrize("input,expected", [
    ("test1", "result1"),
    ("test2", "result2"),
    ("test3", "result3"),
])
def test_multiple_cases(input, expected):
    """Test multiple input/output combinations"""
    result = function(input)
    assert result == expected
```

### Testing Database Operations

```python
@pytest.mark.integration
@pytest.mark.asyncio
async def test_database_operation():
    """Test real database operation"""
    from backend.repositories.task_repository import get_session_factory

    session_factory = get_session_factory()
    async with session_factory() as session:
        # Perform database operations
        # Cleanup happens automatically via session rollback
```

---

## 🔧 Available Fixtures

### From `conftest.py`

| Fixture | Description | Type |
|---------|-------------|------|
| `test_user_id` | Consistent test user UUID | UUID |
| `random_user_id` | Random UUID for isolation | UUID |
| `mock_settings` | Mocked settings object | MagicMock |
| `document_store` | Real DocumentStore instance | DocumentStore |
| `mock_document_store` | Mocked DocumentStore | MagicMock |
| `mock_tavily_client` | Mocked Tavily client | AsyncMock |
| `sample_search_results` | Sample web search results | list[dict] |
| `sample_document_chunks` | Sample chunks for testing | list[ChunkCreate] |
| `mock_task_callback` | Mock progress callback | AsyncMock |

---

## 🏷️ Test Markers

Mark tests with decorators to categorize them:

```python
@pytest.mark.integration  # Requires external services
@pytest.mark.slow         # Takes >5 seconds
@pytest.mark.api          # Tests API endpoints
```

Run specific markers:
```bash
pytest -m integration     # Only integration tests
pytest -m "not slow"      # Skip slow tests
pytest -m api             # Only API tests
```

---

## 📊 Code Coverage

### Generate Coverage Report

```bash
# HTML report
pytest --cov=backend --cov-report=html
open htmlcov/index.html

# Terminal report
pytest --cov=backend --cov-report=term

# Show missing lines
pytest --cov=backend --cov-report=term-missing
```

### Coverage Targets

- **Core modules**: 90%+
- **Agents**: 80%+
- **Tools**: 85%+
- **API endpoints**: 90%+

---

## 🐛 Debugging Tests

### Run with Print Statements

```bash
pytest -s  # Show print() output
```

### Run with Debugger

```python
def test_with_debugger():
    import pdb; pdb.set_trace()  # Breakpoint
    result = function()
    assert result == expected
```

### Show Full Diff on Assertion Failure

```bash
pytest -vv  # Extra verbose shows full diff
```

### Only Run Failed Tests

```bash
pytest --lf  # Last failed
pytest --ff  # Failed first, then others
```

---

## 🚨 Continuous Integration

### GitHub Actions (Example)

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.12'

      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install pytest pytest-asyncio pytest-cov

      - name: Run tests
        run: |
          pytest --cov=backend --cov-report=xml

      - name: Upload coverage
        uses: codecov/codecov-action@v3
```

---

## ✅ Best Practices

### DO ✅

- **Test one thing per test** - Clear, focused tests
- **Use descriptive names** - `test_web_search_returns_cached_results_when_available`
- **Follow AAA pattern** - Arrange, Act, Assert
- **Mock external dependencies** - Fast, reliable tests
- **Clean up after tests** - Use fixtures for cleanup
- **Test error cases** - Not just happy paths
- **Use type hints** - Better IDE support

### DON'T ❌

- **Don't test implementation details** - Test behavior, not internals
- **Don't share state between tests** - Each test should be independent
- **Don't make tests flaky** - No random data, no timing dependencies
- **Don't skip cleanup** - Use fixtures for automatic cleanup
- **Don't test external services** - Mock them instead
- **Don't write slow tests** - Aim for < 1 second per test

---

## 📚 Example: Complete Test File

```python
"""
Unit tests for TavilyToolset
Tests web search with cache-first architecture
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timezone

from backend.tools.web_search.tavily_toolset import TavilyToolset, TavilySearchResult
from backend.tools.web_search.exceptions import TavilyAPIError


class TestTavilySearch:
    """Test Tavily search functionality"""

    @pytest.mark.asyncio
    async def test_search_returns_results(
        self,
        mock_settings,
        mock_document_store,
        mock_tavily_client
    ):
        """Test that search returns formatted results"""
        # ARRANGE
        toolset = TavilyToolset(
            api_key="test_key",
            document_store=mock_document_store,
            enable_caching=False  # Disable cache for unit test
        )

        # Mock Tavily client
        with patch('backend.tools.web_search.tavily_toolset.AsyncTavilyClient') as MockClient:
            MockClient.return_value = mock_tavily_client

            # ACT
            result = await toolset.search(
                query="test query",
                user_id=uuid4(),
                use_cache=False
            )

            # ASSERT
            assert isinstance(result, TavilySearchResult)
            assert result.query == "test query"
            assert len(result.results) == 2
            assert result.source == "api"
            mock_tavily_client.search.assert_called_once()


    @pytest.mark.asyncio
    async def test_search_uses_cache_when_enabled(
        self,
        mock_document_store,
        test_user_id
    ):
        """Test cache-first pattern"""
        # ARRANGE
        toolset = TavilyToolset(
            api_key="test_key",
            document_store=mock_document_store,
            enable_caching=True
        )

        # Mock cache hit
        mock_document_store.search_collection.return_value = [
            (uuid4(), 0.95),  # High similarity score
        ]

        # ACT
        result = await toolset.search(
            query="test",
            user_id=test_user_id,
            use_cache=True
        )

        # ASSERT
        assert result.source == "cache"
        mock_document_store.search_collection.assert_called_once()
```

---

## 🎓 Learning Resources

- [Pytest Documentation](https://docs.pytest.org/)
- [Pytest-asyncio](https://pytest-asyncio.readthedocs.io/)
- [Testing Best Practices](https://docs.python-guide.org/writing/tests/)
- [FastAPI Testing](https://fastapi.tiangolo.com/tutorial/testing/)

---

**Status**: 🚀 Comprehensive Testing Framework
**Last Updated**: February 2026
**Test Count**: 96 passing tests
**Coverage**: 75%+ (target: 80%)
