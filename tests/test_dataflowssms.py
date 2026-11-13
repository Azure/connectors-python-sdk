# ------------------------------------------------------------
# Copyright (c) Microsoft Corporation.  All rights reserved.
# ------------------------------------------------------------

"""Wire-level contracts for the two SMS send verbs and safe GET reads."""

from __future__ import annotations

from urllib.parse import parse_qs, urlsplit

import pytest
from azure.core.credentials import AzureKeyCredential
from azure.core.exceptions import ServiceRequestError

from azure.connectors.data_flows_sms import DataFlowsSmsClient
from azure.connectors.sdk import ConnectorException
from tests.test_sdk_azure_core_pipeline import RecordingTransport, create_response


RUNTIME_URL = "https://connector.example.test/apim/dataflowssms/connection-1"


@pytest.mark.asyncio
async def test_send_sms_get_preserves_get_route_and_query() -> None:
    """Keep the newly exposed GET send operation distinct from POST send_sms."""
    transport = RecordingTransport(create_response(content=b'{"status":"accepted"}'))
    async with DataFlowsSmsClient(
        RUNTIME_URL, AzureKeyCredential("test-key"), transport=transport,
    ) as client:
        result = await client.send_sms_get(
            recipient="+12065550123", sender_id="Notify", message="hello world", type_="sms",
        )

    assert result == {"status": "accepted"}
    request, = transport.requests
    assert request.method == "GET"
    assert urlsplit(request.url).path.endswith("/dataflowssms/connection-1/sms/send")
    assert parse_qs(urlsplit(request.url).query) == {
        "recipient": ["+12065550123"], "sender_id": ["Notify"],
        "message": ["hello world"], "type": ["sms"],
    }
    assert request.content is None


@pytest.mark.asyncio
@pytest.mark.parametrize("retry_unsafe_http_methods", [False, True])
async def test_send_sms_get_never_retries_even_with_unsafe_opt_in(
    retry_unsafe_http_methods: bool,
) -> None:
    """Do not replay a side-effecting GET send after a retryable server response."""
    transport = RecordingTransport(
        create_response(status=500, content=b'{"error":"retryable"}'),
        create_response(status=200, content=b'{"status":"duplicate"}'),
    )
    async with DataFlowsSmsClient(
        RUNTIME_URL, AzureKeyCredential("test-key"), transport=transport,
        max_retry_attempts=2, initial_retry_delay_seconds=0,
        retry_jitter_factor=0,
        retry_unsafe_http_methods=retry_unsafe_http_methods,
    ) as client:
        with pytest.raises(ConnectorException) as captured:
            await client.send_sms_get(
                recipient="+12065550123", sender_id="Notify", message="once",
            )

    assert captured.value.status_code == 500
    assert len(transport.requests) == 1
    assert transport.requests[0].method == "GET"
    assert urlsplit(transport.requests[0].url).path.endswith("/sms/send")


@pytest.mark.asyncio
@pytest.mark.parametrize("retry_unsafe_http_methods", [False, True])
async def test_send_sms_get_never_retries_transport_errors(
    retry_unsafe_http_methods: bool,
) -> None:
    """Never replay SMS sends after a retryable transport exception either."""
    transport = RecordingTransport(
        ServiceRequestError("connection dropped"),
        create_response(status=200, content=b'{"status":"duplicate"}'),
    )
    async with DataFlowsSmsClient(
        RUNTIME_URL, AzureKeyCredential("test-key"), transport=transport,
        max_retry_attempts=2, initial_retry_delay_seconds=0,
        retry_jitter_factor=0,
        retry_unsafe_http_methods=retry_unsafe_http_methods,
    ) as client:
        with pytest.raises(ServiceRequestError, match="connection dropped"):
            await client.send_sms_get(
                recipient="+12065550123", sender_id="Notify", message="once",
            )

    assert len(transport.requests) == 1
    assert transport.requests[0].method == "GET"
    assert urlsplit(transport.requests[0].url).path.endswith("/sms/send")


@pytest.mark.asyncio
@pytest.mark.parametrize("retry_unsafe_http_methods", [False, True])
async def test_list_sms_retains_normal_get_retry(retry_unsafe_http_methods: bool) -> None:
    """Retry ordinary read-only SMS GETs without weakening send-GET protection."""
    transport = RecordingTransport(
        create_response(status=500, content=b'{"error":"temporary"}'),
        create_response(status=200, content=b'{"messages":[{"id":"message-1"}]}'),
    )
    async with DataFlowsSmsClient(
        RUNTIME_URL, AzureKeyCredential("test-key"), transport=transport,
        max_retry_attempts=2, initial_retry_delay_seconds=0,
        retry_jitter_factor=0,
        retry_unsafe_http_methods=retry_unsafe_http_methods,
    ) as client:
        result = await client.list_sms(page=1)

    assert result == {"messages": [{"id": "message-1"}]}
    assert len(transport.requests) == 2
    assert all(request.method == "GET" for request in transport.requests)
    assert all(urlsplit(request.url).path.endswith("/sms") for request in transport.requests)
    assert all(parse_qs(urlsplit(request.url).query) == {"page": ["1"]}
               for request in transport.requests)
