# Copyright (c) Microsoft Corporation. All rights reserved.

"""Unit tests for ExcelonlinebusinessClient."""

import pytest
from unittest.mock import AsyncMock, patch
from azure.connectors.excelonlinebusiness import (
    ExcelonlinebusinessClient,
    TableToCreate,
    TableMetadata,
    Item,
    ItemsList,
    Comment,
    CommentsList,
    CommentDetails,
    GetItemResponse,
    WorksheetMetadata,
    CreateWorksheetInput,
    RunScriptProdInput,
    RunScriptProdResponse,
    Table,
    TablesList,
    BlobMetadata,
    SensitivityLabelMetadata,
)
from azure.connectors.sdk import (
    ConnectorClientOptions,
    ManagedIdentityTokenProvider,
    ConnectorException,
)
from tests.conftest import MockResponse


class TestExcelonlinebusinessClientInitialization:
    """Tests for ExcelonlinebusinessClient initialization."""

    def test_init_with_valid_url_and_defaults(self):
        """Test initialization with valid URL and default parameters."""
        client = ExcelonlinebusinessClient("https://example.azure.com/connections/test")

        assert client._connection_runtime_url == "https://example.azure.com/connections/test"
        assert client.connector_name == "excelonlinebusiness"
        assert isinstance(client._http_client._token_provider, ManagedIdentityTokenProvider)

    def test_init_with_trailing_slash(self):
        """Test that trailing slash is removed from URL."""
        client = ExcelonlinebusinessClient("https://example.azure.com/connections/test/")

        assert client._connection_runtime_url == "https://example.azure.com/connections/test"

    def test_init_with_custom_token_provider(self, mock_token_provider):
        """Test initialization with custom token provider."""
        client = ExcelonlinebusinessClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        assert client._http_client._token_provider is mock_token_provider

    def test_init_with_custom_options(self, mock_token_provider):
        """Test initialization with custom options."""
        options = ConnectorClientOptions(timeout_seconds=60.0, max_retry_attempts=5)
        client = ExcelonlinebusinessClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider,
            options=options
        )

        assert client._options is options
        assert client._options.timeout_seconds == 60.0
        assert client._options.max_retry_attempts == 5

    def test_init_with_empty_url_raises_error(self):
        """Test that empty URL raises ValueError."""
        with pytest.raises(ValueError, match="connection_runtime_url cannot be None or empty"):
            ExcelonlinebusinessClient("")

    def test_init_with_none_url_raises_error(self):
        """Test that None URL raises ValueError."""
        with pytest.raises(ValueError, match="connection_runtime_url cannot be None or empty"):
            ExcelonlinebusinessClient(None)

    def test_connector_name_property(self, mock_token_provider):
        """Test connector_name property returns 'excelonlinebusiness'."""
        client = ExcelonlinebusinessClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        assert client.connector_name == "excelonlinebusiness"


class TestExcelonlinebusinessClientLifecycle:
    """Tests for ExcelonlinebusinessClient lifecycle methods."""

    @pytest.mark.asyncio
    async def test_close(self, mock_token_provider):
        """Test close method calls http_client.close."""
        client = ExcelonlinebusinessClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        with patch.object(client._http_client, 'close', new_callable=AsyncMock) as mock_close:
            await client.close()
            mock_close.assert_called_once()

    @pytest.mark.asyncio
    async def test_context_manager(self, mock_token_provider):
        """Test async context manager functionality."""
        with patch.object(ExcelonlinebusinessClient, 'close', new_callable=AsyncMock) as mock_close:
            async with ExcelonlinebusinessClient(
                "https://example.azure.com/connections/test",
                token_provider=mock_token_provider
            ) as client:
                assert isinstance(client, ExcelonlinebusinessClient)

            mock_close.assert_called_once()


