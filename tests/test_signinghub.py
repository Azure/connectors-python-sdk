# Copyright (c) Microsoft Corporation. All rights reserved.

"""Unit tests for SigninghubClient."""

from unittest.mock import AsyncMock, patch

import pytest

from azure.connectors.signinghub import (
    SigninghubClient,
    CheckBoxFieldRequest,
    UpdateCheckBoxFieldRequest,
)
from azure.connectors.sdk import (
    ConnectorClientOptions,
    ConnectorException,
    ManagedIdentityTokenProvider,
)
from tests.conftest import MockResponse


class TestSigninghubClientInitialization:
    """Tests for SigninghubClient initialization."""

    def test_init_with_valid_url_and_defaults(self):
        """Test initialization with valid URL and default parameters."""
        client = SigninghubClient("https://example.azure.com/connections/test")

        assert client._connection_runtime_url == "https://example.azure.com/connections/test"
        assert client.connector_name == "signinghub"
        assert isinstance(client._http_client._token_provider, ManagedIdentityTokenProvider)

    def test_init_with_trailing_slash(self):
        """Test that trailing slash is removed from URL."""
        client = SigninghubClient("https://example.azure.com/connections/test/")

        assert client._connection_runtime_url == "https://example.azure.com/connections/test"

    def test_init_with_custom_token_provider(self, mock_token_provider):
        """Test initialization with custom token provider."""
        client = SigninghubClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider,
        )

        assert client._http_client._token_provider is mock_token_provider

    def test_init_with_custom_options(self, mock_token_provider):
        """Test initialization with custom options."""
        options = ConnectorClientOptions(timeout_seconds=60.0, max_retry_attempts=5)
        client = SigninghubClient(
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
            SigninghubClient("")

    def test_init_with_none_url_raises_error(self):
        """Test that None URL raises ValueError."""
        with pytest.raises(ValueError, match="connection_runtime_url cannot be None or empty"):
            SigninghubClient(None)

    def test_connector_name_property(self, mock_token_provider):
        """Test connector_name property returns 'signinghub'."""
        client = SigninghubClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider,
        )

        assert client.connector_name == "signinghub"


class TestSigninghubClientLifecycle:
    """Tests for SigninghubClient lifecycle methods."""

    @pytest.mark.asyncio
    async def test_close(self, mock_token_provider):
        """Test close method calls http_client.close."""
        client = SigninghubClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider,
        )

        with patch.object(client._http_client, "close", new_callable=AsyncMock) as mock_close:
            await client.close()
            mock_close.assert_called_once()


class TestDocumentsUploadStreamAsync:
    """Tests for raw document upload transport."""

    @pytest.mark.asyncio
    async def test_forwards_exact_bytes_and_media_type(self, mock_token_provider):
        """Test document upload forwards bytes without transformation."""
        client = SigninghubClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider,
        )
        document = b"\x00\xffPDF\r\n"
        mock_response = MockResponse(status=201, text='{"documentId": "doc-1"}')

        with patch.object(
            client._http_client,
            "send_async",
            new_callable=AsyncMock,
            return_value=mock_response,
        ) as mock_send:
            await client.documents_upload_stream_async(
                input=document,
                package_id="package-1",
            )

            assert mock_send.call_args.kwargs["body"] is document
            assert mock_send.call_args.kwargs["content_type"] == "application/octet-stream"

    @pytest.mark.asyncio
    async def test_context_manager(self, mock_token_provider):
        """Test async context manager functionality."""
        with patch.object(SigninghubClient, "close", new_callable=AsyncMock) as mock_close:
            async with SigninghubClient(
                "https://example.azure.com/connections/test",
                token_provider=mock_token_provider,
            ) as client:
                assert isinstance(client, SigninghubClient)

            mock_close.assert_called_once()


