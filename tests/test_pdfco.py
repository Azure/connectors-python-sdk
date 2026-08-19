# Copyright (c) Microsoft Corporation. All rights reserved.

"""Unit tests for PdfcoClient."""

from unittest.mock import AsyncMock, patch

import pytest

from azure.connectors.pdfco import (
    PdfcoClient,
    HtmlToPdfInput,
    UrlToPdfInput,
    PdfFillerInput,
)
from azure.connectors.sdk import (
    ConnectorClientOptions,
    ConnectorException,
    ManagedIdentityTokenProvider,
)
from tests.conftest import MockResponse


class TestPdfcoClientInitialization:
    """Tests for PdfcoClient initialization."""

    def test_init_with_valid_url_and_defaults(self):
        """Test initialization with valid URL and default parameters."""
        client = PdfcoClient("https://example.azure.com/connections/test")

        assert client._connection_runtime_url == "https://example.azure.com/connections/test"
        assert client.connector_name == "pdfco"
        assert isinstance(client._http_client._token_provider, ManagedIdentityTokenProvider)

    def test_init_with_trailing_slash(self):
        """Test that trailing slash is removed from URL."""
        client = PdfcoClient("https://example.azure.com/connections/test/")

        assert client._connection_runtime_url == "https://example.azure.com/connections/test"

    def test_init_with_custom_token_provider(self, mock_token_provider):
        """Test initialization with custom token provider."""
        client = PdfcoClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider,
        )

        assert client._http_client._token_provider is mock_token_provider

    def test_init_with_custom_options(self, mock_token_provider):
        """Test initialization with custom options."""
        options = ConnectorClientOptions(timeout_seconds=60.0, max_retry_attempts=5)
        client = PdfcoClient(
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
            PdfcoClient("")

    def test_init_with_none_url_raises_error(self):
        """Test that None URL raises ValueError."""
        with pytest.raises(ValueError, match="connection_runtime_url cannot be None or empty"):
            PdfcoClient(None)

    def test_connector_name_property(self, mock_token_provider):
        """Test connector_name property returns 'pdfco'."""
        client = PdfcoClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider,
        )

        assert client.connector_name == "pdfco"


class TestPdfcoClientLifecycle:
    """Tests for PdfcoClient lifecycle methods."""

    @pytest.mark.asyncio
    async def test_close(self, mock_token_provider):
        """Test close method calls http_client.close."""
        client = PdfcoClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider,
        )

        with patch.object(client._http_client, "close", new_callable=AsyncMock) as mock_close:
            await client.close()
            mock_close.assert_called_once()

    @pytest.mark.asyncio
    async def test_context_manager(self, mock_token_provider):
        """Test async context manager functionality."""
        with patch.object(PdfcoClient, "close", new_callable=AsyncMock) as mock_close:
            async with PdfcoClient(
                "https://example.azure.com/connections/test",
                token_provider=mock_token_provider,
            ) as client:
                assert isinstance(client, PdfcoClient)

            mock_close.assert_called_once()


class TestHtmlToPdfAsync:
    """Tests for html_to_pdf_async method (POST with body)."""

    @pytest.mark.asyncio
    async def test_success_forwards_request_body(self, mock_token_provider):
        """Test that the POST operation forwards the request body to send_async."""
        client = PdfcoClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider,
        )
        request = HtmlToPdfInput()
        mock_response = MockResponse(status=200, text='{"url": "https://example.com/out.pdf"}')

        with patch.object(
            client._http_client,
            "send_async",
            new_callable=AsyncMock,
            return_value=mock_response,
        ) as mock_send:
            result = await client.html_to_pdf_async(input=request)

            mock_send.assert_called_once()
            method, path = mock_send.call_args[0][0], mock_send.call_args[0][1]
            assert method == "POST"
            assert path.endswith("/v1/pdf/convert/from/html")
            assert mock_send.call_args.kwargs["body"] is request
            assert result is not None
            assert "url" in result

    @pytest.mark.asyncio
    async def test_error_response_raises_connector_exception(self, mock_token_provider):
        """Test that a non-2xx response raises ConnectorException."""
        client = PdfcoClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider,
        )
        mock_response = MockResponse(status=400, text="Bad Request")

        with patch.object(
            client._http_client,
            "send_async",
            new_callable=AsyncMock,
            return_value=mock_response,
        ):
            with pytest.raises(ConnectorException) as exc_info:
                await client.html_to_pdf_async(input=HtmlToPdfInput())

            assert exc_info.value.status_code == 400


