# Copyright (c) Microsoft Corporation. All rights reserved.

"""Unit tests for ServicebusClient."""

import json
import pytest
from unittest.mock import AsyncMock, patch
from azure.connectors.servicebus import (
    ServicebusClient,
    ServiceBusMessage,
    SendMessagesInput,
    CreateTopicSubscriptionInput,
)
from azure.connectors.sdk import (
    ConnectorClientOptions,
    ManagedIdentityTokenProvider,
    ConnectorException,
)
from tests.conftest import MockResponse


class TestServicebusClientInitialization:
    """Tests for ServicebusClient initialization."""

    def test_init_with_valid_url_and_defaults(self):
        """Test initialization with valid URL and default parameters."""
        client = ServicebusClient("https://example.azure.com/connections/test")

        assert client._connection_runtime_url == "https://example.azure.com/connections/test"
        assert client.connector_name == "servicebus"
        assert isinstance(client._http_client._token_provider, ManagedIdentityTokenProvider)

    def test_init_with_trailing_slash(self):
        """Test that trailing slash is removed from URL."""
        client = ServicebusClient("https://example.azure.com/connections/test/")

        assert client._connection_runtime_url == "https://example.azure.com/connections/test"

    def test_init_with_custom_token_provider(self, mock_token_provider):
        """Test initialization with custom token provider."""
        client = ServicebusClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        assert client._http_client._token_provider is mock_token_provider

    def test_init_with_custom_options(self, mock_token_provider):
        """Test initialization with custom options."""
        options = ConnectorClientOptions(timeout_seconds=60.0, max_retry_attempts=5)
        client = ServicebusClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider,
            options=options
        )

        assert client._options is options
        assert client._options.timeout_seconds == 60.0
        assert client._options.max_retry_attempts == 5

    def test_init_with_empty_url_raises_error(self):
        """Test that empty URL raises ValueError."""
        with pytest.raises(ValueError, match="connection_runtime_url cannot be None or empty"):
            ServicebusClient("")

    def test_init_with_none_url_raises_error(self):
        """Test that None URL raises ValueError."""
        with pytest.raises(ValueError, match="connection_runtime_url cannot be None or empty"):
            ServicebusClient(None)

    def test_connector_name_property(self, mock_token_provider):
        """Test connector_name property returns 'servicebus'."""
        client = ServicebusClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        assert client.connector_name == "servicebus"


class TestServicebusClientLifecycle:
    """Tests for ServicebusClient lifecycle methods."""

    @pytest.mark.asyncio
    async def test_close(self, mock_token_provider):
        """Test close method calls http_client.close."""
        client = ServicebusClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        with patch.object(client._http_client, 'close', new_callable=AsyncMock) as mock_close:
            await client.close()
            mock_close.assert_called_once()

    @pytest.mark.asyncio
    async def test_context_manager(self, mock_token_provider):
        """Test async context manager functionality."""
        with patch.object(ServicebusClient, 'close', new_callable=AsyncMock) as mock_close:
            async with ServicebusClient(
                "https://example.azure.com/connections/test",
                token_provider=mock_token_provider
            ) as client:
                assert isinstance(client, ServicebusClient)

            mock_close.assert_called_once()


class TestSendMessage:
    """Tests for send_message_async method."""

    @pytest.mark.asyncio
    async def test_send_message_success(self, mock_token_provider):
        """Test successful message send."""
        client = ServicebusClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(200)
        with patch.object(
            client._http_client, 'send_async', new_callable=AsyncMock, return_value=mock_response
        ) as mock_send:
            message = ServiceBusMessage(content_data="Test message")
            await client.send_message_async(input=message, entity_name="myqueue")

            mock_send.assert_called_once()
            call_args = mock_send.call_args
            assert call_args[0][0] == "POST"
            assert "myqueue/messages" in call_args[0][1]

    @pytest.mark.asyncio
    async def test_send_message_with_system_properties(self, mock_token_provider):
        """Test send message with system properties parameter."""
        client = ServicebusClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(200)
        with patch.object(
            client._http_client, 'send_async', new_callable=AsyncMock, return_value=mock_response
        ) as mock_send:
            message = ServiceBusMessage(content_data="Test message")
            await client.send_message_async(
                input=message,
                entity_name="myqueue",
                system_properties="true"
            )

            call_args = mock_send.call_args
            assert "systemProperties=true" in call_args[0][1]


