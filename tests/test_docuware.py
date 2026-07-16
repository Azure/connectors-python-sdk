# Copyright (c) Microsoft Corporation. All rights reserved.

"""Unit tests for DocuwareClient."""

from unittest.mock import AsyncMock, patch

import pytest

from azure.connectors.docuware import (
    DocuwareClient,
    SearchForDocumentsInFileCabinetInput,
)
from azure.connectors.sdk import (
    ConnectorClientOptions,
    ConnectorException,
    ManagedIdentityTokenProvider,
)
from tests.conftest import MockResponse


class TestDocuwareClientInitialization:
    """Tests for DocuwareClient initialization."""

    def test_init_with_valid_url_and_defaults(self):
        """Test initialization with valid URL and default parameters."""
        client = DocuwareClient("https://example.azure.com/connections/test")

        assert client._connection_runtime_url == "https://example.azure.com/connections/test"
        assert client.connector_name == "docuware"
        assert isinstance(client._http_client._token_provider, ManagedIdentityTokenProvider)

    def test_init_with_trailing_slash(self):
        """Test that trailing slash is removed from URL."""
        client = DocuwareClient("https://example.azure.com/connections/test/")

        assert client._connection_runtime_url == "https://example.azure.com/connections/test"

    def test_init_with_custom_token_provider(self, mock_token_provider):
        """Test initialization with custom token provider."""
        client = DocuwareClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider,
        )

        assert client._http_client._token_provider is mock_token_provider

    def test_init_with_custom_options(self, mock_token_provider):
        """Test initialization with custom options."""
        options = ConnectorClientOptions(timeout_seconds=60.0, max_retry_attempts=5)
        client = DocuwareClient(
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
            DocuwareClient("")

    def test_init_with_none_url_raises_error(self):
        """Test that None URL raises ValueError."""
        with pytest.raises(ValueError, match="connection_runtime_url cannot be None or empty"):
            DocuwareClient(None)

    def test_connector_name_property(self, mock_token_provider):
        """Test connector_name property returns 'docuware'."""
        client = DocuwareClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider,
        )

        assert client.connector_name == "docuware"


class TestDocuwareClientLifecycle:
    """Tests for DocuwareClient lifecycle methods."""

    @pytest.mark.asyncio
    async def test_close(self, mock_token_provider):
        """Test close method calls http_client.close."""
        client = DocuwareClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider,
        )

        with patch.object(client._http_client, "close", new_callable=AsyncMock) as mock_close:
            await client.close()
            mock_close.assert_called_once()

    @pytest.mark.asyncio
    async def test_context_manager(self, mock_token_provider):
        """Test async context manager functionality."""
        with patch.object(DocuwareClient, "close", new_callable=AsyncMock) as mock_close:
            async with DocuwareClient(
                "https://example.azure.com/connections/test",
                token_provider=mock_token_provider,
            ) as client:
                assert isinstance(client, DocuwareClient)

            mock_close.assert_called_once()


class TestGetOrganizationAsync:
    """Tests for get_organization_async method (GET, no body)."""

    @pytest.mark.asyncio
    async def test_success_sends_get(self, mock_token_provider):
        """Test that the operation issues a GET and returns parsed JSON."""
        client = DocuwareClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider,
        )
        mock_response = MockResponse(status=200, text='{"Name": "Contoso"}')

        with patch.object(
            client._http_client,
            "send_async",
            new_callable=AsyncMock,
            return_value=mock_response,
        ) as mock_send:
            result = await client.get_organization_async()

            mock_send.assert_called_once()
            method, path = mock_send.call_args[0][0], mock_send.call_args[0][1]
            assert method == "GET"
            assert path.endswith("/Organization")
            assert mock_send.call_args.kwargs["body"] is None
            assert result is not None
            assert result["Name"] == "Contoso"

    @pytest.mark.asyncio
    async def test_error_response_raises_connector_exception(self, mock_token_provider):
        """Test that a non-2xx response raises ConnectorException."""
        client = DocuwareClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider,
        )
        mock_response = MockResponse(status=401, text="Unauthorized")

        with patch.object(
            client._http_client,
            "send_async",
            new_callable=AsyncMock,
            return_value=mock_response,
        ):
            with pytest.raises(ConnectorException) as exc_info:
                await client.get_organization_async()

            assert exc_info.value.status_code == 401


