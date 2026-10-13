# Copyright (c) Microsoft Corporation. All rights reserved.

"""Unit tests for MqClient."""

import pytest
from unittest.mock import AsyncMock, patch
from azure.core.credentials import AzureKeyCredential
from azure.connectors.aio.mq import MqClient
from azure.connectors.mq import (
    SingleGetValidOptions,
    MultipleGetValidOptions,
    SendValidDataOptions,
)
from azure.connectors.sdk import (
    ConnectorException,
)
from tests.conftest import MockResponse
from tests.generated_connector_test_utils import resolve_generated_result


class TestMqClientInitialization:
    """Tests for MqClient initialization."""

    def test_init_with_valid_url_and_defaults(self):
        """Test initialization with valid URL and default parameters."""
        client = MqClient("https://example.azure.com/connections/test",
                          AzureKeyCredential("test-key"))

        assert client._connection_runtime_url == "https://example.azure.com/connections/test"
        assert client.connector_name == "mq"
        assert isinstance(client._http_client._credential, AzureKeyCredential)

    def test_init_with_trailing_slash(self):
        """Test that trailing slash is removed from URL."""
        client = MqClient("https://example.azure.com/connections/test/",
                          AzureKeyCredential("test-key"))

        assert client._connection_runtime_url == "https://example.azure.com/connections/test"

    def test_init_with_custom_credential(self, mock_credential):
        """Test initialization with custom token provider."""
        client = MqClient(
            "https://example.azure.com/connections/test",
            credential=mock_credential
        )

        assert client._http_client._credential is mock_credential

    def test_init_with_custom_settings(self, mock_credential):
        """Test initialization with custom pipeline settings."""
        client = MqClient(
            "https://example.azure.com/connections/test",
            credential=mock_credential,
            timeout=60.0,
            max_retry_attempts=5,
        )
        assert client._http_client._timeout_seconds == 60.0

    def test_init_with_empty_url_raises_error(self):
        """Test that empty URL raises ValueError."""
        with pytest.raises(ValueError, match="connection_runtime_url cannot be None or empty"):
            MqClient("", AzureKeyCredential("test-key"))

    def test_init_with_none_url_raises_error(self):
        """Test that None URL raises ValueError."""
        with pytest.raises(ValueError, match="connection_runtime_url cannot be None or empty"):
            MqClient(None, AzureKeyCredential("test-key"))

    def test_connector_name_property(self, mock_credential):
        """Test connector_name property returns 'mq'."""
        client = MqClient(
            "https://example.azure.com/connections/test",
            credential=mock_credential
        )

        assert client.connector_name == "mq"


class TestMqClientLifecycle:
    """Tests for MqClient lifecycle methods."""

    @pytest.mark.asyncio
    async def test_close(self, mock_credential):
        """Test close method calls http_client.close."""
        client = MqClient(
            "https://example.azure.com/connections/test",
            credential=mock_credential
        )

        with patch.object(client._http_client, 'close', new_callable=AsyncMock) as mock_close:
            await client.close()
            mock_close.assert_called_once()

    @pytest.mark.asyncio
    async def test_context_manager(self, mock_credential):
        """Test async context manager functionality."""
        with patch.object(MqClient, 'close', new_callable=AsyncMock) as mock_close:
            async with MqClient(
                "https://example.azure.com/connections/test",
                credential=mock_credential
            ) as client:
                assert isinstance(client, MqClient)

            mock_close.assert_called_once()


