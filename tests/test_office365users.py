# Copyright (c) Microsoft Corporation. All rights reserved.

"""Unit tests for Office365usersClient."""

import pytest
from unittest.mock import AsyncMock, patch
from azure.connectors.office365users import (
    Office365usersClient,
    GraphUserUpdateableV1,
    UpdateMyPhotoInput,
    HttpRequestInput,
)
from azure.connectors.sdk import (
    ConnectorClientOptions,
    ManagedIdentityTokenProvider,
    ConnectorException,
)
from tests.conftest import MockResponse


class TestOffice365usersClientInitialization:
    """Tests for Office365usersClient initialization."""

    def test_init_with_valid_url_and_defaults(self):
        """Test initialization with valid URL and default parameters."""
        client = Office365usersClient("https://example.azure.com/connections/test")

        assert client._connection_runtime_url == "https://example.azure.com/connections/test"
        assert client.connector_name == "office365users"
        assert isinstance(client._http_client._token_provider, ManagedIdentityTokenProvider)

    def test_init_with_trailing_slash(self):
        """Test that trailing slash is removed from URL."""
        client = Office365usersClient("https://example.azure.com/connections/test/")

        assert client._connection_runtime_url == "https://example.azure.com/connections/test"

    def test_init_with_custom_token_provider(self, mock_token_provider):
        """Test initialization with custom token provider."""
        client = Office365usersClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        assert client._http_client._token_provider is mock_token_provider

    def test_init_with_custom_options(self, mock_token_provider):
        """Test initialization with custom options."""
        options = ConnectorClientOptions(timeout_seconds=60.0, max_retry_attempts=5)
        client = Office365usersClient(
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
            Office365usersClient("")

    def test_init_with_none_url_raises_error(self):
        """Test that None URL raises ValueError."""
        with pytest.raises(ValueError, match="connection_runtime_url cannot be None or empty"):
            Office365usersClient(None)

    def test_connector_name_property(self, mock_token_provider):
        """Test connector_name property returns 'office365users'."""
        client = Office365usersClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        assert client.connector_name == "office365users"


class TestOffice365usersClientLifecycle:
    """Tests for Office365usersClient lifecycle methods."""

    @pytest.mark.asyncio
    async def test_close(self, mock_token_provider):
        """Test close method calls http_client.close."""
        client = Office365usersClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        with patch.object(client._http_client, 'close', new_callable=AsyncMock) as mock_close:
            await client.close()
            mock_close.assert_called_once()

    @pytest.mark.asyncio
    async def test_context_manager(self, mock_token_provider):
        """Test async context manager functionality."""
        with patch.object(Office365usersClient, 'close', new_callable=AsyncMock) as mock_close:
            async with Office365usersClient(
                "https://example.azure.com/connections/test",
                token_provider=mock_token_provider
            ) as client:
                assert isinstance(client, Office365usersClient)

            mock_close.assert_called_once()


class TestUpdateMyProfile:
    """Tests for update_my_profile_async method."""

    @pytest.mark.asyncio
    async def test_success(self, mock_token_provider):
        """Test successful PATCH request."""
        client = Office365usersClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(status=200, text='{}')
        profile_input = GraphUserUpdateableV1(about_me="Test about me")

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ) as mock_send:
            await client.update_my_profile_async(input=profile_input)

            mock_send.assert_called_once()
            call_args = mock_send.call_args
            assert call_args[0][0] == "PATCH"
            assert "codeless/v1.0/me" in call_args[0][1]


class TestUpdateMyPhoto:
    """Tests for update_my_photo_async method."""

    @pytest.mark.asyncio
    async def test_success(self, mock_token_provider):
        """Test successful PUT request."""
        client = Office365usersClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(status=200, text='{}')
        photo_input = UpdateMyPhotoInput()

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ) as mock_send:
            await client.update_my_photo_async(input=photo_input)

            mock_send.assert_called_once()
            call_args = mock_send.call_args
            assert call_args[0][0] == "PUT"
            assert "codeless/v1.0/me/photo/$value" in call_args[0][1]


