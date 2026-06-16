# Copilot Instructions for azure-connectors-python-sdk

## Overview

This repository contains the Python SDK for Azure Connectors. Code must follow Python best practices (PEP 8, PEP 484) and the team's conventions for async/await patterns, type safety, and API design.

## Quick Reference: Coding Style Rules

### File Structure

```python
# ------------------------------------------------------------
# Copyright (c) Microsoft Corporation.  All rights reserved.
# ------------------------------------------------------------

"""Module docstring describing the purpose of this module."""

from __future__ import annotations

import asyncio
from typing import Any, Optional

from azure.connectors.sdk import ConnectorClient


class YourClass:
    """Class docstring."""
    
    pass
```

**Rules:**

- Copyright header: Use `# ----` (4 dashes) format with double space before "All rights reserved"
- Module docstring immediately after copyright
- Use `from __future__ import annotations` for forward references
- Imports sorted: standard library, third-party, local (use `isort`)
- One blank line between import groups

### Naming Conventions

| Element | Rule | Example |
|---------|------|---------|
| Modules | lowercase with underscores | `http_client.py` |
| Classes | PascalCase | `ConnectorClient` |
| Functions/methods | snake_case | `get_connection_status()` |
| Constants | UPPER_SNAKE_CASE | `DEFAULT_TIMEOUT_SECONDS` |
| Private members | leading underscore | `_internal_method()`, `_private_attr` |
| Type variables | PascalCase with suffix | `ResponseT`, `ItemT` |

**Variable naming rules:**

- Use complete, unabbreviated English terms for all identifiers
- No single-letter variable names except for well-known conventions (`i`, `j` for indices, `e` for exceptions in handlers)
- No placeholder names (`blah`, `foo`, `temp`, `x`) — always use meaningful names

### File Organization

**One primary class per module:**

- Main class should match the module name (e.g., `http_client.py` contains `HttpClient`)
- Helper classes and functions can coexist in the same module if tightly coupled
- Keep modules focused — split large modules into submodules

### Type Hints

**ALWAYS use type hints for public APIs:**

```python
from typing import Optional

async def get_user(
    user_id: str,
    include_details: bool = False,
) -> Optional[User]:
    """Retrieve a user by ID."""
    ...
```

**Rules:**

- Use `from __future__ import annotations` for modern syntax
- Use `Optional[X]` or `X | None` for nullable types
- Use `list[str]` (lowercase) instead of `List[str]` (Python 3.9+)
- Return type is required for all public functions/methods
- Use `TypedDict` for structured dictionaries
- Use `Protocol` for duck typing instead of ABCs when appropriate

### Async/Await Patterns

**Use async context managers:**

```python
async with aiohttp.ClientSession() as session:
    async with session.get(url) as response:
        data = await response.json()
```

**Rules:**

- Use `async with` for resources that need cleanup
- Prefer `asyncio.gather()` for concurrent operations
- Never use `asyncio.run()` inside async code
- Use `asyncio.create_task()` for fire-and-forget operations (with proper error handling)

**DO NOT:**

```python
# Wrong: Blocking call in async function
response = requests.get(url)  # Use aiohttp instead

# Wrong: Manual cleanup without context manager
session = aiohttp.ClientSession()
try:
    ...
finally:
    await session.close()  # Use async with instead
```

### Function Signatures

**Single line** if all parameters fit:

```python
def process_item(item: Item, validate: bool = True) -> Result:
```

**Multi-line for longer signatures:**

```python
async def create_connection(
    connection_id: str,
    connection_type: str,
    *,
    timeout_seconds: int = 30,
    retry_count: int = 3,
) -> Connection:
```

**Rules:**

- Use keyword-only arguments (after `*`) for optional parameters with defaults
- Boolean parameters SHOULD use keyword-only to avoid ambiguity
- Trailing comma after last parameter in multi-line signatures
- Opening paren stays with function name

### Docstrings

**Use Google-style docstrings:**

```python
def process_request(
    request: Request,
    *,
    validate: bool = True,
) -> Response:
    """Process an incoming request and return the response.
    
    Args:
        request: The request to process.
        validate: Whether to validate the request before processing.
    
    Returns:
        The processed response.
    
    Raises:
        ValidationError: If validation is enabled and the request is invalid.
        ConnectionError: If the connection to the backend fails.
    """
```

