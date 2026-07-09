# Copyright (c) Microsoft Corporation. All rights reserved.

"""Unit tests for ShiftsClient."""

from unittest.mock import AsyncMock, patch

import pytest

from azure.connectors.shifts import (
    ShiftsClient,
    CreateShiftRequest,
    WebHookRequest,
    EditOpenShiftRequest,
)
from azure.connectors.sdk import (
    ConnectorClientOptions,
    ConnectorException,
    ManagedIdentityTokenProvider,
)
from tests.conftest import MockResponse


class TestShiftsClientInitialization:
    """Tests for ShiftsClient initialization."""

    def test_init_with_valid_url_and_defaults(self):
        """Test initialization with valid URL and default parameters."""
        client = ShiftsClient("https://example.azure.com/connections/test")

        assert client._connection_runtime_url == "https://example.azure.com/connections/test"
        assert client.connector_name == "shifts"
        assert isinstance(client._http_client._token_provider, ManagedIdentityTokenProvider)

    def test_init_with_trailing_slash(self):
        """Test that trailing slash is removed from URL."""
        client = ShiftsClient("https://example.azure.com/connections/test/")

        assert client._connection_runtime_url == "https://example.azure.com/connections/test"

    def test_init_with_custom_token_provider(self, mock_token_provider):
        """Test initialization with custom token provider."""
        client = ShiftsClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider,
        )

        assert client._http_client._token_provider is mock_token_provider

    def test_init_with_custom_options(self, mock_token_provider):
        """Test initialization with custom options."""
        options = ConnectorClientOptions(timeout_seconds=60.0, max_retry_attempts=5)
        client = ShiftsClient(
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
            ShiftsClient("")

    def test_init_with_none_url_raises_error(self):
        """Test that None URL raises ValueError."""
        with pytest.raises(ValueError, match="connection_runtime_url cannot be None or empty"):
            ShiftsClient(None)

    def test_connector_name_property(self, mock_token_provider):
        """Test connector_name property returns 'shifts'."""
        client = ShiftsClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider,
        )

        assert client.connector_name == "shifts"


class TestShiftsClientLifecycle:
    """Tests for ShiftsClient lifecycle methods."""

    @pytest.mark.asyncio
    async def test_close(self, mock_token_provider):
        """Test close method calls http_client.close."""
        client = ShiftsClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider,
        )

        with patch.object(client._http_client, "close", new_callable=AsyncMock) as mock_close:
            await client.close()
            mock_close.assert_called_once()

    @pytest.mark.asyncio
    async def test_context_manager(self, mock_token_provider):
        """Test async context manager functionality."""
        with patch.object(ShiftsClient, "close", new_callable=AsyncMock) as mock_close:
            async with ShiftsClient(
                "https://example.azure.com/connections/test",
                token_provider=mock_token_provider,
            ) as client:
                assert isinstance(client, ShiftsClient)

            mock_close.assert_called_once()


class TestGetAllTeamsAsync:
    """Tests for get_all_teams_async method."""

    @pytest.mark.asyncio
    async def test_success(self, mock_token_provider):
        """Test successful teams retrieval."""
        client = ShiftsClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider,
        )
        mock_response = MockResponse(
            status=200, text='{"value": [{"id": "team-1", "displayName": "Store Team"}]}')

        with patch.object(
            client._http_client,
            "send_async",
            new_callable=AsyncMock,
            return_value=mock_response,
        ) as mock_send:
            result = await client.get_all_teams_async()

            mock_send.assert_called_once()
            method, path = mock_send.call_args[0][0], mock_send.call_args[0][1]
            assert method == "GET"
            assert "/v1.0/me/joinedTeams" in path
            assert result is not None
            assert "value" in result

    @pytest.mark.asyncio
    async def test_error_response_raises_exception(self, mock_token_provider):
        """Test that teams retrieval error raises ConnectorException."""
        client = ShiftsClient(
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
                await client.get_all_teams_async()


class TestGetScheduleAsync:
    """Tests for get_schedule_async method."""

    @pytest.mark.asyncio
    async def test_success(self, mock_token_provider):
        """Test successful schedule retrieval."""
        client = ShiftsClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider,
        )
        mock_response = MockResponse(status=200, text='{"id": "schedule-1", "timeZone": "UTC"}')

        with patch.object(
            client._http_client,
            "send_async",
            new_callable=AsyncMock,
            return_value=mock_response,
        ) as mock_send:
            result = await client.get_schedule_async(team_id="team-123")

            mock_send.assert_called_once()
            method, path = mock_send.call_args[0][0], mock_send.call_args[0][1]
            assert method == "GET"
            assert "/v1.0/teams/team-123/schedule" in path
            assert result is not None
            assert result.get("id") == "schedule-1"

    @pytest.mark.asyncio
    async def test_error_response_raises_exception(self, mock_token_provider):
        """Test that schedule retrieval error raises ConnectorException."""
        client = ShiftsClient(
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
                await client.get_schedule_async(team_id="missing-team")


class TestListShiftsAsync:
    """Tests for list_shifts_async method."""

    @pytest.mark.asyncio
    async def test_success_with_query_params(self, mock_token_provider):
        """Test list shifts query parameter handling."""
        client = ShiftsClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider,
        )
        mock_response = MockResponse(status=200, text='{"value": [{"id": "shift-1"}]}')

        with patch.object(
            client._http_client,
            "send_async",
            new_callable=AsyncMock,
            return_value=mock_response,
        ) as mock_send:
            result = await client.list_shifts_async(
                team_id="team-123",
                start_time="2026-07-01T00:00:00Z",
                end_time="2026-07-31T00:00:00Z",
                top="10",
            )

            mock_send.assert_called_once()
            method, path = mock_send.call_args[0][0], mock_send.call_args[0][1]
            assert method == "GET"
            assert "/v1.0/teams/team-123/schedule/shifts" in path
            assert "startTime=2026-07-01T00%3A00%3A00Z" in path
            assert "endTime=2026-07-31T00%3A00%3A00Z" in path
            assert "$top=10" in path
            assert result is not None

    @pytest.mark.asyncio
    async def test_error_response_raises_exception(self, mock_token_provider):
        """Test that list shifts error raises ConnectorException."""
        client = ShiftsClient(
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
                await client.list_shifts_async(team_id="team-123")


class TestCreateShiftAsync:
    """Tests for create_shift_async method."""

    @pytest.mark.asyncio
    async def test_success(self, mock_token_provider):
        """Test successful shift creation."""
        client = ShiftsClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider,
        )
        payload = CreateShiftRequest(scheduling_group_id="group-1", user_id="user-1")
        mock_response = MockResponse(status=201, text='{"id": "shift-1"}')

        with patch.object(
            client._http_client,
            "send_async",
            new_callable=AsyncMock,
            return_value=mock_response,
        ) as mock_send:
            result = await client.create_shift_async(input=payload, team_id="team-123")

            mock_send.assert_called_once()
            method, path = mock_send.call_args[0][0], mock_send.call_args[0][1]
            body = mock_send.call_args[1].get("body")
            assert method == "POST"
            assert "/v1.0/teams/team-123/schedule/shifts" in path
            assert body is payload
            assert result is not None

    @pytest.mark.asyncio
    async def test_error_response_raises_exception(self, mock_token_provider):
        """Test that shift creation error raises ConnectorException."""
        client = ShiftsClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider,
        )
        payload = CreateShiftRequest(scheduling_group_id="group-1", user_id="user-1")
        mock_response = MockResponse(status=400, text='{"error": "Bad request"}')

        with patch.object(
            client._http_client,
            "send_async",
            new_callable=AsyncMock,
            return_value=mock_response,
        ):
            with pytest.raises(ConnectorException):
                await client.create_shift_async(input=payload, team_id="team-123")


