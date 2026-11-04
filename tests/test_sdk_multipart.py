# ------------------------------------------------------------
# Copyright (c) Microsoft Corporation.  All rights reserved.
# ------------------------------------------------------------

"""Wire-level tests for multipart connector request encoding."""

from __future__ import annotations

from email import policy
from email.parser import BytesParser
from urllib.parse import parse_qs, urlsplit

import pytest
from azure.core.credentials import AzureKeyCredential

from azure.connectors.cloudmersiveconvert import CloudmersiveconvertClient
from azure.connectors.docuware import DocuwareClient
from azure.connectors.sdk import ConnectorException, MultipartFile, encode_multipart_form_data
from azure.connectors.zohosign import ZohosignClient
from tests.test_sdk_azure_core_pipeline import RecordingTransport, create_response


@pytest.mark.asyncio
async def test_multipart_preserves_files_repeated_fields_and_utf8_text() -> None:
    """Keep arbitrary file bytes and each text field in its own MIME part."""
    content = b"\x00\x7f\x80\xff\r\nnot-json"
    body, content_type = await encode_multipart_form_data(
        [
            ("description", "caf\u00e9"),
            ("tags", "first"),
            ("tags", "second"),
            ("enabled", "false"),
            ("count", "0"),
            ("empty", ""),
            ("file", MultipartFile(content, "example.bin", "application/custom")),
            ("default-file", b""),
        ]
    )
    message = BytesParser(policy=policy.default).parsebytes(
        f"Content-Type: {content_type}\r\n\r\n".encode("ascii") + body
    )
    parts = list(message.iter_parts())

    assert content_type.startswith("multipart/form-data; boundary=")
    assert [part.get_param("name", header="content-disposition") for part in parts] == [
        "description", "tags", "tags", "enabled", "count", "empty", "file", "default-file"
    ]
    assert [part.get_payload(decode=True) for part in parts[:6]] == [
        "caf\u00e9".encode("utf-8"), b"first", b"second", b"false", b"0", b""
    ]
    assert parts[6].get_payload(decode=True) == content
    assert parts[6].get_filename() == "example.bin"
    assert parts[6].get_content_type() == "application/custom"
    assert parts[7].get_payload(decode=True) == b""
    assert parts[7].get_filename() == "blob"
    assert parts[7].get_content_type() == "application/octet-stream"


@pytest.mark.asyncio
async def test_empty_multipart_has_a_complete_boundary() -> None:
    """Encode an empty form rather than sending JSON or omitting the MIME body."""
    body, content_type = await encode_multipart_form_data([])
    message = BytesParser(policy=policy.default).parsebytes(
        f"Content-Type: {content_type}\r\n\r\n".encode("ascii") + body
    )

    assert body == f"--{message.get_boundary()}--\r\n".encode("ascii")
    assert list(message.iter_parts()) == []


@pytest.mark.parametrize(
    "file_name, content_type",
    [("", "text/plain"), ("bad\r\nname", "text/plain"), ("good", "text/plain\r\nbad")],
)
def test_multipart_file_rejects_invalid_headers(file_name: str, content_type: str) -> None:
    """Reject malformed file headers before dispatch."""
    with pytest.raises(ValueError):
        MultipartFile(b"content", file_name, content_type)


@pytest.mark.asyncio
async def test_multipart_rejects_values_that_would_need_json_serialization() -> None:
    """Reject accidental structured fields instead of sending success-shaped output."""
    with pytest.raises(TypeError, match="Multipart field 'invalid'"):
        await encode_multipart_form_data([("invalid", {"nested": "value"})])


@pytest.mark.asyncio
@pytest.mark.parametrize("with_metadata", [False, True])
async def test_generated_upload_preserves_file_and_binary_response(
    with_metadata: bool,
) -> None:
    """Run a generated upload through the real Azure Core request builder."""
    content = b"\x00\x7f\x80\xff"
    response = create_response(content=b"")
    response.body.return_value = content
    response.read.return_value = content
    response.text.return_value = content.decode("utf-8", errors="replace")
    transport = RecordingTransport(response)
    upload = (
        MultipartFile(content, "example.docx", "application/custom")
        if with_metadata else content
    )
    async with CloudmersiveconvertClient(
        "https://example.test/connection",
        AzureKeyCredential("test-key"),
        transport=transport,
    ) as client:
        result = await client.convert_document_autodetect_to_pdf(
            upload,
            headers={"Content-Type": "application/json", "X-Custom-Header": "sample"},
            client_request_id="multipart-id",
        )

    assert result == content
    assert len(transport.requests) == 1
    request = transport.requests[0]
    assert request.method == "POST"
    assert urlsplit(request.url).path == "/connection/convert/autodetect/to/pdf"
    assert request.headers["x-ms-client-request-id"] == "multipart-id"
    assert request.headers["X-Custom-Header"] == "sample"
    message = BytesParser(policy=policy.default).parsebytes(
        f"Content-Type: {request.headers['Content-Type']}\r\n\r\n".encode("ascii")
        + request.content
    )
    parts = list(message.iter_parts())
    assert len(parts) == 1
    assert parts[0].get_param("name", header="content-disposition") == "inputFile"
    assert parts[0].get_payload(decode=True) == content
    assert parts[0].get_filename() == ("example.docx" if with_metadata else "blob")
    assert parts[0].get_content_type() == (
        "application/custom" if with_metadata else "application/octet-stream"
    )


