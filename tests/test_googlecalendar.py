# Copyright (c) Microsoft Corporation. All rights reserved.

"""Unit tests for GooglecalendarClient."""

import inspect

import pytest
from unittest.mock import AsyncMock, patch

from azure.connectors.googlecalendar import (
    CalendarEventChangedList,
    CalendarEventList,
    CalendarList,
    CalendarListEntry,
    GooglecalendarClient,
    ObjectEntity,
    PatchEvent,
    RequestEvent,
    ResponseEvent,
    ResponseEventWithActionType,
    TRIGGER_OPERATIONS,
)
from azure.connectors.sdk import (
    ConnectorClientOptions,
    ConnectorException,
    ManagedIdentityTokenProvider,
)
from tests.conftest import MockResponse


async def _invoke_operation(client: GooglecalendarClient, operation: str):
    """Invoke a Google Calendar operation by name for shared tests."""
    if operation == "list_calendars":
        return await client.list_calendars_async(min_access_role="reader")
    if operation == "list_events":
        return await client.list_events_async(
            calendar_id="cal123",
            time_min="2026-01-01T00:00:00Z",
            time_max="2026-01-31T23:59:59Z",
            q="planning",
        )
    if operation == "create_event":
        return await client.create_event_async(
            input=RequestEvent(),
            calendar_id="cal123",
        )
    if operation == "get_event":
        return await client.get_event_async(calendar_id="cal123", event_id="evt123")
    if operation == "delete_event":
        return await client.delete_event_async(calendar_id="cal123", event_id="evt123")
    if operation == "update_event":
        return await client.update_event_async(
            input=PatchEvent(),
            calendar_id="cal123",
            event_id="evt123",
        )
    if operation == "list_writable_calendars":
        return await client.list_writable_calendars_async()

    raise ValueError(f"Unsupported operation '{operation}'.")


class TestGooglecalendarClientInitialization:
    """Tests for GooglecalendarClient initialization."""

    def test_init_with_valid_url_and_defaults(self):
        """Test initialization with valid URL and default parameters."""
        client = GooglecalendarClient("https://example.azure.com/connections/test")

        assert client._connection_runtime_url == "https://example.azure.com/connections/test"
        assert client.connector_name == "googlecalendar"
        assert isinstance(client._http_client._token_provider, ManagedIdentityTokenProvider)

    def test_init_with_trailing_slash(self):
        """Test that trailing slash is removed from URL."""
        client = GooglecalendarClient("https://example.azure.com/connections/test/")

        assert client._connection_runtime_url == "https://example.azure.com/connections/test"

    def test_init_with_custom_token_provider(self, mock_token_provider):
        """Test initialization with custom token provider."""
        client = GooglecalendarClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider,
        )

        assert client._http_client._token_provider is mock_token_provider

    def test_init_with_custom_options(self, mock_token_provider):
        """Test initialization with custom options."""
        options = ConnectorClientOptions(timeout_seconds=60.0, max_retry_attempts=5)
        client = GooglecalendarClient(
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
            GooglecalendarClient("")

    def test_init_with_none_url_raises_error(self):
        """Test that None URL raises ValueError."""
        with pytest.raises(ValueError, match="connection_runtime_url cannot be None or empty"):
            GooglecalendarClient(None)

    def test_connector_name_property(self, mock_token_provider):
        """Test connector_name property returns 'googlecalendar'."""
        client = GooglecalendarClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider,
        )

        assert client.connector_name == "googlecalendar"


class TestGooglecalendarClientLifecycle:
    """Tests for GooglecalendarClient lifecycle methods."""

    @pytest.mark.asyncio
    async def test_close(self, mock_token_provider):
        """Test close method calls http_client.close."""
        client = GooglecalendarClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider,
        )

        with patch.object(client._http_client, "close", new_callable=AsyncMock) as mock_close:
            await client.close()
            mock_close.assert_called_once()

    @pytest.mark.asyncio
    async def test_context_manager(self, mock_token_provider):
        """Test async context manager functionality."""
        with patch.object(
            GooglecalendarClient,
            "close",
            new_callable=AsyncMock,
        ) as mock_close:
            async with GooglecalendarClient(
                "https://example.azure.com/connections/test",
                token_provider=mock_token_provider,
            ) as client:
                assert isinstance(client, GooglecalendarClient)

            mock_close.assert_called_once()