class TestDelete:
    """Tests for delete_async method."""

    @pytest.mark.asyncio
    async def test_success_with_json_response(self, mock_credential):
        """Test successful POST request."""
        client = MqClient(
            "https://example.azure.com/connections/test",
            credential=mock_credential
        )

        mock_response = MockResponse(
            status=200,
            text='{"messageId": "msg123", "status": "deleted"}'
        )
        input_options = SingleGetValidOptions(queue="QUEUE.NAME")

        with patch.object(
            client._http_client,
            'send',
            new_callable=AsyncMock,
            return_value=mock_response
        ) as mock_send:
            result = await client.delete(input=input_options)

            mock_send.assert_called_once()
            call_args = mock_send.call_args
            assert call_args[0][0] == "POST"
            assert "/v2/delete" in call_args[0][1]
            assert result["messageId"] == "msg123"

    @pytest.mark.asyncio
    async def test_empty_response_returns_none(self, mock_credential):
        """Test that empty response returns None."""
        client = MqClient(
            "https://example.azure.com/connections/test",
            credential=mock_credential
        )

        mock_response = MockResponse(status=200, text="")

        with patch.object(
            client._http_client,
            'send',
            new_callable=AsyncMock,
            return_value=mock_response
        ):
            result = await client.delete(input=SingleGetValidOptions())
            assert result is None

    @pytest.mark.asyncio
    async def test_error_response_raises_exception(self, mock_credential):
        """Test that error response raises ConnectorException."""
        client = MqClient(
            "https://example.azure.com/connections/test",
            credential=mock_credential
        )

        mock_response = MockResponse(status=404, text='{"error": "Message not found"}')

        with patch.object(
            client._http_client,
            'send',
            new_callable=AsyncMock,
            return_value=mock_response
        ):
            with pytest.raises(ConnectorException) as exc_info:
                await client.delete(input=SingleGetValidOptions())

            assert exc_info.value.status_code == 404


class TestDeleteAll:
    """Tests for list_delete_all method."""

    @pytest.mark.asyncio
    async def test_success_with_json_response(self, mock_credential):
        """Test successful POST request."""
        client = MqClient(
            "https://example.azure.com/connections/test",
            credential=mock_credential
        )

        mock_response = MockResponse(
            status=200,
            text='{"value": [{"deletedCount": 5, "messages": []}]}'
        )
        input_options = MultipleGetValidOptions(queue="QUEUE.NAME", batch_size=10)

        with patch.object(
            client._http_client,
            'send',
            new_callable=AsyncMock,
            return_value=mock_response
        ) as mock_send:
            result = await resolve_generated_result(
                client.list_delete_all(input=input_options)
            )

            mock_send.assert_called_once()
            call_args = mock_send.call_args
            assert call_args[0][0] == "POST"
            assert "/v2/deleteall" in call_args[0][1]
            assert result[0]["deletedCount"] == 5

    @pytest.mark.asyncio
    async def test_empty_response_returns_empty_page(self, mock_credential):
        """Test that empty response yields no items."""
        client = MqClient(
            "https://example.azure.com/connections/test",
            credential=mock_credential
        )

        mock_response = MockResponse(status=200, text="")

        with patch.object(
            client._http_client,
            'send',
            new_callable=AsyncMock,
            return_value=mock_response
        ):
            result = await resolve_generated_result(
                client.list_delete_all(input=MultipleGetValidOptions())
            )
            assert result == []

    @pytest.mark.asyncio
    async def test_error_response_raises_exception(self, mock_credential):
        """Test that error response raises ConnectorException."""
        client = MqClient(
            "https://example.azure.com/connections/test",
            credential=mock_credential
        )

        mock_response = MockResponse(status=500, text='{"error": "Internal Server Error"}')

        with patch.object(
            client._http_client,
            'send',
            new_callable=AsyncMock,
            return_value=mock_response
        ):
            with pytest.raises(ConnectorException) as exc_info:
                await resolve_generated_result(
                    client.list_delete_all(input=MultipleGetValidOptions())
                )

            assert exc_info.value.status_code == 500


