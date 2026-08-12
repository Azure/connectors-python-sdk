# Copyright (c) Microsoft Corporation. All rights reserved.

"""Unit tests for Office365groupsClient."""

import pytest
from unittest.mock import AsyncMock, patch

from azure.connectors.office365groups import (
    Office365groupsClient,
    ListGroupMembersResponse,
    OnGroupMemberAddedOrRemovedResponse,
    ListGroupsResponse,
    CreateCalendarEventResponse,
    OnNewEventResponse,
    ObjectWithoutType,
    ListOwnedGroupsResponse,
    SensitivityLabelMetadata,
    TRIGGER_OPERATIONS,
    UpdateCalendarEventRequest,
    UpdateCalendarEventHTMLRequest,
)
from azure.connectors.sdk import (
    ConnectorClientOptions,
    ManagedIdentityTokenProvider,
    ConnectorException,
)
from tests.conftest import MockResponse


class TestOffice365groupsClientInitialization:
    """Tests for Office365groupsClient initialization."""

    def test_init_with_valid_url_and_defaults(self):
        """Test initialization with valid URL and default parameters."""
        client = Office365groupsClient("https://example.azure.com/connections/test")

        assert client._connection_runtime_url == "https://example.azure.com/connections/test"
        assert client.connector_name == "office365groups"
        assert isinstance(client._http_client._token_provider, ManagedIdentityTokenProvider)

    def test_init_with_trailing_slash(self):
        """Test that trailing slash is removed from URL."""
        client = Office365groupsClient("https://example.azure.com/connections/test/")

        assert client._connection_runtime_url == "https://example.azure.com/connections/test"

    def test_init_with_custom_token_provider(self, mock_token_provider):
        """Test initialization with custom token provider."""
        client = Office365groupsClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        assert client._http_client._token_provider is mock_token_provider

    def test_init_with_custom_options(self, mock_token_provider):
        """Test initialization with custom options."""
        options = ConnectorClientOptions(timeout_seconds=60.0, max_retry_attempts=5)
        client = Office365groupsClient(
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
            Office365groupsClient("")

    def test_init_with_none_url_raises_error(self):
        """Test that None URL raises ValueError."""
        with pytest.raises(ValueError, match="connection_runtime_url cannot be None or empty"):
            Office365groupsClient(None)

    def test_connector_name_property(self, mock_token_provider):
        """Test connector_name property returns 'office365groups'."""
        client = Office365groupsClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        assert client.connector_name == "office365groups"

    def test_init_preserves_url_without_trailing_slash(self, mock_token_provider):
        """Test that URL without trailing slash is preserved."""
        client = Office365groupsClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        assert client._connection_runtime_url == "https://example.azure.com/connections/test"


class TestOffice365groupsClientLifecycle:
    """Tests for Office365groupsClient lifecycle methods."""

    @pytest.mark.asyncio
    async def test_close(self, mock_token_provider):
        """Test close method calls http_client.close."""
        client = Office365groupsClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        with patch.object(client._http_client, 'close', new_callable=AsyncMock) as mock_close:
            await client.close()
            mock_close.assert_called_once()

    @pytest.mark.asyncio
    async def test_context_manager(self, mock_token_provider):
        """Test async context manager functionality."""
        with patch.object(Office365groupsClient, 'close', new_callable=AsyncMock) as mock_close:
            async with Office365groupsClient(
                "https://example.azure.com/connections/test",
                token_provider=mock_token_provider
            ) as client:
                assert isinstance(client, Office365groupsClient)

            mock_close.assert_called_once()


class TestListGroupMembersAsync:
    """Tests for list_group_members_async method."""

    @pytest.mark.asyncio
    async def test_success(self, mock_token_provider):
        """Test successful list group members request."""
        client = Office365groupsClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(
            status=200,
            text='{"value": [{"id": "user1", "displayName": "John Doe"}]}'
        )

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ) as mock_send:
            result = await client.list_group_members_async(group_id="group-123")

            mock_send.assert_called_once()
            assert result is not None
            assert "value" in result
            assert len(result["value"]) == 1

    @pytest.mark.asyncio
    async def test_with_top_parameter(self, mock_token_provider):
        """Test list group members with top parameter."""
        client = Office365groupsClient(
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
            await client.list_group_members_async(group_id="group-123", top="10")

            call_args = mock_send.call_args
            assert "$top=10" in call_args[0][1]

    @pytest.mark.asyncio
    async def test_empty_response_returns_none(self, mock_token_provider):
        """Test that empty response returns None."""
        client = Office365groupsClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(status=200, text='')

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ):
            result = await client.list_group_members_async(group_id="group-123")
            assert result is None

    @pytest.mark.asyncio
    async def test_error_response_raises_exception(self, mock_token_provider):
        """Test that error response raises ConnectorException."""
        client = Office365groupsClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(status=404, text='{"error": "Not found"}')

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ):
            with pytest.raises(ConnectorException):
                await client.list_group_members_async(group_id="group-123")


