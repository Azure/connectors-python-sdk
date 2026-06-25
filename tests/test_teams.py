"""Unit tests for Teams connector client."""

import pytest
from unittest.mock import AsyncMock, patch

from azure.connectors.teams import (
    TeamsClient,
    NewMeeting,
    CreateChannelInput,
    CreateTagInput,
    AddMemberToTagInput,
    CreateATeamInput,
    AddMemberToTeamInput,
    AddMemberToChannelInput,
    NewChat,
    HttpRequestInput,
    WebhookChatMessageTriggerInput,
    DynamicUserMessageWithOptionsSubscriptionRequest,
)
from azure.connectors.sdk import ConnectorClientOptions, ConnectorException
from tests.conftest import MockResponse


class TestTeamsClientInitialization:
    """Tests for TeamsClient initialization."""

    def test_init_with_valid_url_and_defaults(self, mock_token_provider):
        """Test initialization with valid URL and default options."""
        client = TeamsClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        assert client._connection_runtime_url == "https://example.azure.com/connections/test"

    def test_init_with_trailing_slash(self, mock_token_provider):
        """Test that trailing slash is removed from URL."""
        client = TeamsClient(
            "https://example.azure.com/connections/test/",
            token_provider=mock_token_provider
        )

        assert client._connection_runtime_url == "https://example.azure.com/connections/test"

    def test_init_with_custom_token_provider(self, mock_token_provider):
        """Test initialization with custom token provider."""
        client = TeamsClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        assert client is not None

    def test_init_with_custom_options(self, mock_token_provider):
        """Test initialization with custom options."""
        options = ConnectorClientOptions()
        client = TeamsClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider,
            options=options
        )

        assert client is not None

    def test_init_with_empty_url_raises_error(self, mock_token_provider):
        """Test that empty URL raises ValueError."""
        with pytest.raises(ValueError, match="connection_runtime_url cannot be None or empty"):
            TeamsClient("", token_provider=mock_token_provider)

    def test_init_with_none_url_raises_error(self, mock_token_provider):
        """Test that None URL raises ValueError."""
        with pytest.raises(ValueError, match="connection_runtime_url cannot be None or empty"):
            TeamsClient(None, token_provider=mock_token_provider)

    def test_connector_name_property(self, mock_token_provider):
        """Test connector_name property returns correct value."""
        client = TeamsClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        assert client.connector_name == "teams"


class TestTeamsClientLifecycle:
    """Tests for TeamsClient lifecycle methods."""

    @pytest.mark.asyncio
    async def test_close(self, mock_token_provider):
        """Test close method."""
        client = TeamsClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        with patch.object(client._http_client, 'close', new_callable=AsyncMock) as mock_close:
            await client.close()
            mock_close.assert_called_once()

    @pytest.mark.asyncio
    async def test_context_manager(self, mock_token_provider):
        """Test async context manager."""
        client = TeamsClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        with patch.object(client._http_client, 'close', new_callable=AsyncMock) as mock_close:
            async with client:
                assert client is not None

            mock_close.assert_called_once()


class TestTeamsMeetingOperations:
    """Tests for Teams meeting operations."""

    @pytest.mark.asyncio
    async def test_create_teams_meeting_success(self, mock_token_provider):
        """Test successful Teams meeting creation."""
        client = TeamsClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(
            status=201,
            text='{"id": "meeting123", "joinUrl": "https://teams.microsoft.com/l/meetup/..."}'
        )

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ) as mock_send:
            input_data = NewMeeting()
            result = await client.create_teams_meeting_async(input_data, "calendar123")

            call_args = mock_send.call_args
            assert call_args[0][0] == "POST"
            assert "/v1.0/me/calendars/calendar123/events" in call_args[0][1]
            assert result["id"] == "meeting123"

    @pytest.mark.asyncio
    async def test_create_teams_meeting_error(self, mock_token_provider):
        """Test Teams meeting creation error handling."""
        client = TeamsClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(status=400, text='{"error": "Bad Request"}')

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ):
            input_data = NewMeeting()
            with pytest.raises(ConnectorException) as exc_info:
                await client.create_teams_meeting_async(input_data, "calendar123")

            assert exc_info.value.status_code == 400


