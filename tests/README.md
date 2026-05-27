# Unit Tests

This directory contains comprehensive unit tests for the Azure Connectors Python SDK.

## Test Structure

```
tests/
├── __init__.py                      # Package initialization
├── conftest.py                      # Shared pytest fixtures and utilities
├── test_kusto.py                    # Kusto connector tests (37 tests, 98% coverage)
├── test_msgraph.py                  # Microsoft Graph connector tests (46 tests)
├── test_office365.py                # Office365 connector tests (41 tests, 79% coverage)
├── test_sharepointonline.py         # SharePoint Online connector tests (44 tests, 57% coverage)
├── test_teams.py                    # Teams connector tests (27 passed, 18 skipped, 73% coverage)
├── test_sdk_authentication.py       # Authentication module tests (21 tests)
├── test_sdk_client_base.py          # Client base module tests (14 tests)
├── test_sdk_exceptions.py           # Exceptions module tests (14 tests)
├── test_sdk_http_client.py          # HTTP client module tests (30 tests)
├── test_sdk_options.py              # Options module tests (14 tests)
├── test_sdk_trigger_payload.py      # Trigger payload module tests (17 tests)
└── README.md                        # This file
```

## Running Tests

### Run all tests
```bash
pytest
```

### Run tests for a specific connector
```bash
pytest tests/test_kusto.py
```

### Run tests with verbose output
```bash
pytest -v
```

### Run tests with coverage
```bash
pytest --cov=azure.connectors --cov-report=term-missing
```

### Run tests with coverage for a specific module
```bash
pytest tests/test_kusto.py --cov=azure.connectors.kusto --cov-report=term-missing
```

## Test Coverage

Current test coverage by module:

### Connector Tests (195 passing, 18 skipped)

- **kusto.py**: 98% (37 tests)
  - Initialization tests (7)
  - Lifecycle tests (2)
  - API method tests (16)
  - Data class tests (7)
  - Edge case tests (5)

- **msgraph.py**: (46 tests)
  - Initialization tests (7)
  - Lifecycle tests (2)
  - User operation tests (3)
  - Group operation tests (13)
  - License operation tests (3)
  - Subscription operation tests (2)
  - Data class tests (8)
  - Edge case tests (8)

- **office365.py**: 79% (41 tests covering 53 methods)
  - Initialization tests (7)
  - Lifecycle tests (2)
  - Email operation tests (13)
  - Calendar operation tests (3)
  - Contact operation tests (1)
  - MCP endpoint tests (2)
  - Data class tests (4)
  - Edge case tests (9)

- **sharepointonline.py**: 57% (44 tests)
  - Initialization tests (7)
  - Lifecycle tests (2)
  - Get all tables tests (4)
  - File operation tests (5)
  - Folder operation tests (4)
  - Item operation tests (5)
  - Sharing operation tests (2)
  - Copy/move operation tests (3)
  - Approval operation tests (2)
  - Data class tests (4)
  - Edge case tests (6)

- **teams.py**: 73% (27 passed, 18 skipped)
  - Initialization tests (7)
  - Lifecycle tests (2)
  - Meeting operation tests (2)
  - List operation tests (3)
  - Channel operation tests (4 skipped - template variable bugs in generated code)
  - Chat operation tests (1 skipped - template variable bugs in generated code)
  - Tag operation tests (6 skipped - template variable bugs in generated code)
  - Message operation tests (4 skipped - template variable bugs in generated code)
  - Member operation tests (1 skipped - template variable bugs in generated code)
  - Trigger operation tests (2 skipped - template variable bugs in generated code)
  - Data class tests (7)
  - Edge case tests (6)

**Note:** Some Teams connector methods have template variables (e.g., `{groupId}`, `{channelId}`) that are not defined as parameters in the generated code. These tests are skipped with appropriate documentation. Once the code generation issue is fixed, these tests can be enabled.

### SDK Component Tests (110 passing)

- **authentication.py**: (21 tests)
  - AzureIdentityTokenProvider tests (8)
  - ManagedIdentityTokenProvider tests (5)
  - ConnectionStringTokenProvider tests (5)
  - TokenProvider interface tests (3)

- **client_base.py**: (14 tests)
  - Abstract class tests (1)
  - Initialization tests (6)
  - Lifecycle tests (5)
  - Credential wrapping tests (2)

- **exceptions.py**: (14 tests)
  - Initialization and message format tests (5)
  - Body truncation tests (5)
  - Status code and attribute tests (4)

- **http_client.py**: (30 tests)
  - ConnectorResponse tests (9)
  - Initialization and session tests (7)
  - Request sending tests (10)
  - Retry delay tests (2)
  - GET method tests (2)

- **options.py**: (14 tests)
  - Default values 305 tests (285 passing, 20 skipped)
- **Connector Tests**: 195 tests (177
  - Type verification tests (3)

- **trigger_payload.py**: (17 tests)
  - TriggerCallbackBody tests (7)
  - TriggerCallbackPayload tests (10)

### Overall Test Statistics

- **Total Tests**: 259 tests (249 passing, 18 skipped)
- **Connector Tests**: 149 tests (131 passing, 18 skipped)
- **SDK Component Tests**: 110 tests (110 passing)
- **Overall Coverage**: ~75%

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

- Fast execution (< 1 second for 37 tests)
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
