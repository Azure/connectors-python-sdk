# Copyright (c) Microsoft Corporation. All rights reserved.

"""Unit tests for PipedriveClient."""

import pytest
from unittest.mock import AsyncMock, patch

from azure.connectors.pipedrive import (
    AddActivityRequest,
    AddDealRequestV2,
    PipedriveClient,
    UpdateDealStageRequestV2,
    UpdateDealStatusRequest,
)
from azure.connectors.sdk import (
    ConnectorClientOptions,
    ConnectorException,
    ManagedIdentityTokenProvider,
)
from tests.conftest import MockResponse


async def _invoke_operation(client: PipedriveClient, operation: str):
    """Invoke a Pipedrive operation by name for shared tests."""
    if operation == "trig_new_activity":
        return await client.trig_new_activity_async()
    if operation == "get_deal":
        return await client.get_deal_async(deal_id="1")
    if operation == "update_deal_status":
        return await client.update_deal_status_async(
            input=UpdateDealStatusRequest(),
            deal_id="1",
        )
    if operation == "add_activity":
        return await client.add_activity_async(input=AddActivityRequest())
    if operation == "get_stage":
        return await client.get_stage_async(stage_id="1")
    if operation == "add_deal":
        return await client.add_deal_async(input=AddDealRequestV2())
    if operation == "trig_new_deal":
        return await client.trig_new_deal_async()
    if operation == "update_deal_stage":
        return await client.update_deal_stage_async(
            input=UpdateDealStageRequestV2(),
            deal_id="1",
        )
    if operation == "list_deals":
        return await client.list_deals_async()

    raise ValueError(f"Unsupported operation '{operation}'.")


class TestPipedriveClientInitialization:
    """Tests for PipedriveClient initialization."""

    def test_init_with_valid_url_and_defaults(self):
        """Test initialization with valid URL and default parameters."""
        client = PipedriveClient("https://example.azure.com/connections/test")

        assert client._connection_runtime_url == "https://example.azure.com/connections/test"
        assert client.connector_name == "pipedrive"
        assert isinstance(client._http_client._token_provider, ManagedIdentityTokenProvider)

    def test_init_with_trailing_slash(self):
        """Test that trailing slash is removed from URL."""
        client = PipedriveClient("https://example.azure.com/connections/test/")

        assert client._connection_runtime_url == "https://example.azure.com/connections/test"

    def test_init_with_custom_token_provider(self, mock_token_provider):
        """Test initialization with custom token provider."""
        client = PipedriveClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider,
        )

        assert client._http_client._token_provider is mock_token_provider

    def test_init_with_custom_options(self, mock_token_provider):
        """Test initialization with custom options."""
        options = ConnectorClientOptions(timeout_seconds=60.0, max_retry_attempts=5)
        client = PipedriveClient(
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
            PipedriveClient("")

    def test_init_with_none_url_raises_error(self):
        """Test that None URL raises ValueError."""
        with pytest.raises(ValueError, match="connection_runtime_url cannot be None or empty"):
            PipedriveClient(None)

    def test_connector_name_property(self, mock_token_provider):
        """Test connector_name property returns 'pipedrive'."""
        client = PipedriveClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider,
        )

        assert client.connector_name == "pipedrive"


class TestPipedriveClientLifecycle:
    """Tests for PipedriveClient lifecycle methods."""

    @pytest.mark.asyncio
    async def test_close(self, mock_token_provider):
        """Test close method calls http_client.close."""
        client = PipedriveClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider,
        )

        with patch.object(client._http_client, "close", new_callable=AsyncMock) as mock_close:
            await client.close()
            mock_close.assert_called_once()

    @pytest.mark.asyncio
    async def test_context_manager(self, mock_token_provider):
        """Test async context manager functionality."""
        with patch.object(PipedriveClient, "close", new_callable=AsyncMock) as mock_close:
            async with PipedriveClient(
                "https://example.azure.com/connections/test",
                token_provider=mock_token_provider,
            ) as client:
                assert isinstance(client, PipedriveClient)

            mock_close.assert_called_once()


