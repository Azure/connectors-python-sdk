# Copyright (c) Microsoft Corporation. All rights reserved.

"""Unit tests for KustoClient."""

import json
import pytest
from unittest.mock import AsyncMock, patch
from azure.connectors.kusto import (
    KustoClient,
    QueryAndListSchema,
    ControlCommandAndListSchema,
    QueryAndVisualizeSchema,
    CommandAndVisualizeSchema,
    MCPQueryRequest,
)
from azure.connectors.sdk import (
    ConnectorClientOptions,
    ManagedIdentityTokenProvider,
    ConnectorException,
)
from tests.conftest import MockTokenProvider, MockResponse


class TestKustoClientInitialization:
    """Tests for KustoClient initialization."""

    def test_init_with_valid_url_and_defaults(self):
        """Test initialization with valid URL and default parameters."""
        client = KustoClient("https://example.azure.com/connections/test")

        assert client._connection_runtime_url == "https://example.azure.com/connections/test"
        assert client.connector_name == "kusto"
        assert isinstance(client._http_client._token_provider, ManagedIdentityTokenProvider)

    def test_init_with_trailing_slash(self):
        """Test that trailing slash is removed from URL."""
        client = KustoClient("https://example.azure.com/connections/test/")

        assert client._connection_runtime_url == "https://example.azure.com/connections/test"

    def test_init_with_custom_token_provider(self, mock_token_provider):
        """Test initialization with custom token provider."""
        client = KustoClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        assert client._http_client._token_provider is mock_token_provider

    def test_init_with_custom_options(self, mock_token_provider):
        """Test initialization with custom options."""
        options = ConnectorClientOptions(timeout_seconds=60.0, max_retry_attempts=5)
        client = KustoClient(
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
            KustoClient("")

    def test_init_with_none_url_raises_error(self):
        """Test that None URL raises ValueError."""
        with pytest.raises(ValueError, match="connection_runtime_url cannot be None or empty"):
            KustoClient(None)

    def test_connector_name_property(self, mock_token_provider):
        """Test connector_name property returns 'kusto'."""
        client = KustoClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        assert client.connector_name == "kusto"


class TestKustoClientLifecycle:
    """Tests for KustoClient lifecycle methods."""

    @pytest.mark.asyncio
    async def test_close(self, mock_token_provider):
        """Test close method calls http_client.close."""
        client = KustoClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        with patch.object(client._http_client, 'close', new_callable=AsyncMock) as mock_close:
            await client.close()
            mock_close.assert_called_once()

    @pytest.mark.asyncio
    async def test_context_manager(self, mock_token_provider):
        """Test async context manager functionality."""
        with patch.object(KustoClient, 'close', new_callable=AsyncMock) as mock_close:
            async with KustoClient(
                "https://example.azure.com/connections/test",
                token_provider=mock_token_provider
            ) as client:
                assert isinstance(client, KustoClient)

            mock_close.assert_called_once()


class TestListKustoResults:
    """Tests for list_kusto_results_async method."""

    @pytest.mark.asyncio
    async def test_success_with_json_response(self, mock_token_provider):
        """Test successful query execution with JSON response."""
        client = KustoClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(
            status=200,
            text='{"rows": [{"col1": "value1"}], "columns": ["col1"]}'
        )

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ) as mock_send:
            input_schema = QueryAndListSchema(
                cluster="testcluster",
                db="testdb",
                csl="TestTable | take 10"
            )
            result = await client.list_kusto_results_async(input_schema)

            mock_send.assert_called_once_with(
                "POST",
                "https://example.azure.com/connections/test/ListKustoResults/false",
                body=input_schema
            )
            assert result == {"rows": [{"col1": "value1"}], "columns": ["col1"]}

    @pytest.mark.asyncio
    async def test_success_with_empty_response(self, mock_token_provider):
        """Test successful query with empty response body."""
        client = KustoClient(
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
            input_schema = QueryAndListSchema()
            result = await client.list_kusto_results_async(input_schema)

            assert result is None

    @pytest.mark.asyncio
    async def test_error_response_raises_exception(self, mock_token_provider):
        """Test that non-2xx response raises ConnectorException."""
        client = KustoClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(
            status=400,
            text='{"error": "Invalid query"}'
        )

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ):
            input_schema = QueryAndListSchema()

            with pytest.raises(ConnectorException) as exc_info:
                await client.list_kusto_results_async(input_schema)

            assert exc_info.value.status_code == 400
            assert exc_info.value.response_body == '{"error": "Invalid query"}'
            expected_op = "POST https://example.azure.com/connections/test/"
            assert expected_op in exc_info.value.operation

    @pytest.mark.asyncio
    async def test_500_error_raises_exception(self, mock_token_provider):
        """Test that 500 error raises ConnectorException."""
        client = KustoClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(
            status=500,
            text='Internal Server Error'
        )

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ):
            with pytest.raises(ConnectorException) as exc_info:
                await client.list_kusto_results_async(QueryAndListSchema())

            assert exc_info.value.status_code == 500


