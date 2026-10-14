# Copyright (c) Microsoft Corporation. All rights reserved.

"""Unit tests for SqlClient."""

import inspect

import pytest
from unittest.mock import AsyncMock, patch

from azure.core.credentials import AzureKeyCredential
from azure.connectors.aio.sql import SqlClient
from azure.connectors.sql import (
    DatabasesList,
    ExecuteProcedureInput,
    GetItemsResponse,
    GetTablesResponse,
    ODataServersList,
    PatchItemInput,
    PostItemInput,
    ProceduresList,
    Server,
    SqlItem,
    SqlItemsList,
    SqlPassThroughNativeQueryBody,
    Table,
    TablesList,
    TRIGGER_OPERATIONS,
)
from azure.connectors.sdk import (
    ConnectorException,
)
from tests.conftest import MockResponse
from tests.generated_connector_test_utils import (
    get_generated_operations,
    resolve_generated_result,
)


async def _invoke_operation(client: SqlClient, operation: str):
    """Invoke a SQL operation by name for shared method tests."""
    if operation == "delete_item":
        return await client.delete_item(
            server="srv", database="db", table="tbl", id="1"
        )
    if operation == "execute_pass_through_native_query":
        return await client.execute_pass_through_native_query(
            input=SqlPassThroughNativeQueryBody(query="SELECT 1"),
            server="srv",
            database="db",
        )
    if operation == "execute_procedure":
        return await client.execute_procedure(
            input=ExecuteProcedureInput(),
            server="srv",
            database="db",
            procedure="proc",
        )
    if operation == "get_item":
        return await client.get_item(
            server="srv", database="db", table="tbl", id="1"
        )
    if operation == "list_items":
        return await resolve_generated_result(
            client.list_items(server="srv", database="db", table="tbl")
        )
    if operation == "list_tables":
        return await resolve_generated_result(
            client.list_tables(server="srv", database="db")
        )
    if operation == "patch_item":
        return await client.patch_item(
            input=PatchItemInput(),
            server="srv",
            database="db",
            table="tbl",
            id="1",
        )
    if operation == "post_item":
        return await client.post_item(
            input=PostItemInput(), server="srv", database="db", table="tbl"
        )
    if operation == "list_servers":
        return await resolve_generated_result(client.list_servers())
    if operation == "list_databases":
        return await resolve_generated_result(client.list_databases(server="srv"))
    if operation == "list_tables_for_delete_item":
        return await resolve_generated_result(
            client.list_tables_for_delete_item(server="srv", database="db")
        )
    if operation == "list_procedures_v2":
        return await resolve_generated_result(
            client.list_procedures_v2(server="srv", database="db")
        )
    if operation == "get_procedure_v2":
        return await client.get_procedure_v2(
            server="srv", database="db", procedure="proc"
        )
    if operation == "list_tables_for_get_item":
        return await resolve_generated_result(
            client.list_tables_for_get_item(server="srv", database="db")
        )
    if operation == "list_tables_for_get_on_new_items":
        return await resolve_generated_result(client.list_tables_for_get_on_new_items(
            server="srv", database="db"
        ))
    if operation == "list_tables_for_get_on_updated_items":
        return await resolve_generated_result(client.list_tables_for_get_on_updated_items(
            server="srv", database="db"
        ))
    if operation == "list_tables_for_patch_item":
        return await resolve_generated_result(
            client.list_tables_for_patch_item(server="srv", database="db")
        )
    if operation == "get_table_for_patch":
        return await client.get_table_for_patch(
            server="srv", database="db", table="tbl"
        )
    if operation == "list_tables_for_post_item":
        return await resolve_generated_result(
            client.list_tables_for_post_item(server="srv", database="db")
        )
    if operation == "get_table":
        return await client.get_table(server="srv", database="db", table="tbl")
    if operation == "get_pass_through_native_query_metadata":
        return await client.get_pass_through_native_query_metadata(
            input=SqlPassThroughNativeQueryBody(query="SELECT 1"),
            server="srv",
            database="db",
        )
    if operation == "get_procedure":
        return await client.get_procedure(procedure="proc")
    if operation == "list_procedures":
        return await resolve_generated_result(client.list_procedures())

    raise ValueError(f"Unsupported operation '{operation}'.")


