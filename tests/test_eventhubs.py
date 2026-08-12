# Copyright (c) Microsoft Corporation. All rights reserved.

"""Unit tests for EventhubsClient."""

import pytest
from unittest.mock import AsyncMock, patch
from azure.connectors.eventhubs import (
    EventhubsClient,
    Event,
    SendEventsInput,
    ObjectEntity,
    SystemProperties,
    SendEvent,
    TRIGGER_OPERATIONS,
)
from azure.connectors.sdk import (
    ConnectorClientOptions,
    ManagedIdentityTokenProvider,
    ConnectorException,
)
from tests.conftest import MockResponse


class TestEventhubsClientInitialization:
    """Tests for EventhubsClient initialization."""

    def test_init_with_valid_url_and_defaults(self):
        """Test initialization with valid URL and default parameters."""
        client = EventhubsClient("https://example.azure.com/connections/test")

        assert client._connection_runtime_url == "https://example.azure.com/connections/test"
        assert client.connector_name == "eventhubs"
        assert isinstance(client._http_client._token_provider, ManagedIdentityTokenProvider)

    def test_init_with_trailing_slash(self):
        """Test that trailing slash is removed from URL."""
        client = EventhubsClient("https://example.azure.com/connections/test/")

        assert client._connection_runtime_url == "https://example.azure.com/connections/test"

    def test_init_with_custom_token_provider(self, mock_token_provider):
        """Test initialization with custom token provider."""
        client = EventhubsClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        assert client._http_client._token_provider is mock_token_provider

    def test_init_with_custom_options(self, mock_token_provider):
        """Test initialization with custom options."""
        options = ConnectorClientOptions(timeout_seconds=60.0, max_retry_attempts=5)
        client = EventhubsClient(
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
            EventhubsClient("")

    def test_init_with_none_url_raises_error(self):
        """Test that None URL raises ValueError."""
        with pytest.raises(ValueError, match="connection_runtime_url cannot be None or empty"):
            EventhubsClient(None)

    def test_connector_name_property(self, mock_token_provider):
        """Test connector_name property returns 'eventhubs'."""
        client = EventhubsClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        assert client.connector_name == "eventhubs"


class TestEventhubsClientLifecycle:
    """Tests for EventhubsClient lifecycle methods."""

    @pytest.mark.asyncio
    async def test_close(self, mock_token_provider):
        """Test close method calls http_client.close."""
        client = EventhubsClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        with patch.object(client._http_client, 'close', new_callable=AsyncMock) as mock_close:
            await client.close()
            mock_close.assert_called_once()

    @pytest.mark.asyncio
    async def test_context_manager(self, mock_token_provider):
        """Test async context manager functionality."""
        with patch.object(EventhubsClient, 'close', new_callable=AsyncMock) as mock_close:
            async with EventhubsClient(
                "https://example.azure.com/connections/test",
                token_provider=mock_token_provider
            ) as client:
                assert isinstance(client, EventhubsClient)

            mock_close.assert_called_once()


class TestTriggerOperations:
    """Tests for trigger registration contracts."""

    def test_on_new_events_is_registered_without_callable_method(self):
        """Test event polling is a metadata-only trigger."""
        assert "OnNewEvents" in TRIGGER_OPERATIONS
        assert not hasattr(EventhubsClient, "on_new_events_async")

    @pytest.mark.asyncio
    async def test_generate_event_schema(self, mock_token_provider):
        """Test event schema discovery forwards content metadata."""
        client = EventhubsClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )
        mock_response = MockResponse(status=200, text='{"type": "object"}')

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ) as mock_send:
            result = await client.generate_event_schema_async(
                content_type="application/json",
                content_schema="schema-1"
            )

            url = mock_send.call_args[0][1]
            assert "contentType=application/json" in url
            assert "contentSchema=schema-1" in url
            assert result == {"type": "object"}


class TestSendEvent:
    """Tests for send_event_async method."""

    @pytest.mark.asyncio
    async def test_success(self, mock_token_provider):
        """Test successful POST request."""
        client = EventhubsClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(status=201, text="")
        event_input = SendEvent(
            content_data='{"message": "Hello, Event Hub!"}',
            properties={"type": "greeting"}
        )

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ) as mock_send:
            await client.send_event_async(
                input=event_input,
                event_hub_name="myeventhub"
            )

            mock_send.assert_called_once()
            call_args = mock_send.call_args
            assert call_args[0][0] == "POST"
            assert "/myeventhub/events" in call_args[0][1]
            # Verify body is passed
            body = call_args.kwargs.get('body') or call_args[1].get('body')
            assert body is event_input

    @pytest.mark.asyncio
    async def test_with_partition_key(self, mock_token_provider):
        """Test POST request with partition key parameter."""
        client = EventhubsClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(status=201, text="")
        event_input = SendEvent(content_data='{"data": "test"}')

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ) as mock_send:
            await client.send_event_async(
                input=event_input,
                event_hub_name="myeventhub",
                partition_key="partition-1"
            )

            call_args = mock_send.call_args
            url = call_args[0][1]
            assert "partitionKey=partition-1" in url

    @pytest.mark.asyncio
    async def test_error_response_raises_exception(self, mock_token_provider):
        """Test that error response raises ConnectorException."""
        client = EventhubsClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(status=400, text='{"error": "Invalid event format"}')
        event_input = SendEvent(content_data='{"invalid": true}')

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ):
            with pytest.raises(ConnectorException) as exc_info:
                await client.send_event_async(
                    input=event_input,
                    event_hub_name="myeventhub"
                )

            assert exc_info.value.status_code == 400