class TestTeamsListOperations:
    """Tests for Teams list operations."""

    @pytest.mark.asyncio
    async def test_get_all_teams_success(self, mock_token_provider):
        """Test successful retrieval of all teams."""
        client = TeamsClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(
            status=200,
            text='{"value": [{"id": "team1", "displayName": "Team 1"}]}'
        )

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ):
            result = await client.get_all_teams_async()

            assert "value" in result
            assert len(result["value"]) == 1

    @pytest.mark.asyncio
    async def test_get_all_teams_empty_response(self, mock_token_provider):
        """Test get all teams with empty response."""
        client = TeamsClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(status=204, text='')

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ):
            result = await client.get_all_teams_async()

            assert result is None

    @pytest.mark.asyncio
    async def test_get_all_associated_teams_success(self, mock_token_provider):
        """Test successful retrieval of associated teams."""
        client = TeamsClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(
            status=200,
            text='{"value": [{"tenantId": "tenant1", "teamId": "team1"}]}'
        )

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ):
            result = await client.get_all_associated_teams_async()

            assert "value" in result

    @pytest.mark.asyncio
    async def test_get_all_teams_error_response(self, mock_token_provider):
        """Test that error response raises ConnectorException."""
        client = TeamsClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(
            status=401,
            text='{"error": "Unauthorized"}'
        )

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ):
            with pytest.raises(ConnectorException) as exc_info:
                await client.get_all_associated_teams_async()

            assert exc_info.value.status_code == 401


class TestUserOperations:
    """Tests for user operations."""

    @pytest.mark.asyncio
    async def test_at_mention_user_success(self, mock_token_provider):
        """Test successful @mention token retrieval."""
        client = TeamsClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(
            status=200,
            text='{"id": "user123", "displayName": "John Doe", "mail": "john@example.com"}'
        )

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ) as mock_send:
            result = await client.at_mention_user_async("user123")

            call_args = mock_send.call_args
            assert call_args[0][0] == "GET"
            assert "/v1.0/users/user123" in call_args[0][1]
            assert result["displayName"] == "John Doe"

    @pytest.mark.asyncio
    async def test_at_mention_user_error(self, mock_token_provider):
        """Test @mention user error handling."""
        client = TeamsClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(status=404, text='{"error": "User not found"}')

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ):
            with pytest.raises(ConnectorException) as exc_info:
                await client.at_mention_user_async("nonexistent")

            assert exc_info.value.status_code == 404


class TestChatOperations:
    """Tests for chat operations."""

    @pytest.mark.asyncio
    async def test_create_chat_success(self, mock_token_provider):
        """Test successful chat creation."""
        client = TeamsClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(
            status=201,
            text='{"id": "chat123", "chatType": "oneOnOne"}'
        )

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ) as mock_send:
            input_data = NewChat()
            result = await client.create_chat_async(input_data)

            call_args = mock_send.call_args
            assert call_args[0][0] == "POST"
            assert "/beta/chats" in call_args[0][1]
            assert result["id"] == "chat123"

    @pytest.mark.asyncio
    async def test_create_chat_error(self, mock_token_provider):
        """Test chat creation error handling."""
        client = TeamsClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(status=400, text='{"error": "Bad Request"}')

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ):
            with pytest.raises(ConnectorException) as exc_info:
                await client.create_chat_async(NewChat())

            assert exc_info.value.status_code == 400


class TestTeamCreationOperations:
    """Tests for team creation operations."""

    @pytest.mark.asyncio
    async def test_create_a_team_success(self, mock_token_provider):
        """Test successful team creation."""
        client = TeamsClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(
            status=201,
            text='{"id": "team123", "displayName": "New Team"}'
        )

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ) as mock_send:
            input_data = CreateATeamInput(
                display_name="New Team",
                description="A new team",
                visibility="Private"
            )
            result = await client.create_a_team_async(input_data)

            call_args = mock_send.call_args
            assert call_args[0][0] == "POST"
            assert "/beta/teams" in call_args[0][1]
            assert result["displayName"] == "New Team"

    @pytest.mark.asyncio
    async def test_create_a_team_error(self, mock_token_provider):
        """Test team creation error handling."""
        client = TeamsClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(status=403, text='{"error": "Forbidden"}')

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ):
            with pytest.raises(ConnectorException) as exc_info:
                await client.create_a_team_async(CreateATeamInput())

            assert exc_info.value.status_code == 403


