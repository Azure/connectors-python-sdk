# Copyright (c) Microsoft Corporation. All rights reserved.

"""Unit tests for DocusignClient."""

from unittest.mock import AsyncMock, patch

import pytest

from azure.connectors.docusign import (
    DocusignClient,
    CombinedEmailBodyAndCustomFields,
    DynamicSigners,
    UpdateDocgenFormFieldsInput,
)
from azure.connectors.sdk import (
    ConnectorClientOptions,
    ConnectorException,
    ManagedIdentityTokenProvider,
)
from tests.conftest import MockResponse


class TestDocusignClientInitialization:
    """Tests for DocusignClient initialization."""

    def test_init_with_valid_url_and_defaults(self):
        """Test initialization with valid URL and default parameters."""
        client = DocusignClient("https://example.azure.com/connections/test")

        assert client._connection_runtime_url == "https://example.azure.com/connections/test"
        assert client.connector_name == "docusign"
        assert isinstance(client._http_client._token_provider, ManagedIdentityTokenProvider)

    def test_init_with_trailing_slash(self):
        """Test that trailing slash is removed from URL."""
        client = DocusignClient("https://example.azure.com/connections/test/")

        assert client._connection_runtime_url == "https://example.azure.com/connections/test"

    def test_init_with_custom_token_provider(self, mock_token_provider):
        """Test initialization with custom token provider."""
        client = DocusignClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider,
        )

        assert client._http_client._token_provider is mock_token_provider

    def test_init_with_custom_options(self, mock_token_provider):
        """Test initialization with custom options."""
        options = ConnectorClientOptions(timeout_seconds=60.0, max_retry_attempts=5)
        client = DocusignClient(
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
            DocusignClient("")

    def test_init_with_none_url_raises_error(self):
        """Test that None URL raises ValueError."""
        with pytest.raises(ValueError, match="connection_runtime_url cannot be None or empty"):
            DocusignClient(None)

    def test_connector_name_property(self, mock_token_provider):
        """Test connector_name property returns 'docusign'."""
        client = DocusignClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider,
        )

        assert client.connector_name == "docusign"


class TestDocusignClientLifecycle:
    """Tests for DocusignClient lifecycle methods."""

    @pytest.mark.asyncio
    async def test_close(self, mock_token_provider):
        """Test close method calls http_client.close."""
        client = DocusignClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider,
        )

        with patch.object(client._http_client, "close", new_callable=AsyncMock) as mock_close:
            await client.close()
            mock_close.assert_called_once()

    @pytest.mark.asyncio
    async def test_context_manager(self, mock_token_provider):
        """Test async context manager functionality."""
        with patch.object(DocusignClient, "close", new_callable=AsyncMock) as mock_close:
            async with DocusignClient(
                "https://example.azure.com/connections/test",
                token_provider=mock_token_provider,
            ) as client:
                assert isinstance(client, DocusignClient)

            mock_close.assert_called_once()


