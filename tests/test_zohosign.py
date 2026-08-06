# Copyright (c) Microsoft Corporation. All rights reserved.

"""Unit tests for ZohosignClient."""

from unittest.mock import AsyncMock, patch

import pytest

from azure.connectors.sdk import ConnectorException, ManagedIdentityTokenProvider
from azure.connectors.zohosign import InvokeAPIInput, UpdateDocumentInput, ZohosignClient
from tests.conftest import MockResponse


class TestZohosignClientInitialization:
    """Tests for ZohosignClient initialization and lifecycle."""

    def test_init_with_valid_url_and_defaults(self):
        """Test initialization with the default token provider."""
        client = ZohosignClient("https://example.azure.com/connections/test/")

        assert client._connection_runtime_url == "https://example.azure.com/connections/test"
        assert client.connector_name == "zohosign"
        assert isinstance(client._http_client._token_provider, ManagedIdentityTokenProvider)

    @pytest.mark.asyncio
    async def test_context_manager_closes_client(self, mock_token_provider):
        """Test the async context manager closes the client."""
        with patch.object(ZohosignClient, "close", new_callable=AsyncMock) as mock_close:
            async with ZohosignClient(
                "https://example.azure.com/connections/test",
                token_provider=mock_token_provider,
            ):
                pass

            mock_close.assert_called_once()


class TestZohosignOperations:
    """Tests for representative Zoho Sign operations."""

    @pytest.mark.asyncio
    async def test_get_document_success(self, mock_token_provider):
        """Test document retrieval serializes the request path."""
        client = ZohosignClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider,
        )
        mock_response = MockResponse(status=200, text='{"status": "success"}')

        with patch.object(
            client._http_client,
            "send_async",
            new_callable=AsyncMock,
            return_value=mock_response,
        ) as mock_send:
            result = await client.get_document_async(request_id="request-1")

            assert mock_send.call_args.args[0] == "GET"
            assert mock_send.call_args.args[1].endswith("/requests/request-1")
            assert result == {"status": "success"}

    @pytest.mark.asyncio
    async def test_invoke_api_forwards_body(self, mock_token_provider):
        """Test generic API invocation forwards its dynamic body."""
        client = ZohosignClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider,
        )
        payload = InvokeAPIInput(additional_properties={"name": "contract"})
        mock_response = MockResponse(status=200, text='{"code": 0}')

        with patch.object(
            client._http_client,
            "send_async",
            new_callable=AsyncMock,
            return_value=mock_response,
        ) as mock_send:
            await client.invoke_a_p_i_async(input=payload, url="requests", method="POST")

            assert mock_send.call_args.kwargs["body"] is payload
            assert "method=POST" in mock_send.call_args.args[1]

    @pytest.mark.asyncio
    async def test_update_document_forwards_body(self, mock_token_provider):
        """Test document update forwards its typed body."""
        client = ZohosignClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider,
        )
        payload = UpdateDocumentInput(requests={"request_name": "Contract"})
        mock_response = MockResponse(status=200, text='{"status": "success"}')

        with patch.object(
            client._http_client,
            "send_async",
            new_callable=AsyncMock,
            return_value=mock_response,
        ) as mock_send:
            await client.update_document_async(input=payload, request_id="request-1")

            assert mock_send.call_args.args[0] == "PUT"
            assert mock_send.call_args.kwargs["body"] is payload

    @pytest.mark.asyncio
    async def test_non_success_response_raises_exception(self, mock_token_provider):
        """Test API errors raise ConnectorException."""
        client = ZohosignClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider,
        )
        mock_response = MockResponse(status=404, text='{"error": "Not found"}')

        with patch.object(
            client._http_client,
            "send_async",
            new_callable=AsyncMock,
            return_value=mock_response,
        ):
            with pytest.raises(ConnectorException) as exc_info:
                await client.get_document_async(request_id="missing")

            assert exc_info.value.status_code == 404

    def test_multipart_create_document_is_not_generated(self):
        """Test the unsupported multipart operation is excluded."""
        assert not hasattr(ZohosignClient, "create_document_async")
