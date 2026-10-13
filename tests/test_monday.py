# Copyright (c) Microsoft Corporation. All rights reserved.

"""Unit tests for MondayClient."""

from unittest.mock import AsyncMock, patch

import pytest

from azure.core.credentials import AzureKeyCredential
import azure.connectors.monday as monday_module
from azure.connectors.aio.monday import MondayClient
from azure.connectors.monday import (
    CreateBoardInput,
    CreateItemInput,
    CreateItemResponse,
    CreateNotificationInput,
    CreateWorkspaceInput,
    GetSubitemSchemaResponse,
    GetTagsResponse,
    GetUsersResponse,
    GetWorkspacesResponse,
    UpdateItemColumnInput,
    TRIGGER_OPERATIONS,
)
from azure.connectors.sdk import (
    ConnectorException,
)
from tests.conftest import MockResponse
from tests.generated_connector_test_utils import (
    get_generated_operations,
    invoke_generated_operation,
    model_instance,
    resolve_generated_result,
)


async def _invoke_operation(client: MondayClient, operation: str):
    """Invoke a Monday operation by name for shared tests."""
    return await invoke_generated_operation(client, operation, monday_module)


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
    "list_boards",
    "list_groups_for_get_items",
    "list_columns_for_item_filtering",
    "list_column_filter_operator",
    "get_column_names_schema",
    "get_single_column_schema",
    "get_column_names_schema_for_webhook",
    "get_schema_for_get_items_action",
    "get_column_names_schema_for_update_webhook",
    "get_column_names_schema_for_item_name_change_webhook",
    "get_column_names_schema_for_subitem_name_change_webhook",
    "get_column_names_schema_for_column_changes_webhook",
    "get_subitem_column_names",
    "get_subitem_schema",
]


class TestMondayClientInitialization:
    """Tests for MondayClient initialization."""

    def test_init_with_valid_url_and_defaults(self):
        """Test initialization with valid URL and default parameters."""
        client = MondayClient("https://example.azure.com/connections/test",
                              AzureKeyCredential("test-key"))

        assert client._connection_runtime_url == "https://example.azure.com/connections/test"
        assert client.connector_name == "monday"
        assert isinstance(client._http_client._credential, AzureKeyCredential)

    def test_init_with_trailing_slash(self):
        """Test that trailing slash is removed from URL."""
        client = MondayClient("https://example.azure.com/connections/test/",
                              AzureKeyCredential("test-key"))

        assert client._connection_runtime_url == "https://example.azure.com/connections/test"

    def test_init_with_custom_credential(self, mock_credential):
        """Test initialization with custom token provider."""
        client = MondayClient(
            "https://example.azure.com/connections/test",
            credential=mock_credential,
        )

        assert client._http_client._credential is mock_credential

    def test_init_with_custom_settings(self, mock_credential):
        """Test initialization with custom pipeline settings."""
        client = MondayClient(
            "https://example.azure.com/connections/test",
            credential=mock_credential,
            timeout=60.0,
            max_retry_attempts=5,
        )
        assert client._http_client._timeout_seconds == 60.0

    def test_init_with_empty_url_raises_error(self):
        """Test that empty URL raises ValueError."""
        with pytest.raises(ValueError, match="connection_runtime_url cannot be None or empty"):
            MondayClient("", AzureKeyCredential("test-key"))

    def test_init_with_none_url_raises_error(self):
        """Test that None URL raises ValueError."""
        with pytest.raises(ValueError, match="connection_runtime_url cannot be None or empty"):
            MondayClient(None, AzureKeyCredential("test-key"))

    def test_connector_name_property(self, mock_credential):
        """Test connector_name property returns 'monday'."""
        client = MondayClient(
            "https://example.azure.com/connections/test",
            credential=mock_credential,
        )

        assert client.connector_name == "monday"


class TestMondayClientLifecycle:
    """Tests for MondayClient lifecycle methods."""

    @pytest.mark.asyncio
    async def test_close(self, mock_credential):
        """Test close method calls http_client.close."""
        client = MondayClient(
            "https://example.azure.com/connections/test",
            credential=mock_credential,
        )

        with patch.object(client._http_client, "close", new_callable=AsyncMock) as mock_close:
            await client.close()
            mock_close.assert_called_once()

    @pytest.mark.asyncio
    async def test_context_manager(self, mock_credential):
        """Test async context manager functionality."""
        with patch.object(MondayClient, "close", new_callable=AsyncMock) as mock_close:
            async with MondayClient(
                "https://example.azure.com/connections/test",
                credential=mock_credential,
            ) as client:
                assert isinstance(client, MondayClient)

            mock_close.assert_called_once()