ALL_OPERATIONS = [
    "delete_item",
    "execute_pass_through_native_query",
    "execute_procedure",
    "get_item",
    "list_items",
    "list_tables",
    "patch_item",
    "post_item",
    "list_servers",
    "list_databases",
    "list_tables_for_delete_item",
    "list_procedures_v2",
    "get_procedure_v2",
    "list_tables_for_get_item",
    "list_tables_for_get_on_new_items",
    "list_tables_for_get_on_updated_items",
    "list_tables_for_patch_item",
    "get_table_for_patch",
    "list_tables_for_post_item",
    "get_table",
    "get_pass_through_native_query_metadata",
    "get_procedure",
    "list_procedures",
]


class TestSqlClientInitialization:
    """Tests for SqlClient initialization."""

    def test_init_with_valid_url_and_defaults(self):
        """Test initialization with valid URL and default parameters."""
        client = SqlClient("https://example.azure.com/connections/test",
                           AzureKeyCredential("test-key"))

        assert client._connection_runtime_url == "https://example.azure.com/connections/test"
        assert client.connector_name == "sql"
        assert isinstance(client._http_client._credential, AzureKeyCredential)

    def test_init_with_trailing_slash(self):
        """Test that trailing slash is removed from URL."""
        client = SqlClient("https://example.azure.com/connections/test/",
                           AzureKeyCredential("test-key"))

        assert client._connection_runtime_url == "https://example.azure.com/connections/test"

    def test_init_with_custom_credential(self, mock_credential):
        """Test initialization with custom token provider."""
        client = SqlClient(
            "https://example.azure.com/connections/test",
            credential=mock_credential,
        )

        assert client._http_client._credential is mock_credential

    def test_init_with_custom_settings(self, mock_credential):
        """Test initialization with custom pipeline settings."""
        client = SqlClient(
            "https://example.azure.com/connections/test",
            credential=mock_credential,
            timeout=60.0,
            max_retry_attempts=5,
        )
        assert client._http_client._timeout_seconds == 60.0

    def test_init_with_empty_url_raises_error(self):
        """Test that empty URL raises ValueError."""
        with pytest.raises(ValueError, match="connection_runtime_url cannot be None or empty"):
            SqlClient("", AzureKeyCredential("test-key"))

    def test_init_with_none_url_raises_error(self):
        """Test that None URL raises ValueError."""
        with pytest.raises(ValueError, match="connection_runtime_url cannot be None or empty"):
            SqlClient(None, AzureKeyCredential("test-key"))

    def test_connector_name_property(self, mock_credential):
        """Test connector_name property returns 'sql'."""
        client = SqlClient(
            "https://example.azure.com/connections/test",
            credential=mock_credential,
        )

        assert client.connector_name == "sql"


class TestSqlClientLifecycle:
    """Tests for SqlClient lifecycle methods."""

    @pytest.mark.asyncio
    async def test_close(self, mock_credential):
        """Test close method calls http_client.close."""
        client = SqlClient(
            "https://example.azure.com/connections/test",
            credential=mock_credential,
        )

        with patch.object(client._http_client, "close", new_callable=AsyncMock) as mock_close:
            await client.close()
            mock_close.assert_called_once()

    @pytest.mark.asyncio
    async def test_context_manager(self, mock_credential):
        """Test async context manager functionality."""
        with patch.object(SqlClient, "close", new_callable=AsyncMock) as mock_close:
            async with SqlClient(
                "https://example.azure.com/connections/test",
                credential=mock_credential,
            ) as client:
                assert isinstance(client, SqlClient)

            mock_close.assert_called_once()


