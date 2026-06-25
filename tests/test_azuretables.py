# Copyright (c) Microsoft Corporation. All rights reserved.

"""Unit tests for AzuretablesClient."""

import pytest
from unittest.mock import AsyncMock, patch
from azure.connectors.azuretables import (
    AzuretablesClient,
    CreateEntityInput,
    InsertEntityResponse,
    CreateTableInput,
    GetTableResponse,
    GetEntitiesResponse,
    GetEntityResponse,
    GetTablesResponse,
    InsertMergeEntityInput,
    InsertReplaceEntityInput,
    MergeEntityInput,
    ReplaceEntityInput,
    StorageAccountList,
    StorageAccount,
    Item,
)
from azure.connectors.sdk import (
    ConnectorClientOptions,
    ManagedIdentityTokenProvider,
    ConnectorException,
)
from tests.conftest import MockResponse


class TestAzuretablesClientInitialization:
    """Tests for AzuretablesClient initialization."""

    def test_init_with_valid_url_and_defaults(self):
        """Test initialization with valid URL and default parameters."""
        client = AzuretablesClient("https://example.azure.com/connections/test")

        assert client._connection_runtime_url == "https://example.azure.com/connections/test"
        assert client.connector_name == "azuretables"
        assert isinstance(client._http_client._token_provider, ManagedIdentityTokenProvider)

    def test_init_with_trailing_slash(self):
        """Test that trailing slash is removed from URL."""
        client = AzuretablesClient("https://example.azure.com/connections/test/")

        assert client._connection_runtime_url == "https://example.azure.com/connections/test"

    def test_init_with_custom_token_provider(self, mock_token_provider):
        """Test initialization with custom token provider."""
        client = AzuretablesClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        assert client._http_client._token_provider is mock_token_provider

    def test_init_with_custom_options(self, mock_token_provider):
        """Test initialization with custom options."""
        options = ConnectorClientOptions(timeout_seconds=60.0, max_retry_attempts=5)
        client = AzuretablesClient(
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
            AzuretablesClient("")

    def test_init_with_none_url_raises_error(self):
        """Test that None URL raises ValueError."""
        with pytest.raises(ValueError, match="connection_runtime_url cannot be None or empty"):
            AzuretablesClient(None)

    def test_connector_name_property(self, mock_token_provider):
        """Test connector_name property returns 'azuretables'."""
        client = AzuretablesClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        assert client.connector_name == "azuretables"


class TestAzuretablesClientLifecycle:
    """Tests for AzuretablesClient lifecycle methods."""

    @pytest.mark.asyncio
    async def test_close(self, mock_token_provider):
        """Test close method calls http_client.close."""
        client = AzuretablesClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        with patch.object(client._http_client, 'close', new_callable=AsyncMock) as mock_close:
            await client.close()
            mock_close.assert_called_once()

    @pytest.mark.asyncio
    async def test_context_manager(self, mock_token_provider):
        """Test async context manager functionality."""
        with patch.object(AzuretablesClient, 'close', new_callable=AsyncMock) as mock_close:
            async with AzuretablesClient(
                "https://example.azure.com/connections/test",
                token_provider=mock_token_provider
            ) as client:
                assert isinstance(client, AzuretablesClient)

            mock_close.assert_called_once()


class TestCreateEntity:
    """Tests for create_entity_async method."""

    @pytest.mark.asyncio
    async def test_success_with_json_response(self, mock_token_provider):
        """Test successful POST request."""
        client = AzuretablesClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(
            status=201,
            text='{"PartitionKey": "pk1", "RowKey": "rk1", "Name": "Test"}'
        )
        entity_input = CreateEntityInput(
            additional_properties={"PartitionKey": "pk1", "RowKey": "rk1", "Name": "Test"}
        )

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ) as mock_send:
            result = await client.create_entity_async(
                input=entity_input,
                storage_account_name="mystorageaccount",
                table_name="mytable"
            )

            mock_send.assert_called_once()
            call_args = mock_send.call_args
            assert call_args[0][0] == "POST"
            assert "/storageAccounts/mystorageaccount/tables/mytable/entities" in call_args[0][1]
            assert result["PartitionKey"] == "pk1"

    @pytest.mark.asyncio
    async def test_error_response_raises_exception(self, mock_token_provider):
        """Test that error response raises ConnectorException."""
        client = AzuretablesClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(status=400, text='{"error": "Invalid entity"}')
        entity_input = CreateEntityInput(additional_properties={})

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ):
            with pytest.raises(ConnectorException) as exc_info:
                await client.create_entity_async(
                    input=entity_input,
                    storage_account_name="mystorageaccount",
                    table_name="mytable"
                )

            assert exc_info.value.status_code == 400


