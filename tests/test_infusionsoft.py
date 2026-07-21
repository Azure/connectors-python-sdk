# Copyright (c) Microsoft Corporation. All rights reserved.

"""Unit tests for InfusionsoftClient."""

from unittest.mock import AsyncMock, patch

import pytest

from azure.connectors.infusionsoft import (
    CreateTaskRequest,
    InfusionsoftClient,
    ListOrdersResponse,
    ListTasksResponse,
    OnNewTaskResponse,
    TaskResponse,
    TRIGGER_OPERATIONS,
)
from azure.connectors.sdk import (
    ConnectorClientOptions,
    ConnectorException,
    ManagedIdentityTokenProvider,
)
from tests.conftest import MockResponse


async def _invoke_operation(client: InfusionsoftClient, operation: str):
    """Invoke an Infusionsoft operation by name for shared tests."""
    if operation == "create_task":
        return await client.create_task_async(input=CreateTaskRequest())
    if operation == "update_task":
        return await client.update_task_async(input=CreateTaskRequest(), id="1")
    if operation == "list_tasks":
        return await client.list_tasks_async()

    raise ValueError(f"Unsupported operation '{operation}'.")


ALL_OPERATIONS = [
    "create_task",
    "update_task",
    "list_tasks",
]


class TestInfusionsoftClientInitialization:
    """Tests for InfusionsoftClient initialization."""

    def test_init_with_valid_url_and_defaults(self):
        """Test initialization with valid URL and default parameters."""
        client = InfusionsoftClient("https://example.azure.com/connections/test")

        assert client._connection_runtime_url == "https://example.azure.com/connections/test"
        assert client.connector_name == "infusionsoft"
        assert isinstance(client._http_client._token_provider, ManagedIdentityTokenProvider)

    def test_init_with_trailing_slash(self):
        """Test that trailing slash is removed from URL."""
        client = InfusionsoftClient("https://example.azure.com/connections/test/")

        assert client._connection_runtime_url == "https://example.azure.com/connections/test"

    def test_init_with_custom_token_provider(self, mock_token_provider):
        """Test initialization with custom token provider."""
        client = InfusionsoftClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider,
        )

        assert client._http_client._token_provider is mock_token_provider

    def test_init_with_custom_options(self, mock_token_provider):
        """Test initialization with custom options."""
        options = ConnectorClientOptions(timeout_seconds=60.0, max_retry_attempts=5)
        client = InfusionsoftClient(
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
            InfusionsoftClient("")

    def test_init_with_none_url_raises_error(self):
        """Test that None URL raises ValueError."""
        with pytest.raises(ValueError, match="connection_runtime_url cannot be None or empty"):
            InfusionsoftClient(None)

    def test_connector_name_property(self, mock_token_provider):
        """Test connector_name property returns 'infusionsoft'."""
        client = InfusionsoftClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider,
        )

        assert client.connector_name == "infusionsoft"


class TestInfusionsoftClientLifecycle:
    """Tests for InfusionsoftClient lifecycle methods."""

    @pytest.mark.asyncio
    async def test_close(self, mock_token_provider):
        """Test close method calls http_client.close."""
        client = InfusionsoftClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider,
        )

        with patch.object(client._http_client, "close", new_callable=AsyncMock) as mock_close:
            await client.close()
            mock_close.assert_called_once()

    @pytest.mark.asyncio
    async def test_context_manager(self, mock_token_provider):
        """Test async context manager functionality."""
        with patch.object(InfusionsoftClient, "close", new_callable=AsyncMock) as mock_close:
            async with InfusionsoftClient(
                "https://example.azure.com/connections/test",
                token_provider=mock_token_provider,
            ) as client:
                assert isinstance(client, InfusionsoftClient)

            mock_close.assert_called_once()


