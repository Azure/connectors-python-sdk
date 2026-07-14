# Copyright (c) Microsoft Corporation. All rights reserved.

"""Unit tests for SqlClient."""

import pytest
from unittest.mock import AsyncMock, patch

from azure.connectors.sql import (
    SqlClient,
    DatabasesList,
    ExecuteProcedureInput,
    GetItemsResponse,
    GetTablesResponse,
    ODataServersList,
    PassThroughNativeQueryBody,
    PatchItemInput,
    PostItemInput,
    ProceduresList,
    Server,
    SqlItem,
    SqlItemsList,
    SqlPassThroughNativeQueryBody,
    Table,
    TablesList,
)
from azure.connectors.sdk import (
    ConnectorClientOptions,
    ConnectorException,
    ManagedIdentityTokenProvider,
)
from tests.conftest import MockResponse


async def _invoke_operation(client: SqlClient, operation: str):
    """Invoke a SQL operation by name for shared error-handling tests."""
    if operation == "delete_item":
        return await client.delete_item_async(
            server="srv", database="db", table="tbl", id="1"
        )
    if operation == "execute_pass_through_native_query":
        return await client.execute_pass_through_native_query_async(
            input=SqlPassThroughNativeQueryBody(query="SELECT 1"),
            server="srv",
            database="db",
        )
    if operation == "execute_procedure":
        return await client.execute_procedure_async(
            input=ExecuteProcedureInput(),
            server="srv",
            database="db",
            procedure="proc",
        )
    if operation == "get_item":
        return await client.get_item_async(
            server="srv", database="db", table="tbl", id="1"
        )
    if operation == "get_items":
        return await client.get_items_async(server="srv", database="db", table="tbl")
    if operation == "get_on_new_items":
        return await client.get_on_new_items_async(
            server="srv", database="db", table="tbl"
        )
    if operation == "get_on_updated_items":
        return await client.get_on_updated_items_async(
            server="srv", database="db", table="tbl"
        )
    if operation == "get_tables":
        return await client.get_tables_async(server="srv", database="db")
    if operation == "patch_item":
        return await client.patch_item_async(
            input=PatchItemInput(),
            server="srv",
            database="db",
            table="tbl",
            id="1",
        )
    if operation == "post_item":
        return await client.post_item_async(
            input=PostItemInput(), server="srv", database="db", table="tbl"
        )
    if operation == "get_servers":
        return await client.get_servers_async()
    if operation == "get_databases":
        return await client.get_databases_async(server="srv")
    if operation == "get_tables_for_delete_item":
        return await client.get_tables_for_delete_item_async(server="srv", database="db")
    if operation == "get_pass_through_native_query_metadata_v2":
        return await client.get_pass_through_native_query_metadata_v2_async(
            input=SqlPassThroughNativeQueryBody(query="SELECT 1"),
            server="srv",
            database="db",
        )
    if operation == "get_procedures_v2":
        return await client.get_procedures_v2_async(server="srv", database="db")
    if operation == "get_procedure_v2":
        return await client.get_procedure_v2_async(
            server="srv", database="db", procedure="proc"
        )
    if operation == "get_tables_for_get_item":
        return await client.get_tables_for_get_item_async(server="srv", database="db")
    if operation == "get_table_v2":
        return await client.get_table_v2_async(server="srv", database="db", table="tbl")
    if operation == "get_tables_for_get_on_new_items":
        return await client.get_tables_for_get_on_new_items_async(
            server="srv", database="db"
        )
    if operation == "get_tables_for_get_on_updated_items":
        return await client.get_tables_for_get_on_updated_items_async(
            server="srv", database="db"
        )
    if operation == "get_tables_for_patch_item":
        return await client.get_tables_for_patch_item_async(server="srv", database="db")
    if operation == "get_table_for_patch":
        return await client.get_table_for_patch_async(
            server="srv", database="db", table="tbl"
        )
    if operation == "get_tables_for_post_item":
        return await client.get_tables_for_post_item_async(server="srv", database="db")
    if operation == "get_table":
        return await client.get_table_async(table="tbl")
    if operation == "get_pass_through_native_query_metadata":
        return await client.get_pass_through_native_query_metadata_async(
            input=PassThroughNativeQueryBody()
        )
    if operation == "get_procedure":
        return await client.get_procedure_async(procedure="proc")
    if operation == "get_procedures":
        return await client.get_procedures_async()

    raise ValueError(f"Unsupported operation '{operation}'.")


ALL_OPERATIONS = [
    "delete_item",
    "execute_pass_through_native_query",
    "execute_procedure",
    "get_item",
    "get_items",
    "get_on_new_items",
    "get_on_updated_items",
    "get_tables",
    "patch_item",
    "post_item",
    "get_servers",
    "get_databases",
    "get_tables_for_delete_item",
    "get_pass_through_native_query_metadata_v2",
    "get_procedures_v2",
    "get_procedure_v2",
    "get_tables_for_get_item",
    "get_table_v2",
    "get_tables_for_get_on_new_items",
    "get_tables_for_get_on_updated_items",
    "get_tables_for_patch_item",
    "get_table_for_patch",
    "get_tables_for_post_item",
    "get_table",
    "get_pass_through_native_query_metadata",
    "get_procedure",
    "get_procedures",
]


