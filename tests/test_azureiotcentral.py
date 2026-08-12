# Copyright (c) Microsoft Corporation. All rights reserved.

"""Unit tests for AzureiotcentralClient."""

import pytest
from unittest.mock import AsyncMock, patch

from azure.connectors.azureiotcentral import (
    AzureiotcentralClient,
    Device,
    DeviceCloudProperties,
    DeviceCommand,
    DeviceGroup,
    DeviceRelationship,
    Job,
    Organization,
    ScheduledJob,
    User,
    WorkflowTrigger,
    TRIGGER_OPERATIONS,
)
from azure.connectors.sdk import (
    ConnectorClientOptions,
    ConnectorException,
    ManagedIdentityTokenProvider,
)
from tests.conftest import MockResponse


BASE_URL = "https://example.azure.com/connections/test"


# Maps each public operation (method name without the "_async" suffix) to the
# keyword arguments required to invoke it. The "input" body argument is passed
# as an empty dict since send_async is mocked in every test.
OPERATION_ARGS = {
    "device_groups_list": {"application": "app-1"},
    "device_groups_get": {"device_group_id": "dg-1", "application": "app-1"},
    "device_groups_set": {"input": {}, "device_group_id": "dg-1", "application": "app-1"},
    "device_groups_remove": {"device_group_id": "dg-1", "application": "app-1"},
    "device_groups_get_devices": {"device_group_id": "dg-1", "application": "app-1"},
    "devices_get_cloud_properties": {"device_id": "d-1", "application": "app-1"},
    "devices_update_cloud_properties": {"input": {}, "device_id": "d-1", "application": "app-1"},
    "devices_execute_component_command": {
        "input": {},
        "device_id": "d-1",
        "component_name": "c-1",
        "command_name": "cmd-1",
        "application": "app-1",
    },
    "device_relationships_list": {"device_id": "d-1", "application": "app-1"},
    "device_relationships_get": {
        "device_id": "d-1",
        "relationship_id": "r-1",
        "application": "app-1",
    },
    "device_relationships_set": {
        "input": {},
        "relationship_id": "r-1",
        "device_id": "d-1",
        "application": "app-1",
    },
    "device_relationships_update": {
        "input": {},
        "device_id": "d-1",
        "relationship_id": "r-1",
        "application": "app-1",
    },
    "device_relationships_remove": {
        "device_id": "d-1",
        "relationship_id": "r-1",
        "application": "app-1",
    },
    "jobs_list": {"application": "app-1"},
    "jobs_get": {"job_id": "j-1", "application": "app-1"},
    "jobs_set": {"input": {}, "job_id": "j-1", "application": "app-1"},
    "jobs_get_devices": {"job_id": "j-1", "application": "app-1"},
    "jobs_stop": {"job_id": "j-1", "application": "app-1"},
    "jobs_resume": {"job_id": "j-1", "application": "app-1"},
    "jobs_rerun": {"job_id": "j-1", "rerun_id": "rr-1", "application": "app-1"},
    "organizations_list": {"application": "app-1"},
    "organizations_get": {"organization_id": "o-1", "application": "app-1"},
    "organizations_set": {
        "input": {},
        "organization_id": "o-1",
        "application": "app-1",
    },
    "organizations_remove": {"organization_id": "o-1", "application": "app-1"},
    "scheduled_jobs_list": {"application": "app-1"},
    "scheduled_jobs_get": {"scheduled_job_id": "sj-1", "application": "app-1"},
    "scheduled_jobs_set": {
        "input": {},
        "scheduled_job_id": "sj-1",
        "application": "app-1",
    },
    "scheduled_jobs_update": {
        "input": {},
        "scheduled_job_id": "sj-1",
        "application": "app-1",
    },
    "scheduled_jobs_remove": {"scheduled_job_id": "sj-1", "application": "app-1"},
    "scheduled_jobs_list_jobs": {"scheduled_job_id": "sj-1", "application": "app-1"},
    "devices_get": {"device_id": "d-1", "application": "app-1"},
    "devices_get_command_response": {
        "device_id": "d-1",
        "command_name": "cmd-1",
        "application": "app-1",
    },
    "devices_get_component_command_response": {
        "device_id": "d-1",
        "component_name": "c-1",
        "command_name": "cmd-1",
        "application": "app-1",
    },
    "devices_get_component_telemetry_value": {
        "device_id": "d-1",
        "component_name": "c-1",
        "telemetry_name": "t-1",
        "application": "app-1",
    },
    "devices_get_module_command_response": {
        "device_id": "d-1",
        "module": "m-1",
        "command_name": "cmd-1",
        "application": "app-1",
    },
    "devices_get_module_component_command_response": {
        "device_id": "d-1",
        "module": "m-1",
        "component_name": "c-1",
        "command_name": "cmd-1",
        "application": "app-1",
    },
    "devices_get_module_component_telemetry_value": {
        "device_id": "d-1",
        "module": "m-1",
        "component_name": "c-1",
        "telemetry_name": "t-1",
        "application": "app-1",
    },
    "devices_get_module_properties": {"device_id": "d-1", "module": "m-1", "application": "app-1"},
    "devices_get_module_telemetry_value": {
        "device_id": "d-1",
        "module": "m-1",
        "telemetry_name": "t-1",
        "application": "app-1",
    },
    "devices_get_properties": {"device_id": "d-1", "application": "app-1"},
    "devices_get_telemetry_value": {
        "device_id": "d-1",
        "telemetry_name": "t-1",
        "application": "app-1",
    },
    "devices_list": {"application": "app-1"},
    "devices_remove": {"device_id": "d-1", "application": "app-1"},
    "devices_run_command": {
        "input": {},
        "device_id": "d-1",
        "command_name": "cmd-1",
        "application": "app-1",
    },
    "devices_run_component_command": {
        "input": {},
        "device_id": "d-1",
        "component_name": "c-1",
        "command_name": "cmd-1",
        "application": "app-1",
    },
    "devices_run_module_command": {
        "input": {},
        "device_id": "d-1",
        "module": "m-1",
        "command_name": "cmd-1",
        "application": "app-1",
    },
    "devices_run_module_component_command": {
        "input": {},
        "device_id": "d-1",
        "module": "m-1",
        "component_name": "c-1",
        "command_name": "cmd-1",
        "application": "app-1",
    },
    "devices_set": {"input": {}, "device_id": "d-1", "application": "app-1"},
    "devices_update_module_properties": {
        "input": {},
        "device_id": "d-1",
        "module": "m-1",
        "application": "app-1",
    },
    "devices_update_properties": {"input": {}, "device_id": "d-1", "application": "app-1"},
    "device_templates_get": {"template_id": "tpl-1", "application": "app-1"},
    "device_templates_list": {"application": "app-1"},
    "device_templates_remove": {"template_id": "tpl-1", "application": "app-1"},
    "roles_get": {"role_id": "role-1", "application": "app-1"},
    "roles_list": {"application": "app-1"},
    "users_create": {"input": {}, "user_id": "u-1", "application": "app-1"},
    "users_get": {"user_id": "u-1", "application": "app-1"},
    "users_list": {"application": "app-1"},
    "users_remove": {"user_id": "u-1", "application": "app-1"},
    "users_update": {"input": {}, "user_id": "u-1", "application": "app-1"},
    "applications_list": {},
    "workflow_get_components": {"application": "app-1", "template": "tpl-1"},
    "workflow_get_capabilities": {"application": "app-1", "template": "tpl-1"},
    "workflow_get_capabilities_v1": {"application": "app-1", "template": "tpl-1"},
    "workflow_get_components_v1": {"application": "app-1", "template": "tpl-1"},
    "workflow_get_modules": {"application": "app-1", "template": "tpl-1"},
    "schema_device_cloud_properties": {"application": "app-1"},
    "schema_device_command": {"application": "app-1"},
    "schema_device_command_v1": {"application": "app-1"},
    "schema_device_properties": {"application": "app-1"},
    "schema_device_telemetry": {"application": "app-1"},
    "schema_job": {"application": "app-1"},
    "schema_scheduled_job": {"application": "app-1"},
    "schema_user": {"application": "app-1"},
    "schema_webhook_action_body": {"application": "app-1"},
}