class TestRead:
    """Tests for read_async method."""

    @pytest.mark.asyncio
    async def test_success_with_json_response(self, mock_credential):
        """Test successful POST request."""
        client = MqClient(
            "https://example.azure.com/connections/test",
            credential=mock_credential
        )

        mock_response = MockResponse(
            status=200,
            text='{"messageId": "msg456", "messageData": "Hello World"}'
        )
        input_options = SingleGetValidOptions(queue="QUEUE.NAME", include_info="true")

        with patch.object(
            client._http_client,
            'send',
            new_callable=AsyncMock,
            return_value=mock_response
        ) as mock_send:
            result = await client.read(input=input_options)

            mock_send.assert_called_once()
            call_args = mock_send.call_args
            assert call_args[0][0] == "POST"
            assert "/v2/read" in call_args[0][1]
            assert result["messageData"] == "Hello World"

    @pytest.mark.asyncio
    async def test_empty_response_returns_none(self, mock_credential):
        """Test that empty response returns None."""
        client = MqClient(
            "https://example.azure.com/connections/test",
            credential=mock_credential
        )

        mock_response = MockResponse(status=200, text="")

        with patch.object(
            client._http_client,
            'send',
            new_callable=AsyncMock,
            return_value=mock_response
        ):
            result = await client.read(input=SingleGetValidOptions())
            assert result is None

    @pytest.mark.asyncio
    async def test_error_response_raises_exception(self, mock_credential):
        """Test that error response raises ConnectorException."""
        client = MqClient(
            "https://example.azure.com/connections/test",
            credential=mock_credential
        )

        mock_response = MockResponse(status=403, text='{"error": "Access denied"}')

        with patch.object(
            client._http_client,
            'send',
            new_callable=AsyncMock,
            return_value=mock_response
        ):
            with pytest.raises(ConnectorException) as exc_info:
                await client.read(input=SingleGetValidOptions())

            assert exc_info.value.status_code == 403


class TestReadAll:
    """Tests for list_read_all method."""

    @pytest.mark.asyncio
    async def test_success_with_json_response(self, mock_credential):
        """Test successful POST request."""
        client = MqClient(
            "https://example.azure.com/connections/test",
            credential=mock_credential
        )

        mock_response = MockResponse(
            status=200,
            text='{"value": [{"messageId": "msg1"}, {"messageId": "msg2"}]}'
        )
        input_options = MultipleGetValidOptions(queue="QUEUE.NAME", batch_size=10)

        with patch.object(
            client._http_client,
            'send',
            new_callable=AsyncMock,
            return_value=mock_response
        ) as mock_send:
            result = await resolve_generated_result(
                client.list_read_all(input=input_options)
            )

            mock_send.assert_called_once()
            call_args = mock_send.call_args
            assert call_args[0][0] == "POST"
            assert "/v2/readall" in call_args[0][1]
            assert len(result) == 2

    @pytest.mark.asyncio
    async def test_empty_response_returns_empty_page(self, mock_credential):
        """Test that empty response yields no items."""
        client = MqClient(
            "https://example.azure.com/connections/test",
            credential=mock_credential
        )

        mock_response = MockResponse(status=200, text="")

        with patch.object(
            client._http_client,
            'send',
            new_callable=AsyncMock,
            return_value=mock_response
        ):
            result = await resolve_generated_result(
                client.list_read_all(input=MultipleGetValidOptions())
            )
            assert result == []

    @pytest.mark.asyncio
    async def test_error_response_raises_exception(self, mock_credential):
        """Test that error response raises ConnectorException."""
        client = MqClient(
            "https://example.azure.com/connections/test",
            credential=mock_credential
        )

        mock_response = MockResponse(status=408, text='{"error": "Request timeout"}')

        with patch.object(
            client._http_client,
            'send',
            new_callable=AsyncMock,
            return_value=mock_response
        ):
            with pytest.raises(ConnectorException) as exc_info:
                await resolve_generated_result(
                    client.list_read_all(input=MultipleGetValidOptions())
                )

            assert exc_info.value.status_code == 408


