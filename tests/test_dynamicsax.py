# Copyright (c) Microsoft Corporation. All rights reserved.

"""Unit tests for DynamicsaxClient."""

import pytest
from unittest.mock import AsyncMock, patch

from azure.connectors.dynamicsax import (
    AxOnlineProcedureResult,
    BusinessEventSubscription,
    BusinessEventSubscriptionResponse,
    BusinessEventsList,
    DataSet,
    DataSetsList,
    DynamicsaxClient,
    ExecuteProcedureInput,
    GetItemResponse,
    Item,
    ItemsList,
    PatchItemInput,
    PostItemInput,
    Procedure,
    ProceduresList,
    Table,
    TablesList,
    TriggerFieldDataList,
    TRIGGER_OPERATIONS,
)
from azure.connectors.sdk import (
    ConnectorClientOptions,
    ConnectorException,
    ManagedIdentityTokenProvider,
)
from tests.conftest import MockResponse

BASE_URL = "https://example.azure.com/connections/test"

# Maps each operation name (without the "_async" suffix) to its call kwargs.
OPERATION_ARGS = {
    "execute_procedure": {
        "input": ExecuteProcedureInput(),
        "dataset": "ds",
        "procedure": "proc",
    },
    "get_items": {"dataset": "ds", "table": "tbl"},
    "post_item": {
        "input": PostItemInput(),
        "dataset": "ds",
        "table": "tbl",
    },
    "get_item": {"dataset": "ds", "table": "tbl", "id": "1"},
    "delete_item": {"dataset": "ds", "table": "tbl", "id": "1"},
    "patch_item": {
        "input": PatchItemInput(),
        "dataset": "ds",
        "table": "tbl",
        "id": "1",
    },
    "get_tables": {"dataset": "ds"},
    "get_data_sets": {},
    "get_business_event_categories": {"dataset": "ds"},
    "get_business_events": {"dataset": "ds", "businesseventcategory": "cat"},
    "get_legal_entities": {
        "dataset": "ds",
        "businesseventcategory": "cat",
        "businessevent": "evt",
    },
    "get_procedures": {"dataset": "ds"},
    "get_procedure": {"dataset": "ds", "procedure": "proc"},
    "get_table": {"dataset": "ds", "table": "tbl"},
}

# Operations that do not return a JSON body (return None on success).
NO_JSON_OPERATIONS = {"delete_item"}

ALL_OPERATIONS = sorted(OPERATION_ARGS.keys())


async def _invoke_operation(client: DynamicsaxClient, operation: str):
    """Invoke a Dynamics AX operation by name for shared parametrized tests."""
    return await getattr(client, f"{operation}_async")(**OPERATION_ARGS[operation])


def _make_client(token_provider=None):
    """Create a client for testing."""
    return DynamicsaxClient(BASE_URL, token_provider=token_provider)