class TestInfusionsoftClientOperations:
    """Tests for InfusionsoftClient operations against expected HTTP calls."""

    @pytest.mark.asyncio
    async def test_create_task_success(self, mock_token_provider):
        """Test task creation issues a POST to /crm/rest/v1/tasks/ with body."""
        client = InfusionsoftClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider,
        )
        mock_response = MockResponse(status=201, text='{"id": 9}')

        with patch.object(
            client._http_client,
            "send_async",
            new_callable=AsyncMock,
            return_value=mock_response,
        ) as mock_send:
            result = await client.create_task_async(input=CreateTaskRequest())

            method, path = mock_send.call_args[0][0], mock_send.call_args[0][1]
            assert method == "POST"
            assert path.endswith("/crm/rest/v1/tasks/")
            assert mock_send.call_args.kwargs["body"] is not None
            assert result == {"id": 9}

    @pytest.mark.asyncio
    async def test_update_task_success_targets_resource(self, mock_token_provider):
        """Test task update issues a PUT to /crm/rest/v1/tasks/{id}."""
        client = InfusionsoftClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider,
        )
        mock_response = MockResponse(status=200, text='{"id": 5}')

        with patch.object(
            client._http_client,
            "send_async",
            new_callable=AsyncMock,
            return_value=mock_response,
        ) as mock_send:
            result = await client.update_task_async(input=CreateTaskRequest(), id="5")

            method, path = mock_send.call_args[0][0], mock_send.call_args[0][1]
            assert method == "PUT"
            assert path.endswith("/crm/rest/v1/tasks/5")
            assert mock_send.call_args.kwargs["body"] is not None
            assert result == {"id": 5}

    @pytest.mark.asyncio
    async def test_list_tasks_success_includes_order_query(self, mock_token_provider):
        """Test task listing issues a GET to /crm/rest/v1/tasks/search with order."""
        client = InfusionsoftClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider,
        )
        mock_response = MockResponse(status=200, text='{"tasks": [{"id": 1}]}')

        with patch.object(
            client._http_client,
            "send_async",
            new_callable=AsyncMock,
            return_value=mock_response,
        ) as mock_send:
            result = await client.list_tasks_async()

            method, path = mock_send.call_args[0][0], mock_send.call_args[0][1]
            assert method == "GET"
            assert "/crm/rest/v1/tasks/search?" in path
            assert "order=" in path
            assert result == {"tasks": [{"id": 1}]}

    @pytest.mark.asyncio
    async def test_empty_response_body_returns_none(self, mock_token_provider):
        """Test a 2xx response with no body returns None."""
        client = InfusionsoftClient(
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
            result = await client.list_tasks_async()

            assert result is None


class TestInfusionsoftClientErrorHandling:
    """Error handling tests that ensure all methods raise ConnectorException."""

    @pytest.mark.asyncio
    @pytest.mark.parametrize("operation", ALL_OPERATIONS)
    async def test_error_response_raises_exception_for_all_operations(
        self,
        mock_token_provider,
        operation,
    ):
        """Test non-2xx responses raise ConnectorException for every operation."""
        client = InfusionsoftClient(
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


class TestInfusionsoftTriggerOperations:
    """Tests for the module-level TRIGGER_OPERATIONS registry."""

    def test_all_expected_triggers_registered(self):
        """Test the registry exposes every Infusionsoft trigger operation."""
        assert set(TRIGGER_OPERATIONS) == {
            "OnNewTask",
            "OnNewOrder",
        }

    @pytest.mark.parametrize("operation_id", list(TRIGGER_OPERATIONS))
    def test_trigger_metadata_shape(self, operation_id):
        """Test each trigger entry carries the expected metadata fields."""
        trigger = TRIGGER_OPERATIONS[operation_id]

        assert trigger["operation_id"] == operation_id
        assert trigger["method"] == "get"
        assert trigger["path"].startswith("/{connectionId}/")
        assert "callback_payload_type" in trigger
        assert isinstance(trigger["required_parameters"], list)

    def test_triggers_are_not_client_methods(self):
        """Test trigger operations are not emitted as callable client methods."""
        assert not hasattr(InfusionsoftClient, "on_new_task_async")
        assert not hasattr(InfusionsoftClient, "on_new_order_async")


class TestInfusionsoftTypeSerialization:
    """Tests for Infusionsoft connector dataclass defaults."""

    def test_response_dataclasses_initialize_expected_defaults(self):
        """Test generated response dataclasses initialize with None defaults."""
        assert ListTasksResponse().tasks is None
        assert TaskResponse().id is None
        assert TaskResponse().type_ is None
        assert OnNewTaskResponse().additional_properties == {}
        assert ListOrdersResponse().additional_properties == {}

    def test_request_dataclasses_instantiate(self):
        """Test generated request dataclasses instantiate without arguments."""
        assert CreateTaskRequest() is not None
        assert CreateTaskRequest().type_ is None
