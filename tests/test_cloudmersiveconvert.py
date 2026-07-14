# Copyright (c) Microsoft Corporation. All rights reserved.

"""Unit tests for CloudmersiveconvertClient."""

from unittest.mock import AsyncMock, patch

import pytest

from azure.connectors.cloudmersiveconvert import (
    CloudmersiveconvertClient,
    GetDocxBodyRequest,
    GetDocxGetCommentsHierarchicalRequest,
)
from azure.connectors.sdk import (
    ConnectorClientOptions,
    ConnectorException,
    ManagedIdentityTokenProvider,
)
from tests.conftest import MockResponse


class TestCloudmersiveconvertClientInitialization:
    """Tests for CloudmersiveconvertClient initialization."""

    def test_init_with_valid_url_and_defaults(self):
        """Test initialization with valid URL and default parameters."""
        client = CloudmersiveconvertClient("https://example.azure.com/connections/test")

        assert client._connection_runtime_url == "https://example.azure.com/connections/test"
        assert client.connector_name == "cloudmersiveconvert"
        assert isinstance(client._http_client._token_provider, ManagedIdentityTokenProvider)

    def test_init_with_trailing_slash(self):
        """Test that trailing slash is removed from URL."""
        client = CloudmersiveconvertClient("https://example.azure.com/connections/test/")

        assert client._connection_runtime_url == "https://example.azure.com/connections/test"

    def test_init_with_custom_token_provider(self, mock_token_provider):
        """Test initialization with custom token provider."""
        client = CloudmersiveconvertClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider,
        )

        assert client._http_client._token_provider is mock_token_provider

    def test_init_with_custom_options(self, mock_token_provider):
        """Test initialization with custom options."""
        options = ConnectorClientOptions(timeout_seconds=60.0, max_retry_attempts=5)
        client = CloudmersiveconvertClient(
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
            CloudmersiveconvertClient("")

    def test_init_with_none_url_raises_error(self):
        """Test that None URL raises ValueError."""
        with pytest.raises(ValueError, match="connection_runtime_url cannot be None or empty"):
            CloudmersiveconvertClient(None)

    def test_connector_name_property(self, mock_token_provider):
        """Test connector_name property returns 'cloudmersiveconvert'."""
        client = CloudmersiveconvertClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider,
        )

        assert client.connector_name == "cloudmersiveconvert"


class TestCloudmersiveconvertClientLifecycle:
    """Tests for CloudmersiveconvertClient lifecycle methods."""

    @pytest.mark.asyncio
    async def test_close(self, mock_token_provider):
        """Test close method calls http_client.close."""
        client = CloudmersiveconvertClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider,
        )

        with patch.object(client._http_client, "close", new_callable=AsyncMock) as mock_close:
            await client.close()
            mock_close.assert_called_once()

    @pytest.mark.asyncio
    async def test_context_manager(self, mock_token_provider):
        """Test async context manager functionality."""
        with patch.object(CloudmersiveconvertClient, "close", new_callable=AsyncMock) as mock_close:
            async with CloudmersiveconvertClient(
                "https://example.azure.com/connections/test",
                token_provider=mock_token_provider,
            ) as client:
                assert isinstance(client, CloudmersiveconvertClient)

            mock_close.assert_called_once()


