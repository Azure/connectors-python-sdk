# Copyright (c) Microsoft Corporation. All rights reserved.

"""Unit tests for AzureadClient."""

import pytest
from unittest.mock import AsyncMock, patch
from azure.connectors.azuread import (
    AzureadClient,
    CreateOffice365GroupInput,
    CreateSecurityGroupInput,
    CreateUserRequest,
    CreateGroupInput,
    CreateGroupResponse,
    GetGroupResponse,
    GetUserResponse,
    GetGroupMembersResponse,
)
from azure.connectors.sdk import (
    ConnectorClientOptions,
    ManagedIdentityTokenProvider,
    ConnectorException,
)
from tests.conftest import MockResponse


class TestAzureadClientInitialization:
    """Tests for AzureadClient initialization."""

    def test_init_with_valid_url_and_defaults(self):
        """Test initialization with valid URL and default parameters."""
        client = AzureadClient("https://example.azure.com/connections/test")

        assert client._connection_runtime_url == "https://example.azure.com/connections/test"
        assert client.connector_name == "azuread"
        assert isinstance(client._http_client._token_provider, ManagedIdentityTokenProvider)

    def test_init_with_trailing_slash(self):
        """Test that trailing slash is removed from URL."""
        client = AzureadClient("https://example.azure.com/connections/test/")

        assert client._connection_runtime_url == "https://example.azure.com/connections/test"

    def test_init_with_custom_token_provider(self, mock_token_provider):
        """Test initialization with custom token provider."""
        client = AzureadClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        assert client._http_client._token_provider is mock_token_provider

    def test_init_with_custom_options(self, mock_token_provider):
        """Test initialization with custom options."""
        options = ConnectorClientOptions(timeout_seconds=60.0, max_retry_attempts=5)
        client = AzureadClient(
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
            AzureadClient("")

    def test_init_with_none_url_raises_error(self):
        """Test that None URL raises ValueError."""
        with pytest.raises(ValueError, match="connection_runtime_url cannot be None or empty"):
            AzureadClient(None)

    def test_connector_name_property(self, mock_token_provider):
        """Test connector_name property returns 'azuread'."""
        client = AzureadClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        assert client.connector_name == "azuread"


class TestAzureadClientLifecycle:
    """Tests for AzureadClient lifecycle methods."""

    @pytest.mark.asyncio
    async def test_close(self, mock_token_provider):
        """Test close method calls http_client.close."""
        client = AzureadClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        with patch.object(client._http_client, 'close', new_callable=AsyncMock) as mock_close:
            await client.close()
            mock_close.assert_called_once()

    @pytest.mark.asyncio
    async def test_context_manager(self, mock_token_provider):
        """Test async context manager functionality."""
        with patch.object(AzureadClient, 'close', new_callable=AsyncMock) as mock_close:
            async with AzureadClient(
                "https://example.azure.com/connections/test",
                token_provider=mock_token_provider
            ) as client:
                assert isinstance(client, AzureadClient)

            mock_close.assert_called_once()


class TestCreateOffice365Group:
    """Tests for create_office365_group_async method."""

    @pytest.mark.asyncio
    async def test_success_with_json_response(self, mock_token_provider):
        """Test successful POST request."""
        client = AzureadClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(
            status=201,
            text='{"id": "group123", "displayName": "Engineering Team", "mailEnabled": true}'
        )
        group_input = CreateOffice365GroupInput(
            display_name="Engineering Team",
            description="Engineering department group",
            mail_nickname="engineering",
            group_types=["Unified"],
            security_enabled=False,
            mail_enabled=True
        )

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ) as mock_send:
            result = await client.create_office365_group_async(input=group_input)

            mock_send.assert_called_once()
            call_args = mock_send.call_args
            assert call_args[0][0] == "POST"
            assert "/v1.0/groups/office365" in call_args[0][1]
            assert result["id"] == "group123"
            assert result["displayName"] == "Engineering Team"

    @pytest.mark.asyncio
    async def test_empty_response_returns_none(self, mock_token_provider):
        """Test that empty response returns None."""
        client = AzureadClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(status=201, text="")
        group_input = CreateOffice365GroupInput(display_name="Test Group")

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ):
            result = await client.create_office365_group_async(input=group_input)
            assert result is None

    @pytest.mark.asyncio
    async def test_error_response_raises_exception(self, mock_token_provider):
        """Test that error response raises ConnectorException."""
        client = AzureadClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(status=400, text='{"error": "Invalid group configuration"}')
        group_input = CreateOffice365GroupInput(display_name="")

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ):
            with pytest.raises(ConnectorException) as exc_info:
                await client.create_office365_group_async(input=group_input)

            assert exc_info.value.status_code == 400