class TestMembershipTriggers:
    """Tests for membership trigger operations."""

    @pytest.mark.asyncio
    async def test_on_group_membership_add_success(self, mock_token_provider):
        """Test successful membership add trigger."""
        client = TeamsClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(
            status=200,
            text='{"value": [{"id": "member1", "displayName": "New Member"}]}'
        )

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ) as mock_send:
            result = await client.on_group_membership_add_async()

            call_args = mock_send.call_args
            assert call_args[0][0] == "GET"
            assert "/trigger/v1.0/groups/delta" in call_args[0][1]
            assert "value" in result

    @pytest.mark.asyncio
    async def test_on_group_membership_add_with_select(self, mock_token_provider):
        """Test membership add trigger with select parameter."""
        client = TeamsClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(
            status=200,
            text='{"value": [{"displayName": "New Member"}]}'
        )

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ) as mock_send:
            result = await client.on_group_membership_add_async(select="displayName")

            call_args = mock_send.call_args
            assert "$select=" in call_args[0][1]
            assert "value" in result

    @pytest.mark.asyncio
    async def test_on_group_membership_removal_success(self, mock_token_provider):
        """Test successful membership removal trigger."""
        client = TeamsClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(
            status=200,
            text='{"value": [{"id": "member1", "displayName": "Removed Member"}]}'
        )

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ) as mock_send:
            result = await client.on_group_membership_removal_async()

            call_args = mock_send.call_args
            assert call_args[0][0] == "GET"
            assert "/trigger/v1.0/groups/removal" in call_args[0][1]
            assert "value" in result

    @pytest.mark.asyncio
    async def test_on_group_membership_removal_error(self, mock_token_provider):
        """Test membership removal trigger error handling."""
        client = TeamsClient(
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
                await client.on_group_membership_removal_async()

            assert exc_info.value.status_code == 401


class TestHttpRequestOperations:
    """Tests for HTTP request operations."""

    @pytest.mark.asyncio
    async def test_http_request_success(self, mock_token_provider):
        """Test successful HTTP request."""
        client = TeamsClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(
            status=200,
            text='{"data": "response data"}'
        )

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ) as mock_send:
            input_data = HttpRequestInput()
            result = await client.http_request_async(input_data)

            call_args = mock_send.call_args
            assert call_args[0][0] == "POST"
            assert "/httprequest" in call_args[0][1]
            assert result["data"] == "response data"

    @pytest.mark.asyncio
    async def test_http_request_error(self, mock_token_provider):
        """Test HTTP request error handling."""
        client = TeamsClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(status=500, text='{"error": "Internal Server Error"}')

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ):
            with pytest.raises(ConnectorException) as exc_info:
                await client.http_request_async(HttpRequestInput())

            assert exc_info.value.status_code == 500


class TestWebhookOperations:
    """Tests for webhook and subscription operations."""

    @pytest.mark.asyncio
    async def test_webhook_chat_message_trigger_success(self, mock_token_provider):
        """Test successful webhook chat message trigger."""
        client = TeamsClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(status=200, text='')

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ) as mock_send:
            input_data = WebhookChatMessageTriggerInput()
            await client.webhook_chat_message_trigger_async(input_data)

            call_args = mock_send.call_args
            assert call_args[0][0] == "POST"
            assert "/beta/subscriptions/chatmessagetrigger" in call_args[0][1]

    @pytest.mark.asyncio
    async def test_webhook_chat_message_trigger_error(self, mock_token_provider):
        """Test webhook chat message trigger error handling."""
        client = TeamsClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(status=400, text='{"error": "Bad Request"}')

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ):
            with pytest.raises(ConnectorException):
                await client.webhook_chat_message_trigger_async(WebhookChatMessageTriggerInput())

    @pytest.mark.asyncio
    async def test_subscribe_user_message_with_options_success(self, mock_token_provider):
        """Test successful user message subscription."""
        client = TeamsClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(status=200, text='')

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ) as mock_send:
            input_data = DynamicUserMessageWithOptionsSubscriptionRequest()
            await client.subscribe_user_message_with_options_async(input_data)

            call_args = mock_send.call_args
            assert call_args[0][0] == "POST"
            assert "/flowbot/actions/messagewithoptions" in call_args[0][1]

    @pytest.mark.asyncio
    async def test_subscribe_user_message_with_options_error(self, mock_token_provider):
        """Test user message subscription error handling."""
        client = TeamsClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(status=403, text='{"error": "Forbidden"}')

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ):
            with pytest.raises(ConnectorException):
                await client.subscribe_user_message_with_options_async(
                    DynamicUserMessageWithOptionsSubscriptionRequest()
                )


