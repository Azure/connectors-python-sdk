# Copyright (c) Microsoft Corporation. All rights reserved.

"""Unit tests for AzureautomationClient."""

import pytest
from unittest.mock import AsyncMock, patch
from azure.connectors.azureautomation import (
    AzureautomationClient,
    CreateJobInput,
    CreateJobResponse,
    AutomationAccountResponse,
    SubscriptionListResult,
    Subscription,
    ResourceGroupListResult,
    ResourceGroup,
    RunbookListResults,
)
from azure.connectors.sdk import (
    ConnectorClientOptions,
    ManagedIdentityTokenProvider,
    ConnectorException,
)
from tests.conftest import MockResponse


class TestAzureautomationClientInitialization:
    """Tests for AzureautomationClient initialization."""

    def test_init_with_valid_url_and_defaults(self):
        """Test initialization with valid URL and default parameters."""
        client = AzureautomationClient(
            "https://example.azure.com/connections/test"
        )

        assert client._connection_runtime_url == (
            "https://example.azure.com/connections/test"
        )
        assert client.connector_name == "azureautomation"
        assert isinstance(
            client._http_client._token_provider, ManagedIdentityTokenProvider
        )

    def test_init_with_trailing_slash(self):
        """Test that trailing slash is removed from URL."""
        client = AzureautomationClient(
            "https://example.azure.com/connections/test/"
        )

        assert client._connection_runtime_url == (
            "https://example.azure.com/connections/test"
        )

    def test_init_with_custom_token_provider(self, mock_token_provider):
        """Test initialization with custom token provider."""
        client = AzureautomationClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        assert client._http_client._token_provider is mock_token_provider

    def test_init_with_custom_options(self, mock_token_provider):
        """Test initialization with custom options."""
        options = ConnectorClientOptions(
            timeout_seconds=60.0, max_retry_attempts=5
        )
        client = AzureautomationClient(
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
            AzureautomationClient("")

    def test_init_with_none_url_raises_error(self):
        """Test that None URL raises ValueError."""
        with pytest.raises(
            ValueError, match="connection_runtime_url cannot be None or empty"
        ):
            AzureautomationClient(None)

    def test_connector_name_property(self, mock_token_provider):
        """Test connector_name property returns 'azureautomation'."""
        client = AzureautomationClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        assert client.connector_name == "azureautomation"


class TestAzureautomationClientLifecycle:
    """Tests for AzureautomationClient lifecycle methods."""

    @pytest.mark.asyncio
    async def test_close(self, mock_token_provider):
        """Test close method calls http_client.close."""
        client = AzureautomationClient(
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
            AzureautomationClient, 'close', new_callable=AsyncMock
        ) as mock_close:
            async with AzureautomationClient(
                "https://example.azure.com/connections/test",
                token_provider=mock_token_provider
            ) as client:
                assert isinstance(client, AzureautomationClient)

            mock_close.assert_called_once()


class TestDataClasses:
    """Tests for data class creation and attributes."""

    def test_create_job_response(self):
        """Test CreateJobResponse dataclass creation."""
        response = CreateJobResponse(
            id="/subscriptions/xxx/jobs/job123",
            properties={"status": "Running", "runbookName": "MyRunbook"}
        )

        assert response.id == "/subscriptions/xxx/jobs/job123"
        assert response.properties["status"] == "Running"

    def test_automation_account_response(self):
        """Test AutomationAccountResponse dataclass creation."""
        response = AutomationAccountResponse(
            value=[
                {"name": "account1", "location": "eastus"},
                {"name": "account2", "location": "westus"}
            ]
        )

        assert len(response.value) == 2
        assert response.value[0]["name"] == "account1"

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

    def test_resource_group(self):
        """Test ResourceGroup dataclass creation."""
        rg = ResourceGroup(
            id="/subscriptions/xxx/resourceGroups/my-rg",
            name="my-rg",
            managed_by=None
        )

        assert rg.name == "my-rg"
        assert rg.managed_by is None

    def test_resource_group_list_result(self):
        """Test ResourceGroupListResult dataclass creation."""
        rg = ResourceGroup(name="rg1")
        result = ResourceGroupListResult(
            value=[rg],
            next_link=None
        )

        assert len(result.value) == 1
        assert result.next_link is None

    def test_runbook_list_results(self):
        """Test RunbookListResults dataclass creation."""
        result = RunbookListResults(
            value=[
                {"name": "Runbook1", "type": "PowerShell"},
                {"name": "Runbook2", "type": "Python"}
            ]
        )

        assert len(result.value) == 2
        assert result.value[0]["name"] == "Runbook1"


class TestEdgeCases:
    """Tests for edge cases and special scenarios."""

    @pytest.mark.asyncio
    async def test_http_client_property_access(self, mock_token_provider):
        """Test accessing http_client property."""
        client = AzureautomationClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        assert client.http_client is not None
        assert client._http_client is client.http_client

    def test_dataclass_defaults(self):
        """Test dataclass default values."""
        response = CreateJobResponse()
        assert response.id is None
        assert response.properties is None

        subscription = Subscription()
        assert subscription.subscription_id is None
        assert subscription.display_name is None

    def test_multiple_client_instances(self, mock_token_provider):
        """Test creating multiple client instances."""
        client1 = AzureautomationClient(
            "https://example1.azure.com/connections/test",
            token_provider=mock_token_provider
        )
        client2 = AzureautomationClient(
            "https://example2.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        assert client1._connection_runtime_url != client2._connection_runtime_url
        assert client1.connector_name == client2.connector_name


class TestGetJobOutputAsync:
    """Tests for get_job_output_async method."""

    @pytest.mark.asyncio
    async def test_success_returns_content(self, mock_token_provider):
        """Test successful job output retrieval returns content."""
        client = AzureautomationClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(
            status=200,
            text="Job output content here",
            content=b"Job output content here"
        )

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ) as mock_send:
            result = await client.get_job_output_async(
                subscription_id="sub123",
                resource_group_name="rg-test",
                automation_account="myAutomation",
                job_id="job456"
            )

            mock_send.assert_called_once()
            call_args = mock_send.call_args
            assert call_args[0][0] == "GET"
            assert "/subscriptions/sub123" in call_args[0][1]
            assert "/resourceGroups/rg-test" in call_args[0][1]
            assert "/automationAccounts/myAutomation" in call_args[0][1]
            assert "/jobs/job456/output" in call_args[0][1]
            assert result == b"Job output content here"

    @pytest.mark.asyncio
    async def test_error_response_raises_exception(self, mock_token_provider):
        """Test that non-2xx response raises ConnectorException."""
        client = AzureautomationClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(
            status=404,
            text="Not found"
        )

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ):
            with pytest.raises(ConnectorException) as exc_info:
                await client.get_job_output_async(
                    subscription_id="sub123",
                    resource_group_name="rg-test",
                    automation_account="myAutomation",
                    job_id="job456"
                )

            assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    async def test_method_exists(self, mock_token_provider):
        """Test that get_job_output_async method exists on client."""
        client = AzureautomationClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        assert hasattr(client, 'get_job_output_async')
        assert callable(client.get_job_output_async)


