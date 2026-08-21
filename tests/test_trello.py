# Copyright (c) Microsoft Corporation. All rights reserved.

"""Unit tests for TrelloClient."""

import inspect
from unittest.mock import AsyncMock, patch

import pytest

from azure.connectors.sdk import (
    ConnectorClientOptions,
    ConnectorException,
    ManagedIdentityTokenProvider,
)
from azure.connectors.trello import (
    Card,
    CommentPost,
    CreateBoard,
    CreateCard,
    CreateList,
    TrelloClient,
    TRIGGER_OPERATIONS,
    UpdateBoard,
    UpdateCard,
)
from tests.conftest import MockResponse


async def _invoke_operation(client: TrelloClient, operation: str):
    """Invoke a Trello operation by name for shared tests."""
    if operation == "list_cards":
        return await client.list_cards_async(board_id="board")
    if operation == "list_cards_simple":
        return await client.list_cards_simple_async(board_id="board")
    if operation == "get_card":
        return await client.get_card_async(card_id="card", board_id="board")
    if operation == "delete_card":
        return await client.delete_card_async(card_id="card", board_id="board")
    if operation == "list_boards":
        return await client.list_boards_async()
    if operation == "list_boards_simple":
        return await client.list_boards_simple_async()
    if operation == "get_board":
        return await client.get_board_async(board_id="board")
    if operation == "update_board":
        return await client.update_board_async(input=UpdateBoard(), board_id="board")
    if operation == "list_lists":
        return await client.list_lists_async(board_id="board")
    if operation == "list_lists_simple":
        return await client.list_lists_simple_async(board_id="board")
    if operation == "get_list":
        return await client.get_list_async(list_id="list", board_id="board")
    if operation == "update_list":
        return await client.update_list_async(list_id="list", board_id="board")
    if operation == "get_user_profile":
        return await client.get_user_profile_async()
    if operation == "list_teams":
        return await client.list_teams_async()
    if operation == "list_team_members":
        return await client.list_team_members_async(team_id="team")
    if operation == "list_board_members":
        return await client.list_board_members_async(board_id="board")
    if operation == "list_board_labels":
        return await client.list_board_labels_async(board_id="board")
    if operation == "get_team_for_board":
        return await client.get_team_for_board_async(board_id="board")
    if operation == "list_card_members":
        return await client.list_card_members_async(card_id="card", board_id="board")
    if operation == "list_card_comments":
        return await client.list_card_comments_async(card_id="card", board_id="board")
    if operation == "add_comment_to_card":
        return await client.add_comment_to_card_async(
            input=CommentPost(),
            card_id="card",
            board_id="board",
        )
    if operation == "add_member_to_card":
        return await client.add_member_to_card_async(
            card_id="card",
            board_id="board",
            member_id="member",
        )
    if operation == "create_board":
        return await client.create_board_async(input=CreateBoard())
    if operation == "create_list":
        return await client.create_list_async(input=CreateList())
    if operation == "close_board":
        return await client.close_board_async(board_id="board")
    if operation == "create_card":
        return await client.create_card_async(input=CreateCard(), board_id="board")
    if operation == "update_card":
        return await client.update_card_async(
            input=UpdateCard(),
            card_id="card",
            board_id="board",
        )

    raise ValueError(f"Unsupported operation '{operation}'.")


ALL_OPERATIONS = [
    "list_cards",
    "list_cards_simple",
    "get_card",
    "delete_card",
    "list_boards",
    "list_boards_simple",
    "get_board",
    "update_board",
    "list_lists",
    "list_lists_simple",
    "get_list",
    "update_list",
    "get_user_profile",
    "list_teams",
    "list_team_members",
    "list_board_members",
    "list_board_labels",
    "get_team_for_board",
    "list_card_members",
    "list_card_comments",
    "add_comment_to_card",
    "add_member_to_card",
    "create_board",
    "create_list",
    "close_board",
    "create_card",
    "update_card",
]


class TestTrelloClientInitialization:
    """Tests for TrelloClient initialization."""

    def test_init_with_valid_url_and_defaults(self):
        """Test initialization with valid URL and default parameters."""
        client = TrelloClient("https://example.azure.com/connections/test")

        assert client._connection_runtime_url == "https://example.azure.com/connections/test"
        assert client.connector_name == "trello"
        assert isinstance(client._http_client._token_provider, ManagedIdentityTokenProvider)

    def test_init_with_trailing_slash(self):
        """Test that trailing slash is removed from URL."""
        client = TrelloClient("https://example.azure.com/connections/test/")

        assert client._connection_runtime_url == "https://example.azure.com/connections/test"

    def test_init_with_custom_token_provider(self, mock_token_provider):
        """Test initialization with custom token provider."""
        client = TrelloClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider,
        )

        assert client._http_client._token_provider is mock_token_provider

    def test_init_with_custom_options(self, mock_token_provider):
        """Test initialization with custom options."""
        options = ConnectorClientOptions(timeout_seconds=60.0, max_retry_attempts=5)
        client = TrelloClient(
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
            TrelloClient("")

    def test_init_with_none_url_raises_error(self):
        """Test that None URL raises ValueError."""
        with pytest.raises(ValueError, match="connection_runtime_url cannot be None or empty"):
            TrelloClient(None)

    def test_connector_name_property(self, mock_token_provider):
        """Test connector_name property returns 'trello'."""
        client = TrelloClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider,
        )

        assert client.connector_name == "trello"


