# Copyright (c) Microsoft Corporation. All rights reserved.

"""Unit tests for WebexClient."""

from unittest.mock import AsyncMock, patch

import pytest

from azure.connectors.webex import (
    CreateSpaceInput,
    CreateSpaceMemberInput,
    CreateTeamMemberInput,
    SendMessageInput,
    TRIGGER_OPERATIONS,
    WebexClient,
)
from azure.connectors.sdk import (
    ConnectorClientOptions,
    ConnectorException,
    ManagedIdentityTokenProvider,
)
from tests.conftest import MockResponse


class TestWebexClientInitialization:
    """Tests for WebexClient initialization."""

    def test_init_with_valid_url_and_defaults(self):
        """Test initialization with valid URL and default parameters."""
        client = WebexClient("https://example.azure.com/connections/test")

        assert client._connection_runtime_url == "https://example.azure.com/connections/test"
        assert client.connector_name == "webex"
        assert isinstance(client._http_client._token_provider, ManagedIdentityTokenProvider)

    def test_init_with_trailing_slash(self):
        """Test that trailing slash is removed from URL."""
        client = WebexClient("https://example.azure.com/connections/test/")

        assert client._connection_runtime_url == "https://example.azure.com/connections/test"

    def test_init_with_custom_token_provider(self, mock_token_provider):
        """Test initialization with custom token provider."""
        client = WebexClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider,
        )

        assert client._http_client._token_provider is mock_token_provider

    def test_init_with_custom_options(self, mock_token_provider):
        """Test initialization with custom options."""
        options = ConnectorClientOptions(timeout_seconds=60.0, max_retry_attempts=5)
        client = WebexClient(
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
            WebexClient("")

    def test_init_with_none_url_raises_error(self):
        """Test that None URL raises ValueError."""
        with pytest.raises(ValueError, match="connection_runtime_url cannot be None or empty"):
            WebexClient(None)

    def test_connector_name_property(self, mock_token_provider):
        """Test connector_name property returns 'webex'."""
        client = WebexClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider,
        )

        assert client.connector_name == "webex"


class TestWebexClientLifecycle:
    """Tests for WebexClient lifecycle methods."""

    @pytest.mark.asyncio
    async def test_close(self, mock_token_provider):
        """Test close method calls http_client.close."""
        client = WebexClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider,
        )

        with patch.object(client._http_client, "close", new_callable=AsyncMock) as mock_close:
            await client.close()
            mock_close.assert_called_once()

    @pytest.mark.asyncio
    async def test_context_manager(self, mock_token_provider):
        """Test async context manager functionality."""
        with patch.object(WebexClient, "close", new_callable=AsyncMock) as mock_close:
            async with WebexClient(
                "https://example.azure.com/connections/test",
                token_provider=mock_token_provider,
            ) as client:
                assert isinstance(client, WebexClient)

            mock_close.assert_called_once()


