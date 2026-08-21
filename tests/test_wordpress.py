# Copyright (c) Microsoft Corporation. All rights reserved.

"""Unit tests for WordpressClient."""

from unittest.mock import AsyncMock, patch

import pytest

import azure.connectors.wordpress as wordpress_module
from azure.connectors.sdk import ConnectorException, ManagedIdentityTokenProvider
from azure.connectors.wordpress import (
    CreatePostModel,
    TRIGGER_OPERATIONS,
    WordpressClient,
)
from tests.conftest import MockResponse
from tests.generated_connector_test_utils import (
    get_generated_operations,
    invoke_generated_operation,
)


SUCCESS_CONTRACTS = {
    "create": ("POST", "/sites/value/posts/new", True),
    "get": ("GET", "/sites/value/posts/value", False),
    "list_sites": (
        "GET",
        "/me/sites?fields=ID%2C%20name%2C%20description%2C%20URL%2C%20%20is_multisite%2C"
        "%20post_count%2Csubscribers_count%2C%20lang%2Cvisible%2Cis_private%2C"
        "single_user_site%2Cis_vip%2Cis_following",
        False,
    ),
    "site_stats": ("GET", "/sites/value/stats?fields=stats", False),
}
ALL_OPERATIONS = list(SUCCESS_CONTRACTS)


class TestWordpressClient:
    """Tests for WordpressClient."""

    def test_init_with_defaults(self):
        """Test initialization with default authentication."""
        client = WordpressClient("https://example.azure.com/connections/test/")

        assert client._connection_runtime_url == "https://example.azure.com/connections/test"
        assert client.connector_name == "wordpress"
        assert isinstance(client._http_client._token_provider, ManagedIdentityTokenProvider)

    @pytest.mark.parametrize("connection_runtime_url", ["", None])
    def test_init_with_invalid_url_raises_error(self, connection_runtime_url):
        """Test invalid runtime URLs are rejected."""
        with pytest.raises(ValueError, match="connection_runtime_url cannot be None or empty"):
            WordpressClient(connection_runtime_url)

    @pytest.mark.asyncio
    async def test_context_manager(self, mock_token_provider):
        """Test async context manager cleanup."""
        with patch.object(WordpressClient, "close", new_callable=AsyncMock) as mock_close:
            async with WordpressClient(
                "https://example.azure.com/connections/test",
                token_provider=mock_token_provider,
            ) as client:
                assert isinstance(client, WordpressClient)

        mock_close.assert_called_once()

    def test_all_generated_operations_are_covered(self):
        """Test the expected generated operation surface."""
        assert get_generated_operations(WordpressClient) == set(ALL_OPERATIONS)

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        ("operation", "expected_method", "expected_url_suffix", "expects_body"),
        [
            (operation, *contract)
            for operation, contract in SUCCESS_CONTRACTS.items()
        ],
    )
    async def test_generated_operation_success_contract(
        self,
        operation,
        expected_method,
        expected_url_suffix,
        expects_body,
        mock_token_provider,
    ):
        """Test every generated operation's successful HTTP contract."""
        client = WordpressClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider,
        )

        with patch.object(
            client._http_client,
            "send_async",
            new_callable=AsyncMock,
            return_value=MockResponse(status=200, text='{"ok": true}'),
        ) as mock_send:
            result = await invoke_generated_operation(client, operation, wordpress_module)

        method, url = mock_send.call_args.args[:2]
        assert method == expected_method
        assert url.endswith(expected_url_suffix)
        assert (mock_send.call_args.kwargs["body"] is not None) is expects_body
        assert result == {"ok": True}

    @pytest.mark.asyncio
    async def test_create_post_success(self, mock_token_provider):
        """Test creating a post sends the generated request model."""
        client = WordpressClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider,
        )
        response = MockResponse(status=200, text='{"ID": 42}')

        with patch.object(
            client._http_client,
            "send_async",
            new_callable=AsyncMock,
            return_value=response,
        ) as mock_send:
            result = await client.create_async(
                input=CreatePostModel(title="Generated SDK", content="Hello"),
                site_id="site/one",
            )

        method, url = mock_send.call_args.args[:2]
        assert method == "POST"
        assert url.endswith("/sites/site%2Fone/posts/new")
        assert mock_send.call_args.kwargs["body"].title == "Generated SDK"
        assert result == {"ID": 42}

    @pytest.mark.asyncio
    async def test_list_sites_success(self, mock_token_provider):
        """Test listing sites uses the current WordPress route."""
        client = WordpressClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider,
        )

        with patch.object(
            client._http_client,
            "send_async",
            new_callable=AsyncMock,
            return_value=MockResponse(status=200, text='{"sites": []}'),
        ) as mock_send:
            result = await client.list_sites_async()

        method, url = mock_send.call_args.args[:2]
        assert method == "GET"
        assert "/me/sites?fields=" in url
        assert result == {"sites": []}

    def test_trigger_metadata(self):
        """Test polling trigger metadata is registered instead of callable."""
        assert set(TRIGGER_OPERATIONS) == {"OnTriggerNewPost"}
        assert TRIGGER_OPERATIONS["OnTriggerNewPost"]["path"].endswith(
            "/trigger/me/posts"
        )
        assert not hasattr(WordpressClient, "on_trigger_new_post_async")

    @pytest.mark.asyncio
    @pytest.mark.parametrize("operation", ALL_OPERATIONS)
    async def test_non_success_response_raises_exception(
        self,
        operation,
        mock_token_provider,
    ):
        """Test every generated operation raises for a non-success response."""
        client = WordpressClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider,
        )

        with patch.object(
            client._http_client,
            "send_async",
            new_callable=AsyncMock,
            return_value=MockResponse(status=400, text="bad request"),
        ):
            with pytest.raises(ConnectorException):
                await invoke_generated_operation(client, operation, wordpress_module)