class TestCreateTable:
    """Tests for create_table_async method."""

    @pytest.mark.asyncio
    async def test_success_with_json_response(self, mock_token_provider):
        """Test successful POST request."""
        client = ExcelonlinebusinessClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(
            status=201,
            text='{"name": "Table1", "title": "Sales Data"}'
        )
        table_input = TableToCreate(
            table_name="Table1",
            range="A1:D10",
            columns_names="Name;Value;Date;Status"
        )

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ) as mock_send:
            result = await client.create_table_async(
                input=table_input,
                drive="drive-id",
                file="file-id",
                source="me"
            )

            mock_send.assert_called_once()
            call_args = mock_send.call_args
            assert call_args[0][0] == "POST"
            assert "/drives/drive-id/files/file-id/tables" in call_args[0][1]
            assert result["name"] == "Table1"

    @pytest.mark.asyncio
    async def test_error_response_raises_exception(self, mock_token_provider):
        """Test that error response raises ConnectorException."""
        client = ExcelonlinebusinessClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(status=400, text='{"error": "Invalid range"}')
        table_input = TableToCreate(table_name="Table1")

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ):
            with pytest.raises(ConnectorException) as exc_info:
                await client.create_table_async(
                    input=table_input,
                    drive="drive-id",
                    file="file-id",
                    source="me"
                )

            assert exc_info.value.status_code == 400


class TestCreateIdColumn:
    """Tests for create_id_column_async method."""

    @pytest.mark.asyncio
    async def test_success(self, mock_token_provider):
        """Test successful POST request."""
        client = ExcelonlinebusinessClient(
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
            await client.create_id_column_async(
                drive="drive-id",
                file="file-id",
                table="Table1",
                source="me",
                id_column="ID",
                populate_column="true"
            )

            mock_send.assert_called_once()
            call_args = mock_send.call_args
            assert call_args[0][0] == "POST"
            assert "/createIdColumn" in call_args[0][1]


class TestGetItems:
    """Tests for get_items_async method."""

    @pytest.mark.asyncio
    async def test_success_with_json_response(self, mock_token_provider):
        """Test successful GET request."""
        client = ExcelonlinebusinessClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(
            status=200,
            text='{"value": [{"Name": "Item1", "Value": 100}, {"Name": "Item2", "Value": 200}]}'
        )

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ) as mock_send:
            result = await client.get_items_async(
                drive="drive-id",
                file="file-id",
                table="Table1",
                source="me"
            )

            mock_send.assert_called_once()
            call_args = mock_send.call_args
            assert call_args[0][0] == "GET"
            assert "/items" in call_args[0][1]
            assert len(result["value"]) == 2

    @pytest.mark.asyncio
    async def test_with_query_parameters(self, mock_token_provider):
        """Test GET request with query parameters."""
        client = ExcelonlinebusinessClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(status=200, text='{"value": []}')

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ) as mock_send:
            await client.get_items_async(
                drive="drive-id",
                file="file-id",
                table="Table1",
                source="me",
                filter="Value gt 50",
                orderby="Name asc",
                top="10",
                skip="5"
            )

            call_args = mock_send.call_args
            url = call_args[0][1]
            assert "$filter=" in url
            assert "$orderby=" in url
            assert "$top=" in url
            assert "$skip=" in url


class TestGetComments:
    """Tests for get_comments_async method."""

    @pytest.mark.asyncio
    async def test_success_with_json_response(self, mock_token_provider):
        """Test successful GET request."""
        client = ExcelonlinebusinessClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(
            status=200,
            text='{"value": [{"id": "comment1", "content": "Review this cell"}]}'
        )

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ) as mock_send:
            result = await client.get_comments_async(
                drive="drive-id",
                file="file-id"
            )

            mock_send.assert_called_once()
            call_args = mock_send.call_args
            assert call_args[0][0] == "GET"
            assert "/workbook/comments" in call_args[0][1]
            assert result["value"][0]["id"] == "comment1"


class TestGetComment:
    """Tests for get_comment_async method."""

    @pytest.mark.asyncio
    async def test_success_with_json_response(self, mock_token_provider):
        """Test successful GET request."""
        client = ExcelonlinebusinessClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(
            status=200,
            text='{"id": "comment1", "content": "Please review", "contentType": "plain"}'
        )

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ) as mock_send:
            result = await client.get_comment_async(
                drive="drive-id",
                file="file-id",
                commentid="comment1"
            )

            mock_send.assert_called_once()
            call_args = mock_send.call_args
            assert call_args[0][0] == "GET"
            assert "/comments/comment1" in call_args[0][1]
            assert result["content"] == "Please review"


class TestReplyComment:
    """Tests for reply_comment_async method."""

    @pytest.mark.asyncio
    async def test_success_with_json_response(self, mock_token_provider):
        """Test successful POST request."""
        client = ExcelonlinebusinessClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(
            status=201,
            text='{"id": "reply1", "content": "I will review it"}'
        )
        comment_details = CommentDetails(
            content="I will review it",
            content_type="plain"
        )

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ) as mock_send:
            result = await client.reply_comment_async(
                input=comment_details,
                drive="drive-id",
                file="file-id",
                commentid="comment1"
            )

            mock_send.assert_called_once()
            call_args = mock_send.call_args
            assert call_args[0][0] == "POST"
            assert "/replies" in call_args[0][1]
            assert result["content"] == "I will review it"


