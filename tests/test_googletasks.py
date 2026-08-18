# Copyright (c) Microsoft Corporation. All rights reserved.

"""Unit tests for GoogletasksClient."""

import pytest
from unittest.mock import AsyncMock, patch

from azure.connectors.googletasks import (
    GoogletasksClient,
    TRIGGER_OPERATIONS,
    TaskCreate,
    TaskList,
    TaskListCreate,
    TaskListEntry,
    TaskListList,
    TaskObject,
)
from azure.connectors.sdk import (
    ConnectorClientOptions,
    ConnectorException,
    ManagedIdentityTokenProvider,
)
from tests.conftest import MockResponse


async def _invoke_operation(client: GoogletasksClient, operation: str):
    """Invoke a Google Tasks operation by name for shared tests."""
    if operation == "list_task_lists":
        return await client.list_task_lists_async()
    if operation == "create_task_list":
        return await client.create_task_list_async(input=TaskListCreate(title="Work"))
    if operation == "list_tasks":
        return await client.list_tasks_async(task_list_id="list123")
    if operation == "craete_task":
        return await client.craete_task_async(
            input=TaskCreate(title="Buy milk"),
            task_list_id="list123",
        )
    if operation == "list_task":
        return await client.list_task_async(task_list_id="list123", task_id="task123")
    raise ValueError(f"Unsupported operation '{operation}'.")


class TestGoogletasksClientInitialization:
    """Tests for GoogletasksClient initialization."""

    def test_init_with_valid_url_and_defaults(self):
        """Test initialization with valid URL and default parameters."""
        client = GoogletasksClient("https://example.azure.com/connections/test")

        assert client._connection_runtime_url == "https://example.azure.com/connections/test"
        assert client.connector_name == "googletasks"
        assert isinstance(client._http_client._token_provider, ManagedIdentityTokenProvider)

    def test_init_with_trailing_slash(self):
        """Test that trailing slash is removed from URL."""
        client = GoogletasksClient("https://example.azure.com/connections/test/")

        assert client._connection_runtime_url == "https://example.azure.com/connections/test"

    def test_init_with_custom_token_provider(self, mock_token_provider):
        """Test initialization with custom token provider."""
        client = GoogletasksClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider,
        )

        assert client._http_client._token_provider is mock_token_provider

    def test_init_with_custom_options(self, mock_token_provider):
        """Test initialization with custom options."""
        options = ConnectorClientOptions(timeout_seconds=60.0, max_retry_attempts=5)
        client = GoogletasksClient(
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
            GoogletasksClient("")

    def test_init_with_none_url_raises_error(self):
        """Test that None URL raises ValueError."""
        with pytest.raises(ValueError, match="connection_runtime_url cannot be None or empty"):
            GoogletasksClient(None)

    def test_connector_name_property(self, mock_token_provider):
        """Test connector_name property returns 'googletasks'."""
        client = GoogletasksClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider,
        )

        assert client.connector_name == "googletasks"


class TestGoogletasksClientLifecycle:
    """Tests for GoogletasksClient lifecycle methods."""

    @pytest.mark.asyncio
    async def test_close(self, mock_token_provider):
        """Test close method calls http_client.close."""
        client = GoogletasksClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider,
        )

        with patch.object(client._http_client, "close", new_callable=AsyncMock) as mock_close:
            await client.close()
            mock_close.assert_called_once()

    @pytest.mark.asyncio
    async def test_context_manager(self, mock_token_provider):
        """Test async context manager functionality."""
        with patch.object(GoogletasksClient, "close", new_callable=AsyncMock) as mock_close:
            async with GoogletasksClient(
                "https://example.azure.com/connections/test",
                token_provider=mock_token_provider,
            ) as client:
                assert isinstance(client, GoogletasksClient)

            mock_close.assert_called_once()