class TestEditDocumentDocxBodyAsync:
    """Tests for edit_document_docx_body_async method (POST with body)."""

    @pytest.mark.asyncio
    async def test_success_forwards_request_body(self, mock_token_provider):
        """Test that the POST operation forwards the request body to send_async."""
        client = CloudmersiveconvertClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider,
        )
        request = GetDocxBodyRequest()
        mock_response = MockResponse(status=200, text='{"successful": true}')

        with patch.object(
            client._http_client,
            "send_async",
            new_callable=AsyncMock,
            return_value=mock_response,
        ) as mock_send:
            result = await client.edit_document_docx_body_async(input=request)

            mock_send.assert_called_once()
            method, path = mock_send.call_args[0][0], mock_send.call_args[0][1]
            assert method == "POST"
            assert path.endswith("/convert/edit/docx/get-body")
            assert mock_send.call_args.kwargs["body"] is request
            assert result is not None
            assert result["successful"] is True

    @pytest.mark.asyncio
    async def test_error_response_raises_connector_exception(self, mock_token_provider):
        """Test that a non-2xx response raises ConnectorException."""
        client = CloudmersiveconvertClient(
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
                await client.edit_document_docx_body_async(input=GetDocxBodyRequest())

            assert exc_info.value.status_code == 400


class TestEditDocumentDocxGetCommentsHierarchicalAsync:
    """Tests for edit_document_docx_get_comments_hierarchical_async method."""

    @pytest.mark.asyncio
    async def test_success_forwards_request_body(self, mock_token_provider):
        """Test that the POST operation forwards the request body to send_async."""
        client = CloudmersiveconvertClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider,
        )
        request = GetDocxGetCommentsHierarchicalRequest()
        mock_response = MockResponse(status=200, text='{"Comments": []}')

        with patch.object(
            client._http_client,
            "send_async",
            new_callable=AsyncMock,
            return_value=mock_response,
        ) as mock_send:
            result = await client.edit_document_docx_get_comments_hierarchical_async(
                input=request
            )

            mock_send.assert_called_once()
            method, path = mock_send.call_args[0][0], mock_send.call_args[0][1]
            assert method == "POST"
            assert path.endswith("/convert/edit/docx/get-comments/hierarchical")
            assert mock_send.call_args.kwargs["body"] is request
            assert result is not None

    @pytest.mark.asyncio
    async def test_server_error_raises_connector_exception(self, mock_token_provider):
        """Test that a 5xx response raises ConnectorException."""
        client = CloudmersiveconvertClient(
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
                await client.edit_document_docx_get_comments_hierarchical_async(
                    input=GetDocxGetCommentsHierarchicalRequest()
                )


class TestConvertDocumentAutodetectGetInfoAsync:
    """Tests for convert_document_autodetect_get_info_async method (POST, no body)."""

    @pytest.mark.asyncio
    async def test_success_sends_post_with_no_body(self, mock_token_provider):
        """Test that the no-body POST operation sends body=None to send_async."""
        client = CloudmersiveconvertClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider,
        )
        mock_response = MockResponse(status=200, text='{"Successful": true}')

        with patch.object(
            client._http_client,
            "send_async",
            new_callable=AsyncMock,
            return_value=mock_response,
        ) as mock_send:
            result = await client.convert_document_autodetect_get_info_async()

            mock_send.assert_called_once()
            method, path = mock_send.call_args[0][0], mock_send.call_args[0][1]
            assert method == "POST"
            assert path.endswith("/convert/autodetect/get-info")
            assert mock_send.call_args.kwargs["body"] is None
            assert result is not None

    @pytest.mark.asyncio
    async def test_error_response_raises_connector_exception(self, mock_token_provider):
        """Test that a non-2xx response raises ConnectorException."""
        client = CloudmersiveconvertClient(
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
                await client.convert_document_autodetect_get_info_async()


BASE_URL = "https://example.azure.com/connections/test"

OPERATION_ARGS = {
    "compare_document_docx": {},
    "convert_data_csv_to_json": {},
    "convert_data_json_to_xml": {"input": {}},
    "convert_data_xls_to_json": {},
    "convert_data_xlsx_to_json": {},
    "convert_data_xml_edit_add_attribute_with_x_path": {},
    "convert_data_xml_edit_add_child_with_x_path": {},
    "convert_data_xml_edit_remove_all_child_nodes_with_x_path": {},
    "convert_data_xml_edit_replace_with_x_path": {},
    "convert_data_xml_edit_set_value_with_x_path": {},
    "convert_data_xml_filter_with_x_path": {},
    "convert_data_xml_query_with_x_query": {},
    "convert_data_xml_query_with_x_query_multi": {},
    "convert_data_xml_remove_with_x_path": {},
    "convert_data_xml_to_json": {},
    "convert_data_xml_transform_with_xslt_to_xml": {},
    "convert_document_autodetect_get_info": {},
    "convert_document_autodetect_to_pdf": {},
    "convert_document_autodetect_to_png_array": {},
    "convert_document_autodetect_to_txt": {},
    "convert_document_csv_to_xlsx": {},
    "convert_document_doc_to_docx": {},
    "convert_document_doc_to_pdf": {},
    "convert_document_doc_to_txt": {},
    "convert_document_docx_to_pdf": {},
    "convert_document_docx_to_txt": {},
    "convert_document_html_to_pdf": {},
    "convert_document_html_to_png": {},
    "convert_document_html_to_txt": {},
    "convert_document_pdf_to_docx": {},
    "convert_document_pdf_to_docx_rasterize": {},
    "convert_document_pdf_to_png_array": {},
    "convert_document_pdf_to_png_single": {},
    "convert_document_pdf_to_pptx": {},
    "convert_document_pdf_to_txt": {},
    "convert_document_png_array_to_pdf": {},
    "convert_document_ppt_to_pdf": {},
    "convert_document_ppt_to_pptx": {},
    "convert_document_pptx_to_pdf": {},
    "convert_document_pptx_to_txt": {},
    "convert_document_xls_to_csv": {},
    "convert_document_xls_to_pdf": {},
    "convert_document_xls_to_xlsx": {},
    "convert_document_xlsx_to_csv": {},
    "convert_document_xlsx_to_pdf": {},
    "convert_document_xlsx_to_txt": {},
    "convert_image_get_image_info": {},
    "convert_image_image_format_convert": {"format1": "test", "format2": "test"},
    "convert_image_image_set_d_p_i": {"dpi": "test"},
    "convert_image_multipage_image_format_convert": {"format1": "test", "format2": "test"},
    "convert_template_apply_html_template": {"input": {}},
    "convert_web_html_to_docx": {"input": {}},
    "convert_web_html_to_pdf": {"input": {}},
    "convert_web_html_to_png": {"input": {}},
    "convert_web_html_to_txt": {"input": {}},
    "convert_web_md_to_html": {},
    "convert_web_url_to_pdf": {"input": {}},
    "convert_web_url_to_screenshot": {"input": {}},
    "convert_web_url_to_txt": {"input": {}},
    "edit_document_begin_editing": {},
    "edit_document_docx_body": {"input": {}},
    "edit_document_docx_create_blank_document": {"input": {}},
    "edit_document_docx_delete_pages": {"input": {}},
    "edit_document_docx_delete_table_row": {"input": {}},
    "edit_document_docx_delete_table_row_range": {"input": {}},
    "edit_document_docx_get_comments_hierarchical": {"input": {}},
    "edit_document_docx_get_headers_and_footers": {"input": {}},
    "edit_document_docx_get_images": {"input": {}},
    "edit_document_docx_get_sections": {"input": {}},
    "edit_document_docx_get_styles": {"input": {}},
    "edit_document_docx_get_table_by_index": {"input": {}},
    "edit_document_docx_get_table_row": {"input": {}},
    "edit_document_docx_get_tables": {"input": {}},
    "edit_document_docx_insert_comment_on_paragraph": {"input": {}},
    "edit_document_docx_insert_image": {"input": {}},
    "edit_document_docx_insert_paragraph": {"input": {}},
    "edit_document_docx_insert_table": {"input": {}},
    "edit_document_docx_insert_table_row": {"input": {}},
    "edit_document_docx_pages": {"input": {}},
    "edit_document_docx_remove_headers_and_footers": {"input": {}},
    "edit_document_docx_remove_object": {"input": {}},
    "edit_document_docx_replace": {"input": {}},
    "edit_document_docx_set_footer_add_page_number": {"input": {}},
    "edit_document_docx_set_footer": {"input": {}},
    "edit_document_docx_set_header": {"input": {}},
    "edit_document_docx_update_table_cell": {"input": {}},
    "edit_document_docx_update_table_row": {"input": {}},
    "edit_document_finish_editing": {"input": {}},
    "edit_document_pptx_delete_slides": {"input": {}},
    "edit_document_pptx_replace": {"input": {}},
    "edit_document_xlsx_clear_cell_by_index": {"input": {}},
    "edit_document_xlsx_create_blank_spreadsheet": {"input": {}},
    "edit_document_xlsx_create_spreadsheet_from_data": {"input": {}},
    "edit_document_xlsx_delete_worksheet": {"input": {}},
    "edit_document_xlsx_get_cell_by_identifier": {"input": {}},
    "edit_document_xlsx_get_cell_by_index": {"input": {}},
    "edit_document_xlsx_get_columns": {"input": {}},
    "edit_document_xlsx_get_images": {"input": {}},
    "edit_document_xlsx_get_rows_and_cells": {"input": {}},
    "edit_document_xlsx_get_styles": {"input": {}},
    "edit_document_xlsx_get_worksheets": {"input": {}},
    "edit_document_xlsx_insert_worksheet": {"input": {}},
    "edit_document_xlsx_set_cell_by_identifier": {"input": {}},
    "edit_document_xlsx_set_cell_by_index": {"input": {}},
    "merge_document_docx": {},
    "merge_document_docx_multi": {},
    "merge_document_pdf": {},
    "merge_document_pdf_multi": {},
    "merge_document_png": {},
    "merge_document_pptx": {},
    "merge_document_pptx_multi": {},
    "merge_document_txt": {},
    "merge_document_txt_multi": {},
    "merge_document_xlsx": {},
    "merge_document_xlsx_multi": {},
    "split_document_docx": {},
    "split_document_pdf_by_page": {},
    "split_document_pptx": {},
    "split_document_txt_by_line": {},
    "split_document_txt_by_string": {},
    "split_document_xlsx": {},
    "validate_document_autodetect_validation": {},
    "validate_document_docx_validation": {},
    "validate_document_json_validation": {},
    "validate_document_pdf_validation": {},
    "validate_document_pptx_validation": {},
    "validate_document_xlsx_validation": {},
    "validate_document_xml_validation": {},
}

ALL_OPERATIONS = sorted(OPERATION_ARGS.keys())


async def _invoke_operation(client: CloudmersiveconvertClient, operation: str):
    """Invoke a Cloudmersive Convert operation by name for shared method tests."""
    method = getattr(client, f"{operation}_async")
    return await method(**OPERATION_ARGS[operation])


class TestCloudmersiveconvertClientAllOperations:
    """Success path smoke tests covering every generated operation."""

    @pytest.mark.asyncio
    @pytest.mark.parametrize("operation", ALL_OPERATIONS)
    async def test_all_operations_success(self, mock_token_provider, operation):
        """Test every operation issues a request and returns without error."""
        client = CloudmersiveconvertClient(BASE_URL, token_provider=mock_token_provider)
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


class TestCloudmersiveconvertClientAllOperationsErrorHandling:
    """Error handling tests that ensure every operation raises ConnectorException."""

    @pytest.mark.asyncio
    @pytest.mark.parametrize("operation", ALL_OPERATIONS)
    async def test_error_response_raises_exception_for_all_operations(
        self,
        mock_token_provider,
        operation,
    ):
        """Test non-2xx responses raise ConnectorException for every operation."""
        client = CloudmersiveconvertClient(BASE_URL, token_provider=mock_token_provider)
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
