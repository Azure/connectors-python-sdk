# Copyright (c) Microsoft Corporation. All rights reserved.

"""Unit tests for PlumsailClient."""

from unittest.mock import AsyncMock, patch

import pytest

from azure.connectors.plumsail import (
    PlumsailClient,
    Pdf2TextRequest,
    AddPowerAutomateWebhookData,
)
from azure.connectors.sdk import (
    ConnectorClientOptions,
    ConnectorException,
    ManagedIdentityTokenProvider,
)
from tests.conftest import MockResponse


class TestPlumsailClientInitialization:
    """Tests for PlumsailClient initialization."""

    def test_init_with_valid_url_and_defaults(self):
        """Test initialization with valid URL and default parameters."""
        client = PlumsailClient("https://example.azure.com/connections/test")

        assert client._connection_runtime_url == "https://example.azure.com/connections/test"
        assert client.connector_name == "plumsail"
        assert isinstance(client._http_client._token_provider, ManagedIdentityTokenProvider)

    def test_init_with_trailing_slash(self):
        """Test that trailing slash is removed from URL."""
        client = PlumsailClient("https://example.azure.com/connections/test/")

        assert client._connection_runtime_url == "https://example.azure.com/connections/test"

    def test_init_with_custom_token_provider(self, mock_token_provider):
        """Test initialization with custom token provider."""
        client = PlumsailClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider,
        )

        assert client._http_client._token_provider is mock_token_provider

    def test_init_with_custom_options(self, mock_token_provider):
        """Test initialization with custom options."""
        options = ConnectorClientOptions(timeout_seconds=60.0, max_retry_attempts=5)
        client = PlumsailClient(
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
            PlumsailClient("")

    def test_init_with_none_url_raises_error(self):
        """Test that None URL raises ValueError."""
        with pytest.raises(ValueError, match="connection_runtime_url cannot be None or empty"):
            PlumsailClient(None)

    def test_connector_name_property(self, mock_token_provider):
        """Test connector_name property returns 'plumsail'."""
        client = PlumsailClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider,
        )

        assert client.connector_name == "plumsail"


class TestPlumsailClientLifecycle:
    """Tests for PlumsailClient lifecycle methods."""

    @pytest.mark.asyncio
    async def test_close(self, mock_token_provider):
        """Test close method calls http_client.close."""
        client = PlumsailClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider,
        )

        with patch.object(client._http_client, "close", new_callable=AsyncMock) as mock_close:
            await client.close()
            mock_close.assert_called_once()

    @pytest.mark.asyncio
    async def test_context_manager(self, mock_token_provider):
        """Test async context manager functionality."""
        with patch.object(PlumsailClient, "close", new_callable=AsyncMock) as mock_close:
            async with PlumsailClient(
                "https://example.azure.com/connections/test",
                token_provider=mock_token_provider,
            ) as client:
                assert isinstance(client, PlumsailClient)

            mock_close.assert_called_once()