ALL_OPERATIONS = sorted(OPERATION_ARGS.keys())


async def _invoke_operation(client: AzureiotcentralClient, operation: str):
    """Invoke an IoT Central operation by name for shared method tests."""
    method = getattr(client, f"{operation}_async")
    return await method(**OPERATION_ARGS[operation])


def _make_client(token_provider=None):
    """Create an AzureiotcentralClient for tests."""
    return AzureiotcentralClient(BASE_URL, token_provider=token_provider)


class TestAzureiotcentralClientInitialization:
    """Tests for AzureiotcentralClient initialization."""

    def test_init_with_valid_url_and_defaults(self):
        """Test initialization with valid URL and default parameters."""
        client = AzureiotcentralClient(BASE_URL)

        assert client._connection_runtime_url == BASE_URL
        assert client.connector_name == "azureiotcentral"
        assert isinstance(client._http_client._token_provider, ManagedIdentityTokenProvider)

    def test_init_with_trailing_slash(self):
        """Test that trailing slash is removed from URL."""
        client = AzureiotcentralClient(BASE_URL + "/")

        assert client._connection_runtime_url == BASE_URL

    def test_init_with_custom_token_provider(self, mock_token_provider):
        """Test initialization with custom token provider."""
        client = AzureiotcentralClient(BASE_URL, token_provider=mock_token_provider)

        assert client._http_client._token_provider is mock_token_provider

    def test_init_with_custom_options(self, mock_token_provider):
        """Test initialization with custom options."""
        options = ConnectorClientOptions(timeout_seconds=60.0, max_retry_attempts=5)
        client = AzureiotcentralClient(
            BASE_URL,
            token_provider=mock_token_provider,
            options=options,
        )

        assert client._options is options
        assert client._options.timeout_seconds == 60.0
        assert client._options.max_retry_attempts == 5

    def test_init_with_empty_url_raises_error(self):
        """Test that empty URL raises ValueError."""
        with pytest.raises(ValueError, match="connection_runtime_url cannot be None or empty"):
            AzureiotcentralClient("")

    def test_init_with_none_url_raises_error(self):
        """Test that None URL raises ValueError."""
        with pytest.raises(ValueError, match="connection_runtime_url cannot be None or empty"):
            AzureiotcentralClient(None)

    def test_connector_name_property(self, mock_token_provider):
        """Test connector_name property returns 'azureiotcentral'."""
        client = _make_client(mock_token_provider)

        assert client.connector_name == "azureiotcentral"