class TestListKustoShowCommandResults:
    """Tests for list_kusto_show_command_results_async method."""

    @pytest.mark.asyncio
    async def test_success_with_json_response(self, mock_token_provider):
        """Test successful show command execution."""
        client = KustoClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(
            status=200,
            text='{"command_result": "success"}'
        )

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ) as mock_send:
            input_schema = ControlCommandAndListSchema(
                cluster="testcluster",
                db="testdb",
                csl=".show tables"
            )
            result = await client.list_kusto_show_command_results_async(input_schema)

            mock_send.assert_called_once_with(
                "POST",
                "https://example.azure.com/connections/test/ListKustoShowCommandResults",
                body=input_schema
            )
            assert result == {"command_result": "success"}

    @pytest.mark.asyncio
    async def test_empty_response_returns_none(self, mock_token_provider):
        """Test that empty response returns None."""
        client = KustoClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(status=204, text="")

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ):
            result = await client.list_kusto_show_command_results_async(
                ControlCommandAndListSchema()
            )

            assert result is None

    @pytest.mark.asyncio
    async def test_error_response_raises_exception(self, mock_token_provider):
        """Test that error response raises ConnectorException."""
        client = KustoClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(
            status=403,
            text='{"error": "Forbidden"}'
        )

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ):
            with pytest.raises(ConnectorException) as exc_info:
                await client.list_kusto_show_command_results_async(
                    ControlCommandAndListSchema()
                )

            assert exc_info.value.status_code == 403


class TestRunKustoQueryAndVisualizeResults:
    """Tests for run_kusto_query_and_visualize_results_async method."""

    @pytest.mark.asyncio
    async def test_success_with_chart_data(self, mock_token_provider):
        """Test successful query with chart visualization."""
        client = KustoClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(
            status=200,
            text='{"chart": "data", "type": "line"}'
        )

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ) as mock_send:
            input_schema = QueryAndVisualizeSchema(
                cluster="testcluster",
                db="testdb",
                csl="TestTable | summarize count() by timestamp",
                chart_type="line"
            )
            result = await client.run_kusto_query_and_visualize_results_async(input_schema)

            mock_send.assert_called_once_with(
                "POST",
                "https://example.azure.com/connections/test/RunKustoAndVisualizeResults/false",
                body=input_schema
            )
            assert result == {"chart": "data", "type": "line"}

    @pytest.mark.asyncio
    async def test_error_response_raises_exception(self, mock_token_provider):
        """Test that error response raises ConnectorException."""
        client = KustoClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(
            status=400,
            text='{"error": "Invalid chart type"}'
        )

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ):
            with pytest.raises(ConnectorException) as exc_info:
                await client.run_kusto_query_and_visualize_results_async(
                    QueryAndVisualizeSchema()
                )

            assert exc_info.value.status_code == 400


class TestRunKustoCommandAndVisualizeResults:
    """Tests for run_kusto_command_and_visualize_results_async method."""

    @pytest.mark.asyncio
    async def test_success_with_chart_data(self, mock_token_provider):
        """Test successful control command with chart visualization."""
        client = KustoClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(
            status=200,
            text='{"visualization": "bar_chart"}'
        )

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ) as mock_send:
            input_schema = CommandAndVisualizeSchema(
                cluster="testcluster",
                db="testdb",
                csl=".show schema",
                chart_type="bar"
            )
            result = await client.run_kusto_command_and_visualize_results_async(input_schema)

            mock_send.assert_called_once_with(
                "POST",
                "https://example.azure.com/connections/test/RunKustoAndVisualizeResults/true",
                body=input_schema
            )
            assert result == {"visualization": "bar_chart"}

    @pytest.mark.asyncio
    async def test_empty_response_returns_none(self, mock_token_provider):
        """Test that empty response returns None."""
        client = KustoClient(
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
            result = await client.run_kusto_command_and_visualize_results_async(
                CommandAndVisualizeSchema()
            )

            assert result is None


class TestRunAsyncControlCommandAndWait:
    """Tests for run_async_control_command_and_wait_async method."""

    @pytest.mark.asyncio
    async def test_success_with_command_id(self, mock_token_provider):
        """Test successful async command execution."""
        client = KustoClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(
            status=200,
            text='{"commandId": "123", "state": "Completed", "status": "Success"}'
        )

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ) as mock_send:
            input_schema = ControlCommandAndListSchema(
                cluster="testcluster",
                db="testdb",
                csl=".set-or-append async TargetTable <| SourceTable"
            )
            result = await client.run_async_control_command_and_wait_async(input_schema)

            mock_send.assert_called_once_with(
                "POST",
                "https://example.azure.com/connections/test/RunAsyncControlCommandAndWait",
                body=input_schema
            )
            assert result["commandId"] == "123"
            assert result["state"] == "Completed"
            assert result["status"] == "Success"

    @pytest.mark.asyncio
    async def test_error_response_raises_exception(self, mock_token_provider):
        """Test that error response raises ConnectorException."""
        client = KustoClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(
            status=408,
            text='{"error": "Command timeout"}'
        )

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ):
            with pytest.raises(ConnectorException) as exc_info:
                await client.run_async_control_command_and_wait_async(
                    ControlCommandAndListSchema()
                )

            assert exc_info.value.status_code == 408