class TestUrlToPdfAsync:
    """Tests for url_to_pdf_async method (POST with body)."""

    @pytest.mark.asyncio
    async def test_success_forwards_request_body(self, mock_token_provider):
        """Test that the POST operation forwards the request body to send_async."""
        client = PdfcoClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider,
        )
        request = UrlToPdfInput()
        mock_response = MockResponse(status=200, text='{"url": "https://example.com/out.pdf"}')

        with patch.object(
            client._http_client,
            "send_async",
            new_callable=AsyncMock,
            return_value=mock_response,
        ) as mock_send:
            result = await client.url_to_pdf_async(input=request)

            mock_send.assert_called_once()
            method, path = mock_send.call_args[0][0], mock_send.call_args[0][1]
            assert method == "POST"
            assert path.endswith("/v1/pdf/convert/from/url")
            assert mock_send.call_args.kwargs["body"] is request
            assert result is not None

    @pytest.mark.asyncio
    async def test_server_error_raises_connector_exception(self, mock_token_provider):
        """Test that a 5xx response raises ConnectorException."""
        client = PdfcoClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider,
        )
        mock_response = MockResponse(status=500, text="Internal Server Error")

        with patch.object(
            client._http_client,
            "send_async",
            new_callable=AsyncMock,
            return_value=mock_response,
        ):
            with pytest.raises(ConnectorException):
                await client.url_to_pdf_async(input=UrlToPdfInput())


class TestPdfFillerAsync:
    """Tests for pdf_filler_async method (POST with body)."""

    @pytest.mark.asyncio
    async def test_success_forwards_request_body(self, mock_token_provider):
        """Test that the POST operation forwards the request body to send_async."""
        client = PdfcoClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider,
        )
        request = PdfFillerInput()
        mock_response = MockResponse(status=200, text='{"url": "https://example.com/filled.pdf"}')

        with patch.object(
            client._http_client,
            "send_async",
            new_callable=AsyncMock,
            return_value=mock_response,
        ) as mock_send:
            result = await client.pdf_filler_async(input=request)

            mock_send.assert_called_once()
            method, path = mock_send.call_args[0][0], mock_send.call_args[0][1]
            assert method == "POST"
            assert path.endswith("/v1/pdf/edit/add")
            assert mock_send.call_args.kwargs["body"] is request
            assert result is not None

    @pytest.mark.asyncio
    async def test_empty_response_returns_none(self, mock_token_provider):
        """Test that an empty 2xx response body returns None."""
        client = PdfcoClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider,
        )
        mock_response = MockResponse(status=200, text="")

        with patch.object(
            client._http_client,
            "send_async",
            new_callable=AsyncMock,
            return_value=mock_response,
        ):
            result = await client.pdf_filler_async(input=PdfFillerInput())

            assert result is None

    @pytest.mark.asyncio
    async def test_error_response_raises_connector_exception(self, mock_token_provider):
        """Test that a non-2xx response raises ConnectorException."""
        client = PdfcoClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider,
        )
        mock_response = MockResponse(status=422, text="Unprocessable Entity")

        with patch.object(
            client._http_client,
            "send_async",
            new_callable=AsyncMock,
            return_value=mock_response,
        ):
            with pytest.raises(ConnectorException):
                await client.pdf_filler_async(input=PdfFillerInput())


BASE_URL = "https://example.azure.com/connections/test"

