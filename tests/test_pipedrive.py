# Copyright (c) Microsoft Corporation. All rights reserved.

"""Unit tests for PipedriveClient."""

import pytest
from unittest.mock import AsyncMock, patch

from azure.core.credentials import AzureKeyCredential
from azure.connectors.aio.pipedrive import PipedriveClient
from azure.connectors.pipedrive import (
    AddActivityRequest,
    AddDealRequest,
    UpdateDealStageRequest,
    UpdateDealStatusRequest,
    TRIGGER_OPERATIONS,
)
from azure.connectors.sdk import (
    ConnectorException,
)
from tests.conftest import MockResponse
from tests.generated_connector_test_utils import resolve_generated_result


async def _invoke_operation(client: PipedriveClient, operation: str):
    """Invoke a Pipedrive operation by name for shared tests."""
    if operation == "get_deal":
        return await client.get_deal(deal_id="1")
    if operation == "update_deal_status":
        return await client.update_deal_status(
            input=UpdateDealStatusRequest(status="won"),
            deal_id="1",
        )
    if operation == "add_activity":
        return await client.add_activity(
            input=AddActivityRequest(type_="call", subject="Customer follow-up")
        )
    if operation == "get_stage":
        return await client.get_stage(stage_id="1")
    if operation == "add_deal":
        return await client.add_deal(input=AddDealRequest(title="New Deal"))
    if operation == "update_deal_stage":
        return await client.update_deal_stage(
            input=UpdateDealStageRequest(pipeline_id="1", stage_id="2"),
            deal_id="1",
        )
    if operation == "list_deals":
        return await resolve_generated_result(client.list_deals())

    raise ValueError(f"Unsupported operation '{operation}'.")


class TestPipedriveClientInitialization:
    """Tests for PipedriveClient initialization."""

    def test_init_with_valid_url_and_defaults(self):
        """Test initialization with valid URL and default parameters."""
        client = PipedriveClient("https://example.azure.com/connections/test",
                                 AzureKeyCredential("test-key"))

        assert client._connection_runtime_url == "https://example.azure.com/connections/test"
        assert client.connector_name == "pipedrive"
        assert isinstance(client._http_client._credential, AzureKeyCredential)

    def test_init_with_trailing_slash(self):
        """Test that trailing slash is removed from URL."""
        client = PipedriveClient("https://example.azure.com/connections/test/",
                                 AzureKeyCredential("test-key"))

        assert client._connection_runtime_url == "https://example.azure.com/connections/test"

    def test_init_with_custom_credential(self, mock_credential):
        """Test initialization with custom token provider."""
        client = PipedriveClient(
            "https://example.azure.com/connections/test",
            credential=mock_credential,
        )

        assert client._http_client._credential is mock_credential

    def test_init_with_custom_settings(self, mock_credential):
        """Test initialization with custom pipeline settings."""
        client = PipedriveClient(
            "https://example.azure.com/connections/test",
            credential=mock_credential,
            timeout=60.0,
            max_retry_attempts=5,
        )
        assert client._http_client._timeout_seconds == 60.0

    def test_init_with_empty_url_raises_error(self):
        """Test that empty URL raises ValueError."""
        with pytest.raises(ValueError, match="connection_runtime_url cannot be None or empty"):
            PipedriveClient("", AzureKeyCredential("test-key"))

    def test_init_with_none_url_raises_error(self):
        """Test that None URL raises ValueError."""
        with pytest.raises(ValueError, match="connection_runtime_url cannot be None or empty"):
            PipedriveClient(None, AzureKeyCredential("test-key"))

    def test_connector_name_property(self, mock_credential):
        """Test connector_name property returns 'pipedrive'."""
        client = PipedriveClient(
            "https://example.azure.com/connections/test",
            credential=mock_credential,
        )

        assert client.connector_name == "pipedrive"