class TestReceive:
    """Tests for receive_async method."""

    @pytest.mark.asyncio
    async def test_success_with_json_response(self, mock_credential):
        """Test successful POST request."""
        client = MqClient(
            "https://example.azure.com/connections/test",
            credential=mock_credential
        )

        mock_response = MockResponse(
            status=200,
            text='{"messageId": "msg789", "messageData": "Received content"}'
        )
        input_options = SingleGetValidOptions(queue="QUEUE.NAME", timeout="00:00:30")

        with patch.object(
            client._http_client,
            'send',
            new_callable=AsyncMock,
            return_value=mock_response
        ) as mock_send:
            result = await client.receive(input=input_options)

            mock_send.assert_called_once()
            call_args = mock_send.call_args
            assert call_args[0][0] == "POST"
            assert "/v2/receive" in call_args[0][1]
            assert result["messageData"] == "Received content"

    @pytest.mark.asyncio
    async def test_empty_response_returns_none(self, mock_credential):
        """Test that empty response returns None."""
        client = MqClient(
            "https://example.azure.com/connections/test",
            credential=mock_credential
        )

        mock_response = MockResponse(status=200, text="")

        with patch.object(
            client._http_client,
            'send',
            new_callable=AsyncMock,
            return_value=mock_response
        ):
            result = await client.receive(input=SingleGetValidOptions())
            assert result is None

    @pytest.mark.asyncio
    async def test_error_response_raises_exception(self, mock_credential):
        """Test that error response raises ConnectorException."""
        client = MqClient(
            "https://example.azure.com/connections/test",
            credential=mock_credential
        )

        mock_response = MockResponse(status=503, text='{"error": "Service unavailable"}')

        with patch.object(
            client._http_client,
            'send',
            new_callable=AsyncMock,
            return_value=mock_response
        ):
            with pytest.raises(ConnectorException) as exc_info:
                await client.receive(input=SingleGetValidOptions())

            assert exc_info.value.status_code == 503


class TestReceiveAll:
    """Tests for list_receive_all method."""

    @pytest.mark.asyncio
    async def test_success_with_json_response(self, mock_credential):
        """Test successful POST request."""
        client = MqClient(
            "https://example.azure.com/connections/test",
            credential=mock_credential
        )

        mock_response = MockResponse(
            status=200,
            text='{"value": [{"messageId": "msg1", "messageData": "Data1"}]}'
        )
        input_options = MultipleGetValidOptions(
            queue="QUEUE.NAME",
            batch_size=5,
            timeout="00:01:00"
        )

        with patch.object(
            client._http_client,
            'send',
            new_callable=AsyncMock,
            return_value=mock_response
        ) as mock_send:
            result = await resolve_generated_result(
                client.list_receive_all(input=input_options)
            )

            mock_send.assert_called_once()
            call_args = mock_send.call_args
            assert call_args[0][0] == "POST"
            assert "/v2/receiveall" in call_args[0][1]
            assert len(result) == 1

    @pytest.mark.asyncio
    async def test_empty_response_returns_empty_page(self, mock_credential):
        """Test that empty response yields no items."""
        client = MqClient(
            "https://example.azure.com/connections/test",
            credential=mock_credential
        )

        mock_response = MockResponse(status=200, text="")

        with patch.object(
            client._http_client,
            'send',
            new_callable=AsyncMock,
            return_value=mock_response
        ):
            result = await resolve_generated_result(
                client.list_receive_all(input=MultipleGetValidOptions())
            )
            assert result == []

    @pytest.mark.asyncio
    async def test_error_response_raises_exception(self, mock_credential):
        """Test that error response raises ConnectorException."""
        client = MqClient(
            "https://example.azure.com/connections/test",
            credential=mock_credential
        )

        mock_response = MockResponse(status=401, text='{"error": "Unauthorized"}')

        with patch.object(
            client._http_client,
            'send',
            new_callable=AsyncMock,
            return_value=mock_response
        ):
            with pytest.raises(ConnectorException) as exc_info:
                await resolve_generated_result(
                    client.list_receive_all(input=MultipleGetValidOptions())
                )

            assert exc_info.value.status_code == 401