class TestListGroupsAsync:
    """Tests for list_groups_async method."""

    @pytest.mark.asyncio
    async def test_success(self, mock_token_provider):
        """Test successful list groups request."""
        client = Office365groupsClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(
            status=200,
            text='{"value": [{"id": "group1", "displayName": "Engineering"}]}'
        )

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ) as mock_send:
            result = await client.list_groups_async()

            mock_send.assert_called_once()
            assert result is not None
            assert "value" in result

    @pytest.mark.asyncio
    async def test_with_filter_parameter(self, mock_token_provider):
        """Test list groups with filter parameter."""
        client = Office365groupsClient(
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
            await client.list_groups_async(filter="displayName eq 'Engineering'")

            call_args = mock_send.call_args
            assert "$filter=" in call_args[0][1]

    @pytest.mark.asyncio
    async def test_with_pagination_parameters(self, mock_token_provider):
        """Test list groups with top and skiptoken parameters."""
        client = Office365groupsClient(
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
            await client.list_groups_async(top="50", skiptoken="token123")

            call_args = mock_send.call_args
            path = call_args[0][1]
            assert "$top=50" in path
            assert "$skiptoken=token123" in path


class TestAddMemberToGroupAsync:
    """Tests for add_member_to_group_async method."""

    @pytest.mark.asyncio
    async def test_success(self, mock_token_provider):
        """Test successful add member to group request."""
        client = Office365groupsClient(
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
            await client.add_member_to_group_async(
                group_id="group-123",
                user_upn="user@contoso.com"
            )

            mock_send.assert_called_once()
            call_args = mock_send.call_args
            assert call_args[0][0] == "POST"
            assert "userUpn=user%40contoso.com" in call_args[0][1]


class TestRemoveMemberFromGroupAsync:
    """Tests for remove_member_from_group_async method."""

    @pytest.mark.asyncio
    async def test_success(self, mock_token_provider):
        """Test successful remove member from group request."""
        client = Office365groupsClient(
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
            await client.remove_member_from_group_async(
                group_id="group-123",
                user_upn="user@contoso.com"
            )

            mock_send.assert_called_once()
            call_args = mock_send.call_args
            assert call_args[0][0] == "DELETE"


class TestCreateCalendarEventAsync:
    """Tests for create_calendar_event_async method."""

    @pytest.mark.asyncio
    async def test_success(self, mock_token_provider):
        """Test successful create calendar event request."""
        client = Office365groupsClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(
            status=201,
            text='{"id": "event-123", "subject": "Team Meeting"}'
        )

        event_input = UpdateCalendarEventHTMLRequest(
            subject="Team Meeting",
            is_all_day=False
        )

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ) as mock_send:
            result = await client.create_calendar_event_async(
                input=event_input,
                group_id="group-123"
            )

            mock_send.assert_called_once()
            assert result is not None
            assert result["id"] == "event-123"


class TestUpdateCalendarEventAsync:
    """Tests for update_calendar_event_async method."""

    @pytest.mark.asyncio
    async def test_success(self, mock_token_provider):
        """Test successful update calendar event request."""
        client = Office365groupsClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(
            status=200,
            text='{"id": "event-123", "subject": "Updated Meeting"}'
        )

        event_input = UpdateCalendarEventHTMLRequest(
            subject="Updated Meeting"
        )

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ) as mock_send:
            result = await client.update_calendar_event_async(
                input=event_input,
                event="event-123",
                group_id="group-123"
            )

            mock_send.assert_called_once()
            call_args = mock_send.call_args
            assert call_args[0][0] == "PATCH"
            assert result is not None


class TestCalendarDeleteItemAsync:
    """Tests for calendar_delete_item_async method."""

    @pytest.mark.asyncio
    async def test_success(self, mock_token_provider):
        """Test successful delete calendar event request."""
        client = Office365groupsClient(
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
            await client.calendar_delete_item_async(
                event="event-123",
                group_id="group-123"
            )

            mock_send.assert_called_once()
            call_args = mock_send.call_args
            assert call_args[0][0] == "DELETE"


class TestListDeletedGroupsAsync:
    """Tests for list_deleted_groups_async method."""

    @pytest.mark.asyncio
    async def test_success(self, mock_token_provider):
        """Test successful list deleted groups request."""
        client = Office365groupsClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(
            status=200,
            text='{"value": [{"id": "deleted-group", "displayName": "Old Group"}]}'
        )

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ) as mock_send:
            result = await client.list_deleted_groups_async()

            mock_send.assert_called_once()
            assert result is not None
            assert "value" in result

    @pytest.mark.asyncio
    async def test_empty_response_returns_none(self, mock_token_provider):
        """Test that empty response returns None."""
        client = Office365groupsClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(status=200, text='')

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ):
            result = await client.list_deleted_groups_async()
            assert result is None


class TestRestoreDeletedGroupAsync:
    """Tests for restore_deleted_group_async method."""

    @pytest.mark.asyncio
    async def test_success(self, mock_token_provider):
        """Test successful restore deleted group request."""
        client = Office365groupsClient(
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
            await client.restore_deleted_group_async(group_id="deleted-group-123")

            mock_send.assert_called_once()
            call_args = mock_send.call_args
            assert call_args[0][0] == "POST"
            assert "deleted-group-123" in call_args[0][1]


class TestListOwnedGroupsAsync:
    """Tests for list_owned_groups_async method."""

    @pytest.mark.asyncio
    async def test_success(self, mock_token_provider):
        """Test successful list owned groups request."""
        client = Office365groupsClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(
            status=200,
            text='{"value": [{"id": "my-group", "displayName": "My Team"}]}'
        )

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ) as mock_send:
            result = await client.list_owned_groups_async()

            mock_send.assert_called_once()
            assert result is not None
            assert "value" in result


class TestHttpRequestAsync:
    """Tests for http_request_async method."""

    @pytest.mark.asyncio
    async def test_success(self, mock_token_provider):
        """Test successful HTTP request."""
        client = Office365groupsClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(
            status=200,
            text='{"result": "success"}'
        )

        request_input = b'{"method":"GET"}'

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ) as mock_send:
            result = await client.http_request_async(input=request_input)

            mock_send.assert_called_once()
            assert result is not None

    @pytest.mark.asyncio
    async def test_error_response_raises_exception(self, mock_token_provider):
        """Test that error response raises ConnectorException."""
        client = Office365groupsClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(status=400, text='{"error": "Bad request"}')

        request_input = b"{}"

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ):
            with pytest.raises(ConnectorException):
                await client.http_request_async(input=request_input)