class TestGetStatusOfJobAsync:
    """Tests for get_status_of_job_async method."""

    @pytest.mark.asyncio
    async def test_success_with_json_response(self, mock_token_provider):
        """Test successful job status retrieval with JSON response."""
        client = AzureautomationClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(
            status=200,
            text='{"id": "/subscriptions/xxx/jobs/job123", "properties": {"status": "Running"}}'
        )

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ) as mock_send:
            result = await client.get_status_of_job_async(
                subscription_id="sub123",
                resource_group_name="rg-test",
                automation_account="myAutomation",
                job_id="job456"
            )

            mock_send.assert_called_once()
            call_args = mock_send.call_args
            assert call_args[0][0] == "GET"
            assert "/subscriptions/sub123" in call_args[0][1]
            assert "/resourceGroups/rg-test" in call_args[0][1]
            assert "/automationAccounts/myAutomation" in call_args[0][1]
            assert "/jobs/job456" in call_args[0][1]
            assert "/output" not in call_args[0][1]
            assert result["properties"]["status"] == "Running"

    @pytest.mark.asyncio
    async def test_success_with_empty_response(self, mock_token_provider):
        """Test successful request with empty response body."""
        client = AzureautomationClient(
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
            result = await client.get_status_of_job_async(
                subscription_id="sub123",
                resource_group_name="rg-test",
                automation_account="myAutomation",
                job_id="job456"
            )

            assert result is None

    @pytest.mark.asyncio
    async def test_error_response_raises_exception(self, mock_token_provider):
        """Test that non-2xx response raises ConnectorException."""
        client = AzureautomationClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(
            status=500,
            text="Server error"
        )

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ):
            with pytest.raises(ConnectorException) as exc_info:
                await client.get_status_of_job_async(
                    subscription_id="sub123",
                    resource_group_name="rg-test",
                    automation_account="myAutomation",
                    job_id="job456"
                )

            assert exc_info.value.status_code == 500

    @pytest.mark.asyncio
    async def test_method_exists(self, mock_token_provider):
        """Test that get_status_of_job_async method exists on client."""
        client = AzureautomationClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        assert hasattr(client, 'get_status_of_job_async')
        assert callable(client.get_status_of_job_async)


