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
    CreateSectionInput,
    PostMessageToSelfRequest,
    NewChat,
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


class TestChannelOperations:
    """Tests for channel operations."""

    @pytest.mark.asyncio
    async def test_get_channels_for_group_success(self, mock_token_provider):
        """Test successful retrieval of channels."""
        client = TeamsClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(
            status=200,
            text='{"value": [{"id": "channel1", "displayName": "General"}]}'
        )

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ) as mock_send:
            result = await client.get_channels_for_group_async("group123")

            call_args = mock_send.call_args
            assert call_args[0][0] == "GET"
            assert "/beta/groups/group123/channels" in call_args[0][1]
            assert "value" in result

    @pytest.mark.asyncio
    async def test_create_channel_success(self, mock_token_provider):
        """Test successful channel creation."""
        client = TeamsClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(
            status=201,
            text='{"id": "channel123", "displayName": "New Channel"}'
        )

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ) as mock_send:
            input_data = CreateChannelInput(
                display_name="New Channel",
                description="Test Description"
            )
            result = await client.create_channel_async(input_data, "group123")

            call_args = mock_send.call_args
            assert call_args[0][0] == "POST"
            assert "/beta/groups/group123/channels" in call_args[0][1]
            assert result["id"] == "channel123"

    @pytest.mark.skip(reason="Method get_channel_async does not exist in generated SDK")
    @pytest.mark.asyncio
    async def test_get_channel_success(self, mock_token_provider):
        """Test successful channel retrieval."""
        pass

    @pytest.mark.asyncio
    async def test_get_all_channels_for_team_success(self, mock_token_provider):
        """Test successful retrieval of all channels for a team."""
        client = TeamsClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(
            status=200,
            text='{"value": [{"id": "channel1", "displayName": "General"}]}'
        )

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ) as mock_send:
            result = await client.get_all_channels_for_team_async("group123")

            call_args = mock_send.call_args
            assert call_args[0][0] == "GET"
            assert "/beta/teams/group123/allChannels" in call_args[0][1]
            assert "value" in result


class TestChatOperations:
    """Tests for chat operations."""

    @pytest.mark.skip(reason="Method get_chats_async does not exist in generated SDK")
    @pytest.mark.asyncio
    async def test_get_chats_success(self, mock_token_provider):
        """Test successful retrieval of chats."""
        pass

    @pytest.mark.asyncio
    async def test_create_chat_success(self, mock_token_provider):
        """Test successful chat creation."""
        client = TeamsClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(
            status=201,
            text='{"id": "chat123", "topic": "Test Chat"}'
        )

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ) as mock_send:
            input_data = NewChat(topic="Test Chat", members="user1;user2")
            result = await client.create_chat_async(input_data)

            call_args = mock_send.call_args
            assert call_args[0][0] == "POST"
            assert "/beta/chats" in call_args[0][1]
            assert result["id"] == "chat123"


class TestTagOperations:
    """Tests for tag operations."""

    @pytest.mark.asyncio
    async def test_get_tags_success(self, mock_token_provider):
        """Test successful retrieval of tags."""
        client = TeamsClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(
            status=200,
            text='{"value": [{"id": "tag1", "displayName": "Test Tag"}]}'
        )

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ) as mock_send:
            result = await client.get_tags_async("group123")

            call_args = mock_send.call_args
            assert call_args[0][0] == "GET"
            assert "/v1.0/teams/group123/tags" in call_args[0][1]
            assert "value" in result

    @pytest.mark.asyncio
    async def test_create_tag_success(self, mock_token_provider):
        """Test successful tag creation."""
        client = TeamsClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(
            status=201,
            text='{"id": "tag123", "displayName": "New Tag"}'
        )

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ) as mock_send:
            input_data = CreateTagInput(display_name="New Tag")
            result = await client.create_tag_async(input_data, "group123")

            call_args = mock_send.call_args
            assert call_args[0][0] == "POST"
            assert "/v1.0/teams/group123/tags" in call_args[0][1]
            assert result["id"] == "tag123"

    @pytest.mark.skip(reason="Method add_member_to_tag_async does not exist in generated SDK")
    @pytest.mark.asyncio
    async def test_add_member_to_tag_success(self, mock_token_provider):
        """Test successful member addition to tag."""
        pass

    @pytest.mark.skip(reason="Method get_tag_members_async does not exist in generated SDK")
    @pytest.mark.asyncio
    async def test_get_tag_members_success(self, mock_token_provider):
        """Test successful retrieval of tag members."""
        pass

    @pytest.mark.skip(reason="Method delete_tag_member_async does not exist in generated SDK")
    @pytest.mark.asyncio
    async def test_delete_tag_member_success(self, mock_token_provider):
        """Test successful tag member deletion."""
        pass

    @pytest.mark.skip(reason="Method delete_tag_async does not exist in generated SDK")
    @pytest.mark.asyncio
    async def test_delete_tag_success(self, mock_token_provider):
        """Test successful tag deletion."""
        pass