class TestProfilesMeGetAsync:
    """Tests for profiles_me_get_async method (GET, no body)."""

    @pytest.mark.asyncio
    async def test_success_sends_get(self, mock_token_provider):
        """Test that the operation issues a GET and returns parsed JSON."""
        client = PlumsailClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider,
        )
        mock_response = MockResponse(status=200, text='{"email": "user@example.com"}')

        with patch.object(
            client._http_client,
            "send_async",
            new_callable=AsyncMock,
            return_value=mock_response,
        ) as mock_send:
            result = await client.profiles_me_get_async()

            mock_send.assert_called_once()
            method, path = mock_send.call_args[0][0], mock_send.call_args[0][1]
            assert method == "GET"
            assert path.endswith("/profiles/me")
            assert mock_send.call_args.kwargs["body"] is None
            assert result is not None
            assert result["email"] == "user@example.com"

    @pytest.mark.asyncio
    async def test_error_response_raises_connector_exception(self, mock_token_provider):
        """Test that a non-2xx response raises ConnectorException."""
        client = PlumsailClient(
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
                await client.profiles_me_get_async()

            assert exc_info.value.status_code == 401


class TestExtractTextFromPdfAsync:
    """Tests for flow_v1_documents_jobs_extract_text_from_pdf_async (POST with body)."""

    @pytest.mark.asyncio
    async def test_success_forwards_request_body(self, mock_token_provider):
        """Test that the POST operation forwards the request body to send_async."""
        client = PlumsailClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider,
        )
        request = Pdf2TextRequest()
        mock_response = MockResponse(status=200, text='{"text": "hello"}')

        with patch.object(
            client._http_client,
            "send_async",
            new_callable=AsyncMock,
            return_value=mock_response,
        ) as mock_send:
            result = await client.flow_v1_documents_jobs_extract_text_from_pdf_async(input=request)

            mock_send.assert_called_once()
            method, path = mock_send.call_args[0][0], mock_send.call_args[0][1]
            assert method == "POST"
            assert path.endswith("/flow/v1/Documents/jobs/ExtractTextFromPdf")
            assert mock_send.call_args.kwargs["body"] is request
            assert result is not None
            assert result["text"] == "hello"

    @pytest.mark.asyncio
    async def test_error_response_raises_connector_exception(self, mock_token_provider):
        """Test that a non-2xx response raises ConnectorException."""
        client = PlumsailClient(
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
            with pytest.raises(ConnectorException):
                await client.flow_v1_documents_jobs_extract_text_from_pdf_async(
                    input=Pdf2TextRequest()
                )


class TestProcessesFlowTriggersAsync:
    """Tests for flow_v1_processes_flow_triggers_async (POST with body, no return)."""

    @pytest.mark.asyncio
    async def test_success_forwards_request_body(self, mock_token_provider):
        """Test that the POST operation forwards the request body to send_async."""
        client = PlumsailClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider,
        )
        request = AddPowerAutomateWebhookData()
        mock_response = MockResponse(status=200, text="")

        with patch.object(
            client._http_client,
            "send_async",
            new_callable=AsyncMock,
            return_value=mock_response,
        ) as mock_send:
            result = await client.flow_v1_processes_flow_triggers_async(input=request)

            mock_send.assert_called_once()
            method, path = mock_send.call_args[0][0], mock_send.call_args[0][1]
            assert method == "POST"
            assert path.endswith("/flow/v1/ProcessesFlow/triggers")
            assert mock_send.call_args.kwargs["body"] is request
            assert result is None

    @pytest.mark.asyncio
    async def test_error_response_raises_connector_exception(self, mock_token_provider):
        """Test that a non-2xx response raises ConnectorException."""
        client = PlumsailClient(
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
                await client.flow_v1_processes_flow_triggers_async(
                    input=AddPowerAutomateWebhookData()
                )


BASE_URL = "https://example.azure.com/connections/test"

OPERATION_ARGS = {
    "flow_v1_documents_flow_schema_add_watermark_to_pdf": {"type_": "test"},
    "flow_v1_documents_flow_schema_parse_csv": {"headers": "test"},
    "flow_v1_documents_flow_schema_reg_exp_match": {"pattern": "test"},
    "flow_v1_documents_flow_schema_split_pdf": {"type_": "test"},
    "flow_v1_documents_jobs_add_watermark_to_pdf": {"input": {}, "type_": "test"},
    "flow_v1_documents_jobs_any2_pdf_v2": {"input": {}},
    "flow_v1_documents_jobs_apply_docx": {"input": {}},
    "flow_v1_documents_jobs_apply_docx_template": {"input": {}},
    "flow_v1_documents_jobs_apply_html": {"input": {}},
    "flow_v1_documents_jobs_apply_pptx": {"input": {}},
    "flow_v1_documents_jobs_apply_xlsx_template": {"input": {}},
    "flow_v1_documents_jobs_compress_pdf": {"input": {}},
    "flow_v1_documents_jobs_create_archive": {"input": {}},
    "flow_v1_documents_jobs_csv2_xlsx": {"input": {}},
    "flow_v1_documents_jobs_doc2_docx": {"input": {}},
    "flow_v1_documents_jobs_docx2_pdf": {"input": {}},
    "flow_v1_documents_jobs_email2_pdf": {"input": {}},
    "flow_v1_documents_jobs_extract_archive": {"input": {}},
    "flow_v1_documents_jobs_extract_text_from_pdf": {"input": {}},
    "flow_v1_documents_jobs_fill_in_pdf_form": {"input": {}},
    "flow_v1_documents_jobs_get_pdf_form": {"input": {}},
    "flow_v1_documents_jobs_get_pdf_protection_info": {"input": {}},
    "flow_v1_documents_jobs_html2_docx": {"input": {}},
    "flow_v1_documents_jobs_html2_pdf": {"input": {}},
    "flow_v1_documents_jobs_image2_pdf": {"input": {}},
    "flow_v1_documents_jobs_json2_csv": {"input": {}},
    "flow_v1_documents_jobs_json2_xlsx": {"input": {}},
    "flow_v1_documents_jobs_merge_any_to_pdf_v2": {"input": {}},
    "flow_v1_documents_jobs_merge_docx": {"input": {}},
    "flow_v1_documents_jobs_merge_xlsx": {"input": {}},
    "flow_v1_documents_jobs_parse_csv": {"input": {}},
    "flow_v1_documents_jobs_pdf2_image_v2": {"input": {}},
    "flow_v1_documents_jobs_ppt2_pptx": {"input": {}},
    "flow_v1_documents_jobs_pptx2_pdf": {"input": {}},
    "flow_v1_documents_jobs_protect_pdf": {"input": {}},
    "flow_v1_documents_jobs_reg_exp_match": {"input": {}},
    "flow_v1_documents_jobs_reg_exp_replace": {"input": {}},
    "flow_v1_documents_jobs_reg_exp_test": {"input": {}},
    "flow_v1_documents_jobs_split_pdf_v2": {"input": {}, "type_": "test"},
    "flow_v1_documents_jobs_xls2_xlsx": {"input": {}},
    "flow_v1_documents_jobs_xslx2_pdf": {"input": {}},
    "flow_v1_processes_flow_jobs_execute_process": {"input": {}, "process_id": "test"},
    "flow_v1_processes_flow_jobs_execute_process_with_generated_data": {
        "input": {},
        "process_id": "test",
    },
    "flow_v1_processes_flow_schema_get_json_data": {"process_id": "test"},
    "flow_v1_processes_flow_schema_get_processes": {},
    "flow_v1_processes_flow_triggers": {"input": {}},
    "flow_v1_processes_flow_triggers_by_process_id_schema_get": {"process_id": "test"},
    "profiles_me_get": {},
}

ALL_OPERATIONS = sorted(OPERATION_ARGS.keys())


async def _invoke_operation(client: PlumsailClient, operation: str):
    """Invoke a Plumsail operation by name for shared method tests."""
    method = getattr(client, f"{operation}_async")
    return await method(**OPERATION_ARGS[operation])


class TestPlumsailClientAllOperations:
    """Success path smoke tests covering every generated operation."""

    @pytest.mark.asyncio
    @pytest.mark.parametrize("operation", ALL_OPERATIONS)
    async def test_all_operations_success(self, mock_token_provider, operation):
        """Test every operation issues a request and returns without error."""
        client = PlumsailClient(BASE_URL, token_provider=mock_token_provider)
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


class TestPlumsailClientAllOperationsErrorHandling:
    """Error handling tests that ensure every operation raises ConnectorException."""

    @pytest.mark.asyncio
    @pytest.mark.parametrize("operation", ALL_OPERATIONS)
    async def test_error_response_raises_exception_for_all_operations(
        self,
        mock_token_provider,
        operation,
    ):
        """Test non-2xx responses raise ConnectorException for every operation."""
        client = PlumsailClient(BASE_URL, token_provider=mock_token_provider)
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