class TestOnGroupMembershipChangeAsync:
    """Tests for OnGroupMembershipChange trigger metadata."""

    def test_registration_metadata(self):
        """Test trigger registration metadata."""
        metadata = TRIGGER_OPERATIONS["OnGroupMembershipChange"]

        assert metadata["method"] == "get"
        assert metadata["required_parameters"] == ["groupId"]
        assert metadata["callback_payload_type"] == "OnGroupMemberAddedOrRemovedResponse"


class TestOnNewEventAsync:
    """Tests for OnNewEvent trigger metadata."""

    def test_registration_metadata(self):
        """Test trigger registration metadata."""
        metadata = TRIGGER_OPERATIONS["OnNewEvent"]

        assert metadata["method"] == "get"
        assert metadata["required_parameters"] == ["groupId"]
        assert metadata["callback_payload_type"] == "OnNewEventResponse"


class TestListDeletedGroupsByOwnerAsync:
    """Tests for list_deleted_groups_by_owner_async method."""

    @pytest.mark.asyncio
    async def test_success(self, mock_token_provider):
        """Test successful list deleted groups by owner request."""
        client = Office365groupsClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(
            status=200,
            text='{"value": [{"id": "my-deleted-group"}]}'
        )

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ) as mock_send:
            result = await client.list_deleted_groups_by_owner_async()

            mock_send.assert_called_once()
            call_args = mock_send.call_args
            assert call_args[0][0] == "POST"
            assert result is not None