class TestMessageOperations:
    """Tests for message operations."""

    @pytest.mark.skip(reason="Method does not exist in generated SDK")
    @pytest.mark.asyncio
    async def test_get_messages_from_channel_success(self, mock_token_provider):
        """Test successful retrieval of channel messages."""
        pass

    @pytest.mark.skip(reason="Method get_message_details_async does not exist in generated SDK")
    @pytest.mark.asyncio
    async def test_get_message_details_success(self, mock_token_provider):
        """Test successful retrieval of message details."""
        pass

    @pytest.mark.skip(reason="Method list_replies_to_message_async does not exist in generated SDK")
    @pytest.mark.asyncio
    async def test_list_replies_to_message_success(self, mock_token_provider):
        """Test successful listing of message replies."""
        pass

    @pytest.mark.skip(reason="Method list_replies_to_message_async does not exist in generated SDK")
    @pytest.mark.asyncio
    async def test_list_replies_with_top_parameter(self, mock_token_provider):
        """Test listing replies with top parameter."""
        pass

    @pytest.mark.asyncio
    async def test_post_message_to_self_success(self, mock_token_provider):
        """Test successful posting message to self."""
        client = TeamsClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(
            status=201,
            text='{"id": "message123", "body": {"content": "Test message"}}'
        )

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ) as mock_send:
            input_data = PostMessageToSelfRequest(body={"content": "Test message"})
            result = await client.post_message_to_self_async(input_data)

            call_args = mock_send.call_args
            assert call_args[0][0] == "POST"
            assert "/v1.0/chats/48:notes/messages" in call_args[0][1]
            assert result["id"] == "message123"


class TestMemberOperations:
    """Tests for member operations."""

    @pytest.mark.skip(reason="Method list_members_async does not exist in generated SDK")
    @pytest.mark.asyncio
    async def test_list_members_success(self, mock_token_provider):
        """Test successful listing of members."""
        pass

    @pytest.mark.asyncio
    async def test_list_team_members_success(self, mock_token_provider):
        """Test successful listing of team members."""
        client = TeamsClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(
            status=200,
            text='{"value": [{"id": "member1", "displayName": "User 1"}]}'
        )

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ) as mock_send:
            result = await client.list_team_members_async("team123")

            call_args = mock_send.call_args
            assert call_args[0][0] == "GET"
            assert "/v1.0/teams/team123/members" in call_args[0][1]
            assert "value" in result

    @pytest.mark.asyncio
    async def test_add_member_to_team_success(self, mock_token_provider):
        """Test successful addition of member to team."""
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
        ) as mock_send:
            input_data = AddMemberToTeamInput(user_id="user@example.com", owner=False)
            await client.add_member_to_team_async(input_data, "team123")

            call_args = mock_send.call_args
            assert call_args[0][0] == "POST"
            assert "/v1.0/teams/team123/members" in call_args[0][1]

    @pytest.mark.asyncio
    async def test_remove_member_from_team_success(self, mock_token_provider):
        """Test successful removal of member from team."""
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
        ) as mock_send:
            await client.remove_member_from_team_async("team123", "membership123")

            call_args = mock_send.call_args
            assert call_args[0][0] == "DELETE"
            assert "/v1.0/teams/team123/members/membership123" in call_args[0][1]


class TestTriggerOperations:
    """Tests for trigger operations."""

    @pytest.mark.skip(reason="Method on_new_channel_message_async does not exist in generated SDK")
    @pytest.mark.asyncio
    async def test_on_new_channel_message_success(self, mock_token_provider):
        """Test successful new channel message trigger."""
        pass

    @pytest.mark.skip(reason="Method on_new_channel_message_async does not exist in generated SDK")
    @pytest.mark.asyncio
    async def test_on_new_channel_message_with_top(self, mock_token_provider):
        """Test new channel message trigger with top parameter."""
        pass


class TestTeamOperations:
    """Tests for team operations."""

    @pytest.mark.asyncio
    async def test_get_team_success(self, mock_token_provider):
        """Test successful retrieval of a team."""
        client = TeamsClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(
            status=200,
            text='{"id": "team123", "displayName": "Test Team", "description": "A test team"}'
        )

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ) as mock_send:
            result = await client.get_team_async("team123")

            call_args = mock_send.call_args
            assert call_args[0][0] == "GET"
            assert "/beta/teams/team123" in call_args[0][1]
            assert result["id"] == "team123"
            assert result["displayName"] == "Test Team"

    @pytest.mark.asyncio
    async def test_get_team_error(self, mock_token_provider):
        """Test get team error handling."""
        client = TeamsClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(status=404, text='{"error": "Team not found"}')

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ):
            with pytest.raises(ConnectorException) as exc_info:
                await client.get_team_async("nonexistent")

            assert exc_info.value.status_code == 404


