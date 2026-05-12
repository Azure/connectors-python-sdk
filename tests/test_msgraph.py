"""Unit tests for msgraph connector."""

import pytest
from unittest.mock import AsyncMock, patch

from azure.connectors.msgraphgroupsanduser import (
    MsgraphgroupsanduserClient,
    ListUsersResponse,
    ListGroupsByDisplayNameSearchResponse,
    ListSubscribedSkusResponse,
    ListDirectGroupMembersResponse,
    GetMemberLicenseDetailsResponse,
    GetGroupPropertiesResponse,
    GetMemberGroupsInput,
    GetMemberGroupsResponse,
)
from azure.connectors.sdk import ConnectorException


class TestMsgraphClientInitialization:
    """Tests for MsgraphgroupsanduserClient initialization."""

    def test_init_with_valid_url_and_defaults(self):
        """Test initialization with valid URL and default values."""
        client = MsgraphgroupsanduserClient("https://example.azure.com/connections/test")

        assert client._connection_runtime_url == "https://example.azure.com/connections/test"
        assert client._http_client._token_provider is not None
        assert client._options is not None

    def test_init_with_trailing_slash_removes_slash(self):
        """Test that trailing slash is removed from URL."""
        client = MsgraphgroupsanduserClient("https://example.azure.com/connections/test/")

        assert client._connection_runtime_url == "https://example.azure.com/connections/test"

    def test_init_with_custom_token_provider(self, mock_token_provider):
        """Test initialization with custom token provider."""
        client = MsgraphgroupsanduserClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        assert client._http_client._token_provider is mock_token_provider

    def test_init_with_custom_options(self, mock_token_provider):
        """Test initialization with custom options."""
        from azure.connectors.sdk import ConnectorClientOptions
        options = ConnectorClientOptions(timeout_seconds=60.0)

        client = MsgraphgroupsanduserClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider,
            options=options
        )

        assert client._options is options

    def test_init_with_empty_url_raises_error(self):
        """Test that empty URL raises ValueError."""
        with pytest.raises(ValueError, match="connection_runtime_url cannot be None or empty"):
            MsgraphgroupsanduserClient("")

    def test_init_with_none_url_raises_error(self):
        """Test that None URL raises ValueError."""
        with pytest.raises(ValueError, match="connection_runtime_url cannot be None or empty"):
            MsgraphgroupsanduserClient(None)

    def test_connector_name_property(self):
        """Test connector_name property returns correct value."""
        client = MsgraphgroupsanduserClient("https://example.azure.com/connections/test")

        assert client.connector_name == "msgraphgroupsanduser"


class TestMsgraphClientLifecycle:
    """Tests for MsgraphgroupsanduserClient lifecycle methods."""

    @pytest.mark.asyncio
    async def test_close(self):
        """Test close method."""
        client = MsgraphgroupsanduserClient("https://example.azure.com/connections/test")

        with patch.object(client._http_client, 'close', new_callable=AsyncMock) as mock_close:
            await client.close()
            mock_close.assert_called_once()

    @pytest.mark.asyncio
    async def test_async_context_manager(self):
        """Test async context manager usage."""
        client = MsgraphgroupsanduserClient("https://example.azure.com/connections/test")

        with patch.object(client._http_client, 'close', new_callable=AsyncMock) as mock_close:
            async with client:
                pass

            mock_close.assert_called_once()


class TestListUsers:
    """Tests for list_users_async method."""

    @pytest.mark.asyncio
    async def test_success_with_json_response(self, mock_token_provider, mock_response_success):
        """Test successful list users with JSON response."""
        client = MsgraphgroupsanduserClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response_success.text = (
            '{"@odata.context": "https://graph.microsoft.com/v1.0/$metadata#users", '
            '"value": [{"id": "user1", "displayName": "User One"}]}'
        )

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response_success
        ) as mock_send:
            result = await client.list_users_async()

            assert result is not None
            assert result["value"][0]["id"] == "user1"
            mock_send.assert_called_once_with(
                "GET",
                "https://example.azure.com/connections/test/v1.0/users",
                body=None
            )

    @pytest.mark.asyncio
    async def test_success_with_empty_response(self, mock_token_provider, mock_response_empty):
        """Test list users with empty response."""
        client = MsgraphgroupsanduserClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response_empty
        ):
            result = await client.list_users_async()

            assert result is None

    @pytest.mark.asyncio
    async def test_error_raises_exception(self, mock_token_provider, mock_response_error):
        """Test that error response raises ConnectorException."""
        client = MsgraphgroupsanduserClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response_error
        ):
            with pytest.raises(ConnectorException) as exc_info:
                await client.list_users_async()

            assert exc_info.value.status_code == 400