class TestCreateJobAsync:
    """Tests for create_job_async method."""

    @pytest.mark.asyncio
    async def test_success_with_json_response(self, mock_token_provider):
        """Test successful job creation with JSON response."""
        client = AzureautomationClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(
            status=200,
            text=(
                '{"id": "/subscriptions/xxx/jobs/newjob123", '
                '"properties": {"status": "New", "runbook": {"name": "MyRunbook"}}}'
            )
        )

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ) as mock_send:
            result = await client.create_job_async(
                input=CreateJobInput(),
                subscription_id="sub123",
                resource_group_name="rg-test",
                automation_account="myAutomation"
            )

            mock_send.assert_called_once()
            call_args = mock_send.call_args
            assert call_args[0][0] == "PUT"
            assert "/subscriptions/sub123" in call_args[0][1]
            assert "/resourceGroups/rg-test" in call_args[0][1]
            assert "/automationAccounts/myAutomation" in call_args[0][1]
            assert "/jobs" in call_args[0][1]
            assert result["properties"]["status"] == "New"

    @pytest.mark.asyncio
    async def test_success_with_wait_parameter(self, mock_token_provider):
        """Test job creation with wait parameter."""
        client = AzureautomationClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(
            status=200,
            text=(
                '{"id": "/subscriptions/xxx/jobs/newjob123", '
                '"properties": {"status": "Completed"}}'
            )
        )

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ) as mock_send:
            result = await client.create_job_async(
                input=CreateJobInput(),
                subscription_id="sub123",
                resource_group_name="rg-test",
                automation_account="myAutomation",
                wait="true"
            )

            mock_send.assert_called_once()
            call_args = mock_send.call_args
            assert call_args[0][0] == "PUT"
            assert "wait=true" in call_args[0][1]
            assert result["properties"]["status"] == "Completed"

    @pytest.mark.asyncio
    async def test_success_with_empty_response(self, mock_token_provider):
        """Test successful job creation with empty response body."""
        client = AzureautomationClient(
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
            result = await client.create_job_async(
                input=CreateJobInput(),
                subscription_id="sub123",
                resource_group_name="rg-test",
                automation_account="myAutomation"
            )

            assert result is None

    @pytest.mark.asyncio
    async def test_error_response_raises_exception(self, mock_token_provider):
        """Test that non-2xx response raises ConnectorException."""
        client = AzureautomationClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(
            status=400,
            text="Bad request"
        )

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ):
            with pytest.raises(ConnectorException) as exc_info:
                await client.create_job_async(
                    input=CreateJobInput(),
                    subscription_id="sub123",
                    resource_group_name="rg-test",
                    automation_account="myAutomation"
                )

            assert exc_info.value.status_code == 400

    @pytest.mark.asyncio
    async def test_method_exists(self, mock_token_provider):
        """Test that create_job_async method exists on client."""
        client = AzureautomationClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        assert hasattr(client, 'create_job_async')
        assert callable(client.create_job_async)

    @pytest.mark.asyncio
    async def test_wait_parameter_is_optional(self, mock_token_provider):
        """Test that wait parameter is optional."""
        client = AzureautomationClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(
            status=200,
            text='{"id": "job123"}'
        )

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ) as mock_send:
            # Call without wait parameter
            await client.create_job_async(
                input=CreateJobInput(),
                subscription_id="sub123",
                resource_group_name="rg-test",
                automation_account="myAutomation"
            )
            call_args = mock_send.call_args
            assert "wait=" not in call_args[0][1]

            mock_send.reset_mock()

            # Call with wait parameter
            await client.create_job_async(
                input=CreateJobInput(),
                subscription_id="sub123",
                resource_group_name="rg-test",
                automation_account="myAutomation",
                wait="true"
            )
            call_args = mock_send.call_args
            assert "wait=true" in call_args[0][1]
