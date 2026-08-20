# Copyright (c) Microsoft Corporation. All rights reserved.

"""Unit tests for PlannerClient."""

import pytest
from unittest.mock import AsyncMock, patch

from azure.connectors.planner import (
    PlannerClient,
    UnassignUsersInput,
    GetTaskResponse,
    AssignUsersInput,
    ListMyPlansResponse,
    GetPlanDetailsResponse,
    CreateBucketInput,
    CreateBucketResponse,
    GetTaskDetailsResponse,
    ListBucketsResponse,
    ListTasksResponse,
    UpdateTaskDetailsRequest,
    ListGroupsResponse,
    GetTaskResponseV2,
    GetTaskResponseV3,
    AppliedCategories,
    UpdateTaskRequest,
    CreateTaskRequest,
    ErrorResponse,
    TRIGGER_OPERATIONS,
)
from azure.connectors.sdk import (
    ConnectorClientOptions,
    ManagedIdentityTokenProvider,
    ConnectorException,
)
from azure.connectors.sdk.serialization import to_wire
from tests.conftest import MockResponse


class TestPlannerClientInitialization:
    """Tests for PlannerClient initialization."""

    def test_init_with_valid_url_and_defaults(self):
        """Test initialization with valid URL and default parameters."""
        client = PlannerClient("https://example.azure.com/connections/test")

        assert client._connection_runtime_url == "https://example.azure.com/connections/test"
        assert client.connector_name == "planner"
        assert isinstance(client._http_client._token_provider, ManagedIdentityTokenProvider)

    def test_init_with_trailing_slash(self):
        """Test that trailing slash is removed from URL."""
        client = PlannerClient("https://example.azure.com/connections/test/")

        assert client._connection_runtime_url == "https://example.azure.com/connections/test"

    def test_init_with_custom_token_provider(self, mock_token_provider):
        """Test initialization with custom token provider."""
        client = PlannerClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        assert client._http_client._token_provider is mock_token_provider

    def test_init_with_custom_options(self, mock_token_provider):
        """Test initialization with custom options."""
        options = ConnectorClientOptions(timeout_seconds=60.0, max_retry_attempts=5)
        client = PlannerClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider,
            options=options
        )

        assert client._options is options
        assert client._options.timeout_seconds == 60.0
        assert client._options.max_retry_attempts == 5

    def test_init_with_empty_url_raises_error(self):
        """Test that empty URL raises ValueError."""
        with pytest.raises(ValueError, match="connection_runtime_url cannot be None or empty"):
            PlannerClient("")

    def test_init_with_none_url_raises_error(self):
        """Test that None URL raises ValueError."""
        with pytest.raises(ValueError, match="connection_runtime_url cannot be None or empty"):
            PlannerClient(None)

    def test_connector_name_property(self, mock_token_provider):
        """Test connector_name property returns 'planner'."""
        client = PlannerClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        assert client.connector_name == "planner"

    def test_init_preserves_url_without_trailing_slash(self, mock_token_provider):
        """Test that URL without trailing slash is preserved."""
        client = PlannerClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        assert client._connection_runtime_url == "https://example.azure.com/connections/test"


class TestPlannerClientLifecycle:
    """Tests for PlannerClient lifecycle methods."""

    @pytest.mark.asyncio
    async def test_close(self, mock_token_provider):
        """Test close method calls http_client.close."""
        client = PlannerClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        with patch.object(client._http_client, 'close', new_callable=AsyncMock) as mock_close:
            await client.close()
            mock_close.assert_called_once()

    @pytest.mark.asyncio
    async def test_context_manager(self, mock_token_provider):
        """Test async context manager functionality."""
        with patch.object(PlannerClient, 'close', new_callable=AsyncMock) as mock_close:
            async with PlannerClient(
                "https://example.azure.com/connections/test",
                token_provider=mock_token_provider
            ) as client:
                assert isinstance(client, PlannerClient)

            mock_close.assert_called_once()