class TestTriggerForShiftsAsync:
    """Tests for trigger_for_shifts_async method."""

    @pytest.mark.asyncio
    async def test_success(self, mock_token_provider):
        """Test successful shifts webhook registration."""
        client = ShiftsClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider,
        )
        payload = WebHookRequest(notification_url="https://example.com/callback")
        mock_response = MockResponse(status=202, text="")

        with patch.object(
            client._http_client,
            "send_async",
            new_callable=AsyncMock,
            return_value=mock_response,
        ) as mock_send:
            result = await client.trigger_for_shifts_async(input=payload, team_id="team-123")

            mock_send.assert_called_once()
            method, path = mock_send.call_args[0][0], mock_send.call_args[0][1]
            assert method == "POST"
            assert "/trigger/teams/team-123/shifts" in path
            assert result is None


class TestDeleteTimeOffAsync:
    """Tests for delete_time_off_async method (DELETE)."""

    @pytest.mark.asyncio
    async def test_success(self, mock_token_provider):
        """Test successful time-off deletion."""
        client = ShiftsClient(
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
            await client.delete_time_off_async(team_id="team-1", time_off_id="toff-1")

            mock_send.assert_called_once()
            method, path = mock_send.call_args[0][0], mock_send.call_args[0][1]
            assert method == "DELETE"
            assert "/teams/team-1/schedule/timesoff/toff-1" in path

    @pytest.mark.asyncio
    async def test_error_response_raises_exception(self, mock_token_provider):
        """Test DELETE error path raises ConnectorException."""
        client = ShiftsClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider,
        )
        mock_response = MockResponse(status=404, text='{"error": "Time off not found"}')

        with patch.object(
            client._http_client,
            "send_async",
            new_callable=AsyncMock,
            return_value=mock_response,
        ):
            with pytest.raises(ConnectorException):
                await client.delete_time_off_async(team_id="team-1", time_off_id="missing")


class TestUpdateOpenShiftAsync:
    """Tests for update_open_shift_async method (PUT with body)."""

    @pytest.mark.asyncio
    async def test_success_sends_body_and_returns_result(self, mock_token_provider):
        """Test PUT sends input body and returns result."""
        client = ShiftsClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider,
        )
        payload = EditOpenShiftRequest()
        mock_response = MockResponse(status=200, text='{"id": "oshift-1"}')

        with patch.object(
            client._http_client,
            "send_async",
            new_callable=AsyncMock,
            return_value=mock_response,
        ) as mock_send:
            result = await client.update_open_shift_async(
                input=payload,
                team_id="team-1",
                open_shift_id="oshift-1",
            )

            mock_send.assert_called_once()
            method, path = mock_send.call_args[0][0], mock_send.call_args[0][1]
            body = mock_send.call_args[1].get("body")
            assert method == "PUT"
            assert "/teams/team-1/schedule/openShifts/oshift-1" in path
            assert body is payload
            assert result is not None

    @pytest.mark.asyncio
    async def test_error_response_raises_exception(self, mock_token_provider):
        """Test PUT error path raises ConnectorException."""
        client = ShiftsClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider,
        )
        payload = EditOpenShiftRequest()
        mock_response = MockResponse(status=403, text='{"error": "Forbidden"}')

        with patch.object(
            client._http_client,
            "send_async",
            new_callable=AsyncMock,
            return_value=mock_response,
        ):
            with pytest.raises(ConnectorException):
                await client.update_open_shift_async(
                    input=payload,
                    team_id="team-1",
                    open_shift_id="oshift-1",
                )
