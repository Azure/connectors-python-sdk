# Copyright (c) Microsoft Corporation. All rights reserved.

"""Unit tests for TodoClient."""

from unittest.mock import AsyncMock, patch

import pytest

from azure.connectors.todo import (
    CreateToDo,
    CreateToDoList,
    TRIGGER_OPERATIONS,
    TodoClient,
    ToDoHtml,
    UpdateToDo,
)
from azure.connectors.sdk import (
    ConnectorClientOptions,
    ConnectorException,
    ManagedIdentityTokenProvider,
)
from azure.connectors.sdk.serialization import to_wire
from tests.conftest import MockResponse


class TestTodoClientInitialization:
    """Tests for TodoClient initialization."""

    def test_init_with_valid_url_and_defaults(self):
        """Test initialization with valid URL and default parameters."""
        client = TodoClient("https://example.azure.com/connections/test")

        assert client._connection_runtime_url == "https://example.azure.com/connections/test"
        assert client.connector_name == "todo"
        assert isinstance(client._http_client._token_provider, ManagedIdentityTokenProvider)

    def test_init_with_trailing_slash(self):
        """Test that trailing slash is removed from URL."""
        client = TodoClient("https://example.azure.com/connections/test/")

        assert client._connection_runtime_url == "https://example.azure.com/connections/test"

    def test_init_with_custom_token_provider(self, mock_token_provider):
        """Test initialization with custom token provider."""
        client = TodoClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider,
        )

        assert client._http_client._token_provider is mock_token_provider

    def test_init_with_custom_options(self, mock_token_provider):
        """Test initialization with custom options."""
        options = ConnectorClientOptions(timeout_seconds=60.0, max_retry_attempts=5)
        client = TodoClient(
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
            TodoClient("")

    def test_init_with_none_url_raises_error(self):
        """Test that None URL raises ValueError."""
        with pytest.raises(ValueError, match="connection_runtime_url cannot be None or empty"):
            TodoClient(None)

    def test_connector_name_property(self, mock_token_provider):
        """Test connector_name property returns 'todo'."""
        client = TodoClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider,
        )

        assert client.connector_name == "todo"


class TestTodoClientLifecycle:
    """Tests for TodoClient lifecycle methods."""

    @pytest.mark.asyncio
    async def test_close(self, mock_token_provider):
        """Test close method calls http_client.close."""
        client = TodoClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider,
        )

        with patch.object(client._http_client, "close", new_callable=AsyncMock) as mock_close:
            await client.close()
            mock_close.assert_called_once()

    @pytest.mark.asyncio
    async def test_context_manager(self, mock_token_provider):
        """Test async context manager functionality."""
        with patch.object(TodoClient, "close", new_callable=AsyncMock) as mock_close:
            async with TodoClient(
                "https://example.azure.com/connections/test",
                token_provider=mock_token_provider,
            ) as client:
                assert isinstance(client, TodoClient)

            mock_close.assert_called_once()


class TestTodoModelSerialization:
    """Tests for distinct Todo wire names that normalize alike."""

    def test_todo_html_preserves_colliding_ids(self):
        """Test that natural and OData IDs survive serialization together."""
        model = ToDoHtml(id="natural-id", id_2="odata-id")

        payload = to_wire(model)

        assert payload["id"] == "natural-id"
        assert payload["@odata.id"] == "odata-id"


class TestGetAllTodoListsAsync:
    """Tests for get_all_todo_lists_async method."""

    @pytest.mark.asyncio
    async def test_success(self, mock_token_provider):
        """Test successful listing of todo lists."""
        client = TodoClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider,
        )
        mock_response = MockResponse(status=200, text='{"value": [{"id": "list-1"}]}')

        with patch.object(
            client._http_client,
            "send_async",
            new_callable=AsyncMock,
            return_value=mock_response,
        ) as mock_send:
            result = await client.get_all_todo_lists_async()

            mock_send.assert_called_once()
            method, path = mock_send.call_args[0][0], mock_send.call_args[0][1]
            assert method == "GET"
            assert path.endswith("/lists")
            assert result is not None
            assert "value" in result

    @pytest.mark.asyncio
    async def test_error_response_raises_exception(self, mock_token_provider):
        """Test that error response raises ConnectorException."""
        client = TodoClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider,
        )
        mock_response = MockResponse(status=500, text='{"error": "Server error"}')

        with patch.object(
            client._http_client,
            "send_async",
            new_callable=AsyncMock,
            return_value=mock_response,
        ):
            with pytest.raises(ConnectorException):
                await client.get_all_todo_lists_async()