class TestListMyTasksAsync:
    """Tests for list_my_tasks_async method."""

    @pytest.mark.asyncio
    async def test_success(self, mock_token_provider):
        """Test successful list my tasks request."""
        client = PlannerClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(
            status=200,
            text='{"value": [{"id": "task-1", "title": "My Task"}]}'
        )

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ) as mock_send:
            result = await client.list_my_tasks_async()

            mock_send.assert_called_once()
            assert result is not None
            assert "value" in result

    @pytest.mark.asyncio
    async def test_empty_response_returns_none(self, mock_token_provider):
        """Test that empty response returns None."""
        client = PlannerClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(status=200, text='')

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ):
            result = await client.list_my_tasks_async()
            assert result is None

    @pytest.mark.asyncio
    async def test_error_response_raises_exception(self, mock_token_provider):
        """Test that error response raises ConnectorException."""
        client = PlannerClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(status=401, text='{"error": "Unauthorized"}')

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ):
            with pytest.raises(ConnectorException):
                await client.list_my_tasks_async()


class TestListGroupPlansAsync:
    """Tests for list_group_plans_async method."""

    @pytest.mark.asyncio
    async def test_success(self, mock_token_provider):
        """Test successful list group plans request."""
        client = PlannerClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(
            status=200,
            text='{"value": [{"id": "plan-1", "title": "Team Plan"}]}'
        )

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ) as mock_send:
            result = await client.list_group_plans_async(group_id="group-123")

            mock_send.assert_called_once()
            call_args = mock_send.call_args
            assert "group-123" in call_args[0][1]
            assert result is not None

    @pytest.mark.asyncio
    async def test_error_response_raises_exception(self, mock_token_provider):
        """Test that error response raises ConnectorException."""
        client = PlannerClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(status=404, text='{"error": "Not found"}')

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ):
            with pytest.raises(ConnectorException):
                await client.list_group_plans_async(group_id="invalid")


class TestGetTaskAsync:
    """Tests for get_task_async method."""

    @pytest.mark.asyncio
    async def test_success(self, mock_token_provider):
        """Test successful get task request."""
        client = PlannerClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(
            status=200,
            text='{"id": "task-123", "title": "My Task", "percentComplete": 50}'
        )

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ) as mock_send:
            result = await client.get_task_async(id="task-123")

            mock_send.assert_called_once()
            call_args = mock_send.call_args
            assert "task-123" in call_args[0][1]
            assert result is not None
            assert result["id"] == "task-123"

    @pytest.mark.asyncio
    async def test_error_response_raises_exception(self, mock_token_provider):
        """Test that error response raises ConnectorException."""
        client = PlannerClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(status=404, text='{"error": "Task not found"}')

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ):
            with pytest.raises(ConnectorException):
                await client.get_task_async(id="invalid")


class TestGetTaskDetailsAsync:
    """Tests for get_task_details_async method."""

    @pytest.mark.asyncio
    async def test_success(self, mock_token_provider):
        """Test successful get task details request."""
        client = PlannerClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(
            status=200,
            text='{"id": "task-123", "description": "Task description"}'
        )

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ) as mock_send:
            result = await client.get_task_details_async(id="task-123")

            mock_send.assert_called_once()
            assert result is not None
            assert result["description"] == "Task description"

    @pytest.mark.asyncio
    async def test_empty_response_returns_none(self, mock_token_provider):
        """Test that empty response returns None."""
        client = PlannerClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(status=200, text='')

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ):
            result = await client.get_task_details_async(id="task-123")
            assert result is None


class TestGetPlanDetailsAsync:
    """Tests for get_plan_details_async method."""

    @pytest.mark.asyncio
    async def test_success(self, mock_token_provider):
        """Test successful get plan details request."""
        client = PlannerClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(
            status=200,
            text='{"id": "plan-123", "categoryDescriptions": {}}'
        )

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ) as mock_send:
            result = await client.get_plan_details_async(id="plan-123")

            mock_send.assert_called_once()
            assert result is not None

    @pytest.mark.asyncio
    async def test_error_response_raises_exception(self, mock_token_provider):
        """Test that error response raises ConnectorException."""
        client = PlannerClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(status=403, text='{"error": "Forbidden"}')

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ):
            with pytest.raises(ConnectorException):
                await client.get_plan_details_async(id="plan-123")


