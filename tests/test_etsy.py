# Copyright (c) Microsoft Corporation. All rights reserved.

"""Unit tests for EtsyClient."""

from unittest.mock import AsyncMock, patch

import pytest

from azure.connectors.etsy import EtsyClient
from azure.connectors.sdk import ConnectorException
from tests.conftest import MockResponse


CONNECTION_URL = "https://example.azure.com/connections/etsy"


def test_initialization_and_validation(mock_token_provider):
    """Test connector identity, URL normalization, and required URL validation."""
    client = EtsyClient(f"{CONNECTION_URL}/", token_provider=mock_token_provider)

    assert client.connector_name == "etsy"
    assert client._connection_runtime_url == CONNECTION_URL
    with pytest.raises(ValueError, match="connection_runtime_url cannot be None or empty"):
        EtsyClient("")


@pytest.mark.asyncio
async def test_ping_returns_response(mock_token_provider):
    """Test the representative ping operation."""
    client = EtsyClient(CONNECTION_URL, token_provider=mock_token_provider)
    response = MockResponse(status=200, text='{"application_id": 1}')

    with patch.object(
        client.http_client,
        "send_async",
        new_callable=AsyncMock,
        return_value=response,
    ) as mock_send:
        result = await client.ping_async()

    mock_send.assert_awaited_once_with(
        "GET",
        f"{CONNECTION_URL}/openapi-ping",
        body=None,
    )
    assert result == {"application_id": 1}


@pytest.mark.asyncio
async def test_ping_error_raises_connector_exception(mock_token_provider):
    """Test that Etsy errors retain the connector response details."""
    client = EtsyClient(CONNECTION_URL, token_provider=mock_token_provider)

    with patch.object(
        client.http_client,
        "send_async",
        new_callable=AsyncMock,
        return_value=MockResponse(status=429, text="rate limited"),
    ):
        with pytest.raises(ConnectorException) as error:
            await client.ping_async()

    assert error.value.status_code == 429
    assert error.value.response_body == "rate limited"
