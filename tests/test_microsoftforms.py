# Copyright (c) Microsoft Corporation. All rights reserved.

"""Unit tests for MicrosoftformsClient."""

from unittest.mock import AsyncMock, patch

import pytest

from azure.connectors.microsoftforms import MicrosoftformsClient, WebhookRequestBody
from azure.connectors.sdk import (
    ConnectorClientOptions,
    ConnectorException,
    ManagedIdentityTokenProvider,
)
from tests.conftest import MockResponse


class TestMicrosoftformsClientInitialization:
    """Tests for MicrosoftformsClient initialization."""

    def test_init_with_valid_url_and_defaults(self):
        """Test initialization with valid URL and default parameters."""
        client = MicrosoftformsClient("https://example.azure.com/connections/test")

        assert client._connection_runtime_url == "https://example.azure.com/connections/test"
        assert client.connector_name == "microsoftforms"
        assert isinstance(client._http_client._token_provider, ManagedIdentityTokenProvider)

    def test_init_with_trailing_slash(self):
        """Test that trailing slash is removed from URL."""
        client = MicrosoftformsClient("https://example.azure.com/connections/test/")

        assert client._connection_runtime_url == "https://example.azure.com/connections/test"

    def test_init_with_custom_token_provider(self, mock_token_provider):
        """Test initialization with custom token provider."""
        client = MicrosoftformsClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider,
        )

        assert client._http_client._token_provider is mock_token_provider

    def test_init_with_custom_options(self, mock_token_provider):
        """Test initialization with custom options."""
        options = ConnectorClientOptions(timeout_seconds=60.0, max_retry_attempts=5)
        client = MicrosoftformsClient(
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
            MicrosoftformsClient("")

    def test_init_with_none_url_raises_error(self):
        """Test that None URL raises ValueError."""
        with pytest.raises(ValueError, match="connection_runtime_url cannot be None or empty"):
            MicrosoftformsClient(None)

    def test_connector_name_property(self, mock_token_provider):
        """Test connector_name property returns 'microsoftforms'."""
        client = MicrosoftformsClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider,
        )

        assert client.connector_name == "microsoftforms"


class TestMicrosoftformsClientLifecycle:
    """Tests for MicrosoftformsClient lifecycle methods."""

    @pytest.mark.asyncio
    async def test_close(self, mock_token_provider):
        """Test close method calls http_client.close."""
        client = MicrosoftformsClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider,
        )

        with patch.object(client._http_client, "close", new_callable=AsyncMock) as mock_close:
            await client.close()
            mock_close.assert_called_once()

    @pytest.mark.asyncio
    async def test_context_manager(self, mock_token_provider):
        """Test async context manager functionality."""
        with patch.object(MicrosoftformsClient, "close", new_callable=AsyncMock) as mock_close:
            async with MicrosoftformsClient(
                "https://example.azure.com/connections/test",
                token_provider=mock_token_provider,
            ) as client:
                assert isinstance(client, MicrosoftformsClient)

            mock_close.assert_called_once()


class TestCreateFormWebhookAsync:
    """Tests for create_form_webhook_async method."""

    @pytest.mark.asyncio
    async def test_success(self, mock_token_provider):
        """Test successful webhook creation."""
        client = MicrosoftformsClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider,
        )
        payload = WebhookRequestBody(
            event_type="newResponse",
            notification_url="https://contoso.example/callback",
            source="flow",
        )
        mock_response = MockResponse(status=201, text="")

        with patch.object(
            client._http_client,
            "send_async",
            new_callable=AsyncMock,
            return_value=mock_response,
        ) as mock_send:
            result = await client.create_form_webhook_async(input=payload, form_id="form-123")

            assert result is None
            mock_send.assert_called_once()
            method, path = mock_send.call_args[0][0], mock_send.call_args[0][1]
            assert method == "POST"
            assert "/formapi/api/forms/form-123/webhooks" in path

    @pytest.mark.asyncio
    async def test_error_response_raises_exception(self, mock_token_provider):
        """Test that error response raises ConnectorException."""
        client = MicrosoftformsClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider,
        )
        payload = WebhookRequestBody(event_type="newResponse")
        mock_response = MockResponse(status=403, text='{"error": "Forbidden"}')

        with patch.object(
            client._http_client,
            "send_async",
            new_callable=AsyncMock,
            return_value=mock_response,
        ):
            with pytest.raises(ConnectorException):
                await client.create_form_webhook_async(input=payload, form_id="form-123")