class TestCreateTaskAsync:
    """Tests for create_task_async method."""

    @pytest.mark.asyncio
    async def test_success(self, mock_token_provider):
        """Test successful create task request."""
        client = PlannerClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(
            status=201,
            text='{"id": "task-new", "title": "New Task"}'
        )

        task_input = CreateTaskRequest(
            group_id="group-123",
            plan_id="plan-123",
            title="New Task"
        )

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ) as mock_send:
            result = await client.create_task_async(input=task_input)

            mock_send.assert_called_once()
            call_args = mock_send.call_args
            assert call_args[0][0] == "POST"
            assert result is not None
            assert result["title"] == "New Task"

    @pytest.mark.asyncio
    async def test_error_response_raises_exception(self, mock_token_provider):
        """Test that error response raises ConnectorException."""
        client = PlannerClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(status=400, text='{"error": "Bad request"}')

        task_input = CreateTaskRequest(title="New Task")

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ):
            with pytest.raises(ConnectorException):
                await client.create_task_async(input=task_input)


class TestCreateBucketAsync:
    """Tests for create_bucket_async method."""

    @pytest.mark.asyncio
    async def test_success(self, mock_token_provider):
        """Test successful create bucket request."""
        client = PlannerClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(
            status=201,
            text='{"id": "bucket-new", "name": "New Bucket"}'
        )

        bucket_input = CreateBucketInput(
            name="New Bucket",
            group_id="group-123",
            plan_id="plan-123"
        )

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ) as mock_send:
            result = await client.create_bucket_async(input=bucket_input)

            mock_send.assert_called_once()
            call_args = mock_send.call_args
            assert call_args[0][0] == "POST"
            assert result is not None
            assert result["name"] == "New Bucket"


class TestUpdateTaskAsync:
    """Tests for update_task_async method."""

    @pytest.mark.asyncio
    async def test_success(self, mock_token_provider):
        """Test successful update task request."""
        client = PlannerClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(
            status=200,
            text='{"id": "task-123", "title": "Updated Task"}'
        )

        update_input = UpdateTaskRequest(
            title="Updated Task",
            percent_complete=75
        )

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ) as mock_send:
            result = await client.update_task_async(
                input=update_input,
                id="task-123"
            )

            mock_send.assert_called_once()
            call_args = mock_send.call_args
            assert call_args[0][0] == "PATCH"
            assert "task-123" in call_args[0][1]
            assert result is not None

    @pytest.mark.asyncio
    async def test_error_response_raises_exception(self, mock_token_provider):
        """Test that error response raises ConnectorException."""
        client = PlannerClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(status=404, text='{"error": "Not found"}')

        update_input = UpdateTaskRequest(title="Updated Task")

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ):
            with pytest.raises(ConnectorException):
                await client.update_task_async(input=update_input, id="invalid")


class TestUpdateTaskDetailsAsync:
    """Tests for update_task_details_async method."""

    @pytest.mark.asyncio
    async def test_success(self, mock_token_provider):
        """Test successful update task details request."""
        client = PlannerClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(
            status=200,
            text='{"id": "task-123", "description": "Updated description"}'
        )

        update_input = UpdateTaskDetailsRequest(
            description="Updated description"
        )

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ) as mock_send:
            result = await client.update_task_details_async(
                input=update_input,
                id="task-123"
            )

            mock_send.assert_called_once()
            call_args = mock_send.call_args
            assert call_args[0][0] == "PATCH"
            assert result is not None


class TestDeleteTaskAsync:
    """Tests for delete_task_async method."""

    @pytest.mark.asyncio
    async def test_success(self, mock_token_provider):
        """Test successful delete task request."""
        client = PlannerClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(status=204, text='')

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ) as mock_send:
            await client.delete_task_async(id="task-123")

            mock_send.assert_called_once()
            call_args = mock_send.call_args
            assert call_args[0][0] == "DELETE"
            assert "task-123" in call_args[0][1]


