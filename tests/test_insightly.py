# Copyright (c) Microsoft Corporation. All rights reserved.

"""Unit tests for InsightlyClient."""

from unittest.mock import AsyncMock, patch

import pytest

from azure.connectors.insightly import (
    ContactRequest,
    InsightlyClient,
    LeadRequest,
    ListContactsResponse,
    ListEventsResponse,
    ListLeadsResponse,
    ListProjectsResponse,
    ListTasksResponse,
    ListUsersResponse,
    OrganizationRequest,
    ProjectRequest,
    TaskRequest,
    TRIGGER_OPERATIONS,
)
from azure.connectors.sdk import (
    ConnectorClientOptions,
    ConnectorException,
    ManagedIdentityTokenProvider,
)
from tests.conftest import MockResponse


async def _invoke_operation(client: InsightlyClient, operation: str):
    """Invoke an Insightly operation by name for shared tests."""
    if operation == "list_tasks":
        return await client.list_tasks_async()
    if operation == "update_task":
        return await client.update_task_async(input=TaskRequest(), id="1")
    if operation == "add_task":
        return await client.add_task_async(input=TaskRequest())
    if operation == "list_projects":
        return await client.list_projects_async()
    if operation == "update_project":
        return await client.update_project_async(input=ProjectRequest(), id="1")
    if operation == "add_project":
        return await client.add_project_async(input=ProjectRequest())
    if operation == "list_leads":
        return await client.list_leads_async()
    if operation == "update_lead":
        return await client.update_lead_async(input=LeadRequest(), id="1")
    if operation == "add_lead":
        return await client.add_lead_async(input=LeadRequest())
    if operation == "list_contacts":
        return await client.list_contacts_async()
    if operation == "update_contact":
        return await client.update_contact_async(input=ContactRequest(), id="1")
    if operation == "add_contact":
        return await client.add_contact_async(input=ContactRequest())
    if operation == "list_users":
        return await client.list_users_async()
    if operation == "delete_task":
        return await client.delete_task_async(task_id="1")
    if operation == "follow_task":
        return await client.follow_task_async(task_id="1")
    if operation == "delete_project":
        return await client.delete_project_async(project_id="1")
    if operation == "delete_lead":
        return await client.delete_lead_async(lead_id="1")
    if operation == "delete_contact":
        return await client.delete_contact_async(contact_id="1")
    if operation == "add_organization":
        return await client.add_organization_async(input=OrganizationRequest())

    raise ValueError(f"Unsupported operation '{operation}'.")


ALL_OPERATIONS = [
    "list_tasks",
    "update_task",
    "add_task",
    "list_projects",
    "update_project",
    "add_project",
    "list_leads",
    "update_lead",
    "add_lead",
    "list_contacts",
    "update_contact",
    "add_contact",
    "list_users",
    "delete_task",
    "follow_task",
    "delete_project",
    "delete_lead",
    "delete_contact",
    "add_organization",
]


class TestInsightlyClientInitialization:
    """Tests for InsightlyClient initialization."""

    def test_init_with_valid_url_and_defaults(self):
        """Test initialization with valid URL and default parameters."""
        client = InsightlyClient("https://example.azure.com/connections/test")

        assert client._connection_runtime_url == "https://example.azure.com/connections/test"
        assert client.connector_name == "insightly"
        assert isinstance(client._http_client._token_provider, ManagedIdentityTokenProvider)

    def test_init_with_trailing_slash(self):
        """Test that trailing slash is removed from URL."""
        client = InsightlyClient("https://example.azure.com/connections/test/")

        assert client._connection_runtime_url == "https://example.azure.com/connections/test"

    def test_init_with_custom_token_provider(self, mock_token_provider):
        """Test initialization with custom token provider."""
        client = InsightlyClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider,
        )

        assert client._http_client._token_provider is mock_token_provider

    def test_init_with_custom_options(self, mock_token_provider):
        """Test initialization with custom options."""
        options = ConnectorClientOptions(timeout_seconds=60.0, max_retry_attempts=5)
        client = InsightlyClient(
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
            InsightlyClient("")

    def test_init_with_none_url_raises_error(self):
        """Test that None URL raises ValueError."""
        with pytest.raises(ValueError, match="connection_runtime_url cannot be None or empty"):
            InsightlyClient(None)

    def test_connector_name_property(self, mock_token_provider):
        """Test connector_name property returns 'insightly'."""
        client = InsightlyClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider,
        )

        assert client.connector_name == "insightly"


