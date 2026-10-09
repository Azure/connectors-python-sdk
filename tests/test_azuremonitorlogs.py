# Copyright (c) Microsoft Corporation. All rights reserved.

"""Unit tests for AzuremonitorlogsClient."""

import pytest
from unittest.mock import AsyncMock, patch
from azure.core.credentials import AzureKeyCredential
from azure.connectors.azuremonitorlogs import (
    AzuremonitorlogsClient,
    QueryDataInput,
    QuerySchemaInput,
    VisualizeQueryInput,
    Subscription,
    SubscriptionListResult,
    ResourceGroup,
    ResourceItem,
    TimeRangeItem,
)
from azure.connectors.sdk import (
    ConnectorException,
)
from tests.conftest import MockResponse
from tests.generated_connector_test_utils import resolve_generated_result


class TestAzuremonitorlogsClientInitialization:
    """Tests for AzuremonitorlogsClient initialization."""

    def test_init_with_valid_url_and_defaults(self):
        """Test initialization with valid URL and default parameters."""
        client = AzuremonitorlogsClient(
            "https://example.azure.com/connections/test",
            AzureKeyCredential("test-key"),
        )

        assert client._connection_runtime_url == (
            "https://example.azure.com/connections/test"
        )
        assert client.connector_name == "azuremonitorlogs"
        assert isinstance(
            client._http_client._credential, AzureKeyCredential
        )

    def test_init_with_trailing_slash(self):
        """Test that trailing slash is removed from URL."""
        client = AzuremonitorlogsClient(
            "https://example.azure.com/connections/test/",
            AzureKeyCredential("test-key"),
        )

        assert client._connection_runtime_url == (
            "https://example.azure.com/connections/test"
        )

    def test_init_with_custom_credential(self, mock_credential):
        """Test initialization with custom token provider."""
        client = AzuremonitorlogsClient(
            "https://example.azure.com/connections/test",
            credential=mock_credential,
        )

        assert client._http_client._credential is mock_credential

    def test_init_with_custom_settings(self, mock_credential):
        """Test initialization with custom pipeline settings."""
        client = AzuremonitorlogsClient(
            "https://example.azure.com/connections/test",
            credential=mock_credential,
            timeout_seconds=60.0,
            max_retry_attempts=5,
        )
        assert client._http_client._timeout_seconds == 60.0

    def test_init_with_empty_url_raises_error(self):
        """Test that empty URL raises ValueError."""
        with pytest.raises(
            ValueError,
            match="connection_runtime_url cannot be None or empty",
        ):
            AzuremonitorlogsClient("", AzureKeyCredential("test-key"))

    def test_init_with_none_url_raises_error(self):
        """Test that None URL raises ValueError."""
        with pytest.raises(
            ValueError,
            match="connection_runtime_url cannot be None or empty",
        ):
            AzuremonitorlogsClient(None, AzureKeyCredential("test-key"))


class TestAzuremonitorlogsClientLifecycle:
    """Tests for AzuremonitorlogsClient lifecycle methods."""

    @pytest.mark.asyncio
    async def test_close(self, mock_credential):
        """Test close method calls http_client.close."""
        client = AzuremonitorlogsClient(
            "https://example.azure.com/connections/test",
            credential=mock_credential,
        )

        with patch.object(
            client._http_client,
            "close",
            new_callable=AsyncMock,
        ) as mock_close:
            await client.close()
            mock_close.assert_called_once()

    @pytest.mark.asyncio
    async def test_context_manager(self, mock_credential):
        """Test async context manager functionality."""
        with patch.object(
            AzuremonitorlogsClient,
            "close",
            new_callable=AsyncMock,
        ) as mock_close:
            async with AzuremonitorlogsClient(
                "https://example.azure.com/connections/test",
                credential=mock_credential,
            ) as client:
                assert isinstance(client, AzuremonitorlogsClient)

            mock_close.assert_called_once()


class TestDataClasses:
    """Tests for data class creation and attributes."""

    def test_subscription(self):
        """Test Subscription dataclass creation."""
        subscription = Subscription(
            id="/subscriptions/sub-id",
            subscription_id="sub-id",
            authorization_source="RoleBased",
        )

        assert subscription.subscription_id == "sub-id"
        assert subscription.authorization_source == "RoleBased"

    def test_subscription_list_result(self):
        """Test SubscriptionListResult dataclass creation."""
        subscription = Subscription(subscription_id="sub-id")
        result = SubscriptionListResult(
            value=[subscription],
            next_link="https://next.example.com",
        )

        assert len(result.value) == 1
        assert result.next_link is not None

    def test_resource_group_and_item(self):
        """Test ResourceGroup and ResourceItem dataclass creation."""
        resource_group = ResourceGroup(
            id="/subscriptions/sub-id/resourceGroups/rg1",
            name="rg1",
        )
        resource_item = ResourceItem(
            id="/subscriptions/sub-id/resourceGroups/rg1/providers/x/y",
            name="my-resource",
        )

        assert resource_group.name == "rg1"
        assert resource_item.name == "my-resource"

    def test_time_range_item(self):
        """Test TimeRangeItem dataclass creation."""
        item = TimeRangeItem(id=1, name="Relative")

        assert item.id == 1
        assert item.name == "Relative"


