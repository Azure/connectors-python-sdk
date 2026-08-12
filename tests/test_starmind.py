# Copyright (c) Microsoft Corporation. All rights reserved.

"""Unit tests for StarmindClient."""

from unittest.mock import AsyncMock, patch

import pytest

from azure.connectors.sdk import ConnectorException
from azure.connectors.starmind import StarmindClient
from tests.conftest import MockResponse


CONNECTION_URL = "https://example.azure.com/connections/starmind"


def test_initialization_and_validation(mock_token_provider):
    """Test connector identity, URL normalization, and required URL validation."""
    client = StarmindClient(f"{CONNECTION_URL}/", token_provider=mock_token_provider)

    assert client.connector_name == "starmind"
    assert client._connection_runtime_url == CONNECTION_URL
    with pytest.raises(ValueError, match="connection_runtime_url cannot be None or empty"):
        StarmindClient("")


@pytest.mark.asyncio
async def test_find_questions_returns_response(mock_token_provider):
    """Test the representative question search operation."""
    client = StarmindClient(CONNECTION_URL, token_provider=mock_token_provider)
    response = MockResponse(status=200, text='{"items": [{"id": "question"}]}')

    with patch.object(
        client.http_client,
        "send_async",
        new_callable=AsyncMock,
        return_value=response,
    ) as mock_send:
        result = await client.find_questions_async()

    mock_send.assert_awaited_once_with(
        "GET",
        f"{CONNECTION_URL}/api/v3/questions",
        body=None,
    )
    assert result == {"items": [{"id": "question"}]}


@pytest.mark.asyncio
async def test_find_questions_error_raises_connector_exception(mock_token_provider):
    """Test that Starmind errors retain response details."""
    client = StarmindClient(CONNECTION_URL, token_provider=mock_token_provider)

    with patch.object(
        client.http_client,
        "send_async",
        new_callable=AsyncMock,
        return_value=MockResponse(status=401, text="unauthorized"),
    ):
        with pytest.raises(ConnectorException) as error:
            await client.find_questions_async()

    assert error.value.status_code == 401
    assert error.value.response_body == "unauthorized"
