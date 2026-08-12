# Copyright (c) Microsoft Corporation. All rights reserved.

"""Unit tests for MondayClient."""

from unittest.mock import AsyncMock, patch

import pytest

from azure.connectors.monday import MondayClient
from azure.connectors.sdk import ConnectorException
from tests.conftest import MockResponse


CONNECTION_URL = "https://example.azure.com/connections/monday"


def test_initialization_and_validation(mock_token_provider):
    """Test connector identity, URL normalization, and required URL validation."""
    client = MondayClient(f"{CONNECTION_URL}/", token_provider=mock_token_provider)

    assert client.connector_name == "monday"
    assert client._connection_runtime_url == CONNECTION_URL
    with pytest.raises(ValueError, match="connection_runtime_url cannot be None or empty"):
        MondayClient("")


@pytest.mark.asyncio
async def test_get_workspaces_returns_response(mock_token_provider):
    """Test the representative workspace discovery operation."""
    client = MondayClient(CONNECTION_URL, token_provider=mock_token_provider)
    response = MockResponse(status=200, text='{"data": [{"id": "1"}]}')

    with patch.object(
        client.http_client,
        "send_async",
        new_callable=AsyncMock,
        return_value=response,
    ) as mock_send:
        result = await client.get_workspaces_async()

    mock_send.assert_awaited_once_with(
        "GET",
        f"{CONNECTION_URL}/getData/getWorkspacesV2",
        body=None,
    )
    assert result == {"data": [{"id": "1"}]}


@pytest.mark.asyncio
async def test_get_workspaces_error_raises_connector_exception(mock_token_provider):
    """Test that monday.com errors retain response details."""
    client = MondayClient(CONNECTION_URL, token_provider=mock_token_provider)

    with patch.object(
        client.http_client,
        "send_async",
        new_callable=AsyncMock,
        return_value=MockResponse(status=400, text="invalid request"),
    ):
        with pytest.raises(ConnectorException) as error:
            await client.get_workspaces_async()

    assert error.value.status_code == 400
    assert error.value.response_body == "invalid request"
