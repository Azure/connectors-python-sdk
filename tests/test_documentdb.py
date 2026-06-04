# Copyright (c) Microsoft Corporation. All rights reserved.

"""Unit tests for DocumentdbClient."""

import pytest
from unittest.mock import AsyncMock, patch
from azure.connectors.documentdb import (
    DocumentdbClient,
    PostDocumentsResponse,
    CreateStoredProcedureInput,
    CreateStoredProcedureResponse,
    ExecuteStoredProcedureInput,
    ObjectWithoutType,
    GetDocumentResponse,
    GetDocumentsResponse,
    GetStoredProceduresResponse,
    QueryDocumentsResponse,
    PutDocumentResponse,
    ReplaceStoredProcedureInput,
    DocumentsQuery,
    ObjectEntity,
    DocumentsCollection,
    GetAccountResponse,
    GetDatabasesResponse,
    GetDatabaseResponse,
    GetCollectionsResponse,
    GetCollectionResponse,
    PostDocumentsRequest,
    PutDocumentRequest,
    QueryRequest,
    QueryResponse,
    DataWithSensitivityLabelInfo,
    SensitivityLabelMetadata,
    CosmosDbAccountList,
    CosmosDbAccount,
)
from azure.connectors.sdk import (
    ConnectorClientOptions,
    ManagedIdentityTokenProvider,
    ConnectorException,
)
from tests.conftest import MockResponse