class TestSendMessages:
    """Tests for send_messages_async method."""

    @pytest.mark.asyncio
    async def test_send_messages_batch_success(self, mock_token_provider):
        """Test successful batch message send."""
        client = ServicebusClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(200)
        with patch.object(
            client._http_client, 'send_async', new_callable=AsyncMock, return_value=mock_response
        ) as mock_send:
            input_data = SendMessagesInput()
            await client.send_messages_async(input=input_data, entity_name="myqueue")

            mock_send.assert_called_once()
            call_args = mock_send.call_args
            assert call_args[0][0] == "POST"
            assert "myqueue/messages/batch" in call_args[0][1]

    @pytest.mark.asyncio
    async def test_send_messages_error_response(self, mock_token_provider):
        """Test that error response raises ConnectorException."""
        client = ServicebusClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(400, '{"error": "Invalid batch format"}')
        with patch.object(
            client._http_client, 'send_async', new_callable=AsyncMock, return_value=mock_response
        ):
            with pytest.raises(ConnectorException) as exc_info:
                input_data = SendMessagesInput()
                await client.send_messages_async(input=input_data, entity_name="myqueue")

            assert exc_info.value.status_code == 400


class TestGetMessageFromQueue:
    """Tests for get_message_from_queue_async method."""

    @pytest.mark.asyncio
    async def test_get_message_success(self, mock_token_provider):
        """Test successful message retrieval from queue."""
        client = ServicebusClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        response_data = {
            "contentData": "Test message content",
            "messageId": "msg-123",
            "contentType": "application/json"
        }
        mock_response = MockResponse(200, json.dumps(response_data))
        with patch.object(
            client._http_client, 'send_async', new_callable=AsyncMock, return_value=mock_response
        ) as mock_send:
            result = await client.get_message_from_queue_async(queue_name="myqueue")

            mock_send.assert_called_once()
            call_args = mock_send.call_args
            assert call_args[0][0] == "GET"
            assert "myqueue/messages/head" in call_args[0][1]
            assert result["messageId"] == "msg-123"

    @pytest.mark.asyncio
    async def test_get_message_with_queue_type(self, mock_token_provider):
        """Test get message with queue type parameter."""
        client = ServicebusClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(200, "{}")
        with patch.object(
            client._http_client, 'send_async', new_callable=AsyncMock, return_value=mock_response
        ) as mock_send:
            await client.get_message_from_queue_async(
                queue_name="myqueue",
                queue_type="Main"
            )

            call_args = mock_send.call_args
            assert "queueType=Main" in call_args[0][1]

    @pytest.mark.asyncio
    async def test_get_message_error_response(self, mock_token_provider):
        """Test that error response raises ConnectorException."""
        client = ServicebusClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(404, "Queue not found")
        with patch.object(
            client._http_client, 'send_async', new_callable=AsyncMock, return_value=mock_response
        ):
            with pytest.raises(ConnectorException):
                await client.get_message_from_queue_async(queue_name="nonexistent")

    @pytest.mark.asyncio
    async def test_get_message_empty_response(self, mock_token_provider):
        """Test that empty response returns None."""
        client = ServicebusClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(200, "")
        with patch.object(
            client._http_client, 'send_async', new_callable=AsyncMock, return_value=mock_response
        ):
            result = await client.get_message_from_queue_async(queue_name="myqueue")
            assert result is None


class TestGetMessageFromQueueWithPeekLock:
    """Tests for get_new_message_from_queue_with_peek_lock_async method."""

    @pytest.mark.asyncio
    async def test_get_message_peek_lock_success(self, mock_token_provider):
        """Test successful peek-lock message retrieval."""
        client = ServicebusClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        response_data = {"contentData": "Test", "lockToken": "token-123"}
        mock_response = MockResponse(200, json.dumps(response_data))
        with patch.object(
            client._http_client, 'send_async', new_callable=AsyncMock, return_value=mock_response
        ) as mock_send:
            result = await client.get_new_message_from_queue_with_peek_lock_async(
                queue_name="myqueue"
            )

            call_args = mock_send.call_args
            assert "myqueue/messages/head/peek" in call_args[0][1]
            assert result["lockToken"] == "token-123"

    @pytest.mark.asyncio
    async def test_get_message_peek_lock_with_session(self, mock_token_provider):
        """Test peek-lock with session ID parameter."""
        client = ServicebusClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(200, "{}")
        with patch.object(
            client._http_client, 'send_async', new_callable=AsyncMock, return_value=mock_response
        ) as mock_send:
            await client.get_new_message_from_queue_with_peek_lock_async(
                queue_name="myqueue",
                session_id="session-abc"
            )

            call_args = mock_send.call_args
            assert "sessionId=session-abc" in call_args[0][1]

    @pytest.mark.asyncio
    async def test_peek_lock_error_response(self, mock_token_provider):
        """Test that error response raises ConnectorException."""
        client = ServicebusClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(404, '{"error": "Queue not found"}')
        with patch.object(
            client._http_client, 'send_async', new_callable=AsyncMock, return_value=mock_response
        ):
            with pytest.raises(ConnectorException) as exc_info:
                await client.get_new_message_from_queue_with_peek_lock_async(
                    queue_name="nonexistent"
                )

            assert exc_info.value.status_code == 404


