# Copyright (c) Microsoft Corporation. All rights reserved.

"""Unit tests for SendgridClient."""

from unittest.mock import AsyncMock, patch

import pytest

from azure.connectors.sendgrid import (
    AddGlobalSuppressRequestAndResponse,
    EmailRequest,
    SendgridClient,
)
from azure.connectors.sdk import (
    ConnectorClientOptions,
    ConnectorException,
    ManagedIdentityTokenProvider,
)
from tests.conftest import MockResponse


class TestSendgridClientInitialization:
    """Tests for SendgridClient initialization."""

    def test_init_with_valid_url_and_defaults(self):
        """Test initialization with valid URL and default parameters."""
        client = SendgridClient("https://example.azure.com/connections/test")

        assert client._connection_runtime_url == "https://example.azure.com/connections/test"
        assert client.connector_name == "sendgrid"
        assert isinstance(client._http_client._token_provider, ManagedIdentityTokenProvider)

    def test_init_with_trailing_slash(self):
        """Test that trailing slash is removed from URL."""
        client = SendgridClient("https://example.azure.com/connections/test/")

        assert client._connection_runtime_url == "https://example.azure.com/connections/test"

    def test_init_with_custom_token_provider(self, mock_token_provider):
        """Test initialization with custom token provider."""
        client = SendgridClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider,
        )

        assert client._http_client._token_provider is mock_token_provider

    def test_init_with_custom_options(self, mock_token_provider):
        """Test initialization with custom options."""
        options = ConnectorClientOptions(timeout_seconds=60.0, max_retry_attempts=5)
        client = SendgridClient(
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
            SendgridClient("")

    def test_init_with_none_url_raises_error(self):
        """Test that None URL raises ValueError."""
        with pytest.raises(ValueError, match="connection_runtime_url cannot be None or empty"):
            SendgridClient(None)

    def test_connector_name_property(self, mock_token_provider):
        """Test connector_name property returns 'sendgrid'."""
        client = SendgridClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider,
        )

        assert client.connector_name == "sendgrid"


class TestSendgridClientLifecycle:
    """Tests for SendgridClient lifecycle methods."""

    @pytest.mark.asyncio
    async def test_close(self, mock_token_provider):
        """Test close method calls http_client.close."""
        client = SendgridClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider,
        )

        with patch.object(client._http_client, "close", new_callable=AsyncMock) as mock_close:
            await client.close()
            mock_close.assert_called_once()

    @pytest.mark.asyncio
    async def test_context_manager(self, mock_token_provider):
        """Test async context manager functionality."""
        with patch.object(SendgridClient, "close", new_callable=AsyncMock) as mock_close:
            async with SendgridClient(
                "https://example.azure.com/connections/test",
                token_provider=mock_token_provider,
            ) as client:
                assert isinstance(client, SendgridClient)

            mock_close.assert_called_once()


