# Copyright (c) Microsoft Corporation. All rights reserved.

"""Unit tests for UniversalprintClient."""

import pytest
from unittest.mock import AsyncMock, patch

from azure.connectors.universalprint import (
    PrintFileInput,
    UniversalprintClient,
)
from azure.connectors.sdk import (
    ConnectorClientOptions,
    ConnectorException,
    ManagedIdentityTokenProvider,
)
from tests.conftest import MockResponse


async def _invoke_operation(client: UniversalprintClient, operation: str):
    """Invoke a Universal Print operation by name for shared tests."""
    if operation == "print_file":
        return await client.print_file_async(
            input=PrintFileInput(),
            printer="printer123",
            file_name="document.pdf",
        )
    if operation == "list_recent_shares":
        return await client.list_recent_shares_async()

    raise ValueError(f"Unsupported operation '{operation}'.")


class TestUniversalprintClientInitialization:
    """Tests for UniversalprintClient initialization."""

    def test_init_with_valid_url_and_defaults(self):
        """Test initialization with valid URL and default parameters."""
        client = UniversalprintClient("https://example.azure.com/connections/test")

        assert client._connection_runtime_url == "https://example.azure.com/connections/test"
        assert client.connector_name == "universalprint"
        assert isinstance(client._http_client._token_provider, ManagedIdentityTokenProvider)

    def test_init_with_trailing_slash(self):
        """Test that trailing slash is removed from URL."""
        client = UniversalprintClient("https://example.azure.com/connections/test/")

        assert client._connection_runtime_url == "https://example.azure.com/connections/test"

    def test_init_with_custom_token_provider(self, mock_token_provider):
        """Test initialization with custom token provider."""
        client = UniversalprintClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider,
        )

        assert client._http_client._token_provider is mock_token_provider

    def test_init_with_custom_options(self, mock_token_provider):
        """Test initialization with custom options."""
        options = ConnectorClientOptions(timeout_seconds=60.0, max_retry_attempts=5)
        client = UniversalprintClient(
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
            UniversalprintClient("")

    def test_init_with_none_url_raises_error(self):
        """Test that None URL raises ValueError."""
        with pytest.raises(ValueError, match="connection_runtime_url cannot be None or empty"):
            UniversalprintClient(None)

    def test_connector_name_property(self, mock_token_provider):
        """Test connector_name property returns 'universalprint'."""
        client = UniversalprintClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider,
        )

        assert client.connector_name == "universalprint"


class TestUniversalprintClientLifecycle:
    """Tests for UniversalprintClient lifecycle methods."""

    @pytest.mark.asyncio
    async def test_close(self, mock_token_provider):
        """Test close method calls http_client.close."""
        client = UniversalprintClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider,
        )

        with patch.object(client._http_client, "close", new_callable=AsyncMock) as mock_close:
            await client.close()
            mock_close.assert_called_once()

    @pytest.mark.asyncio
    async def test_context_manager(self, mock_token_provider):
        """Test async context manager functionality."""
        with patch.object(UniversalprintClient, "close", new_callable=AsyncMock) as mock_close:
            async with UniversalprintClient(
                "https://example.azure.com/connections/test",
                token_provider=mock_token_provider,
            ) as client:
                assert isinstance(client, UniversalprintClient)

            mock_close.assert_called_once()


class TestUniversalprintClientMethods:
    """Success path tests for Universal Print methods."""

    @pytest.mark.asyncio
    async def test_print_file_success(self, mock_token_provider):
        """Test print_file_async posts the body to the shares endpoint."""
        client = UniversalprintClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider,
        )
        mock_response = MockResponse(status=202, text="")
        body = PrintFileInput()

        with patch.object(
            client._http_client,
            "send_async",
            new_callable=AsyncMock,
            return_value=mock_response,
        ) as mock_send:
            result = await client.print_file_async(
                input=body,
                printer="printer123",
                file_name="document.pdf",
            )

            assert result is None
            assert mock_send.call_args[0][0] == "POST"
            assert "/v1.0/print/shares" in mock_send.call_args[0][1]
            assert mock_send.call_args.kwargs["body"] is body

    @pytest.mark.asyncio
    async def test_print_file_includes_query_params(self, mock_token_provider):
        """Test print_file_async serializes printer, file name, and configuration params."""
        client = UniversalprintClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider,
        )
        mock_response = MockResponse(status=202, text="")

        with patch.object(
            client._http_client,
            "send_async",
            new_callable=AsyncMock,
            return_value=mock_response,
        ) as mock_send:
            await client.print_file_async(
                input=PrintFileInput(),
                printer="printer123",
                file_name="document.pdf",
                configuration_copies="2",
                configuration_color_mode="color",
            )

            request_url = mock_send.call_args[0][1]
            assert "printer=printer123" in request_url
            assert "fileName=document.pdf" in request_url
            assert "configuration_copies=2" in request_url
            assert "configuration_colorMode=color" in request_url

    @pytest.mark.asyncio
    async def test_list_recent_shares_success(self, mock_token_provider):
        """Test list_recent_shares_async returns parsed JSON."""
        client = UniversalprintClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider,
        )
        mock_response = MockResponse(status=200, text='{"value":[{"id":"share123"}]}')

        with patch.object(
            client._http_client,
            "send_async",
            new_callable=AsyncMock,
            return_value=mock_response,
        ) as mock_send:
            result = await client.list_recent_shares_async()

            assert result["value"][0]["id"] == "share123"
            assert mock_send.call_args[0][0] == "GET"
            assert "/beta/me/print/recentPrinterShares" in mock_send.call_args[0][1]

    @pytest.mark.asyncio
    async def test_list_recent_shares_empty_returns_none(self, mock_token_provider):
        """Test list_recent_shares_async returns None for an empty body."""
        client = UniversalprintClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider,
        )
        mock_response = MockResponse(status=200, text="")

        with patch.object(
            client._http_client,
            "send_async",
            new_callable=AsyncMock,
            return_value=mock_response,
        ):
            result = await client.list_recent_shares_async()

            assert result is None


class TestUniversalprintClientErrorHandling:
    """Error handling tests that ensure all methods raise ConnectorException."""

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "operation",
        [
            "print_file",
            "list_recent_shares",
        ],
    )
    async def test_error_response_raises_exception_for_all_operations(
        self,
        mock_token_provider,
        operation,
    ):
        """Test non-2xx responses raise ConnectorException for every operation."""
        client = UniversalprintClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider,
        )
        mock_response = MockResponse(status=500, text='{"error":"server failure"}')

        with patch.object(
            client._http_client,
            "send_async",
            new_callable=AsyncMock,
            return_value=mock_response,
        ):
            with pytest.raises(ConnectorException):
                await _invoke_operation(client, operation)