class TestCreateSecurityGroup:
    """Tests for create_security_group_async method."""

    @pytest.mark.asyncio
    async def test_success_with_json_response(self, mock_token_provider):
        """Test successful POST request."""
        client = AzureadClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(
            status=201,
            text='{"id": "sec-group456", "displayName": "Security Admins", "securityEnabled": true}'
        )
        group_input = CreateSecurityGroupInput(
            display_name="Security Admins",
            description="Security administrators group",
            mail_nickname="secadmins",
            security_enabled=True,
            mail_enabled=False
        )

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ) as mock_send:
            result = await client.create_security_group_async(input=group_input)

            mock_send.assert_called_once()
            call_args = mock_send.call_args
            assert call_args[0][0] == "POST"
            assert "/v1.0/groups/securityGroup" in call_args[0][1]
            assert result["id"] == "sec-group456"
            assert result["securityEnabled"] is True

    @pytest.mark.asyncio
    async def test_error_response_raises_exception(self, mock_token_provider):
        """Test that error response raises ConnectorException."""
        client = AzureadClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(status=403, text='{"error": "Insufficient permissions"}')
        group_input = CreateSecurityGroupInput(display_name="Test Security Group")

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ):
            with pytest.raises(ConnectorException) as exc_info:
                await client.create_security_group_async(input=group_input)

            assert exc_info.value.status_code == 403

    @pytest.mark.asyncio
    async def test_empty_response_returns_none(self, mock_token_provider):
        """Test that empty response returns None."""
        client = AzureadClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(status=201, text="")
        group_input = CreateSecurityGroupInput(display_name="Empty Response Group")

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ):
            result = await client.create_security_group_async(input=group_input)
            assert result is None


class TestCreateUser:
    """Tests for create_user_async method."""

    @pytest.mark.asyncio
    async def test_success_with_json_response(self, mock_token_provider):
        """Test successful POST request."""
        client = AzureadClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(
            status=201,
            text=(
                '{"id": "user789", "displayName": "John Doe", '
                '"userPrincipalName": "john.doe@contoso.com"}'
            )
        )
        user_input = CreateUserRequest(
            account_enabled=True,
            display_name="John Doe",
            mail_nickname="johndoe",
            user_principal_name="john.doe@contoso.com",
            given_name="John",
            surname="Doe",
            password_profile={"password": "SecurePass123!", "forceChangePasswordNextSignIn": True}
        )

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ) as mock_send:
            result = await client.create_user_async(input=user_input)

            mock_send.assert_called_once()
            call_args = mock_send.call_args
            assert call_args[0][0] == "POST"
            assert "/v1.0/users" in call_args[0][1]
            assert result["id"] == "user789"
            assert result["displayName"] == "John Doe"

    @pytest.mark.asyncio
    async def test_with_all_optional_fields(self, mock_token_provider):
        """Test with all optional fields populated."""
        client = AzureadClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(status=201, text='{"id": "user-full"}')
        user_input = CreateUserRequest(
            account_enabled=True,
            display_name="Jane Smith",
            mail_nickname="janesmith",
            user_principal_name="jane.smith@contoso.com",
            given_name="Jane",
            surname="Smith",
            business_phones=["+1-555-123-4567"],
            department="Engineering",
            job_title="Senior Developer",
            mobile_phone="+1-555-987-6543",
            office_location="Building A, Room 101",
            preferred_language="en-US"
        )

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ):
            result = await client.create_user_async(input=user_input)
            assert result["id"] == "user-full"

    @pytest.mark.asyncio
    async def test_error_response_raises_exception(self, mock_token_provider):
        """Test that error response raises ConnectorException."""
        client = AzureadClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(status=409, text='{"error": "User already exists"}')
        user_input = CreateUserRequest(
            display_name="Existing User",
            user_principal_name="existing@contoso.com"
        )

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ):
            with pytest.raises(ConnectorException) as exc_info:
                await client.create_user_async(input=user_input)

            assert exc_info.value.status_code == 409

    @pytest.mark.asyncio
    async def test_empty_response_returns_none(self, mock_token_provider):
        """Test that empty response returns None."""
        client = AzureadClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(status=201, text="")
        user_input = CreateUserRequest(display_name="Empty Response User")

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ):
            result = await client.create_user_async(input=user_input)
            assert result is None


