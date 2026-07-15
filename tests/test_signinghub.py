# Copyright (c) Microsoft Corporation. All rights reserved.

"""Unit tests for SigninghubClient."""

from unittest.mock import AsyncMock, patch

import pytest

from azure.connectors.signinghub import (
    SigninghubClient,
    CheckBoxFieldRequest,
    UpdateCheckBoxFieldRequest,
)
from azure.connectors.sdk import (
    ConnectorClientOptions,
    ConnectorException,
    ManagedIdentityTokenProvider,
)
from tests.conftest import MockResponse


class TestSigninghubClientInitialization:
    """Tests for SigninghubClient initialization."""

    def test_init_with_valid_url_and_defaults(self):
        """Test initialization with valid URL and default parameters."""
        client = SigninghubClient("https://example.azure.com/connections/test")

        assert client._connection_runtime_url == "https://example.azure.com/connections/test"
        assert client.connector_name == "signinghub"
        assert isinstance(client._http_client._token_provider, ManagedIdentityTokenProvider)

    def test_init_with_trailing_slash(self):
        """Test that trailing slash is removed from URL."""
        client = SigninghubClient("https://example.azure.com/connections/test/")

        assert client._connection_runtime_url == "https://example.azure.com/connections/test"

    def test_init_with_custom_token_provider(self, mock_token_provider):
        """Test initialization with custom token provider."""
        client = SigninghubClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider,
        )

        assert client._http_client._token_provider is mock_token_provider

    def test_init_with_custom_options(self, mock_token_provider):
        """Test initialization with custom options."""
        options = ConnectorClientOptions(timeout_seconds=60.0, max_retry_attempts=5)
        client = SigninghubClient(
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
            SigninghubClient("")

    def test_init_with_none_url_raises_error(self):
        """Test that None URL raises ValueError."""
        with pytest.raises(ValueError, match="connection_runtime_url cannot be None or empty"):
            SigninghubClient(None)

    def test_connector_name_property(self, mock_token_provider):
        """Test connector_name property returns 'signinghub'."""
        client = SigninghubClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider,
        )

        assert client.connector_name == "signinghub"


class TestSigninghubClientLifecycle:
    """Tests for SigninghubClient lifecycle methods."""

    @pytest.mark.asyncio
    async def test_close(self, mock_token_provider):
        """Test close method calls http_client.close."""
        client = SigninghubClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider,
        )

        with patch.object(client._http_client, "close", new_callable=AsyncMock) as mock_close:
            await client.close()
            mock_close.assert_called_once()

    @pytest.mark.asyncio
    async def test_context_manager(self, mock_token_provider):
        """Test async context manager functionality."""
        with patch.object(SigninghubClient, "close", new_callable=AsyncMock) as mock_close:
            async with SigninghubClient(
                "https://example.azure.com/connections/test",
                token_provider=mock_token_provider,
            ) as client:
                assert isinstance(client, SigninghubClient)

            mock_close.assert_called_once()


class TestContactsGetAsync:
    """Tests for contacts_get_async method (GET with query parameters)."""

    @pytest.mark.asyncio
    async def test_success_serializes_path_and_query(self, mock_token_provider):
        """Test successful contacts retrieval serializes path and query params."""
        client = SigninghubClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider,
        )
        mock_response = MockResponse(status=200, text='{"value": [{"email": "a@b.com"}]}')

        with patch.object(
            client._http_client,
            "send_async",
            new_callable=AsyncMock,
            return_value=mock_response,
        ) as mock_send:
            result = await client.contacts_get_async(
                record_per_page="10",
                page_no="1",
                sort_by="name",
                asc="true",
            )

            mock_send.assert_called_once()
            method, path = mock_send.call_args[0][0], mock_send.call_args[0][1]
            assert method == "GET"
            assert "/v4/settings/contacts/10/1" in path
            assert "sort-by=name" in path
            assert "asc=true" in path
            assert result is not None
            assert "value" in result

    @pytest.mark.asyncio
    async def test_error_response_raises_connector_exception(self, mock_token_provider):
        """Test that a non-2xx response raises ConnectorException."""
        client = SigninghubClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider,
        )
        mock_response = MockResponse(status=404, text="Not Found")

        with patch.object(
            client._http_client,
            "send_async",
            new_callable=AsyncMock,
            return_value=mock_response,
        ):
            with pytest.raises(ConnectorException) as exc_info:
                await client.contacts_get_async(record_per_page="10", page_no="1")

            assert exc_info.value.status_code == 404