class TestGetLoginAccountsAsync:
    """Tests for get_login_accounts_async method."""

    @pytest.mark.asyncio
    async def test_success(self, mock_token_provider):
        """Test successful login accounts retrieval."""
        client = DocusignClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider,
        )
        mock_response = MockResponse(status=200, text='{"accounts": [{"accountId": "123"}]}')

        with patch.object(
            client._http_client,
            "send_async",
            new_callable=AsyncMock,
            return_value=mock_response,
        ) as mock_send:
            result = await client.get_login_accounts_async()

            mock_send.assert_called_once()
            method, path = mock_send.call_args[0][0], mock_send.call_args[0][1]
            assert method == "GET"
            assert path.endswith("/oauth/userinfo")
            assert result is not None
            assert "accounts" in result

    @pytest.mark.asyncio
    async def test_error_response_raises_exception(self, mock_token_provider):
        """Test login accounts error path."""
        client = DocusignClient(
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
                await client.get_login_accounts_async()


class TestSearchListEnvelopesAsync:
    """Tests for search_list_envelopes_async method."""

    @pytest.mark.asyncio
    async def test_success_with_filters(self, mock_token_provider):
        """Test envelope search query parameter handling."""
        client = DocusignClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider,
        )
        mock_response = MockResponse(status=200, text='{"value": [{"envelopeId": "env-1"}]}')

        with patch.object(
            client._http_client,
            "send_async",
            new_callable=AsyncMock,
            return_value=mock_response,
        ) as mock_send:
            result = await client.search_list_envelopes_async(
                account_id="acct-1",
                envelope_title="Quarterly Contract",
                top="5",
                skip="0",
            )

            mock_send.assert_called_once()
            method, path = mock_send.call_args[0][0], mock_send.call_args[0][1]
            assert method == "GET"
            assert "/accounts/acct-1/envelopes/SearchListEnvelopes" in path
            assert "envelopeTitle=Quarterly%20Contract" in path
            assert "top=5" in path
            assert "skip=0" in path
            assert result is not None

    @pytest.mark.asyncio
    async def test_error_response_raises_exception(self, mock_token_provider):
        """Test envelope search error path."""
        client = DocusignClient(
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
                await client.search_list_envelopes_async(account_id="acct-1")


class TestCreateBlankEnvelopeAsync:
    """Tests for create_blank_envelope_async method."""

    @pytest.mark.asyncio
    async def test_success(self, mock_token_provider):
        """Test successful blank envelope creation."""
        client = DocusignClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider,
        )
        payload = CombinedEmailBodyAndCustomFields()
        mock_response = MockResponse(status=201, text='{"envelopeId": "env-1"}')

        with patch.object(
            client._http_client,
            "send_async",
            new_callable=AsyncMock,
            return_value=mock_response,
        ) as mock_send:
            result = await client.create_blank_envelope_async(
                input=payload,
                account_id="acct-1",
                email_subject="Please sign",
            )

            mock_send.assert_called_once()
            method, path = mock_send.call_args[0][0], mock_send.call_args[0][1]
            body = mock_send.call_args[1].get("body")
            assert method == "POST"
            assert "/accounts/acct-1/envelopes/createBlankEnvelopeV2" in path
            assert "emailSubject=Please%20sign" in path
            assert body is payload
            assert result is not None

    @pytest.mark.asyncio
    async def test_error_response_raises_exception(self, mock_token_provider):
        """Test blank envelope creation error path."""
        client = DocusignClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider,
        )
        payload = CombinedEmailBodyAndCustomFields()
        mock_response = MockResponse(status=400, text='{"error": "Bad request"}')

        with patch.object(
            client._http_client,
            "send_async",
            new_callable=AsyncMock,
            return_value=mock_response,
        ):
            with pytest.raises(ConnectorException):
                await client.create_blank_envelope_async(
                    input=payload,
                    account_id="acct-1",
                    email_subject="Please sign",
                )


class TestSendEnvelopeAsync:
    """Tests for send_envelope_async method."""

    @pytest.mark.asyncio
    async def test_success(self, mock_token_provider):
        """Test successful send envelope request."""
        client = DocusignClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider,
        )
        payload = DynamicSigners()
        mock_response = MockResponse(status=201, text='{"envelopeId": "env-2"}')

        with patch.object(
            client._http_client,
            "send_async",
            new_callable=AsyncMock,
            return_value=mock_response,
        ) as mock_send:
            result = await client.send_envelope_async(
                input=payload,
                account_id="acct-1",
                status="sent",
                template_id="template-1",
                email_subject="Sign this document",
            )

            mock_send.assert_called_once()
            method, path = mock_send.call_args[0][0], mock_send.call_args[0][1]
            body = mock_send.call_args[1].get("body")
            assert method == "POST"
            assert "/accounts/acct-1/envelopes" in path
            assert "status=sent" in path
            assert "templateId=template-1" in path
            assert body is payload
            assert result is not None

    @pytest.mark.asyncio
    async def test_error_response_raises_exception(self, mock_token_provider):
        """Test send envelope error path raises ConnectorException."""
        client = DocusignClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider,
        )
        payload = DynamicSigners()
        mock_response = MockResponse(status=400, text='{"error": "Invalid template"}')

        with patch.object(
            client._http_client,
            "send_async",
            new_callable=AsyncMock,
            return_value=mock_response,
        ):
            with pytest.raises(ConnectorException):
                await client.send_envelope_async(
                    input=payload,
                    account_id="acct-1",
                    status="sent",
                    template_id="bad-template",
                    email_subject="Sign this document",
                )