class TestGetTodoListAsync:
    """Tests for get_to_do_list_async method."""

    @pytest.mark.asyncio
    async def test_success_encodes_folder_id(self, mock_token_provider):
        """Test successful retrieval encodes the to-do list identifier."""
        client = TodoClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider,
        )
        mock_response = MockResponse(
            status=200,
            text='{"id": "list 1", "displayName": "Work"}',
        )

        with patch.object(
            client._http_client,
            "send_async",
            new_callable=AsyncMock,
            return_value=mock_response,
        ) as mock_send:
            result = await client.get_to_do_list_async(folder_id="list 1")

            mock_send.assert_called_once_with(
                "GET",
                "https://example.azure.com/connections/test/lists/list%201",
                body=None,
            )
            assert result == {"id": "list 1", "displayName": "Work"}

    @pytest.mark.asyncio
    async def test_error_response_raises_exception(self, mock_token_provider):
        """Test retrieval raises for a non-success response."""
        client = TodoClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider,
        )
        mock_response = MockResponse(status=404, text='{"error": "Not found"}')

        with patch.object(
            client._http_client,
            "send_async",
            new_callable=AsyncMock,
            return_value=mock_response,
        ):
            with pytest.raises(ConnectorException) as exc_info:
                await client.get_to_do_list_async(folder_id="missing-list")

            assert exc_info.value.status_code == 404


class TestCreateTodoListAsync:
    """Tests for create_to_do_list_async method."""

    @pytest.mark.asyncio
    async def test_success(self, mock_token_provider):
        """Test successful todo list creation."""
        client = TodoClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider,
        )
        payload = CreateToDoList(display_name="Work")
        mock_response = MockResponse(status=201, text='{"id": "list-1", "displayName": "Work"}')

        with patch.object(
            client._http_client,
            "send_async",
            new_callable=AsyncMock,
            return_value=mock_response,
        ) as mock_send:
            result = await client.create_to_do_list_async(input=payload)

            mock_send.assert_called_once()
            method, path = mock_send.call_args[0][0], mock_send.call_args[0][1]
            body = mock_send.call_args[1].get("body")
            assert method == "POST"
            assert path.endswith("/lists")
            assert body is payload
            assert result is not None

    @pytest.mark.asyncio
    async def test_error_response_raises_exception(self, mock_token_provider):
        """Test create list error path."""
        client = TodoClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider,
        )
        payload = CreateToDoList(display_name="Work")
        mock_response = MockResponse(status=400, text='{"error": "Bad request"}')

        with patch.object(
            client._http_client,
            "send_async",
            new_callable=AsyncMock,
            return_value=mock_response,
        ):
            with pytest.raises(ConnectorException):
                await client.create_to_do_list_async(input=payload)


class TestUpdateTodoListAsync:
    """Tests for update_to_do_list_async method."""

    @pytest.mark.asyncio
    async def test_success_encodes_folder_id_and_sends_body(self, mock_token_provider):
        """Test successful update encodes the identifier and sends the body."""
        client = TodoClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider,
        )
        payload = CreateToDoList(display_name="Updated work")
        mock_response = MockResponse(
            status=200,
            text='{"id": "list 1", "displayName": "Updated work"}',
        )

        with patch.object(
            client._http_client,
            "send_async",
            new_callable=AsyncMock,
            return_value=mock_response,
        ) as mock_send:
            result = await client.update_to_do_list_async(
                input=payload,
                folder_id="list 1",
            )

            mock_send.assert_called_once_with(
                "PATCH",
                "https://example.azure.com/connections/test/lists/list%201",
                body=payload,
            )
            assert result == {"id": "list 1", "displayName": "Updated work"}

    @pytest.mark.asyncio
    async def test_error_response_raises_exception(self, mock_token_provider):
        """Test update raises for a non-success response."""
        client = TodoClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider,
        )
        payload = CreateToDoList(display_name="Updated work")
        mock_response = MockResponse(status=400, text='{"error": "Bad request"}')

        with patch.object(
            client._http_client,
            "send_async",
            new_callable=AsyncMock,
            return_value=mock_response,
        ):
            with pytest.raises(ConnectorException) as exc_info:
                await client.update_to_do_list_async(
                    input=payload,
                    folder_id="missing-list",
                )

            assert exc_info.value.status_code == 400