class TestSqlClientInitialization:
    """Tests for SqlClient initialization."""

    def test_init_with_valid_url_and_defaults(self):
        """Test initialization with valid URL and default parameters."""
        client = SqlClient("https://example.azure.com/connections/test")

        assert client._connection_runtime_url == "https://example.azure.com/connections/test"
        assert client.connector_name == "sql"
        assert isinstance(client._http_client._token_provider, ManagedIdentityTokenProvider)

    def test_init_with_trailing_slash(self):
        """Test that trailing slash is removed from URL."""
        client = SqlClient("https://example.azure.com/connections/test/")

        assert client._connection_runtime_url == "https://example.azure.com/connections/test"

    def test_init_with_custom_token_provider(self, mock_token_provider):
        """Test initialization with custom token provider."""
        client = SqlClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider,
        )

        assert client._http_client._token_provider is mock_token_provider

    def test_init_with_custom_options(self, mock_token_provider):
        """Test initialization with custom options."""
        options = ConnectorClientOptions(timeout_seconds=60.0, max_retry_attempts=5)
        client = SqlClient(
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
            SqlClient("")

    def test_init_with_none_url_raises_error(self):
        """Test that None URL raises ValueError."""
        with pytest.raises(ValueError, match="connection_runtime_url cannot be None or empty"):
            SqlClient(None)

    def test_connector_name_property(self, mock_token_provider):
        """Test connector_name property returns 'sql'."""
        client = SqlClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider,
        )

        assert client.connector_name == "sql"


class TestSqlClientLifecycle:
    """Tests for SqlClient lifecycle methods."""

    @pytest.mark.asyncio
    async def test_close(self, mock_token_provider):
        """Test close method calls http_client.close."""
        client = SqlClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider,
        )

        with patch.object(client._http_client, "close", new_callable=AsyncMock) as mock_close:
            await client.close()
            mock_close.assert_called_once()

    @pytest.mark.asyncio
    async def test_context_manager(self, mock_token_provider):
        """Test async context manager functionality."""
        with patch.object(SqlClient, "close", new_callable=AsyncMock) as mock_close:
            async with SqlClient(
                "https://example.azure.com/connections/test",
                token_provider=mock_token_provider,
            ) as client:
                assert isinstance(client, SqlClient)

            mock_close.assert_called_once()