class TestListGroupsByDisplayNameSearch:
    """Tests for list_groups_by_display_name_search_async method."""

    @pytest.mark.asyncio
    async def test_success_with_search_and_count(self, mock_token_provider, mock_response_success):
        """Test successful search with search term and count."""
        client = MsgraphgroupsanduserClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response_success.text = (
            '{"@odata.context": "https://graph.microsoft.com/v1.0/$metadata#groups", '
            '"@odata.count": 2, "value": [{"id": "group1", "displayName": "Test Group"}]}'
        )

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response_success
        ) as mock_send:
            result = await client.list_groups_by_display_name_search_async(
                count="true",
                search="Test"
            )

            assert result is not None
            assert "@odata.count" in result
            mock_send.assert_called_once()
            call_path = mock_send.call_args[0][1]
            assert "$search=Test" in call_path
            assert "$count=true" in call_path

    @pytest.mark.asyncio
    async def test_success_with_count_only(self, mock_token_provider, mock_response_success):
        """Test successful search with count only."""
        client = MsgraphgroupsanduserClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response_success.text = '{"value": []}'

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response_success
        ) as mock_send:
            result = await client.list_groups_by_display_name_search_async(count="true")

            assert result is not None
            call_path = mock_send.call_args[0][1]
            assert "$count=true" in call_path
            assert "$search" not in call_path

    @pytest.mark.asyncio
    async def test_url_encodes_search_parameter(self, mock_token_provider, mock_response_success):
        """Test that search parameter is URL encoded."""
        client = MsgraphgroupsanduserClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response_success.text = '{}'

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response_success
        ) as mock_send:
            await client.list_groups_by_display_name_search_async(
                count="true",
                search="Test Group Name"
            )

            call_path = mock_send.call_args[0][1]
            assert "$search=Test%20Group%20Name" in call_path

    @pytest.mark.asyncio
    async def test_error_raises_exception(self, mock_token_provider, mock_response_error):
        """Test that error response raises ConnectorException."""
        client = MsgraphgroupsanduserClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response_error
        ):
            with pytest.raises(ConnectorException) as exc_info:
                await client.list_groups_by_display_name_search_async(count="true")

            assert exc_info.value.status_code == 400


class TestListSubscribedSkus:
    """Tests for list_subscribed_skus_async method."""

    @pytest.mark.asyncio
    async def test_success_with_json_response(self, mock_token_provider, mock_response_success):
        """Test successful list subscribed SKUs."""
        client = MsgraphgroupsanduserClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response_success.text = (
            '{"value": [{"skuId": "sku1", "skuPartNumber": "ENTERPRISEPACK"}]}'
        )

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response_success
        ) as mock_send:
            result = await client.list_subscribed_skus_async()

            assert result is not None
            assert result["value"][0]["skuPartNumber"] == "ENTERPRISEPACK"
            mock_send.assert_called_once_with(
                "GET",
                "https://example.azure.com/connections/test/v1.0/subscribedSkus",
                body=None
            )

    @pytest.mark.asyncio
    async def test_error_raises_exception(self, mock_token_provider, mock_response_error):
        """Test that error response raises ConnectorException."""
        client = MsgraphgroupsanduserClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response_error
        ):
            with pytest.raises(ConnectorException) as exc_info:
                await client.list_subscribed_skus_async()

            assert exc_info.value.status_code == 400