class TestDeleteTodoListAsync:
    """Tests for delete_to_do_list_async method (DELETE)."""

    @pytest.mark.asyncio
    async def test_success(self, mock_token_provider):
        """Test successful to-do list deletion."""
        client = TodoClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider,
        )
        mock_response = MockResponse(status=204)

        with patch.object(
            client._http_client,
            "send_async",
            new_callable=AsyncMock,
            return_value=mock_response,
        ) as mock_send:
            result = await client.delete_to_do_list_async(folder_id="list 1")

            mock_send.assert_called_once_with(
                "DELETE",
                "https://example.azure.com/connections/test/lists/list%201",
                body=None,
            )
            assert result is None

    @pytest.mark.asyncio
    async def test_error_response_raises_exception(self, mock_token_provider):
        """Test to-do list deletion raises for a non-success response."""
        client = TodoClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider,
        )
        mock_response = MockResponse(status=404, text='{"error": "Not found"}')

        with patch.object(
            client._http_client,
            "send_async",
            new_callable=AsyncMock,
            return_value=mock_response,
        ):
            with pytest.raises(ConnectorException) as exc_info:
                await client.delete_to_do_list_async(folder_id="missing-list")

            assert exc_info.value.status_code == 404


class TestGetTodoAsync:
    """Tests for get_to_do_async method."""

    @pytest.mark.asyncio
    async def test_success_encodes_folder_and_todo_ids(self, mock_token_provider):
        """Test successful retrieval encodes both route identifiers."""
        client = TodoClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider,
        )
        mock_response = MockResponse(
            status=200,
            text='{"id": "task 1", "title": "Buy milk"}',
        )

        with patch.object(
            client._http_client,
            "send_async",
            new_callable=AsyncMock,
            return_value=mock_response,
        ) as mock_send:
            result = await client.get_to_do_async(
                folder_id="list 1",
                id="task 1",
            )

            mock_send.assert_called_once_with(
                "GET",
                "https://example.azure.com/connections/test/lists/list%201/tasks/task%201",
                body=None,
            )
            assert result == {"id": "task 1", "title": "Buy milk"}

    @pytest.mark.asyncio
    async def test_error_response_raises_exception(self, mock_token_provider):
        """Test retrieval raises for a non-success response."""
        client = TodoClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider,
        )
        mock_response = MockResponse(status=404, text='{"error": "Not found"}')

        with patch.object(
            client._http_client,
            "send_async",
            new_callable=AsyncMock,
            return_value=mock_response,
        ):
            with pytest.raises(ConnectorException) as exc_info:
                await client.get_to_do_async(
                    folder_id="list-1",
                    id="missing-task",
                )

            assert exc_info.value.status_code == 404


