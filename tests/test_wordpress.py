# Copyright (c) Microsoft Corporation. All rights reserved.

"""Unit tests for WordpressClient."""

from unittest.mock import AsyncMock, patch

import pytest

from azure.connectors.sdk import ConnectorException
from azure.connectors.wordpress import WordpressClient
from tests.conftest import MockResponse


CONNECTION_URL = "https://example.azure.com/connections/wordpress"


def test_initialization_and_validation(mock_token_provider):
    """Test connector identity, URL normalization, and required URL validation."""
    client = WordpressClient(f"{CONNECTION_URL}/", token_provider=mock_token_provider)

    assert client.connector_name == "wordpress"
    assert client._connection_runtime_url == CONNECTION_URL
    with pytest.raises(ValueError, match="connection_runtime_url cannot be None or empty"):
        WordpressClient("")


@pytest.mark.asyncio
async def test_list_sites_returns_response(mock_token_provider):
    """Test the representative site listing operation."""
    client = WordpressClient(CONNECTION_URL, token_provider=mock_token_provider)
    response = MockResponse(status=200, text='{"sites": [{"ID": 1}]}')

    with patch.object(
        client.http_client,
        "send_async",
        new_callable=AsyncMock,
        return_value=response,
    ) as mock_send:
        result = await client.list_sites_async()

    expected_url = (
        f"{CONNECTION_URL}/me/sites?fields="
        "ID%2C%20name%2C%20description%2C%20URL%2C%20%20is_multisite%2C%20"
        "post_count%2Csubscribers_count%2C%20lang%2Cvisible%2Cis_private%2C"
        "single_user_site%2Cis_vip%2Cis_following"
    )
    mock_send.assert_awaited_once_with("GET", expected_url, body=None)
    assert result == {"sites": [{"ID": 1}]}


@pytest.mark.asyncio
async def test_list_sites_error_raises_connector_exception(mock_token_provider):
    """Test that WordPress errors retain response details."""
    client = WordpressClient(CONNECTION_URL, token_provider=mock_token_provider)

    with patch.object(
        client.http_client,
        "send_async",
        new_callable=AsyncMock,
        return_value=MockResponse(status=500, text="server error"),
    ):
        with pytest.raises(ConnectorException) as error:
            await client.list_sites_async()

    assert error.value.status_code == 500
    assert error.value.response_body == "server error"