class TestDataclasses:
    """Tests for dataclass serialization and defaults."""

    def test_list_group_members_response_defaults(self):
        """Test ListGroupMembersResponse default values."""
        response = ListGroupMembersResponse()
        assert response.context is None
        assert response.next_link is None
        assert response.value is None

    def test_list_group_members_response_with_values(self):
        """Test ListGroupMembersResponse with values."""
        response = ListGroupMembersResponse(
            context="https://graph.microsoft.com/$metadata#groups",
            value=[{"id": "user1"}]
        )
        assert response.context == "https://graph.microsoft.com/$metadata#groups"
        assert len(response.value) == 1

    def test_on_group_member_added_or_removed_response_defaults(self):
        """Test OnGroupMemberAddedOrRemovedResponse default values."""
        response: OnGroupMemberAddedOrRemovedResponse = []
        assert response == []

    def test_list_groups_response_defaults(self):
        """Test ListGroupsResponse default values."""
        response = ListGroupsResponse()
        assert response.context is None
        assert response.next_link is None
        assert response.value is None

    def test_create_calendar_event_response_defaults(self):
        """Test CreateCalendarEventResponse default values."""
        response = CreateCalendarEventResponse()
        assert response.id is None
        assert response.subject is None
        assert response.is_all_day is None

    def test_create_calendar_event_response_with_values(self):
        """Test CreateCalendarEventResponse with values."""
        response = CreateCalendarEventResponse(
            id="event-123",
            subject="Team Meeting",
            is_all_day=False,
            importance="High"
        )
        assert response.id == "event-123"
        assert response.subject == "Team Meeting"
        assert response.is_all_day is False
        assert response.importance == "High"

    def test_on_new_event_response_defaults(self):
        """Test OnNewEventResponse default values."""
        response: OnNewEventResponse = []
        assert response == []

    def test_object_without_type_defaults(self):
        """Test ObjectWithoutType default values."""
        obj = ObjectWithoutType()
        assert obj.additional_properties == {}

    def test_list_owned_groups_response_defaults(self):
        """Test ListOwnedGroupsResponse default values."""
        response = ListOwnedGroupsResponse()
        assert response.context is None
        assert response.value is None

    def test_sensitivity_label_metadata_defaults(self):
        """Test SensitivityLabelMetadata default values."""
        metadata = SensitivityLabelMetadata()
        assert metadata.sensitivity_label_id is None
        assert metadata.name is None
        assert metadata.is_enabled is None

    def test_sensitivity_label_metadata_with_values(self):
        """Test SensitivityLabelMetadata with values."""
        metadata = SensitivityLabelMetadata(
            sensitivity_label_id="label-123",
            name="Confidential",
            display_name="Confidential",
            is_enabled=True,
            is_encrypted=True
        )
        assert metadata.sensitivity_label_id == "label-123"
        assert metadata.name == "Confidential"
        assert metadata.is_enabled is True

    def test_list_owned_groups_response_versioned_defaults(self):
        """Test consolidated ListOwnedGroupsResponse default values."""
        response = ListOwnedGroupsResponse()
        assert response.context is None
        assert response.value is None

    def test_update_calendar_event_request_defaults(self):
        """Test UpdateCalendarEventRequest default values."""
        request = UpdateCalendarEventRequest()
        assert request.subject is None
        assert request.is_all_day is None

    def test_update_calendar_event_request_with_values(self):
        """Test UpdateCalendarEventRequest with values."""
        request = UpdateCalendarEventRequest(
            subject="Team Standup",
            importance="Normal",
            is_all_day=False,
            is_reminder_on=True,
            reminder_minutes_before_start=15
        )
        assert request.subject == "Team Standup"
        assert request.is_reminder_on is True
        assert request.reminder_minutes_before_start == 15

    def test_update_calendar_event_html_request_defaults(self):
        """Test UpdateCalendarEventHTMLRequest default values."""
        request = UpdateCalendarEventHTMLRequest()
        assert request.subject is None
        assert request.body is None

    def test_update_calendar_event_html_request_with_values(self):
        """Test UpdateCalendarEventHTMLRequest with values."""
        request = UpdateCalendarEventHTMLRequest(
            subject="HTML Meeting",
            body={"contentType": "HTML", "content": "<p>Meeting details</p>"},
            is_all_day=True
        )
        assert request.subject == "HTML Meeting"
        assert request.body["contentType"] == "HTML"
        assert request.is_all_day is True