class TestCreateAndUpdateTodoAsync:
    """Tests for create_to_do_async and update_to_do_async methods."""

    @pytest.mark.asyncio
    async def test_create_to_do_success(self, mock_token_provider):
        """Test successful to-do creation."""
        client = TodoClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider,
        )
        payload = CreateToDo(title="Buy milk", status="notStarted")
        mock_response = MockResponse(status=201, text='{"id": "task-1", "title": "Buy milk"}')

        with patch.object(
            client._http_client,
            "send_async",
            new_callable=AsyncMock,
            return_value=mock_response,
        ) as mock_send:
            result = await client.create_to_do_async(input=payload, folder_id="list-1")

            mock_send.assert_called_once()
            method, path = mock_send.call_args[0][0], mock_send.call_args[0][1]
            body = mock_send.call_args[1].get("body")
            assert method == "POST"
            assert "/lists/list-1/tasks" in path
            assert body is payload
            assert result is not None

    @pytest.mark.asyncio
    async def test_update_to_do_success(self, mock_token_provider):
        """Test successful to-do update."""
        client = TodoClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider,
        )
        payload = UpdateToDo(title="Buy milk and eggs", status="inProgress")
        mock_response = MockResponse(
            status=200, text='{"id": "task-1", "title": "Buy milk and eggs"}')

        with patch.object(
            client._http_client,
            "send_async",
            new_callable=AsyncMock,
            return_value=mock_response,
        ) as mock_send:
            result = await client.update_to_do_async(input=payload, folder_id="list-1", id="task-1")

            mock_send.assert_called_once()
            method, path = mock_send.call_args[0][0], mock_send.call_args[0][1]
            body = mock_send.call_args[1].get("body")
            assert method == "PATCH"
            assert "/lists/list-1/tasks/task-1" in path
            assert body is payload
            assert result is not None


class TestDeleteTodoAsync:
    """Tests for delete_to_do_async method (DELETE)."""

    @pytest.mark.asyncio
    async def test_success(self, mock_token_provider):
        """Test successful to-do deletion."""
        client = TodoClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider,
        )
        mock_response = MockResponse(status=204)

        with patch.object(
            client._http_client,
            "send_async",
            new_callable=AsyncMock,
            return_value=mock_response,
        ) as mock_send:
            result = await client.delete_to_do_async(
                folder_id="list 1",
                id="task 1",
            )

            mock_send.assert_called_once_with(
                "DELETE",
                "https://example.azure.com/connections/test/lists/list%201/tasks/task%201",
                body=None,
            )
            assert result is None

    @pytest.mark.asyncio
    async def test_error_response_raises_exception(self, mock_token_provider):
        """Test to-do deletion raises for a non-success response."""
        client = TodoClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider,
        )
        mock_response = MockResponse(status=500, text='{"error": "Server error"}')

        with patch.object(
            client._http_client,
            "send_async",
            new_callable=AsyncMock,
            return_value=mock_response,
        ):
            with pytest.raises(ConnectorException) as exc_info:
                await client.delete_to_do_async(
                    folder_id="list-1",
                    id="task-1",
                )

            assert exc_info.value.status_code == 500


class TestListTodosByFolderAsync:
    """Tests for list_to_dos_by_folder_async method."""

    @pytest.mark.asyncio
    async def test_success_with_top_query(self, mock_token_provider):
        """Test list-to-dos query parameter handling."""
        client = TodoClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider,
        )
        mock_response = MockResponse(status=200, text='{"value": [{"id": "task-1"}]}')

        with patch.object(
            client._http_client,
            "send_async",
            new_callable=AsyncMock,
            return_value=mock_response,
        ) as mock_send:
            result = await client.list_to_dos_by_folder_async(folder_id="list-1", top="10")

            mock_send.assert_called_once()
            method, path = mock_send.call_args[0][0], mock_send.call_args[0][1]
            assert method == "GET"
            assert "/lists/list-1/tasks" in path
            assert "$top=10" in path
            assert result is not None


class TestTodoTriggerOperations:
    """Tests for To Do trigger metadata."""

    @pytest.mark.parametrize(
        ("operation_id", "route"),
        [
            ("OnNewToDoInFolderV2", "onNewToDoInFolder"),
            ("OnUpdateToDoInFolderV2", "onUpdateToDoInFolder"),
        ],
    )
    def test_trigger_operation_metadata(self, operation_id, route):
        """Test polling triggers expose their registration contract."""
        trigger = TRIGGER_OPERATIONS[operation_id]

        assert trigger["operation_id"] == operation_id
        assert trigger["path"] == f"/{{connectionId}}/v2/trigger/{route}/{{folderId}}"
        assert trigger["method"] == "get"
        assert trigger["required_parameters"] == ["folderId"]
        assert trigger["callback_payload_type"] == "ToDo"