class TestCreateTable:
    """Tests for create_table_async method."""

    @pytest.mark.asyncio
    async def test_success_with_json_response(self, mock_token_provider):
        """Test successful POST request."""
        client = AzuretablesClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(
            status=201,
            text='{"odata.id": "https://storage/Tables(\'newtable\')", "TableName": "newtable"}'
        )
        table_input = CreateTableInput(additional_properties={"TableName": "newtable"})

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ) as mock_send:
            result = await client.create_table_async(
                input=table_input,
                storage_account_name="mystorageaccount"
            )

            mock_send.assert_called_once()
            call_args = mock_send.call_args
            assert call_args[0][0] == "POST"
            assert "/storageAccounts/mystorageaccount/tables" in call_args[0][1]
            assert result["TableName"] == "newtable"

    @pytest.mark.asyncio
    async def test_error_response_raises_exception(self, mock_token_provider):
        """Test that error response raises ConnectorException."""
        client = AzuretablesClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(status=409, text='{"error": "Table already exists"}')
        table_input = CreateTableInput(additional_properties={"TableName": "existingtable"})

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ):
            with pytest.raises(ConnectorException) as exc_info:
                await client.create_table_async(
                    input=table_input,
                    storage_account_name="mystorageaccount"
                )

            assert exc_info.value.status_code == 409


class TestDeleteEntity:
    """Tests for delete_entity_async method."""

    @pytest.mark.asyncio
    async def test_success(self, mock_token_provider):
        """Test successful DELETE request."""
        client = AzuretablesClient(
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
            await client.delete_entity_async(
                storage_account_name="mystorageaccount",
                table_name="mytable",
                partition_key="pk1",
                row_key="rk1"
            )

            mock_send.assert_called_once()
            call_args = mock_send.call_args
            assert call_args[0][0] == "DELETE"
            assert "/etag(PartitionKey='pk1',RowKey='rk1')" in call_args[0][1]

    @pytest.mark.asyncio
    async def test_error_response_raises_exception(self, mock_token_provider):
        """Test that error response raises ConnectorException."""
        client = AzuretablesClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(status=404, text='{"error": "Entity not found"}')

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ):
            with pytest.raises(ConnectorException) as exc_info:
                await client.delete_entity_async(
                    storage_account_name="mystorageaccount",
                    table_name="mytable",
                    partition_key="nonexistent",
                    row_key="nonexistent"
                )

            assert exc_info.value.status_code == 404


class TestDeleteTable:
    """Tests for delete_table_async method."""

    @pytest.mark.asyncio
    async def test_success(self, mock_token_provider):
        """Test successful DELETE request."""
        client = AzuretablesClient(
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
            await client.delete_table_async(
                storage_account_name="mystorageaccount",
                table_name="mytable"
            )

            mock_send.assert_called_once()
            call_args = mock_send.call_args
            assert call_args[0][0] == "DELETE"
            assert "/storageAccounts/mystorageaccount/tables/mytable" in call_args[0][1]

    @pytest.mark.asyncio
    async def test_error_response_raises_exception(self, mock_token_provider):
        """Test that error response raises ConnectorException."""
        client = AzuretablesClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(status=404, text='{"error": "Table not found"}')

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ):
            with pytest.raises(ConnectorException) as exc_info:
                await client.delete_table_async(
                    storage_account_name="mystorageaccount",
                    table_name="nonexistent"
                )

            assert exc_info.value.status_code == 404


