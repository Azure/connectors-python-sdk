# Copyright (c) Microsoft Corporation. All rights reserved.

"""Unit tests for YammerClient."""

import pytest
from unittest.mock import AsyncMock, patch
from azure.connectors.yammer import (
    YammerClient,
    Network,
    YammerEntity,
    User,
    MessageV2,
    MessageBody,
    LikedBy,
    Topic,
    PostOperationRequestV2,
)
from azure.connectors.sdk import (
    ConnectorClientOptions,
    ManagedIdentityTokenProvider,
    ConnectorException,
)
from tests.conftest import MockResponse


class TestYammerClientInitialization:
    """Tests for YammerClient initialization."""

    def test_init_with_valid_url_and_defaults(self):
        """Test initialization with valid URL and default parameters."""
        client = YammerClient("https://example.azure.com/connections/test")

        assert client._connection_runtime_url == (
            "https://example.azure.com/connections/test"
        )
        assert client.connector_name == "yammer"
        assert isinstance(
            client._http_client._token_provider, ManagedIdentityTokenProvider
        )

    def test_init_with_trailing_slash(self):
        """Test that trailing slash is removed from URL."""
        client = YammerClient("https://example.azure.com/connections/test/")

        assert client._connection_runtime_url == (
            "https://example.azure.com/connections/test"
        )

    def test_init_with_custom_token_provider(self, mock_token_provider):
        """Test initialization with custom token provider."""
        client = YammerClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        assert client._http_client._token_provider is mock_token_provider

    def test_init_with_custom_options(self, mock_token_provider):
        """Test initialization with custom options."""
        options = ConnectorClientOptions(
            timeout_seconds=60.0, max_retry_attempts=5
        )
        client = YammerClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider,
            options=options
        )

        assert client._options is options
        assert client._options.timeout_seconds == 60.0
        assert client._options.max_retry_attempts == 5

    def test_init_with_empty_url_raises_error(self):
        """Test that empty URL raises ValueError."""
        with pytest.raises(
            ValueError, match="connection_runtime_url cannot be None or empty"
        ):
            YammerClient("")

    def test_init_with_none_url_raises_error(self):
        """Test that None URL raises ValueError."""
        with pytest.raises(
            ValueError, match="connection_runtime_url cannot be None or empty"
        ):
            YammerClient(None)

    def test_connector_name_property(self, mock_token_provider):
        """Test connector_name property returns 'yammer'."""
        client = YammerClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        assert client.connector_name == "yammer"


class TestYammerClientLifecycle:
    """Tests for YammerClient lifecycle methods."""

    @pytest.mark.asyncio
    async def test_close(self, mock_token_provider):
        """Test close method calls http_client.close."""
        client = YammerClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        with patch.object(
            client._http_client, 'close', new_callable=AsyncMock
        ) as mock_close:
            await client.close()
            mock_close.assert_called_once()

    @pytest.mark.asyncio
    async def test_context_manager(self, mock_token_provider):
        """Test async context manager functionality."""
        with patch.object(
            YammerClient, 'close', new_callable=AsyncMock
        ) as mock_close:
            async with YammerClient(
                "https://example.azure.com/connections/test",
                token_provider=mock_token_provider
            ) as client:
                assert isinstance(client, YammerClient)

            mock_close.assert_called_once()