class TestCompleteMessageInQueue:
    """Tests for complete_message_in_queue_async method."""

    @pytest.mark.asyncio
    async def test_complete_message_success(self, mock_token_provider):
        """Test successful message completion."""
        client = ServicebusClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(200)
        with patch.object(
            client._http_client, 'send_async', new_callable=AsyncMock, return_value=mock_response
        ) as mock_send:
            await client.complete_message_in_queue_async(
                queue_name="myqueue",
                lock_token="token-123"
            )

            mock_send.assert_called_once()
            call_args = mock_send.call_args
            assert call_args[0][0] == "DELETE"
            assert "myqueue/messages/complete" in call_args[0][1]
            assert "lockToken=token-123" in call_args[0][1]

    @pytest.mark.asyncio
    async def test_complete_message_error_response(self, mock_token_provider):
        """Test that error response raises ConnectorException."""
        client = ServicebusClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(404, '{"error": "Lock token expired"}')
        with patch.object(
            client._http_client, 'send_async', new_callable=AsyncMock, return_value=mock_response
        ):
            with pytest.raises(ConnectorException) as exc_info:
                await client.complete_message_in_queue_async(
                    queue_name="myqueue",
                    lock_token="expired-token"
                )

            assert exc_info.value.status_code == 404


class TestAbandonMessageInQueue:
    """Tests for abandon_message_in_queue_async method."""

    @pytest.mark.asyncio
    async def test_abandon_message_success(self, mock_token_provider):
        """Test successful message abandonment."""
        client = ServicebusClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(200)
        with patch.object(
            client._http_client, 'send_async', new_callable=AsyncMock, return_value=mock_response
        ) as mock_send:
            await client.abandon_message_in_queue_async(
                queue_name="myqueue",
                lock_token="token-123"
            )

            mock_send.assert_called_once()
            call_args = mock_send.call_args
            assert call_args[0][0] == "POST"
            assert "myqueue/messages/abandon" in call_args[0][1]

    @pytest.mark.asyncio
    async def test_abandon_message_error_response(self, mock_token_provider):
        """Test that error response raises ConnectorException."""
        client = ServicebusClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(404, '{"error": "Lock token expired"}')
        with patch.object(
            client._http_client, 'send_async', new_callable=AsyncMock, return_value=mock_response
        ):
            with pytest.raises(ConnectorException) as exc_info:
                await client.abandon_message_in_queue_async(
                    queue_name="myqueue",
                    lock_token="expired-token"
                )

            assert exc_info.value.status_code == 404


class TestDeferMessageInQueue:
    """Tests for defer_message_in_queue_async method."""

    @pytest.mark.asyncio
    async def test_defer_message_success(self, mock_token_provider):
        """Test successful message deferral."""
        client = ServicebusClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(200)
        with patch.object(
            client._http_client, 'send_async', new_callable=AsyncMock, return_value=mock_response
        ) as mock_send:
            await client.defer_message_in_queue_async(
                queue_name="myqueue",
                lock_token="token-123"
            )

            mock_send.assert_called_once()
            call_args = mock_send.call_args
            assert "myqueue/messages/defer" in call_args[0][1]

    @pytest.mark.asyncio
    async def test_defer_message_error_response(self, mock_token_provider):
        """Test that error response raises ConnectorException."""
        client = ServicebusClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(404, '{"error": "Lock token expired"}')
        with patch.object(
            client._http_client, 'send_async', new_callable=AsyncMock, return_value=mock_response
        ):
            with pytest.raises(ConnectorException) as exc_info:
                await client.defer_message_in_queue_async(
                    queue_name="myqueue",
                    lock_token="expired-token"
                )

            assert exc_info.value.status_code == 404


