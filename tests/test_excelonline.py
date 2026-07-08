# Copyright (c) Microsoft Corporation. All rights reserved.

"""Unit tests for ExcelonlineClient."""

import pytest
from unittest.mock import AsyncMock, patch

from azure.connectors.excelonline import (
    CreateWorksheetInput,
    ExcelonlineClient,
    GetAllWorksheetsResponse,
    GetColumnsResponse,
    GetTablesResponse,
    Item,
    ItemsList,
    TableMetadata,
    TableToCreate,
    WorksheetMetadata,
)
from azure.connectors.sdk import (
    ConnectorClientOptions,
    ConnectorException,
    ManagedIdentityTokenProvider,
)
from tests.conftest import MockResponse


async def _invoke_operation(client: ExcelonlineClient, operation: str):
    """Invoke an Excel Online operation by name for shared error tests."""
    if operation == "create_table":
        return await client.create_table_async(
            input=TableToCreate(table_name="Table1", range="A1:B2"),
            drive="drive123",
            file="file123",
        )
    if operation == "create_id_column":
        return await client.create_id_column_async(
            drive="drive123",
            file="file123",
            table="Table1",
            id_column="ID",
        )
    if operation == "get_items":
        return await client.get_items_async(
            drive="drive123",
            file="file123",
            table="Table1",
            top="10",
        )
    if operation == "get_item":
        return await client.get_item_async(
            drive="drive123",
            file="file123",
            table="Table1",
            id="row1",
            id_column="ID",
        )
    if operation == "delete_item":
        return await client.delete_item_async(
            drive="drive123",
            file="file123",
            table="Table1",
            id="row1",
            id_column="ID",
        )
    if operation == "patch_item":
        return await client.patch_item_async(
            input=Item(dynamic_properties={"Name": "Updated"}),
            drive="drive123",
            file="file123",
            table="Table1",
            id="row1",
            id_column="ID",
        )
    if operation == "get_all_worksheets":
        return await client.get_all_worksheets_async(drive="drive123", file="file123")
    if operation == "create_worksheet":
        return await client.create_worksheet_async(
            input=CreateWorksheetInput(name="Sheet2"),
            drive="drive123",
            file="file123",
        )
    if operation == "get_tables":
        return await client.get_tables_async(drive="drive123", file="file123")
    if operation == "add_row":
        return await client.add_row_async(
            input=Item(dynamic_properties={"Name": "Item1", "Value": 100}),
            drive="drive123",
            file="file123",
            table="Table1",
        )
    if operation == "get_columns":
        return await client.get_columns_async(
            drive="drive123",
            file="file123",
            table="Table1",
        )

    raise ValueError(f"Unsupported operation '{operation}'.")


class TestExcelonlineClientInitialization:
    """Tests for ExcelonlineClient initialization."""

    def test_init_with_valid_url_and_defaults(self):
        """Test initialization with valid URL and default parameters."""
        client = ExcelonlineClient("https://example.azure.com/connections/test")

        assert client._connection_runtime_url == "https://example.azure.com/connections/test"
        assert client.connector_name == "excelonline"
        assert isinstance(client._http_client._token_provider, ManagedIdentityTokenProvider)

    def test_init_with_trailing_slash(self):
        """Test that trailing slash is removed from URL."""
        client = ExcelonlineClient("https://example.azure.com/connections/test/")

        assert client._connection_runtime_url == "https://example.azure.com/connections/test"

    def test_init_with_custom_token_provider(self, mock_token_provider):
        """Test initialization with custom token provider."""
        client = ExcelonlineClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider,
        )

        assert client._http_client._token_provider is mock_token_provider

    def test_init_with_custom_options(self, mock_token_provider):
        """Test initialization with custom options."""
        options = ConnectorClientOptions(timeout_seconds=60.0, max_retry_attempts=5)
        client = ExcelonlineClient(
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
            ExcelonlineClient("")

    def test_init_with_none_url_raises_error(self):
        """Test that None URL raises ValueError."""
        with pytest.raises(ValueError, match="connection_runtime_url cannot be None or empty"):
            ExcelonlineClient(None)

    def test_connector_name_property(self, mock_token_provider):
        """Test connector_name property returns 'excelonline'."""
        client = ExcelonlineClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider,
        )

        assert client.connector_name == "excelonline"


class TestExcelonlineClientLifecycle:
    """Tests for ExcelonlineClient lifecycle methods."""

    @pytest.mark.asyncio
    async def test_close(self, mock_token_provider):
        """Test close method calls http_client.close."""
        client = ExcelonlineClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider,
        )

        with patch.object(client._http_client, "close", new_callable=AsyncMock) as mock_close:
            await client.close()
            mock_close.assert_called_once()

    @pytest.mark.asyncio
    async def test_context_manager(self, mock_token_provider):
        """Test async context manager functionality."""
        with patch.object(ExcelonlineClient, "close", new_callable=AsyncMock) as mock_close:
            async with ExcelonlineClient(
                "https://example.azure.com/connections/test",
                token_provider=mock_token_provider,
            ) as client:
                assert isinstance(client, ExcelonlineClient)

            mock_close.assert_called_once()