class TestGetNetworks:
    """Tests for get_networks_async method."""

    @pytest.mark.asyncio
    async def test_success(self, mock_token_provider):
        """Test successful GET request."""
        client = YammerClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(
            status=200,
            text='[{"id": "net123", "name": "Contoso", "permalink": "contoso"}]'
        )

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ) as mock_send:
            result = await client.get_networks_async()

            mock_send.assert_called_once()
            call_args = mock_send.call_args
            assert call_args[0][0] == "GET"
            assert "/networks.json" in call_args[0][1]
            assert len(result) == 1
            assert result[0]["name"] == "Contoso"

    @pytest.mark.asyncio
    async def test_error_response_raises_exception(self, mock_token_provider):
        """Test that error response raises ConnectorException."""
        client = YammerClient(
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
                await client.get_networks_async()

            assert exc_info.value.status_code == 401


class TestGetGroups:
    """Tests for get_groups_async method."""

    @pytest.mark.asyncio
    async def test_success(self, mock_token_provider):
        """Test successful GET request."""
        client = YammerClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(
            status=200,
            text='[{"id": 1, "full_name": "Engineering Team"}]'
        )

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ) as mock_send:
            result = await client.get_groups_async()

            mock_send.assert_called_once()
            call_args = mock_send.call_args
            assert call_args[0][0] == "GET"
            assert "/groups.json" in call_args[0][1]
            assert len(result) == 1

    @pytest.mark.asyncio
    async def test_with_query_parameters(self, mock_token_provider):
        """Test GET request with query parameters."""
        client = YammerClient(
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
            await client.get_groups_async(
                network_id="net123",
                mine="1",
                show_all_company_group="true"
            )

            call_args = mock_send.call_args
            url = call_args[0][1]
            assert "network_id=net123" in url
            assert "mine=1" in url
            assert "showAllCompanyGroup=true" in url


class TestGetUserDetailsById:
    """Tests for get_user_details_by_id_async method."""

    @pytest.mark.asyncio
    async def test_success(self, mock_token_provider):
        """Test successful GET request."""
        client = YammerClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(
            status=200,
            text='{"name": "jdoe", "full_name": "John Doe", "email": "jdoe@contoso.com"}'
        )

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ) as mock_send:
            result = await client.get_user_details_by_id_async(user_id="12345")

            mock_send.assert_called_once()
            call_args = mock_send.call_args
            assert call_args[0][0] == "GET"
            assert "/users/12345.json" in call_args[0][1]
            assert result["full_name"] == "John Doe"


class TestLikeMessage:
    """Tests for like_message_async method."""

    @pytest.mark.asyncio
    async def test_success(self, mock_token_provider):
        """Test successful POST request."""
        client = YammerClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(status=200, text="")

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ) as mock_send:
            await client.like_message_async(message_id="msg123")

            mock_send.assert_called_once()
            call_args = mock_send.call_args
            assert call_args[0][0] == "POST"
            assert "/messages/liked_by/current.json" in call_args[0][1]
            assert "message_id=msg123" in call_args[0][1]


class TestGetAllMessages:
    """Tests for get_all_messages_async method."""

    @pytest.mark.asyncio
    async def test_success(self, mock_token_provider):
        """Test successful GET request."""
        client = YammerClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(
            status=200,
            text='{"value": [{"id": 1, "content_excerpt": "Hello"}]}'
        )

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ) as mock_send:
            _ = await client.get_all_messages_async()

            mock_send.assert_called_once()
            call_args = mock_send.call_args
            assert call_args[0][0] == "GET"
            assert "/v3/messages.json" in call_args[0][1]

    @pytest.mark.asyncio
    async def test_with_pagination_params(self, mock_token_provider):
        """Test GET request with pagination parameters."""
        client = YammerClient(
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
            await client.get_all_messages_async(
                network_id="net123",
                older_than="100",
                newer_than="50",
                threaded="true",
                limit="20"
            )

            call_args = mock_send.call_args
            url = call_args[0][1]
            assert "network_id=net123" in url
            assert "older_than=100" in url
            assert "newer_than=50" in url
            assert "threaded=true" in url
            assert "limit=20" in url


class TestGetMessagesFollowing:
    """Tests for get_messages_following_async method."""

    @pytest.mark.asyncio
    async def test_success(self, mock_token_provider):
        """Test successful GET request."""
        client = YammerClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(
            status=200,
            text='{"value": [{"id": 1, "content_excerpt": "Update"}]}'
        )

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ) as mock_send:
            _ = await client.get_messages_following_async()

            mock_send.assert_called_once()
            call_args = mock_send.call_args
            assert call_args[0][0] == "GET"
            assert "/v3/messages/following.json" in call_args[0][1]