**Rules:**

- First line is a concise summary ending with a period
- Blank line between summary and sections
- Document all parameters in `Args:` section
- Document return value in `Returns:` section (skip for `None`)
- Document exceptions in `Raises:` section

### Comments

**Inline comments - use NOTE format:**

```python
# NOTE(username): Explanation of why this code exists.
result = do_something()
```

**Rules:**

- Two spaces before inline comment
- Blank line ABOVE standalone comment (unless first line in block)
- NO blank line between comment and code it describes
- Prefix: `# NOTE(username):` where username is your GitHub username
- Comment on the 'why', not the 'what'

### Exception Handling

```python
try:
    result = await client.get_resource(resource_id)
except SpecificError as e:
    logger.error("Failed to get resource '%s': %s", resource_id, e)
    raise
except Exception as e:
    raise ConnectorError(
        f"Unexpected error retrieving resource '{resource_id}'."
    ) from e
```

**Rules:**

- Exception variable name: `e` (or more specific like `http_error`)
- Always chain exceptions with `from e` to preserve context
- Wrap inserted values in single quotes in error messages
- End error messages with period
- **All exceptions must have descriptive messages** — never raise exceptions without context

**DO:**

```python
raise ValueError(f"Parameter 'connection_id' cannot be empty.")
raise ConnectorError(f"Operation '{operation_id}' is not supported.")
```

**DO NOT:**

```python
raise ValueError()  # No message
raise Exception("error")  # Non-descriptive, too generic
```

### String Formatting

**Use f-strings for simple formatting:**

```python
message = f"Processing request '{request_id}' for user '{user_id}'."
```

**Use logging-style formatting for log messages:**

```python
logger.info("Processing request '%s' for user '%s'.", request_id, user_id)
```

### Class Layout Order

1. Class docstring
2. Class-level constants
3. `__init__` method
4. `__enter__`/`__exit__` or `__aenter__`/`__aexit__` (context managers)
5. Properties
6. Public methods
7. Private methods (`_method`)
8. Magic methods (`__str__`, `__repr__`, etc.)

### Module Layout Order

1. Module docstring
2. `from __future__ import annotations`
3. Standard library imports
4. Third-party imports
5. Local imports
6. Constants
7. Type aliases
8. Classes
9. Functions
10. `if __name__ == "__main__":` block (if applicable)

## Patterns to Avoid

| Anti-Pattern | Correct Pattern |
|--------------|-----------------|
| `requests` in async code | `aiohttp` with async/await |
| Mutable default arguments | `None` with default inside function |
| Bare `except:` | `except Exception as e:` |
| `isinstance(x, str)` for type unions | Use `typing.Union` or `\|` with type guards |
| Magic numbers | Named constants (e.g., `DEFAULT_TIMEOUT_SECONDS`) |
| Magic strings (e.g., `"type"`, `"object"`) | Named constants or enums |
| `list[0]` without length check | `next(iter(list), None)` or explicit validation |

## Testing

```python
import pytest
from unittest.mock import AsyncMock, patch

@pytest.mark.asyncio
async def test_get_user_returns_user_when_found():
    """Test that get_user returns the user when found."""
    # Arrange
    mock_client = AsyncMock()
    mock_client.get.return_value = {"id": "123", "name": "Test User"}
    
    # Act
    result = await get_user(mock_client, user_id="123")
    
    # Assert
    assert result is not None
    assert result.id == "123"
```

**Rules:**

- Test function naming: `test_<method>_<scenario>_<expected>` or `test_<behavior>`
- Use `pytest.mark.asyncio` for async tests
- Use `AsyncMock` for mocking async functions
- Follow Arrange-Act-Assert pattern
- One assertion concept per test (multiple related asserts are OK)

## Git Workflow

- Branch naming: `feature/description`, `fix/description`, `docs/description`
- Never push directly to main
- Always create PR for review

## Releasing a New Version

