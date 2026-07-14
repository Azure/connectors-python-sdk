# Copyright (c) Microsoft Corporation. All rights reserved.

"""Unit tests for CloudmersiveconvertClient."""

from unittest.mock import AsyncMock, patch

import pytest

from azure.connectors.cloudmersiveconvert import (
    CloudmersiveconvertClient,
    GetDocxBodyRequest,
    GetDocxGetCommentsHierarchicalRequest,
)
from azure.connectors.sdk import (
    ConnectorClientOptions,
    ConnectorException,
    ManagedIdentityTokenProvider,
)
from tests.conftest import MockResponse


class TestCloudmersiveconvertClientInitialization:
    """Tests for CloudmersiveconvertClient initialization."""

    def test_init_with_valid_url_and_defaults(self):
        """Test initialization with valid URL and default parameters."""
        client = CloudmersiveconvertClient("https://example.azure.com/connections/test")

        assert client._connection_runtime_url == "https://example.azure.com/connections/test"
        assert client.connector_name == "cloudmersiveconvert"
        assert isinstance(client._http_client._token_provider, ManagedIdentityTokenProvider)

    def test_init_with_trailing_slash(self):
        """Test that trailing slash is removed from URL."""
        client = CloudmersiveconvertClient("https://example.azure.com/connections/test/")

        assert client._connection_runtime_url == "https://example.azure.com/connections/test"

    def test_init_with_custom_token_provider(self, mock_token_provider):
        """Test initialization with custom token provider."""
        client = CloudmersiveconvertClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider,
        )

        assert client._http_client._token_provider is mock_token_provider

    def test_init_with_custom_options(self, mock_token_provider):
        """Test initialization with custom options."""
        options = ConnectorClientOptions(timeout_seconds=60.0, max_retry_attempts=5)
        client = CloudmersiveconvertClient(
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
            CloudmersiveconvertClient("")

    def test_init_with_none_url_raises_error(self):
        """Test that None URL raises ValueError."""
        with pytest.raises(ValueError, match="connection_runtime_url cannot be None or empty"):
            CloudmersiveconvertClient(None)

    def test_connector_name_property(self, mock_token_provider):
        """Test connector_name property returns 'cloudmersiveconvert'."""
        client = CloudmersiveconvertClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider,
        )

        assert client.connector_name == "cloudmersiveconvert"


class TestCloudmersiveconvertClientLifecycle:
    """Tests for CloudmersiveconvertClient lifecycle methods."""

    @pytest.mark.asyncio
    async def test_close(self, mock_token_provider):
        """Test close method calls http_client.close."""
        client = CloudmersiveconvertClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider,
        )

        with patch.object(client._http_client, "close", new_callable=AsyncMock) as mock_close:
            await client.close()
            mock_close.assert_called_once()

    @pytest.mark.asyncio
    async def test_context_manager(self, mock_token_provider):
        """Test async context manager functionality."""
        with patch.object(CloudmersiveconvertClient, "close", new_callable=AsyncMock) as mock_close:
            async with CloudmersiveconvertClient(
                "https://example.azure.com/connections/test",
                token_provider=mock_token_provider,
            ) as client:
                assert isinstance(client, CloudmersiveconvertClient)

            mock_close.assert_called_once()


