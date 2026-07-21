# Copyright (c) Microsoft Corporation. All rights reserved.

"""Unit tests for MondayClient."""

from unittest.mock import AsyncMock, patch

import pytest

from azure.connectors.monday import (
    CreateBoardInput,
    CreateColumnInput,
    CreateGroupInput,
    CreateItemInput,
    CreateItemResponse,
    CreateNotificationInput,
    CreateSubitemInput,
    CreateUpdateInput,
    CreateWorkspaceInput,
    DuplicateBoardInput,
    GetSubitemSchemaResponse,
    GetTagsResponse,
    GetUsersResponse,
    GetWorkspacesResponse,
    MondayClient,
    MoveItemToGroupInput,
    UpdateItemColumnInput,
    UpdateMultipleItemColumnsInput,
    TRIGGER_OPERATIONS,
)
from azure.connectors.sdk import (
    ConnectorClientOptions,
    ConnectorException,
    ManagedIdentityTokenProvider,
)
from tests.conftest import MockResponse


async def _invoke_operation(client: MondayClient, operation: str):
    """Invoke a Monday operation by name for shared tests."""
    if operation == "create_item":
        return await client.create_item_async(input=CreateItemInput())
    if operation == "duplicate_board":
        return await client.duplicate_board_async(input=DuplicateBoardInput())
    if operation == "create_board":
        return await client.create_board_async(input=CreateBoardInput())
    if operation == "create_column":
        return await client.create_column_async(input=CreateColumnInput())
    if operation == "create_group":
        return await client.create_group_async(input=CreateGroupInput())
    if operation == "update_item_column":
        return await client.update_item_column_async(input=UpdateItemColumnInput())
    if operation == "update_multiple_item_columns":
        return await client.update_multiple_item_columns_async(
            input=UpdateMultipleItemColumnsInput()
        )
    if operation == "move_item_to_group":
        return await client.move_item_to_group_async(input=MoveItemToGroupInput())
    if operation == "create_notification":
        return await client.create_notification_async(input=CreateNotificationInput())
    if operation == "create_subitem":
        return await client.create_subitem_async(input=CreateSubitemInput())
    if operation == "create_update":
        return await client.create_update_async(input=CreateUpdateInput())
    if operation == "create_workspace":
        return await client.create_workspace_async(input=CreateWorkspaceInput())
    if operation == "get_subitems":
        return await client.get_subitems_async(
            workspace_id="1", board_id="2", item_id="3"
        )
    if operation == "get_item_by_id":
        return await client.get_item_by_id_async(
            item_id="1", workspace_id="2", board_id="3"
        )
    if operation == "get_items":
        return await client.get_items_async(
            workspace_id="1", board_id="2", group_id="3"
        )
    if operation == "get_tags":
        return await client.get_tags_async()
    if operation == "get_users":
        return await client.get_users_async()
    if operation == "get_workspaces":
        return await client.get_workspaces_async()
    if operation == "get_boards":
        return await client.get_boards_async()
    if operation == "get_groups_for_get_items":
        return await client.get_groups_for_get_items_async(board_id="1")
    if operation == "get_columns_for_item_filtering":
        return await client.get_columns_for_item_filtering_async(board_id="1")
    if operation == "get_column_filter_operator":
        return await client.get_column_filter_operator_async(board_id="1")
    if operation == "get_column_names_schema":
        return await client.get_column_names_schema_async()
    if operation == "get_single_column_schema":
        return await client.get_single_column_schema_async()
    if operation == "get_column_names_schema_for_webhook":
        return await client.get_column_names_schema_for_webhook_async()
    if operation == "get_schema_for_get_items_action":
        return await client.get_schema_for_get_items_action_async()
    if operation == "get_column_names_schema_for_update_webhook":
        return await client.get_column_names_schema_for_update_webhook_async()
    if operation == "get_subitem_column_names":
        return await client.get_subitem_column_names_async(parent_board_id="1")
    if operation == "get_subitem_schema":
        return await client.get_subitem_schema_async(parent_board_id="1")

    raise ValueError(f"Unsupported operation '{operation}'.")


ALL_OPERATIONS = [
    "create_item",
    "duplicate_board",
    "create_board",
    "create_column",
    "create_group",
    "update_item_column",
    "update_multiple_item_columns",
    "move_item_to_group",
    "create_notification",
    "create_subitem",
    "create_update",
    "create_workspace",
    "get_subitems",
    "get_item_by_id",
    "get_items",
    "get_tags",
    "get_users",
    "get_workspaces",
    "get_boards",
    "get_groups_for_get_items",
    "get_columns_for_item_filtering",
    "get_column_filter_operator",
    "get_column_names_schema",
    "get_single_column_schema",
    "get_column_names_schema_for_webhook",
    "get_schema_for_get_items_action",
    "get_column_names_schema_for_update_webhook",
    "get_subitem_column_names",
    "get_subitem_schema",
]


