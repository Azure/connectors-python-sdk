# Copyright (c) Microsoft Corporation. All rights reserved.

"""Unit tests for AzuredatafactoryClient."""

import pytest
from unittest.mock import AsyncMock, patch
from azure.connectors.azuredatafactory import (
    AzuredatafactoryClient,
    CreatePipelineRunResponse,
    PipelineRun,
    DataFactoryListResult,
    DataFactory,
    PipelineListResult,
    Pipeline,
    Activity,
    ActivityFull,
    ParameterValueSpecification,
    SubscriptionListResult,
    Subscription,
    SubscriptionPolicies,
    ResourceGroupListResult,
    ResourceGroup,
    ResourceGroupProperties,
)
from azure.connectors.sdk import (
    ConnectorClientOptions,
    ManagedIdentityTokenProvider,
    ConnectorException,
)
from tests.conftest import MockResponse


class TestAzuredatafactoryClientInitialization:
    """Tests for AzuredatafactoryClient initialization."""

    def test_init_with_valid_url_and_defaults(self):
        """Test initialization with valid URL and default parameters."""
        client = AzuredatafactoryClient(
            "https://example.azure.com/connections/test"
        )

        assert client._connection_runtime_url == (
            "https://example.azure.com/connections/test"
        )
        assert client.connector_name == "azuredatafactory"
        assert isinstance(
            client._http_client._token_provider, ManagedIdentityTokenProvider
        )

    def test_init_with_trailing_slash(self):
        """Test that trailing slash is removed from URL."""
        client = AzuredatafactoryClient(
            "https://example.azure.com/connections/test/"
        )

        assert client._connection_runtime_url == (
            "https://example.azure.com/connections/test"
        )

    def test_init_with_custom_token_provider(self, mock_token_provider):
        """Test initialization with custom token provider."""
        client = AzuredatafactoryClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        assert client._http_client._token_provider is mock_token_provider

    def test_init_with_custom_options(self, mock_token_provider):
        """Test initialization with custom options."""
        options = ConnectorClientOptions(
            timeout_seconds=60.0, max_retry_attempts=5
        )
        client = AzuredatafactoryClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider,
            options=options
        )

        assert client._options is options
        assert client._options.timeout_seconds == 60.0
        assert client._options.max_retry_attempts == 5

    def test_init_with_empty_url_raises_error(self):
        """Test that empty URL raises ValueError."""
        with pytest.raises(
            ValueError, match="connection_runtime_url cannot be None or empty"
        ):
            AzuredatafactoryClient("")

    def test_init_with_none_url_raises_error(self):
        """Test that None URL raises ValueError."""
        with pytest.raises(
            ValueError, match="connection_runtime_url cannot be None or empty"
        ):
            AzuredatafactoryClient(None)

    def test_connector_name_property(self, mock_token_provider):
        """Test connector_name property returns 'azuredatafactory'."""
        client = AzuredatafactoryClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        assert client.connector_name == "azuredatafactory"


class TestAzuredatafactoryClientLifecycle:
    """Tests for AzuredatafactoryClient lifecycle methods."""

    @pytest.mark.asyncio
    async def test_close(self, mock_token_provider):
        """Test close method calls http_client.close."""
        client = AzuredatafactoryClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        with patch.object(
            client._http_client, 'close', new_callable=AsyncMock
        ) as mock_close:
            await client.close()
            mock_close.assert_called_once()

    @pytest.mark.asyncio
    async def test_context_manager(self, mock_token_provider):
        """Test async context manager functionality."""
        with patch.object(
            AzuredatafactoryClient, 'close', new_callable=AsyncMock
        ) as mock_close:
            async with AzuredatafactoryClient(
                "https://example.azure.com/connections/test",
                token_provider=mock_token_provider
            ) as client:
                assert isinstance(client, AzuredatafactoryClient)

            mock_close.assert_called_once()


