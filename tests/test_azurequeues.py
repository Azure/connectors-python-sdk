# Copyright (c) Microsoft Corporation. All rights reserved.

"""Unit tests for AzurequeuesClient."""

import pytest
from unittest.mock import AsyncMock, patch
from azure.connectors.azurequeues import (
    AzurequeuesClient,
    Messages,
    QueueArray,
    PutMessageInput,
    StorageAccountList,
    StorageAccount,
    QueueInfo,
    MessagePost,
    QueueMessage,
    QueueMessagesList,
    TRIGGER_OPERATIONS,
)
from azure.connectors.sdk import (
    ConnectorClientOptions,
    ManagedIdentityTokenProvider,
    ConnectorException,
)
from tests.conftest import MockResponse


class TestAzurequeuesClientInitialization:
    """Tests for AzurequeuesClient initialization."""

    def test_init_with_valid_url_and_defaults(self):
        """Test initialization with valid URL and default parameters."""
        client = AzurequeuesClient("https://example.azure.com/connections/test")

        assert client._connection_runtime_url == "https://example.azure.com/connections/test"
        assert client.connector_name == "azurequeues"
        assert isinstance(client._http_client._token_provider, ManagedIdentityTokenProvider)

    def test_init_with_trailing_slash(self):
        """Test that trailing slash is removed from URL."""
        client = AzurequeuesClient("https://example.azure.com/connections/test/")

        assert client._connection_runtime_url == "https://example.azure.com/connections/test"

    def test_init_with_custom_token_provider(self, mock_token_provider):
        """Test initialization with custom token provider."""
        client = AzurequeuesClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        assert client._http_client._token_provider is mock_token_provider

    def test_init_with_custom_options(self, mock_token_provider):
        """Test initialization with custom options."""
        options = ConnectorClientOptions(timeout_seconds=60.0, max_retry_attempts=5)
        client = AzurequeuesClient(
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
            AzurequeuesClient("")

    def test_init_with_none_url_raises_error(self):
        """Test that None URL raises ValueError."""
        with pytest.raises(ValueError, match="connection_runtime_url cannot be None or empty"):
            AzurequeuesClient(None)

    def test_connector_name_property(self, mock_token_provider):
        """Test connector_name property returns 'azurequeues'."""
        client = AzurequeuesClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        assert client.connector_name == "azurequeues"


class TestAzurequeuesClientLifecycle:
    """Tests for AzurequeuesClient lifecycle methods."""

    @pytest.mark.asyncio
    async def test_close(self, mock_token_provider):
        """Test close method calls http_client.close."""
        client = AzurequeuesClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        with patch.object(client._http_client, 'close', new_callable=AsyncMock) as mock_close:
            await client.close()
            mock_close.assert_called_once()

    @pytest.mark.asyncio
    async def test_context_manager(self, mock_token_provider):
        """Test async context manager functionality."""
        with patch.object(AzurequeuesClient, 'close', new_callable=AsyncMock) as mock_close:
            async with AzurequeuesClient(
                "https://example.azure.com/connections/test",
                token_provider=mock_token_provider
            ) as client:
                assert isinstance(client, AzurequeuesClient)

            mock_close.assert_called_once()


class TestDeleteMessage:
    """Tests for delete_message_async method."""

    @pytest.mark.asyncio
    async def test_success(self, mock_token_provider):
        """Test successful DELETE request."""
        client = AzurequeuesClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(status=204, text="")

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ) as mock_send:
            await client.delete_message_async(
                storage_account_name="mystorageaccount",
                queue_name="myqueue",
                message_id="msg-123",
                popreceipt="receipt-abc"
            )

            mock_send.assert_called_once()
            call_args = mock_send.call_args
            assert call_args[0][0] == "DELETE"
            expected_path = "/storageAccounts/mystorageaccount/queues/myqueue/messages/msg-123"
            assert expected_path in call_args[0][1]
            assert "popreceipt=receipt-abc" in call_args[0][1]

    @pytest.mark.asyncio
    async def test_popreceipt_is_required(self, mock_token_provider):
        """Test DELETE requires a pop receipt."""
        client = AzurequeuesClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        with pytest.raises(TypeError):
            await client.delete_message_async(
                storage_account_name="mystorageaccount",
                queue_name="myqueue",
                message_id="msg-123"
            )

    @pytest.mark.asyncio
    async def test_error_response_raises_exception(self, mock_token_provider):
        """Test that error response raises ConnectorException."""
        client = AzurequeuesClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(status=404, text='{"error": "Message not found"}')

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ):
            with pytest.raises(ConnectorException) as exc_info:
                await client.delete_message_async(
                    storage_account_name="mystorageaccount",
                    queue_name="myqueue",
                    message_id="nonexistent",
                    popreceipt="receipt-abc"
                )

            assert exc_info.value.status_code == 404