class TestSqlClientMethods:
    """Success path tests for representative SQL methods."""

    @pytest.mark.asyncio
    async def test_list_servers_success(self, mock_credential):
        """Test list_servers returns parsed items and targets /servers."""
        client = SqlClient(
            "https://example.azure.com/connections/test",
            credential=mock_credential,
        )
        mock_response = MockResponse(status=200, text='{"value":[{"name":"srv1"}]}')

        with patch.object(
            client._http_client,
            "send",
            new_callable=AsyncMock,
            return_value=mock_response,
        ) as mock_send:
            result = await resolve_generated_result(client.list_servers())

            assert result[0]["name"] == "srv1"
            assert mock_send.call_args[0][1].endswith("/servers")

    @pytest.mark.asyncio
    async def test_list_databases_sends_server_query(self, mock_credential):
        """Test list_databases appends the server query parameter."""
        client = SqlClient(
            "https://example.azure.com/connections/test",
            credential=mock_credential,
        )
        mock_response = MockResponse(status=200, text='{"value":[]}')

        with patch.object(
            client._http_client,
            "send",
            new_callable=AsyncMock,
            return_value=mock_response,
        ) as mock_send:
            await resolve_generated_result(client.list_databases(server="srv1"))

            request_url = mock_send.call_args[0][1]
            assert "/databases" in request_url
            assert "server=srv1" in request_url

    @pytest.mark.asyncio
    async def test_get_items_success(self, mock_credential):
        """Test get_items_async targets the v2 items endpoint."""
        client = SqlClient(
            "https://example.azure.com/connections/test",
            credential=mock_credential,
        )
        mock_response = MockResponse(status=200, text='{"value":[{"dynamicProperties":{}}]}')

        with patch.object(
            client._http_client,
            "send",
            new_callable=AsyncMock,
            return_value=mock_response,
        ) as mock_send:
            result = await resolve_generated_result(client.list_items(
                server="srv", database="db", table="tbl"
            ))

            assert result
            assert "/v2/datasets/srv,db/tables/tbl/items" in mock_send.call_args[0][1]

    @pytest.mark.asyncio
    async def test_get_items_appends_odata_query_params(self, mock_credential):
        """Test get_items_async serializes OData query parameters."""
        client = SqlClient(
            "https://example.azure.com/connections/test",
            credential=mock_credential,
        )
        mock_response = MockResponse(status=200, text='{"value":[]}')

        with patch.object(
            client._http_client,
            "send",
            new_callable=AsyncMock,
            return_value=mock_response,
        ) as mock_send:
            await resolve_generated_result(client.list_items(
                server="srv",
                database="db",
                table="tbl",
                filter="Id eq 1",
                top="10",
            ))

            request_url = mock_send.call_args[0][1]
            assert "$filter=Id%20eq%201" in request_url
            assert "$top=10" in request_url

    @pytest.mark.asyncio
    async def test_post_item_sends_body(self, mock_credential):
        """Test post_item_async sends the input body to the items endpoint."""
        client = SqlClient(
            "https://example.azure.com/connections/test",
            credential=mock_credential,
        )
        mock_response = MockResponse(status=200, text='{"id":"1"}')

        with patch.object(
            client._http_client,
            "send",
            new_callable=AsyncMock,
            return_value=mock_response,
        ) as mock_send:
            await client.post_item(
                input=PostItemInput(additional_properties={"Name": "Contoso"}),
                server="srv",
                database="db",
                table="tbl",
            )

            assert mock_send.call_args[0][0] == "POST"
            assert isinstance(mock_send.call_args.kwargs["body"], PostItemInput)
            assert "/v2/datasets/srv,db/tables/tbl/items" in mock_send.call_args[0][1]

    @pytest.mark.asyncio
    async def test_patch_item_uses_patch_verb(self, mock_credential):
        """Test patch_item_async issues a PATCH and forwards the body."""
        client = SqlClient(
            "https://example.azure.com/connections/test",
            credential=mock_credential,
        )
        mock_response = MockResponse(status=200, text='{"id":"1"}')
        body = PatchItemInput()

        with patch.object(
            client._http_client,
            "send",
            new_callable=AsyncMock,
            return_value=mock_response,
        ) as mock_send:
            await client.patch_item(
                input=body,
                server="srv",
                database="db",
                table="tbl",
                id="1",
            )

            assert mock_send.call_args[0][0] == "PATCH"
            assert "/v2/datasets/srv,db/tables/tbl/items/1" in mock_send.call_args[0][1]
            assert mock_send.call_args.kwargs["body"] is body

    @pytest.mark.asyncio
    async def test_delete_item_uses_delete_verb(self, mock_credential):
        """Test delete_item_async issues a DELETE and returns None."""
        client = SqlClient(
            "https://example.azure.com/connections/test",
            credential=mock_credential,
        )
        mock_response = MockResponse(status=200, text="")

        with patch.object(
            client._http_client,
            "send",
            new_callable=AsyncMock,
            return_value=mock_response,
        ) as mock_send:
            result = await client.delete_item(
                server="srv", database="db", table="tbl", id="1"
            )

            assert result is None
            assert mock_send.call_args[0][0] == "DELETE"
            assert "/v2/datasets/srv,db/tables/tbl/items/1" in mock_send.call_args[0][1]

    @pytest.mark.asyncio
    async def test_execute_procedure_sends_body(self, mock_credential):
        """Test execute_procedure_async posts the input to the procedures endpoint."""
        client = SqlClient(
            "https://example.azure.com/connections/test",
            credential=mock_credential,
        )
        mock_response = MockResponse(status=200, text='{"ResultSets":{}}')

        with patch.object(
            client._http_client,
            "send",
            new_callable=AsyncMock,
            return_value=mock_response,
        ) as mock_send:
            await client.execute_procedure(
                input=ExecuteProcedureInput(),
                server="srv",
                database="db",
                procedure="proc",
            )

            assert mock_send.call_args[0][0] == "POST"
            assert "/v2/datasets/srv,db/procedures/proc" in mock_send.call_args[0][1]

    @pytest.mark.asyncio
    async def test_execute_pass_through_native_query_success(self, mock_credential):
        """Test execute_pass_through_native_query_async posts to the query endpoint."""
        client = SqlClient(
            "https://example.azure.com/connections/test",
            credential=mock_credential,
        )
        mock_response = MockResponse(status=200, text='{"resultSets":{}}')

        with patch.object(
            client._http_client,
            "send",
            new_callable=AsyncMock,
            return_value=mock_response,
        ) as mock_send:
            await client.execute_pass_through_native_query(
                input=SqlPassThroughNativeQueryBody(query="SELECT 1"),
                server="srv",
                database="db",
            )

            assert mock_send.call_args[0][0] == "POST"
            assert "/v2/datasets/srv,db/query/sql" in mock_send.call_args[0][1]

    @pytest.mark.asyncio
    async def test_list_procedures_v2_success(self, mock_credential):
        """Test list_procedures_v2 targets the v2 procedures endpoint."""
        client = SqlClient(
            "https://example.azure.com/connections/test",
            credential=mock_credential,
        )
        mock_response = MockResponse(status=200, text='{"value":[]}')

        with patch.object(
            client._http_client,
            "send",
            new_callable=AsyncMock,
            return_value=mock_response,
        ) as mock_send:
            await resolve_generated_result(
                client.list_procedures_v2(server="srv", database="db")
            )

            assert "/v2/datasets/srv,db/procedures" in mock_send.call_args[0][1]

    @pytest.mark.asyncio
    async def test_get_table_success(self, mock_credential):
        """Test get_table_async targets the current v2 metadata endpoint."""
        client = SqlClient(
            "https://example.azure.com/connections/test",
            credential=mock_credential,
        )
        mock_response = MockResponse(status=200, text='{"name":"tbl"}')

        with patch.object(
            client._http_client,
            "send",
            new_callable=AsyncMock,
            return_value=mock_response,
        ) as mock_send:
            await client.get_table(server="srv", database="db", table="tbl")

            assert "/v2/$metadata.json/datasets/srv,db/tables/tbl" in mock_send.call_args[0][1]

    @pytest.mark.asyncio
    @pytest.mark.parametrize("operation", ALL_OPERATIONS)
    async def test_all_operations_success(self, mock_credential, operation):
        """Test every operation issues a request and returns without error."""
        base_url = "https://example.azure.com/connections/test"
        client = SqlClient(base_url, credential=mock_credential)
        mock_response = MockResponse(status=200, text="{}")

        with patch.object(
            client._http_client,
            "send",
            new_callable=AsyncMock,
            return_value=mock_response,
        ) as mock_send:
            await _invoke_operation(client, operation)

            assert mock_send.call_count == 1
            assert mock_send.call_args[0][1].startswith(base_url)