class TestCreatePipelineRunAsync:
    """Tests for create_pipeline_run_async method."""

    @pytest.mark.asyncio
    async def test_success_with_json_response(self, mock_token_provider):
        """Test successful pipeline run creation with JSON response."""
        client = AzuredatafactoryClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(
            status=200,
            text='{"runId": "run-12345"}'
        )

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ) as mock_send:
            input_data = ParameterValueSpecification(
                additional_properties={"param1": "value1"}
            )
            result = await client.create_pipeline_run_async(
                input=input_data,
                subscription_id="sub-123",
                resource_group_name="rg-test",
                data_factory_name="adf-test",
                pipeline_name="pipeline-test"
            )

            mock_send.assert_called_once()
            call_args = mock_send.call_args
            assert call_args[0][0] == "POST"
            assert "/CreateRun" in call_args[0][1]
            assert result["runId"] == "run-12345"

    @pytest.mark.asyncio
    async def test_success_with_reference_pipeline_run_id(
        self, mock_token_provider
    ):
        """Test pipeline run creation with reference pipeline run ID."""
        client = AzuredatafactoryClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(
            status=200,
            text='{"runId": "run-67890"}'
        )

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ) as mock_send:
            input_data = ParameterValueSpecification()
            result = await client.create_pipeline_run_async(
                input=input_data,
                subscription_id="sub-123",
                resource_group_name="rg-test",
                data_factory_name="adf-test",
                pipeline_name="pipeline-test",
                reference_pipeline_run_id="ref-run-001"
            )

            call_args = mock_send.call_args
            assert "referencePipelineRunId=" in call_args[0][1]
            assert result["runId"] == "run-67890"

    @pytest.mark.asyncio
    async def test_success_with_empty_response(self, mock_token_provider):
        """Test successful request with empty response body."""
        client = AzuredatafactoryClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(status=200, text="")

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ):
            input_data = ParameterValueSpecification()
            result = await client.create_pipeline_run_async(
                input=input_data,
                subscription_id="sub-123",
                resource_group_name="rg-test",
                data_factory_name="adf-test",
                pipeline_name="pipeline-test"
            )

            assert result is None

    @pytest.mark.asyncio
    async def test_error_response_raises_exception(self, mock_token_provider):
        """Test that non-2xx response raises ConnectorException."""
        client = AzuredatafactoryClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(
            status=400,
            text='{"error": "Invalid pipeline"}'
        )

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ):
            input_data = ParameterValueSpecification()

            with pytest.raises(ConnectorException) as exc_info:
                await client.create_pipeline_run_async(
                    input=input_data,
                    subscription_id="sub-123",
                    resource_group_name="rg-test",
                    data_factory_name="adf-test",
                    pipeline_name="pipeline-test"
                )

            assert exc_info.value.status_code == 400

    @pytest.mark.asyncio
    async def test_method_exists(self, mock_token_provider):
        """Test that create_pipeline_run_async method exists on client."""
        client = AzuredatafactoryClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        assert hasattr(client, 'create_pipeline_run_async')
        assert callable(client.create_pipeline_run_async)


class TestCancelPipelineRunAsync:
    """Tests for cancel_pipeline_run_async method."""

    @pytest.mark.asyncio
    async def test_success(self, mock_token_provider):
        """Test successful pipeline run cancellation."""
        client = AzuredatafactoryClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(status=200, text="")

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ) as mock_send:
            await client.cancel_pipeline_run_async(
                subscription_id="sub-123",
                resource_group_name="rg-test",
                data_factory_name="adf-test",
                pipeline_run_name="run-12345"
            )

            mock_send.assert_called_once()
            call_args = mock_send.call_args
            assert call_args[0][0] == "POST"
            assert "/cancelpipelineRun/" in call_args[0][1]

    @pytest.mark.asyncio
    async def test_method_exists(self, mock_token_provider):
        """Test that cancel_pipeline_run_async method exists on client."""
        client = AzuredatafactoryClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        assert hasattr(client, 'cancel_pipeline_run_async')
        assert callable(client.cancel_pipeline_run_async)


