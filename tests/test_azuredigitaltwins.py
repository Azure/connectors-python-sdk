# Copyright (c) Microsoft Corporation. All rights reserved.

"""Unit tests for AzuredigitaltwinsClient."""

import pytest
from unittest.mock import AsyncMock, patch
from azure.connectors.azuredigitaltwins import (
    AzuredigitaltwinsClient,
    AddTwinInput,
    AddRelationshipInput,
    ListModelsResponse,
    GetModelByIdResponse,
    TwinResult,
    GetComponentResult,
    TwinRelationship,
    ListIncomingRelationshipsResponse,
    SendTelemetryInput,
    SendComponentTelemetryInput,
    ListRelationshipsResponse,
    QueryTwinsInput,
    QueryResult,
    IncomingRelationship,
)
from azure.connectors.sdk import (
    ConnectorClientOptions,
    ManagedIdentityTokenProvider,
    ConnectorException,
)
from tests.conftest import MockResponse


class TestAzuredigitaltwinsClientInitialization:
    """Tests for AzuredigitaltwinsClient initialization."""

    def test_init_with_valid_url_and_defaults(self):
        """Test initialization with valid URL and default parameters."""
        client = AzuredigitaltwinsClient(
            "https://example.azure.com/connections/test"
        )

        assert client._connection_runtime_url == (
            "https://example.azure.com/connections/test"
        )
        assert client.connector_name == "azuredigitaltwins"
        assert isinstance(
            client._http_client._token_provider, ManagedIdentityTokenProvider
        )

    def test_init_with_trailing_slash(self):
        """Test that trailing slash is removed from URL."""
        client = AzuredigitaltwinsClient(
            "https://example.azure.com/connections/test/"
        )

        assert client._connection_runtime_url == (
            "https://example.azure.com/connections/test"
        )

    def test_init_with_custom_token_provider(self, mock_token_provider):
        """Test initialization with custom token provider."""
        client = AzuredigitaltwinsClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        assert client._http_client._token_provider is mock_token_provider

    def test_init_with_custom_options(self, mock_token_provider):
        """Test initialization with custom options."""
        options = ConnectorClientOptions(
            timeout_seconds=60.0, max_retry_attempts=5
        )
        client = AzuredigitaltwinsClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider,
            options=options
        )

        assert client._options is options
        assert client._options.timeout_seconds == 60.0
        assert client._options.max_retry_attempts == 5

    def test_init_with_empty_url_raises_error(self):
        """Test that empty URL raises ValueError."""
        with pytest.raises(
            ValueError, match="connection_runtime_url cannot be None or empty"
        ):
            AzuredigitaltwinsClient("")

    def test_init_with_none_url_raises_error(self):
        """Test that None URL raises ValueError."""
        with pytest.raises(
            ValueError, match="connection_runtime_url cannot be None or empty"
        ):
            AzuredigitaltwinsClient(None)

    def test_connector_name_property(self, mock_token_provider):
        """Test connector_name property returns 'azuredigitaltwins'."""
        client = AzuredigitaltwinsClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        assert client.connector_name == "azuredigitaltwins"


class TestAzuredigitaltwinsClientLifecycle:
    """Tests for AzuredigitaltwinsClient lifecycle methods."""

    @pytest.mark.asyncio
    async def test_close(self, mock_token_provider):
        """Test close method calls http_client.close."""
        client = AzuredigitaltwinsClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        with patch.object(
            client._http_client, 'close', new_callable=AsyncMock
        ) as mock_close:
            await client.close()
            mock_close.assert_called_once()

    @pytest.mark.asyncio
    async def test_context_manager(self, mock_token_provider):
        """Test async context manager functionality."""
        with patch.object(
            AzuredigitaltwinsClient, 'close', new_callable=AsyncMock
        ) as mock_close:
            async with AzuredigitaltwinsClient(
                "https://example.azure.com/connections/test",
                token_provider=mock_token_provider
            ) as client:
                assert isinstance(client, AzuredigitaltwinsClient)

            mock_close.assert_called_once()