class TestSendEvents:
    """Tests for send_events_async method."""

    @pytest.mark.asyncio
    async def test_success(self, mock_token_provider):
        """Test successful POST request for batch events."""
        client = EventhubsClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(status=201, text="")
        events_input: SendEventsInput = [
            SendEvent(content_data='{"msg": "Event 1"}'),
            SendEvent(content_data='{"msg": "Event 2"}'),
        ]

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ) as mock_send:
            await client.send_events_async(
                input=events_input,
                event_hub_name="myeventhub",
                partition_key="partition-1"
            )

            mock_send.assert_called_once()
            call_args = mock_send.call_args
            assert call_args[0][0] == "POST"
            assert "/myeventhub/events/batch" in call_args[0][1]

    @pytest.mark.asyncio
    async def test_with_partition_key(self, mock_token_provider):
        """Test POST batch request with partition key parameter."""
        client = EventhubsClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(status=201, text="")
        events_input: SendEventsInput = []

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ) as mock_send:
            await client.send_events_async(
                input=events_input,
                event_hub_name="myeventhub",
                partition_key="partition-2"
            )

            call_args = mock_send.call_args
            url = call_args[0][1]
            assert "partitionKey=partition-2" in url
            assert "/events/batch" in url

    @pytest.mark.asyncio
    async def test_error_response_raises_exception(self, mock_token_provider):
        """Test that error response raises ConnectorException."""
        client = EventhubsClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(status=413, text='{"error": "Batch too large"}')
        events_input: SendEventsInput = []

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ):
            with pytest.raises(ConnectorException) as exc_info:
                await client.send_events_async(
                    input=events_input,
                    event_hub_name="myeventhub",
                    partition_key="partition-1"
                )

            assert exc_info.value.status_code == 413


class TestDataClasses:
    """Tests for data class creation and attributes."""

    def test_event(self):
        """Test Event dataclass creation."""
        content = ObjectEntity(additional_properties={"message": "Hello"})
        system_props = SystemProperties(
            enqueued_time_utc="2024-01-15T10:30:00Z",
            offset="12345",
            partition_key="pk1",
            sequence_number=100
        )
        event = Event(
            content_data=content,
            properties={"type": "notification"},
            system_properties=system_props
        )

        assert event.content_data is not None
        assert event.properties["type"] == "notification"
        assert event.system_properties.sequence_number == 100

    def test_send_events_input(self):
        """Test SendEventsInput list creation."""
        events_input: SendEventsInput = [
            SendEvent(content_data="event1"),
            SendEvent(content_data="event2"),
        ]

        assert events_input[0].content_data == "event1"
        assert len(events_input) == 2

    def test_object_entity(self):
        """Test ObjectEntity dataclass creation."""
        entity = ObjectEntity(
            additional_properties={"key1": "value1", "key2": 42, "nested": {"a": 1}}
        )

        assert entity.additional_properties["key1"] == "value1"
        assert entity.additional_properties["key2"] == 42
        assert entity.additional_properties["nested"]["a"] == 1

    def test_system_properties(self):
        """Test SystemProperties dataclass creation."""
        props = SystemProperties(
            enqueued_time_utc="2024-01-15T10:30:00Z",
            offset="67890",
            partition_key="partition-key-1",
            sequence_number=500
        )

        assert props.enqueued_time_utc == "2024-01-15T10:30:00Z"
        assert props.offset == "67890"
        assert props.partition_key == "partition-key-1"
        assert props.sequence_number == 500

    def test_system_properties_defaults(self):
        """Test SystemProperties with default None values."""
        props = SystemProperties()

        assert props.enqueued_time_utc is None
        assert props.offset is None
        assert props.partition_key is None
        assert props.sequence_number is None

    def test_send_event(self):
        """Test SendEvent dataclass creation."""
        event = SendEvent(
            content_data='{"message": "Hello, World!", "timestamp": 1640000000}',
            properties={"correlation_id": "abc-123", "priority": "high"}
        )

        assert event.content_data is not None
        assert "message" in event.content_data
        assert event.properties["correlation_id"] == "abc-123"

    def test_send_event_minimal(self):
        """Test SendEvent with minimal data."""
        event = SendEvent(content_data="simple text message")

        assert event.content_data == "simple text message"
        assert event.properties is None


class TestEdgeCases:
    """Tests for edge cases and special scenarios."""

    @pytest.mark.asyncio
    async def test_http_client_property_access(self, mock_token_provider):
        """Test accessing http_client property."""
        client = EventhubsClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        assert client.http_client is not None
        assert client._http_client is client.http_client

    @pytest.mark.asyncio
    async def test_multiple_consecutive_calls(self, mock_token_provider):
        """Test multiple consecutive API calls."""
        client = EventhubsClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(status=200, text='[]')

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ) as mock_send:
            await client.get_partition_keys_async(event_hub_name="hub1")
            await client.get_partition_keys_async(event_hub_name="hub2")

            assert mock_send.call_count == 2

    @pytest.mark.asyncio
    async def test_special_characters_in_event_hub_name(self, mock_token_provider):
        """Test handling of special characters in event hub name."""
        client = EventhubsClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(status=200, text='[]')

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ) as mock_send:
            await client.get_partition_keys_async(
                event_hub_name="my-event-hub"
            )

            call_args = mock_send.call_args
            url = call_args[0][1]
            assert "eventHubName=my-event-hub" in url

    @pytest.mark.asyncio
    async def test_unauthorized_raises_exception(self, mock_token_provider):
        """Test that 401 unauthorized raises ConnectorException."""
        client = EventhubsClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(status=401, text='{"error": "Unauthorized"}')

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ):
            with pytest.raises(ConnectorException) as exc_info:
                await client.get_event_hubs_async()

            assert exc_info.value.status_code == 401