class TestAssignUsersAsync:
    """Tests for assign_users_async method."""

    @pytest.mark.asyncio
    async def test_success(self, mock_token_provider):
        """Test successful assign users request."""
        client = PlannerClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(
            status=200,
            text='{"id": "task-123", "assignments": []}'
        )

        assign_input = AssignUsersInput(
            assignments="user1@contoso.com;user2@contoso.com"
        )

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ) as mock_send:
            result = await client.assign_users_async(
                input=assign_input,
                id="task-123"
            )

            mock_send.assert_called_once()
            call_args = mock_send.call_args
            assert call_args[0][0] == "PATCH"
            assert result is not None

    @pytest.mark.asyncio
    async def test_error_response_raises_exception(self, mock_token_provider):
        """Test that error response raises ConnectorException."""
        client = PlannerClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(status=400, text='{"error": "Invalid user"}')

        assign_input = AssignUsersInput(assignments="invalid")

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ):
            with pytest.raises(ConnectorException):
                await client.assign_users_async(input=assign_input, id="task-123")


class TestUnassignUsersAsync:
    """Tests for unassign_users_async method."""

    @pytest.mark.asyncio
    async def test_success(self, mock_token_provider):
        """Test successful unassign users request."""
        client = PlannerClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(
            status=200,
            text='{"id": "task-123", "assignments": []}'
        )

        unassign_input = UnassignUsersInput(
            assignments="user1@contoso.com"
        )

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ) as mock_send:
            result = await client.unassign_users_async(
                input=unassign_input,
                id="task-123"
            )

            mock_send.assert_called_once()
            call_args = mock_send.call_args
            assert call_args[0][0] == "PATCH"
            assert result is not None


class TestTriggerOperations:
    """Tests for Planner trigger registration metadata."""

    def test_on_task_assigned_to_me_metadata(self):
        """Test assigned-task trigger metadata."""
        trigger = TRIGGER_OPERATIONS["OnTaskAssignedToMe_V2"]

        assert trigger["path"].endswith("/ontaskassignedtome_trigger/tasks")
        assert trigger["method"] == "get"
        assert trigger["required_parameters"] == []
        assert trigger["callback_payload_type"] == "ListTasksResponse"

    def test_triggers_are_not_client_methods(self):
        """Test triggers are not exposed as callable client methods."""
        assert not hasattr(PlannerClient, "on_task_assigned_to_me_async")


