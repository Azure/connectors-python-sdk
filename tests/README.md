# Unit Tests

This directory contains comprehensive unit tests for the Azure Connectors Python SDK.

## Test Structure

- `test_<connector>.py` validates a generated connector client and its models.
- `test_sdk_*.py` validates shared authentication, HTTP, serialization, and trigger infrastructure.
- `generated_connector_test_utils.py` invokes generated operations with representative required arguments.
- `conftest.py` provides shared pytest fixtures and mock responses.

## Running Tests

### Run all tests

```bash
python -m pytest tests
```

### Run tests for a specific connector

```bash
python -m pytest tests/test_kusto.py
```

### Run tests with verbose output

```bash
python -m pytest tests -v
```

### Collect tests without running them

```bash
python -m pytest tests --collect-only -q
```

### Run tests with coverage

```bash
python -m pytest tests --cov=azure.connectors --cov-report=term-missing
```

### Run tests with coverage for a specific module

```bash
python -m pytest tests/test_kusto.py --cov=azure.connectors.kusto --cov-report=term-missing
```

## Connector Coverage Expectations

Generated connector tests should cover:

- Initialization, custom options, lifecycle, and connector identity.
- The complete generated operation surface.
- Representative request methods, paths, query parameters, and bodies.
- Non-success responses for every generated operation.
- Empty successful responses where supported.
- Trigger metadata without exposing trigger routes as client methods.
- Request and response model serialization, including wire-name mappings.

## Writing Tests

### Test Organization

Tests are organized into classes by functionality:

- `TestXClientInitialization`: Tests for client initialization
- `TestXClientLifecycle`: Tests for lifecycle methods (close, context manager)
- `TestMethodName`: Tests for specific API methods
- `TestDataClasses`: Tests for data classes and type definitions
- `TestEdgeCases`: Tests for edge cases and boundary conditions

### Fixtures

Common fixtures are defined in [conftest.py](conftest.py):

- `mock_token_provider`: A mock token provider for testing
- `mock_response_success`: A successful mock HTTP response
- `mock_response_error`: An error mock HTTP response
- `mock_response_empty`: An empty mock HTTP response

### Example Test

```python
@pytest.mark.asyncio
async def test_success_with_json_response(self, mock_token_provider):
    """Test successful query execution with JSON response."""
    client = KustoClient(
        "https://example.azure.com/connections/test",
        token_provider=mock_token_provider
    )
    
    mock_response = MockResponse(
        status=200,
        text='{"rows": [{"col1": "value1"}]}'
    )
    
    with patch.object(
        client._http_client,
        'send_async',
        new_callable=AsyncMock,
        return_value=mock_response
    ):
        result = await client.list_kusto_results_async(QueryAndListSchema())
        assert result == {"rows": [{"col1": "value1"}]}
```

## Test Categories

### 1. Initialization Tests
- Valid URL with defaults
- Trailing slash handling
- Custom token provider
- Custom options
- Error cases (empty URL, None URL)
- Property access

### 2. Lifecycle Tests
- Close method
- Async context manager

### 3. API Method Tests
- Success with JSON response
- Success with empty response
- Error responses (4xx, 5xx)
- Parameter passing
- URL construction
- Query string encoding

### 4. Data Class Tests
- Data class creation
- Field validation
- Default values
- Type definitions

### 5. Edge Case Tests
- Multiple consecutive calls
- JSON parse errors
- URL construction edge cases
- Property access

## Dependencies

Test dependencies are defined in [../src/pyproject.toml](../src/pyproject.toml):

- `pytest`: Test framework
- `pytest-asyncio`: Async test support
- `pytest-cov`: Coverage reporting

Install dev dependencies:

```bash
pip install -e ".[dev]"
```

## CI/CD Integration

Tests are designed to run in CI/CD pipelines with:

- Fast, isolated execution
- No external dependencies
- Comprehensive mocking
- Clear error messages
- Strict async mode

## Best Practices

1. **Use descriptive test names**: `test_method_scenario_expected_result`
2. **Group related tests**: Use test classes to organize tests
3. **Mock external dependencies**: Never make real HTTP calls in unit tests
4. **Test error cases**: Always test both success and failure paths
5. **Use fixtures**: Reuse common setup code via pytest fixtures
6. **Document test intent**: Include docstrings explaining what is being tested
7. **Verify all code paths**: Aim for high coverage (95%+)
8. **Keep tests fast**: Unit tests should run in milliseconds
