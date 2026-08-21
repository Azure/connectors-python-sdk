# Copyright (c) Microsoft Corporation. All rights reserved.

"""Unit tests for TallyfyClient."""

from unittest.mock import AsyncMock, patch

import pytest

import azure.connectors.tallyfy as tallyfy_module
from azure.connectors.sdk import ConnectorException, ManagedIdentityTokenProvider
from azure.connectors.tallyfy import CreateRunInput, CreateTaskInput, TallyfyClient
from tests.conftest import MockResponse
from tests.generated_connector_test_utils import (
    get_generated_operations,
    invoke_generated_operation,
)


SUCCESS_CONTRACTS = {
    "comment_task": ("POST", "/organizations/value/tasks/value/comment", True),
    "completed_one_off_task": (
        "POST",
        "/organizations/value/completed-tasks",
        True,
    ),
    "completed_process_task": (
        "POST",
        "/organizations/value/runs/value/completed-tasks",
        True,
    ),
    "create_run": ("POST", "/organizations/value/runs", True),
    "create_task": (
        "POST",
        "/processes/micro-functions/organizations/value/tasks",
        True,
    ),
    "edit_step_type": (
        "PUT",
        "/processes/micro-functions/organizations/value/blueprints/value/steps/value/"
        "edit-step-type",
        True,
    ),
    "edit_task_deadline": (
        "PUT",
        "/processes/micro-functions/organizations/value/tasks/value/edit-deadline",
        True,
    ),
    "get_organization_users": ("GET", "/organizations/value/users", False),
    "get_user_organizations": ("GET", "/me/organizations", False),
    "get_user_tasks": (
        "GET",
        "/organizations/value/users/value/tasks",
        False,
    ),
    "invite_user_to_organization": (
        "POST",
        "/organizations/value/users/invite",
        True,
    ),
    "remove_assignee": (
        "PUT",
        "/processes/micro-functions/organizations/value/tasks/value/remove-assignee/value",
        False,
    ),
    "remove_guest": (
        "PUT",
        "/processes/micro-functions/organizations/value/tasks/value/remove-guest/value",
        False,
    ),
    "reopen_one_off_task": (
        "DELETE",
        "/organizations/value/completed-tasks/value",
        False,
    ),
    "reopen_process_task": (
        "POST",
        "/organizations/value/runs/value/completed-tasks/value",
        False,
    ),
}
ALL_OPERATIONS = list(SUCCESS_CONTRACTS)


class TestTallyfyClient:
    """Tests for TallyfyClient."""

    def test_init_with_defaults(self):
        """Test initialization with default authentication."""
        client = TallyfyClient("https://example.azure.com/connections/test/")

        assert client._connection_runtime_url == "https://example.azure.com/connections/test"
        assert client.connector_name == "tallyfy"
        assert isinstance(client._http_client._token_provider, ManagedIdentityTokenProvider)

    @pytest.mark.parametrize("connection_runtime_url", ["", None])
    def test_init_with_invalid_url_raises_error(self, connection_runtime_url):
        """Test invalid runtime URLs are rejected."""
        with pytest.raises(ValueError, match="connection_runtime_url cannot be None or empty"):
            TallyfyClient(connection_runtime_url)

    @pytest.mark.asyncio
    async def test_context_manager(self, mock_token_provider):
        """Test async context manager cleanup."""
        with patch.object(TallyfyClient, "close", new_callable=AsyncMock) as mock_close:
            async with TallyfyClient(
                "https://example.azure.com/connections/test",
                token_provider=mock_token_provider,
            ) as client:
                assert isinstance(client, TallyfyClient)

        mock_close.assert_called_once()

    def test_all_generated_operations_are_covered(self):
        """Test the expected generated operation surface."""
        assert get_generated_operations(TallyfyClient) == set(ALL_OPERATIONS)

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        ("operation", "expected_method", "expected_url_suffix", "expects_body"),
        [
            (operation, *contract)
            for operation, contract in SUCCESS_CONTRACTS.items()
        ],
    )
    async def test_generated_operation_success_contract(
        self,
        operation,
        expected_method,
        expected_url_suffix,
        expects_body,
        mock_token_provider,
    ):
        """Test every generated operation's successful HTTP contract."""
        client = TallyfyClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider,
        )

        with patch.object(
            client._http_client,
            "send_async",
            new_callable=AsyncMock,
            return_value=MockResponse(status=200, text='{"ok": true}'),
        ) as mock_send:
            result = await invoke_generated_operation(client, operation, tallyfy_module)

        method, url = mock_send.call_args.args[:2]
        assert method == expected_method
        assert url.endswith(expected_url_suffix)
        assert (mock_send.call_args.kwargs["body"] is not None) is expects_body
        assert result == {"ok": True}

    @pytest.mark.asyncio
    async def test_create_run_success(self, mock_token_provider):
        """Test creating a run sends the generated request body."""
        client = TallyfyClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider,
        )

        with patch.object(
            client._http_client,
            "send_async",
            new_callable=AsyncMock,
            return_value=MockResponse(status=201, text='{"id": "run-1"}'),
        ) as mock_send:
            result = await client.create_run_async(
                input=CreateRunInput(name="Quarterly review", checklist_id="checklist-1"),
                org="organization/one",
            )

        method, url = mock_send.call_args.args[:2]
        assert method == "POST"
        assert url.endswith("/organizations/organization%2Fone/runs")
        assert mock_send.call_args.kwargs["body"].name == "Quarterly review"
        assert result == {"id": "run-1"}

    @pytest.mark.asyncio
    async def test_create_task_success(self, mock_token_provider):
        """Test creating a task uses the micro-functions route."""
        client = TallyfyClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider,
        )

        with patch.object(
            client._http_client,
            "send_async",
            new_callable=AsyncMock,
            return_value=MockResponse(status=201, text='{"id": "task-1"}'),
        ) as mock_send:
            await client.create_task_async(
                input=CreateTaskInput(name="Review document", description="Check details"),
                org="organization",
            )

        assert mock_send.call_args.args[0] == "POST"
        assert mock_send.call_args.args[1].endswith(
            "/processes/micro-functions/organizations/organization/tasks"
        )

    @pytest.mark.asyncio
    @pytest.mark.parametrize("operation", ALL_OPERATIONS)
    async def test_non_success_response_raises_exception(
        self,
        operation,
        mock_token_provider,
    ):
        """Test every generated operation raises for a non-success response."""
        client = TallyfyClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider,
        )

        with patch.object(
            client._http_client,
            "send_async",
            new_callable=AsyncMock,
            return_value=MockResponse(status=400, text="bad request"),
        ):
            with pytest.raises(ConnectorException):
                await invoke_generated_operation(client, operation, tallyfy_module)