class TestWebexClientOperations:
    """Tests for WebexClient operations against expected HTTP calls."""

    @pytest.mark.asyncio
    async def test_create_space_member_success(self, mock_token_provider):
        """Test add member to space issues a POST to the memberships route."""
        client = WebexClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider,
        )
        mock_response = MockResponse(status=200, text='{"id": "m1"}')

        with patch.object(
            client._http_client,
            "send_async",
            new_callable=AsyncMock,
            return_value=mock_response,
        ) as mock_send:
            result = await client.create_space_member_async(
                input=CreateSpaceMemberInput(room_id="R1", person_email="a@b.com"),
            )

            method, url = mock_send.call_args[0][0], mock_send.call_args[0][1]
            assert method == "POST"
            assert url.endswith("/v1/memberships")
            assert mock_send.call_args.kwargs["body"] is not None
            assert result == {"id": "m1"}

    @pytest.mark.asyncio
    async def test_get_messages_success(self, mock_token_provider):
        """Test get messages issues a GET with the roomId query parameter."""
        client = WebexClient(
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
            result = await client.get_messages_async(room_id="R1")

            method, url = mock_send.call_args[0][0], mock_send.call_args[0][1]
            assert method == "GET"
            assert "/v1/messages" in url
            assert "roomId=R1" in url
            assert result == {"items": []}

    @pytest.mark.asyncio
    async def test_send_message_success(self, mock_token_provider):
        """Test send message issues a POST to the messages route."""
        client = WebexClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider,
        )
        mock_response = MockResponse(status=200, text='{"id": "msg1"}')

        with patch.object(
            client._http_client,
            "send_async",
            new_callable=AsyncMock,
            return_value=mock_response,
        ) as mock_send:
            result = await client.send_message_async(
                input=SendMessageInput(room_id="R1", text="hello"),
            )

            method, url = mock_send.call_args[0][0], mock_send.call_args[0][1]
            assert method == "POST"
            assert url.endswith("/v1/messages")
            assert mock_send.call_args.kwargs["body"] is not None
            assert result == {"id": "msg1"}

    @pytest.mark.asyncio
    async def test_get_message_details_success(self, mock_token_provider):
        """Test get message details issues a GET to the message route."""
        client = WebexClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider,
        )
        mock_response = MockResponse(status=200, text='{"id": "msg1"}')

        with patch.object(
            client._http_client,
            "send_async",
            new_callable=AsyncMock,
            return_value=mock_response,
        ) as mock_send:
            result = await client.get_message_details_async(message_id="msg1")

            method, url = mock_send.call_args[0][0], mock_send.call_args[0][1]
            assert method == "GET"
            assert url.endswith("/v1/messages/msg1")
            assert result == {"id": "msg1"}

    @pytest.mark.asyncio
    async def test_get_people_success(self, mock_token_provider):
        """Test get people issues a GET with query parameters."""
        client = WebexClient(
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
            result = await client.get_people_async(email="a@b.com")

            method, url = mock_send.call_args[0][0], mock_send.call_args[0][1]
            assert method == "GET"
            assert "/v1/people" in url
            assert "email=a%40b.com" in url
            assert result == {"items": []}

    @pytest.mark.asyncio
    async def test_get_my_own_details_success(self, mock_token_provider):
        """Test get my own details issues a GET to the people/me route."""
        client = WebexClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider,
        )
        mock_response = MockResponse(status=200, text='{"id": "me"}')

        with patch.object(
            client._http_client,
            "send_async",
            new_callable=AsyncMock,
            return_value=mock_response,
        ) as mock_send:
            result = await client.get_my_own_details_async()

            method, url = mock_send.call_args[0][0], mock_send.call_args[0][1]
            assert method == "GET"
            assert url.endswith("/v1/people/me")
            assert result == {"id": "me"}

    @pytest.mark.asyncio
    async def test_get_spaces_success(self, mock_token_provider):
        """Test get spaces issues a GET to the rooms route."""
        client = WebexClient(
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
            result = await client.get_spaces_async()

            method, url = mock_send.call_args[0][0], mock_send.call_args[0][1]
            assert method == "GET"
            assert url.endswith("/v1/rooms")
            assert result == {"items": []}

    @pytest.mark.asyncio
    async def test_create_space_success(self, mock_token_provider):
        """Test create space issues a POST to the rooms route."""
        client = WebexClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider,
        )
        mock_response = MockResponse(status=200, text='{"id": "R1"}')

        with patch.object(
            client._http_client,
            "send_async",
            new_callable=AsyncMock,
            return_value=mock_response,
        ) as mock_send:
            result = await client.create_space_async(
                input=CreateSpaceInput(title="My Space"),
            )

            method, url = mock_send.call_args[0][0], mock_send.call_args[0][1]
            assert method == "POST"
            assert url.endswith("/v1/rooms")
            assert mock_send.call_args.kwargs["body"] is not None
            assert result == {"id": "R1"}

    @pytest.mark.asyncio
    async def test_get_space_detail_success(self, mock_token_provider):
        """Test get space detail issues a GET to the room route."""
        client = WebexClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider,
        )
        mock_response = MockResponse(status=200, text='{"id": "R1"}')

        with patch.object(
            client._http_client,
            "send_async",
            new_callable=AsyncMock,
            return_value=mock_response,
        ) as mock_send:
            result = await client.get_space_detail_async(room_id="R1")

            method, url = mock_send.call_args[0][0], mock_send.call_args[0][1]
            assert method == "GET"
            assert url.endswith("/v1/rooms/R1")
            assert result == {"id": "R1"}

    @pytest.mark.asyncio
    async def test_create_team_member_success(self, mock_token_provider):
        """Test add member to team issues a POST to the team memberships route."""
        client = WebexClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider,
        )
        mock_response = MockResponse(status=200, text='{"id": "tm1"}')

        with patch.object(
            client._http_client,
            "send_async",
            new_callable=AsyncMock,
            return_value=mock_response,
        ) as mock_send:
            result = await client.create_team_member_async(
                input=CreateTeamMemberInput(team_id="T1", person_email="a@b.com"),
            )

            method, url = mock_send.call_args[0][0], mock_send.call_args[0][1]
            assert method == "POST"
            assert url.endswith("/v1/team/memberships")
            assert mock_send.call_args.kwargs["body"] is not None
            assert result == {"id": "tm1"}

    @pytest.mark.asyncio
    async def test_empty_response_body_returns_none(self, mock_token_provider):
        """Test a 2xx response with no body returns None."""
        client = WebexClient(
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
            result = await client.get_spaces_async()

            assert result is None


class TestWebexClientErrorHandling:
    """Error handling tests for WebexClient operations."""

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "operation",
        [
            "create_space_member",
            "get_messages",
            "send_message",
            "get_message_details",
            "get_people",
            "get_my_own_details",
            "get_spaces",
            "create_space",
            "get_space_detail",
            "create_team_member",
        ],
    )
    async def test_error_response_raises_exception(self, mock_token_provider, operation):
        """Test non-2xx responses raise ConnectorException for every operation."""
        client = WebexClient(
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
                if operation == "create_space_member":
                    await client.create_space_member_async(input=CreateSpaceMemberInput())
                elif operation == "get_messages":
                    await client.get_messages_async(room_id="R1")
                elif operation == "send_message":
                    await client.send_message_async(input=SendMessageInput())
                elif operation == "get_message_details":
                    await client.get_message_details_async(message_id="msg1")
                elif operation == "get_people":
                    await client.get_people_async(email="a@b.com")
                elif operation == "get_my_own_details":
                    await client.get_my_own_details_async()
                elif operation == "get_spaces":
                    await client.get_spaces_async()
                elif operation == "create_space":
                    await client.create_space_async(input=CreateSpaceInput())
                elif operation == "get_space_detail":
                    await client.get_space_detail_async(room_id="R1")
                else:
                    await client.create_team_member_async(input=CreateTeamMemberInput())

            assert exc_info.value.status_code == 500


class TestWebexTriggerOperations:
    """Tests for the module-level TRIGGER_OPERATIONS registry."""

    def test_all_expected_triggers_registered(self):
        """Test the registry exposes every Webex trigger operation."""
        assert set(TRIGGER_OPERATIONS) == {
            "MembershipsUpdated",
            "MembershipsDeleted",
            "MembershipsCreated",
            "MessagesCreated",
            "MessagesDeleted",
            "SpaceCreated",
            "SpaceUpdated",
        }

    @pytest.mark.parametrize("operation_id", list(TRIGGER_OPERATIONS))
    def test_trigger_metadata_shape(self, operation_id):
        """Test each trigger entry carries the expected metadata fields."""
        trigger = TRIGGER_OPERATIONS[operation_id]

        assert trigger["operation_id"] == operation_id
        assert trigger["method"] == "post"
        assert trigger["path"].startswith("/{connectionId}/")
        assert trigger["required_parameters"] == ["body"]
        assert "callback_payload_type" in trigger

    def test_triggers_are_not_client_methods(self):
        """Test trigger operations are not emitted as callable client methods."""
        assert not hasattr(WebexClient, "memberships_created_async")
        assert not hasattr(WebexClient, "messages_created_async")


class TestWebexTypeSerialization:
    """Tests for Webex dataclass defaults and reserved-name field renames."""

    def test_dataclass_defaults(self):
        """Test dataclasses default to None and reserved names are renamed."""
        assert CreateSpaceInput().title is None
        assert CreateSpaceInput().team_id is None
        assert SendMessageInput().room_id is None
        assert CreateTeamMemberInput().team_id is None