class TestSendgridClientOperations:
    """Tests for SendgridClient operations against expected HTTP calls."""

    @pytest.mark.asyncio
    async def test_add_global_suppression_success(self, mock_token_provider):
        """Test add global suppression issues a POST to the suppressions route."""
        client = SendgridClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider,
        )
        mock_response = MockResponse(status=200, text='{"recipient_emails": []}')

        with patch.object(
            client._http_client,
            "send_async",
            new_callable=AsyncMock,
            return_value=mock_response,
        ) as mock_send:
            result = await client.add_global_suppression_async(
                input=AddGlobalSuppressRequestAndResponse(recipient_emails=["a@b.com"]),
            )

            method, url = mock_send.call_args[0][0], mock_send.call_args[0][1]
            assert method == "POST"
            assert url.endswith("/suppressions/global")
            assert mock_send.call_args.kwargs["body"] is not None
            assert result == {"recipient_emails": []}

    @pytest.mark.asyncio
    async def test_get_global_suppression_success(self, mock_token_provider):
        """Test get global suppression issues a GET to the suppressions route."""
        client = SendgridClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider,
        )
        mock_response = MockResponse(status=200, text='{"recipient_email": "a@b.com"}')

        with patch.object(
            client._http_client,
            "send_async",
            new_callable=AsyncMock,
            return_value=mock_response,
        ) as mock_send:
            result = await client.get_global_suppression_async(email="a@b.com")

            method, url = mock_send.call_args[0][0], mock_send.call_args[0][1]
            assert method == "GET"
            assert url.endswith("/suppressions/global/a@b.com")
            assert result == {"recipient_email": "a@b.com"}

    @pytest.mark.asyncio
    async def test_delete_global_suppression_success(self, mock_token_provider):
        """Test delete global suppression issues a DELETE and returns None."""
        client = SendgridClient(
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
            result = await client.delete_global_suppression_async(email="a@b.com")

            method, url = mock_send.call_args[0][0], mock_send.call_args[0][1]
            assert method == "DELETE"
            assert url.endswith("/suppressions/global/a@b.com")
            assert result is None

    @pytest.mark.asyncio
    async def test_add_recipient_to_list_success(self, mock_token_provider):
        """Test add recipient to list issues a POST to the recipients route."""
        client = SendgridClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider,
        )
        mock_response = MockResponse(status=200, text='{"id": "r1"}')

        with patch.object(
            client._http_client,
            "send_async",
            new_callable=AsyncMock,
            return_value=mock_response,
        ) as mock_send:
            result = await client.add_recipient_to_list_async(
                list_id="L1",
                recipient_id="R1",
            )

            method, url = mock_send.call_args[0][0], mock_send.call_args[0][1]
            assert method == "POST"
            assert url.endswith("/v3/contactdb/lists/L1/recipients/R1")
            assert result == {"id": "r1"}

    @pytest.mark.asyncio
    async def test_get_bounce_success(self, mock_token_provider):
        """Test get bounce issues a GET to the bounces route."""
        client = SendgridClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider,
        )
        mock_response = MockResponse(status=200, text='{"email": "a@b.com"}')

        with patch.object(
            client._http_client,
            "send_async",
            new_callable=AsyncMock,
            return_value=mock_response,
        ) as mock_send:
            result = await client.get_bounce_async(email="a@b.com")

            method, url = mock_send.call_args[0][0], mock_send.call_args[0][1]
            assert method == "GET"
            assert url.endswith("/suppression/bounces/a@b.com")
            assert result == {"email": "a@b.com"}

    @pytest.mark.asyncio
    async def test_delete_bounce_success(self, mock_token_provider):
        """Test delete bounce issues a DELETE and returns None."""
        client = SendgridClient(
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
            result = await client.delete_bounce_async(email="a@b.com")

            method, url = mock_send.call_args[0][0], mock_send.call_args[0][1]
            assert method == "DELETE"
            assert url.endswith("/suppression/bounces/a@b.com")
            assert result is None

    @pytest.mark.asyncio
    async def test_check_email_is_in_unsubscribes_list_success(self, mock_token_provider):
        """Test unsubscribe check issues a GET to the unsubscribes route."""
        client = SendgridClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider,
        )
        mock_response = MockResponse(status=200, text='{"isUnsubscribed": true}')

        with patch.object(
            client._http_client,
            "send_async",
            new_callable=AsyncMock,
            return_value=mock_response,
        ) as mock_send:
            result = await client.check_email_is_in_unsubscribes_list_async(email="a@b.com")

            method, url = mock_send.call_args[0][0], mock_send.call_args[0][1]
            assert method == "GET"
            assert url.endswith("/unsubscribes/a@b.com")
            assert result == {"isUnsubscribed": True}

    @pytest.mark.asyncio
    async def test_send_email_success(self, mock_token_provider):
        """Test send email issues a POST to the mail send route with a body."""
        client = SendgridClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider,
        )
        mock_response = MockResponse(status=200, text='{"message": "success"}')

        with patch.object(
            client._http_client,
            "send_async",
            new_callable=AsyncMock,
            return_value=mock_response,
        ) as mock_send:
            result = await client.send_email_async(
                input=EmailRequest(to="a@b.com", subject="Hi", body="Hello"),
            )

            method, url = mock_send.call_args[0][0], mock_send.call_args[0][1]
            assert method == "POST"
            assert url.endswith("/v4/mail/send")
            assert mock_send.call_args.kwargs["body"] is not None
            assert result == {"message": "success"}

    @pytest.mark.asyncio
    async def test_list_recipient_lists_success(self, mock_token_provider):
        """Test list recipient lists issues a GET to the lists route."""
        client = SendgridClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider,
        )
        mock_response = MockResponse(status=200, text='{"lists": []}')

        with patch.object(
            client._http_client,
            "send_async",
            new_callable=AsyncMock,
            return_value=mock_response,
        ) as mock_send:
            result = await client.list_recipient_lists_async()

            method, url = mock_send.call_args[0][0], mock_send.call_args[0][1]
            assert method == "GET"
            assert url.endswith("/v3/contactdb/lists")
            assert result == {"lists": []}

    @pytest.mark.asyncio
    async def test_list_recipients_success(self, mock_token_provider):
        """Test list recipients issues a GET to the recipients route."""
        client = SendgridClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider,
        )
        mock_response = MockResponse(status=200, text='{"recipients": []}')

        with patch.object(
            client._http_client,
            "send_async",
            new_callable=AsyncMock,
            return_value=mock_response,
        ) as mock_send:
            result = await client.list_recipients_async()

            method, url = mock_send.call_args[0][0], mock_send.call_args[0][1]
            assert method == "GET"
            assert url.endswith("/v3/contactdb/recipients")
            assert result == {"recipients": []}

    @pytest.mark.asyncio
    async def test_empty_response_body_returns_none(self, mock_token_provider):
        """Test a 2xx response with no body returns None."""
        client = SendgridClient(
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
            result = await client.list_recipients_async()

            assert result is None


class TestSendgridClientErrorHandling:
    """Error handling tests for SendgridClient operations."""

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "operation",
        [
            "add_global_suppression",
            "get_global_suppression",
            "delete_global_suppression",
            "add_recipient_to_list",
            "get_bounce",
            "delete_bounce",
            "check_email_is_in_unsubscribes_list",
            "send_email",
            "list_recipient_lists",
            "list_recipients",
        ],
    )
    async def test_error_response_raises_exception(self, mock_token_provider, operation):
        """Test non-2xx responses raise ConnectorException for every operation."""
        client = SendgridClient(
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
            with pytest.raises(ConnectorException) as exc_info:
                if operation == "add_global_suppression":
                    await client.add_global_suppression_async(
                        input=AddGlobalSuppressRequestAndResponse()
                    )
                elif operation == "get_global_suppression":
                    await client.get_global_suppression_async(email="a@b.com")
                elif operation == "delete_global_suppression":
                    await client.delete_global_suppression_async(email="a@b.com")
                elif operation == "add_recipient_to_list":
                    await client.add_recipient_to_list_async(
                        list_id="L1", recipient_id="R1"
                    )
                elif operation == "get_bounce":
                    await client.get_bounce_async(email="a@b.com")
                elif operation == "delete_bounce":
                    await client.delete_bounce_async(email="a@b.com")
                elif operation == "check_email_is_in_unsubscribes_list":
                    await client.check_email_is_in_unsubscribes_list_async(email="a@b.com")
                elif operation == "send_email":
                    await client.send_email_async(input=EmailRequest())
                elif operation == "list_recipient_lists":
                    await client.list_recipient_lists_async()
                else:
                    await client.list_recipients_async()

            assert exc_info.value.status_code == 500


class TestSendgridTypeSerialization:
    """Tests for SendGrid dataclass defaults and reserved-name field renames."""

    def test_dataclass_defaults(self):
        """Test dataclasses default to None and reserved names are renamed."""
        assert EmailRequest().from_ is None
        assert EmailRequest().subject is None
        assert AddGlobalSuppressRequestAndResponse().recipient_emails is None