class TestDocumentdbClientInitialization:
    """Tests for DocumentdbClient initialization."""

    def test_init_with_valid_url_and_defaults(self):
        """Test initialization with valid URL and default parameters."""
        client = DocumentdbClient("https://example.azure.com/connections/test")

        assert client._connection_runtime_url == "https://example.azure.com/connections/test"
        assert client.connector_name == "documentdb"
        assert isinstance(client._http_client._token_provider, ManagedIdentityTokenProvider)

    def test_init_with_trailing_slash(self):
        """Test that trailing slash is removed from URL."""
        client = DocumentdbClient("https://example.azure.com/connections/test/")

        assert client._connection_runtime_url == "https://example.azure.com/connections/test"

    def test_init_with_custom_token_provider(self, mock_token_provider):
        """Test initialization with custom token provider."""
        client = DocumentdbClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        assert client._http_client._token_provider is mock_token_provider

    def test_init_with_custom_options(self, mock_token_provider):
        """Test initialization with custom options."""
        options = ConnectorClientOptions(timeout_seconds=60.0, max_retry_attempts=5)
        client = DocumentdbClient(
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
            DocumentdbClient("")

    def test_init_with_none_url_raises_error(self):
        """Test that None URL raises ValueError."""
        with pytest.raises(ValueError, match="connection_runtime_url cannot be None or empty"):
            DocumentdbClient(None)

    def test_connector_name_property(self, mock_token_provider):
        """Test connector_name property returns 'documentdb'."""
        client = DocumentdbClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        assert client.connector_name == "documentdb"


class TestDocumentdbClientLifecycle:
    """Tests for DocumentdbClient lifecycle methods."""

    @pytest.mark.asyncio
    async def test_close(self, mock_token_provider):
        """Test close method calls http_client.close."""
        client = DocumentdbClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        with patch.object(client._http_client, 'close', new_callable=AsyncMock) as mock_close:
            await client.close()
            mock_close.assert_called_once()

    @pytest.mark.asyncio
    async def test_context_manager(self, mock_token_provider):
        """Test async context manager functionality."""
        with patch.object(DocumentdbClient, 'close', new_callable=AsyncMock) as mock_close:
            async with DocumentdbClient(
                "https://example.azure.com/connections/test",
                token_provider=mock_token_provider
            ) as client:
                assert isinstance(client, DocumentdbClient)

            mock_close.assert_called_once()


class TestQueryDocuments:
    """Tests for query_documents_async method."""

    @pytest.mark.asyncio
    async def test_success_with_json_response(self, mock_token_provider):
        """Test successful GET request."""
        client = DocumentdbClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(
            status=200,
            text='{"value": [{"id": "doc1", "name": "Test Document"}], "count": 1}'
        )

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ) as mock_send:
            result = await client.query_documents_async(
                cosmos_db_account_name="mycosmosdb",
                database_id="mydb",
                container_id="mycontainer"
            )

            mock_send.assert_called_once()
            call_args = mock_send.call_args
            assert call_args[0][0] == "GET"
            assert "/cosmosdb/mycosmosdb/dbs/mydb/colls/mycontainer/query" in call_args[0][1]
            assert result["count"] == 1

    @pytest.mark.asyncio
    async def test_with_query_text(self, mock_token_provider):
        """Test GET request with query text parameter."""
        client = DocumentdbClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(
            status=200,
            text='{"value": [{"id": "doc1"}], "count": 1}'
        )

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ) as mock_send:
            await client.query_documents_async(
                cosmos_db_account_name="mycosmosdb",
                database_id="mydb",
                container_id="mycontainer",
                query_text="SELECT * FROM c WHERE c.status = 'active'"
            )

            call_args = mock_send.call_args
            url = call_args[0][1]
            assert "queryText=" in url

    @pytest.mark.asyncio
    async def test_with_partition_key(self, mock_token_provider):
        """Test GET request with partition key parameter."""
        client = DocumentdbClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(status=200, text='{"value": [], "count": 0}')

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ) as mock_send:
            await client.query_documents_async(
                cosmos_db_account_name="mycosmosdb",
                database_id="mydb",
                container_id="mycontainer",
                partition_key="region-1"
            )

            call_args = mock_send.call_args
            url = call_args[0][1]
            assert "partitionKey=region-1" in url

    @pytest.mark.asyncio
    async def test_with_all_query_parameters(self, mock_token_provider):
        """Test GET request with all query parameters."""
        client = DocumentdbClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(
            status=200,
            text='{"value": [], "count": 0, "continuationToken": "next-token"}'
        )

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ) as mock_send:
            await client.query_documents_async(
                cosmos_db_account_name="mycosmosdb",
                database_id="mydb",
                container_id="mycontainer",
                query_text="SELECT * FROM c",
                partition_key="pk1",
                max_item_count="100",
                continuation_token="abc123",
                consistency_level="Session",
                session_token="session-xyz"
            )

            call_args = mock_send.call_args
            url = call_args[0][1]
            assert "queryText=" in url
            assert "partitionKey=pk1" in url
            assert "maxItemCount=100" in url
            assert "continuationToken=abc123" in url
            assert "consistencyLevel=Session" in url
            assert "sessionToken=session-xyz" in url

    @pytest.mark.asyncio
    async def test_error_response_raises_exception(self, mock_token_provider):
        """Test that error response raises ConnectorException."""
        client = DocumentdbClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(status=404, text='{"error": "Container not found"}')

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ):
            with pytest.raises(ConnectorException) as exc_info:
                await client.query_documents_async(
                    cosmos_db_account_name="mycosmosdb",
                    database_id="mydb",
                    container_id="nonexistent"
                )

            assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    async def test_empty_response_returns_none(self, mock_token_provider):
        """Test that empty response returns None."""
        client = DocumentdbClient(
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
            result = await client.query_documents_async(
                cosmos_db_account_name="mycosmosdb",
                database_id="mydb",
                container_id="mycontainer"
            )
            assert result is None

    @pytest.mark.asyncio
    async def test_unauthorized_raises_exception(self, mock_token_provider):
        """Test that 401 unauthorized raises ConnectorException."""
        client = DocumentdbClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(status=401, text='{"error": "Unauthorized"}')

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ):
            with pytest.raises(ConnectorException) as exc_info:
                await client.query_documents_async(
                    cosmos_db_account_name="mycosmosdb",
                    database_id="mydb",
                    container_id="mycontainer"
                )

            assert exc_info.value.status_code == 401