class TestMyTrendingDocuments:
    """Tests for my_trending_documents_async method."""

    @pytest.mark.asyncio
    async def test_success_with_json_response(self, mock_token_provider):
        """Test successful GET request."""
        client = Office365usersClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(
            status=200,
            text='{"value": [{"id": "doc1", "weight": 0.9}]}'
        )

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ) as mock_send:
            result = await client.my_trending_documents_async()

            mock_send.assert_called_once()
            assert "value" in result
            assert len(result["value"]) == 1

    @pytest.mark.asyncio
    async def test_with_filter_parameter(self, mock_token_provider):
        """Test GET request with filter parameter."""
        client = Office365usersClient(
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
            await client.my_trending_documents_async(filter="resourceVisualization/type eq 'Excel'")

            call_args = mock_send.call_args
            assert "$filter=" in call_args[0][1]

    @pytest.mark.asyncio
    async def test_empty_response_returns_none(self, mock_token_provider):
        """Test that empty response returns None."""
        client = Office365usersClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(status=204, text="")

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ):
            result = await client.my_trending_documents_async()
            assert result is None

    @pytest.mark.asyncio
    async def test_error_response_raises_exception(self, mock_token_provider):
        """Test that error response raises ConnectorException."""
        client = Office365usersClient(
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
                await client.my_trending_documents_async()

            assert exc_info.value.status_code == 401


class TestRelevantPeople:
    """Tests for relevant_people_async method."""

    @pytest.mark.asyncio
    async def test_success_with_json_response(self, mock_token_provider):
        """Test successful GET request."""
        client = Office365usersClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(
            status=200,
            text='{"value": [{"id": "person1", "displayName": "John Doe"}]}'
        )

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ) as mock_send:
            result = await client.relevant_people_async(user_id="user123")

            mock_send.assert_called_once()
            call_args = mock_send.call_args
            assert "users/user123/relevantpeople" in call_args[0][1]
            assert "value" in result

    @pytest.mark.asyncio
    async def test_error_response_raises_exception(self, mock_token_provider):
        """Test that error response raises ConnectorException."""
        client = Office365usersClient(
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
                await client.relevant_people_async(user_id="invalid")

            assert exc_info.value.status_code == 404


class TestUserPhotoMetadata:
    """Tests for user_photo_metadata_async method."""

    @pytest.mark.asyncio
    async def test_success_with_user_id(self, mock_token_provider):
        """Test successful GET request with user_id parameter."""
        client = Office365usersClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(
            status=200,
            text='{"@odata.mediaContentType": "image/jpeg", "height": 648, "width": 648}'
        )

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ) as mock_send:
            result = await client.user_photo_metadata_async(user_id="user123")

            mock_send.assert_called_once()
            call_args = mock_send.call_args
            assert "userId=user123" in call_args[0][1]
            assert "@odata.mediaContentType" in result

    @pytest.mark.asyncio
    async def test_empty_response_returns_none(self, mock_token_provider):
        """Test that empty response returns None."""
        client = Office365usersClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(status=204, text="")

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ):
            result = await client.user_photo_metadata_async(user_id=None)
            assert result is None