class TestPipedriveClientLifecycle:
    """Tests for PipedriveClient lifecycle methods."""

    @pytest.mark.asyncio
    async def test_close(self, mock_credential):
        """Test close method calls http_client.close."""
        client = PipedriveClient(
            "https://example.azure.com/connections/test",
            credential=mock_credential,
        )

        with patch.object(client._http_client, "close", new_callable=AsyncMock) as mock_close:
            await client.close()
            mock_close.assert_called_once()

    @pytest.mark.asyncio
    async def test_context_manager(self, mock_credential):
        """Test async context manager functionality."""
        with patch.object(PipedriveClient, "close", new_callable=AsyncMock) as mock_close:
            async with PipedriveClient(
                "https://example.azure.com/connections/test",
                credential=mock_credential,
            ) as client:
                assert isinstance(client, PipedriveClient)

            mock_close.assert_called_once()


class TestPipedriveClientMethods:
    """Success path tests for Pipedrive methods."""

    @pytest.mark.asyncio
    async def test_get_deal_success(self, mock_credential):
        """Test get_deal_async targets the single-deal endpoint."""
        client = PipedriveClient(
            "https://example.azure.com/connections/test",
            credential=mock_credential,
        )
        mock_response = MockResponse(status=200, text='{"data":{"id":42}}')

        with patch.object(
            client._http_client,
            "send",
            new_callable=AsyncMock,
            return_value=mock_response,
        ) as mock_send:
            result = await client.get_deal(deal_id="42")

            assert result["data"]["id"] == 42
            assert mock_send.call_args[0][0] == "GET"
            assert "/v1/deals/42" in mock_send.call_args[0][1]

    @pytest.mark.asyncio
    async def test_update_deal_status_success(self, mock_credential):
        """Test update_deal_status_async sends the body via PUT."""
        client = PipedriveClient(
            "https://example.azure.com/connections/test",
            credential=mock_credential,
        )
        mock_response = MockResponse(status=200, text='{"data":{"id":42}}')
        body = UpdateDealStatusRequest(status="won")

        with patch.object(
            client._http_client,
            "send",
            new_callable=AsyncMock,
            return_value=mock_response,
        ) as mock_send:
            await client.update_deal_status(input=body, deal_id="42")

            assert mock_send.call_args[0][0] == "PUT"
            assert "/update_status_deal/v1/deals/42" in mock_send.call_args[0][1]
            assert mock_send.call_args.kwargs["body"] is body

    @pytest.mark.asyncio
    async def test_add_activity_success(self, mock_credential):
        """Test add_activity_async posts the body to the activities endpoint."""
        client = PipedriveClient(
            "https://example.azure.com/connections/test",
            credential=mock_credential,
        )
        mock_response = MockResponse(status=201, text='{"data":{"id":7}}')
        body = AddActivityRequest(type_="call", subject="Customer follow-up")

        with patch.object(
            client._http_client,
            "send",
            new_callable=AsyncMock,
            return_value=mock_response,
        ) as mock_send:
            result = await client.add_activity(input=body)

            assert result["data"]["id"] == 7
            assert mock_send.call_args[0][0] == "POST"
            assert "/v1/activities" in mock_send.call_args[0][1]
            assert mock_send.call_args.kwargs["body"] is body

    @pytest.mark.asyncio
    async def test_get_stage_success(self, mock_credential):
        """Test get_stage_async targets the single-stage endpoint."""
        client = PipedriveClient(
            "https://example.azure.com/connections/test",
            credential=mock_credential,
        )
        mock_response = MockResponse(status=200, text='{"data":{"id":3}}')

        with patch.object(
            client._http_client,
            "send",
            new_callable=AsyncMock,
            return_value=mock_response,
        ) as mock_send:
            result = await client.get_stage(stage_id="3")

            assert result["data"]["id"] == 3
            assert mock_send.call_args[0][0] == "GET"
            assert "/v1/stages/3" in mock_send.call_args[0][1]

    @pytest.mark.asyncio
    async def test_add_deal_success(self, mock_credential):
        """Test add_deal_async posts the body to the v2 deals endpoint."""
        client = PipedriveClient(
            "https://example.azure.com/connections/test",
            credential=mock_credential,
        )
        mock_response = MockResponse(status=201, text='{"data":{"id":99}}')
        body = AddDealRequest(title="New Deal")

        with patch.object(
            client._http_client,
            "send",
            new_callable=AsyncMock,
            return_value=mock_response,
        ) as mock_send:
            result = await client.add_deal(input=body)

            assert result["data"]["id"] == 99
            assert mock_send.call_args[0][0] == "POST"
            assert "/connector-v2/v1/deals" in mock_send.call_args[0][1]
            assert mock_send.call_args.kwargs["body"] is body

    @pytest.mark.asyncio
    async def test_update_deal_stage_success(self, mock_credential):
        """Test update_deal_stage_async sends the body via PUT to the v2 endpoint."""
        client = PipedriveClient(
            "https://example.azure.com/connections/test",
            credential=mock_credential,
        )
        mock_response = MockResponse(status=200, text='{"data":{"id":42}}')
        body = UpdateDealStageRequest(pipeline_id="1", stage_id="2")

        with patch.object(
            client._http_client,
            "send",
            new_callable=AsyncMock,
            return_value=mock_response,
        ) as mock_send:
            await client.update_deal_stage(input=body, deal_id="42")

            assert mock_send.call_args[0][0] == "PUT"
            assert "/connector-v2/update_stage_deal/v1/deals/42" in mock_send.call_args[0][1]
            assert mock_send.call_args.kwargs["body"] is body

    @pytest.mark.asyncio
    async def test_list_deals_success(self, mock_credential):
        """Test list_deals_async targets the deals collection endpoint."""
        client = PipedriveClient(
            "https://example.azure.com/connections/test",
            credential=mock_credential,
        )
        mock_response = MockResponse(status=200, text='{"data":[{"id":1}]}')

        with patch.object(
            client._http_client,
            "send",
            new_callable=AsyncMock,
            return_value=mock_response,
        ) as mock_send:
            result = await resolve_generated_result(client.list_deals())

            assert result[0]["id"] == 1
            assert mock_send.call_args[0][0] == "GET"
            assert "/v1/deals" in mock_send.call_args[0][1]

    @pytest.mark.asyncio
    async def test_list_deals_empty_returns_none(self, mock_credential):
        """Test list_deals_async returns None for an empty body."""
        client = PipedriveClient(
            "https://example.azure.com/connections/test",
            credential=mock_credential,
        )
        mock_response = MockResponse(status=200, text="")

        with patch.object(
            client._http_client,
            "send",
            new_callable=AsyncMock,
            return_value=mock_response,
        ):
            result = await resolve_generated_result(client.list_deals())

            assert result == []


