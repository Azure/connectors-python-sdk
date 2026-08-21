# Copyright (c) Microsoft Corporation. All rights reserved.

"""Unit tests for SlackClient."""

from unittest.mock import AsyncMock, patch

import pytest

from azure.connectors.sdk import (
    ConnectorClientOptions,
    ConnectorException,
    ManagedIdentityTokenProvider,
)
from azure.connectors.slack import PostMessageRequest, SlackClient, TRIGGER_OPERATIONS
from tests.conftest import MockResponse


class TestSlackClientInitialization:
    """Tests for SlackClient initialization."""

    def test_init_with_valid_url_and_defaults(self):
        """Test initialization with valid URL and default parameters."""
        client = SlackClient("https://example.azure.com/connections/test")

        assert client._connection_runtime_url == "https://example.azure.com/connections/test"
        assert client.connector_name == "slack"
        assert isinstance(client._http_client._token_provider, ManagedIdentityTokenProvider)

    def test_init_with_trailing_slash(self):
        """Test that trailing slash is removed from URL."""
        client = SlackClient("https://example.azure.com/connections/test/")

        assert client._connection_runtime_url == "https://example.azure.com/connections/test"

    def test_init_with_custom_token_provider(self, mock_token_provider):
        """Test initialization with custom token provider."""
        client = SlackClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider,
        )

        assert client._http_client._token_provider is mock_token_provider

    def test_init_with_custom_options(self, mock_token_provider):
        """Test initialization with custom options."""
        options = ConnectorClientOptions(timeout_seconds=60.0, max_retry_attempts=5)
        client = SlackClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider,
            options=options,
        )

        assert client._options is options
        assert client._options.timeout_seconds == 60.0
        assert client._options.max_retry_attempts == 5

    def test_init_with_empty_url_raises_error(self):
        """Test that empty URL raises ValueError."""
        with pytest.raises(ValueError, match="connection_runtime_url cannot be None or empty"):
            SlackClient("")

    def test_init_with_none_url_raises_error(self):
        """Test that None URL raises ValueError."""
        with pytest.raises(ValueError, match="connection_runtime_url cannot be None or empty"):
            SlackClient(None)

    def test_connector_name_property(self, mock_token_provider):
        """Test connector_name property returns 'slack'."""
        client = SlackClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider,
        )

        assert client.connector_name == "slack"


class TestSlackClientLifecycle:
    """Tests for SlackClient lifecycle methods."""

    @pytest.mark.asyncio
    async def test_close(self, mock_token_provider):
        """Test close method calls http_client.close."""
        client = SlackClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider,
        )

        with patch.object(client._http_client, "close", new_callable=AsyncMock) as mock_close:
            await client.close()
            mock_close.assert_called_once()

    @pytest.mark.asyncio
    async def test_context_manager(self, mock_token_provider):
        """Test async context manager functionality."""
        with patch.object(SlackClient, "close", new_callable=AsyncMock) as mock_close:
            async with SlackClient(
                "https://example.azure.com/connections/test",
                token_provider=mock_token_provider,
            ) as client:
                assert isinstance(client, SlackClient)

            mock_close.assert_called_once()


class TestSetDndAsync:
    """Tests for set_dnd_async method."""

    @pytest.mark.asyncio
    async def test_success_uses_acronym_aware_name(self, mock_token_provider):
        """Test setting DND through the acronym-aware public method name."""
        client = SlackClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider,
        )
        mock_response = MockResponse(status=200, text='{"ok": true}')

        with patch.object(
            client._http_client,
            "send_async",
            new_callable=AsyncMock,
            return_value=mock_response,
        ) as mock_send:
            result = await client.set_dnd_async(num_minutes="30")

            mock_send.assert_called_once_with(
                "GET",
                "https://example.azure.com/connections/test/dnd.setSnooze?num_minutes=30",
                body=None,
            )
            assert result == {"ok": True}
            assert not hasattr(SlackClient, "set_d_n_d_async")

    @pytest.mark.asyncio
    async def test_error_response_raises_exception(self, mock_token_provider):
        """Test DND errors raise ConnectorException."""
        client = SlackClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider,
        )
        mock_response = MockResponse(status=400, text='{"error": "Bad request"}')

        with patch.object(
            client._http_client,
            "send_async",
            new_callable=AsyncMock,
            return_value=mock_response,
        ):
            with pytest.raises(ConnectorException):
                await client.set_dnd_async(num_minutes="invalid")