class TestDataClasses:
    """Tests for data class creation and attributes."""

    def test_post_documents_response(self):
        """Test PostDocumentsResponse dataclass creation."""
        response = PostDocumentsResponse(
            rid="_rid123",
            ts=1640000000,
            self="/dbs/mydb/colls/mycoll/docs/doc1",
            etag='"00000000-0000-0000-0000-000000000000"',
            attachments="attachments/",
            id="doc1"
        )

        assert response.rid == "_rid123"
        assert response.ts == 1640000000
        assert response.id == "doc1"

    def test_create_stored_procedure_input(self):
        """Test CreateStoredProcedureInput dataclass creation."""
        sp_input = CreateStoredProcedureInput(
            body="function(params) { return params; }",
            id="myStoredProcedure"
        )

        assert sp_input.body == "function(params) { return params; }"
        assert sp_input.id == "myStoredProcedure"

    def test_create_stored_procedure_response(self):
        """Test CreateStoredProcedureResponse dataclass creation."""
        response = CreateStoredProcedureResponse(
            etag='"etag-value"',
            rid="_rid123",
            self="/dbs/mydb/colls/mycoll/sprocs/mysp",
            ts=1640000000,
            body="function(params) { return params; }",
            id="mysp"
        )

        assert response.etag == '"etag-value"'
        assert response.id == "mysp"

    def test_execute_stored_procedure_input(self):
        """Test ExecuteStoredProcedureInput dataclass creation."""
        sp_input = ExecuteStoredProcedureInput(
            additional_properties={"param1": "value1", "param2": 42}
        )

        assert sp_input.additional_properties["param1"] == "value1"
        assert sp_input.additional_properties["param2"] == 42

    def test_object_without_type(self):
        """Test ObjectWithoutType dataclass creation."""
        obj = ObjectWithoutType(
            additional_properties={"key1": "value1", "key2": [1, 2, 3]}
        )

        assert obj.additional_properties["key1"] == "value1"
        assert obj.additional_properties["key2"] == [1, 2, 3]

    def test_get_document_response(self):
        """Test GetDocumentResponse dataclass creation."""
        metadata = DataWithSensitivityLabelInfo(name="field1")
        response = GetDocumentResponse(metadata=[metadata])

        assert response.metadata is not None
        assert len(response.metadata) == 1

    def test_get_documents_response(self):
        """Test GetDocumentsResponse dataclass creation."""
        response = GetDocumentsResponse(
            rid="_rid123",
            documents=[{"id": "doc1"}, {"id": "doc2"}],
            metadata=None
        )

        assert response.rid == "_rid123"
        assert response.documents is not None
        assert len(response.documents) == 2

    def test_get_stored_procedures_response(self):
        """Test GetStoredProceduresResponse dataclass creation."""
        response = GetStoredProceduresResponse(
            count=2,
            rid="_rid123",
            stored_procedures=[{"id": "sp1"}, {"id": "sp2"}]
        )

        assert response.count == 2
        assert len(response.stored_procedures) == 2

    def test_query_documents_response(self):
        """Test QueryDocumentsResponse dataclass creation."""
        doc = ObjectWithoutType(additional_properties={"id": "doc1"})
        response = QueryDocumentsResponse(
            value=[doc],
            continuation_token="next-token",
            count=1,
            request_charge=3.5,
            session_token="session-123",
            activity_id="activity-456"
        )

        assert response.count == 1
        assert response.request_charge == 3.5
        assert response.continuation_token == "next-token"

    def test_put_document_response(self):
        """Test PutDocumentResponse dataclass creation."""
        response = PutDocumentResponse(rid="_rid123", id="doc1")

        assert response.rid == "_rid123"
        assert response.id == "doc1"

    def test_replace_stored_procedure_input(self):
        """Test ReplaceStoredProcedureInput dataclass creation."""
        sp_input = ReplaceStoredProcedureInput(
            body="function(params) { return params * 2; }",
            id="existingSp"
        )

        assert sp_input.body is not None
        assert sp_input.id == "existingSp"

    def test_documents_query(self):
        """Test DocumentsQuery dataclass creation."""
        query = DocumentsQuery(query_text="SELECT * FROM c WHERE c.status = 'active'")

        assert query.query_text is not None
        assert "SELECT" in query.query_text

    def test_object_entity(self):
        """Test ObjectEntity dataclass creation."""
        entity = ObjectEntity(
            additional_properties={"name": "Test", "value": 100}
        )

        assert entity.additional_properties["name"] == "Test"

    def test_documents_collection(self):
        """Test DocumentsCollection dataclass creation."""
        doc = ObjectWithoutType(additional_properties={"id": "doc1"})
        collection = DocumentsCollection(
            value=[doc],
            continuation_token="token-123",
            count=1,
            request_charge=2.5,
            session_token="session-abc",
            activity_id="activity-xyz"
        )

        assert collection.count == 1
        assert collection.request_charge == 2.5

    def test_get_account_response(self):
        """Test GetAccountResponse dataclass creation."""
        response = GetAccountResponse(
            self="/",
            rid="_rid",
            id="myaccount"
        )

        assert response.id == "myaccount"

    def test_get_databases_response(self):
        """Test GetDatabasesResponse dataclass creation."""
        response = GetDatabasesResponse(
            rid="_rid",
            databases=[{"id": "db1"}, {"id": "db2"}],
            count=2
        )

        assert response.count == 2
        assert len(response.databases) == 2

    def test_get_database_response(self):
        """Test GetDatabaseResponse dataclass creation."""
        response = GetDatabaseResponse(
            id="mydb",
            rid="_rid123",
            self="/dbs/mydb",
            etag='"etag"',
            colls="colls/",
            users="users/",
            ts=1640000000
        )

        assert response.id == "mydb"
        assert response.ts == 1640000000

    def test_get_collections_response(self):
        """Test GetCollectionsResponse dataclass creation."""
        response = GetCollectionsResponse(
            rid="_rid",
            document_collections=[{"id": "coll1"}, {"id": "coll2"}],
            count=2
        )

        assert response.count == 2
        assert len(response.document_collections) == 2

    def test_get_collection_response(self):
        """Test GetCollectionResponse dataclass creation."""
        response = GetCollectionResponse(
            additional_properties={"id": "mycollection", "partitionKey": {"paths": ["/pk"]}}
        )

        assert response.additional_properties["id"] == "mycollection"

    def test_post_documents_request(self):
        """Test PostDocumentsRequest dataclass creation."""
        request = PostDocumentsRequest(
            additional_properties={"id": "newdoc", "name": "New Document"}
        )

        assert request.additional_properties["id"] == "newdoc"

    def test_put_document_request(self):
        """Test PutDocumentRequest dataclass creation."""
        request = PutDocumentRequest(
            additional_properties={"id": "doc1", "name": "Updated Document"}
        )

        assert request.additional_properties["name"] == "Updated Document"

    def test_query_request(self):
        """Test QueryRequest dataclass creation."""
        request = QueryRequest(query="SELECT * FROM c")

        assert request.query == "SELECT * FROM c"

    def test_query_response(self):
        """Test QueryResponse dataclass creation."""
        response = QueryResponse(
            rid="_rid",
            count=5.0,
            documents=[{"id": "doc1"}, {"id": "doc2"}]
        )

        assert response.count == 5.0
        assert len(response.documents) == 2

    def test_data_with_sensitivity_label_info(self):
        """Test DataWithSensitivityLabelInfo dataclass creation."""
        label = SensitivityLabelMetadata(name="Confidential")
        data = DataWithSensitivityLabelInfo(
            name="customerEmail",
            sensitivity_label_info=[label]
        )

        assert data.name == "customerEmail"
        assert len(data.sensitivity_label_info) == 1

    def test_sensitivity_label_metadata(self):
        """Test SensitivityLabelMetadata dataclass creation."""
        label = SensitivityLabelMetadata(
            sensitivity_label_id="label-001",
            name="Confidential",
            display_name="Confidential - Internal Use Only",
            tooltip="This data is confidential",
            priority=1,
            color="#FF0000",
            is_encrypted=True,
            is_enabled=True,
            is_parent=False,
            parent_sensitivity_label_id=None
        )

        assert label.name == "Confidential"
        assert label.is_encrypted is True
        assert label.priority == 1

    def test_cosmos_db_account_list(self):
        """Test CosmosDbAccountList dataclass creation."""
        account1 = CosmosDbAccount(name="account1", display_name="Account 1")
        account2 = CosmosDbAccount(name="account2", display_name="Account 2")
        account_list = CosmosDbAccountList(value=[account1, account2])

        assert account_list.value is not None
        assert len(account_list.value) == 2

    def test_cosmos_db_account(self):
        """Test CosmosDbAccount dataclass creation."""
        account = CosmosDbAccount(
            name="mycosmosdb",
            display_name="My Cosmos DB Account"
        )

        assert account.name == "mycosmosdb"
        assert account.display_name == "My Cosmos DB Account"