class TestEditDocumentDocxBodyAsync:
    """Tests for edit_document_docx_body_async method (POST with body)."""

    @pytest.mark.asyncio
    async def test_success_forwards_request_body(self, mock_token_provider):
        """Test that the POST operation forwards the request body to send_async."""
        client = CloudmersiveconvertClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider,
        )
        request = GetDocxBodyRequest()
        mock_response = MockResponse(status=200, text='{"successful": true}')

        with patch.object(
            client._http_client,
            "send_async",
            new_callable=AsyncMock,
            return_value=mock_response,
        ) as mock_send:
            result = await client.edit_document_docx_body_async(input=request)

            mock_send.assert_called_once()
            method, path = mock_send.call_args[0][0], mock_send.call_args[0][1]
            assert method == "POST"
            assert path.endswith("/convert/edit/docx/get-body")
            assert mock_send.call_args.kwargs["body"] is request
            assert result is not None
            assert result["successful"] is True

    @pytest.mark.asyncio
    async def test_error_response_raises_connector_exception(self, mock_token_provider):
        """Test that a non-2xx response raises ConnectorException."""
        client = CloudmersiveconvertClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider,
        )
        mock_response = MockResponse(status=400, text="Bad Request")

        with patch.object(
            client._http_client,
            "send_async",
            new_callable=AsyncMock,
            return_value=mock_response,
        ):
            with pytest.raises(ConnectorException) as exc_info:
                await client.edit_document_docx_body_async(input=GetDocxBodyRequest())

            assert exc_info.value.status_code == 400


class TestEditDocumentDocxGetCommentsHierarchicalAsync:
    """Tests for edit_document_docx_get_comments_hierarchical_async method."""

    @pytest.mark.asyncio
    async def test_success_forwards_request_body(self, mock_token_provider):
        """Test that the POST operation forwards the request body to send_async."""
        client = CloudmersiveconvertClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider,
        )
        request = GetDocxGetCommentsHierarchicalRequest()
        mock_response = MockResponse(status=200, text='{"Comments": []}')

        with patch.object(
            client._http_client,
            "send_async",
            new_callable=AsyncMock,
            return_value=mock_response,
        ) as mock_send:
            result = await client.edit_document_docx_get_comments_hierarchical_async(
                input=request
            )

            mock_send.assert_called_once()
            method, path = mock_send.call_args[0][0], mock_send.call_args[0][1]
            assert method == "POST"
            assert path.endswith("/convert/edit/docx/get-comments/hierarchical")
            assert mock_send.call_args.kwargs["body"] is request
            assert result is not None

    @pytest.mark.asyncio
    async def test_server_error_raises_connector_exception(self, mock_token_provider):
        """Test that a 5xx response raises ConnectorException."""
        client = CloudmersiveconvertClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider,
        )
        mock_response = MockResponse(status=500, text="Internal Server Error")

        with patch.object(
            client._http_client,
            "send_async",
            new_callable=AsyncMock,
            return_value=mock_response,
        ):
            with pytest.raises(ConnectorException):
                await client.edit_document_docx_get_comments_hierarchical_async(
                    input=GetDocxGetCommentsHierarchicalRequest()
                )


class TestConvertDocumentAutodetectGetInfoAsync:
    """Tests for convert_document_autodetect_get_info_async method (POST, no body)."""

    @pytest.mark.asyncio
    async def test_success_sends_post_with_no_body(self, mock_token_provider):
        """Test that the no-body POST operation sends body=None to send_async."""
        client = CloudmersiveconvertClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider,
        )
        mock_response = MockResponse(status=200, text='{"Successful": true}')

        with patch.object(
            client._http_client,
            "send_async",
            new_callable=AsyncMock,
            return_value=mock_response,
        ) as mock_send:
            result = await client.convert_document_autodetect_get_info_async()

            mock_send.assert_called_once()
            method, path = mock_send.call_args[0][0], mock_send.call_args[0][1]
            assert method == "POST"
            assert path.endswith("/convert/autodetect/get-info")
            assert mock_send.call_args.kwargs["body"] is None
            assert result is not None

    @pytest.mark.asyncio
    async def test_error_response_raises_connector_exception(self, mock_token_provider):
        """Test that a non-2xx response raises ConnectorException."""
        client = CloudmersiveconvertClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider,
        )
        mock_response = MockResponse(status=422, text="Unprocessable Entity")

        with patch.object(
            client._http_client,
            "send_async",
            new_callable=AsyncMock,
            return_value=mock_response,
        ):
            with pytest.raises(ConnectorException):
                await client.convert_document_autodetect_get_info_async()