class TestMCPKustoQueryManagement:
    """Tests for mcp_kusto_query_management_async method."""

    @pytest.mark.asyncio
    async def test_success_without_session_id(self, mock_token_provider):
        """Test successful MCP query without session ID."""
        client = KustoClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(
            status=200,
            text='{"jsonrpc": "2.0", "id": "1", "result": {"data": "test"}}'
        )

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ) as mock_send:
            input_request = MCPQueryRequest(
                jsonrpc="2.0",
                id="1",
                method="query",
                params={"query": "TestTable | take 1"}
            )
            result = await client.mcp_kusto_query_management_async(input_request)

            mock_send.assert_called_once_with(
                "POST",
                "https://example.azure.com/connections/test/mcp/KustoQueryManagement",
                body=input_request
            )
            assert result["jsonrpc"] == "2.0"
            assert result["id"] == "1"

    @pytest.mark.asyncio
    async def test_success_with_session_id(self, mock_token_provider):
        """Test successful MCP query with session ID."""
        client = KustoClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(
            status=200,
            text='{"jsonrpc": "2.0", "id": "2", "result": {}}'
        )

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ) as mock_send:
            input_request = MCPQueryRequest(jsonrpc="2.0", id="2", method="init")
            result = await client.mcp_kusto_query_management_async(
                input_request,
                session_id="session-123"
            )

            base_url = "https://example.azure.com/connections/test"
            expected_path = f"{base_url}/mcp/KustoQueryManagement?sessionId=session-123"
            mock_send.assert_called_once_with(
                "POST",
                expected_path,
                body=input_request
            )
            assert result["jsonrpc"] == "2.0"

    @pytest.mark.asyncio
    async def test_session_id_with_special_characters(self, mock_token_provider):
        """Test MCP query with session ID containing special characters."""
        client = KustoClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(status=200, text='{"result": "ok"}')

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ) as mock_send:
            await client.mcp_kusto_query_management_async(
                MCPQueryRequest(),
                session_id="session with spaces"
            )

            # Verify URL encoding of spaces
            call_args = mock_send.call_args
            assert "session%20with%20spaces" in call_args[0][1]

    @pytest.mark.asyncio
    async def test_empty_response_returns_none(self, mock_token_provider):
        """Test that empty response returns None."""
        client = KustoClient(
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
            result = await client.mcp_kusto_query_management_async(MCPQueryRequest())

            assert result is None

    @pytest.mark.asyncio
    async def test_error_response_raises_exception(self, mock_token_provider):
        """Test that error response raises ConnectorException."""
        client = KustoClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(
            status=500,
            text='{"jsonrpc": "2.0", "error": {"code": -1, "message": "Internal error"}}'
        )

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ):
            with pytest.raises(ConnectorException) as exc_info:
                await client.mcp_kusto_query_management_async(MCPQueryRequest())

            assert exc_info.value.status_code == 500