class TestGetMessagesInGroup:
    """Tests for get_messages_in_group_async method."""

    @pytest.mark.asyncio
    async def test_success(self, mock_token_provider):
        """Test successful GET request."""
        client = YammerClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(
            status=200,
            text='{"value": [{"id": 1, "group_id": 123}]}'
        )

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ) as mock_send:
            _ = await client.get_messages_in_group_async(group_id="123")

            mock_send.assert_called_once()
            call_args = mock_send.call_args
            assert call_args[0][0] == "GET"
            assert "/v3/messages/in_group/123.json" in call_args[0][1]


class TestGetMessagesInThread:
    """Tests for get_messages_in_thread_async method."""

    @pytest.mark.asyncio
    async def test_success(self, mock_token_provider):
        """Test successful GET request."""
        client = YammerClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(
            status=200,
            text='{"value": [{"id": 1, "thread_id": 456}]}'
        )

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ) as mock_send:
            _ = await client.get_messages_in_thread_async(thread_id="456")

            mock_send.assert_called_once()
            call_args = mock_send.call_args
            assert call_args[0][0] == "GET"
            assert "/v3/messages/in_thread/456.json" in call_args[0][1]


class TestOnNewMessagesFollowing:
    """Tests for on_new_messages_following_async method (trigger)."""

    @pytest.mark.asyncio
    async def test_success(self, mock_token_provider):
        """Test successful GET trigger request."""
        client = YammerClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(
            status=200,
            text='{"messages": [{"id": 1, "content_excerpt": "New post"}]}'
        )

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ) as mock_send:
            _ = await client.on_new_messages_following_async()

            mock_send.assert_called_once()
            call_args = mock_send.call_args
            assert call_args[0][0] == "GET"
            assert "/v2/trigger/messages/following.json" in call_args[0][1]

    @pytest.mark.asyncio
    async def test_with_network_and_triggerstate(self, mock_token_provider):
        """Test GET trigger with parameters."""
        client = YammerClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(status=200, text='{"messages": []}')

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ) as mock_send:
            await client.on_new_messages_following_async(
                network_id="net123",
                triggerstate="state456"
            )

            call_args = mock_send.call_args
            url = call_args[0][1]
            assert "network_id=net123" in url
            assert "triggerstate=state456" in url


class TestOnNewMessagesInGroup:
    """Tests for on_new_messages_in_group_async method (trigger)."""

    @pytest.mark.asyncio
    async def test_success(self, mock_token_provider):
        """Test successful GET trigger request."""
        client = YammerClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(
            status=200,
            text='{"messages": [{"id": 1, "group_id": 123}]}'
        )

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ) as mock_send:
            _ = await client.on_new_messages_in_group_async(group_id="123")

            mock_send.assert_called_once()
            call_args = mock_send.call_args
            assert call_args[0][0] == "GET"
            assert "/v2/trigger/in_group/123.json" in call_args[0][1]


class TestPostMessage:
    """Tests for post_message_async method."""

    @pytest.mark.asyncio
    async def test_success(self, mock_token_provider):
        """Test successful POST request."""
        client = YammerClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(
            status=201,
            text='{"id": 789, "content_excerpt": "New message"}'
        )
        message_input = PostOperationRequestV2(
            group_id=123,
            body="Hello Yammer!",
            title="Test Post"
        )

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ) as mock_send:
            _ = await client.post_message_async(input=message_input)

            mock_send.assert_called_once()
            call_args = mock_send.call_args
            assert call_args[0][0] == "POST"
            assert "/v2/messages.json" in call_args[0][1]

    @pytest.mark.asyncio
    async def test_with_network_id(self, mock_token_provider):
        """Test POST request with network_id parameter."""
        client = YammerClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(status=201, text='{"id": 789}')
        message_input = PostOperationRequestV2(body="Hello!")

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ) as mock_send:
            await client.post_message_async(
                input=message_input,
                network_id="net123"
            )

            call_args = mock_send.call_args
            url = call_args[0][1]
            assert "network_id=net123" in url

    @pytest.mark.asyncio
    async def test_error_response_raises_exception(self, mock_token_provider):
        """Test that error response raises ConnectorException."""
        client = YammerClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(
            status=403, text='{"error": "Not authorized to post"}'
        )
        message_input = PostOperationRequestV2(body="Test")

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ):
            with pytest.raises(ConnectorException) as exc_info:
                await client.post_message_async(input=message_input)

            assert exc_info.value.status_code == 403