class TestGetEntities:
    """Tests for get_entities_async method."""

    @pytest.mark.asyncio
    async def test_success_with_json_response(self, mock_token_provider):
        """Test successful GET request."""
        client = AzuretablesClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(
            status=200,
            text=(
                '{"value": [{"PartitionKey": "pk1", "RowKey": "rk1"}, '
                '{"PartitionKey": "pk1", "RowKey": "rk2"}]}'
            )
        )

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ) as mock_send:
            result = await client.get_entities_async(
                storage_account_name="mystorageaccount",
                table_name="mytable"
            )

            mock_send.assert_called_once()
            call_args = mock_send.call_args
            assert call_args[0][0] == "GET"
            assert "/storageAccounts/mystorageaccount/tables/mytable/entities" in call_args[0][1]
            assert len(result["value"]) == 2

    @pytest.mark.asyncio
    async def test_with_query_parameters(self, mock_token_provider):
        """Test GET request with query parameters."""
        client = AzuretablesClient(
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
            await client.get_entities_async(
                storage_account_name="mystorageaccount",
                table_name="mytable",
                next_partition_key="pk2",
                next_row_key="rk5",
                filter="PartitionKey eq 'pk1'",
                select="Name,Value"
            )

            call_args = mock_send.call_args
            url = call_args[0][1]
            assert "NextPartitionKey=pk2" in url
            assert "NextRowKey=rk5" in url
            assert "$filter=" in url
            assert "$select=" in url

    @pytest.mark.asyncio
    async def test_error_response_raises_exception(self, mock_token_provider):
        """Test that error response raises ConnectorException."""
        client = AzuretablesClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(status=404, text='{"error": "Table not found"}')

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ):
            with pytest.raises(ConnectorException) as exc_info:
                await client.get_entities_async(
                    storage_account_name="mystorageaccount",
                    table_name="nonexistent"
                )

            assert exc_info.value.status_code == 404


class TestGetEntity:
    """Tests for get_entity_async method."""

    @pytest.mark.asyncio
    async def test_success_with_json_response(self, mock_token_provider):
        """Test successful GET request."""
        client = AzuretablesClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(
            status=200,
            text='{"PartitionKey": "pk1", "RowKey": "rk1", "Name": "Test Entity"}'
        )

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ) as mock_send:
            result = await client.get_entity_async(
                storage_account_name="mystorageaccount",
                table_name="mytable",
                partition_key="pk1",
                row_key="rk1"
            )

            mock_send.assert_called_once()
            call_args = mock_send.call_args
            assert call_args[0][0] == "GET"
            assert "/entities(PartitionKey='pk1',RowKey='rk1')" in call_args[0][1]
            assert result["Name"] == "Test Entity"

    @pytest.mark.asyncio
    async def test_with_select_parameter(self, mock_token_provider):
        """Test GET request with select parameter."""
        client = AzuretablesClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(status=200, text='{"Name": "Test"}')

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ) as mock_send:
            await client.get_entity_async(
                storage_account_name="mystorageaccount",
                table_name="mytable",
                partition_key="pk1",
                row_key="rk1",
                select="Name"
            )

            call_args = mock_send.call_args
            url = call_args[0][1]
            assert "$select=Name" in url

    @pytest.mark.asyncio
    async def test_error_response_raises_exception(self, mock_token_provider):
        """Test that error response raises ConnectorException."""
        client = AzuretablesClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(status=404, text='{"error": "Entity not found"}')

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ):
            with pytest.raises(ConnectorException) as exc_info:
                await client.get_entity_async(
                    storage_account_name="mystorageaccount",
                    table_name="mytable",
                    partition_key="nonexistent",
                    row_key="nonexistent"
                )

            assert exc_info.value.status_code == 404


class TestGetTable:
    """Tests for get_table_async method."""

    @pytest.mark.asyncio
    async def test_success_with_json_response(self, mock_token_provider):
        """Test successful GET request."""
        client = AzuretablesClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(
            status=200,
            text='{"odata.id": "https://storage/Tables(\'mytable\')", "TableName": "mytable"}'
        )

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ) as mock_send:
            result = await client.get_table_async(
                storage_account_name="mystorageaccount",
                table_name="mytable"
            )

            mock_send.assert_called_once()
            call_args = mock_send.call_args
            assert call_args[0][0] == "GET"
            assert "/storageAccounts/mystorageaccount/tables/mytable" in call_args[0][1]
            assert result["TableName"] == "mytable"

    @pytest.mark.asyncio
    async def test_error_response_raises_exception(self, mock_token_provider):
        """Test that error response raises ConnectorException."""
        client = AzuretablesClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(status=404, text='{"error": "Table not found"}')

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ):
            with pytest.raises(ConnectorException) as exc_info:
                await client.get_table_async(
                    storage_account_name="mystorageaccount",
                    table_name="nonexistent"
                )

            assert exc_info.value.status_code == 404