class TestSqlClientMethods:
    """Success path tests for representative SQL methods."""

    @pytest.mark.asyncio
    async def test_get_servers_success(self, mock_token_provider):
        """Test get_servers_async returns parsed JSON and targets /servers."""
        client = SqlClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider,
        )
        mock_response = MockResponse(status=200, text='{"value":[{"name":"srv1"}]}')

        with patch.object(
            client._http_client,
            "send_async",
            new_callable=AsyncMock,
            return_value=mock_response,
        ) as mock_send:
            result = await client.get_servers_async()

            assert result["value"][0]["name"] == "srv1"
            assert mock_send.call_args[0][1].endswith("/servers")

    @pytest.mark.asyncio
    async def test_get_databases_sends_server_query(self, mock_token_provider):
        """Test get_databases_async appends the server query parameter."""
        client = SqlClient(
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
            await client.get_databases_async(server="srv1")

            request_url = mock_send.call_args[0][1]
            assert "/databases" in request_url
            assert "server=srv1" in request_url

    @pytest.mark.asyncio
    async def test_get_items_success(self, mock_token_provider):
        """Test get_items_async targets the v2 items endpoint."""
        client = SqlClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider,
        )
        mock_response = MockResponse(status=200, text='{"value":[{"dynamicProperties":{}}]}')

        with patch.object(
            client._http_client,
            "send_async",
            new_callable=AsyncMock,
            return_value=mock_response,
        ) as mock_send:
            result = await client.get_items_async(
                server="srv", database="db", table="tbl"
            )

            assert "value" in result
            assert "/v2/datasets/srv,db/tables/tbl/items" in mock_send.call_args[0][1]

    @pytest.mark.asyncio
    async def test_get_items_appends_odata_query_params(self, mock_token_provider):
        """Test get_items_async serializes OData query parameters."""
        client = SqlClient(
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
            await client.get_items_async(
                server="srv",
                database="db",
                table="tbl",
                filter="Id eq 1",
                top="10",
            )

            request_url = mock_send.call_args[0][1]
            assert "$filter=Id%20eq%201" in request_url
            assert "$top=10" in request_url

    @pytest.mark.asyncio
    async def test_post_item_sends_body(self, mock_token_provider):
        """Test post_item_async sends the input body to the items endpoint."""
        client = SqlClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider,
        )
        mock_response = MockResponse(status=200, text='{"id":"1"}')

        with patch.object(
            client._http_client,
            "send_async",
            new_callable=AsyncMock,
            return_value=mock_response,
        ) as mock_send:
            await client.post_item_async(
                input=PostItemInput(additional_properties={"Name": "Contoso"}),
                server="srv",
                database="db",
                table="tbl",
            )

            assert mock_send.call_args[0][0] == "POST"
            assert isinstance(mock_send.call_args.kwargs["body"], PostItemInput)
            assert "/v2/datasets/srv,db/tables/tbl/items" in mock_send.call_args[0][1]

    @pytest.mark.asyncio
    async def test_patch_item_uses_patch_verb(self, mock_token_provider):
        """Test patch_item_async issues a PATCH to the row endpoint."""
        client = SqlClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider,
        )
        mock_response = MockResponse(status=200, text='{"id":"1"}')

        with patch.object(
            client._http_client,
            "send_async",
            new_callable=AsyncMock,
            return_value=mock_response,
        ) as mock_send:
            await client.patch_item_async(
                input=PatchItemInput(),
                server="srv",
                database="db",
                table="tbl",
                id="1",
            )

            assert mock_send.call_args[0][0] == "PATCH"
            assert "/v2/datasets/srv,db/tables/tbl/items/1" in mock_send.call_args[0][1]

    @pytest.mark.asyncio
    async def test_delete_item_uses_delete_verb(self, mock_token_provider):
        """Test delete_item_async issues a DELETE and returns None."""
        client = SqlClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider,
        )
        mock_response = MockResponse(status=200, text="")

        with patch.object(
            client._http_client,
            "send_async",
            new_callable=AsyncMock,
            return_value=mock_response,
        ) as mock_send:
            result = await client.delete_item_async(
                server="srv", database="db", table="tbl", id="1"
            )

            assert result is None
            assert mock_send.call_args[0][0] == "DELETE"
            assert "/v2/datasets/srv,db/tables/tbl/items/1" in mock_send.call_args[0][1]

    @pytest.mark.asyncio
    async def test_execute_procedure_sends_body(self, mock_token_provider):
        """Test execute_procedure_async posts the input to the procedures endpoint."""
        client = SqlClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider,
        )
        mock_response = MockResponse(status=200, text='{"ResultSets":{}}')

        with patch.object(
            client._http_client,
            "send_async",
            new_callable=AsyncMock,
            return_value=mock_response,
        ) as mock_send:
            await client.execute_procedure_async(
                input=ExecuteProcedureInput(),
                server="srv",
                database="db",
                procedure="proc",
            )

            assert mock_send.call_args[0][0] == "POST"
            assert "/v2/datasets/srv,db/procedures/proc" in mock_send.call_args[0][1]

    @pytest.mark.asyncio
    async def test_execute_pass_through_native_query_success(self, mock_token_provider):
        """Test execute_pass_through_native_query_async posts to the query endpoint."""
        client = SqlClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider,
        )
        mock_response = MockResponse(status=200, text='{"resultSets":{}}')

        with patch.object(
            client._http_client,
            "send_async",
            new_callable=AsyncMock,
            return_value=mock_response,
        ) as mock_send:
            await client.execute_pass_through_native_query_async(
                input=SqlPassThroughNativeQueryBody(query="SELECT 1"),
                server="srv",
                database="db",
            )

            assert mock_send.call_args[0][0] == "POST"
            assert "/v2/datasets/srv,db/query/sql" in mock_send.call_args[0][1]

    @pytest.mark.asyncio
    async def test_get_procedures_v2_success(self, mock_token_provider):
        """Test get_procedures_v2_async targets the v2 procedures endpoint."""
        client = SqlClient(
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
            await client.get_procedures_v2_async(server="srv", database="db")

            assert "/v2/datasets/srv,db/procedures" in mock_send.call_args[0][1]

    @pytest.mark.asyncio
    async def test_get_on_new_items_success(self, mock_token_provider):
        """Test get_on_new_items_async targets the onnewitems trigger endpoint."""
        client = SqlClient(
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
            await client.get_on_new_items_async(server="srv", database="db", table="tbl")

            assert "/v2/datasets/srv,db/tables/tbl/onnewitems" in mock_send.call_args[0][1]

    @pytest.mark.asyncio
    async def test_get_table_success(self, mock_token_provider):
        """Test get_table_async targets the legacy default metadata endpoint."""
        client = SqlClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider,
        )
        mock_response = MockResponse(status=200, text='{"name":"tbl"}')

        with patch.object(
            client._http_client,
            "send_async",
            new_callable=AsyncMock,
            return_value=mock_response,
        ) as mock_send:
            await client.get_table_async(table="tbl")

            assert "/$metadata.json/datasets/default/tables/tbl" in mock_send.call_args[0][1]


class TestSqlClientErrorHandling:
    """Error handling tests that ensure all methods raise ConnectorException."""

    @pytest.mark.asyncio
    @pytest.mark.parametrize("operation", ALL_OPERATIONS)
    async def test_error_response_raises_exception_for_all_operations(
        self,
        mock_token_provider,
        operation,
    ):
        """Test non-2xx responses raise ConnectorException for every operation."""
        client = SqlClient(
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