class TestListSubscriptionsAsync:
    """Tests for list_subscriptions_async method."""

    @pytest.mark.asyncio
    async def test_success_returns_json(self, mock_credential):
        """Test successful response returns parsed JSON."""
        client = AzuremonitorlogsClient(
            "https://example.azure.com/connections/test",
            credential=mock_credential,
        )

        mock_response = MockResponse(
            status=200,
            text='{"value": [{"subscriptionId": "sub-id"}]}'
        )

        with patch.object(
            client._http_client,
            "send_async",
            new_callable=AsyncMock,
            return_value=mock_response,
        ) as mock_send:
            result = await resolve_generated_result(client.list_subscriptions_async())

            mock_send.assert_called_once_with(
                "GET",
                "https://example.azure.com/connections/test/listSubscriptions",
                body=None,
                timeout=None,
                headers=None,
                client_request_id=None,
                response_hook=None,
            )
            assert result[0]["subscriptionId"] == "sub-id"

    @pytest.mark.asyncio
    async def test_error_response_raises_exception(self, mock_credential):
        """Test non-2xx response raises ConnectorException."""
        client = AzuremonitorlogsClient(
            "https://example.azure.com/connections/test",
            credential=mock_credential,
        )

        with patch.object(
            client._http_client,
            "send_async",
            new_callable=AsyncMock,
            return_value=MockResponse(status=500, text="Server error"),
        ):
            with pytest.raises(ConnectorException) as exc_info:
                await resolve_generated_result(client.list_subscriptions_async())

            assert exc_info.value.status_code == 500


class TestListResourceGroupsAsync:
    """Tests for list_resource_groups_async method."""

    @pytest.mark.asyncio
    async def test_success_appends_query_params(self, mock_credential):
        """Test subscription query parameter is appended to URL."""
        client = AzuremonitorlogsClient(
            "https://example.azure.com/connections/test",
            credential=mock_credential,
        )

        with patch.object(
            client._http_client,
            "send_async",
            new_callable=AsyncMock,
            return_value=MockResponse(status=200, text='{"value": []}'),
        ) as mock_send:
            await resolve_generated_result(
                client.list_resource_groups_async(subscriptions="sub-id")
            )

            call_args = mock_send.call_args
            assert call_args.args[0] == "GET"
            assert (
                call_args.args[1]
                == "https://example.azure.com/connections/test/"
                "listResourceGroups?subscriptions=sub-id"
            )
            assert call_args.kwargs["body"] is None


class TestListResourcesAsync:
    """Tests for list_resources_async method."""

    @pytest.mark.asyncio
    async def test_success_appends_multiple_query_params(
        self,
        mock_credential,
    ):
        """Test all resource filters are appended to URL."""
        client = AzuremonitorlogsClient(
            "https://example.azure.com/connections/test",
            credential=mock_credential,
        )

        with patch.object(
            client._http_client,
            "send_async",
            new_callable=AsyncMock,
            return_value=MockResponse(status=200, text='{"value": []}'),
        ) as mock_send:
            await resolve_generated_result(client.list_resources_async(
                subscriptions="sub-id",
                resourcegroups="rg1",
                resourcetype="Microsoft.OperationalInsights/workspaces",
            ))

            request_url = mock_send.call_args.args[1]
            assert "listResources?" in request_url
            assert "subscriptions=sub-id" in request_url
            assert "resourcegroups=rg1" in request_url
            assert "resourcetype=Microsoft.OperationalInsights%2Fworkspaces" in request_url


class TestQueryDataAsync:
    """Tests for query_data_async method."""

    @pytest.mark.asyncio
    async def test_success_sends_body_and_returns_json(self, mock_credential):
        """Test successful query sends body and returns parsed JSON."""
        client = AzuremonitorlogsClient(
            "https://example.azure.com/connections/test",
            credential=mock_credential,
        )

        request_body = QueryDataInput(
            query="Heartbeat | take 1",
            timerangetype="SetInQuery",
        )

        with patch.object(
            client._http_client,
            "send_async",
            new_callable=AsyncMock,
            return_value=MockResponse(status=200, text='{"value": [{"Computer": "vm1"}]}'),
        ) as mock_send:
            result = await client.query_data_async(
                input=request_body,
                subscriptions="sub-id",
                resourcegroups="rg1",
                resourcetype="Microsoft.OperationalInsights/workspaces",
                resourcename="workspace1",
            )

            assert result["value"][0]["Computer"] == "vm1"
            assert mock_send.call_args.args[0] == "POST"
            assert mock_send.call_args.kwargs["body"] is request_body

    @pytest.mark.asyncio
    async def test_empty_response_returns_none(self, mock_credential):
        """Test successful empty response returns None."""
        client = AzuremonitorlogsClient(
            "https://example.azure.com/connections/test",
            credential=mock_credential,
        )

        with patch.object(
            client._http_client,
            "send_async",
            new_callable=AsyncMock,
            return_value=MockResponse(status=200, text=""),
        ):
            result = await client.query_data_async(
                input=QueryDataInput(),
                subscriptions="sub-id",
                resourcegroups="rg1",
                resourcetype="type",
                resourcename="name",
            )

            assert result is None