class TestMondayClientInitialization:
    """Tests for MondayClient initialization."""

    def test_init_with_valid_url_and_defaults(self):
        """Test initialization with valid URL and default parameters."""
        client = MondayClient("https://example.azure.com/connections/test")

        assert client._connection_runtime_url == "https://example.azure.com/connections/test"
        assert client.connector_name == "monday"
        assert isinstance(client._http_client._token_provider, ManagedIdentityTokenProvider)

    def test_init_with_trailing_slash(self):
        """Test that trailing slash is removed from URL."""
        client = MondayClient("https://example.azure.com/connections/test/")

        assert client._connection_runtime_url == "https://example.azure.com/connections/test"

    def test_init_with_custom_token_provider(self, mock_token_provider):
        """Test initialization with custom token provider."""
        client = MondayClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider,
        )

        assert client._http_client._token_provider is mock_token_provider

    def test_init_with_custom_options(self, mock_token_provider):
        """Test initialization with custom options."""
        options = ConnectorClientOptions(timeout_seconds=60.0, max_retry_attempts=5)
        client = MondayClient(
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
            MondayClient("")

    def test_init_with_none_url_raises_error(self):
        """Test that None URL raises ValueError."""
        with pytest.raises(ValueError, match="connection_runtime_url cannot be None or empty"):
            MondayClient(None)

    def test_connector_name_property(self, mock_token_provider):
        """Test connector_name property returns 'monday'."""
        client = MondayClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider,
        )

        assert client.connector_name == "monday"


class TestMondayClientLifecycle:
    """Tests for MondayClient lifecycle methods."""

    @pytest.mark.asyncio
    async def test_close(self, mock_token_provider):
        """Test close method calls http_client.close."""
        client = MondayClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider,
        )

        with patch.object(client._http_client, "close", new_callable=AsyncMock) as mock_close:
            await client.close()
            mock_close.assert_called_once()

    @pytest.mark.asyncio
    async def test_context_manager(self, mock_token_provider):
        """Test async context manager functionality."""
        with patch.object(MondayClient, "close", new_callable=AsyncMock) as mock_close:
            async with MondayClient(
                "https://example.azure.com/connections/test",
                token_provider=mock_token_provider,
            ) as client:
                assert isinstance(client, MondayClient)

            mock_close.assert_called_once()