class TestListModelsAsync:
    """Tests for list_models_async method."""

    @pytest.mark.asyncio
    async def test_success_with_json_response(self, mock_token_provider):
        """Test successful models list with JSON response."""
        client = AzuredigitaltwinsClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(
            status=200,
            text='{"value": [{"id": "dtmi:example:Room;1"}]}'
        )

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ) as mock_send:
            result = await client.list_models_async(api_version="2023-02-27-preview")

            mock_send.assert_called_once()
            call_args = mock_send.call_args
            assert call_args[0][0] == "GET"
            assert "/models" in call_args[0][1]
            assert result["value"][0]["id"] == "dtmi:example:Room;1"

    @pytest.mark.asyncio
    async def test_with_optional_parameters(self, mock_token_provider):
        """Test list models with optional parameters."""
        client = AzuredigitaltwinsClient(
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
            await client.list_models_async(
                api_version="2023-02-27-preview",
                dependencies_for="dtmi:example:Room;1",
                include_model_definition="true"
            )

            call_args = mock_send.call_args
            assert "dependenciesFor=" in call_args[0][1]
            assert "includeModelDefinition=" in call_args[0][1]

    @pytest.mark.asyncio
    async def test_error_response_raises_exception(self, mock_token_provider):
        """Test that non-2xx response raises ConnectorException."""
        client = AzuredigitaltwinsClient(
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
                await client.list_models_async(api_version="2023-02-27-preview")

            assert exc_info.value.status_code == 401


class TestGetModelByIdAsync:
    """Tests for get_model_by_id_async method."""

    @pytest.mark.asyncio
    async def test_success_with_json_response(self, mock_token_provider):
        """Test successful model retrieval with JSON response."""
        client = AzuredigitaltwinsClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(
            status=200,
            text='{"id": "dtmi:example:Room;1", "decommissioned": false}'
        )

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ) as mock_send:
            result = await client.get_model_by_id_async(
                modelid="dtmi:example:Room;1",
                api_version="2023-02-27-preview"
            )

            mock_send.assert_called_once()
            assert result["id"] == "dtmi:example:Room;1"

    @pytest.mark.asyncio
    async def test_error_response_raises_exception(self, mock_token_provider):
        """Test that non-2xx response raises ConnectorException."""
        client = AzuredigitaltwinsClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(status=404, text='{"error": "Model not found"}')

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ):
            with pytest.raises(ConnectorException) as exc_info:
                await client.get_model_by_id_async(
                    modelid="nonexistent",
                    api_version="2023-02-27-preview"
                )

            assert exc_info.value.status_code == 404


class TestDeleteModelAsync:
    """Tests for delete_model_async method."""

    @pytest.mark.asyncio
    async def test_success(self, mock_token_provider):
        """Test successful model deletion."""
        client = AzuredigitaltwinsClient(
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
            await client.delete_model_async(
                modelid="dtmi:example:Room;1",
                api_version="2023-02-27-preview"
            )

            mock_send.assert_called_once()
            call_args = mock_send.call_args
            assert call_args[0][0] == "DELETE"


class TestGetTwinByIdAsync:
    """Tests for get_twin_by_id_async method."""

    @pytest.mark.asyncio
    async def test_success_with_json_response(self, mock_token_provider):
        """Test successful twin retrieval with JSON response."""
        client = AzuredigitaltwinsClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(
            status=200,
            text='{"$dtId": "room1", "$metadata": {"$model": "dtmi:example:Room;1"}}'
        )

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ) as mock_send:
            result = await client.get_twin_by_id_async(
                twinid="room1",
                api_version="2023-02-27-preview"
            )

            mock_send.assert_called_once()
            assert result["$dtId"] == "room1"

    @pytest.mark.asyncio
    async def test_error_response_raises_exception(self, mock_token_provider):
        """Test that non-2xx response raises ConnectorException."""
        client = AzuredigitaltwinsClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(status=404, text='{"error": "Twin not found"}')

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ):
            with pytest.raises(ConnectorException) as exc_info:
                await client.get_twin_by_id_async(
                    twinid="nonexistent",
                    api_version="2023-02-27-preview"
                )

            assert exc_info.value.status_code == 404