class TestGetDeferredMessageFromQueue:
    """Tests for get_deferred_message_from_queue_async method."""

    @pytest.mark.asyncio
    async def test_get_deferred_message_success(self, mock_token_provider):
        """Test successful deferred message retrieval."""
        client = ServicebusClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        response_data = {"contentData": "Deferred message", "sequenceNumber": 42}
        mock_response = MockResponse(200, json.dumps(response_data))
        with patch.object(
            client._http_client, 'send_async', new_callable=AsyncMock, return_value=mock_response
        ) as mock_send:
            result = await client.get_deferred_message_from_queue_async(
                queue_name="myqueue",
                sequence_number="42"
            )

            call_args = mock_send.call_args
            assert call_args[0][0] == "GET"
            assert "sequenceNumber=42" in call_args[0][1]
            assert result["sequenceNumber"] == 42

    @pytest.mark.asyncio
    async def test_get_deferred_message_error_response(self, mock_token_provider):
        """Test that error response raises ConnectorException."""
        client = ServicebusClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(404, '{"error": "Message not found"}')
        with patch.object(
            client._http_client, 'send_async', new_callable=AsyncMock, return_value=mock_response
        ):
            with pytest.raises(ConnectorException) as exc_info:
                await client.get_deferred_message_from_queue_async(
                    queue_name="myqueue",
                    sequence_number="999"
                )

            assert exc_info.value.status_code == 404


class TestDeadLetterMessageInQueue:
    """Tests for dead_letter_message_in_queue_async method."""

    @pytest.mark.asyncio
    async def test_dead_letter_message_success(self, mock_token_provider):
        """Test successful message dead-lettering."""
        client = ServicebusClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(200)
        with patch.object(
            client._http_client, 'send_async', new_callable=AsyncMock, return_value=mock_response
        ) as mock_send:
            await client.dead_letter_message_in_queue_async(
                queue_name="myqueue",
                lock_token="token-123",
                dead_letter_reason="Processing failed"
            )

            mock_send.assert_called_once()
            call_args = mock_send.call_args
            assert "myqueue/messages/deadletter" in call_args[0][1]
            assert "deadLetterReason=Processing%20failed" in call_args[0][1]

    @pytest.mark.asyncio
    async def test_dead_letter_error_response(self, mock_token_provider):
        """Test that error response raises ConnectorException."""
        client = ServicebusClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(404, '{"error": "Lock token expired"}')
        with patch.object(
            client._http_client, 'send_async', new_callable=AsyncMock, return_value=mock_response
        ):
            with pytest.raises(ConnectorException) as exc_info:
                await client.dead_letter_message_in_queue_async(
                    queue_name="myqueue",
                    lock_token="expired-token",
                    dead_letter_reason="Failed"
                )

            assert exc_info.value.status_code == 404


class TestRenewLockOnMessageInQueue:
    """Tests for renew_lock_on_message_in_queue_async method."""

    @pytest.mark.asyncio
    async def test_renew_lock_success(self, mock_token_provider):
        """Test successful lock renewal."""
        client = ServicebusClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(200)
        with patch.object(
            client._http_client, 'send_async', new_callable=AsyncMock, return_value=mock_response
        ) as mock_send:
            await client.renew_lock_on_message_in_queue_async(
                queue_name="myqueue",
                lock_token="token-123"
            )

            mock_send.assert_called_once()
            call_args = mock_send.call_args
            assert "myqueue/messages/renewlock" in call_args[0][1]