class TestSend:
    """Tests for send_async method."""

    @pytest.mark.asyncio
    async def test_success_with_json_response(self, mock_credential):
        """Test successful POST request."""
        client = MqClient(
            "https://example.azure.com/connections/test",
            credential=mock_credential
        )

        mock_response = MockResponse(
            status=200,
            text='{"itemInternalId": "item123", "messageId": "msg123"}'
        )
        input_options = SendValidDataOptions(
            queue="QUEUE.NAME",
            message="Hello MQ!",
            message_type="text"
        )

        with patch.object(
            client._http_client,
            'send',
            new_callable=AsyncMock,
            return_value=mock_response
        ) as mock_send:
            result = await client.send(input=input_options)

            mock_send.assert_called_once()
            call_args = mock_send.call_args
            assert call_args[0][0] == "POST"
            assert "/v2/send" in call_args[0][1]
            assert result["messageId"] == "msg123"

    @pytest.mark.asyncio
    async def test_with_correlation_id(self, mock_credential):
        """Test send with correlation ID."""
        client = MqClient(
            "https://example.azure.com/connections/test",
            credential=mock_credential
        )

        mock_response = MockResponse(
            status=200,
            text='{"itemInternalId": "item456", "correlationId": "corr123"}'
        )
        input_options = SendValidDataOptions(
            queue="QUEUE.NAME",
            message="Correlated message",
            correlation_id="corr123"
        )

        with patch.object(
            client._http_client,
            'send',
            new_callable=AsyncMock,
            return_value=mock_response
        ) as mock_send:
            result = await client.send(input=input_options)

            mock_send.assert_called_once()
            assert result["correlationId"] == "corr123"

    @pytest.mark.asyncio
    async def test_with_reply_to_queue(self, mock_credential):
        """Test send with reply-to queue."""
        client = MqClient(
            "https://example.azure.com/connections/test",
            credential=mock_credential
        )

        mock_response = MockResponse(status=200, text='{"itemInternalId": "item789"}')
        input_options = SendValidDataOptions(
            queue="QUEUE.NAME",
            message="Request message",
            reply_to_queue="REPLY.QUEUE",
            reply_to_queue_manager="REPLY.QM"
        )

        with patch.object(
            client._http_client,
            'send',
            new_callable=AsyncMock,
            return_value=mock_response
        ) as mock_send:
            result = await client.send(input=input_options)

            mock_send.assert_called_once()
            assert result["itemInternalId"] == "item789"

    @pytest.mark.asyncio
    async def test_empty_response_returns_none(self, mock_credential):
        """Test that empty response returns None."""
        client = MqClient(
            "https://example.azure.com/connections/test",
            credential=mock_credential
        )

        mock_response = MockResponse(status=200, text="")

        with patch.object(
            client._http_client,
            'send',
            new_callable=AsyncMock,
            return_value=mock_response
        ):
            result = await client.send(
                input=SendValidDataOptions(message="test message")
            )
            assert result is None

    @pytest.mark.asyncio
    async def test_error_response_raises_exception(self, mock_credential):
        """Test that error response raises ConnectorException."""
        client = MqClient(
            "https://example.azure.com/connections/test",
            credential=mock_credential
        )

        mock_response = MockResponse(status=400, text='{"error": "Invalid message format"}')

        with patch.object(
            client._http_client,
            'send',
            new_callable=AsyncMock,
            return_value=mock_response
        ):
            with pytest.raises(ConnectorException) as exc_info:
                await client.send(
                    input=SendValidDataOptions(message="test message")
                )

            assert exc_info.value.status_code == 400

    @pytest.mark.asyncio
    async def test_queue_full_error(self, mock_credential):
        """Test that queue full error raises ConnectorException."""
        client = MqClient(
            "https://example.azure.com/connections/test",
            credential=mock_credential
        )

        mock_response = MockResponse(status=507, text='{"error": "Queue is full"}')

        with patch.object(
            client._http_client,
            'send',
            new_callable=AsyncMock,
            return_value=mock_response
        ):
            with pytest.raises(ConnectorException) as exc_info:
                await client.send(input=SendValidDataOptions(message="test"))

            assert exc_info.value.status_code == 507