class TestRemoveMemberFromGroup:
    """Tests for remove_member_from_group_async method."""

    @pytest.mark.asyncio
    async def test_success(self, mock_token_provider):
        """Test successful DELETE request."""
        client = AzureadClient(
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
            await client.remove_member_from_group_async(
                group_id="group-abc123",
                member_id="user-xyz789"
            )

            mock_send.assert_called_once()
            call_args = mock_send.call_args
            assert call_args[0][0] == "DELETE"
            assert "/v1.0/groups/group-abc123/members/user-xyz789/$ref" in call_args[0][1]

    @pytest.mark.asyncio
    async def test_with_different_ids(self, mock_token_provider):
        """Test with different group and member IDs."""
        client = AzureadClient(
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
            await client.remove_member_from_group_async(
                group_id="5e6cf5c7-b511-4842-6aae-3f6b8ae5e95b",
                member_id="8a9bf2d1-c322-5933-7bbf-4g7c9bf6f06c"
            )

            call_args = mock_send.call_args
            assert "5e6cf5c7-b511-4842-6aae-3f6b8ae5e95b" in call_args[0][1]
            assert "8a9bf2d1-c322-5933-7bbf-4g7c9bf6f06c" in call_args[0][1]


class TestCreateGroup:
    """Tests for create_group_async method."""

    @pytest.mark.asyncio
    async def test_success_with_json_response(self, mock_token_provider):
        """Test successful POST request."""
        client = AzureadClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(
            status=201,
            text='{"id": "generic-group123", "displayName": "Generic Group", "mailEnabled": false}'
        )
        group_input = CreateGroupInput(
            display_name="Generic Group",
            description="A generic group",
            mail_nickname="genericgroup",
            group_types=["Unified"],
            security_enabled=True,
            mail_enabled=False
        )

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ) as mock_send:
            result = await client.create_group_async(input=group_input)

            mock_send.assert_called_once()
            call_args = mock_send.call_args
            assert call_args[0][0] == "POST"
            assert "/v1.0/groups" in call_args[0][1]
            assert "office365" not in call_args[0][1]
            assert "securityGroup" not in call_args[0][1]
            assert result["id"] == "generic-group123"

    @pytest.mark.asyncio
    async def test_error_response_raises_exception(self, mock_token_provider):
        """Test that error response raises ConnectorException."""
        client = AzureadClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(status=400, text='{"error": "Invalid request"}')
        group_input = CreateGroupInput(display_name="")

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ):
            with pytest.raises(ConnectorException) as exc_info:
                await client.create_group_async(input=group_input)

            assert exc_info.value.status_code == 400

    @pytest.mark.asyncio
    async def test_empty_response_returns_none(self, mock_token_provider):
        """Test that empty response returns None."""
        client = AzureadClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(status=201, text="")
        group_input = CreateGroupInput(display_name="Empty Response Group")

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ):
            result = await client.create_group_async(input=group_input)
            assert result is None