The official release flow is the Azure DevOps `eng/ci/library-release.yml`
pipeline. It creates a `release/{version}` branch, updates
`src/azure/connectors/__init__.py`, builds the wheel and source distribution,
creates a GitHub draft release with the artifacts, uploads partner drops, and
then requires a manual partner-release/PyPI step. The package version is loaded
from `azure.connectors.__version__` via `src/pyproject.toml`.

### Standard Release (ADO pipeline)

Run the ADO release pipeline with the intended version. The pipeline creates a
bare numeric Git tag such as `1.2.3` or `1.2.3b1`; Python release tags are not
`v`-prefixed.

```shell
# Example versions accepted by the release pipeline:
1.2.3
1.2.3a1
1.2.3b1
1.2.3rc1
```

### Pre-release

Use Python/PEP 440 pre-release suffixes:

```shell
1.2.3a1   # Alpha
1.2.3b1   # Beta
1.2.3rc1  # Release candidate
```

### Manual PyPI Publication

After artifacts are uploaded to the Azure SDK partner drops location, manually
trigger the partner-release pipeline using the BlobPath printed by the official
pipeline. Return to the original run and approve the final manual gate once the
partner-release pipeline has started.

### Re-releasing a Version

Do not delete or recreate a published release tag as a normal retry path. Release
tags are part of the supply-chain integrity boundary and are protected by tag
rulesets. If a release fails after a tag was pushed, use a new version. For a
retry of the same base package, use a PEP 440 post-release such as
`1.2.3.post1`.

```shell
# Run the official release pipeline again with a new version:
1.2.3.post1
```

**Note:** PyPI does not allow re-uploading the same version. If the package was
pushed successfully but the release failed, always use a new version number.
Deleting or retagging an existing remote tag should be treated as break-glass
admin work, not the standard process.

### What the Release Workflow Does

1. Creates and validates a `release/{version}` branch
2. Builds wheel and sdist with `python -m build`
3. Creates a GitHub draft release with the distribution files attached
4. Uploads distribution files to Azure SDK partner drops
5. Guides the maintainer through the manual partner-release/PyPI publication

## Adding a New Connector

When adding a new connector client to the SDK, use the **add-connector** skill (`.github/skills/add-connector/SKILL.md`) for detailed templates and step-by-step guidance.

### Steps

1. **Create the connector module** in `src/azure/connectors/`:
   - File name should match the connector API name (e.g., `office365.py`, `sharepointonline.py`)

2. **Implement the client class** following existing patterns:
   ```python
   from azure.connectors.sdk import ConnectorClient
   
   class Office365Client(ConnectorClient):
       """Client for Office 365 connector operations."""
       
       async def send_email(self, ...) -> EmailResponse:
           ...
   ```

3. **Export from `__init__.py`** — add the new client to `src/azure/connectors/__init__.py`

4. **Update `README.md`** — add the connector to the "Validated Connectors" table with status (`✅ E2E Validated` or `🔄 SDK Generated`) and test count

5. **Add unit tests** — create `test_<connector>.py` in `tests/` following the pattern of existing tests:
   - Constructor tests
   - Method tests with mocked responses
   - Error handling tests
   - Type serialization round-trips

6. **Create sample usage file** — create `sample_connector_usage_<connector>.py` in `samples/sample_connector_usage/` following the pattern of existing samples (port from .NET if available)

7. **Update `samples/sample_connector_usage/README.md`** — add the new sample to the samples table

8. **Update the connection setup skill** — add the connector's API name to the supported list in `.github/skills/connection-setup/SKILL.md` (Step 2)

9. **Run all tests** — `pytest` must pass with zero failures before committing

10. **Create a PR** — reference the GitHub issue (e.g., `Closes #9`)

### Validation checklist

- [ ] Module follows naming conventions (`snake_case.py`)
- [ ] Client class has proper type hints on all public methods
- [ ] Docstrings present on class and all public methods
- [ ] Existing connector tests still pass (no regressions)
- [ ] New connector tests cover: constructor, mocked success, mocked error, exception handling
- [ ] Module exported in `__init__.py`
- [ ] README.md connector table updated
- [ ] Sample file created and compiles without errors
- [ ] Samples README updated
