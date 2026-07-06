# Copyright (c) Microsoft Corporation. All rights reserved.

"""Unit tests for TodoClient."""

from unittest.mock import AsyncMock, patch

import pytest

from azure.connectors.todo import TodoClient, CreateToDoListV2, CreateToDoV2, UpdateToDoV2
from azure.connectors.sdk import (
    ConnectorClientOptions,
    ConnectorException,
    ManagedIdentityTokenProvider,
)
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

        with patch.object(client._http_client, "send_async", new_callable=AsyncMock, return_value=mock_response) as mock_send:
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

        with patch.object(client._http_client, "send_async", new_callable=AsyncMock, return_value=mock_response):
            with pytest.raises(ConnectorException):
                await client.get_all_todo_lists_async()


class TestCreateTodoListAsync:
    """Tests for create_to_do_list_async method."""

    @pytest.mark.asyncio
    async def test_success(self, mock_token_provider):
        """Test successful todo list creation."""
        client = TodoClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider,
        )
        payload = CreateToDoListV2(display_name="Work")
        mock_response = MockResponse(status=201, text='{"id": "list-1", "displayName": "Work"}')

        with patch.object(client._http_client, "send_async", new_callable=AsyncMock, return_value=mock_response) as mock_send:
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
        payload = CreateToDoListV2(display_name="Work")
        mock_response = MockResponse(status=400, text='{"error": "Bad request"}')

        with patch.object(client._http_client, "send_async", new_callable=AsyncMock, return_value=mock_response):
            with pytest.raises(ConnectorException):
                await client.create_to_do_list_async(input=payload)


class TestCreateAndUpdateTodoAsync:
    """Tests for create_to_do_async and update_to_do_async methods."""

    @pytest.mark.asyncio
    async def test_create_to_do_success(self, mock_token_provider):
        """Test successful to-do creation."""
        client = TodoClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider,
        )
        payload = CreateToDoV2(title="Buy milk", status="notStarted")
        mock_response = MockResponse(status=201, text='{"id": "task-1", "title": "Buy milk"}')

        with patch.object(client._http_client, "send_async", new_callable=AsyncMock, return_value=mock_response) as mock_send:
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
        payload = UpdateToDoV2(title="Buy milk and eggs", status="inProgress")
        mock_response = MockResponse(status=200, text='{"id": "task-1", "title": "Buy milk and eggs"}')

        with patch.object(client._http_client, "send_async", new_callable=AsyncMock, return_value=mock_response) as mock_send:
            result = await client.update_to_do_async(input=payload, folder_id="list-1", id="task-1")

            mock_send.assert_called_once()
            method, path = mock_send.call_args[0][0], mock_send.call_args[0][1]
            body = mock_send.call_args[1].get("body")
            assert method == "PATCH"
            assert "/lists/list-1/tasks/task-1" in path
            assert body is payload
            assert result is not None


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

        with patch.object(client._http_client, "send_async", new_callable=AsyncMock, return_value=mock_response) as mock_send:
            result = await client.list_to_dos_by_folder_async(folder_id="list-1", top="10")

            mock_send.assert_called_once()
            method, path = mock_send.call_args[0][0], mock_send.call_args[0][1]
            assert method == "GET"
            assert "/lists/list-1/tasks" in path
            assert "$top=10" in path
            assert result is not None


class TestTodoTriggersAsync:
    """Tests for To Do trigger methods."""

    @pytest.mark.asyncio
    async def test_on_new_to_do_in_folder_success(self, mock_token_provider):
        """Test new to-do trigger method."""
        client = TodoClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider,
        )
        mock_response = MockResponse(status=200, text='{"id": "task-1"}')

        with patch.object(client._http_client, "send_async", new_callable=AsyncMock, return_value=mock_response) as mock_send:
            result = await client.on_new_to_do_in_folder_async(folder_id="list-1")

            mock_send.assert_called_once()
            method, path = mock_send.call_args[0][0], mock_send.call_args[0][1]
            assert method == "GET"
            assert "/v2/trigger/onNewToDoInFolder/list-1" in path
            assert result is not None

    @pytest.mark.asyncio
    async def test_on_update_to_do_in_folder_error(self, mock_token_provider):
        """Test updated to-do trigger error path."""
        client = TodoClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider,
        )
        mock_response = MockResponse(status=401, text='{"error": "Unauthorized"}')

        with patch.object(client._http_client, "send_async", new_callable=AsyncMock, return_value=mock_response):
            with pytest.raises(ConnectorException):
                await client.on_update_to_do_in_folder_async(folder_id="list-1")