class TestMondayClientOperations:
    """Tests for MondayClient operations against expected HTTP calls."""

    def test_all_generated_operations_are_covered(self):
        """Test the expected generated operation surface."""
        assert get_generated_operations(MondayClient) == set(ALL_OPERATIONS)

    @pytest.mark.asyncio
    async def test_create_item_success(self, mock_credential):
        """Test create item issues a POST to executePowerAutomateAction/CreateItem."""
        client = MondayClient(
            "https://example.azure.com/connections/test",
            credential=mock_credential,
        )
        mock_response = MockResponse(status=200, text='{"data": {"id": "9"}}')

        with patch.object(
            client._http_client,
            "send",
            new_callable=AsyncMock,
            return_value=mock_response,
        ) as mock_send:
            result = await client.create_item(
                input=model_instance(CreateItemInput),
            )

            method, path = mock_send.call_args[0][0], mock_send.call_args[0][1]
            assert method == "POST"
            assert path.endswith("/executePowerAutomateAction/CreateItem")
            assert mock_send.call_args.kwargs["body"] is not None
            assert result == {"data": {"id": "9"}}

    @pytest.mark.asyncio
    async def test_update_item_column_success(self, mock_credential):
        """Test update item column POSTs to executePowerAutomateAction/UpdateItemColumn."""
        client = MondayClient(
            "https://example.azure.com/connections/test",
            credential=mock_credential,
        )
        mock_response = MockResponse(status=200, text='{"data": {"id": "5"}}')

        with patch.object(
            client._http_client,
            "send",
            new_callable=AsyncMock,
            return_value=mock_response,
        ) as mock_send:
            result = await client.update_item_column(
                input=model_instance(UpdateItemColumnInput),
            )

            method, path = mock_send.call_args[0][0], mock_send.call_args[0][1]
            assert method == "POST"
            assert path.endswith("/executePowerAutomateAction/UpdateItemColumn")
            assert mock_send.call_args.kwargs["body"] is not None
            assert result == {"data": {"id": "5"}}

    @pytest.mark.asyncio
    async def test_get_tags_success(self, mock_credential):
        """Test get tags issues a GET to getData/getTagsV2."""
        client = MondayClient(
            "https://example.azure.com/connections/test",
            credential=mock_credential,
        )
        mock_response = MockResponse(status=200, text='{"data": []}')

        with patch.object(
            client._http_client,
            "send",
            new_callable=AsyncMock,
            return_value=mock_response,
        ) as mock_send:
            result = await client.get_tags()

            method, path = mock_send.call_args[0][0], mock_send.call_args[0][1]
            assert method == "GET"
            assert path.endswith("/getData/getTagsV2")
            assert result == {"data": []}

    @pytest.mark.asyncio
    async def test_list_boards_includes_query_parameter(self, mock_credential):
        """Test list boards appends the workspaceId query parameter."""
        client = MondayClient(
            "https://example.azure.com/connections/test",
            credential=mock_credential,
        )
        mock_response = MockResponse(status=200, text='{"data": []}')

        with patch.object(
            client._http_client,
            "send",
            new_callable=AsyncMock,
            return_value=mock_response,
        ) as mock_send:
            await resolve_generated_result(
                client.list_boards(workspace_id="42")
            )

            method, path = mock_send.call_args[0][0], mock_send.call_args[0][1]
            assert method == "GET"
            assert "/getData/getBoards" in path
            assert "workspaceId=42" in path

    @pytest.mark.asyncio
    async def test_get_subitems_includes_query_parameters(self, mock_credential):
        """Test get subitems appends the item lookup query parameters."""
        client = MondayClient(
            "https://example.azure.com/connections/test",
            credential=mock_credential,
        )
        mock_response = MockResponse(status=200, text='{"data": []}')

        with patch.object(
            client._http_client,
            "send",
            new_callable=AsyncMock,
            return_value=mock_response,
        ) as mock_send:
            await client.get_subitems(workspace_id="1", board_id="2", item_id="3")

            method, path = mock_send.call_args[0][0], mock_send.call_args[0][1]
            assert method == "GET"
            assert "/getData/getSubitems" in path
            assert "itemId=3" in path

    @pytest.mark.asyncio
    async def test_empty_response_body_returns_none(self, mock_credential):
        """Test a 2xx response with no body returns None."""
        client = MondayClient(
            "https://example.azure.com/connections/test",
            credential=mock_credential,
        )
        mock_response = MockResponse(status=200, text="")

        with patch.object(
            client._http_client,
            "send",
            new_callable=AsyncMock,
            return_value=mock_response,
        ):
            result = await client.create_item(
                input=model_instance(CreateItemInput),
            )

            assert result is None


class TestMondayClientErrorHandling:
    """Error handling tests that ensure all methods raise ConnectorException."""

    @pytest.mark.asyncio
    @pytest.mark.parametrize("operation", ALL_OPERATIONS)
    async def test_error_response_raises_exception_for_all_operations(
        self,
        mock_credential,
        operation,
    ):
        """Test non-2xx responses raise ConnectorException for every operation."""
        client = MondayClient(
            "https://example.azure.com/connections/test",
            credential=mock_credential,
        )
        mock_response = MockResponse(status=500, text='{"error":"server failure"}')

        with patch.object(
            client._http_client,
            "send",
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
    """Tests for Monday connector dataclass construction."""

    def test_response_dataclasses_initialize_expected_defaults(self):
        """Test generated response dataclasses initialize with None defaults."""
        assert CreateItemResponse().data is None
        assert GetTagsResponse().data is None
        assert GetUsersResponse().data is None
        assert GetWorkspacesResponse().data is None
        assert GetSubitemSchemaResponse().schema is None

    def test_request_dataclasses_instantiate(self):
        """Test generated request dataclasses populate required fields."""
        assert model_instance(CreateItemInput).item_name is not None
        assert model_instance(CreateBoardInput).board_name is not None
        assert model_instance(CreateNotificationInput).text is not None
        assert model_instance(CreateWorkspaceInput).name is not None