@pytest.mark.asyncio
@pytest.mark.parametrize("include_optional_fields", [False, True])
async def test_generated_docuware_upload_preserves_hidden_default(
    include_optional_fields: bool,
) -> None:
    """Send internal defaults while omitting absent optional fields."""
    transport = RecordingTransport(create_response(content=b'{"DocumentId":123}'))
    content = b"\x00\xff"
    async with DocuwareClient(
        "https://example.test/connection",
        AzureKeyCredential("test-key"),
        transport=transport,
    ) as client:
        result = await client.store_to_file_cabinet(
            "cabinet",
            "dialog",
            index='{"invoice":"123"}' if include_optional_fields else None,
            file=MultipartFile(content, "invoice.bin") if include_optional_fields else None,
        )

    assert result == {"DocumentId": 123}
    request = transport.requests[0]
    assert urlsplit(request.url).path == "/connection/FileCabinets/cabinet/Documents"
    assert parse_qs(urlsplit(request.url).query) == {"StoreDialogId": ["dialog"]}
    message = BytesParser(policy=policy.default).parsebytes(
        f"Content-Type: {request.headers['Content-Type']}\r\n\r\n".encode("ascii")
        + request.content
    )
    parts = {
        part.get_param("name", header="content-disposition"): part
        for part in message.iter_parts()
    }
    assert parts["Default"].get_payload(decode=True) == b"{}"
    assert set(parts) == ({"Default", "index", "file"} if include_optional_fields else {"Default"})
    if include_optional_fields:
        assert parts["index"].get_payload(decode=True) == b'{"invoice":"123"}'
        assert parts["file"].get_payload(decode=True) == content


@pytest.mark.asyncio
async def test_generated_zohosign_upload_sends_a_file_part() -> None:
    """Create a Zoho Sign document with a real multipart file request."""
    transport = RecordingTransport(create_response(content=b'{"code":0}'))
    async with ZohosignClient(
        "https://example.test/connection",
        AzureKeyCredential("test-key"),
        transport=transport,
    ) as client:
        result = await client.create_document(b"\x00\xff")

    assert result == {"code": 0}
    request = transport.requests[0]
    assert urlsplit(request.url).path == "/connection/requests"
    message = BytesParser(policy=policy.default).parsebytes(
        f"Content-Type: {request.headers['Content-Type']}\r\n\r\n".encode("ascii")
        + request.content
    )
    part = next(message.iter_parts())
    assert part.get_param("name", header="content-disposition") == "file"
    assert part.get_payload(decode=True) == b"\x00\xff"


@pytest.mark.asyncio
@pytest.mark.parametrize("status", [400, 503])
async def test_generated_multipart_errors_propagate_without_unsafe_retries(status: int) -> None:
    """Do not retry a side-effecting multipart upload by default."""
    transport = RecordingTransport(
        create_response(status, content=b"Upload failed"),
        create_response(content=b"unexpected retry"),
    )
    async with CloudmersiveconvertClient(
        "https://example.test/connection",
        AzureKeyCredential("test-key"),
        transport=transport,
    ) as client:
        with pytest.raises(ConnectorException) as error:
            await client.convert_document_autodetect_to_pdf(b"content")

    assert error.value.status_code == status
    assert len(transport.requests) == 1


@pytest.mark.asyncio
async def test_generated_upload_rejects_missing_required_file_before_dispatch() -> None:
    """A missing file must not become a text field containing None."""
    transport = RecordingTransport()
    async with CloudmersiveconvertClient(
        "https://example.test/connection",
        AzureKeyCredential("test-key"),
        transport=transport,
    ) as client:
        with pytest.raises(ValueError, match="Parameter 'inputFile' is required"):
            await client.convert_document_autodetect_to_pdf(None)

    assert transport.requests == []