class TestContactsGetAsync:
    """Tests for contacts_get_async method (GET with query parameters)."""

    @pytest.mark.asyncio
    async def test_success_serializes_path_and_query(self, mock_token_provider):
        """Test successful contacts retrieval serializes path and query params."""
        client = SigninghubClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider,
        )
        mock_response = MockResponse(status=200, text='{"value": [{"email": "a@b.com"}]}')

        with patch.object(
            client._http_client,
            "send_async",
            new_callable=AsyncMock,
            return_value=mock_response,
        ) as mock_send:
            result = await client.contacts_get_async(
                record_per_page="10",
                page_no="1",
                sort_by="name",
                asc="true",
            )

            mock_send.assert_called_once()
            method, path = mock_send.call_args[0][0], mock_send.call_args[0][1]
            assert method == "GET"
            assert "/v4/settings/contacts/10/1" in path
            assert "sort-by=name" in path
            assert "asc=true" in path
            assert result is not None
            assert "value" in result

    @pytest.mark.asyncio
    async def test_error_response_raises_connector_exception(self, mock_token_provider):
        """Test that a non-2xx response raises ConnectorException."""
        client = SigninghubClient(
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
                await client.contacts_get_async(record_per_page="10", page_no="1")

            assert exc_info.value.status_code == 404


class TestCheckboxAddCheckBoxAsync:
    """Tests for checkbox_add_check_box_async method (POST with body)."""

    @pytest.mark.asyncio
    async def test_success_forwards_request_body(self, mock_token_provider):
        """Test that the POST operation forwards the request body to send_async."""
        client = SigninghubClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider,
        )
        request = CheckBoxFieldRequest()
        mock_response = MockResponse(status=200, text='{"field_id": "cb-1"}')

        with patch.object(
            client._http_client,
            "send_async",
            new_callable=AsyncMock,
            return_value=mock_response,
        ) as mock_send:
            result = await client.checkbox_add_check_box_async(
                input=request,
                package_id="pkg-1",
                document_id="doc-1",
            )

            mock_send.assert_called_once()
            method, path = mock_send.call_args[0][0], mock_send.call_args[0][1]
            assert method == "POST"
            assert path.endswith("/packages/pkg-1/documents/doc-1/fields/checkbox")
            assert mock_send.call_args.kwargs["body"] is request
            assert result is not None

    @pytest.mark.asyncio
    async def test_error_response_raises_connector_exception(self, mock_token_provider):
        """Test that a non-2xx response raises ConnectorException."""
        client = SigninghubClient(
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
                await client.checkbox_add_check_box_async(
                    input=CheckBoxFieldRequest(),
                    package_id="pkg-1",
                    document_id="doc-1",
                )


class TestCheckboxUpdateCheckBoxAsync:
    """Tests for checkbox_update_check_box_async method (PUT with body)."""

    @pytest.mark.asyncio
    async def test_success_forwards_request_body(self, mock_token_provider):
        """Test that the PUT operation forwards the request body to send_async."""
        client = SigninghubClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider,
        )
        request = UpdateCheckBoxFieldRequest()
        mock_response = MockResponse(status=200, text='{"field_id": "cb-1"}')

        with patch.object(
            client._http_client,
            "send_async",
            new_callable=AsyncMock,
            return_value=mock_response,
        ) as mock_send:
            result = await client.checkbox_update_check_box_async(
                input=request,
                package_id="pkg-1",
                document_id="doc-1",
            )

            mock_send.assert_called_once()
            assert mock_send.call_args[0][0] == "PUT"
            assert mock_send.call_args.kwargs["body"] is request
            assert result is not None

    @pytest.mark.asyncio
    async def test_error_response_raises_connector_exception(self, mock_token_provider):
        """Test that a non-2xx response raises ConnectorException."""
        client = SigninghubClient(
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
                await client.checkbox_update_check_box_async(
                    input=UpdateCheckBoxFieldRequest(),
                    package_id="pkg-1",
                    document_id="doc-1",
                )


class TestAttachmentDeleteAttachmentAsync:
    """Tests for attachment_delete_attachment_async method (DELETE)."""

    @pytest.mark.asyncio
    async def test_success_completes_without_error(self, mock_token_provider):
        """Test successful delete completes without raising."""
        client = SigninghubClient(
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
            result = await client.attachment_delete_attachment_async(
                package_id="pkg-1",
                document_id="doc-1",
                attachment_id="att-1",
            )

            mock_send.assert_called_once()
            method, path = mock_send.call_args[0][0], mock_send.call_args[0][1]
            assert method == "DELETE"
            assert path.endswith(
                "/packages/pkg-1/documents/doc-1/attachments/att-1"
            )
            assert result is None

    @pytest.mark.asyncio
    async def test_not_found_raises_connector_exception(self, mock_token_provider):
        """Test that a 404 response raises ConnectorException."""
        client = SigninghubClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider,
        )
        mock_response = MockResponse(status=404, text="Attachment not found")

        with patch.object(
            client._http_client,
            "send_async",
            new_callable=AsyncMock,
            return_value=mock_response,
        ):
            with pytest.raises(ConnectorException) as exc_info:
                await client.attachment_delete_attachment_async(
                    package_id="pkg-1",
                    document_id="doc-1",
                    attachment_id="missing",
                )

            assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    async def test_server_error_raises_connector_exception(self, mock_token_provider):
        """Test that a 5xx response raises ConnectorException."""
        client = SigninghubClient(
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
                await client.attachment_delete_attachment_async(
                    package_id="pkg-1",
                    document_id="doc-1",
                    attachment_id="att-1",
                )


BASE_URL = "https://example.azure.com/connections/test"

OPERATION_ARGS = {
    "attachment_delete_attachment": {
        "package_id": "package-1",
        "document_id": "doc-1",
        "attachment_id": "att-1",
    },
    "attachment_download_attachment": {
        "package_id": "package-1",
        "document_id": "doc-1",
        "attachment_id": "att-1",
    },
    "attachment_get_attachments": {"package_id": "package-1", "document_id": "doc-1"},
    "attachment_upload_attachment": {
        "input": b"raw-attachment-bytes",
        "package_id": "package-1",
        "document_id": "doc-1",
    },
    "checkbox_add_check_box": {
        "input": {},
        "package_id": "package-1",
        "document_id": "doc-1",
    },
    "checkbox_update_check_box": {
        "input": {},
        "package_id": "package-1",
        "document_id": "doc-1",
    },
    "contacts_get": {"record_per_page": "10", "page_no": "1"},
    "documents_delete_document": {"package_id": "package-1", "document_id": "doc-1"},
    "documents_download_document_bytes": {
        "package_id": "package-1",
        "document_id": "doc-1",
    },
    "documents_get_certify_policy": {"package_id": "package-1", "document_id": "doc-1"},
    "documents_get_document_details": {"package_id": "package-1", "document_id": "doc-1"},
    "documents_rename_document": {
        "input": {},
        "package_id": "package-1",
        "document_id": "doc-1",
    },
    "documents_update_certify_policy": {
        "input": {},
        "package_id": "package-1",
        "document_id": "doc-1",
    },
    "documents_upload_from_library": {"package_id": "package-1", "document_id": "doc-1"},
    "documents_upload_stream": {"input": b"raw-document-bytes", "package_id": "package-1"},
    "enterprise_documents_get_enterprise_workflow_access": {
        "package_id": "package-1",
        "order": "1",
    },
    "enterprise_documents_update_enterprise_workflow_access": {
        "input": {},
        "package_id": "package-1",
        "order": "1",
    },
    "fields_auto_assign_field": {
        "input": {},
        "package_id": "package-1",
        "document_id": "doc-1",
    },
    "fields_auto_place": {
        "input": {},
        "package_id": "package-1",
        "document_id": "doc-1",
    },
    "fields_delete_document_field": {
        "input": {},
        "package_id": "package-1",
        "document_id": "doc-1",
    },
    "fields_fill_form_fields": {
        "input": {},
        "package_id": "package-1",
        "document_id": "doc-1",
    },
    "fields_get_all_document_fields": {
        "package_id": "package-1",
        "document_id": "doc-1",
        "page_no": "1",
    },
    "folder_move_package": {"input": {}, "package_id": "package-1"},
    "initials_add_initial": {
        "input": {},
        "package_id": "package-1",
        "document_id": "doc-1",
    },
    "initials_fill": {"input": {}, "package_id": "package-1", "document_id": "doc-1"},
    "initials_update_initial": {
        "input": {},
        "package_id": "package-1",
        "document_id": "doc-1",
    },
    "in_person_add_in_person": {
        "input": {},
        "package_id": "package-1",
        "document_id": "doc-1",
    },
    "in_person_update_in_person": {
        "input": {},
        "package_id": "package-1",
        "document_id": "doc-1",
    },
    "package_add_package": {"input": {}},
    "package_approve": {"input": {}, "package_id": "package-1"},
    "package_decline": {"input": {}, "package_id": "package-1"},
    "package_delete_package": {"package_id_bulk_action": "package-1"},
    "package_download_package_bytes": {"package_id_bulk_action": "package-1"},
    "package_finish": {"package_id": "package-1"},
    "package_gatekeeper_approve": {"input": {}, "package_id": "package-1"},
    "package_gatekeeper_decline": {"input": {}, "package_id": "package-1"},
    "package_get_all_packages": {
        "document_status": "PENDING",
        "page_no": "1",
        "record_per_page": "10",
    },
    "package_get_package_details": {"package_id": "package-1"},
    "package_rename_package": {"input": {}, "package_id_bulk_action": "package-1"},
    "package_submit": {"package_id": "package-1"},
    "q_r_add_q_r_code": {
        "input": {},
        "package_id": "package-1",
        "document_id": "doc-1",
    },
    "q_r_update_q_r_code": {
        "input": {},
        "package_id": "package-1",
        "document_id": "doc-1",
    },
    "radio_add_radio_box": {
        "input": {},
        "package_id": "package-1",
        "document_id": "doc-1",
    },
    "radio_update_radio_box": {
        "input": {},
        "package_id": "package-1",
        "document_id": "doc-1",
    },
    "settings_get_templates": {"record_per_page": "10", "page_no": "1"},
    "signature_add_signature": {
        "input": {},
        "package_id": "package-1",
        "document_id": "doc-1",
    },
    "signature_update_signature": {
        "input": {},
        "package_id": "package-1",
        "document_id": "doc-1",
    },
    "signing_bulk_sign_documents": {
        "input": {},
        "package_id_bulk_action": "package-1",
    },
    "signing_bulk_sign_status": {"input": {}, "bulk_action": "action-1"},
    "signing_sign_document": {
        "input": {},
        "package_id": "package-1",
        "document_id": "doc-1",
    },
    "template_get_enterprise_templates": {"record_per_page": "10", "page_no": "1"},
    "text_box_add_text_box": {
        "input": {},
        "package_id": "package-1",
        "document_id": "doc-1",
    },
    "text_box_update_text_box": {
        "input": {},
        "package_id": "package-1",
        "document_id": "doc-1",
    },
    "workflow_apply_template": {
        "input": {},
        "package_id": "package-1",
        "document_id": "doc-1",
    },
    "workflow_evidence_report_download_bytes": {"package_id": "package-1"},
    "workflow_get_workflow_detail": {"package_id": "package-1"},
    "workflow_get_workflow_history": {
        "package_id": "package-1",
        "page_no": "1",
        "records_per_page": "10",
    },
    "workflow_get_workflow_reminder": {"package_id": "package-1", "order": "1"},
    "workflow_get_workflow_users": {"package_id": "package-1"},
    "workflow_mark_workflow_completed": {"package_id": "package-1"},
    "workflow_permission_get_workflow_permissions": {
        "package_id": "package-1",
        "order": "1",
    },
    "workflow_permission_update_workflow_permissions": {
        "input": {},
        "package_id": "package-1",
        "order": "1",
    },
    "workflow_recall_workflow": {"package_id": "package-1"},
    "workflow_start_workflow": {"package_id": "package-1"},
    "workflow_update_workflow": {"input": {}, "package_id": "package-1"},
    "workflow_update_workflow_post_process": {"input": {}, "package_id": "package-1"},
    "workflow_update_workflow_reminder": {
        "input": {},
        "package_id": "package-1",
        "order": "1",
    },
    "workflow_workflow_add_group": {"input": {}, "package_id": "package-1"},
    "workflow_workflow_add_placeholder": {"input": {}, "package_id": "package-1"},
    "workflow_workflow_add_user": {"input": {}, "package_id": "package-1"},
    "workflow_workflow_delete_user": {"package_id": "package-1", "order": "1"},
    "workflow_workflow_update_placeholder": {
        "input": {},
        "package_id": "package-1",
        "order": "1",
    },
    "workflow_workflow_user_update": {
        "input": {},
        "package_id": "package-1",
        "order": "1",
    },
    "workflow_workflow_user_update_order": {
        "input": {},
        "package_id": "package-1",
        "order": "1",
    },
    "work_space_delete_shared_space": {"id": "space-1"},
    "work_space_get_shared_space": {"id": "space-1"},
    "work_space_update_shared_space": {"input": {}, "id": "space-1"},
}

ALL_OPERATIONS = sorted(OPERATION_ARGS.keys())


async def _invoke_operation(client: SigninghubClient, operation: str):
    """Invoke a SigningHub operation by name for shared method tests."""
    method = getattr(client, f"{operation}_async")
    return await method(**OPERATION_ARGS[operation])


class TestSigninghubClientAllOperations:
    """Success path smoke tests covering every generated operation."""

    @pytest.mark.asyncio
    @pytest.mark.parametrize("operation", ALL_OPERATIONS)
    async def test_all_operations_success(self, mock_token_provider, operation):
        """Test every operation issues a request and returns without error."""
        client = SigninghubClient(BASE_URL, token_provider=mock_token_provider)
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


class TestSigninghubClientAllOperationsErrorHandling:
    """Error handling tests that ensure every operation raises ConnectorException."""

    @pytest.mark.asyncio
    @pytest.mark.parametrize("operation", ALL_OPERATIONS)
    async def test_error_response_raises_exception_for_all_operations(
        self,
        mock_token_provider,
        operation,
    ):
        """Test non-2xx responses raise ConnectorException for every operation."""
        client = SigninghubClient(BASE_URL, token_provider=mock_token_provider)
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