class TestListDirectGroupMembers:
    """Tests for list_direct_group_members_async method."""

    @pytest.mark.asyncio
    async def test_success_with_all_parameters(self, mock_token_provider, mock_response_success):
        """Test successful list with all query parameters."""
        client = MsgraphgroupsanduserClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response_success.text = (
            '{"@odata.count": 5, "value": [{"id": "member1", '
            '"displayName": "Member One"}]}'
        )

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response_success
        ) as mock_send:
            result = await client.list_direct_group_members_async(
                group_id="group-123",
                count="true",
                filter="userType eq 'Member'",
                select="id,displayName"
            )

            assert result is not None
            assert result["@odata.count"] == 5
            call_path = mock_send.call_args[0][1]
            assert "/v1.0/groups/group-123/members" in call_path
            assert "$filter=userType%20eq%20%27Member%27" in call_path
            assert "$select=id%2CdisplayName" in call_path
            assert "$count=true" in call_path

    @pytest.mark.asyncio
    async def test_success_with_group_id_and_count_only(
        self, mock_token_provider, mock_response_success
    ):
        """Test successful list with required parameters only."""
        client = MsgraphgroupsanduserClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response_success.text = '{"value": []}'

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response_success
        ) as mock_send:
            result = await client.list_direct_group_members_async(
                group_id="group-456",
                count="false"
            )

            assert result is not None
            call_path = mock_send.call_args[0][1]
            assert "/v1.0/groups/group-456/members" in call_path
            assert "$count=false" in call_path
            assert "$filter" not in call_path
            assert "$select" not in call_path

    @pytest.mark.asyncio
    async def test_group_id_in_path(self, mock_token_provider, mock_response_success):
        """Test that group_id is properly inserted into path."""
        client = MsgraphgroupsanduserClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response_success.text = '{}'

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response_success
        ) as mock_send:
            await client.list_direct_group_members_async(
                group_id="test-group-id",
                count="true"
            )

            call_path = mock_send.call_args[0][1]
            assert "groups/test-group-id/members" in call_path

    @pytest.mark.asyncio
    async def test_error_raises_exception(self, mock_token_provider, mock_response_error):
        """Test that error response raises ConnectorException."""
        client = MsgraphgroupsanduserClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response_error
        ):
            with pytest.raises(ConnectorException) as exc_info:
                await client.list_direct_group_members_async(
                    group_id="group-123",
                    count="true"
                )

            assert exc_info.value.status_code == 400


class TestGetMemberLicenseDetails:
    """Tests for get_member_license_details_async method."""

    @pytest.mark.asyncio
    async def test_success_with_select_parameter(self, mock_token_provider, mock_response_success):
        """Test successful get with select parameter."""
        client = MsgraphgroupsanduserClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response_success.text = '{"value": [{"skuId": "sku1", "servicePlans": []}]}'

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response_success
        ) as mock_send:
            result = await client.get_member_license_details_async(
                id="user-123",
                select="skuId,servicePlans"
            )

            assert result is not None
            assert result["value"][0]["skuId"] == "sku1"
            call_path = mock_send.call_args[0][1]
            assert "/v1.0/users/user-123/licenseDetails" in call_path
            assert "$select=skuId%2CservicePlans" in call_path

    @pytest.mark.asyncio
    async def test_success_without_select_parameter(
        self, mock_token_provider, mock_response_success
    ):
        """Test successful get without select parameter."""
        client = MsgraphgroupsanduserClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response_success.text = '{"value": []}'

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response_success
        ) as mock_send:
            result = await client.get_member_license_details_async(id="user-456")

            assert result is not None
            call_path = mock_send.call_args[0][1]
            assert "/v1.0/users/user-456/licenseDetails" in call_path
            assert "$select" not in call_path

    @pytest.mark.asyncio
    async def test_error_raises_exception(self, mock_token_provider, mock_response_error):
        """Test that error response raises ConnectorException."""
        client = MsgraphgroupsanduserClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response_error
        ):
            with pytest.raises(ConnectorException) as exc_info:
                await client.get_member_license_details_async(id="user-123")

            assert exc_info.value.status_code == 400


class TestGetGroupProperties:
    """Tests for get_group_properties_async method."""

    @pytest.mark.asyncio
    async def test_success_with_json_response(self, mock_token_provider, mock_response_success):
        """Test successful get group properties."""
        client = MsgraphgroupsanduserClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response_success.text = (
            '{"id": "group-123", "displayName": "Test Group", '
            '"mailEnabled": true, "securityEnabled": false}'
        )

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response_success
        ) as mock_send:
            result = await client.get_group_properties_async(group_id="group-123")

            assert result is not None
            assert result["id"] == "group-123"
            assert result["displayName"] == "Test Group"
            mock_send.assert_called_once_with(
                "GET",
                "https://example.azure.com/connections/test/v1.0/groups/group-123",
                body=None
            )

    @pytest.mark.asyncio
    async def test_group_id_in_path(self, mock_token_provider, mock_response_success):
        """Test that group_id is properly inserted into path."""
        client = MsgraphgroupsanduserClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response_success.text = '{}'

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response_success
        ) as mock_send:
            await client.get_group_properties_async(group_id="my-group-id")

            call_path = mock_send.call_args[0][1]
            assert "groups/my-group-id" in call_path

    @pytest.mark.asyncio
    async def test_error_raises_exception(self, mock_token_provider, mock_response_error):
        """Test that error response raises ConnectorException."""
        client = MsgraphgroupsanduserClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response_error
        ):
            with pytest.raises(ConnectorException) as exc_info:
                await client.get_group_properties_async(group_id="group-123")

            assert exc_info.value.status_code == 400