class TestGetMessages:
    """Tests for get_messages_async method."""

    @pytest.mark.asyncio
    async def test_success_with_json_response(self, mock_token_provider):
        """Test successful GET request."""
        client = AzurequeuesClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(
            status=200,
            text='{"queueMessagesList": [{"messageId": "msg1", "messageText": "Hello"}]}'
        )

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ) as mock_send:
            result = await client.get_messages_async(
                storage_account_name="mystorageaccount",
                queue_name="myqueue"
            )

            mock_send.assert_called_once()
            call_args = mock_send.call_args
            assert call_args[0][0] == "GET"
            assert "/storageAccounts/mystorageaccount/queues/myqueue/messages" in call_args[0][1]
            assert result["queueMessagesList"][0]["messageId"] == "msg1"

    @pytest.mark.asyncio
    async def test_with_query_parameters(self, mock_token_provider):
        """Test GET request with numofmessages and visibilitytimeout parameters."""
        client = AzurequeuesClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(status=200, text='{"queueMessagesList": []}')

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ) as mock_send:
            await client.get_messages_async(
                storage_account_name="mystorageaccount",
                queue_name="myqueue",
                numofmessages="10",
                visibilitytimeout="30"
            )

            call_args = mock_send.call_args
            url = call_args[0][1]
            assert "numofmessages=10" in url
            assert "visibilitytimeout=30" in url

    @pytest.mark.asyncio
    async def test_error_response_raises_exception(self, mock_token_provider):
        """Test that error response raises ConnectorException."""
        client = AzurequeuesClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(status=404, text='{"error": "Queue not found"}')

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ):
            with pytest.raises(ConnectorException) as exc_info:
                await client.get_messages_async(
                    storage_account_name="mystorageaccount",
                    queue_name="nonexistent"
                )

            assert exc_info.value.status_code == 404


class TestListQueues:
    """Tests for list_queues_async method."""

    @pytest.mark.asyncio
    async def test_success_with_json_response(self, mock_token_provider):
        """Test successful GET request."""
        client = AzurequeuesClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(
            status=200,
            text='{"value": [{"name": "queue1"}, {"name": "queue2"}]}'
        )

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ) as mock_send:
            result = await client.list_queues_async(
                storage_account_name="mystorageaccount"
            )

            mock_send.assert_called_once()
            call_args = mock_send.call_args
            assert call_args[0][0] == "GET"
            assert "/storageAccounts/mystorageaccount/queues/list" in call_args[0][1]
            assert len(result["value"]) == 2

    @pytest.mark.asyncio
    async def test_empty_response_returns_none(self, mock_token_provider):
        """Test that empty response returns None."""
        client = AzurequeuesClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(status=200, text="")

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ):
            result = await client.list_queues_async(
                storage_account_name="mystorageaccount"
            )
            assert result is None

    @pytest.mark.asyncio
    async def test_error_response_raises_exception(self, mock_token_provider):
        """Test that error response raises ConnectorException."""
        client = AzurequeuesClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(status=404, text='{"error": "Storage account not found"}')

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ):
            with pytest.raises(ConnectorException) as exc_info:
                await client.list_queues_async(
                    storage_account_name="nonexistent"
                )

            assert exc_info.value.status_code == 404


class TestTriggerOperations:
    """Tests for trigger registration contracts."""

    def test_triggers_are_registered_without_callable_methods(self):
        """Test polling triggers are metadata-only operations."""
        assert "OnMessages_V2" in TRIGGER_OPERATIONS
        assert "OnMessageThresholdReached_V2" in TRIGGER_OPERATIONS
        assert not hasattr(AzurequeuesClient, "on_messages_async")
        assert not hasattr(AzurequeuesClient, "on_message_threshold_reached_async")


class TestPutMessage:
    """Tests for put_message_async method."""

    @pytest.mark.asyncio
    async def test_success(self, mock_token_provider):
        """Test successful POST request."""
        client = AzurequeuesClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(status=201, text="")
        message_input = PutMessageInput("Hello, Queue!")

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ) as mock_send:
            await client.put_message_async(
                input=message_input,
                storage_account_name="mystorageaccount",
                queue_name="myqueue"
            )

            mock_send.assert_called_once()
            call_args = mock_send.call_args
            assert call_args[0][0] == "POST"
            expected_path = "/storageAccounts/mystorageaccount/queues/myqueue/messages"
            assert expected_path in call_args[0][1]
            # Verify body is passed
            body = call_args.kwargs.get('body') or call_args[1].get('body')
            assert body is message_input

    @pytest.mark.asyncio
    async def test_error_response_raises_exception(self, mock_token_provider):
        """Test that error response raises ConnectorException."""
        client = AzurequeuesClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(status=400, text='{"error": "Invalid message format"}')
        message_input = PutMessageInput("")

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ):
            with pytest.raises(ConnectorException) as exc_info:
                await client.put_message_async(
                    input=message_input,
                    storage_account_name="mystorageaccount",
                    queue_name="myqueue"
                )

            assert exc_info.value.status_code == 400