class TestOnlineMeetingOperations:
    """Tests for online meeting operations."""

    @pytest.mark.asyncio
    async def test_get_online_meeting_success(self, mock_token_provider):
        """Test successful retrieval of an online meeting."""
        client = TeamsClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(
            status=200,
            text='{"id": "meeting123", "subject": "Test Meeting", '
                 '"joinWebUrl": "https://teams.microsoft.com/l/meetup/..."}'
        )

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ) as mock_send:
            result = await client.get_online_meeting_async("meetingId", "meeting123")

            call_args = mock_send.call_args
            assert call_args[0][0] == "GET"
            assert "/v1.0/me/onlineMeetings/lookup" in call_args[0][1]
            assert "lookupType=meetingId" in call_args[0][1]
            assert result["id"] == "meeting123"


class TestSectionOperations:
    """Tests for section operations."""

    @pytest.mark.asyncio
    async def test_list_sections_success(self, mock_token_provider):
        """Test successful listing of sections."""
        client = TeamsClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(
            status=200,
            text='{"value": [{"id": "section1", "displayName": "My Section"}]}'
        )

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ) as mock_send:
            result = await client.list_sections_async()

            call_args = mock_send.call_args
            assert call_args[0][0] == "GET"
            assert "/beta/me/teamwork/sections" in call_args[0][1]
            assert "value" in result

    @pytest.mark.asyncio
    async def test_create_section_success(self, mock_token_provider):
        """Test successful section creation."""
        client = TeamsClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(
            status=201,
            text='{"id": "section123", "displayName": "New Section"}'
        )

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ) as mock_send:
            input_data = CreateSectionInput(display_name="New Section")
            result = await client.create_section_async(input_data)

            call_args = mock_send.call_args
            assert call_args[0][0] == "POST"
            assert "/beta/me/teamwork/sections" in call_args[0][1]
            assert result["id"] == "section123"


class TestAdhocCallOperations:
    """Tests for ad-hoc call recording and transcript operations."""

    @pytest.mark.asyncio
    async def test_get_all_adhoc_call_recordings_success(self, mock_token_provider):
        """Test successful retrieval of ad-hoc call recordings."""
        client = TeamsClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(
            status=200,
            text='{"value": [{"id": "recording1", "createdDateTime": "2024-01-15T10:00:00Z"}]}'
        )

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ) as mock_send:
            result = await client.get_all_adhoc_call_recordings_async()

            call_args = mock_send.call_args
            assert call_args[0][0] == "GET"
            assert "/v1.0/me/adhocCalls/getAllRecordings" in call_args[0][1]
            assert "value" in result

    @pytest.mark.asyncio
    async def test_get_all_adhoc_call_recordings_with_params(self, mock_token_provider):
        """Test retrieval of ad-hoc call recordings with query parameters."""
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
        ) as mock_send:
            await client.get_all_adhoc_call_recordings_async(
                start_date_time="2024-01-01T00:00:00Z",
                end_date_time="2024-01-31T23:59:59Z",
                top="10"
            )

            call_args = mock_send.call_args
            assert call_args[0][0] == "GET"
            assert "startDateTime=" in call_args[0][1]
            assert "endDateTime=" in call_args[0][1]
            assert "$top=10" in call_args[0][1]

    @pytest.mark.asyncio
    async def test_get_all_adhoc_call_transcripts_success(self, mock_token_provider):
        """Test successful retrieval of ad-hoc call transcripts."""
        client = TeamsClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(
            status=200,
            text='{"value": [{"id": "transcript1", "createdDateTime": "2024-01-15T10:00:00Z"}]}'
        )

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ) as mock_send:
            result = await client.get_all_adhoc_call_transcripts_async()

            call_args = mock_send.call_args
            assert call_args[0][0] == "GET"
            assert "/v1.0/me/adhocCalls/getAllTranscripts" in call_args[0][1]
            assert "value" in result

    @pytest.mark.asyncio
    async def test_get_all_adhoc_call_transcripts_with_params(self, mock_token_provider):
        """Test retrieval of ad-hoc call transcripts with query parameters."""
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
        ) as mock_send:
            await client.get_all_adhoc_call_transcripts_async(
                start_date_time="2024-01-01T00:00:00Z",
                end_date_time="2024-01-31T23:59:59Z",
                top="10"
            )

            call_args = mock_send.call_args
            assert call_args[0][0] == "GET"
            assert "startDateTime=" in call_args[0][1]
            assert "endDateTime=" in call_args[0][1]
            assert "$top=10" in call_args[0][1]


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

    def test_create_section_input_creation(self):
        """Test CreateSectionInput data class creation."""
        section = CreateSectionInput(
            display_name="My Section",
            is_expanded=True
        )
        assert section.display_name == "My Section"
        assert section.is_expanded is True

    def test_post_message_to_self_request_creation(self):
        """Test PostMessageToSelfRequest data class creation."""
        message = PostMessageToSelfRequest(
            body={"content": "Test message content"}
        )
        assert message.body["content"] == "Test message content"

    def test_new_chat_creation(self):
        """Test NewChat data class creation."""
        chat = NewChat(
            topic="Group Chat Topic",
            members="user1@example.com;user2@example.com"
        )
        assert chat.topic == "Group Chat Topic"
        assert chat.members == "user1@example.com;user2@example.com"


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
