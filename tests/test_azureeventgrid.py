# Copyright (c) Microsoft Corporation. All rights reserved.

"""Unit tests for AzureeventgridClient."""

import pytest
from unittest.mock import AsyncMock, patch

from azure.connectors.azureeventgrid import (
    AzureeventgridClient,
    EventRequest,
    EventSchema,
    EventTypesResponse,
    ResourceNameResponse,
    Subscription,
    SubscriptionListResult,
    TopicTypesResponse,
    TRIGGER_OPERATIONS,
)
from azure.connectors.sdk import (
    ConnectorClientOptions,
    ConnectorException,
    ManagedIdentityTokenProvider,
)
from tests.conftest import MockResponse


async def _invoke_operation(client: AzureeventgridClient, operation: str):
    """Invoke an Event Grid operation by name for shared error-handling tests."""
    if operation == "subscriptions_list":
        return await client.subscriptions_list_async()
    if operation == "topic_types_list":
        return await client.topic_types_list_async()

    raise ValueError(f"Unsupported operation '{operation}'.")


ALL_OPERATIONS = [
    "subscriptions_list",
    "topic_types_list",
]


class TestAzureeventgridClientInitialization:
    """Tests for AzureeventgridClient initialization."""

    def test_init_with_valid_url_and_defaults(self):
        """Test initialization with valid URL and default parameters."""
        client = AzureeventgridClient("https://example.azure.com/connections/test")

        assert client._connection_runtime_url == "https://example.azure.com/connections/test"
        assert client.connector_name == "azureeventgrid"
        assert isinstance(client._http_client._token_provider, ManagedIdentityTokenProvider)

    def test_init_with_trailing_slash(self):
        """Test that trailing slash is removed from URL."""
        client = AzureeventgridClient("https://example.azure.com/connections/test/")

        assert client._connection_runtime_url == "https://example.azure.com/connections/test"

    def test_init_with_custom_token_provider(self, mock_token_provider):
        """Test initialization with custom token provider."""
        client = AzureeventgridClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider,
        )

        assert client._http_client._token_provider is mock_token_provider

    def test_init_with_custom_options(self, mock_token_provider):
        """Test initialization with custom options."""
        options = ConnectorClientOptions(timeout_seconds=60.0, max_retry_attempts=5)
        client = AzureeventgridClient(
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
            AzureeventgridClient("")

    def test_init_with_none_url_raises_error(self):
        """Test that None URL raises ValueError."""
        with pytest.raises(ValueError, match="connection_runtime_url cannot be None or empty"):
            AzureeventgridClient(None)

    def test_connector_name_property(self, mock_token_provider):
        """Test connector_name property returns 'azureeventgrid'."""
        client = AzureeventgridClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider,
        )

        assert client.connector_name == "azureeventgrid"


class TestAzureeventgridClientLifecycle:
    """Tests for AzureeventgridClient lifecycle methods."""

    @pytest.mark.asyncio
    async def test_close(self, mock_token_provider):
        """Test close method calls http_client.close."""
        client = AzureeventgridClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider,
        )

        with patch.object(client._http_client, "close", new_callable=AsyncMock) as mock_close:
            await client.close()
            mock_close.assert_called_once()

    @pytest.mark.asyncio
    async def test_context_manager(self, mock_token_provider):
        """Test async context manager functionality."""
        with patch.object(AzureeventgridClient, "close", new_callable=AsyncMock) as mock_close:
            async with AzureeventgridClient(
                "https://example.azure.com/connections/test",
                token_provider=mock_token_provider,
            ) as client:
                assert isinstance(client, AzureeventgridClient)

            mock_close.assert_called_once()


class TestAzureeventgridClientMethods:
    """Success path tests for Event Grid methods."""

    @pytest.mark.asyncio
    async def test_subscriptions_list_success(self, mock_token_provider):
        """Test subscriptions_list_async returns parsed JSON and targets /subscriptions."""
        client = AzureeventgridClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider,
        )
        mock_response = MockResponse(status=200, text='{"value":[{"subscriptionId":"sub-1"}]}')

        with patch.object(
            client._http_client,
            "send_async",
            new_callable=AsyncMock,
            return_value=mock_response,
        ) as mock_send:
            result = await client.subscriptions_list_async()

            assert result["value"][0]["subscriptionId"] == "sub-1"
            assert mock_send.call_args[0][0] == "GET"
            assert "/subscriptions" in mock_send.call_args[0][1]
            assert "x-ms-api-version=2015-11-01" in mock_send.call_args[0][1]

    @pytest.mark.asyncio
    async def test_topic_types_list_success(self, mock_token_provider):
        """Test topic_types_list_async targets the topicTypes endpoint."""
        client = AzureeventgridClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider,
        )
        mock_response = MockResponse(status=200, text='{"value":[]}')

        with patch.object(
            client._http_client,
            "send_async",
            new_callable=AsyncMock,
            return_value=mock_response,
        ) as mock_send:
            result = await client.topic_types_list_async()

            assert "value" in result
            request_url = mock_send.call_args[0][1]
            assert "/providers/Microsoft.EventGrid/topicTypes" in request_url
            assert "x-ms-api-version=2017-09-15-preview" in request_url

    @pytest.mark.asyncio
    async def test_topic_types_list_empty_body_returns_none(self, mock_token_provider):
        """Test topic_types_list_async returns None when the body is empty."""
        client = AzureeventgridClient(
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
            result = await client.topic_types_list_async()

            assert result is None


class TestAzureeventgridClientErrorHandling:
    """Error handling tests that ensure all methods raise ConnectorException."""

    @pytest.mark.asyncio
    @pytest.mark.parametrize("operation", ALL_OPERATIONS)
    async def test_error_response_raises_exception_for_all_operations(
        self,
        mock_token_provider,
        operation,
    ):
        """Test non-2xx responses raise ConnectorException for every operation."""
        client = AzureeventgridClient(
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


class TestAzureeventgridTypeSerialization:
    """Tests for Event Grid connector dataclass defaults."""

    def test_dataclass_instances_initialize_expected_defaults(self):
        """Test generated dataclasses initialize with expected default values."""
        subscription_list = SubscriptionListResult()
        topic_types = TopicTypesResponse()
        event_types = EventTypesResponse()
        resource_names = ResourceNameResponse()
        event_request = EventRequest()
        event_schema = EventSchema()
        subscription = Subscription()

        assert subscription_list.value is None
        assert topic_types.value is None
        assert event_types.value is None
        assert resource_names.value is None
        assert event_request.properties is None
        assert event_schema.additional_properties == {}
        assert subscription.subscription_id is None


class TestAzureeventgridTriggerOperations:
    """Tests for the module-level trigger registration metadata."""

    def test_create_subscription_registered_as_trigger(self):
        """Test the create subscription route is registered as a trigger operation."""
        assert "CreateSubscription" in TRIGGER_OPERATIONS
        trigger = TRIGGER_OPERATIONS["CreateSubscription"]

        assert trigger["operation_id"] == "CreateSubscription"
        assert trigger["method"] == "post"
        assert trigger["path"].endswith("/resource/eventSubscriptions")
        assert "subscriptionId" in trigger["required_parameters"]

    def test_create_subscription_not_a_client_method(self):
        """Test the trigger route is no longer exposed as a callable client method."""
        assert not hasattr(AzureeventgridClient, "create_subscription_async")