class TestGetFileCabinetsAsync:
    """Tests for get_file_cabinets_async method (GET with query parameter)."""

    @pytest.mark.asyncio
    async def test_success_appends_query_parameter(self, mock_token_provider):
        """Test that the query parameter is appended to the request URL."""
        client = DocuwareClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider,
        )
        mock_response = MockResponse(status=200, text='{"FileCabinets": []}')

        with patch.object(
            client._http_client,
            "send_async",
            new_callable=AsyncMock,
            return_value=mock_response,
        ) as mock_send:
            result = await client.get_file_cabinets_async(file_cabinet_type="FileCabinet")

            mock_send.assert_called_once()
            method, path = mock_send.call_args[0][0], mock_send.call_args[0][1]
            assert method == "GET"
            assert "/FileCabinets" in path
            assert "FileCabinetType=FileCabinet" in path
            assert result is not None


class TestSearchForDocumentsInFileCabinetAsync:
    """Tests for search_for_documents_in_file_cabinet_async (POST with body)."""

    @pytest.mark.asyncio
    async def test_success_forwards_request_body(self, mock_token_provider):
        """Test that the POST operation forwards the request body to send_async."""
        client = DocuwareClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider,
        )
        request = SearchForDocumentsInFileCabinetInput()
        mock_response = MockResponse(status=200, text='{"Count": 1, "Documents": []}')

        with patch.object(
            client._http_client,
            "send_async",
            new_callable=AsyncMock,
            return_value=mock_response,
        ) as mock_send:
            result = await client.search_for_documents_in_file_cabinet_async(
                input=request,
                file_cabinet="cabinet-1",
                search_dialog_id="dialog-1",
            )

            mock_send.assert_called_once()
            method, path = mock_send.call_args[0][0], mock_send.call_args[0][1]
            assert method == "POST"
            assert "/FileCabinets/cabinet-1/Search" in path
            assert "SearchDialogId=dialog-1" in path
            assert mock_send.call_args.kwargs["body"] is request
            assert result is not None
            assert result["Count"] == 1

    @pytest.mark.asyncio
    async def test_error_response_raises_connector_exception(self, mock_token_provider):
        """Test that a non-2xx response raises ConnectorException."""
        client = DocuwareClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider,
        )
        request = SearchForDocumentsInFileCabinetInput()
        mock_response = MockResponse(status=400, text="Bad Request")

        with patch.object(
            client._http_client,
            "send_async",
            new_callable=AsyncMock,
            return_value=mock_response,
        ):
            with pytest.raises(ConnectorException) as exc_info:
                await client.search_for_documents_in_file_cabinet_async(
                    input=request,
                    file_cabinet="cabinet-1",
                    search_dialog_id="dialog-1",
                )

            assert exc_info.value.status_code == 400


class TestDeleteDocumentAsync:
    """Tests for delete_document_async method (DELETE, no return value)."""

    @pytest.mark.asyncio
    async def test_success_sends_delete(self, mock_token_provider):
        """Test that the operation issues a DELETE and returns None."""
        client = DocuwareClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider,
        )
        mock_response = MockResponse(status=204, text="")

        with patch.object(
            client._http_client,
            "send_async",
            new_callable=AsyncMock,
            return_value=mock_response,
        ) as mock_send:
            result = await client.delete_document_async(
                file_cabinet_id="cabinet-1",
                document_id="doc-1",
            )

            mock_send.assert_called_once()
            method, path = mock_send.call_args[0][0], mock_send.call_args[0][1]
            assert method == "DELETE"
            assert path.endswith("/FileCabinets/cabinet-1/Documents/doc-1")
            assert result is None

    @pytest.mark.asyncio
    async def test_error_response_raises_connector_exception(self, mock_token_provider):
        """Test that a non-2xx response raises ConnectorException."""
        client = DocuwareClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider,
        )
        mock_response = MockResponse(status=404, text="Not Found")

        with patch.object(
            client._http_client,
            "send_async",
            new_callable=AsyncMock,
            return_value=mock_response,
        ):
            with pytest.raises(ConnectorException) as exc_info:
                await client.delete_document_async(
                    file_cabinet_id="cabinet-1",
                    document_id="doc-1",
                )

            assert exc_info.value.status_code == 404