class TestGetTables:
    """Tests for get_tables_async method."""

    @pytest.mark.asyncio
    async def test_success_with_json_response(self, mock_token_provider):
        """Test successful GET request."""
        client = AzuretablesClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(
            status=200,
            text='{"value": [{"TableName": "table1"}, {"TableName": "table2"}]}'
        )

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ) as mock_send:
            result = await client.get_tables_async(
                storage_account_name="mystorageaccount"
            )

            mock_send.assert_called_once()
            call_args = mock_send.call_args
            assert call_args[0][0] == "GET"
            assert "/storageAccounts/mystorageaccount/tables" in call_args[0][1]
            assert len(result["value"]) == 2

    @pytest.mark.asyncio
    async def test_empty_response_returns_none(self, mock_token_provider):
        """Test that empty response returns None."""
        client = AzuretablesClient(
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
            result = await client.get_tables_async(
                storage_account_name="mystorageaccount"
            )
            assert result is None

    @pytest.mark.asyncio
    async def test_error_response_raises_exception(self, mock_token_provider):
        """Test that error response raises ConnectorException."""
        client = AzuretablesClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(status=404, text='{"error": "Storage account not found"}')

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ):
            with pytest.raises(ConnectorException) as exc_info:
                await client.get_tables_async(
                    storage_account_name="nonexistent"
                )

            assert exc_info.value.status_code == 404


class TestInsertMergeEntity:
    """Tests for insert_merge_entity_async method."""

    @pytest.mark.asyncio
    async def test_success(self, mock_token_provider):
        """Test successful PATCH request (upsert merge)."""
        client = AzuretablesClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(status=204, text="")
        entity_input = InsertMergeEntityInput(
            additional_properties={"Name": "Updated", "Value": 100}
        )

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ) as mock_send:
            await client.insert_merge_entity_async(
                input=entity_input,
                storage_account_name="mystorageaccount",
                table_name="mytable",
                partition_key="pk1",
                row_key="rk1"
            )

            mock_send.assert_called_once()
            call_args = mock_send.call_args
            assert call_args[0][0] == "PATCH"
            assert "/entities(PartitionKey='pk1',RowKey='rk1')" in call_args[0][1]

    @pytest.mark.asyncio
    async def test_error_response_raises_exception(self, mock_token_provider):
        """Test that error response raises ConnectorException."""
        client = AzuretablesClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(status=400, text='{"error": "Invalid entity data"}')
        entity_input = InsertMergeEntityInput(additional_properties={})

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ):
            with pytest.raises(ConnectorException) as exc_info:
                await client.insert_merge_entity_async(
                    input=entity_input,
                    storage_account_name="mystorageaccount",
                    table_name="mytable",
                    partition_key="pk1",
                    row_key="rk1"
                )

            assert exc_info.value.status_code == 400


class TestInsertReplaceEntity:
    """Tests for insert_replace_entity_async method."""

    @pytest.mark.asyncio
    async def test_success(self, mock_token_provider):
        """Test successful PUT request (upsert replace)."""
        client = AzuretablesClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(status=204, text="")
        entity_input = InsertReplaceEntityInput(
            additional_properties={"Name": "Replaced", "Value": 200}
        )

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ) as mock_send:
            await client.insert_replace_entity_async(
                input=entity_input,
                storage_account_name="mystorageaccount",
                table_name="mytable",
                partition_key="pk1",
                row_key="rk1"
            )

            mock_send.assert_called_once()
            call_args = mock_send.call_args
            assert call_args[0][0] == "PUT"
            assert "/entities(PartitionKey='pk1',RowKey='rk1')" in call_args[0][1]

    @pytest.mark.asyncio
    async def test_error_response_raises_exception(self, mock_token_provider):
        """Test that error response raises ConnectorException."""
        client = AzuretablesClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(status=400, text='{"error": "Invalid entity data"}')
        entity_input = InsertReplaceEntityInput(additional_properties={})

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ):
            with pytest.raises(ConnectorException) as exc_info:
                await client.insert_replace_entity_async(
                    input=entity_input,
                    storage_account_name="mystorageaccount",
                    table_name="mytable",
                    partition_key="pk1",
                    row_key="rk1"
                )

            assert exc_info.value.status_code == 400