class TestInsightlyClientLifecycle:
    """Tests for InsightlyClient lifecycle methods."""

    @pytest.mark.asyncio
    async def test_close(self, mock_token_provider):
        """Test close method calls http_client.close."""
        client = InsightlyClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider,
        )

        with patch.object(client._http_client, "close", new_callable=AsyncMock) as mock_close:
            await client.close()
            mock_close.assert_called_once()

    @pytest.mark.asyncio
    async def test_context_manager(self, mock_token_provider):
        """Test async context manager functionality."""
        with patch.object(InsightlyClient, "close", new_callable=AsyncMock) as mock_close:
            async with InsightlyClient(
                "https://example.azure.com/connections/test",
                token_provider=mock_token_provider,
            ) as client:
                assert isinstance(client, InsightlyClient)

            mock_close.assert_called_once()


class TestInsightlyClientOperations:
    """Tests for InsightlyClient operations against expected HTTP calls."""

    @pytest.mark.asyncio
    async def test_list_tasks_success(self, mock_token_provider):
        """Test successful task listing issues a GET to /Tasks."""
        client = InsightlyClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider,
        )
        mock_response = MockResponse(status=200, text='{"tasks": [{"TASK_ID": 1}]}')

        with patch.object(
            client._http_client,
            "send_async",
            new_callable=AsyncMock,
            return_value=mock_response,
        ) as mock_send:
            result = await client.list_tasks_async()

            method, path = mock_send.call_args[0][0], mock_send.call_args[0][1]
            assert method == "GET"
            assert path.endswith("/Tasks")
            assert result == {"tasks": [{"TASK_ID": 1}]}

    @pytest.mark.asyncio
    async def test_add_task_success(self, mock_token_provider):
        """Test successful task creation issues a POST to /Tasks with body."""
        client = InsightlyClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider,
        )
        mock_response = MockResponse(status=201, text='{"TASK_ID": 9}')

        with patch.object(
            client._http_client,
            "send_async",
            new_callable=AsyncMock,
            return_value=mock_response,
        ) as mock_send:
            result = await client.add_task_async(input=TaskRequest())

            method, path = mock_send.call_args[0][0], mock_send.call_args[0][1]
            assert method == "POST"
            assert path.endswith("/Tasks")
            assert mock_send.call_args.kwargs["body"] is not None
            assert result == {"TASK_ID": 9}

    @pytest.mark.asyncio
    async def test_update_task_success_includes_id_query(self, mock_token_provider):
        """Test task update issues a PUT to /Tasks with the id query parameter."""
        client = InsightlyClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider,
        )
        mock_response = MockResponse(status=200, text='{"TASK_ID": 5}')

        with patch.object(
            client._http_client,
            "send_async",
            new_callable=AsyncMock,
            return_value=mock_response,
        ) as mock_send:
            result = await client.update_task_async(input=TaskRequest(), id="5")

            method, path = mock_send.call_args[0][0], mock_send.call_args[0][1]
            assert method == "PUT"
            assert "/Tasks?" in path
            assert "id=5" in path
            assert result == {"TASK_ID": 5}

    @pytest.mark.asyncio
    async def test_delete_task_success_targets_resource(self, mock_token_provider):
        """Test task deletion issues a DELETE to /Tasks/{id}."""
        client = InsightlyClient(
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
            result = await client.delete_task_async(task_id="7")

            method, path = mock_send.call_args[0][0], mock_send.call_args[0][1]
            assert method == "DELETE"
            assert path.endswith("/Tasks/7")
            assert result is None

    @pytest.mark.asyncio
    async def test_follow_task_success_targets_follow(self, mock_token_provider):
        """Test following a task issues a POST to /Tasks/{id}/Follow."""
        client = InsightlyClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider,
        )
        mock_response = MockResponse(status=200, text='{"followed": true}')

        with patch.object(
            client._http_client,
            "send_async",
            new_callable=AsyncMock,
            return_value=mock_response,
        ) as mock_send:
            result = await client.follow_task_async(task_id="7")

            method, path = mock_send.call_args[0][0], mock_send.call_args[0][1]
            assert method == "POST"
            assert path.endswith("/Tasks/7/Follow")
            assert result == {"followed": True}

    @pytest.mark.asyncio
    async def test_add_organization_success(self, mock_token_provider):
        """Test organization creation issues a POST to /Organisations."""
        client = InsightlyClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider,
        )
        mock_response = MockResponse(status=201, text='{"ORGANISATION_ID": 3}')

        with patch.object(
            client._http_client,
            "send_async",
            new_callable=AsyncMock,
            return_value=mock_response,
        ) as mock_send:
            result = await client.add_organization_async(input=OrganizationRequest())

            method, path = mock_send.call_args[0][0], mock_send.call_args[0][1]
            assert method == "POST"
            assert path.endswith("/Organisations")
            assert result == {"ORGANISATION_ID": 3}

    @pytest.mark.asyncio
    async def test_empty_response_body_returns_none(self, mock_token_provider):
        """Test a 2xx response with no body returns None."""
        client = InsightlyClient(
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


class TestInsightlyClientErrorHandling:
    """Error handling tests that ensure all methods raise ConnectorException."""

    @pytest.mark.asyncio
    @pytest.mark.parametrize("operation", ALL_OPERATIONS)
    async def test_error_response_raises_exception_for_all_operations(
        self,
        mock_token_provider,
        operation,
    ):
        """Test non-2xx responses raise ConnectorException for every operation."""
        client = InsightlyClient(
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


class TestInsightlyTriggerOperations:
    """Tests for the module-level TRIGGER_OPERATIONS registry."""

    def test_all_expected_triggers_registered(self):
        """Test the registry exposes every Insightly trigger operation."""
        assert set(TRIGGER_OPERATIONS) == {
            "OnTaskAssignedToMe",
            "OnTaskCreated",
            "OnTaskUpdated",
            "OnProjectCreated",
            "OnProjectUpdated",
            "OnLeadCreated",
            "OnLeadUpdated",
            "OnContactCreated",
            "OnContactUpdated",
            "OnEventCreated",
            "OnEventUpdated",
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
        assert not hasattr(InsightlyClient, "on_task_created_async")
        assert not hasattr(InsightlyClient, "on_lead_created_async")
        assert not hasattr(InsightlyClient, "on_event_updated_async")


class TestInsightlyTypeSerialization:
    """Tests for Insightly connector dataclass defaults."""

    def test_response_dataclasses_initialize_expected_defaults(self):
        """Test generated response dataclasses initialize with None defaults."""
        assert ListTasksResponse().tasks is None
        assert ListProjectsResponse().projects is None
        assert ListLeadsResponse().leads is None
        assert ListContactsResponse().contacts is None
        assert ListUsersResponse().users is None
        assert ListEventsResponse().events is None

    def test_request_dataclasses_instantiate(self):
        """Test generated request dataclasses instantiate without arguments."""
        assert TaskRequest() is not None
        assert ProjectRequest() is not None
        assert LeadRequest() is not None
        assert ContactRequest() is not None
        assert OrganizationRequest() is not None