OPERATION_ARGS = {
    "barcode_generator": {"input": {}},
    "barcode_reader": {"input": {}},
    "document_parser": {"input": {}},
    "email_attachment_extraction": {"input": {}},
    "email_decode": {"input": {}},
    "email_send": {"input": {}},
    "html_to_pdf": {"input": {}},
    "job_check": {"input": {}},
    "merge_pdf": {"input": {}},
    "merge_pdf_simplified": {"input": {}},
    "pdf_add_security": {"input": {}},
    "pdf_attachment_extraction": {"input": {}},
    "pdf_auto_rotate_pages": {"input": {}},
    "pdf_classifier": {"input": {}},
    "pdf_compress": {"input": {}},
    "pdf_delete_pages": {"input": {}},
    "pdf_find_table": {"input": {}},
    "pdf_forms_info_reader": {"input": {}},
    "pdf_from_csv": {"input": {}},
    "pdf_from_doc": {"input": {}},
    "pdf_from_email": {"input": {}},
    "pdf_from_images": {"input": {}},
    "pdf_from_xls_xlsx": {"input": {}},
    "pdf_info_reader": {"input": {}},
    "pdf_rotate_pages": {"input": {}},
    "pdf_searchable": {"input": {}},
    "pdf_security_remove": {"input": {}},
    "pdf_search_text": {"input": {}},
    "pdf_to_csv": {"input": {}},
    "pdf_to_jpg": {"input": {}},
    "pdf_to_json": {"input": {}},
    "pdf_to_json_meta": {"input": {}},
    "pdf_to_png": {"input": {}},
    "pdf_to_tiff": {"input": {}},
    "pdf_to_text": {"input": {}},
    "pdf_to_text_simple": {"input": {}},
    "pdf_to_webp": {"input": {}},
    "pdf_to_xls": {"input": {}},
    "pdf_to_xlsx": {"input": {}},
    "pdf_to_xml": {"input": {}},
    "pdf_unsearchable": {"input": {}},
    "pdf_filler": {"input": {}},
    "search_and_delete_text": {"input": {}},
    "search_and_replace": {"input": {}},
    "search_and_replace_with_image": {"input": {}},
    "split_pdf2": {"input": {}},
    "split_pdf": {"input": {}},
    "url_to_pdf": {"input": {}},
    "xls_to_csv": {"input": {}},
    "xls_to_html": {"input": {}},
    "xls_to_json": {"input": {}},
    "xls_to_txt": {"input": {}},
    "xls_to_xml": {"input": {}},
}

ALL_OPERATIONS = sorted(OPERATION_ARGS.keys())


async def _invoke_operation(client: PdfcoClient, operation: str):
    """Invoke a PDF.co operation by name for shared method tests."""
    method = getattr(client, f"{operation}_async")
    return await method(**OPERATION_ARGS[operation])


class TestPdfcoClientAllOperations:
    """Success path smoke tests covering every generated operation."""

    def test_malformed_operation_names_are_not_generated(self):
        """Test known malformed Swagger operation names are not public methods."""
        malformed_method_names = [
            "pdf_from_xlsxlsx_async",
            "pdf_serarch_text_async",
            "pdf_un_searchable_async",
            "xl_sto_csv_async",
            "xl_sto_html_async",
            "xl_sto_json_async",
            "xl_sto_txt_async",
            "xl_sto_xml_async",
        ]

        for method_name in malformed_method_names:
            assert not hasattr(PdfcoClient, method_name)

    @pytest.mark.asyncio
    @pytest.mark.parametrize("operation", ALL_OPERATIONS)
    async def test_all_operations_success(self, mock_token_provider, operation):
        """Test every operation issues a request and returns without error."""
        client = PdfcoClient(BASE_URL, token_provider=mock_token_provider)
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


class TestPdfcoClientAllOperationsErrorHandling:
    """Error handling tests that ensure every operation raises ConnectorException."""

    @pytest.mark.asyncio
    @pytest.mark.parametrize("operation", ALL_OPERATIONS)
    async def test_error_response_raises_exception_for_all_operations(
        self,
        mock_token_provider,
        operation,
    ):
        """Test non-2xx responses raise ConnectorException for every operation."""
        client = PdfcoClient(BASE_URL, token_provider=mock_token_provider)
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