class TestGetMessagesFromQueue:
    """Tests for get_messages_from_queue_async method."""

    @pytest.mark.asyncio
    async def test_get_messages_batch_success(self, mock_token_provider):
        """Test successful batch message retrieval."""
        client = ServicebusClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        response_data = [{"contentData": "Message 1"}, {"contentData": "Message 2"}]
        mock_response = MockResponse(200, json.dumps(response_data))
        with patch.object(
            client._http_client, 'send_async', new_callable=AsyncMock, return_value=mock_response
        ) as mock_send:
            result = await client.get_messages_from_queue_async(queue_name="myqueue")

            call_args = mock_send.call_args
            assert "myqueue/messages/batch/head" in call_args[0][1]
            assert len(result) == 2

    @pytest.mark.asyncio
    async def test_get_messages_with_max_count(self, mock_token_provider):
        """Test batch retrieval with max message count."""
        client = ServicebusClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(200, "[]")
        with patch.object(
            client._http_client, 'send_async', new_callable=AsyncMock, return_value=mock_response
        ) as mock_send:
            await client.get_messages_from_queue_async(
                queue_name="myqueue",
                max_message_count="10"
            )

            call_args = mock_send.call_args
            assert "maxMessageCount=10" in call_args[0][1]

    @pytest.mark.asyncio
    async def test_get_messages_error_response(self, mock_token_provider):
        """Test that error response raises ConnectorException."""
        client = ServicebusClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(404, '{"error": "Queue not found"}')
        with patch.object(
            client._http_client, 'send_async', new_callable=AsyncMock, return_value=mock_response
        ):
            with pytest.raises(ConnectorException) as exc_info:
                await client.get_messages_from_queue_async(queue_name="nonexistent")

            assert exc_info.value.status_code == 404


class TestCloseSessionInQueue:
    """Tests for close_session_in_queue_async method."""

    @pytest.mark.asyncio
    async def test_close_session_success(self, mock_token_provider):
        """Test successful session close."""
        client = ServicebusClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(200)
        with patch.object(
            client._http_client, 'send_async', new_callable=AsyncMock, return_value=mock_response
        ) as mock_send:
            await client.close_session_in_queue_async(
                queue_name="myqueue",
                session_id="session-123"
            )

            mock_send.assert_called_once()
            call_args = mock_send.call_args
            assert call_args[0][0] == "DELETE"
            assert "myqueue/sessions/session-123/close" in call_args[0][1]

    @pytest.mark.asyncio
    async def test_close_session_error_response(self, mock_token_provider):
        """Test that error response raises ConnectorException."""
        client = ServicebusClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(404, '{"error": "Session not found"}')
        with patch.object(
            client._http_client, 'send_async', new_callable=AsyncMock, return_value=mock_response
        ):
            with pytest.raises(ConnectorException) as exc_info:
                await client.close_session_in_queue_async(
                    queue_name="myqueue",
                    session_id="nonexistent"
                )

            assert exc_info.value.status_code == 404


class TestRenewLockOnSessionInQueue:
    """Tests for renew_lock_on_session_in_queue_async method."""

    @pytest.mark.asyncio
    async def test_renew_session_lock_success(self, mock_token_provider):
        """Test successful session lock renewal."""
        client = ServicebusClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(200)
        with patch.object(
            client._http_client, 'send_async', new_callable=AsyncMock, return_value=mock_response
        ) as mock_send:
            await client.renew_lock_on_session_in_queue_async(
                queue_name="myqueue",
                session_id="session-123"
            )

            mock_send.assert_called_once()
            call_args = mock_send.call_args
            assert "myqueue/sessions/session-123/renewlock" in call_args[0][1]

    @pytest.mark.asyncio
    async def test_renew_session_lock_error_response(self, mock_token_provider):
        """Test that error response raises ConnectorException."""
        client = ServicebusClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(404, '{"error": "Session not found"}')
        with patch.object(
            client._http_client, 'send_async', new_callable=AsyncMock, return_value=mock_response
        ):
            with pytest.raises(ConnectorException) as exc_info:
                await client.renew_lock_on_session_in_queue_async(
                    queue_name="myqueue",
                    session_id="nonexistent"
                )

            assert exc_info.value.status_code == 404


class TestGetMessageFromTopic:
    """Tests for get_message_from_topic_async method."""

    @pytest.mark.asyncio
    async def test_get_topic_message_success(self, mock_token_provider):
        """Test successful message retrieval from topic subscription."""
        client = ServicebusClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        response_data = {"contentData": "Topic message", "messageId": "msg-456"}
        mock_response = MockResponse(200, json.dumps(response_data))
        with patch.object(
            client._http_client, 'send_async', new_callable=AsyncMock, return_value=mock_response
        ) as mock_send:
            result = await client.get_message_from_topic_async(
                topic_name="mytopic",
                subscription_name="mysub"
            )

            call_args = mock_send.call_args
            assert "mytopic/subscriptions/mysub/messages/head" in call_args[0][1]
            assert result["messageId"] == "msg-456"

    @pytest.mark.asyncio
    async def test_get_topic_message_error_response(self, mock_token_provider):
        """Test that error response raises ConnectorException."""
        client = ServicebusClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(404, '{"error": "Subscription not found"}')
        with patch.object(
            client._http_client, 'send_async', new_callable=AsyncMock, return_value=mock_response
        ):
            with pytest.raises(ConnectorException) as exc_info:
                await client.get_message_from_topic_async(
                    topic_name="mytopic",
                    subscription_name="nonexistent"
                )

            assert exc_info.value.status_code == 404