class TestSqlClientErrorHandling:
    """Error handling tests that ensure all methods raise ConnectorException."""

    @pytest.mark.asyncio
    @pytest.mark.parametrize("operation", ALL_OPERATIONS)
    async def test_error_response_raises_exception_for_all_operations(
        self,
        mock_credential,
        operation,
    ):
        """Test non-2xx responses raise ConnectorException for every operation."""
        client = SqlClient(
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
            with pytest.raises(ConnectorException) as exc_info:
                await _invoke_operation(client, operation)

            assert exc_info.value.status_code == 500


class TestSqlTypeSerialization:
    """Tests for SQL connector dataclass defaults."""

    def test_dataclass_instances_initialize_expected_defaults(self):
        """Test generated dataclasses initialize with expected default values."""
        databases_list = DatabasesList()
        servers_list = ODataServersList()
        tables_list = TablesList()
        procedures_list = ProceduresList()
        get_items_response = GetItemsResponse()
        get_tables_response = GetTablesResponse()
        sql_items_list = SqlItemsList()
        server = Server()
        table = Table()
        sql_item = SqlItem()
        query_body = SqlPassThroughNativeQueryBody()
        post_input = PostItemInput()

        assert databases_list.value is None
        assert servers_list.value is None
        assert tables_list.value is None
        assert procedures_list.value is None
        assert get_items_response.value is None
        assert get_tables_response.value is None
        assert sql_items_list.value is None
        assert server.name is None
        assert table.name is None
        assert sql_item.dynamic_properties is None
        assert query_body.query is None
        assert post_input.additional_properties == {}


class TestSqlTriggerOperations:
    """Tests for the module-level trigger registration metadata."""

    def test_trigger_registry_metadata(self):
        """Test the trigger registry matches the generated SQL trigger surface."""
        assert TRIGGER_OPERATIONS == {
            "GetOnNewItems_V2": {
                "operation_id": "GetOnNewItems_V2",
                "path": (
                    "/{connectionId}/v2/datasets/{server},{database}/tables/"
                    "{table}/onnewitems"
                ),
                "method": "get",
                "required_parameters": ["server", "database", "table"],
                "callback_payload_type": "SqlItemsList",
            },
            "GetOnUpdatedItems_V2": {
                "operation_id": "GetOnUpdatedItems_V2",
                "path": (
                    "/{connectionId}/datasets/{server},{database}/tables/"
                    "{table}/onupdateditems"
                ),
                "method": "get",
                "required_parameters": ["server", "database", "table"],
                "callback_payload_type": "SqlItemsList",
            },
        }

    def test_trigger_routes_not_client_methods(self):
        """Test the trigger routes are no longer exposed as callable client methods."""
        assert not hasattr(SqlClient, "get_on_new_items_async")
        assert not hasattr(SqlClient, "get_on_updated_items_async")

    def test_callable_method_signatures(self):
        """Test the client exposes exactly the generated callable methods."""
        expected_signatures = {
            "delete_item": ("self", "server", "database", "table", "id"),
            "execute_pass_through_native_query": (
                "self", "input", "server", "database"
            ),
            "execute_procedure": (
                "self", "input", "server", "database", "procedure"
            ),
            "list_databases": ("self", "server"),
            "get_item": ("self", "server", "database", "table", "id"),
            "list_items": (
                "self", "server", "database", "table", "apply", "filter",
                "orderby", "skip", "top", "select", "count",
                "extract_sensitivity_label", "purview_account_name"
            ),
            "get_pass_through_native_query_metadata": (
                "self", "input", "server", "database"
            ),
            "get_procedure": ("self", "procedure"),
            "get_procedure_v2": (
                "self", "server", "database", "procedure"
            ),
            "list_procedures": ("self",),
            "list_procedures_v2": ("self", "server", "database"),
            "list_servers": ("self",),
            "get_table": (
                "self", "server", "database", "table",
                "extract_sensitivity_label", "purview_account_name"
            ),
            "get_table_for_patch": ("self", "server", "database", "table"),
            "list_tables": (
                "self", "server", "database", "extract_sensitivity_label",
                "purview_account_name"
            ),
            "list_tables_for_delete_item": ("self", "server", "database"),
            "list_tables_for_get_item": ("self", "server", "database"),
            "list_tables_for_get_on_new_items": (
                "self", "server", "database"
            ),
            "list_tables_for_get_on_updated_items": (
                "self", "server", "database"
            ),
            "list_tables_for_patch_item": ("self", "server", "database"),
            "list_tables_for_post_item": ("self", "server", "database"),
            "patch_item": (
                "self", "input", "server", "database", "table", "id"
            ),
            "post_item": ("self", "input", "server", "database", "table"),
        }
        request_control_parameters = (
            "timeout",
            "headers",
            "client_request_id",
            "response_hook",
        )
        expected_signatures = {
            name: parameters + request_control_parameters
            for name, parameters in expected_signatures.items()
        }
        assert get_generated_operations(SqlClient) == set(expected_signatures)
        actual_signatures = {
            name: tuple(inspect.signature(getattr(SqlClient, name)).parameters)
            for name in expected_signatures
        }

        assert actual_signatures == expected_signatures