class TestAddTwinAsync:
    """Tests for add_twin_async method."""

    @pytest.mark.asyncio
    async def test_success_with_json_response(self, mock_token_provider):
        """Test successful twin creation with JSON response."""
        client = AzuredigitaltwinsClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(
            status=200,
            text='{"$dtId": "room1"}'
        )

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ) as mock_send:
            input_data = AddTwinInput(value='{"$dtId": "room1"}')
            result = await client.add_twin_async(
                input=input_data,
                twinid="room1",
                api_version="2023-02-27-preview"
            )

            mock_send.assert_called_once()
            call_args = mock_send.call_args
            assert call_args[0][0] == "PUT"
            assert result["$dtId"] == "room1"


class TestDeleteTwinAsync:
    """Tests for delete_twin_async method."""

    @pytest.mark.asyncio
    async def test_success(self, mock_token_provider):
        """Test successful twin deletion."""
        client = AzuredigitaltwinsClient(
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
            await client.delete_twin_async(
                twinid="room1",
                api_version="2023-02-27-preview"
            )

            mock_send.assert_called_once()
            call_args = mock_send.call_args
            assert call_args[0][0] == "DELETE"


class TestGetComponentAsync:
    """Tests for get_component_async method."""

    @pytest.mark.asyncio
    async def test_success_with_json_response(self, mock_token_provider):
        """Test successful component retrieval with JSON response."""
        client = AzuredigitaltwinsClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(
            status=200,
            text='{"temperature": 72.5, "humidity": 45}'
        )

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ) as mock_send:
            result = await client.get_component_async(
                twinid="room1",
                component_path="thermostat",
                api_version="2023-02-27-preview"
            )

            mock_send.assert_called_once()
            assert "/components/" in mock_send.call_args[0][1]
            assert result["temperature"] == 72.5


class TestGetRelationshipByIdAsync:
    """Tests for get_relationship_by_id_async method."""

    @pytest.mark.asyncio
    async def test_success_with_json_response(self, mock_token_provider):
        """Test successful relationship retrieval with JSON response."""
        client = AzuredigitaltwinsClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(
            status=200,
            text='{"$sourceId": "room1", "$targetId": "floor1", '
                 '"$relationshipId": "rel1"}'
        )

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ) as mock_send:
            result = await client.get_relationship_by_id_async(
                twinid="room1",
                relationship_id="rel1",
                api_version="2023-02-27-preview"
            )

            mock_send.assert_called_once()
            assert result["$relationshipId"] == "rel1"


class TestAddRelationshipAsync:
    """Tests for add_relationship_async method."""

    @pytest.mark.asyncio
    async def test_success_with_json_response(self, mock_token_provider):
        """Test successful relationship creation with JSON response."""
        client = AzuredigitaltwinsClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(
            status=200,
            text='{"$relationshipId": "rel1"}'
        )

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ) as mock_send:
            input_data = AddRelationshipInput(value='{"$targetId": "floor1"}')
            result = await client.add_relationship_async(
                input=input_data,
                twinid="room1",
                relationship_id="rel1",
                api_version="2023-02-27-preview"
            )

            mock_send.assert_called_once()
            call_args = mock_send.call_args
            assert call_args[0][0] == "PUT"
            assert result["$relationshipId"] == "rel1"


class TestDeleteRelationshipAsync:
    """Tests for delete_relationship_async method."""

    @pytest.mark.asyncio
    async def test_success(self, mock_token_provider):
        """Test successful relationship deletion."""
        client = AzuredigitaltwinsClient(
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
            await client.delete_relationship_async(
                twinid="room1",
                relationship_id="rel1",
                api_version="2023-02-27-preview"
            )

            mock_send.assert_called_once()
            call_args = mock_send.call_args
            assert call_args[0][0] == "DELETE"


class TestListRelationshipsAsync:
    """Tests for list_relationships_async method."""

    @pytest.mark.asyncio
    async def test_success_with_json_response(self, mock_token_provider):
        """Test successful relationships list with JSON response."""
        client = AzuredigitaltwinsClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(
            status=200,
            text='{"value": [{"$relationshipId": "rel1"}]}'
        )

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ) as mock_send:
            result = await client.list_relationships_async(
                twinid="room1",
                api_version="2023-02-27-preview"
            )

            mock_send.assert_called_once()
            assert len(result["value"]) == 1