class TestCompleteMessageInTopic:
    """Tests for complete_message_in_topic_async method."""

    @pytest.mark.asyncio
    async def test_complete_topic_message_success(self, mock_token_provider):
        """Test successful message completion in topic subscription."""
        client = ServicebusClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(200)
        with patch.object(
            client._http_client, 'send_async', new_callable=AsyncMock, return_value=mock_response
        ) as mock_send:
            await client.complete_message_in_topic_async(
                topic_name="mytopic",
                subscription_name="mysub",
                lock_token="token-123"
            )

            mock_send.assert_called_once()
            call_args = mock_send.call_args
            assert call_args[0][0] == "DELETE"
            assert "mytopic/subscriptions/mysub/messages/complete" in call_args[0][1]

    @pytest.mark.asyncio
    async def test_complete_topic_message_error_response(self, mock_token_provider):
        """Test that error response raises ConnectorException."""
        client = ServicebusClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(404, '{"error": "Lock token expired"}')
        with patch.object(
            client._http_client, 'send_async', new_callable=AsyncMock, return_value=mock_response
        ):
            with pytest.raises(ConnectorException) as exc_info:
                await client.complete_message_in_topic_async(
                    topic_name="mytopic",
                    subscription_name="mysub",
                    lock_token="expired-token"
                )

            assert exc_info.value.status_code == 404


class TestAbandonMessageInTopic:
    """Tests for abandon_message_in_topic_async method."""

    @pytest.mark.asyncio
    async def test_abandon_topic_message_success(self, mock_token_provider):
        """Test successful message abandonment in topic subscription."""
        client = ServicebusClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(200)
        with patch.object(
            client._http_client, 'send_async', new_callable=AsyncMock, return_value=mock_response
        ) as mock_send:
            await client.abandon_message_in_topic_async(
                topic_name="mytopic",
                subscription_name="mysub",
                lock_token="token-123"
            )

            mock_send.assert_called_once()
            call_args = mock_send.call_args
            assert "mytopic/subscriptions/mysub/messages/abandon" in call_args[0][1]

    @pytest.mark.asyncio
    async def test_abandon_topic_message_error_response(self, mock_token_provider):
        """Test that error response raises ConnectorException."""
        client = ServicebusClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(404, '{"error": "Lock token expired"}')
        with patch.object(
            client._http_client, 'send_async', new_callable=AsyncMock, return_value=mock_response
        ):
            with pytest.raises(ConnectorException) as exc_info:
                await client.abandon_message_in_topic_async(
                    topic_name="mytopic",
                    subscription_name="mysub",
                    lock_token="expired-token"
                )

            assert exc_info.value.status_code == 404


class TestCreateTopicSubscription:
    """Tests for create_topic_subscription_async method."""

    @pytest.mark.asyncio
    async def test_create_subscription_success(self, mock_token_provider):
        """Test successful topic subscription creation."""
        client = ServicebusClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        response_data = {"subscriptionName": "newsub"}
        mock_response = MockResponse(201, json.dumps(response_data))
        with patch.object(
            client._http_client, 'send_async', new_callable=AsyncMock, return_value=mock_response
        ) as mock_send:
            input_data = CreateTopicSubscriptionInput()
            result = await client.create_topic_subscription_async(
                input=input_data,
                topic_name="mytopic",
                subscription_name="newsub"
            )

            call_args = mock_send.call_args
            assert call_args[0][0] == "POST"
            assert "mytopic/subscriptions/newsub" in call_args[0][1]
            assert result["subscriptionName"] == "newsub"

    @pytest.mark.asyncio
    async def test_create_subscription_error_response(self, mock_token_provider):
        """Test that error response raises ConnectorException."""
        client = ServicebusClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(400, '{"error": "Invalid subscription name"}')
        with patch.object(
            client._http_client, 'send_async', new_callable=AsyncMock, return_value=mock_response
        ):
            with pytest.raises(ConnectorException) as exc_info:
                input_data = CreateTopicSubscriptionInput()
                await client.create_topic_subscription_async(
                    input=input_data,
                    topic_name="mytopic",
                    subscription_name="invalid"
                )

            assert exc_info.value.status_code == 400