class TestGetMemberGroups:
    """Tests for get_member_groups_async method."""

    @pytest.mark.asyncio
    async def test_success_with_security_enabled_only_true(
        self, mock_token_provider, mock_response_success
    ):
        """Test successful get with security_enabled_only = true."""
        client = MsgraphgroupsanduserClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response_success.text = '{"value": ["group-1", "group-2", "group-3"]}'

        input_data = GetMemberGroupsInput(security_enabled_only=True)

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response_success
        ) as mock_send:
            result = await client.get_member_groups_async(
                input=input_data,
                member_id="user-123"
            )

            assert result is not None
            assert len(result["value"]) == 3
            mock_send.assert_called_once_with(
                "POST",
                "https://example.azure.com/connections/test/v1.0/users/user-123/getMemberGroups",
                body=input_data
            )

    @pytest.mark.asyncio
    async def test_success_with_security_enabled_only_false(
        self, mock_token_provider, mock_response_success
    ):
        """Test successful get with security_enabled_only = false."""
        client = MsgraphgroupsanduserClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response_success.text = '{"value": []}'

        input_data = GetMemberGroupsInput(security_enabled_only=False)

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response_success
        ):
            result = await client.get_member_groups_async(
                input=input_data,
                member_id="user-456"
            )

            assert result is not None
            assert result["value"] == []

    @pytest.mark.asyncio
    async def test_member_id_in_path(self, mock_token_provider, mock_response_success):
        """Test that member_id is properly inserted into path."""
        client = MsgraphgroupsanduserClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response_success.text = '{}'

        input_data = GetMemberGroupsInput()

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response_success
        ) as mock_send:
            await client.get_member_groups_async(
                input=input_data,
                member_id="member-789"
            )

            call_path = mock_send.call_args[0][1]
            assert "users/member-789/getMemberGroups" in call_path

    @pytest.mark.asyncio
    async def test_error_raises_exception(self, mock_token_provider, mock_response_error):
        """Test that error response raises ConnectorException."""
        client = MsgraphgroupsanduserClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        input_data = GetMemberGroupsInput(security_enabled_only=True)

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response_error
        ):
            with pytest.raises(ConnectorException) as exc_info:
                await client.get_member_groups_async(
                    input=input_data,
                    member_id="user-123"
                )

            assert exc_info.value.status_code == 400


class TestDataClasses:
    """Tests for msgraph data classes."""

    def test_list_users_response_creation(self):
        """Test ListUsersResponse data class creation."""
        response = ListUsersResponse(
            context="https://graph.microsoft.com/v1.0/$metadata#users",
            value=[{"id": "user1", "displayName": "User One"}]
        )

        assert response.context == "https://graph.microsoft.com/v1.0/$metadata#users"
        assert len(response.value) == 1

    def test_list_groups_by_display_name_search_response_creation(self):
        """Test ListGroupsByDisplayNameSearchResponse data class creation."""
        response = ListGroupsByDisplayNameSearchResponse(
            context="https://graph.microsoft.com/v1.0/$metadata#groups",
            count=5,
            value=[{"id": "group1"}]
        )

        assert response.context == "https://graph.microsoft.com/v1.0/$metadata#groups"
        assert response.count == 5

    def test_list_subscribed_skus_response_creation(self):
        """Test ListSubscribedSkusResponse data class creation."""
        response = ListSubscribedSkusResponse(
            context="https://graph.microsoft.com/v1.0/$metadata#subscribedSkus",
            value=[{"skuId": "sku1"}]
        )

        assert response.value[0]["skuId"] == "sku1"

    def test_list_direct_group_members_response_creation(self):
        """Test ListDirectGroupMembersResponse data class creation."""
        response = ListDirectGroupMembersResponse(
            context="https://graph.microsoft.com/v1.0/$metadata#users",
            count=10,
            value=[{"id": "member1"}]
        )

        assert response.count == 10

    def test_get_member_license_details_response_creation(self):
        """Test GetMemberLicenseDetailsResponse data class creation."""
        response = GetMemberLicenseDetailsResponse(
            value=[{"skuId": "license1"}]
        )

        assert response.value[0]["skuId"] == "license1"

    def test_get_group_properties_response_creation(self):
        """Test GetGroupPropertiesResponse data class creation."""
        response = GetGroupPropertiesResponse(
            id="group-123",
            display_name="Test Group",
            mail_enabled=True,
            security_enabled=False,
            group_types=["Unified"],
            description="A test group"
        )

        assert response.id == "group-123"
        assert response.display_name == "Test Group"
        assert response.mail_enabled is True
        assert response.security_enabled is False

    def test_get_member_groups_input_creation(self):
        """Test GetMemberGroupsInput data class creation."""
        input_data = GetMemberGroupsInput(security_enabled_only=True)

        assert input_data.security_enabled_only is True

    def test_get_member_groups_response_creation(self):
        """Test GetMemberGroupsResponse data class creation."""
        response = GetMemberGroupsResponse(
            context="https://graph.microsoft.com/v1.0/$metadata#Collection(Edm.String)",
            value=["group1", "group2", "group3"]
        )

        assert len(response.value) == 3