class TestPipedriveClientMethods:
    """Success path tests for Pipedrive methods."""

    @pytest.mark.asyncio
    async def test_trig_new_activity_success(self, mock_token_provider):
        """Test trig_new_activity_async targets the activity trigger endpoint."""
        client = PipedriveClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider,
        )
        mock_response = MockResponse(status=200, text='{"data":[]}')

        with patch.object(
            client._http_client,
            "send_async",
            new_callable=AsyncMock,
            return_value=mock_response,
        ) as mock_send:
            await client.trig_new_activity_async()

            assert mock_send.call_args[0][0] == "GET"
            assert "/trigger/v1/activities" in mock_send.call_args[0][1]

    @pytest.mark.asyncio
    async def test_get_deal_success(self, mock_token_provider):
        """Test get_deal_async targets the single-deal endpoint."""
        client = PipedriveClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider,
        )
        mock_response = MockResponse(status=200, text='{"data":{"id":42}}')

        with patch.object(
            client._http_client,
            "send_async",
            new_callable=AsyncMock,
            return_value=mock_response,
        ) as mock_send:
            result = await client.get_deal_async(deal_id="42")

            assert result["data"]["id"] == 42
            assert mock_send.call_args[0][0] == "GET"
            assert "/v1/deals/42" in mock_send.call_args[0][1]

    @pytest.mark.asyncio
    async def test_update_deal_status_success(self, mock_token_provider):
        """Test update_deal_status_async sends the body via PUT."""
        client = PipedriveClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider,
        )
        mock_response = MockResponse(status=200, text='{"data":{"id":42}}')
        body = UpdateDealStatusRequest()

        with patch.object(
            client._http_client,
            "send_async",
            new_callable=AsyncMock,
            return_value=mock_response,
        ) as mock_send:
            await client.update_deal_status_async(input=body, deal_id="42")

            assert mock_send.call_args[0][0] == "PUT"
            assert "/update_status_deal/v1/deals/42" in mock_send.call_args[0][1]
            assert mock_send.call_args.kwargs["body"] is body

    @pytest.mark.asyncio
    async def test_add_activity_success(self, mock_token_provider):
        """Test add_activity_async posts the body to the activities endpoint."""
        client = PipedriveClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider,
        )
        mock_response = MockResponse(status=201, text='{"data":{"id":7}}')
        body = AddActivityRequest()

        with patch.object(
            client._http_client,
            "send_async",
            new_callable=AsyncMock,
            return_value=mock_response,
        ) as mock_send:
            result = await client.add_activity_async(input=body)

            assert result["data"]["id"] == 7
            assert mock_send.call_args[0][0] == "POST"
            assert "/v1/activities" in mock_send.call_args[0][1]
            assert mock_send.call_args.kwargs["body"] is body

    @pytest.mark.asyncio
    async def test_get_stage_success(self, mock_token_provider):
        """Test get_stage_async targets the single-stage endpoint."""
        client = PipedriveClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider,
        )
        mock_response = MockResponse(status=200, text='{"data":{"id":3}}')

        with patch.object(
            client._http_client,
            "send_async",
            new_callable=AsyncMock,
            return_value=mock_response,
        ) as mock_send:
            result = await client.get_stage_async(stage_id="3")

            assert result["data"]["id"] == 3
            assert mock_send.call_args[0][0] == "GET"
            assert "/v1/stages/3" in mock_send.call_args[0][1]

    @pytest.mark.asyncio
    async def test_add_deal_success(self, mock_token_provider):
        """Test add_deal_async posts the body to the v2 deals endpoint."""
        client = PipedriveClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider,
        )
        mock_response = MockResponse(status=201, text='{"data":{"id":99}}')
        body = AddDealRequestV2()

        with patch.object(
            client._http_client,
            "send_async",
            new_callable=AsyncMock,
            return_value=mock_response,
        ) as mock_send:
            result = await client.add_deal_async(input=body)

            assert result["data"]["id"] == 99
            assert mock_send.call_args[0][0] == "POST"
            assert "/connector-v2/v1/deals" in mock_send.call_args[0][1]
            assert mock_send.call_args.kwargs["body"] is body

    @pytest.mark.asyncio
    async def test_trig_new_deal_success(self, mock_token_provider):
        """Test trig_new_deal_async targets the v2 deal trigger endpoint."""
        client = PipedriveClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider,
        )
        mock_response = MockResponse(status=200, text='{"data":[]}')

        with patch.object(
            client._http_client,
            "send_async",
            new_callable=AsyncMock,
            return_value=mock_response,
        ) as mock_send:
            await client.trig_new_deal_async()

            assert mock_send.call_args[0][0] == "GET"
            assert "/connector-v2/trigger/v1/deals" in mock_send.call_args[0][1]

    @pytest.mark.asyncio
    async def test_update_deal_stage_success(self, mock_token_provider):
        """Test update_deal_stage_async sends the body via PUT to the v2 endpoint."""
        client = PipedriveClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider,
        )
        mock_response = MockResponse(status=200, text='{"data":{"id":42}}')
        body = UpdateDealStageRequestV2()

        with patch.object(
            client._http_client,
            "send_async",
            new_callable=AsyncMock,
            return_value=mock_response,
        ) as mock_send:
            await client.update_deal_stage_async(input=body, deal_id="42")

            assert mock_send.call_args[0][0] == "PUT"
            assert "/connector-v2/update_stage_deal/v1/deals/42" in mock_send.call_args[0][1]
            assert mock_send.call_args.kwargs["body"] is body

    @pytest.mark.asyncio
    async def test_list_deals_success(self, mock_token_provider):
        """Test list_deals_async targets the deals collection endpoint."""
        client = PipedriveClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider,
        )
        mock_response = MockResponse(status=200, text='{"data":[{"id":1}]}')

        with patch.object(
            client._http_client,
            "send_async",
            new_callable=AsyncMock,
            return_value=mock_response,
        ) as mock_send:
            result = await client.list_deals_async()

            assert result["data"][0]["id"] == 1
            assert mock_send.call_args[0][0] == "GET"
            assert "/v1/deals" in mock_send.call_args[0][1]

    @pytest.mark.asyncio
    async def test_list_deals_empty_returns_none(self, mock_token_provider):
        """Test list_deals_async returns None for an empty body."""
        client = PipedriveClient(
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
            result = await client.list_deals_async()

            assert result is None


class TestPipedriveClientErrorHandling:
    """Error handling tests that ensure all methods raise ConnectorException."""

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "operation",
        [
            "trig_new_activity",
            "get_deal",
            "update_deal_status",
            "add_activity",
            "get_stage",
            "add_deal",
            "trig_new_deal",
            "update_deal_stage",
            "list_deals",
        ],
    )
    async def test_error_response_raises_exception_for_all_operations(
        self,
        mock_token_provider,
        operation,
    ):
        """Test non-2xx responses raise ConnectorException for every operation."""
        client = PipedriveClient(
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
            with pytest.raises(ConnectorException):
                await _invoke_operation(client, operation)