class TestCheckboxAddCheckBoxAsync:
    """Tests for checkbox_add_check_box_async method (POST with body)."""

    @pytest.mark.asyncio
    async def test_success_forwards_request_body(self, mock_token_provider):
        """Test that the POST operation forwards the request body to send_async."""
        client = SigninghubClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider,
        )
        request = CheckBoxFieldRequest()
        mock_response = MockResponse(status=200, text='{"field_id": "cb-1"}')

        with patch.object(
            client._http_client,
            "send_async",
            new_callable=AsyncMock,
            return_value=mock_response,
        ) as mock_send:
            result = await client.checkbox_add_check_box_async(
                input=request,
                package_id="pkg-1",
                document_id="doc-1",
            )

            mock_send.assert_called_once()
            method, path = mock_send.call_args[0][0], mock_send.call_args[0][1]
            assert method == "POST"
            assert path.endswith("/packages/pkg-1/documents/doc-1/fields/checkbox")
            assert mock_send.call_args.kwargs["body"] is request
            assert result is not None

    @pytest.mark.asyncio
    async def test_error_response_raises_connector_exception(self, mock_token_provider):
        """Test that a non-2xx response raises ConnectorException."""
        client = SigninghubClient(
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
            with pytest.raises(ConnectorException):
                await client.checkbox_add_check_box_async(
                    input=CheckBoxFieldRequest(),
                    package_id="pkg-1",
                    document_id="doc-1",
                )


class TestCheckboxUpdateCheckBoxAsync:
    """Tests for checkbox_update_check_box_async method (PUT with body)."""

    @pytest.mark.asyncio
    async def test_success_forwards_request_body(self, mock_token_provider):
        """Test that the PUT operation forwards the request body to send_async."""
        client = SigninghubClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider,
        )
        request = UpdateCheckBoxFieldRequest()
        mock_response = MockResponse(status=200, text='{"field_id": "cb-1"}')

        with patch.object(
            client._http_client,
            "send_async",
            new_callable=AsyncMock,
            return_value=mock_response,
        ) as mock_send:
            result = await client.checkbox_update_check_box_async(
                input=request,
                package_id="pkg-1",
                document_id="doc-1",
            )

            mock_send.assert_called_once()
            assert mock_send.call_args[0][0] == "PUT"
            assert mock_send.call_args.kwargs["body"] is request
            assert result is not None

    @pytest.mark.asyncio
    async def test_error_response_raises_connector_exception(self, mock_token_provider):
        """Test that a non-2xx response raises ConnectorException."""
        client = SigninghubClient(
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
            with pytest.raises(ConnectorException):
                await client.checkbox_update_check_box_async(
                    input=UpdateCheckBoxFieldRequest(),
                    package_id="pkg-1",
                    document_id="doc-1",
                )


class TestAttachmentDeleteAttachmentAsync:
    """Tests for attachment_delete_attachment_async method (DELETE)."""

    @pytest.mark.asyncio
    async def test_success_completes_without_error(self, mock_token_provider):
        """Test successful delete completes without raising."""
        client = SigninghubClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider,
        )
        mock_response = MockResponse(status=204, text="")

        with patch.object(
            client._http_client,
            "send_async",
            new_callable=AsyncMock,
            return_value=mock_response,
        ) as mock_send:
            result = await client.attachment_delete_attachment_async(
                package_id="pkg-1",
                document_id="doc-1",
                attachment_id="att-1",
            )

            mock_send.assert_called_once()
            method, path = mock_send.call_args[0][0], mock_send.call_args[0][1]
            assert method == "DELETE"
            assert path.endswith(
                "/packages/pkg-1/documents/doc-1/attachments/att-1"
            )
            assert result is None

    @pytest.mark.asyncio
    async def test_not_found_raises_connector_exception(self, mock_token_provider):
        """Test that a 404 response raises ConnectorException."""
        client = SigninghubClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider,
        )
        mock_response = MockResponse(status=404, text="Attachment not found")

        with patch.object(
            client._http_client,
            "send_async",
            new_callable=AsyncMock,
            return_value=mock_response,
        ):
            with pytest.raises(ConnectorException) as exc_info:
                await client.attachment_delete_attachment_async(
                    package_id="pkg-1",
                    document_id="doc-1",
                    attachment_id="missing",
                )

            assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    async def test_server_error_raises_connector_exception(self, mock_token_provider):
        """Test that a 5xx response raises ConnectorException."""
        client = SigninghubClient(
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
                await client.attachment_delete_attachment_async(
                    package_id="pkg-1",
                    document_id="doc-1",
                    attachment_id="att-1",
                )