class TestListIncomingRelationshipsAsync:
    """Tests for list_incoming_relationships_async method."""

    @pytest.mark.asyncio
    async def test_success_with_json_response(self, mock_token_provider):
        """Test successful incoming relationships list with JSON response."""
        client = AzuredigitaltwinsClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(
            status=200,
            text='{"value": [{"$sourceId": "floor1", "$relationshipId": "rel1"}]}'
        )

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ) as mock_send:
            result = await client.list_incoming_relationships_async(
                twinid="room1",
                api_version="2023-02-27-preview"
            )

            mock_send.assert_called_once()
            assert "/incomingrelationships" in mock_send.call_args[0][1]
            assert len(result["value"]) == 1


class TestQueryTwinsAsync:
    """Tests for query_twins_async method."""

    @pytest.mark.asyncio
    async def test_success_with_json_response(self, mock_token_provider):
        """Test successful query execution with JSON response."""
        client = AzuredigitaltwinsClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(
            status=200,
            text='{"value": "[{\\"$dtId\\": \\"room1\\"}]"}'
        )

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ) as mock_send:
            query_input = QueryTwinsInput(
                query="SELECT * FROM digitaltwins WHERE $dtId = 'room1'"
            )
            result = await client.query_twins_async(
                input=query_input,
                api_version="2023-02-27-preview"
            )

            mock_send.assert_called_once()
            call_args = mock_send.call_args
            assert call_args[0][0] == "POST"
            assert "/query" in call_args[0][1]
            assert result is not None

    @pytest.mark.asyncio
    async def test_error_response_raises_exception(self, mock_token_provider):
        """Test that non-2xx response raises ConnectorException."""
        client = AzuredigitaltwinsClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(status=400, text='{"error": "Invalid query"}')

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ):
            query_input = QueryTwinsInput(query="INVALID")

            with pytest.raises(ConnectorException) as exc_info:
                await client.query_twins_async(
                    input=query_input,
                    api_version="2023-02-27-preview"
                )

            assert exc_info.value.status_code == 400


