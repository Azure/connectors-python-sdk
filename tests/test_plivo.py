# Copyright (c) Microsoft Corporation. All rights reserved.

"""Unit tests for PlivoClient."""

from unittest.mock import AsyncMock, patch

import pytest

from azure.connectors.plivo import (
    Call,
    GetMessageResponse,
    PlivoClient,
    SMS,
    SendSMSResponse,
)
from azure.connectors.sdk import (
    ConnectorClientOptions,
    ConnectorException,
    ManagedIdentityTokenProvider,
)
from tests.conftest import MockResponse


class TestPlivoClientInitialization:
    """Tests for PlivoClient initialization."""

    def test_init_with_valid_url_and_defaults(self):
        """Test initialization with valid URL and default parameters."""
        client = PlivoClient("https://example.azure.com/connections/test")

        assert client._connection_runtime_url == "https://example.azure.com/connections/test"
        assert client.connector_name == "plivo"
        assert isinstance(client._http_client._token_provider, ManagedIdentityTokenProvider)

    def test_init_with_trailing_slash(self):
        """Test that trailing slash is removed from URL."""
        client = PlivoClient("https://example.azure.com/connections/test/")

        assert client._connection_runtime_url == "https://example.azure.com/connections/test"

    def test_init_with_custom_token_provider(self, mock_token_provider):
        """Test initialization with custom token provider."""
        client = PlivoClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider,
        )

        assert client._http_client._token_provider is mock_token_provider

    def test_init_with_custom_options(self, mock_token_provider):
        """Test initialization with custom options."""
        options = ConnectorClientOptions(timeout_seconds=60.0, max_retry_attempts=5)
        client = PlivoClient(
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
            PlivoClient("")

    def test_init_with_none_url_raises_error(self):
        """Test that None URL raises ValueError."""
        with pytest.raises(ValueError, match="connection_runtime_url cannot be None or empty"):
            PlivoClient(None)

    def test_connector_name_property(self, mock_token_provider):
        """Test connector_name property returns 'plivo'."""
        client = PlivoClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider,
        )

        assert client.connector_name == "plivo"


class TestPlivoClientLifecycle:
    """Tests for PlivoClient lifecycle methods."""

    @pytest.mark.asyncio
    async def test_close(self, mock_token_provider):
        """Test close method calls http_client.close."""
        client = PlivoClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider,
        )

        with patch.object(client._http_client, "close", new_callable=AsyncMock) as mock_close:
            await client.close()
            mock_close.assert_called_once()

    @pytest.mark.asyncio
    async def test_context_manager(self, mock_token_provider):
        """Test async context manager functionality."""
        with patch.object(PlivoClient, "close", new_callable=AsyncMock) as mock_close:
            async with PlivoClient(
                "https://example.azure.com/connections/test",
                token_provider=mock_token_provider,
            ) as client:
                assert isinstance(client, PlivoClient)

            mock_close.assert_called_once()