class TestDataClasses:
    """Tests for data class creation and validation."""

    def test_new_meeting_creation(self):
        """Test NewMeeting data class creation."""
        meeting = NewMeeting()
        assert meeting is not None

    def test_create_channel_input_creation(self):
        """Test CreateChannelInput data class creation."""
        channel = CreateChannelInput(
            display_name="Test Channel",
            description="Test Description"
        )
        assert channel.display_name == "Test Channel"
        assert channel.description == "Test Description"

    def test_create_tag_input_creation(self):
        """Test CreateTagInput data class creation."""
        tag = CreateTagInput(display_name="Test Tag")
        assert tag.display_name == "Test Tag"

    def test_add_member_to_tag_input_creation(self):
        """Test AddMemberToTagInput data class creation."""
        member = AddMemberToTagInput(user_id="user123")
        assert member.user_id == "user123"

    def test_create_a_team_input_creation(self):
        """Test CreateATeamInput data class creation."""
        team = CreateATeamInput(
            display_name="Test Team",
            description="Test Description",
            visibility="Private"
        )
        assert team.display_name == "Test Team"
        assert team.description == "Test Description"
        assert team.visibility == "Private"

    def test_add_member_to_team_input_creation(self):
        """Test AddMemberToTeamInput data class creation."""
        member = AddMemberToTeamInput(
            user_id="user@example.com",
            owner=True
        )
        assert member.user_id == "user@example.com"
        assert member.owner is True

    def test_add_member_to_channel_input_creation(self):
        """Test AddMemberToChannelInput data class creation."""
        member = AddMemberToChannelInput(
            user_id="user@example.com",
            owner=False
        )
        assert member.user_id == "user@example.com"
        assert member.owner is False


class TestEdgeCases:
    """Tests for edge cases and error conditions."""

    @pytest.mark.asyncio
    async def test_multiple_consecutive_calls(self, mock_token_provider):
        """Test multiple consecutive API calls."""
        client = TeamsClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(
            status=200,
            text='{"value": []}'
        )

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ):
            result1 = await client.get_all_teams_async()
            result2 = await client.get_all_teams_async()

            assert result1 is not None
            assert result2 is not None

    @pytest.mark.asyncio
    async def test_json_parse_error_raises_exception(self, mock_token_provider):
        """Test that invalid JSON raises an exception."""
        client = TeamsClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(status=200, text='invalid json')

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ):
            with pytest.raises(Exception):
                await client.get_all_teams_async()

    @pytest.mark.asyncio
    async def test_url_construction_with_multiple_trailing_slashes(self, mock_token_provider):
        """Test URL construction handles multiple trailing slashes."""
        client = TeamsClient(
            "https://example.azure.com/connections/test///",
            token_provider=mock_token_provider
        )

        assert client._connection_runtime_url == "https://example.azure.com/connections/test"

    @pytest.mark.asyncio
    async def test_http_client_property_access(self, mock_token_provider):
        """Test that http_client property is accessible."""
        client = TeamsClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        assert client.http_client is not None
        assert client._http_client is not None

    @pytest.mark.asyncio
    async def test_error_response_raises_exception(self, mock_token_provider):
        """Test that error responses raise ConnectorException."""
        client = TeamsClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(status=500, text='{"error": "Internal Server Error"}')

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ):
            with pytest.raises(ConnectorException) as exc_info:
                await client.get_all_teams_async()

            assert exc_info.value.status_code == 500

    @pytest.mark.asyncio
    async def test_404_error_raises_exception(self, mock_token_provider):
        """Test that 404 error raises ConnectorException."""
        client = TeamsClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(status=404, text='{"error": "Not Found"}')

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ):
            with pytest.raises(ConnectorException) as exc_info:
                await client.get_all_teams_async()

            assert exc_info.value.status_code == 404