class TestEdgeCases:
    """Tests for edge cases and special scenarios."""

    @pytest.mark.asyncio
    async def test_http_client_property_access(self, mock_token_provider):
        """Test accessing http_client property."""
        client = DocumentdbClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        assert client.http_client is not None
        assert client._http_client is client.http_client

    @pytest.mark.asyncio
    async def test_multiple_consecutive_calls(self, mock_token_provider):
        """Test multiple consecutive API calls."""
        client = DocumentdbClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(status=200, text='{"value": [], "count": 0}')

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ) as mock_send:
            await client.query_documents_async(
                cosmos_db_account_name="account1",
                database_id="db1",
                container_id="container1"
            )
            await client.query_documents_async(
                cosmos_db_account_name="account2",
                database_id="db2",
                container_id="container2"
            )

            assert mock_send.call_count == 2

    @pytest.mark.asyncio
    async def test_special_characters_in_ids(self, mock_token_provider):
        """Test handling of special characters in database/container IDs."""
        client = DocumentdbClient(
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
            await client.query_documents_async(
                cosmos_db_account_name="my-cosmos-db",
                database_id="my-database",
                container_id="my-container"
            )

            call_args = mock_send.call_args
            url = call_args[0][1]
            assert "/cosmosdb/my-cosmos-db/dbs/my-database/colls/my-container/query" in url