class TestDataclasses:
    """Tests for dataclass serialization and defaults."""

    def test_unassign_users_input_defaults(self):
        """Test UnassignUsersInput default values."""
        input_obj = UnassignUsersInput()
        assert input_obj.assignments is None

    def test_current_task_requests_use_swagger_wire_names(self):
        """Test current create and update requests preserve Swagger keys."""
        create_request = CreateTaskRequest(
            group_id="group-123",
            plan_id="plan-123",
            bucket_id="bucket-123",
        )
        update_request = UpdateTaskRequest(
            percent_complete=50,
            bucket_id="bucket-456",
        )

        assert to_wire(create_request) == {
            "groupId": "group-123",
            "planId": "plan-123",
            "bucketId": "bucket-123",
        }
        assert to_wire(update_request) == {
            "percentComplete": 50,
            "bucketId": "bucket-456",
        }

    def test_unassign_users_input_with_values(self):
        """Test UnassignUsersInput with values."""
        input_obj = UnassignUsersInput(assignments="user@contoso.com")
        assert input_obj.assignments == "user@contoso.com"

    def test_get_task_response_defaults(self):
        """Test GetTaskResponse default values."""
        response = GetTaskResponse()
        assert response.id is None
        assert response.title is None
        assert response.percent_complete is None

    def test_get_task_response_with_values(self):
        """Test GetTaskResponse with values."""
        response = GetTaskResponse(
            id="task-123",
            title="My Task",
            percent_complete=50,
            plan_id="plan-123"
        )
        assert response.id == "task-123"
        assert response.title == "My Task"
        assert response.percent_complete == 50

    def test_assign_users_input_defaults(self):
        """Test AssignUsersInput default values."""
        input_obj = AssignUsersInput()
        assert input_obj.assignments is None

    def test_list_my_plans_response_defaults(self):
        """Test ListMyPlansResponse default values."""
        response = ListMyPlansResponse()
        assert response.value is None

    def test_get_plan_details_response_defaults(self):
        """Test GetPlanDetailsResponse default values."""
        response = GetPlanDetailsResponse()
        assert response.id is None
        assert response.category_descriptions is None

    def test_create_bucket_input_defaults(self):
        """Test CreateBucketInput default values."""
        input_obj = CreateBucketInput()
        assert input_obj.name is None
        assert input_obj.group_id is None
        assert input_obj.plan_id is None

    def test_create_bucket_input_with_values(self):
        """Test CreateBucketInput with values."""
        input_obj = CreateBucketInput(
            name="New Bucket",
            group_id="group-123",
            plan_id="plan-123"
        )
        assert input_obj.name == "New Bucket"

    def test_create_bucket_response_defaults(self):
        """Test CreateBucketResponse default values."""
        response = CreateBucketResponse()
        assert response.id is None
        assert response.name is None

    def test_get_task_details_response_defaults(self):
        """Test GetTaskDetailsResponse default values."""
        response = GetTaskDetailsResponse()
        assert response.id is None
        assert response.description is None
        assert response.references is None
        assert response.checklist is None

    def test_list_buckets_response_defaults(self):
        """Test ListBucketsResponse default values."""
        response = ListBucketsResponse()
        assert response.value is None

    def test_list_tasks_response_defaults(self):
        """Test ListTasksResponse default values."""
        response = ListTasksResponse()
        assert response.value is None
        assert response.next_link is None

    def test_update_task_details_request_defaults(self):
        """Test UpdateTaskDetailsRequest default values."""
        request = UpdateTaskDetailsRequest()
        assert request.description is None
        assert request.references is None
        assert request.checklist is None

    def test_update_task_details_request_with_values(self):
        """Test UpdateTaskDetailsRequest with values."""
        request = UpdateTaskDetailsRequest(
            description="Task description",
            references=[{"alias": "ref1"}],
            checklist=[{"title": "Item 1"}]
        )
        assert request.description == "Task description"
        assert len(request.references) == 1
        assert len(request.checklist) == 1

    def test_list_groups_response_defaults(self):
        """Test ListGroupsResponse default values."""
        response = ListGroupsResponse()
        assert response.value is None

    def test_get_task_response_v2_defaults(self):
        """Test GetTaskResponseV2 default values."""
        response = GetTaskResponseV2()
        assert response.id is None
        assert response.title is None

    def test_get_task_response_v3_defaults(self):
        """Test GetTaskResponseV3 default values."""
        response = GetTaskResponseV3()
        assert response.id is None
        assert response.priority is None

    def test_get_task_response_v3_with_priority(self):
        """Test GetTaskResponseV3 with priority."""
        response = GetTaskResponseV3(
            id="task-123",
            title="Urgent Task",
            priority=1
        )
        assert response.priority == 1

    def test_update_task_request_defaults(self):
        """Test UpdateTaskRequest default values."""
        request = UpdateTaskRequest()
        assert request.title is None
        assert request.percent_complete is None

    def test_update_task_request_with_values(self):
        """Test UpdateTaskRequest with values."""
        request = UpdateTaskRequest(
            title="Updated Title",
            percent_complete=100,
            bucket_id="bucket-123"
        )
        assert request.title == "Updated Title"
        assert request.percent_complete == 100

    def test_create_task_request_defaults(self):
        """Test CreateTaskRequest default values."""
        request = CreateTaskRequest()
        assert request.priority is None
        assert request.title is None

    def test_create_task_request_with_priority(self):
        """Test CreateTaskRequest with priority."""
        request = CreateTaskRequest(
            group_id="group-123",
            plan_id="plan-123",
            title="High Priority Task",
            priority=1
        )
        assert request.priority == 1

    def test_applied_categories_defaults(self):
        """Test AppliedCategories default values."""
        categories = AppliedCategories()
        assert categories.category1 is None
        assert categories.category25 is None

    def test_applied_categories_with_values(self):
        """Test AppliedCategories with values."""
        categories = AppliedCategories(
            category1=True,
            category2=False,
            category3=True
        )
        assert categories.category1 is True
        assert categories.category2 is False
        assert categories.category3 is True

    def test_error_response_defaults(self):
        """Test ErrorResponse default values."""
        response = ErrorResponse()
        assert response.code is None
        assert response.message is None

    def test_error_response_with_values(self):
        """Test ErrorResponse with values."""
        response = ErrorResponse(
            code="NotFound",
            message="Task not found"
        )
        assert response.code == "NotFound"
        assert response.message == "Task not found"