class TestPutQueue:
    """Tests for put_queue_async method."""

    @pytest.mark.asyncio
    async def test_success_with_json_response(self, mock_token_provider):
        """Test successful PUT request."""
        client = AzurequeuesClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(
            status=201,
            text='{"name": "newqueue", "created": true}'
        )

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ) as mock_send:
            result = await client.put_queue_async(
                storage_account_name="mystorageaccount",
                queue_name="newqueue"
            )

            mock_send.assert_called_once()
            call_args = mock_send.call_args
            assert call_args[0][0] == "PUT"
            assert "/storageAccounts/mystorageaccount/queues/putQueue" in call_args[0][1]
            assert "queueName=newqueue" in call_args[0][1]
            assert result["created"] is True

    @pytest.mark.asyncio
    async def test_error_response_raises_exception(self, mock_token_provider):
        """Test that error response raises ConnectorException."""
        client = AzurequeuesClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(status=409, text='{"error": "Queue already exists"}')

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ):
            with pytest.raises(ConnectorException) as exc_info:
                await client.put_queue_async(
                    storage_account_name="mystorageaccount",
                    queue_name="existingqueue"
                )

            assert exc_info.value.status_code == 409


class TestDataClasses:
    """Tests for data class creation and attributes."""

    def test_messages(self):
        """Test the nested queue messages response shape."""
        message = QueueMessage(message_id="msg1", message_text="Hello")
        queue_messages = QueueMessagesList(queue_message=[message])
        messages = Messages(queue_messages_list=queue_messages)

        assert messages.queue_messages_list is not None
        assert messages.queue_messages_list.queue_message is not None
        assert len(messages.queue_messages_list.queue_message) == 1
        assert messages.queue_messages_list.queue_message[0].message_id == "msg1"

    def test_queue_array(self):
        """Test QueueArray list creation."""
        queue_array: QueueArray = [QueueInfo(name="queue1"), QueueInfo(name="queue2")]

        assert queue_array[0].name == "queue1"

    def test_put_message_input(self):
        """Test PutMessageInput string creation."""
        put_input = PutMessageInput("Test message")

        assert put_input == "Test message"

    def test_storage_account_list(self):
        """Test StorageAccountList dataclass creation."""
        account1 = StorageAccount(name="account1", display_name="My Account 1")
        account2 = StorageAccount(name="account2", display_name="My Account 2")
        account_list = StorageAccountList(value=[account1, account2])

        assert account_list.value is not None
        assert len(account_list.value) == 2
        assert account_list.value[0].name == "account1"

    def test_storage_account(self):
        """Test StorageAccount dataclass creation."""
        account = StorageAccount(
            name="mystorageaccount",
            display_name="My Storage Account"
        )

        assert account.name == "mystorageaccount"
        assert account.display_name == "My Storage Account"

    def test_queue(self):
        """Test QueueInfo dataclass creation."""
        queue = QueueInfo(name="myqueue")

        assert queue.name == "myqueue"

    def test_message_post(self):
        """Test MessagePost dataclass creation."""
        post = MessagePost(message="This is a queue message")

        assert post.message == "This is a queue message"

    def test_queue_message(self):
        """Test QueueMessage dataclass creation."""
        message = QueueMessage(
            message_id="msg-123",
            message_text="Hello from queue",
            insertion_time="2024-01-15T10:30:00Z",
            expiration_time="2024-01-22T10:30:00Z",
            pop_receipt="receipt-abc",
            next_visible_time="2024-01-15T10:35:00Z",
            dequeue_count="1"
        )

        assert message.message_id == "msg-123"
        assert message.message_text == "Hello from queue"
        assert message.insertion_time == "2024-01-15T10:30:00Z"
        assert message.expiration_time == "2024-01-22T10:30:00Z"
        assert message.pop_receipt == "receipt-abc"
        assert message.next_visible_time == "2024-01-15T10:35:00Z"
        assert message.dequeue_count == "1"


class TestEdgeCases:
    """Tests for edge cases and special scenarios."""

    @pytest.mark.asyncio
    async def test_http_client_property_access(self, mock_token_provider):
        """Test accessing http_client property."""
        client = AzurequeuesClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        assert client.http_client is not None
        assert client._http_client is client.http_client

    @pytest.mark.asyncio
    async def test_multiple_consecutive_calls(self, mock_token_provider):
        """Test multiple consecutive API calls."""
        client = AzurequeuesClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(status=200, text='{"value": []}')

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ) as mock_send:
            await client.list_queues_async(storage_account_name="account1")
            await client.list_queues_async(storage_account_name="account2")

            assert mock_send.call_count == 2

    @pytest.mark.asyncio
    async def test_special_characters_in_queue_name(self, mock_token_provider):
        """Test handling of special characters in queue name."""
        client = AzurequeuesClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(status=200, text='{"queueMessagesList": []}')

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ) as mock_send:
            await client.get_messages_async(
                storage_account_name="mystorageaccount",
                queue_name="my-queue-name"
            )

            call_args = mock_send.call_args
            assert "/queues/my-queue-name/messages" in call_args[0][1]