class TestGetPipelineRunAsync:
    """Tests for get_pipeline_run_async method."""

    @pytest.mark.asyncio
    async def test_success_with_json_response(self, mock_token_provider):
        """Test successful pipeline run retrieval with JSON response."""
        client = AzuredatafactoryClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(
            status=200,
            text='{"runId": "run-12345", "pipelineName": "test-pipeline", '
                 '"status": "Succeeded"}'
        )

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ) as mock_send:
            result = await client.get_pipeline_run_async(
                subscription_id="sub-123",
                resource_group_name="rg-test",
                data_factory_name="adf-test",
                pipeline_run_name="run-12345"
            )

            mock_send.assert_called_once()
            call_args = mock_send.call_args
            assert call_args[0][0] == "GET"
            assert "/pipelineRuns/" in call_args[0][1]
            assert result["runId"] == "run-12345"
            assert result["status"] == "Succeeded"

    @pytest.mark.asyncio
    async def test_success_with_empty_response(self, mock_token_provider):
        """Test successful request with empty response body."""
        client = AzuredatafactoryClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(status=200, text="")

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ):
            result = await client.get_pipeline_run_async(
                subscription_id="sub-123",
                resource_group_name="rg-test",
                data_factory_name="adf-test",
                pipeline_run_name="run-12345"
            )

            assert result is None

    @pytest.mark.asyncio
    async def test_error_response_raises_exception(self, mock_token_provider):
        """Test that non-2xx response raises ConnectorException."""
        client = AzuredatafactoryClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(
            status=404,
            text='{"error": "Pipeline run not found"}'
        )

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ):
            with pytest.raises(ConnectorException) as exc_info:
                await client.get_pipeline_run_async(
                    subscription_id="sub-123",
                    resource_group_name="rg-test",
                    data_factory_name="adf-test",
                    pipeline_run_name="run-12345"
                )

            assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    async def test_method_exists(self, mock_token_provider):
        """Test that get_pipeline_run_async method exists on client."""
        client = AzuredatafactoryClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        assert hasattr(client, 'get_pipeline_run_async')
        assert callable(client.get_pipeline_run_async)