class TestDataClasses:
    """Tests for data class creation and attributes."""

    def test_create_office365_group_input_creation(self):
        """Test CreateOffice365GroupInput dataclass creation."""
        group_input = CreateOffice365GroupInput(
            display_name="Test O365 Group",
            description="Test description",
            mail_nickname="testo365",
            group_types=["Unified"],
            security_enabled=False,
            mail_enabled=True
        )

        assert group_input.display_name == "Test O365 Group"
        assert group_input.description == "Test description"
        assert group_input.mail_nickname == "testo365"
        assert group_input.group_types == ["Unified"]
        assert group_input.security_enabled is False
        assert group_input.mail_enabled is True

    def test_create_security_group_input_creation(self):
        """Test CreateSecurityGroupInput dataclass creation."""
        group_input = CreateSecurityGroupInput(
            display_name="Security Group",
            description="Security group description",
            mail_nickname="secgroup",
            security_enabled=True,
            mail_enabled=False
        )

        assert group_input.display_name == "Security Group"
        assert group_input.security_enabled is True
        assert group_input.mail_enabled is False

    def test_create_user_request_creation(self):
        """Test CreateUserRequest dataclass creation."""
        user_request = CreateUserRequest(
            account_enabled=True,
            display_name="Test User",
            mail_nickname="testuser",
            user_principal_name="test@contoso.com",
            given_name="Test",
            surname="User",
            department="IT",
            job_title="Developer"
        )

        assert user_request.account_enabled is True
        assert user_request.display_name == "Test User"
        assert user_request.user_principal_name == "test@contoso.com"
        assert user_request.department == "IT"

    def test_create_group_response_creation(self):
        """Test CreateGroupResponse dataclass creation."""
        response = CreateGroupResponse(
            id="group-id-123",
            display_name="Created Group",
            mail_enabled=True,
            security_enabled=False,
            visibility="Public"
        )

        assert response.id == "group-id-123"
        assert response.display_name == "Created Group"
        assert response.visibility == "Public"

    def test_get_group_response_creation(self):
        """Test GetGroupResponse dataclass creation."""
        response = GetGroupResponse(
            id="group-456",
            display_name="Retrieved Group",
            mail="group@contoso.com",
            mail_enabled=True,
            security_enabled=False,
            visibility="Private"
        )

        assert response.id == "group-456"
        assert response.mail == "group@contoso.com"
        assert response.visibility == "Private"

    def test_get_user_response_creation(self):
        """Test GetUserResponse dataclass creation."""
        response = GetUserResponse(
            id="user-abc",
            display_name="John Doe",
            given_name="John",
            surname="Doe",
            mail="john.doe@contoso.com",
            job_title="Engineer",
            mobile_phone="+1-555-123-4567",
            office_location="Building A",
            preferred_language="en-US",
            user_principal_name="john.doe@contoso.com"
        )

        assert response.id == "user-abc"
        assert response.given_name == "John"
        assert response.surname == "Doe"
        assert response.job_title == "Engineer"

    def test_get_group_members_response_creation(self):
        """Test GetGroupMembersResponse dataclass creation."""
        user1 = GetUserResponse(id="user1", display_name="User One")
        user2 = GetUserResponse(id="user2", display_name="User Two")

        response = GetGroupMembersResponse(
            next_link="https://graph.microsoft.com/v1.0/groups/123/members?$skiptoken=abc",
            value=[user1, user2]
        )

        assert response.next_link is not None
        assert len(response.value) == 2
        assert response.value[0].display_name == "User One"

    def test_create_group_input_creation(self):
        """Test CreateGroupInput dataclass creation."""
        group_input = CreateGroupInput(
            display_name="Generic Group",
            description="Generic description",
            mail_nickname="generic",
            group_types=["Unified"],
            security_enabled=True,
            mail_enabled=True
        )

        assert group_input.display_name == "Generic Group"
        assert group_input.group_types == ["Unified"]
        assert group_input.security_enabled is True


class TestEdgeCases:
    """Tests for edge cases and special scenarios."""

    @pytest.mark.asyncio
    async def test_http_client_property_access(self, mock_token_provider):
        """Test accessing http_client property."""
        client = AzureadClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        assert client.http_client is not None
        assert client._http_client is client.http_client

    @pytest.mark.asyncio
    async def test_special_characters_in_group_id(self, mock_token_provider):
        """Test with special characters in group ID."""
        client = AzureadClient(
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
            await client.remove_member_from_group_async(
                group_id="5e6cf5c7-b511-4842-6aae-3f6b8ae5e95b",
                member_id="8a9bf2d1-c322-5933-7bbf-4g7c9bf6f06c"
            )

            call_args = mock_send.call_args
            assert "5e6cf5c7-b511-4842-6aae-3f6b8ae5e95b" in call_args[0][1]

    @pytest.mark.asyncio
    async def test_multiple_consecutive_calls(self, mock_token_provider):
        """Test multiple consecutive API calls."""
        client = AzureadClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(status=201, text='{"id": "test"}')

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ) as mock_send:
            group_input = CreateGroupInput(display_name="Group 1")
            await client.create_group_async(input=group_input)

            group_input2 = CreateGroupInput(display_name="Group 2")
            await client.create_group_async(input=group_input2)

            assert mock_send.call_count == 2