class TestDeleteTopicSubscription:
    """Tests for delete_topic_subscription_async method."""

    @pytest.mark.asyncio
    async def test_delete_subscription_success(self, mock_token_provider):
        """Test successful topic subscription deletion."""
        client = ServicebusClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(200)
        with patch.object(
            client._http_client, 'send_async', new_callable=AsyncMock, return_value=mock_response
        ) as mock_send:
            await client.delete_topic_subscription_async(
                topic_name="mytopic",
                subscription_name="mysub"
            )

            mock_send.assert_called_once()
            call_args = mock_send.call_args
            assert call_args[0][0] == "DELETE"
            assert "mytopic/subscriptions/mysub" in call_args[0][1]

    @pytest.mark.asyncio
    async def test_delete_subscription_error_response(self, mock_token_provider):
        """Test that error response raises ConnectorException."""
        client = ServicebusClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(404, '{"error": "Subscription not found"}')
        with patch.object(
            client._http_client, 'send_async', new_callable=AsyncMock, return_value=mock_response
        ):
            with pytest.raises(ConnectorException) as exc_info:
                await client.delete_topic_subscription_async(
                    topic_name="mytopic",
                    subscription_name="nonexistent"
                )

            assert exc_info.value.status_code == 404


class TestGetMessagesFromTopic:
    """Tests for get_messages_from_topic_async method."""

    @pytest.mark.asyncio
    async def test_get_topic_messages_batch_success(self, mock_token_provider):
        """Test successful batch message retrieval from topic."""
        client = ServicebusClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        response_data = [{"contentData": "Msg 1"}, {"contentData": "Msg 2"}]
        mock_response = MockResponse(200, json.dumps(response_data))
        with patch.object(
            client._http_client, 'send_async', new_callable=AsyncMock, return_value=mock_response
        ) as mock_send:
            result = await client.get_messages_from_topic_async(
                topic_name="mytopic",
                subscription_name="mysub"
            )

            call_args = mock_send.call_args
            assert "mytopic/subscriptions/mysub/messages/batch/head" in call_args[0][1]
            assert len(result) == 2


class TestDeadLetterMessageInTopic:
    """Tests for dead_letter_message_in_topic_async method."""

    @pytest.mark.asyncio
    async def test_dead_letter_topic_message_success(self, mock_token_provider):
        """Test successful message dead-lettering in topic subscription."""
        client = ServicebusClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(200)
        with patch.object(
            client._http_client, 'send_async', new_callable=AsyncMock, return_value=mock_response
        ) as mock_send:
            await client.dead_letter_message_in_topic_async(
                topic_name="mytopic",
                subscription_name="mysub",
                lock_token="token-123",
                dead_letter_reason="Invalid format"
            )

            call_args = mock_send.call_args
            assert "mytopic/subscriptions/mysub/messages/deadletter" in call_args[0][1]


class TestCloseSessionInTopic:
    """Tests for close_session_in_topic_async method."""

    @pytest.mark.asyncio
    async def test_close_topic_session_success(self, mock_token_provider):
        """Test successful session close in topic subscription."""
        client = ServicebusClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(200)
        with patch.object(
            client._http_client, 'send_async', new_callable=AsyncMock, return_value=mock_response
        ) as mock_send:
            await client.close_session_in_topic_async(
                topic_name="mytopic",
                subscription_name="mysub",
                session_id="session-456"
            )

            mock_send.assert_called_once()
            call_args = mock_send.call_args
            assert "mytopic/subscriptions/mysub/sessions/session-456/close" in call_args[0][1]


class TestRenewLockOnSessionInTopic:
    """Tests for renew_lock_on_session_in_topic_async method."""

    @pytest.mark.asyncio
    async def test_renew_topic_session_lock_success(self, mock_token_provider):
        """Test successful session lock renewal in topic subscription."""
        client = ServicebusClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(200)
        with patch.object(
            client._http_client, 'send_async', new_callable=AsyncMock, return_value=mock_response
        ) as mock_send:
            await client.renew_lock_on_session_in_topic_async(
                topic_name="mytopic",
                subscription_name="mysub",
                session_id="session-456"
            )

            mock_send.assert_called_once()
            call_args = mock_send.call_args
            assert "mytopic/subscriptions/mysub/sessions/session-456/renewlock" in call_args[0][1]
