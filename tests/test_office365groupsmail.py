# Copyright (c) Microsoft Corporation. All rights reserved.

"""Unit tests for Office365groupsmailClient."""

import pytest
from unittest.mock import AsyncMock, patch

from azure.connectors.office365groupsmail import (
    Conversation,
    CreateConversationBody,
    ForwardPostBody,
    ListConversationsResponse,
    Office365groupsmailClient,
    ReplyConversationThreadBody,
    TRIGGER_OPERATIONS,
)
from azure.connectors.sdk import (
    ConnectorClientOptions,
    ConnectorException,
    ManagedIdentityTokenProvider,
)
from tests.conftest import MockResponse


async def _invoke_operation(client: Office365groupsmailClient, operation: str):
    """Invoke an operation by name for shared parameterized tests."""
    if operation == "list_conversations":
        return await client.list_conversations_async(group_id="group123")
    if operation == "create_conversation":
        return await client.create_conversation_async(
            input=CreateConversationBody(topic="Hello"),
            group_id="group123",
        )
    if operation == "get_group_conversation":
        return await client.get_group_conversation_async(
            group_id="group123",
            conversation_id="conv123",
        )
    if operation == "list_conversation_threads":
        return await client.list_conversation_threads_async(
            group_id="group123",
            conversation_id="conv123",
        )
    if operation == "create_conversation_thread":
        return await client.create_conversation_thread_async(
            input=CreateConversationBody(topic="Thread"),
            group_id="group123",
            conversation_id="conv123",
        )
    if operation == "list_group_threads":
        return await client.list_group_threads_async(group_id="group123")
    if operation == "create_group_thread":
        return await client.create_group_thread_async(
            input=CreateConversationBody(topic="Group thread"),
            group_id="group123",
        )
    if operation == "get_conversation_thread":
        return await client.get_conversation_thread_async(
            group_id="group123",
            thread_id="thread123",
        )
    if operation == "delete_conversation_thread":
        return await client.delete_conversation_thread_async(
            group_id="group123",
            thread_id="thread123",
        )
    if operation == "list_thread_posts":
        return await client.list_thread_posts_async(
            group_id="group123",
            thread_id="thread123",
        )
    if operation == "get_thread":
        return await client.get_thread_async(
            group_id="group123",
            thread_id="thread123",
            post_id="post123",
        )
    if operation == "get_attachments":
        return await client.get_attachments_async(
            group_id="group123",
            thread_id="thread123",
            post_id="post123",
        )
    if operation == "reply_to_a_thread":
        return await client.reply_to_a_thread_async(
            input=ReplyConversationThreadBody(),
            group_id="group123",
            thread_id="thread123",
        )
    if operation == "reply":
        return await client.reply_async(
            input=ReplyConversationThreadBody(),
            group_id="group123",
            thread_id="thread123",
            post_id="post123",
        )
    if operation == "http_request":
        return await client.http_request_async(input=b"request")
    if operation == "forward":
        return await client.forward_async(
            input=ForwardPostBody(comment="Forward this"),
            group_mail="group@contoso.com",
            conversation_id="conv123",
            thread_id="thread123",
            post_id="post123",
        )
    if operation == "list_groups":
        return await client.list_groups_async()

    raise ValueError(f"Unsupported operation '{operation}'.")


class TestOffice365groupsmailClientInitialization:
    """Tests for Office365groupsmailClient initialization."""

    def test_init_with_valid_url_and_defaults(self):
        """Test initialization with valid URL and default parameters."""
        client = Office365groupsmailClient("https://example.azure.com/connections/test")

        assert client._connection_runtime_url == "https://example.azure.com/connections/test"
        assert client.connector_name == "office365groupsmail"
        assert isinstance(client._http_client._token_provider, ManagedIdentityTokenProvider)

    def test_init_with_trailing_slash(self):
        """Test that trailing slash is removed from URL."""
        client = Office365groupsmailClient("https://example.azure.com/connections/test/")

        assert client._connection_runtime_url == "https://example.azure.com/connections/test"

    def test_init_with_custom_token_provider(self, mock_token_provider):
        """Test initialization with custom token provider."""
        client = Office365groupsmailClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider,
        )

        assert client._http_client._token_provider is mock_token_provider

    def test_init_with_custom_options(self, mock_token_provider):
        """Test initialization with custom options."""
        options = ConnectorClientOptions(timeout_seconds=60.0, max_retry_attempts=5)
        client = Office365groupsmailClient(
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
            Office365groupsmailClient("")

    def test_init_with_none_url_raises_error(self):
        """Test that None URL raises ValueError."""
        with pytest.raises(ValueError, match="connection_runtime_url cannot be None or empty"):
            Office365groupsmailClient(None)


class TestOffice365groupsmailClientLifecycle:
    """Tests for Office365groupsmailClient lifecycle methods."""

    @pytest.mark.asyncio
    async def test_close(self, mock_token_provider):
        """Test close method calls http_client.close."""
        client = Office365groupsmailClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider,
        )

        with patch.object(client._http_client, "close", new_callable=AsyncMock) as mock_close:
            await client.close()
            mock_close.assert_called_once()

    @pytest.mark.asyncio
    async def test_context_manager(self, mock_token_provider):
        """Test async context manager functionality."""
        with patch.object(Office365groupsmailClient, "close", new_callable=AsyncMock) as mock_close:
            async with Office365groupsmailClient(
                "https://example.azure.com/connections/test",
                token_provider=mock_token_provider,
            ) as client:
                assert isinstance(client, Office365groupsmailClient)

            mock_close.assert_called_once()