class TestSlackContractSurface:
    """Tests for Slack trigger metadata and removed operations."""

    def test_trigger_is_metadata_only(self):
        """Test the file trigger is registered without a callable method."""
        assert TRIGGER_OPERATIONS == {
            "OnNewFile": {
                "operation_id": "OnNewFile",
                "path": "/{connectionId}/trigger/files.list",
                "method": "get",
                "required_parameters": ["channel"],
                "callback_payload_type": None,
            }
        }
        assert not hasattr(SlackClient, "on_new_file_async")

    def test_deprecated_group_operation_is_not_generated(self):
        """Test the deprecated group operation is absent."""
        assert not hasattr(SlackClient, "create_group_async")


class TestListChannelsAsync:
    """Tests for list_channels_async method."""

    @pytest.mark.asyncio
    async def test_success(self, mock_token_provider):
        """Test successful channel listing."""
        client = SlackClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider,
        )
        mock_response = MockResponse(
            status=200,
            text='{"value": [{"id": "C123", "name": "general"}]}',
        )

        with patch.object(
            client._http_client,
            "send_async",
            new_callable=AsyncMock,
            return_value=mock_response,
        ) as mock_send:
            result = await client.list_channels_async()

            mock_send.assert_called_once()
            method, path = mock_send.call_args[0][0], mock_send.call_args[0][1]
            assert method == "GET"
            assert "/v3/conversations.list" in path
            assert result is not None
            assert "value" in result

    @pytest.mark.asyncio
    async def test_error_response_raises_exception(self, mock_token_provider):
        """Test list channels error path."""
        client = SlackClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider,
        )
        mock_response = MockResponse(
            status=500,
            text='{"error": "Server error"}',
        )

        with patch.object(
            client._http_client,
            "send_async",
            new_callable=AsyncMock,
            return_value=mock_response,
        ):
            with pytest.raises(ConnectorException):
                await client.list_channels_async()


class TestCreateChannelAsync:
    """Tests for create_channel_async method."""

    @pytest.mark.asyncio
    async def test_success(self, mock_token_provider):
        """Test successful channel creation."""
        client = SlackClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider,
        )
        mock_response = MockResponse(
            status=201,
            text='{"channel": {"id": "C999", "name": "dev-chat"}}',
        )

        with patch.object(
            client._http_client,
            "send_async",
            new_callable=AsyncMock,
            return_value=mock_response,
        ) as mock_send:
            result = await client.create_channel_async(name="dev-chat", is_private="false")

            mock_send.assert_called_once()
            method, path = mock_send.call_args[0][0], mock_send.call_args[0][1]
            assert method == "POST"
            assert "/conversations.create" in path
            assert "name=dev-chat" in path
            assert "is_private=false" in path
            assert result is not None
            assert result["channel"]["name"] == "dev-chat"

    @pytest.mark.asyncio
    async def test_error_response_raises_exception(self, mock_token_provider):
        """Test create channel error path."""
        client = SlackClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider,
        )
        mock_response = MockResponse(
            status=400,
            text='{"error": "Bad request"}',
        )

        with patch.object(
            client._http_client,
            "send_async",
            new_callable=AsyncMock,
            return_value=mock_response,
        ):
            with pytest.raises(ConnectorException):
                await client.create_channel_async(name="")


class TestPostMessageAsync:
    """Tests for post_message_async method."""

    @pytest.mark.asyncio
    async def test_success(self, mock_token_provider):
        """Test successful message posting."""
        client = SlackClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider,
        )
        payload = PostMessageRequest(channel="#general", text="Hello from SDK")
        mock_response = MockResponse(
            status=200,
            text='{"ok": true, "channel": "C123", "ts": "12345.67"}',
        )

        with patch.object(
            client._http_client,
            "send_async",
            new_callable=AsyncMock,
            return_value=mock_response,
        ) as mock_send:
            result = await client.post_message_async(input=payload)

            mock_send.assert_called_once()
            method, path = mock_send.call_args[0][0], mock_send.call_args[0][1]
            body = mock_send.call_args[1].get("body")
            assert method == "POST"
            assert "/v2/chat.postMessage" in path
            assert body is payload
            assert result is not None
            assert result.get("ok") is True

    @pytest.mark.asyncio
    async def test_error_response_raises_exception(self, mock_token_provider):
        """Test post message error path."""
        client = SlackClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider,
        )
        payload = PostMessageRequest(channel="#general", text="")
        mock_response = MockResponse(
            status=403,
            text='{"error": "forbidden"}',
        )

        with patch.object(
            client._http_client,
            "send_async",
            new_callable=AsyncMock,
            return_value=mock_response,
        ):
            with pytest.raises(ConnectorException):
                await client.post_message_async(input=payload)