class TestAzureiotcentralClientLifecycle:
    """Tests for AzureiotcentralClient lifecycle methods."""

    @pytest.mark.asyncio
    async def test_close(self, mock_token_provider):
        """Test close method calls http_client.close."""
        client = _make_client(mock_token_provider)

        with patch.object(client._http_client, "close", new_callable=AsyncMock) as mock_close:
            await client.close()
            mock_close.assert_called_once()

    @pytest.mark.asyncio
    async def test_context_manager(self, mock_token_provider):
        """Test async context manager functionality."""
        with patch.object(AzureiotcentralClient, "close", new_callable=AsyncMock) as mock_close:
            async with AzureiotcentralClient(
                BASE_URL,
                token_provider=mock_token_provider,
            ) as client:
                assert isinstance(client, AzureiotcentralClient)

            mock_close.assert_called_once()


class TestAzureiotcentralClientMethods:
    """Success path tests for representative IoT Central methods."""

    @pytest.mark.asyncio
    async def test_devices_list_success(self, mock_token_provider):
        """Test devices_list_async returns parsed JSON and issues a GET."""
        client = _make_client(mock_token_provider)
        mock_response = MockResponse(status=200, text='{"value":[{"id":"d-1"}]}')

        with patch.object(
            client._http_client,
            "send_async",
            new_callable=AsyncMock,
            return_value=mock_response,
        ) as mock_send:
            result = await client.devices_list_async(application="app-1")

            assert result["value"][0]["id"] == "d-1"
            assert mock_send.call_args[0][0] == "GET"
            request_url = mock_send.call_args[0][1]
            assert "/api/v1/devices" in request_url
            assert "application=app-1" in request_url

    @pytest.mark.asyncio
    async def test_devices_get_targets_device_path(self, mock_token_provider):
        """Test devices_get_async builds the device-scoped path."""
        client = _make_client(mock_token_provider)
        mock_response = MockResponse(status=200, text='{"id":"d-1"}')

        with patch.object(
            client._http_client,
            "send_async",
            new_callable=AsyncMock,
            return_value=mock_response,
        ) as mock_send:
            result = await client.devices_get_async(device_id="d-1", application="app-1")

            assert result["id"] == "d-1"
            assert "/devices/d-1" in mock_send.call_args[0][1]

    @pytest.mark.asyncio
    async def test_device_groups_set_sends_put_and_body(self, mock_token_provider):
        """Test device_groups_set_async issues a PUT and forwards the body."""
        client = _make_client(mock_token_provider)
        mock_response = MockResponse(status=200, text='{"id":"dg-1"}')
        body = DeviceGroup(display_name="group")

        with patch.object(
            client._http_client,
            "send_async",
            new_callable=AsyncMock,
            return_value=mock_response,
        ) as mock_send:
            result = await client.device_groups_set_async(
                input=body,
                device_group_id="dg-1",
                application="app-1",
            )

            assert result["id"] == "dg-1"
            assert mock_send.call_args[0][0] == "PUT"
            assert "/deviceGroups/dg-1" in mock_send.call_args[0][1]
            assert mock_send.call_args.kwargs["body"] is body

    @pytest.mark.asyncio
    async def test_execute_component_command_sends_post_and_body(
        self,
        mock_token_provider,
    ):
        """Test devices_execute_component_command_async forwards the POST body."""
        client = _make_client(mock_token_provider)
        mock_response = MockResponse(status=200, text="{}")
        body = DeviceCommand()

        with patch.object(
            client._http_client,
            "send_async",
            new_callable=AsyncMock,
            return_value=mock_response,
        ) as mock_send:
            await client.devices_execute_component_command_async(
                input=body,
                device_id="d-1",
                component_name="component-1",
                command_name="command-1",
                application="app-1",
            )

            assert mock_send.call_args[0][0] == "POST"
            assert mock_send.call_args.kwargs["body"] is body

    @pytest.mark.asyncio
    async def test_device_relationships_update_sends_patch_and_body(
        self,
        mock_token_provider,
    ):
        """Test device_relationships_update_async forwards the PATCH body."""
        client = _make_client(mock_token_provider)
        mock_response = MockResponse(status=200, text="{}")
        body = DeviceRelationship()

        with patch.object(
            client._http_client,
            "send_async",
            new_callable=AsyncMock,
            return_value=mock_response,
        ) as mock_send:
            await client.device_relationships_update_async(
                input=body,
                device_id="d-1",
                relationship_id="relationship-1",
                application="app-1",
            )

            assert mock_send.call_args[0][0] == "PATCH"
            assert mock_send.call_args.kwargs["body"] is body

    @pytest.mark.asyncio
    async def test_device_groups_remove_returns_none(self, mock_token_provider):
        """Test device_groups_remove_async issues a DELETE and returns None."""
        client = _make_client(mock_token_provider)
        mock_response = MockResponse(status=204, text="")

        with patch.object(
            client._http_client,
            "send_async",
            new_callable=AsyncMock,
            return_value=mock_response,
        ) as mock_send:
            result = await client.device_groups_remove_async(
                device_group_id="dg-1",
                application="app-1",
            )

            assert result is None
            assert mock_send.call_args[0][0] == "DELETE"

    @pytest.mark.asyncio
    async def test_jobs_set_appends_optional_job_type(self, mock_token_provider):
        """Test jobs_set_async appends the optional jobType query param."""
        client = _make_client(mock_token_provider)
        mock_response = MockResponse(status=200, text='{"id":"j-1"}')

        with patch.object(
            client._http_client,
            "send_async",
            new_callable=AsyncMock,
            return_value=mock_response,
        ) as mock_send:
            await client.jobs_set_async(
                input=Job(display_name="job"),
                job_id="j-1",
                application="app-1",
                job_type="cloudProperty",
            )

            request_url = mock_send.call_args[0][1]
            assert "job_type=cloudProperty" in request_url

    @pytest.mark.asyncio
    async def test_devices_get_command_response_encodes_query_value(self, mock_token_provider):
        """Test optional query values are URL-encoded while keys stay literal."""
        client = _make_client(mock_token_provider)
        mock_response = MockResponse(status=200, text="{}")

        with patch.object(
            client._http_client,
            "send_async",
            new_callable=AsyncMock,
            return_value=mock_response,
        ) as mock_send:
            await client.devices_get_command_response_async(
                device_id="d-1",
                command_name="cmd-1",
                application="app one",
                template="tpl one",
            )

            request_url = mock_send.call_args[0][1]
            assert "application=app%20one" in request_url
            assert "template=tpl%20one" in request_url

    @pytest.mark.asyncio
    async def test_empty_body_returns_none(self, mock_token_provider):
        """Test a JSON-returning method returns None when the body is empty."""
        client = _make_client(mock_token_provider)
        mock_response = MockResponse(status=200, text="")

        with patch.object(
            client._http_client,
            "send_async",
            new_callable=AsyncMock,
            return_value=mock_response,
        ):
            result = await client.devices_list_async(application="app-1")

            assert result is None

    @pytest.mark.asyncio
    @pytest.mark.parametrize("operation", ALL_OPERATIONS)
    async def test_all_operations_success(self, mock_token_provider, operation):
        """Test every operation issues a request and returns without error."""
        client = _make_client(mock_token_provider)
        mock_response = MockResponse(status=200, text="{}")

        with patch.object(
            client._http_client,
            "send_async",
            new_callable=AsyncMock,
            return_value=mock_response,
        ) as mock_send:
            await _invoke_operation(client, operation)

            assert mock_send.call_count == 1
            assert mock_send.call_args[0][1].startswith(BASE_URL)


