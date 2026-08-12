# Copyright (c) Microsoft Corporation. All rights reserved.

"""Unit tests for JedoxodatahubClient."""

from unittest.mock import AsyncMock, patch

import pytest

from azure.connectors.jedoxodatahub import JedoxodatahubClient
from azure.connectors.sdk import ConnectorException
from tests.conftest import MockResponse


CONNECTION_URL = "https://example.azure.com/connections/jedoxodatahub"


def test_initialization_and_validation(mock_token_provider):
    """Test connector identity, URL normalization, and required URL validation."""
    client = JedoxodatahubClient(f"{CONNECTION_URL}/", token_provider=mock_token_provider)

    assert client.connector_name == "jedoxodatahub"
    assert client._connection_runtime_url == CONNECTION_URL
    with pytest.raises(ValueError, match="connection_runtime_url cannot be None or empty"):
        JedoxodatahubClient("")


@pytest.mark.asyncio
async def test_databases_returns_response(mock_token_provider):
    """Test the representative databases operation."""
    client = JedoxodatahubClient(CONNECTION_URL, token_provider=mock_token_provider)
    response = MockResponse(status=200, text='{"value": [{"id": "demo"}]}')

    with patch.object(
        client.http_client,
        "send_async",
        new_callable=AsyncMock,
        return_value=response,
    ) as mock_send:
        result = await client.databases_async()

    mock_send.assert_awaited_once_with(
        "GET",
        f"{CONNECTION_URL}/Databases",
        body=None,
    )
    assert result == {"value": [{"id": "demo"}]}


@pytest.mark.asyncio
async def test_databases_error_raises_connector_exception(mock_token_provider):
    """Test that Jedox OData Hub errors retain response details."""
    client = JedoxodatahubClient(CONNECTION_URL, token_provider=mock_token_provider)

    with patch.object(
        client.http_client,
        "send_async",
        new_callable=AsyncMock,
        return_value=MockResponse(status=403, text="forbidden"),
    ):
        with pytest.raises(ConnectorException) as error:
            await client.databases_async()

    assert error.value.status_code == 403
    assert error.value.response_body == "forbidden"