class TestMondayClientOperations:
    """Tests for MondayClient operations against expected HTTP calls."""

    @pytest.mark.asyncio
    async def test_create_item_success(self, mock_token_provider):
        """Test create item issues a POST to executePowerAutomateAction/CreateItem."""
        client = MondayClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider,
        )
        mock_response = MockResponse(status=200, text='{"data": {"id": "9"}}')

        with patch.object(
            client._http_client,
            "send_async",
            new_callable=AsyncMock,
            return_value=mock_response,
        ) as mock_send:
            result = await client.create_item_async(input=CreateItemInput())

            method, path = mock_send.call_args[0][0], mock_send.call_args[0][1]
            assert method == "POST"
            assert path.endswith("/executePowerAutomateAction/CreateItem")
            assert mock_send.call_args.kwargs["body"] is not None
            assert result == {"data": {"id": "9"}}

    @pytest.mark.asyncio
    async def test_update_item_column_success(self, mock_token_provider):
        """Test update item column POSTs to executePowerAutomateAction/UpdateItemColumn."""
        client = MondayClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider,
        )
        mock_response = MockResponse(status=200, text='{"data": {"id": "5"}}')

        with patch.object(
            client._http_client,
            "send_async",
            new_callable=AsyncMock,
            return_value=mock_response,
        ) as mock_send:
            result = await client.update_item_column_async(input=UpdateItemColumnInput())

            method, path = mock_send.call_args[0][0], mock_send.call_args[0][1]
            assert method == "POST"
            assert path.endswith("/executePowerAutomateAction/UpdateItemColumn")
            assert mock_send.call_args.kwargs["body"] is not None
            assert result == {"data": {"id": "5"}}

    @pytest.mark.asyncio
    async def test_get_tags_success(self, mock_token_provider):
        """Test get tags issues a GET to getData/getTagsV2."""
        client = MondayClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider,
        )
        mock_response = MockResponse(status=200, text='{"data": []}')

        with patch.object(
            client._http_client,
            "send_async",
            new_callable=AsyncMock,
            return_value=mock_response,
        ) as mock_send:
            result = await client.get_tags_async()

            method, path = mock_send.call_args[0][0], mock_send.call_args[0][1]
            assert method == "GET"
            assert path.endswith("/getData/getTagsV2")
            assert result == {"data": []}

    @pytest.mark.asyncio
    async def test_get_boards_includes_query_parameter(self, mock_token_provider):
        """Test get boards appends the workspaceId query parameter."""
        client = MondayClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider,
        )
        mock_response = MockResponse(status=200, text='{"data": []}')

        with patch.object(
            client._http_client,
            "send_async",
            new_callable=AsyncMock,
            return_value=mock_response,
        ) as mock_send:
            await client.get_boards_async(workspace_id="42")

            method, path = mock_send.call_args[0][0], mock_send.call_args[0][1]
            assert method == "GET"
            assert "/getData/getBoards" in path
            assert "workspaceId=42" in path

    @pytest.mark.asyncio
    async def test_get_subitems_includes_query_parameters(self, mock_token_provider):
        """Test get subitems appends the item lookup query parameters."""
        client = MondayClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider,
        )
        mock_response = MockResponse(status=200, text='{"data": []}')

        with patch.object(
            client._http_client,
            "send_async",
            new_callable=AsyncMock,
            return_value=mock_response,
        ) as mock_send:
            await client.get_subitems_async(workspace_id="1", board_id="2", item_id="3")

            method, path = mock_send.call_args[0][0], mock_send.call_args[0][1]
            assert method == "GET"
            assert "/getData/getSubitems" in path
            assert "itemId=3" in path

    @pytest.mark.asyncio
    async def test_empty_response_body_returns_none(self, mock_token_provider):
        """Test a 2xx response with no body returns None."""
        client = MondayClient(
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
            result = await client.create_item_async(input=CreateItemInput())

            assert result is None


class TestMondayClientErrorHandling:
    """Error handling tests that ensure all methods raise ConnectorException."""

    @pytest.mark.asyncio
    @pytest.mark.parametrize("operation", ALL_OPERATIONS)
    async def test_error_response_raises_exception_for_all_operations(
        self,
        mock_token_provider,
        operation,
    ):
        """Test non-2xx responses raise ConnectorException for every operation."""
        client = MondayClient(
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


class TestMondayTriggerOperations:
    """Tests for the module-level TRIGGER_OPERATIONS registry."""

    def test_all_expected_triggers_registered(self):
        """Test the registry exposes every Monday webhook trigger operation."""
        assert set(TRIGGER_OPERATIONS) == {
            "WebhookCreateItem",
            "WebhookCreateUpdate",
            "WebhookChangeName",
            "WebhookChangeSubitemName",
            "WebhookCreateSubitem",
            "WebhookColumnChanges",
            "WebhookAnyColumnChanges",
            "WebhookSubitemColumnChanges",
        }

    @pytest.mark.parametrize("operation_id", list(TRIGGER_OPERATIONS))
    def test_trigger_metadata_shape(self, operation_id):
        """Test each trigger entry carries the expected metadata fields."""
        trigger = TRIGGER_OPERATIONS[operation_id]

        assert trigger["operation_id"] == operation_id
        assert trigger["method"] == "post"
        assert trigger["path"].startswith("/{connectionId}/")
        assert "callback_payload_type" in trigger
        assert isinstance(trigger["required_parameters"], list)

    def test_triggers_are_not_client_methods(self):
        """Test trigger operations are not emitted as callable client methods."""
        assert not hasattr(MondayClient, "webhook_create_item_async")
        assert not hasattr(MondayClient, "on_create_item_async")


class TestMondayTypeSerialization:
    """Tests for Monday connector dataclass defaults."""

    def test_response_dataclasses_initialize_expected_defaults(self):
        """Test generated response dataclasses initialize with None defaults."""
        assert CreateItemResponse().data is None
        assert GetTagsResponse().data is None
        assert GetUsersResponse().data is None
        assert GetWorkspacesResponse().data is None
        assert GetSubitemSchemaResponse().schema is None

    def test_request_dataclasses_instantiate(self):
        """Test generated request dataclasses instantiate without arguments."""
        assert CreateItemInput().item_name is None
        assert CreateBoardInput().board_name is None
        assert CreateNotificationInput().text is None
        assert CreateWorkspaceInput() is not None