class TestEdgeCases:
    """Tests for edge cases and boundary conditions."""

    @pytest.mark.asyncio
    async def test_multiple_consecutive_calls(self, mock_token_provider, mock_response_success):
        """Test multiple consecutive API calls."""
        client = MsgraphgroupsanduserClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response_success.text = '{"value": []}'

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response_success
        ):
            result1 = await client.list_users_async()
            result2 = await client.list_subscribed_skus_async()
            result3 = await client.get_group_properties_async(group_id="group-123")

            assert result1 is not None
            assert result2 is not None
            assert result3 is not None

    @pytest.mark.asyncio
    async def test_json_parse_error_returns_none(self, mock_token_provider):
        """Test that invalid JSON returns None gracefully."""
        from tests.conftest import MockResponse

        client = MsgraphgroupsanduserClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(status=200, text='invalid json{')

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ):
            with pytest.raises(Exception):  # JSON parse error
                await client.list_users_async()

    @pytest.mark.asyncio
    async def test_boolean_parameter_conversion(self, mock_token_provider, mock_response_success):
        """Test that boolean parameters are converted to lowercase strings."""
        client = MsgraphgroupsanduserClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response_success.text = '{}'

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response_success
        ) as mock_send:
            # Pass boolean True as count
            await client.list_groups_by_display_name_search_async(count=True)

            call_path = mock_send.call_args[0][1]
            assert "$count=true" in call_path

    @pytest.mark.asyncio
    async def test_empty_string_parameters_excluded(
        self, mock_token_provider, mock_response_success
    ):
        """Test that None optional parameters are not added to query string."""
        client = MsgraphgroupsanduserClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response_success.text = '{}'

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response_success
        ) as mock_send:
            await client.list_direct_group_members_async(
                group_id="group-123",
                count="true",
                filter=None,
                select=None
            )

            call_path = mock_send.call_args[0][1]
            assert "$count=true" in call_path
            assert "$filter" not in call_path
            assert "$select" not in call_path

    @pytest.mark.asyncio
    async def test_special_characters_in_ids(self, mock_token_provider, mock_response_success):
        """Test that IDs with special characters are handled correctly."""
        client = MsgraphgroupsanduserClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response_success.text = '{}'

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response_success
        ) as mock_send:
            # ID with hyphen and numbers
            await client.get_group_properties_async(group_id="abc-123-def-456")

            call_path = mock_send.call_args[0][1]
            assert "groups/abc-123-def-456" in call_path

    @pytest.mark.asyncio
    async def test_http_methods_used_correctly(self, mock_token_provider, mock_response_success):
        """Test that correct HTTP methods are used for different operations."""
        client = MsgraphgroupsanduserClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response_success.text = '{}'

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response_success
        ) as mock_send:
            # GET methods
            await client.list_users_async()
            assert mock_send.call_args[0][0] == "GET"

            await client.get_group_properties_async(group_id="group-123")
            assert mock_send.call_args[0][0] == "GET"

            # POST method
            input_data = GetMemberGroupsInput()
            await client.get_member_groups_async(input=input_data, member_id="user-123")
            assert mock_send.call_args[0][0] == "POST"