class TestQuerySchemaAsync:
    """Tests for query_schema_async method."""

    @pytest.mark.asyncio
    async def test_success_returns_dynamic_schema_payload(
        self,
        mock_credential,
    ):
        """Test schema lookup returns parsed payload."""
        client = AzuremonitorlogsClient(
            "https://example.azure.com/connections/test",
            credential=mock_credential,
        )

        with patch.object(
            client._http_client,
            "send_async",
            new_callable=AsyncMock,
            return_value=MockResponse(
                status=200,
                text='{"type": "object", "properties": {"Computer": {"type": "string"}}}'
            ),
        ):
            result = await client.query_schema_async(
                input=QuerySchemaInput(),
                subscriptions="sub-id",
                resourcegroups="rg1",
                resourcetype="type",
                resourcename="name",
            )

            assert result["type"] == "object"
            assert "Computer" in result["properties"]


class TestVisualizeQueryAsync:
    """Tests for visualize_query_async method."""

    @pytest.mark.asyncio
    async def test_success_with_vis_type(self, mock_credential):
        """Test visualize call appends visType query parameter."""
        client = AzuremonitorlogsClient(
            "https://example.azure.com/connections/test",
            credential=mock_credential,
        )

        body = VisualizeQueryInput(
            query="Heartbeat | summarize count() by bin(TimeGenerated, 1h)",
            timerangetype="SetInQuery",
        )

        with patch.object(
            client._http_client,
            "send_async",
            new_callable=AsyncMock,
            return_value=MockResponse(status=200, text='{"body": "ok"}'),
        ) as mock_send:
            result = await client.visualize_query_async(
                input=body,
                subscriptions="sub-id",
                resourcegroups="rg1",
                resourcetype="type",
                resourcename="name",
                vis_type="linechart",
            )

            request_url = mock_send.call_args.args[1]
            assert "visualizeQueryV2?" in request_url
            assert "visType=linechart" in request_url
            assert result["body"] == "ok"

    @pytest.mark.asyncio
    async def test_error_response_raises_exception(self, mock_credential):
        """Test non-2xx visualize response raises ConnectorException."""
        client = AzuremonitorlogsClient(
            "https://example.azure.com/connections/test",
            credential=mock_credential,
        )

        with patch.object(
            client._http_client,
            "send_async",
            new_callable=AsyncMock,
            return_value=MockResponse(
                status=400,
                text='{"error": "Invalid chart type"}',
            ),
        ):
            with pytest.raises(ConnectorException) as exc_info:
                await client.visualize_query_async(
                    input=VisualizeQueryInput(),
                    subscriptions="sub-id",
                    resourcegroups="rg1",
                    resourcetype="type",
                    resourcename="name",
                    vis_type="bad",
                )

            assert exc_info.value.status_code == 400


class TestGetTimeRangeSelectionControlAsync:
    """Tests for get_time_range_selection_control_async method."""

    @pytest.mark.asyncio
    async def test_success_returns_control_schema(self, mock_credential):
        """Test the time-range type is encoded and the schema is returned."""
        client = AzuremonitorlogsClient(
            "https://example.azure.com/connections/test",
            credential=mock_credential,
        )

        with patch.object(
            client._http_client,
            "send_async",
            new_callable=AsyncMock,
            return_value=MockResponse(
                status=200,
                text='{"type": "Relative"}',
            ),
        ) as mock_send:
            result = await client.get_time_range_selection_control_async(
                timerangetype="Relative range",
            )

            mock_send.assert_called_once_with(
                "GET",
                "https://example.azure.com/connections/test/"
                "getTimeRangeSelectionControl?timerangetype=Relative%20range",
                body=None,
                timeout=None,
                headers=None,
                client_request_id=None,
                response_hook=None,
            )
            assert result == {"type": "Relative"}

    @pytest.mark.asyncio
    async def test_error_response_raises_exception(self, mock_credential):
        """Test a non-2xx response raises ConnectorException."""
        client = AzuremonitorlogsClient(
            "https://example.azure.com/connections/test",
            credential=mock_credential,
        )

        with patch.object(
            client._http_client,
            "send_async",
            new_callable=AsyncMock,
            return_value=MockResponse(status=400, text="Invalid time range"),
        ):
            with pytest.raises(ConnectorException) as exc_info:
                await client.get_time_range_selection_control_async(
                    timerangetype="invalid",
                )

            assert exc_info.value.status_code == 400