class TestMergeEntity:
    """Tests for merge_entity_async method."""

    @pytest.mark.asyncio
    async def test_success(self, mock_token_provider):
        """Test successful PATCH request."""
        client = AzuretablesClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(status=204, text="")
        entity_input = MergeEntityInput(
            additional_properties={"Name": "Merged"}
        )

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ) as mock_send:
            await client.merge_entity_async(
                input=entity_input,
                storage_account_name="mystorageaccount",
                table_name="mytable",
                partition_key="pk1",
                row_key="rk1"
            )

            mock_send.assert_called_once()
            call_args = mock_send.call_args
            assert call_args[0][0] == "PATCH"
            assert "/etag(PartitionKey='pk1',RowKey='rk1')" in call_args[0][1]

    @pytest.mark.asyncio
    async def test_error_response_raises_exception(self, mock_token_provider):
        """Test that error response raises ConnectorException."""
        client = AzuretablesClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(status=404, text='{"error": "Entity not found"}')
        entity_input = MergeEntityInput(additional_properties={})

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ):
            with pytest.raises(ConnectorException) as exc_info:
                await client.merge_entity_async(
                    input=entity_input,
                    storage_account_name="mystorageaccount",
                    table_name="mytable",
                    partition_key="nonexistent",
                    row_key="nonexistent"
                )

            assert exc_info.value.status_code == 404


class TestReplaceEntity:
    """Tests for replace_entity_async method."""

    @pytest.mark.asyncio
    async def test_success(self, mock_token_provider):
        """Test successful PUT request."""
        client = AzuretablesClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(status=204, text="")
        entity_input = ReplaceEntityInput(
            additional_properties={"Name": "Replaced", "Value": 999}
        )

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ) as mock_send:
            await client.replace_entity_async(
                input=entity_input,
                storage_account_name="mystorageaccount",
                table_name="mytable",
                partition_key="pk1",
                row_key="rk1"
            )

            mock_send.assert_called_once()
            call_args = mock_send.call_args
            assert call_args[0][0] == "PUT"
            assert "/etag(PartitionKey='pk1',RowKey='rk1')" in call_args[0][1]

    @pytest.mark.asyncio
    async def test_error_response_raises_exception(self, mock_token_provider):
        """Test that error response raises ConnectorException."""
        client = AzuretablesClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(status=404, text='{"error": "Entity not found"}')
        entity_input = ReplaceEntityInput(additional_properties={})

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ):
            with pytest.raises(ConnectorException) as exc_info:
                await client.replace_entity_async(
                    input=entity_input,
                    storage_account_name="mystorageaccount",
                    table_name="mytable",
                    partition_key="nonexistent",
                    row_key="nonexistent"
                )

            assert exc_info.value.status_code == 404