class TestGetItem:
    """Tests for get_item_async method."""

    @pytest.mark.asyncio
    async def test_success_with_json_response(self, mock_token_provider):
        """Test successful GET request."""
        client = ExcelonlinebusinessClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(
            status=200,
            text='{"Name": "John Doe", "Value": 150, "Status": "Active"}'
        )

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ) as mock_send:
            result = await client.get_item_async(
                drive="drive-id",
                file="file-id",
                table="Table1",
                id="row-123",
                source="me",
                id_column="ID"
            )

            mock_send.assert_called_once()
            call_args = mock_send.call_args
            assert call_args[0][0] == "GET"
            assert "/items/row-123" in call_args[0][1]
            assert result["Name"] == "John Doe"


class TestDeleteItem:
    """Tests for delete_item_async method."""

    @pytest.mark.asyncio
    async def test_success(self, mock_token_provider):
        """Test successful DELETE request."""
        client = ExcelonlinebusinessClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(status=204, text="")

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ) as mock_send:
            await client.delete_item_async(
                drive="drive-id",
                file="file-id",
                table="Table1",
                id="row-123",
                source="me",
                id_column="ID"
            )

            mock_send.assert_called_once()
            call_args = mock_send.call_args
            assert call_args[0][0] == "DELETE"
            assert "/items/row-123" in call_args[0][1]


class TestPatchItem:
    """Tests for patch_item_async method."""

    @pytest.mark.asyncio
    async def test_success_with_json_response(self, mock_token_provider):
        """Test successful PATCH request."""
        client = ExcelonlinebusinessClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(
            status=200,
            text='{"Name": "Jane Doe", "Value": 200, "Status": "Updated"}'
        )
        item_input = Item(dynamic_properties={"Value": 200, "Status": "Updated"})

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ) as mock_send:
            result = await client.patch_item_async(
                input=item_input,
                drive="drive-id",
                file="file-id",
                table="Table1",
                id="row-123",
                source="me",
                id_column="ID"
            )

            mock_send.assert_called_once()
            call_args = mock_send.call_args
            assert call_args[0][0] == "PATCH"
            assert "/items/row-123" in call_args[0][1]
            assert result["Status"] == "Updated"

    @pytest.mark.asyncio
    async def test_error_response_raises_exception(self, mock_token_provider):
        """Test that error response raises ConnectorException."""
        client = ExcelonlinebusinessClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(status=404, text='{"error": "Row not found"}')
        item_input = Item(dynamic_properties={"Value": 100})

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ):
            with pytest.raises(ConnectorException) as exc_info:
                await client.patch_item_async(
                    input=item_input,
                    drive="drive-id",
                    file="file-id",
                    table="Table1",
                    id="nonexistent",
                    source="me",
                    id_column="ID"
                )

            assert exc_info.value.status_code == 404


class TestRunScriptProd:
    """Tests for run_script_prod_async method."""

    @pytest.mark.asyncio
    async def test_success_with_json_response(self, mock_token_provider):
        """Test successful POST request."""
        client = ExcelonlinebusinessClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(
            status=200,
            text='{"result": "Script executed successfully", "output": {"sum": 1000}}'
        )
        script_input = RunScriptProdInput(
            additional_properties={"param1": "value1", "param2": 42}
        )

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ) as mock_send:
            result = await client.run_script_prod_async(
                input=script_input,
                drive="drive-id",
                file="file-id",
                script_drive="script-drive-id",
                script_id="script-id",
                source="me",
                script_source="sites"
            )

            mock_send.assert_called_once()
            call_args = mock_send.call_args
            assert call_args[0][0] == "POST"
            assert "/officescripting/api/unattended/run" in call_args[0][1]
            assert result["result"] == "Script executed successfully"