class TestGoogletasksClientMethods:
    """Success path tests for representative Google Tasks methods."""

    @pytest.mark.asyncio
    async def test_list_task_lists_success(self, mock_token_provider):
        """Test list_task_lists_async returns parsed JSON."""
        client = GoogletasksClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider,
        )
        mock_response = MockResponse(status=200, text='{"items":[{"id":"list123"}]}')

        with patch.object(
            client._http_client,
            "send_async",
            new_callable=AsyncMock,
            return_value=mock_response,
        ) as mock_send:
            result = await client.list_task_lists_async()

            assert len(result["items"]) == 1
            assert "/users/@me/lists" in mock_send.call_args[0][1]

    @pytest.mark.asyncio
    async def test_create_task_list_success(self, mock_token_provider):
        """Test create_task_list_async sends body and returns parsed JSON."""
        client = GoogletasksClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider,
        )
        mock_response = MockResponse(status=201, text='{"id":"list123","title":"Work"}')

        with patch.object(
            client._http_client,
            "send_async",
            new_callable=AsyncMock,
            return_value=mock_response,
        ) as mock_send:
            result = await client.create_task_list_async(input=TaskListCreate(title="Work"))

            assert result["id"] == "list123"
            assert isinstance(mock_send.call_args.kwargs["body"], TaskListCreate)

    @pytest.mark.asyncio
    async def test_craete_task_success(self, mock_token_provider):
        """Test craete_task_async preserves its operationId spelling."""
        client = GoogletasksClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider,
        )
        mock_response = MockResponse(status=201, text='{"id":"task123","title":"Buy milk"}')

        with patch.object(
            client._http_client,
            "send_async",
            new_callable=AsyncMock,
            return_value=mock_response,
        ) as mock_send:
            result = await client.craete_task_async(
                input=TaskCreate(title="Buy milk"),
                task_list_id="list123",
            )

            assert result["id"] == "task123"
            assert "/lists/list123/tasks" in mock_send.call_args[0][1]

    @pytest.mark.asyncio
    async def test_list_task_success(self, mock_token_provider):
        """Test list_task_async uses list and task identifiers."""
        client = GoogletasksClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider,
        )
        mock_response = MockResponse(status=200, text='{"id":"task123"}')

        with patch.object(
            client._http_client,
            "send_async",
            new_callable=AsyncMock,
            return_value=mock_response,
        ) as mock_send:
            result = await client.list_task_async(task_list_id="list123", task_id="task123")

            assert result["id"] == "task123"
            assert "/lists/list123/tasks/task123" in mock_send.call_args[0][1]


class TestGoogletasksClientErrorHandling:
    """Error handling tests that ensure all methods raise ConnectorException."""

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "operation",
        [
            "list_task_lists",
            "create_task_list",
            "list_tasks",
            "craete_task",
            "list_task",
        ],
    )
    async def test_error_response_raises_exception_for_all_operations(
        self,
        mock_token_provider,
        operation,
    ):
        """Test non-2xx responses raise ConnectorException for every operation."""
        client = GoogletasksClient(
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


class TestGoogletasksTriggerOperations:
    """Tests for Google Tasks trigger registration metadata."""

    def test_triggers_are_registered_without_callable_methods(self):
        """Test polling triggers are metadata-only operations."""
        assert set(TRIGGER_OPERATIONS) == {
            "OnNewTaskList",
            "OnNewTaskInList",
            "OnDueTaskInList",
            "OnCompletedTaskInListV2",
        }
        assert TRIGGER_OPERATIONS["OnNewTaskInList"]["required_parameters"] == [
            "taskListId"
        ]
        assert not hasattr(GoogletasksClient, "on_new_task_in_list_async")
        assert not hasattr(GoogletasksClient, "on_completed_task_in_list_async")


class TestGoogletasksTypeSerialization:
    """Tests for Googletasks connector dataclass defaults."""

    def test_dataclass_instances_initialize_expected_defaults(self):
        """Test generated dataclasses initialize with expected default values."""
        task_list_list = TaskListList()
        task_list_entry = TaskListEntry()
        task_list = TaskList()
        task_object = TaskObject()
        task_list_create = TaskListCreate()
        task_create = TaskCreate()

        assert task_list_list.items is None
        assert task_list_entry.id is None
        assert task_list.items is None
        assert task_object.id is None
        assert task_list_create.title is None
        assert task_create.title is None