class TestDataClasses:
    """Tests for data class creation and attributes."""

    def test_create_entity_input(self):
        """Test CreateEntityInput dataclass creation."""
        entity = CreateEntityInput(
            additional_properties={"PartitionKey": "pk1", "RowKey": "rk1", "Name": "Test"}
        )

        assert entity.additional_properties["PartitionKey"] == "pk1"
        assert entity.additional_properties["Name"] == "Test"

    def test_insert_entity_response(self):
        """Test InsertEntityResponse dataclass creation."""
        response = InsertEntityResponse(
            odata_metadata="https://storage/$metadata#Tables/@Element",
            partition_key="pk1",
            row_key="rk1",
            additional_properties='{"Name": "Test"}'
        )

        assert response.odata_metadata is not None
        assert response.partition_key == "pk1"
        assert response.row_key == "rk1"

    def test_create_table_input(self):
        """Test CreateTableInput dataclass creation."""
        table_input = CreateTableInput(
            additional_properties={"TableName": "newtable"}
        )

        assert table_input.additional_properties["TableName"] == "newtable"

    def test_get_table_response(self):
        """Test GetTableResponse dataclass creation."""
        response = GetTableResponse(
            odata_id="https://storage/Tables('mytable')",
            table_name="mytable"
        )

        assert response.odata_id is not None
        assert response.table_name == "mytable"

    def test_get_entities_response(self):
        """Test GetEntitiesResponse dataclass creation."""
        item1 = Item(partition_key="pk1", row_key="rk1")
        item2 = Item(partition_key="pk1", row_key="rk2")
        response = GetEntitiesResponse(
            odata_metadata="https://storage/$metadata",
            value=[item1, item2]
        )

        assert response.value is not None
        assert len(response.value) == 2

    def test_get_entity_response(self):
        """Test GetEntityResponse dataclass creation."""
        response = GetEntityResponse(
            odata_metadata="https://storage/$metadata",
            partition_key="pk1",
            row_key="rk1",
            additional_properties='{"Name": "Entity1"}'
        )

        assert response.partition_key == "pk1"
        assert response.row_key == "rk1"

    def test_get_tables_response(self):
        """Test GetTablesResponse dataclass creation."""
        response = GetTablesResponse(
            odata_metadata="https://storage/$metadata",
            value=[{"TableName": "table1"}, {"TableName": "table2"}]
        )

        assert response.value is not None
        assert len(response.value) == 2

    def test_insert_merge_entity_input(self):
        """Test InsertMergeEntityInput dataclass creation."""
        entity = InsertMergeEntityInput(
            additional_properties={"Name": "Merged", "Value": 100}
        )

        assert entity.additional_properties["Name"] == "Merged"

    def test_insert_replace_entity_input(self):
        """Test InsertReplaceEntityInput dataclass creation."""
        entity = InsertReplaceEntityInput(
            additional_properties={"Name": "Replaced", "Value": 200}
        )

        assert entity.additional_properties["Name"] == "Replaced"

    def test_merge_entity_input(self):
        """Test MergeEntityInput dataclass creation."""
        entity = MergeEntityInput(
            additional_properties={"UpdatedField": "new value"}
        )

        assert entity.additional_properties["UpdatedField"] == "new value"

    def test_replace_entity_input(self):
        """Test ReplaceEntityInput dataclass creation."""
        entity = ReplaceEntityInput(
            additional_properties={"CompleteEntity": True}
        )

        assert entity.additional_properties["CompleteEntity"] is True

    def test_storage_account_list(self):
        """Test StorageAccountList dataclass creation."""
        account1 = StorageAccount(name="account1", display_name="Account 1")
        account2 = StorageAccount(name="account2", display_name="Account 2")
        account_list = StorageAccountList(value=[account1, account2])

        assert account_list.value is not None
        assert len(account_list.value) == 2

    def test_storage_account(self):
        """Test StorageAccount dataclass creation."""
        account = StorageAccount(
            name="mystorageaccount",
            display_name="My Storage Account"
        )

        assert account.name == "mystorageaccount"
        assert account.display_name == "My Storage Account"

    def test_item(self):
        """Test Item dataclass creation."""
        item = Item(
            partition_key="partition1",
            row_key="row1",
            additional_properties='{"Name": "Item1", "Value": 42}'
        )

        assert item.partition_key == "partition1"
        assert item.row_key == "row1"
        assert item.additional_properties is not None


class TestEdgeCases:
    """Tests for edge cases and special scenarios."""

    @pytest.mark.asyncio
    async def test_http_client_property_access(self, mock_token_provider):
        """Test accessing http_client property."""
        client = AzuretablesClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        assert client.http_client is not None
        assert client._http_client is client.http_client

    @pytest.mark.asyncio
    async def test_multiple_consecutive_calls(self, mock_token_provider):
        """Test multiple consecutive API calls."""
        client = AzuretablesClient(
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
            await client.get_tables_async(storage_account_name="account1")
            await client.get_tables_async(storage_account_name="account2")

            assert mock_send.call_count == 2

    @pytest.mark.asyncio
    async def test_special_characters_in_keys(self, mock_token_provider):
        """Test handling of special characters in partition/row keys."""
        client = AzuretablesClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(status=200, text='{"PartitionKey": "pk-1", "RowKey": "rk_1"}')

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ) as mock_send:
            await client.get_entity_async(
                storage_account_name="mystorageaccount",
                table_name="mytable",
                partition_key="pk-1",
                row_key="rk_1"
            )

            call_args = mock_send.call_args
            assert "(PartitionKey='pk-1',RowKey='rk_1')" in call_args[0][1]