class TestPipedriveClientErrorHandling:
    """Error handling tests that ensure all methods raise ConnectorException."""

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "operation",
        [
            "get_deal",
            "update_deal_status",
            "add_activity",
            "get_stage",
            "add_deal",
            "update_deal_stage",
            "list_deals",
        ],
    )
    async def test_error_response_raises_exception_for_all_operations(
        self,
        mock_credential,
        operation,
    ):
        """Test non-2xx responses raise ConnectorException for every operation."""
        client = PipedriveClient(
            "https://example.azure.com/connections/test",
            credential=mock_credential,
        )
        mock_response = MockResponse(status=500, text='{"error":"server failure"}')

        with patch.object(
            client._http_client,
            "send",
            new_callable=AsyncMock,
            return_value=mock_response,
        ):
            with pytest.raises(ConnectorException):
                await _invoke_operation(client, operation)


class TestPipedriveTriggerOperations:
    """Tests for the module-level trigger registration metadata."""

    def test_trig_new_activity_registered_as_trigger(self):
        """Test the new-activity route is registered as a trigger operation."""
        assert "TrigNewActivity" in TRIGGER_OPERATIONS
        trigger = TRIGGER_OPERATIONS["TrigNewActivity"]

        assert trigger["operation_id"] == "TrigNewActivity"
        assert trigger["path"].endswith("/trigger/v1/activities")

    def test_trig_new_deal_registered_as_trigger(self):
        """Test the new-deal route is registered as a trigger operation."""
        assert "TrigNewDealV2" in TRIGGER_OPERATIONS
        trigger = TRIGGER_OPERATIONS["TrigNewDealV2"]

        assert trigger["operation_id"] == "TrigNewDealV2"
        assert trigger["path"].endswith("/connector-v2/trigger/v1/deals")

    def test_trigger_routes_not_client_methods(self):
        """Test the trigger routes are no longer exposed as callable client methods."""
        assert not hasattr(PipedriveClient, "trig_new_activity_async")
        assert not hasattr(PipedriveClient, "trig_new_deal_async")