class TestAzureiotcentralClientErrorHandling:
    """Error handling tests that ensure all methods raise ConnectorException."""

    @pytest.mark.asyncio
    @pytest.mark.parametrize("operation", ALL_OPERATIONS)
    async def test_error_response_raises_exception_for_all_operations(
        self,
        mock_token_provider,
        operation,
    ):
        """Test non-2xx responses raise ConnectorException for every operation."""
        client = _make_client(mock_token_provider)
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


class TestAzureiotcentralTypeSerialization:
    """Tests for IoT Central connector dataclass defaults."""

    def test_dataclass_instances_initialize_expected_defaults(self):
        """Test generated dataclasses initialize with expected default values."""
        device_group = DeviceGroup()
        device = Device()
        device_command = DeviceCommand()
        cloud_properties = DeviceCloudProperties()
        relationship = DeviceRelationship()
        job = Job()
        organization = Organization()
        scheduled_job = ScheduledJob()
        user = User()
        trigger = WorkflowTrigger()

        assert device_group.id is None
        assert device.id is None
        assert device_command.request is None
        assert cloud_properties is not None
        assert relationship is not None
        assert job.id is None
        assert organization.id is None
        assert scheduled_job.id is None
        assert user.additional_properties == {}
        assert trigger.id is None


class TestAzureiotcentralTriggerOperations:
    """Tests for the module-level trigger registration metadata."""

    def test_workflow_create_trigger_registered_as_trigger(self):
        """Test the workflow create trigger route is registered as a trigger operation."""
        assert "Workflow_CreateTrigger" in TRIGGER_OPERATIONS
        trigger = TRIGGER_OPERATIONS["Workflow_CreateTrigger"]

        assert trigger["operation_id"] == "Workflow_CreateTrigger"
        assert trigger["method"] == "post"

    def test_workflow_create_trigger_not_a_client_method(self):
        """Test the trigger route is no longer exposed as a callable client method."""
        assert not hasattr(AzureiotcentralClient, "workflow_create_trigger_async")