class TestDataClasses:
    """Tests for data class creation and attributes."""

    def test_network(self):
        """Test Network dataclass creation."""
        network = Network(
            id="net123",
            name="Contoso Network",
            permalink="contoso"
        )

        assert network.id == "net123"
        assert network.name == "Contoso Network"
        assert network.permalink == "contoso"

    def test_yammer_entity(self):
        """Test YammerEntity dataclass creation."""
        entity = YammerEntity(
            type_="group",
            id=123,
            full_name="Engineering Team"
        )

        assert entity.type_ == "group"
        assert entity.id == 123
        assert entity.full_name == "Engineering Team"

    def test_user(self):
        """Test User dataclass creation."""
        user = User(
            name="jdoe",
            job_title="Software Engineer",
            location="Seattle",
            full_name="John Doe",
            first_name="John",
            last_name="Doe",
            email="jdoe@contoso.com"
        )

        assert user.name == "jdoe"
        assert user.job_title == "Software Engineer"
        assert user.email == "jdoe@contoso.com"

    def test_message_body(self):
        """Test MessageBody dataclass creation."""
        body = MessageBody(
            parsed="Hello <b>World</b>",
            plain="Hello World",
            rich="<p>Hello <b>World</b></p>"
        )

        assert body.plain == "Hello World"
        assert body.parsed is not None

    def test_message_v2(self):
        """Test MessageV2 dataclass creation."""
        body = MessageBody(plain="Hello")
        message = MessageV2(
            id=123,
            content_excerpt="Hello",
            sender_id=456,
            created_at="2024-01-15T10:30:00Z",
            message_type="update",
            body=body,
            group_id=789,
            thread_id=101
        )

        assert message.id == 123
        assert message.content_excerpt == "Hello"
        assert message.group_id == 789

    def test_topic(self):
        """Test Topic dataclass creation."""
        topic = Topic(id=1, name="Engineering")

        assert topic.id == 1
        assert topic.name == "Engineering"

    def test_liked_by(self):
        """Test LikedBy dataclass creation."""
        liked_by = LikedBy(
            count=5,
            names=[{"name": "John"}, {"name": "Jane"}]
        )

        assert liked_by.count == 5
        assert len(liked_by.names) == 2

    def test_post_operation_request_v2(self):
        """Test PostOperationRequestV2 dataclass creation."""
        request = PostOperationRequestV2(
            group_id=123,
            body="Hello Yammer!",
            title="Announcement",
            broadcast=True
        )

        assert request.group_id == 123
        assert request.body == "Hello Yammer!"
        assert request.broadcast is True


class TestEdgeCases:
    """Tests for edge cases and special scenarios."""

    @pytest.mark.asyncio
    async def test_http_client_property_access(self, mock_token_provider):
        """Test accessing http_client property."""
        client = YammerClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        assert client.http_client is not None
        assert client._http_client is client.http_client

    @pytest.mark.asyncio
    async def test_empty_response_returns_none(self, mock_token_provider):
        """Test that empty response returns None."""
        client = YammerClient(
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
            result = await client.get_networks_async()
            assert result is None

    @pytest.mark.asyncio
    async def test_multiple_consecutive_calls(self, mock_token_provider):
        """Test multiple consecutive API calls."""
        client = YammerClient(
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
            await client.get_networks_async()
            await client.get_groups_async()

            assert mock_send.call_count == 2

    @pytest.mark.asyncio
    async def test_server_error_raises_exception(self, mock_token_provider):
        """Test that 500 server error raises ConnectorException."""
        client = YammerClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(
            status=500, text='{"error": "Internal Server Error"}'
        )

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ):
            with pytest.raises(ConnectorException) as exc_info:
                await client.get_all_messages_async()

            assert exc_info.value.status_code == 500