class TestOffice365groupsmailClientMethods:
    """Success path tests for representative methods."""

    @pytest.mark.asyncio
    async def test_list_conversations_success(self, mock_token_provider):
        """Test list_conversations_async returns parsed payload."""
        client = Office365groupsmailClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider,
        )
        mock_response = MockResponse(status=200, text='{"value":[{"id":"conv1"}]}')

        with patch.object(
            client._http_client,
            "send_async",
            new_callable=AsyncMock,
            return_value=mock_response,
        ) as mock_send:
            result = await client.list_conversations_async(group_id="group123")

            assert len(result["value"]) == 1
            assert "/v1.0/groups/group123/conversations" in mock_send.call_args[0][1]

    @pytest.mark.asyncio
    async def test_create_conversation_success(self, mock_token_provider):
        """Test create_conversation_async sends body and returns parsed payload."""
        client = Office365groupsmailClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider,
        )
        mock_response = MockResponse(status=201, text='{"id":"conv1"}')

        with patch.object(
            client._http_client,
            "send_async",
            new_callable=AsyncMock,
            return_value=mock_response,
        ) as mock_send:
            result = await client.create_conversation_async(
                input=CreateConversationBody(topic="Hi"),
                group_id="group123",
            )

            assert result["id"] == "conv1"
            assert isinstance(mock_send.call_args.kwargs["body"], CreateConversationBody)

    @pytest.mark.asyncio
    async def test_get_thread_expands_attachments(self, mock_token_provider):
        """Test get_thread_async includes expected expand query parameter."""
        client = Office365groupsmailClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider,
        )
        mock_response = MockResponse(status=200, text='{"id":"post1"}')

        with patch.object(
            client._http_client,
            "send_async",
            new_callable=AsyncMock,
            return_value=mock_response,
        ) as mock_send:
            await client.get_thread_async(
                group_id="group123",
                thread_id="thread123",
                post_id="post123",
            )

            assert "$expand=attachments" in mock_send.call_args[0][1]

    @pytest.mark.asyncio
    async def test_list_groups_uses_expected_filters(self, mock_token_provider):
        """Test list_groups_async includes OData filter/select/top query params."""
        client = Office365groupsmailClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider,
        )
        mock_response = MockResponse(status=200, text='{"value": []}')

        with patch.object(
            client._http_client,
            "send_async",
            new_callable=AsyncMock,
            return_value=mock_response,
        ) as mock_send:
            await client.list_groups_async()

            call_path = mock_send.call_args[0][1]
            assert "$filter=" in call_path
            assert "$select=id%2CdisplayName" in call_path
            assert "$top=999" in call_path


class TestOffice365groupsmailClientErrorHandling:
    """Error handling tests for all operations."""

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "operation",
        [
            "list_conversations",
            "create_conversation",
            "get_group_conversation",
            "list_conversation_threads",
            "create_conversation_thread",
            "list_group_threads",
            "create_group_thread",
            "get_conversation_thread",
            "delete_conversation_thread",
            "list_thread_posts",
            "get_thread",
            "get_attachments",
            "reply_to_a_thread",
            "reply",
            "http_request",
            "forward",
            "list_groups",
        ],
    )
    async def test_error_response_raises_exception_for_all_operations(
        self,
        mock_token_provider,
        operation,
    ):
        """Test non-2xx responses raise ConnectorException for every operation."""
        client = Office365groupsmailClient(
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


class TestOnNewEmailInGroupTrigger:
    """Tests for the new-group-email trigger metadata."""

    def test_registration_metadata(self):
        """Test trigger metadata and callback contract."""
        trigger = TRIGGER_OPERATIONS["OnNewEmailInGroup"]

        assert trigger["path"].endswith("/groups/{groupId}/conversations")
        assert trigger["required_parameters"] == ["groupId"]
        assert trigger["callback_payload_type"] == "OnNewEmailInGroupResponse"
        assert not hasattr(Office365groupsmailClient, "on_new_email_in_group_async")


class TestOffice365groupsmailTypeSerialization:
    """Tests for generated dataclass defaults."""

    def test_dataclass_instances_initialize_expected_defaults(self):
        """Test generated dataclasses initialize with expected default values."""
        list_response = ListConversationsResponse()
        conversation = Conversation()

        assert list_response.next_link is None
        assert list_response.value is None
        assert conversation.id is None
