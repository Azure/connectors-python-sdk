# Copyright (c) Microsoft Corporation. All rights reserved.

"""Pytest configuration and shared fixtures."""

import pytest
from unittest.mock import AsyncMock, MagicMock
from azure.connectors.sdk import TokenProvider


class MockTokenProvider(TokenProvider):
    """Mock token provider for testing."""

    def __init__(self, token: str = "mock_token"):
        """Initialize with a mock token."""
        self._token = token
        self.close_called = False

    async def get_access_token_async(self, scopes: list[str]) -> str:
        """Return the mock token."""
        return self._token

    async def close(self):
        """Mark that close was called."""
        self.close_called = True


class MockResponse:
    """Mock aiohttp.ClientResponse for testing."""

    def __init__(self, status: int, text: str = "", headers: dict = None, content: bytes = None):
        """Initialize mock response."""
        self.status = status
        self.text = text
        self.headers = headers or {}
        # Set content: if explicitly provided use that, otherwise encode text
        if content is not None:
            self.content = content
        elif text:
            self.content = text.encode('utf-8')
        else:
            self.content = b""


@pytest.fixture
def mock_token_provider():
    """Fixture providing a mock token provider."""
    return MockTokenProvider()


@pytest.fixture
def mock_response_success():
    """Fixture providing a successful mock response."""
    return MockResponse(status=200, text='{"result": "success"}')


@pytest.fixture
def mock_response_error():
    """Fixture providing an error mock response."""
    return MockResponse(status=400, text='{"error": "Bad Request"}')


@pytest.fixture
def mock_response_empty():
    """Fixture providing an empty mock response."""
    return MockResponse(status=204, text="")