class TestListFormsAsync:
    """Tests for list_forms_async method."""

    @pytest.mark.asyncio
    async def test_success(self, mock_token_provider):
        """Test successful form listing."""
        client = MicrosoftformsClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider,
        )
        mock_response = MockResponse(
            status=200, text='{"value": [{"id": "form-1", "title": "Survey"}]}')

        with patch.object(
            client._http_client,
            "send_async",
            new_callable=AsyncMock,
            return_value=mock_response,
        ) as mock_send:
            result = await client.list_forms_async()

            mock_send.assert_called_once()
            method, path = mock_send.call_args[0][0], mock_send.call_args[0][1]
            assert method == "GET"
            assert path.endswith("/formapi/api/forms")
            assert result is not None
            assert "value" in result

    @pytest.mark.asyncio
    async def test_error_response_raises_exception(self, mock_token_provider):
        """Test that error response raises ConnectorException."""
        client = MicrosoftformsClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider,
        )
        mock_response = MockResponse(status=500, text='{"error": "Server error"}')

        with patch.object(
            client._http_client,
            "send_async",
            new_callable=AsyncMock,
            return_value=mock_response,
        ):
            with pytest.raises(ConnectorException):
                await client.list_forms_async()


class TestGetFormDetailsByIdAsync:
    """Tests for get_form_details_by_id_async method."""

    @pytest.mark.asyncio
    async def test_success(self, mock_token_provider):
        """Test successful details retrieval."""
        client = MicrosoftformsClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider,
        )
        mock_response = MockResponse(status=200, text='{"title": "Survey", "status": "active"}')

        with patch.object(
            client._http_client,
            "send_async",
            new_callable=AsyncMock,
            return_value=mock_response,
        ) as mock_send:
            result = await client.get_form_details_by_id_async(form_id="form-123")

            mock_send.assert_called_once()
            method, path = mock_send.call_args[0][0], mock_send.call_args[0][1]
            assert method == "GET"
            assert "/formapi/api/forms('form-123')" in path
            assert "$select=title%2CmodifiedDate%2CcreatedDate%2Cstatus%2CcreatedBy" in path
            assert result is not None
            assert result.get("title") == "Survey"

    @pytest.mark.asyncio
    async def test_error_response_raises_exception(self, mock_token_provider):
        """Test that error response raises ConnectorException."""
        client = MicrosoftformsClient(
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
            with pytest.raises(ConnectorException):
                await client.get_form_details_by_id_async(form_id="missing")


class TestGetQuestionsAsync:
    """Tests for get_questions_async method."""

    @pytest.mark.asyncio
    async def test_success(self, mock_token_provider):
        """Test successful questions retrieval."""
        client = MicrosoftformsClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider,
        )
        mock_response = MockResponse(
            status=200, text='{"value": [{"id": "q1", "title": "How satisfied are you?"}]}')

        with patch.object(
            client._http_client,
            "send_async",
            new_callable=AsyncMock,
            return_value=mock_response,
        ) as mock_send:
            result = await client.get_questions_async(form_id="form-123")

            mock_send.assert_called_once()
            method, path = mock_send.call_args[0][0], mock_send.call_args[0][1]
            assert method == "GET"
            assert "/formapi/api/forms('form-123')/questions" in path
            assert result is not None
            assert "value" in result

    @pytest.mark.asyncio
    async def test_error_response_raises_exception(self, mock_token_provider):
        """Test that error response raises ConnectorException."""
        client = MicrosoftformsClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider,
        )
        mock_response = MockResponse(status=401, text='{"error": "Unauthorized"}')

        with patch.object(
            client._http_client,
            "send_async",
            new_callable=AsyncMock,
            return_value=mock_response,
        ):
            with pytest.raises(ConnectorException):
                await client.get_questions_async(form_id="form-123")