class TestSendTelemetryAsync:
    """Tests for send_telemetry_async method."""

    @pytest.mark.asyncio
    async def test_success(self, mock_token_provider):
        """Test successful telemetry send."""
        client = AzuredigitaltwinsClient(
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
            telemetry = SendTelemetryInput(value='{"temperature": 72}')
            await client.send_telemetry_async(
                input=telemetry,
                twinid="room1",
                api_version="2023-02-27-preview"
            )

            mock_send.assert_called_once()
            assert "/telemetry" in mock_send.call_args[0][1]


class TestSendComponentTelemetryAsync:
    """Tests for send_component_telemetry_async method."""

    @pytest.mark.asyncio
    async def test_success(self, mock_token_provider):
        """Test successful component telemetry send."""
        client = AzuredigitaltwinsClient(
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
            telemetry = SendComponentTelemetryInput(value='{"temperature": 72}')
            await client.send_component_telemetry_async(
                input=telemetry,
                twinid="room1",
                component_path="thermostat",
                api_version="2023-02-27-preview"
            )

            mock_send.assert_called_once()
            assert "/components/" in mock_send.call_args[0][1]
            assert "/telemetry" in mock_send.call_args[0][1]


class TestDataClasses:
    """Tests for data class creation and attributes."""

    def test_list_models_response(self):
        """Test ListModelsResponse dataclass creation."""
        response = ListModelsResponse(
            value=[{"id": "dtmi:example:Room;1"}],
            continuation_token="token123",
            next_link="https://example.com/next"
        )

        assert len(response.value) == 1
        assert response.continuation_token == "token123"

    def test_get_model_by_id_response(self):
        """Test GetModelByIdResponse dataclass creation."""
        response = GetModelByIdResponse(
            id="dtmi:example:Room;1",
            upload_time="2024-01-15T10:00:00Z",
            decommissioned=False,
            model={"@type": "Interface"}
        )

        assert response.id == "dtmi:example:Room;1"
        assert response.decommissioned is False

    def test_twin_result(self):
        """Test TwinResult dataclass creation."""
        result = TwinResult(result='{"$dtId": "room1"}')

        assert result.result is not None

    def test_get_component_result(self):
        """Test GetComponentResult dataclass creation."""
        result = GetComponentResult(result='{"temperature": 72}')

        assert result.result is not None

    def test_twin_relationship(self):
        """Test TwinRelationship dataclass creation."""
        relationship = TwinRelationship(
            source_id="room1",
            relationship_id="rel1",
            target_id="floor1",
            relationship_name="isPartOf",
            etag="abc123"
        )

        assert relationship.source_id == "room1"
        assert relationship.target_id == "floor1"

    def test_incoming_relationship(self):
        """Test IncomingRelationship dataclass creation."""
        relationship = IncomingRelationship(
            source_id="floor1",
            relationship_id="rel1",
            relationship_name="contains",
            relationship_link="https://example.com/rel"
        )

        assert relationship.source_id == "floor1"
        assert relationship.relationship_name == "contains"

    def test_list_relationships_response(self):
        """Test ListRelationshipsResponse dataclass creation."""
        rel = TwinRelationship(source_id="room1", target_id="floor1")
        response = ListRelationshipsResponse(
            value=[rel],
            continuation_token="token123"
        )

        assert len(response.value) == 1

    def test_list_incoming_relationships_response(self):
        """Test ListIncomingRelationshipsResponse dataclass creation."""
        rel = IncomingRelationship(source_id="floor1")
        response = ListIncomingRelationshipsResponse(
            value=[rel],
            continuation_token="token123"
        )

        assert len(response.value) == 1

    def test_send_telemetry_input(self):
        """Test SendTelemetryInput dataclass creation."""
        telemetry = SendTelemetryInput(value='{"temperature": 72}')

        assert telemetry.value is not None

    def test_send_component_telemetry_input(self):
        """Test SendComponentTelemetryInput dataclass creation."""
        telemetry = SendComponentTelemetryInput(value='{"temperature": 72}')

        assert telemetry.value is not None

    def test_query_twins_input(self):
        """Test QueryTwinsInput dataclass creation."""
        query = QueryTwinsInput(
            query="SELECT * FROM digitaltwins",
            continuation_token="token123"
        )

        assert query.query is not None

    def test_query_result(self):
        """Test QueryResult dataclass creation."""
        result = QueryResult(
            value='[{"$dtId": "room1"}]',
            continuation_token="token123"
        )

        assert result.value is not None


class TestEdgeCases:
    """Tests for edge cases and special scenarios."""

    @pytest.mark.asyncio
    async def test_http_client_property_access(self, mock_token_provider):
        """Test accessing http_client property."""
        client = AzuredigitaltwinsClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        assert client.http_client is not None
        assert client._http_client is client.http_client

    def test_dataclass_defaults(self):
        """Test dataclass default values."""
        response = ListModelsResponse()
        assert response.value is None
        assert response.continuation_token is None

        relationship = TwinRelationship()
        assert relationship.source_id is None
        assert relationship.target_id is None

    def test_multiple_client_instances(self, mock_token_provider):
        """Test creating multiple client instances."""
        client1 = AzuredigitaltwinsClient(
            "https://example1.azure.com/connections/test",
            token_provider=mock_token_provider
        )
        client2 = AzuredigitaltwinsClient(
            "https://example2.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        assert client1._connection_runtime_url != client2._connection_runtime_url
        assert client1.connector_name == client2.connector_name