class TestDataClasses:
    """Tests for data class creation and attributes."""

    def test_table_to_create(self):
        """Test TableToCreate dataclass creation."""
        table = TableToCreate(
            table_name="SalesTable",
            range="A1:E100",
            columns_names="Product;Quantity;Price;Total;Date"
        )

        assert table.table_name == "SalesTable"
        assert table.range == "A1:E100"
        assert "Product" in table.columns_names

    def test_table_metadata(self):
        """Test TableMetadata dataclass creation."""
        metadata = TableMetadata(
            name="Table1",
            title="Monthly Sales",
            x_ms_permission="read-write",
            web_url="https://example.com/workbook/table1"
        )

        assert metadata.name == "Table1"
        assert metadata.title == "Monthly Sales"

    def test_item(self):
        """Test Item dataclass creation."""
        item = Item(
            dynamic_properties={"Name": "Product A", "Value": 99.99, "InStock": True}
        )

        assert item.dynamic_properties["Name"] == "Product A"
        assert item.dynamic_properties["Value"] == 99.99

    def test_items_list(self):
        """Test ItemsList dataclass creation."""
        item1 = Item(dynamic_properties={"Name": "Item1"})
        item2 = Item(dynamic_properties={"Name": "Item2"})
        items_list = ItemsList(value=[item1, item2])

        assert items_list.value is not None
        assert len(items_list.value) == 2

    def test_comment(self):
        """Test Comment dataclass creation."""
        comment = Comment(
            id="comment-123",
            content="This needs attention",
            content_type="plain"
        )

        assert comment.id == "comment-123"
        assert comment.content == "This needs attention"

    def test_comment_details(self):
        """Test CommentDetails dataclass creation."""
        details = CommentDetails(
            content="Reply to the comment",
            content_type="plain"
        )

        assert details.content == "Reply to the comment"

    def test_worksheet_metadata(self):
        """Test WorksheetMetadata dataclass creation."""
        worksheet = WorksheetMetadata(
            id="worksheet-1",
            name="Sheet1",
            position=0,
            visibility="Visible"
        )

        assert worksheet.id == "worksheet-1"
        assert worksheet.name == "Sheet1"
        assert worksheet.position == 0

    def test_create_worksheet_input(self):
        """Test CreateWorksheetInput dataclass creation."""
        input_data = CreateWorksheetInput(name="NewSheet")

        assert input_data.name == "NewSheet"

    def test_run_script_prod_input(self):
        """Test RunScriptProdInput dataclass creation."""
        script_input = RunScriptProdInput(
            additional_properties={"startDate": "2024-01-01", "endDate": "2024-12-31"}
        )

        assert script_input.additional_properties["startDate"] == "2024-01-01"

    def test_table(self):
        """Test Table dataclass creation."""
        table = Table(
            name="SalesData",
            display_name="Sales Data Table",
            dynamic_properties={"rowCount": 500}
        )

        assert table.name == "SalesData"
        assert table.display_name == "Sales Data Table"

    def test_blob_metadata(self):
        """Test BlobMetadata dataclass creation."""
        blob = BlobMetadata(
            id="blob-123",
            name="report.xlsx",
            display_name="Monthly Report",
            path="/Documents/Reports/report.xlsx",
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            is_folder=False
        )

        assert blob.id == "blob-123"
        assert blob.is_folder is False

    def test_sensitivity_label_metadata(self):
        """Test SensitivityLabelMetadata dataclass creation."""
        label = SensitivityLabelMetadata(
            sensitivity_label_id="label-001",
            name="Confidential",
            display_name="Confidential - Internal Use Only",
            priority=1,
            color="#FF0000",
            is_encrypted=True,
            is_enabled=True
        )

        assert label.name == "Confidential"
        assert label.is_encrypted is True


class TestEdgeCases:
    """Tests for edge cases and special scenarios."""

    @pytest.mark.asyncio
    async def test_http_client_property_access(self, mock_token_provider):
        """Test accessing http_client property."""
        client = ExcelonlinebusinessClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        assert client.http_client is not None
        assert client._http_client is client.http_client

    @pytest.mark.asyncio
    async def test_empty_response_returns_none(self, mock_token_provider):
        """Test that empty response returns None."""
        client = ExcelonlinebusinessClient(
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
            result = await client.get_items_async(
                drive="drive-id",
                file="file-id",
                table="Table1",
                source="me"
            )
            assert result is None

    @pytest.mark.asyncio
    async def test_multiple_consecutive_calls(self, mock_token_provider):
        """Test multiple consecutive API calls."""
        client = ExcelonlinebusinessClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(status=200, text='{"value": []}')

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ) as mock_send:
            await client.get_items_async(
                drive="drive1",
                file="file1",
                table="Table1",
                source="me"
            )
            await client.get_items_async(
                drive="drive2",
                file="file2",
                table="Table2",
                source="me"
            )

            assert mock_send.call_count == 2