class TestDataClasses:
    """Tests for data classes and type definitions."""

    def test_query_and_list_schema_creation(self):
        """Test QueryAndListSchema dataclass creation."""
        schema = QueryAndListSchema(
            cluster="testcluster",
            db="testdb",
            csl="TestTable | take 10"
        )

        assert schema.cluster == "testcluster"
        assert schema.db == "testdb"
        assert schema.csl == "TestTable | take 10"

    def test_control_command_and_list_schema_creation(self):
        """Test ControlCommandAndListSchema dataclass creation."""
        schema = ControlCommandAndListSchema(
            cluster="testcluster",
            db="testdb",
            csl=".show tables"
        )

        assert schema.cluster == "testcluster"
        assert schema.db == "testdb"
        assert schema.csl == ".show tables"

    def test_query_and_visualize_schema_creation(self):
        """Test QueryAndVisualizeSchema dataclass creation."""
        schema = QueryAndVisualizeSchema(
            cluster="testcluster",
            db="testdb",
            csl="TestTable | summarize count()",
            chart_type="bar"
        )

        assert schema.cluster == "testcluster"
        assert schema.db == "testdb"
        assert schema.csl == "TestTable | summarize count()"
        assert schema.chart_type == "bar"

    def test_command_and_visualize_schema_creation(self):
        """Test CommandAndVisualizeSchema dataclass creation."""
        schema = CommandAndVisualizeSchema(
            cluster="testcluster",
            db="testdb",
            csl=".show schema",
            chart_type="pie"
        )

        assert schema.cluster == "testcluster"
        assert schema.db == "testdb"
        assert schema.csl == ".show schema"
        assert schema.chart_type == "pie"

    def test_mcp_query_request_creation(self):
        """Test MCPQueryRequest dataclass creation."""
        request = MCPQueryRequest(
            jsonrpc="2.0",
            id="123",
            method="query",
            params={"query": "test"},
            result=None,
            error=None,
            callback_endpoint="https://callback.example.com"
        )

        assert request.jsonrpc == "2.0"
        assert request.id == "123"
        assert request.method == "query"
        assert request.params == {"query": "test"}
        assert request.callback_endpoint == "https://callback.example.com"

    def test_dataclasses_with_defaults(self):
        """Test that dataclasses can be created with default None values."""
        schema = QueryAndListSchema()

        assert schema.cluster is None
        assert schema.db is None
        assert schema.csl is None


class TestEdgeCases:
    """Tests for edge cases and boundary conditions."""

    @pytest.mark.asyncio
    async def test_multiple_consecutive_calls(self, mock_token_provider):
        """Test multiple consecutive API calls work correctly."""
        client = KustoClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response_1 = MockResponse(status=200, text='{"result": "first"}')
        mock_response_2 = MockResponse(status=200, text='{"result": "second"}')

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            side_effect=[mock_response_1, mock_response_2]
        ):
            result_1 = await client.list_kusto_results_async(QueryAndListSchema())
            result_2 = await client.list_kusto_results_async(QueryAndListSchema())

            assert result_1 == {"result": "first"}
            assert result_2 == {"result": "second"}

    @pytest.mark.asyncio
    async def test_json_parse_error_raises_exception(self, mock_token_provider):
        """Test that invalid JSON in response raises an error."""
        client = KustoClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(status=200, text='invalid json{')

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ):
            with pytest.raises(json.JSONDecodeError):
                await client.list_kusto_results_async(QueryAndListSchema())

    @pytest.mark.asyncio
    async def test_url_construction_with_multiple_trailing_slashes(self):
        """Test URL construction handles multiple trailing slashes."""
        client = KustoClient(
            "https://example.azure.com/connections/test///",
            token_provider=MockTokenProvider()
        )

        # rstrip('/') should remove all trailing slashes
        assert client._connection_runtime_url == "https://example.azure.com/connections/test"

    def test_http_client_property_access(self, mock_token_provider):
        """Test that http_client property is accessible."""
        client = KustoClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        assert client.http_client is not None
        assert client.http_client is client._http_client


class TestListKustoResultsSchema:
    """Tests for list_kusto_results_schema_async method."""

    @pytest.mark.asyncio
    async def test_success_returns_schema(self, mock_token_provider):
        """Test successful query-schema retrieval."""
        client = KustoClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )
        input_schema = QueryAndListSchema(
            cluster="testcluster",
            db="testdb",
            csl="TestTable | take 10"
        )

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=MockResponse(
                status=200,
                text='{"columns": [{"name": "Timestamp"}]}'
            )
        ) as mock_send:
            result = await client.list_kusto_results_schema_async(input_schema)

            mock_send.assert_called_once_with(
                "POST",
                "https://example.azure.com/connections/test/ListKustoResultsSchema",
                body=input_schema
            )
            assert result["columns"][0]["name"] == "Timestamp"

    @pytest.mark.asyncio
    async def test_error_response_raises_exception(self, mock_token_provider):
        """Test a non-2xx response raises ConnectorException."""
        client = KustoClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=MockResponse(status=400, text="Invalid query")
        ):
            with pytest.raises(ConnectorException) as exc_info:
                await client.list_kusto_results_schema_async(
                    QueryAndListSchema()
                )

            assert exc_info.value.status_code == 400