class TestDataClasses:
    """Tests for data class creation and attributes."""

    def test_create_pipeline_run_response(self):
        """Test CreatePipelineRunResponse dataclass creation."""
        response = CreatePipelineRunResponse(run_id="run-12345")

        assert response.run_id == "run-12345"

    def test_pipeline_run(self):
        """Test PipelineRun dataclass creation."""
        run = PipelineRun(
            run_id="run-12345",
            pipeline_name="test-pipeline",
            status="Succeeded",
            duration_in_ms=5000,
            parameters={"param1": "value1"}
        )

        assert run.run_id == "run-12345"
        assert run.pipeline_name == "test-pipeline"
        assert run.status == "Succeeded"
        assert run.duration_in_ms == 5000

    def test_data_factory(self):
        """Test DataFactory dataclass creation."""
        factory = DataFactory(
            name="adf-test",
            id="/subscriptions/xxx/resourceGroups/rg/providers/"
               "Microsoft.DataFactory/factories/adf-test",
            location="eastus",
            tags={"env": "test"}
        )

        assert factory.name == "adf-test"
        assert factory.location == "eastus"

    def test_data_factory_list_result(self):
        """Test DataFactoryListResult dataclass creation."""
        factory = DataFactory(name="adf-1")
        result = DataFactoryListResult(
            value=[factory],
            next_link="https://management.azure.com/nextpage"
        )

        assert len(result.value) == 1
        assert result.next_link is not None

    def test_pipeline(self):
        """Test Pipeline dataclass creation."""
        pipeline = Pipeline(
            id="/subscriptions/xxx/pipelines/test",
            name="test-pipeline",
            etag="abc123"
        )

        assert pipeline.name == "test-pipeline"
        assert pipeline.etag == "abc123"

    def test_pipeline_list_result(self):
        """Test PipelineListResult dataclass creation."""
        pipeline = Pipeline(name="pipeline-1")
        result = PipelineListResult(
            value=[pipeline],
            next_link=None
        )

        assert len(result.value) == 1
        assert result.next_link is None

    def test_activity(self):
        """Test Activity dataclass creation."""
        activity = Activity(
            additional_properties={"name": "CopyActivity", "type": "Copy"}
        )

        assert activity.additional_properties["name"] == "CopyActivity"

    def test_activity_full(self):
        """Test ActivityFull dataclass creation."""
        activity = ActivityFull(
            name="CopyData",
            type_="Copy",
            inputs=[{"name": "input1"}],
            outputs=[{"name": "output1"}]
        )

        assert activity.name == "CopyData"
        assert activity.type_ == "Copy"
        assert len(activity.inputs) == 1

    def test_parameter_value_specification(self):
        """Test ParameterValueSpecification dataclass creation."""
        params = ParameterValueSpecification(
            additional_properties={"param1": "value1", "param2": 123}
        )

        assert params.additional_properties["param1"] == "value1"
        assert params.additional_properties["param2"] == 123

    def test_subscription(self):
        """Test Subscription dataclass creation."""
        subscription = Subscription(
            id="/subscriptions/00000000-0000-0000-0000-000000000000",
            subscription_id="00000000-0000-0000-0000-000000000000",
            tenant_id="11111111-1111-1111-1111-111111111111",
            display_name="My Subscription",
            state="Enabled"
        )

        assert subscription.display_name == "My Subscription"
        assert subscription.state == "Enabled"

    def test_subscription_list_result(self):
        """Test SubscriptionListResult dataclass creation."""
        subscription = Subscription(
            subscription_id="sub123",
            display_name="Test Sub"
        )
        result = SubscriptionListResult(
            value=[subscription],
            next_link="https://management.azure.com/nextpage"
        )

        assert len(result.value) == 1
        assert result.next_link is not None

    def test_subscription_policies(self):
        """Test SubscriptionPolicies dataclass creation."""
        policies = SubscriptionPolicies(
            location_placement_id="Public_2014-09-01",
            quota_id="QuotaId_1",
            spending_limit="On"
        )

        assert policies.quota_id == "QuotaId_1"
        assert policies.spending_limit == "On"

    def test_resource_group(self):
        """Test ResourceGroup dataclass creation."""
        rg = ResourceGroup(
            id="/subscriptions/xxx/resourceGroups/my-rg",
            name="my-rg",
            location="eastus",
            managed_by=None
        )

        assert rg.name == "my-rg"
        assert rg.location == "eastus"

    def test_resource_group_list_result(self):
        """Test ResourceGroupListResult dataclass creation."""
        rg = ResourceGroup(name="rg1")
        result = ResourceGroupListResult(
            value=[rg],
            next_link=None
        )

        assert len(result.value) == 1
        assert result.next_link is None

    def test_resource_group_properties(self):
        """Test ResourceGroupProperties dataclass creation."""
        props = ResourceGroupProperties(provisioning_state="Succeeded")

        assert props.provisioning_state == "Succeeded"


class TestEdgeCases:
    """Tests for edge cases and special scenarios."""

    @pytest.mark.asyncio
    async def test_http_client_property_access(self, mock_token_provider):
        """Test accessing http_client property."""
        client = AzuredatafactoryClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        assert client.http_client is not None
        assert client._http_client is client.http_client

    def test_dataclass_defaults(self):
        """Test dataclass default values."""
        response = CreatePipelineRunResponse()
        assert response.run_id is None

        run = PipelineRun()
        assert run.run_id is None
        assert run.status is None

        factory = DataFactory()
        assert factory.name is None
        assert factory.location is None

    def test_multiple_client_instances(self, mock_token_provider):
        """Test creating multiple client instances."""
        client1 = AzuredatafactoryClient(
            "https://example1.azure.com/connections/test",
            token_provider=mock_token_provider
        )
        client2 = AzuredatafactoryClient(
            "https://example2.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        assert client1._connection_runtime_url != client2._connection_runtime_url
        assert client1.connector_name == client2.connector_name