class TestUpdateDocgenFormFieldsAsync:
    """Tests for update_docgen_form_fields_async method (PUT with body)."""

    @pytest.mark.asyncio
    async def test_success_sends_body_and_returns_result(self, mock_token_provider):
        """Test PUT operation sends input body and returns response."""
        client = DocusignClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider,
        )
        payload = UpdateDocgenFormFieldsInput()
        mock_response = MockResponse(status=200, text='{"docgenFields": []}')

        with patch.object(
            client._http_client,
            "send_async",
            new_callable=AsyncMock,
            return_value=mock_response,
        ) as mock_send:
            await client.update_docgen_form_fields_async(
                input=payload,
                account_id="acct-1",
                envelope_id="env-1",
                document_guid=None,
            )

            mock_send.assert_called_once()
            method, path = mock_send.call_args[0][0], mock_send.call_args[0][1]
            body = mock_send.call_args[1].get("body")
            assert method == "PUT"
            assert "/accounts/acct-1/envelopes/env-1/docGenFormFields" in path
            assert body is payload

    @pytest.mark.asyncio
    async def test_error_response_raises_exception(self, mock_token_provider):
        """Test PUT error path raises ConnectorException."""
        client = DocusignClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider,
        )
        payload = UpdateDocgenFormFieldsInput()
        mock_response = MockResponse(status=422, text='{"error": "Invalid fields"}')

        with patch.object(
            client._http_client,
            "send_async",
            new_callable=AsyncMock,
            return_value=mock_response,
        ):
            with pytest.raises(ConnectorException):
                await client.update_docgen_form_fields_async(
                    input=payload,
                    account_id="acct-1",
                    envelope_id="env-1",
                    document_guid=None,
                )


class TestRemoveRecipientFromEnvelopeAsync:
    """Tests for remove_recipient_from_envelope_async method (DELETE)."""

    @pytest.mark.asyncio
    async def test_success_returns_result(self, mock_token_provider):
        """Test successful DELETE returns response."""
        client = DocusignClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider,
        )
        mock_response = MockResponse(status=200, text='{"recipientsRemoved": true}')

        with patch.object(
            client._http_client,
            "send_async",
            new_callable=AsyncMock,
            return_value=mock_response,
        ) as mock_send:
            result = await client.remove_recipient_from_envelope_async(
                account_id="acct-1",
                envelope_id="env-1",
                folder_id=None,
                remove_recipient_from_envelope_recipient_id=None,
            )

            mock_send.assert_called_once()
            method = mock_send.call_args[0][0]
            assert method == "DELETE"
            assert result is not None

    @pytest.mark.asyncio
    async def test_error_response_raises_exception(self, mock_token_provider):
        """Test DELETE error path raises ConnectorException."""
        client = DocusignClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider,
        )
        mock_response = MockResponse(status=404, text='{"error": "Envelope not found"}')

        with patch.object(
            client._http_client,
            "send_async",
            new_callable=AsyncMock,
            return_value=mock_response,
        ):
            with pytest.raises(ConnectorException):
                await client.remove_recipient_from_envelope_async(
                    account_id="acct-1",
                    envelope_id="missing-env",
                    folder_id=None,
                    remove_recipient_from_envelope_recipient_id=None,
                )