class TestTrendingDocuments:
    """Tests for trending_documents_async method."""

    @pytest.mark.asyncio
    async def test_success_with_json_response(self, mock_token_provider):
        """Test successful GET request."""
        client = Office365usersClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(
            status=200,
            text='{"value": [{"id": "doc1", "weight": 0.85}]}'
        )

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ) as mock_send:
            result = await client.trending_documents_async(id="user123")

            mock_send.assert_called_once()
            call_args = mock_send.call_args
            assert "users/user123/insights/trending" in call_args[0][1]
            assert "value" in result

    @pytest.mark.asyncio
    async def test_with_filter_parameter(self, mock_token_provider):
        """Test GET request with filter parameter."""
        client = Office365usersClient(
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
            await client.trending_documents_async(
                id="user123",
                filter="resourceVisualization/type eq 'Word'"
            )

            call_args = mock_send.call_args
            assert "$filter=" in call_args[0][1]

    @pytest.mark.asyncio
    async def test_error_response_raises_exception(self, mock_token_provider):
        """Test that error response raises ConnectorException."""
        client = Office365usersClient(
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
                await client.trending_documents_async(id="user123")

            assert exc_info.value.status_code == 500


class TestHttpRequest:
    """Tests for http_request_async method."""

    @pytest.mark.asyncio
    async def test_success_with_json_response(self, mock_token_provider):
        """Test successful POST request."""
        client = Office365usersClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(
            status=200,
            text='{"result": "success"}'
        )
        request_input = HttpRequestInput()

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ) as mock_send:
            result = await client.http_request_async(input=request_input)

            mock_send.assert_called_once()
            call_args = mock_send.call_args
            assert call_args[0][0] == "POST"
            assert "codeless/httprequest" in call_args[0][1]
            assert "result" in result

    @pytest.mark.asyncio
    async def test_empty_response_returns_none(self, mock_token_provider):
        """Test that empty response returns None."""
        client = Office365usersClient(
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
            result = await client.http_request_async(input=HttpRequestInput())
            assert result is None

    @pytest.mark.asyncio
    async def test_error_response_raises_exception(self, mock_token_provider):
        """Test that error response raises ConnectorException."""
        client = Office365usersClient(
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
                await client.http_request_async(input=HttpRequestInput())

            assert exc_info.value.status_code == 400


class TestDirectReports:
    """Tests for direct_reports_async method."""

    @pytest.mark.asyncio
    async def test_success_with_json_response(self, mock_token_provider):
        """Test successful GET request."""
        client = Office365usersClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(
            status=200,
            text='{"value": [{"id": "report1", "displayName": "Jane Doe"}]}'
        )

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ) as mock_send:
            result = await client.direct_reports_async(id="manager123")

            mock_send.assert_called_once()
            call_args = mock_send.call_args
            assert "users/manager123/directReports" in call_args[0][1]
            assert "value" in result

    @pytest.mark.asyncio
    async def test_with_select_and_top_parameters(self, mock_token_provider):
        """Test GET request with select and top parameters."""
        client = Office365usersClient(
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
            await client.direct_reports_async(
                id="manager123",
                select="displayName,mail",
                top="10"
            )

            call_args = mock_send.call_args
            assert "$select=" in call_args[0][1]
            assert "$top=" in call_args[0][1]

    @pytest.mark.asyncio
    async def test_empty_response_returns_none(self, mock_token_provider):
        """Test that empty response returns None."""
        client = Office365usersClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(status=204, text="")

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ):
            result = await client.direct_reports_async(id="manager123")
            assert result is None

    @pytest.mark.asyncio
    async def test_error_response_raises_exception(self, mock_token_provider):
        """Test that error response raises ConnectorException."""
        client = Office365usersClient(
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
                await client.direct_reports_async(id="manager123")

            assert exc_info.value.status_code == 403


class TestManager:
    """Tests for manager_async method."""

    @pytest.mark.asyncio
    async def test_success_with_json_response(self, mock_token_provider):
        """Test successful GET request."""
        client = Office365usersClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(
            status=200,
            text='{"id": "manager1", "displayName": "Boss Name", "mail": "boss@example.com"}'
        )

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ) as mock_send:
            result = await client.manager_async(id="user123")

            mock_send.assert_called_once()
            call_args = mock_send.call_args
            assert "users/user123/manager" in call_args[0][1]
            assert "displayName" in result

    @pytest.mark.asyncio
    async def test_with_select_parameter(self, mock_token_provider):
        """Test GET request with select parameter."""
        client = Office365usersClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(status=200, text='{"displayName": "Boss Name"}')

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ) as mock_send:
            await client.manager_async(id="user123", select="displayName")

            call_args = mock_send.call_args
            assert "$select=displayName" in call_args[0][1]

    @pytest.mark.asyncio
    async def test_error_response_raises_exception(self, mock_token_provider):
        """Test that error response raises ConnectorException."""
        client = Office365usersClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(status=404, text='{"error": "Manager not found"}')

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ):
            with pytest.raises(ConnectorException) as exc_info:
                await client.manager_async(id="user123")

            assert exc_info.value.status_code == 404