class TestTrelloClientLifecycle:
    """Tests for TrelloClient lifecycle methods."""

    @pytest.mark.asyncio
    async def test_close(self, mock_token_provider):
        """Test close method calls http_client.close."""
        client = TrelloClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider,
        )

        with patch.object(client._http_client, "close", new_callable=AsyncMock) as mock_close:
            await client.close()
            mock_close.assert_called_once()

    @pytest.mark.asyncio
    async def test_context_manager(self, mock_token_provider):
        """Test async context manager functionality."""
        with patch.object(TrelloClient, "close", new_callable=AsyncMock) as mock_close:
            async with TrelloClient(
                "https://example.azure.com/connections/test",
                token_provider=mock_token_provider,
            ) as client:
                assert isinstance(client, TrelloClient)

            mock_close.assert_called_once()


class TestTrelloClientOperations:
    """Tests for Trello operations."""

    def test_all_generated_operations_are_covered(self):
        """Test the operation list matches every generated client method."""
        generated_operations = {
            name.removesuffix("_async")
            for name, method in inspect.getmembers(TrelloClient, inspect.iscoroutinefunction)
            if name.endswith("_async")
        }

        assert generated_operations == set(ALL_OPERATIONS)

    @pytest.mark.asyncio
    async def test_list_cards_serializes_path_and_query(self, mock_token_provider):
        """Test list_cards_async serializes its board and query values."""
        client = TrelloClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider,
        )
        mock_response = MockResponse(status=200, text='[{"id":"card"}]')

        with patch.object(
            client._http_client,
            "send_async",
            new_callable=AsyncMock,
            return_value=mock_response,
        ) as mock_send:
            result = await client.list_cards_async(
                board_id="board/one",
                actions="comment card",
                limit="10",
            )

            assert result == [{"id": "card"}]
            assert mock_send.call_args[0][0] == "GET"
            assert "/boards/board%2Fone/cards" in mock_send.call_args[0][1]
            assert "actions=comment%20card" in mock_send.call_args[0][1]
            assert "limit=10" in mock_send.call_args[0][1]

    @pytest.mark.asyncio
    async def test_create_card_sends_request_body(self, mock_token_provider):
        """Test create_card_async sends the request body and board identifier."""
        client = TrelloClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider,
        )
        request = CreateCard(name="SDK card", id_list="list")
        mock_response = MockResponse(status=201, text='{"id":"card"}')

        with patch.object(
            client._http_client,
            "send_async",
            new_callable=AsyncMock,
            return_value=mock_response,
        ) as mock_send:
            result = await client.create_card_async(input=request, board_id="board")

            assert result == {"id": "card"}
            assert mock_send.call_args[0][0] == "POST"
            assert mock_send.call_args[0][1].endswith("/v2/cards?board_id=board")
            assert mock_send.call_args.kwargs["body"] is request

    @pytest.mark.asyncio
    async def test_delete_card_empty_response_returns_none(self, mock_token_provider):
        """Test delete_card_async returns None for an empty success response."""
        client = TrelloClient(
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
            result = await client.delete_card_async(card_id="card", board_id="board")

            assert result is None
            assert mock_send.call_args[0][0] == "DELETE"
            assert "/cards/card?board_id=board" in mock_send.call_args[0][1]

    @pytest.mark.asyncio
    @pytest.mark.parametrize("operation", ALL_OPERATIONS)
    async def test_error_response_raises_connector_exception(
        self,
        mock_token_provider,
        operation,
    ):
        """Test every Trello operation raises for a non-success response."""
        client = TrelloClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider,
        )
        mock_response = MockResponse(status=500, text='{"error":"failed"}')

        with patch.object(
            client._http_client,
            "send_async",
            new_callable=AsyncMock,
            return_value=mock_response,
        ):
            with pytest.raises(ConnectorException) as exc_info:
                await _invoke_operation(client, operation)

        assert exc_info.value.status_code == 500


class TestTrelloTriggerOperations:
    """Tests for Trello trigger metadata."""

    @pytest.mark.parametrize(
        ("operation_id", "required_parameters"),
        [
            ("OnNewCardInBoardV3", ["board_id"]),
            ("OnNewCardInListV3", ["board_id", "list_id"]),
        ],
    )
    def test_trigger_metadata(self, operation_id, required_parameters):
        """Test trigger metadata retains current V3 routes and payload types."""
        trigger = TRIGGER_OPERATIONS[operation_id]

        assert trigger["operation_id"] == operation_id
        assert trigger["method"] == "get"
        assert trigger["path"].startswith("/{connectionId}/v3/trigger/")
        assert trigger["required_parameters"] == required_parameters
        assert trigger["callback_payload_type"] == "CardInAction"

    def test_trigger_operations_are_not_client_methods(self):
        """Test trigger operations are not emitted as callable client methods."""
        assert not hasattr(TrelloClient, "on_new_card_in_board_async")
        assert not hasattr(TrelloClient, "on_new_card_in_list_async")


class TestTrelloTypeSerialization:
    """Tests for Trello generated model defaults."""

    def test_response_dataclasses_initialize_expected_defaults(self):
        """Test representative response dataclasses initialize with defaults."""
        assert Card().id is None
        assert Card().checklists is None

    def test_request_dataclasses_instantiate(self):
        """Test representative request dataclasses instantiate without arguments."""
        assert CreateBoard().name is None
        assert CreateCard().name is None
        assert CreateList().name is None