class TestGooglecalendarClientMethods:
    """Success path tests for representative Google Calendar methods."""

    @pytest.mark.asyncio
    async def test_list_calendars_success(self, mock_token_provider):
        """Test list_calendars_async returns parsed JSON and query params."""
        client = GooglecalendarClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider,
        )
        mock_response = MockResponse(status=200, text='{"items":[{"id":"cal1"}]}')

        with patch.object(
            client._http_client,
            "send_async",
            new_callable=AsyncMock,
            return_value=mock_response,
        ) as mock_send:
            result = await client.list_calendars_async(min_access_role="reader")

            assert len(result["items"]) == 1
            call_args = mock_send.call_args
            assert call_args[0][0] == "GET"
            assert "/users/me/calendarList" in call_args[0][1]
            assert "minAccessRole=reader" in call_args[0][1]

    @pytest.mark.asyncio
    async def test_list_events_success(self, mock_token_provider):
        """Test list_events_async serializes optional query parameters."""
        client = GooglecalendarClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider,
        )
        mock_response = MockResponse(status=200, text='{"items": []}')

        with patch.object(
            client._http_client,
            "send_async",
            new_callable=AsyncMock,
            return_value=mock_response,
        ) as mock_send:
            result = await client.list_events_async(
                calendar_id="cal123",
                time_min="2026-01-01T00:00:00Z",
                time_max="2026-01-31T23:59:59Z",
                q="planning",
            )

            assert result["items"] == []
            call_args = mock_send.call_args
            assert "/calendars/cal123/events" in call_args[0][1]
            assert "timeMin=2026-01-01T00%3A00%3A00Z" in call_args[0][1]
            assert "timeMax=2026-01-31T23%3A59%3A59Z" in call_args[0][1]
            assert "q=planning" in call_args[0][1]

    @pytest.mark.asyncio
    async def test_create_event_success(self, mock_token_provider):
        """Test create_event_async sends request body and returns JSON."""
        client = GooglecalendarClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider,
        )
        mock_response = MockResponse(status=201, text='{"id":"evt123"}')

        with patch.object(
            client._http_client,
            "send_async",
            new_callable=AsyncMock,
            return_value=mock_response,
        ) as mock_send:
            result = await client.create_event_async(
                input=RequestEvent(summary="Standup"),
                calendar_id="cal123",
            )

            assert result["id"] == "evt123"
            call_args = mock_send.call_args
            assert call_args[0][0] == "POST"
            assert isinstance(call_args.kwargs["body"], RequestEvent)

    @pytest.mark.asyncio
    async def test_list_writable_calendars_success(self, mock_token_provider):
        """Test list_writable_calendars_async includes fixed writer query."""
        client = GooglecalendarClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider,
        )
        mock_response = MockResponse(status=200, text='{"items": []}')

        with patch.object(
            client._http_client,
            "send_async",
            new_callable=AsyncMock,
            return_value=mock_response,
        ) as mock_send:
            await client.list_writable_calendars_async()

            call_args = mock_send.call_args
            assert "/users/me/calendarList/1" in call_args[0][1]
            assert "minAccessRole=writer" in call_args[0][1]


class TestGooglecalendarClientErrorHandling:
    """Error handling tests for all Google Calendar operations."""

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "operation",
        [
            "list_calendars",
            "list_events",
            "create_event",
            "get_event",
            "delete_event",
            "update_event",
            "list_writable_calendars",
        ],
    )
    async def test_error_response_raises_exception_for_all_operations(
        self,
        mock_token_provider,
        operation,
    ):
        """Test non-2xx responses raise ConnectorException for every operation."""
        client = GooglecalendarClient(
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
                await _invoke_operation(client, operation)

            assert exc_info.value.status_code == 500


class TestGooglecalendarApiSurface:
    """Tests for the generated callable and trigger operation surfaces."""

    def test_callable_method_signatures(self):
        """Test the client exposes exactly the generated callable methods."""
        expected_signatures = {
            "create_event_async": ("self", "input", "calendar_id"),
            "delete_event_async": ("self", "calendar_id", "event_id"),
            "get_event_async": ("self", "calendar_id", "event_id"),
            "list_calendars_async": ("self", "min_access_role"),
            "list_events_async": ("self", "calendar_id", "time_min", "time_max", "q"),
            "list_writable_calendars_async": ("self",),
            "update_event_async": ("self", "input", "calendar_id", "event_id"),
        }
        actual_signatures = {
            name: tuple(inspect.signature(method).parameters)
            for name, method in vars(GooglecalendarClient).items()
            if inspect.iscoroutinefunction(method)
        }

        assert actual_signatures == expected_signatures

    def test_trigger_registry_metadata(self):
        """Test polling triggers are represented by exact registration metadata."""
        assert TRIGGER_OPERATIONS == {
            "OnNewEventInCalendar": {
                "operation_id": "OnNewEventInCalendar",
                "path": "/{connectionId}/trigger1/calendars/{calendar_id}/events",
                "method": "get",
                "required_parameters": ["calendar_id"],
                "callback_payload_type": "CalendarEventList",
            },
            "OnUpdatedEventInCalendar": {
                "operation_id": "OnUpdatedEventInCalendar",
                "path": "/{connectionId}/trigger2/calendars/{calendar_id}/events",
                "method": "get",
                "required_parameters": ["calendar_id"],
                "callback_payload_type": "CalendarEventList",
            },
            "OnDeletedEventInCalendar": {
                "operation_id": "OnDeletedEventInCalendar",
                "path": "/{connectionId}/trigger3/calendars/{calendar_id}/events",
                "method": "get",
                "required_parameters": ["calendar_id"],
                "callback_payload_type": "CalendarEventList",
            },
            "OnChangedEventInCalendar": {
                "operation_id": "OnChangedEventInCalendar",
                "path": "/{connectionId}/trigger4/calendars/{calendar_id}/events",
                "method": "get",
                "required_parameters": ["calendar_id"],
                "callback_payload_type": "CalendarEventChangedList",
            },
            "OnEventStarted": {
                "operation_id": "OnEventStarted",
                "path": "/{connectionId}/eventstarted/calendars/{calendar_id}/events",
                "method": "get",
                "required_parameters": ["calendar_id"],
                "callback_payload_type": "CalendarEventList",
            },
        }


class TestGooglecalendarTypeSerialization:
    """Tests for Google Calendar connector dataclass defaults."""

    def test_dataclass_instances_initialize_expected_defaults(self):
        """Test generated dataclasses initialize with expected default values."""
        calendar_list = CalendarList()
        calendar_event_list = CalendarEventList()
        response_event = ResponseEvent()
        object_entity = ObjectEntity()
        changed_list = CalendarEventChangedList()
        calendar_entry = CalendarListEntry()
        request_event = RequestEvent()
        patch_event = PatchEvent()
        changed_event = ResponseEventWithActionType()

        assert calendar_list.items is None
        assert calendar_event_list.items is None
        assert response_event.id is None
        assert object_entity.additional_properties == {}
        assert changed_list.items is None
        assert calendar_entry.id is None
        assert request_event.summary is None
        assert patch_event.summary is None
        assert changed_event.action_type is None