class TestDownloadFileAsync:
    """Tests for download_file_async method (GET, returns raw content bytes)."""

    @pytest.mark.asyncio
    async def test_success_returns_content_bytes(self, mock_token_provider):
        """Test that the operation returns the raw response content."""
        client = DocuwareClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider,
        )
        mock_response = MockResponse(status=200, content=b"file-bytes")

        with patch.object(
            client._http_client,
            "send_async",
            new_callable=AsyncMock,
            return_value=mock_response,
        ) as mock_send:
            result = await client.download_file_async(
                file_cabinet_id="cabinet-1",
                document_id="doc-1",
                file_number="1",
                document_format="pdf",
            )

            mock_send.assert_called_once()
            method, path = mock_send.call_args[0][0], mock_send.call_args[0][1]
            assert method == "GET"
            assert (
                "/FileCabinets/cabinet-1/Documents/doc-1/Sections/1/Download" in path
            )
            assert "DocumentFormat=pdf" in path
            assert result == b"file-bytes"


BASE_URL = "https://example.azure.com/connections/test"

OPERATION_ARGS = {
    "get_organization": {},
    "get_file_cabinets": {"file_cabinet_type": None},
    "get_document_information": {"file_cabinet_id": "cabinet-1", "document_id": "doc-1"},
    "delete_document": {"file_cabinet_id": "cabinet-1", "document_id": "doc-1"},
    "download_file": {
        "file_cabinet_id": "cabinet-1",
        "document_id": "doc-1",
        "file_number": "1",
        "document_format": None,
    },
    "download_document": {
        "file_cabinet_id": "cabinet-1",
        "document_id": "doc-1",
        "document_format": None,
    },
    "list_documents_in_document_tray": {"document_tray": "tray-1"},
    "search_for_documents_in_file_cabinet": {
        "input": {},
        "file_cabinet": "cabinet-1",
        "search_dialog_id": None,
    },
    "update_index_fields": {
        "input": {},
        "file_cabinet_id": "cabinet-1",
        "document_id": "doc-1",
    },
    "transfer_document": {"input": {}, "destination_file_cabinet_id": "cabinet-2"},
    "place_a_stamp": {"input": {}, "file_cabinet_id": "cabinet-1", "document_id": "doc-1"},
    "get_dialogs": {"file_cabinet": "cabinet-1"},
    "get_dialog_fields": {"file_cabinet": "cabinet-1", "dialog_id": "dialog-1"},
    "get_stamps": {"file_cabinet": "cabinet-1"},
    "get_stamp_fields": {"file_cabinet": "cabinet-1", "stamp": "stamp-1"},
    "get_file_cabinet_fields": {"file_cabinet": "cabinet-1"},
}

ALL_OPERATIONS = sorted(OPERATION_ARGS.keys())


async def _invoke_operation(client: DocuwareClient, operation: str):
    """Invoke a DocuWare operation by name for shared method tests."""
    method = getattr(client, f"{operation}_async")
    return await method(**OPERATION_ARGS[operation])


class TestDocuwareClientAllOperations:
    """Success path smoke tests covering every generated operation."""

    @pytest.mark.asyncio
    @pytest.mark.parametrize("operation", ALL_OPERATIONS)
    async def test_all_operations_success(self, mock_token_provider, operation):
        """Test every operation issues a request and returns without error."""
        client = DocuwareClient(BASE_URL, token_provider=mock_token_provider)
        mock_response = MockResponse(status=200, text="{}")

        with patch.object(
            client._http_client,
            "send_async",
            new_callable=AsyncMock,
            return_value=mock_response,
        ) as mock_send:
            await _invoke_operation(client, operation)

            assert mock_send.call_count == 1
            assert mock_send.call_args[0][1].startswith(BASE_URL)


class TestDocuwareClientAllOperationsErrorHandling:
    """Error handling tests that ensure every operation raises ConnectorException."""

    @pytest.mark.asyncio
    @pytest.mark.parametrize("operation", ALL_OPERATIONS)
    async def test_error_response_raises_exception_for_all_operations(
        self,
        mock_token_provider,
        operation,
    ):
        """Test non-2xx responses raise ConnectorException for every operation."""
        client = DocuwareClient(BASE_URL, token_provider=mock_token_provider)
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