class TestMyProfile:
    """Tests for my_profile_async method."""

    @pytest.mark.asyncio
    async def test_success_with_json_response(self, mock_token_provider):
        """Test successful GET request."""
        client = Office365usersClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(
            status=200,
            text='{"id": "me123", "displayName": "Current User", "mail": "me@example.com"}'
        )

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ) as mock_send:
            result = await client.my_profile_async()

            mock_send.assert_called_once()
            call_args = mock_send.call_args
            assert "codeless/v1.0/me" in call_args[0][1]
            assert "displayName" in result

    @pytest.mark.asyncio
    async def test_with_select_parameter(self, mock_token_provider):
        """Test GET request with select parameter."""
        client = Office365usersClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(status=200, text='{"displayName": "Current User"}')

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ) as mock_send:
            await client.my_profile_async(select="displayName,mail")

            call_args = mock_send.call_args
            assert "$select=" in call_args[0][1]

    @pytest.mark.asyncio
    async def test_empty_response_returns_none(self, mock_token_provider):
        """Test that empty response returns None."""
        client = Office365usersClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(status=204, text="")

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ):
            result = await client.my_profile_async()
            assert result is None

    @pytest.mark.asyncio
    async def test_error_response_raises_exception(self, mock_token_provider):
        """Test that error response raises ConnectorException."""
        client = Office365usersClient(
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
                await client.my_profile_async()

            assert exc_info.value.status_code == 401


class TestSearchUser:
    """Tests for search_user_async method."""

    @pytest.mark.asyncio
    async def test_success_with_json_response(self, mock_token_provider):
        """Test successful GET request."""
        client = Office365usersClient(
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
            result = await client.search_user_async(search_term="John")

            mock_send.assert_called_once()
            call_args = mock_send.call_args
            assert "searchTerm=John" in call_args[0][1]
            assert "value" in result

    @pytest.mark.asyncio
    async def test_with_all_parameters(self, mock_token_provider):
        """Test GET request with all parameters."""
        client = Office365usersClient(
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
            await client.search_user_async(
                search_term="John",
                top="25",
                is_search_term_required="true",
                skip_token="abc123"
            )

            call_args = mock_send.call_args
            assert "searchTerm=John" in call_args[0][1]
            assert "top=25" in call_args[0][1]
            assert "isSearchTermRequired=true" in call_args[0][1]
            assert "skipToken=abc123" in call_args[0][1]

    @pytest.mark.asyncio
    async def test_empty_response_returns_none(self, mock_token_provider):
        """Test that empty response returns None."""
        client = Office365usersClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(status=204, text="")

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ):
            result = await client.search_user_async()
            assert result is None

    @pytest.mark.asyncio
    async def test_error_response_raises_exception(self, mock_token_provider):
        """Test that error response raises ConnectorException."""
        client = Office365usersClient(
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
                await client.search_user_async(search_term="test")

            assert exc_info.value.status_code == 500


class TestUserPhoto:
    """Tests for user_photo_async method."""

    @pytest.mark.asyncio
    async def test_success_returns_binary_content(self, mock_token_provider):
        """Test successful GET request returns binary content."""
        client = Office365usersClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        binary_content = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR'
        mock_response = MockResponse(status=200, text="", content=binary_content)

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ) as mock_send:
            result = await client.user_photo_async(id="user123")

            mock_send.assert_called_once()
            call_args = mock_send.call_args
            assert "users/user123/photo/$value" in call_args[0][1]
            assert result == binary_content

    @pytest.mark.asyncio
    async def test_error_response_raises_exception(self, mock_token_provider):
        """Test that error response raises ConnectorException."""
        client = Office365usersClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(status=404, text='{"error": "Photo not found"}')

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ):
            with pytest.raises(ConnectorException) as exc_info:
                await client.user_photo_async(id="user123")

            assert exc_info.value.status_code == 404


class TestUserProfile:
    """Tests for user_profile_async method."""

    @pytest.mark.asyncio
    async def test_success_with_json_response(self, mock_token_provider):
        """Test successful GET request."""
        client = Office365usersClient(
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
            result = await client.user_profile_async(id="user123")

            mock_send.assert_called_once()
            call_args = mock_send.call_args
            assert "codeless/v1.0/users/user123" in call_args[0][1]
            assert "displayName" in result

    @pytest.mark.asyncio
    async def test_with_select_parameter(self, mock_token_provider):
        """Test GET request with select parameter."""
        client = Office365usersClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(status=200, text='{"displayName": "John Doe"}')

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ) as mock_send:
            await client.user_profile_async(id="user123", select="displayName,mail,jobTitle")

            call_args = mock_send.call_args
            assert "$select=" in call_args[0][1]

    @pytest.mark.asyncio
    async def test_empty_response_returns_none(self, mock_token_provider):
        """Test that empty response returns None."""
        client = Office365usersClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(status=204, text="")

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ):
            result = await client.user_profile_async(id="user123")
            assert result is None

    @pytest.mark.asyncio
    async def test_error_response_raises_exception(self, mock_token_provider):
        """Test that error response raises ConnectorException."""
        client = Office365usersClient(
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
                await client.user_profile_async(id="invalid_user")

            assert exc_info.value.status_code == 404