class TestExcelonlineClientMethods:
    """Success path tests for representative Excel Online operations."""

    @pytest.mark.asyncio
    async def test_create_table_success(self, mock_token_provider):
        """Test create_table_async serializes body and source query param."""
        client = ExcelonlineClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider,
        )
        mock_response = MockResponse(status=201, text='{"name":"Table1"}')

        with patch.object(
            client._http_client,
            "send_async",
            new_callable=AsyncMock,
            return_value=mock_response,
        ) as mock_send:
            result = await client.create_table_async(
                input=TableToCreate(table_name="Table1", range="A1:B2"),
                drive="drive123",
                file="file123",
            )

            assert result["name"] == "Table1"
            assert "source=me" in mock_send.call_args[0][1]
            assert isinstance(mock_send.call_args.kwargs["body"], TableToCreate)

    @pytest.mark.asyncio
    async def test_get_items_success(self, mock_token_provider):
        """Test get_items_async emits OData query options."""
        client = ExcelonlineClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider,
        )
        mock_response = MockResponse(status=200, text='{"value":[{"Name":"Item1"}]}')

        with patch.object(
            client._http_client,
            "send_async",
            new_callable=AsyncMock,
            return_value=mock_response,
        ) as mock_send:
            result = await client.get_items_async(
                drive="drive123",
                file="file123",
                table="Table1",
                filter="Name eq 'Item1'",
                top="10",
            )

            assert len(result["value"]) == 1
            call_path = mock_send.call_args[0][1]
            assert "$filter=Name%20eq%20%27Item1%27" in call_path
            assert "$top=10" in call_path

    @pytest.mark.asyncio
    async def test_patch_item_success(self, mock_token_provider):
        """Test patch_item_async sends PATCH with body and idColumn."""
        client = ExcelonlineClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider,
        )
        mock_response = MockResponse(status=200, text='{"Name":"Updated"}')

        with patch.object(
            client._http_client,
            "send_async",
            new_callable=AsyncMock,
            return_value=mock_response,
        ) as mock_send:
            result = await client.patch_item_async(
                input=Item(dynamic_properties={"Name": "Updated"}),
                drive="drive123",
                file="file123",
                table="Table1",
                id="row1",
                id_column="ID",
            )

            assert result["Name"] == "Updated"
            assert "idColumn=ID" in mock_send.call_args[0][1]
            assert isinstance(mock_send.call_args.kwargs["body"], Item)

    @pytest.mark.asyncio
    async def test_get_all_worksheets_success(self, mock_token_provider):
        """Test get_all_worksheets_async uses codeless worksheets endpoint."""
        client = ExcelonlineClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider,
        )
        mock_response = MockResponse(status=200, text='{"value":[{"name":"Sheet1"}]}')

        with patch.object(
            client._http_client,
            "send_async",
            new_callable=AsyncMock,
            return_value=mock_response,
        ) as mock_send:
            result = await client.get_all_worksheets_async(drive="drive123", file="file123")

            assert len(result["value"]) == 1
            assert "/workbook/worksheets" in mock_send.call_args[0][1]

    @pytest.mark.asyncio
    async def test_add_row_success(self, mock_token_provider):
        """Test add_row_async sends row payload."""
        client = ExcelonlineClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider,
        )
        mock_response = MockResponse(status=201, text='{"index":1}')

        with patch.object(
            client._http_client,
            "send_async",
            new_callable=AsyncMock,
            return_value=mock_response,
        ) as mock_send:
            result = await client.add_row_async(
                input=Item(dynamic_properties={"Name": "Item1"}),
                drive="drive123",
                file="file123",
                table="Table1",
            )

            assert result["index"] == 1
            assert isinstance(mock_send.call_args.kwargs["body"], Item)


class TestExcelonlineClientErrorHandling:
    """Error handling tests that ensure all operations raise ConnectorException."""

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "operation",
        [
            "create_table",
            "create_id_column",
            "get_items",
            "get_item",
            "delete_item",
            "patch_item",
            "get_all_worksheets",
            "create_worksheet",
            "get_tables",
            "add_row",
            "get_columns",
        ],
    )
    async def test_error_response_raises_exception_for_all_operations(
        self,
        mock_token_provider,
        operation,
    ):
        """Test non-2xx responses raise ConnectorException for every operation."""
        client = ExcelonlineClient(
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


class TestExcelonlineTypeSerialization:
    """Tests for Excel Online generated dataclass defaults."""

    def test_dataclass_instances_initialize_expected_defaults(self):
        """Test generated dataclasses initialize with expected default values."""
        table_metadata = TableMetadata()
        items = ItemsList()
        worksheet_resp = GetAllWorksheetsResponse()
        worksheet = WorksheetMetadata()
        tables = GetTablesResponse()
        columns = GetColumnsResponse()

        assert table_metadata.name is None
        assert items.value is None
        assert worksheet_resp.value is None
        assert worksheet.name is None
        assert tables.value is None
        assert columns.value is None