class TestPlivoClientOperations:
    """Tests for PlivoClient operations against expected HTTP calls."""

    def _make_client(self, mock_token_provider):
        return PlivoClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider,
        )

    @pytest.mark.asyncio
    async def test_make_call_success(self, mock_token_provider):
        """Test make_call issues a POST to the Call route with the input body."""
        client = self._make_client(mock_token_provider)
        payload = Call(from_="+15551112222", to="+15553334444", answer_url="https://x/answer")
        mock_response = MockResponse(status=200, text='{"api_id": "abc"}')

        with patch.object(
            client._http_client, "send_async", new_callable=AsyncMock,
            return_value=mock_response,
        ) as mock_send:
            result = await client.make_call_async(input=payload, auth_id="MA123")

            assert mock_send.call_args[0][0] == "POST"
            assert "/v1/Account/MA123/Call/" in mock_send.call_args[0][1]
            assert mock_send.call_args.kwargs["body"] is payload
            assert result == {"api_id": "abc"}

    @pytest.mark.asyncio
    async def test_list_messages_success(self, mock_token_provider):
        """Test list_messages issues a GET to the Message route."""
        client = self._make_client(mock_token_provider)
        mock_response = MockResponse(status=200, text='{"api_id": "abc"}')

        with patch.object(
            client._http_client, "send_async", new_callable=AsyncMock,
            return_value=mock_response,
        ) as mock_send:
            result = await client.list_messages_async(auth_id="MA123")

            assert mock_send.call_args[0][0] == "GET"
            assert "/v1/Account/MA123/Message/" in mock_send.call_args[0][1]
            assert result == {"api_id": "abc"}

    @pytest.mark.asyncio
    async def test_send_s_m_s_success(self, mock_token_provider):
        """Test send_s_m_s issues a POST to the Message route with the input body."""
        client = self._make_client(mock_token_provider)
        payload = SMS(src="+15551112222", dst="+15553334444", text="hello")
        mock_response = MockResponse(status=200, text='{"api_id": "abc"}')

        with patch.object(
            client._http_client, "send_async", new_callable=AsyncMock,
            return_value=mock_response,
        ) as mock_send:
            result = await client.send_s_m_s_async(input=payload, auth_id="MA123")

            assert mock_send.call_args[0][0] == "POST"
            assert "/v1/Account/MA123/Message/" in mock_send.call_args[0][1]
            assert mock_send.call_args.kwargs["body"] is payload
            assert result == {"api_id": "abc"}

    @pytest.mark.asyncio
    async def test_get_message_success(self, mock_token_provider):
        """Test get_message issues a GET to the single message route."""
        client = self._make_client(mock_token_provider)
        mock_response = MockResponse(status=200, text='{"api_id": "abc"}')

        with patch.object(
            client._http_client, "send_async", new_callable=AsyncMock,
            return_value=mock_response,
        ) as mock_send:
            result = await client.get_message_async(auth_id="MA123", message_uuid="MSG789")

            assert mock_send.call_args[0][0] == "GET"
            assert "/v1/Account/MA123/Message/MSG789/" in mock_send.call_args[0][1]
            assert result == {"api_id": "abc"}

    @pytest.mark.asyncio
    async def test_empty_response_body_returns_none(self, mock_token_provider):
        """Test a 2xx response with no body returns None."""
        client = self._make_client(mock_token_provider)
        mock_response = MockResponse(status=200, text="")

        with patch.object(
            client._http_client, "send_async", new_callable=AsyncMock,
            return_value=mock_response,
        ):
            result = await client.list_messages_async(auth_id="MA123")

            assert result is None


class TestPlivoClientErrorHandling:
    """Error handling tests for PlivoClient operations."""

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "operation",
        [
            "make_call",
            "list_messages",
            "send_s_m_s",
            "get_message",
        ],
    )
    async def test_error_response_raises_exception(self, mock_token_provider, operation):
        """Test non-2xx responses raise ConnectorException for every operation."""
        client = PlivoClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider,
        )
        mock_response = MockResponse(status=500, text='{"error":"server failure"}')

        with patch.object(
            client._http_client, "send_async", new_callable=AsyncMock,
            return_value=mock_response,
        ):
            with pytest.raises(ConnectorException) as exc_info:
                if operation == "make_call":
                    await client.make_call_async(input=Call(), auth_id="MA123")
                elif operation == "list_messages":
                    await client.list_messages_async(auth_id="MA123")
                elif operation == "send_s_m_s":
                    await client.send_s_m_s_async(input=SMS(), auth_id="MA123")
                else:
                    await client.get_message_async(auth_id="MA123", message_uuid="MSG789")

            assert exc_info.value.status_code == 500


class TestPlivoTypeSerialization:
    """Tests for Plivo dataclass defaults."""

    def test_dataclass_defaults(self):
        """Test dataclasses default their fields to None."""
        assert SendSMSResponse().api_id is None
        assert SendSMSResponse().message_uuid is None
        assert GetMessageResponse().message_state is None
        assert SMS().src is None
        assert Call().from_ is None
        assert Call().answer_method is None