class TestDynamicsaxClientInitialization:
    """Tests for DynamicsaxClient initialization."""

    def test_init_with_valid_url_and_defaults(self):
        """Test initialization with valid URL and default parameters."""
        client = DynamicsaxClient(BASE_URL)

        assert client._connection_runtime_url == BASE_URL
        assert client.connector_name == "dynamicsax"
        assert isinstance(client._http_client._token_provider, ManagedIdentityTokenProvider)

    def test_init_with_trailing_slash(self):
        """Test that trailing slash is removed from URL."""
        client = DynamicsaxClient(BASE_URL + "/")

        assert client._connection_runtime_url == BASE_URL

    def test_init_with_custom_token_provider(self, mock_token_provider):
        """Test initialization with custom token provider."""
        client = _make_client(token_provider=mock_token_provider)

        assert client._http_client._token_provider is mock_token_provider

    def test_init_with_custom_options(self, mock_token_provider):
        """Test initialization with custom options."""
        options = ConnectorClientOptions(timeout_seconds=60.0, max_retry_attempts=5)
        client = DynamicsaxClient(
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
            DynamicsaxClient("")

    def test_init_with_none_url_raises_error(self):
        """Test that None URL raises ValueError."""
        with pytest.raises(ValueError, match="connection_runtime_url cannot be None or empty"):
            DynamicsaxClient(None)

    def test_connector_name_property(self, mock_token_provider):
        """Test connector_name property returns 'dynamicsax'."""
        client = _make_client(token_provider=mock_token_provider)

        assert client.connector_name == "dynamicsax"


class TestDynamicsaxClientLifecycle:
    """Tests for DynamicsaxClient lifecycle methods."""

    @pytest.mark.asyncio
    async def test_close(self, mock_token_provider):
        """Test close method calls http_client.close."""
        client = _make_client(token_provider=mock_token_provider)

        with patch.object(client._http_client, "close", new_callable=AsyncMock) as mock_close:
            await client.close()
            mock_close.assert_called_once()

    @pytest.mark.asyncio
    async def test_context_manager(self, mock_token_provider):
        """Test async context manager functionality."""
        with patch.object(DynamicsaxClient, "close", new_callable=AsyncMock) as mock_close:
            async with _make_client(token_provider=mock_token_provider) as client:
                assert isinstance(client, DynamicsaxClient)

            mock_close.assert_called_once()


class TestDynamicsaxClientMethods:
    """Success path tests for Dynamics AX methods."""

    @pytest.mark.asyncio
    async def test_get_data_sets_success(self, mock_token_provider):
        """Test get_data_sets_async returns parsed JSON targeting /datasets."""
        client = _make_client(token_provider=mock_token_provider)
        mock_response = MockResponse(status=200, text='{"value":[{"name":"instance-1"}]}')

        with patch.object(
            client._http_client,
            "send_async",
            new_callable=AsyncMock,
            return_value=mock_response,
        ) as mock_send:
            result = await client.get_data_sets_async()

            assert result["value"][0]["name"] == "instance-1"
            assert mock_send.call_args[0][0] == "GET"
            assert mock_send.call_args[0][1].endswith("/datasets")

    @pytest.mark.asyncio
    async def test_get_items_targets_items_endpoint(self, mock_token_provider):
        """Test get_items_async targets the datasets/tables/items endpoint."""
        client = _make_client(token_provider=mock_token_provider)
        mock_response = MockResponse(status=200, text='{"value":[]}')

        with patch.object(
            client._http_client,
            "send_async",
            new_callable=AsyncMock,
            return_value=mock_response,
        ) as mock_send:
            await client.get_items_async(dataset="ds", table="tbl")

            request_url = mock_send.call_args[0][1]
            assert "/datasets/ds/tables/tbl/items" in request_url

    @pytest.mark.asyncio
    async def test_get_items_appends_odata_query_params(self, mock_token_provider):
        """Test get_items_async appends OData query params with $ prefix."""
        client = _make_client(token_provider=mock_token_provider)
        mock_response = MockResponse(status=200, text='{"value":[]}')

        with patch.object(
            client._http_client,
            "send_async",
            new_callable=AsyncMock,
            return_value=mock_response,
        ) as mock_send:
            await client.get_items_async(
                dataset="ds",
                table="tbl",
                filter="Name eq 'x'",
                top="5",
            )

            request_url = mock_send.call_args[0][1]
            assert "$filter=" in request_url
            assert "$top=5" in request_url

    @pytest.mark.asyncio
    async def test_post_item_sends_body(self, mock_token_provider):
        """Test post_item_async posts the input to the items endpoint."""
        client = _make_client(token_provider=mock_token_provider)
        mock_response = MockResponse(status=200, text='{"id":"1"}')
        item_input = PostItemInput()

        with patch.object(
            client._http_client,
            "send_async",
            new_callable=AsyncMock,
            return_value=mock_response,
        ) as mock_send:
            result = await client.post_item_async(input=item_input, dataset="ds", table="tbl")

            assert result["id"] == "1"
            assert mock_send.call_args[0][0] == "POST"
            assert mock_send.call_args.kwargs["body"] is item_input

    @pytest.mark.asyncio
    async def test_patch_item_sends_body(self, mock_token_provider):
        """Test patch_item_async patches the item with the provided body."""
        client = _make_client(token_provider=mock_token_provider)
        mock_response = MockResponse(status=200, text='{"id":"1"}')
        item_input = PatchItemInput()

        with patch.object(
            client._http_client,
            "send_async",
            new_callable=AsyncMock,
            return_value=mock_response,
        ) as mock_send:
            result = await client.patch_item_async(
                input=item_input,
                dataset="ds",
                table="tbl",
                id="1",
            )

            assert result["id"] == "1"
            assert mock_send.call_args[0][0] == "PATCH"
            assert mock_send.call_args.kwargs["body"] is item_input

    @pytest.mark.asyncio
    async def test_delete_item_returns_none(self, mock_token_provider):
        """Test delete_item_async issues a DELETE and returns None."""
        client = _make_client(token_provider=mock_token_provider)
        mock_response = MockResponse(status=200, text="")

        with patch.object(
            client._http_client,
            "send_async",
            new_callable=AsyncMock,
            return_value=mock_response,
        ) as mock_send:
            result = await client.delete_item_async(dataset="ds", table="tbl", id="1")

            assert result is None
            assert mock_send.call_args[0][0] == "DELETE"

    @pytest.mark.asyncio
    async def test_get_table_targets_metadata_endpoint(self, mock_token_provider):
        """Test get_table_async targets the $metadata.json endpoint."""
        client = _make_client(token_provider=mock_token_provider)
        mock_response = MockResponse(status=200, text='{"name":"tbl"}')

        with patch.object(
            client._http_client,
            "send_async",
            new_callable=AsyncMock,
            return_value=mock_response,
        ) as mock_send:
            await client.get_table_async(dataset="ds", table="tbl")

            request_url = mock_send.call_args[0][1]
            assert "/$metadata.json/datasets/ds/tables/tbl" in request_url

    @pytest.mark.asyncio
    @pytest.mark.parametrize("operation", ALL_OPERATIONS)
    async def test_all_operations_success(self, mock_token_provider, operation):
        """Test every operation returns the expected success result."""
        client = _make_client(token_provider=mock_token_provider)
        mock_response = MockResponse(status=200, text='{"value":"ok"}')

        with patch.object(
            client._http_client,
            "send_async",
            new_callable=AsyncMock,
            return_value=mock_response,
        ):
            result = await _invoke_operation(client, operation)

            if operation in NO_JSON_OPERATIONS:
                assert result is None
            else:
                assert result == {"value": "ok"}

    @pytest.mark.asyncio
    @pytest.mark.parametrize("operation", sorted(NO_JSON_OPERATIONS))
    async def test_no_json_operations_ignore_body(self, mock_token_provider, operation):
        """Test no-json operations return None even when a body is present."""
        client = _make_client(token_provider=mock_token_provider)
        mock_response = MockResponse(status=200, text='{"unexpected":"body"}')

        with patch.object(
            client._http_client,
            "send_async",
            new_callable=AsyncMock,
            return_value=mock_response,
        ):
            result = await _invoke_operation(client, operation)

            assert result is None


class TestDynamicsaxClientErrorHandling:
    """Error handling tests that ensure all methods raise ConnectorException."""

    @pytest.mark.asyncio
    @pytest.mark.parametrize("operation", ALL_OPERATIONS)
    async def test_error_response_raises_exception_for_all_operations(
        self,
        mock_token_provider,
        operation,
    ):
        """Test non-2xx responses raise ConnectorException for every operation."""
        client = _make_client(token_provider=mock_token_provider)
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


class TestDynamicsaxTypeSerialization:
    """Tests for Dynamics AX connector dataclass defaults."""

    def test_dataclass_instances_initialize_expected_defaults(self):
        """Test generated dataclasses initialize with expected default values."""
        assert BusinessEventSubscription().notification_url is None
        assert BusinessEventSubscriptionResponse().id is None
        assert ExecuteProcedureInput().additional_properties == {}
        assert AxOnlineProcedureResult().value is None
        assert ItemsList().value is None
        assert PostItemInput().additional_properties == {}
        assert GetItemResponse().additional_properties == {}
        assert TablesList().value is None
        assert DataSetsList().value is None
        assert BusinessEventsList().value is None
        assert ProceduresList().value is None
        assert TriggerFieldDataList().value is None
        assert Item().dynamic_properties is None
        assert Procedure().name is None
        assert DataSet().name is None
        assert Table().name is None


class TestDynamicsaxTriggerOperations:
    """Tests for the module-level trigger registration metadata."""

    def test_subscribe_on_a_business_event_registered_as_trigger(self):
        """Test the business event subscription route is registered as a trigger operation."""
        assert "SubscribeOnABusinessEvent" in TRIGGER_OPERATIONS
        trigger = TRIGGER_OPERATIONS["SubscribeOnABusinessEvent"]

        assert trigger["operation_id"] == "SubscribeOnABusinessEvent"
        assert trigger["method"] == "post"

    def test_subscribe_on_a_business_event_not_a_client_method(self):
        """Test the trigger route is no longer exposed as a callable client method."""
        assert not hasattr(DynamicsaxClient, "subscribe_on_a_business_event_async")
