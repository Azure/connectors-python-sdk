# ------------------------------------------------------------
# Copyright (c) Microsoft Corporation.  All rights reserved.
# ------------------------------------------------------------

"""Mocked Azure Core transport and package exports for the new connector clients."""

from __future__ import annotations

import json
from urllib.parse import parse_qs, urlsplit

import pytest
from azure.core.credentials import AzureKeyCredential

import azure.connectors as connectors
from azure.connectors.dataflowssms import DataflowssmsClient, SendSmsInput
from azure.connectors.sdk import ConnectorException
from azure.connectors.service_now import ServiceNowClient
from tests.test_sdk_azure_core_pipeline import RecordingTransport, create_response


RUNTIME_URL = "https://connector.example.test/connections/test"


@pytest.mark.parametrize(
    ("client_name", "module_name", "client_type", "api_name"),
    [
        ("DataflowssmsClient", "dataflowssms", DataflowssmsClient, "dataflowssms"),
        ("ServiceNowClient", "service_now", ServiceNowClient, "service-now"),
    ],
)
def test_new_clients_have_public_lazy_exports(
    client_name: str, module_name: str, client_type: type, api_name: str,
) -> None:
    """Export both client classes from their module and lazy package root."""
    assert connectors.CLIENT_REGISTRY[client_name] == module_name
    assert client_name in connectors.__all__
    assert client_name in dir(connectors)
    assert getattr(connectors, client_name) is client_type
    assert client_type(RUNTIME_URL, AzureKeyCredential("test-key")).connector_name == api_name


@pytest.mark.asyncio
async def test_dataflows_sms_serializes_wire_names_and_reads_response() -> None:
    """Exercise the generated mutation through the Azure Core pipeline, never live."""
    transport = RecordingTransport(create_response(content=b'{"status":"accepted"}'))
    async with DataflowssmsClient(
        RUNTIME_URL, AzureKeyCredential("test-key"), transport=transport,
    ) as client:
        response = await client.send_sms(
            SendSmsInput(
                recipient="+12065550123", sender_id="Notify", message="hello", type_="sms",
            ),
        )

    assert response == {"status": "accepted"}
    request, = transport.requests
    assert request.method == "POST"
    assert urlsplit(request.url).path.endswith("/connections/test/sms/send")
    assert json.loads(request.body) == {
        "recipient": "+12065550123", "sender_id": "Notify",
        "message": "hello", "type": "sms",
    }
    assert transport.closed


@pytest.mark.asyncio
async def test_dataflows_sms_error_preserves_status_and_body() -> None:
    """Turn an actual transport error response into a connector exception."""
    transport = RecordingTransport(create_response(status=400, content=b'{"error":"invalid"}'))
    async with DataflowssmsClient(
        RUNTIME_URL, AzureKeyCredential("test-key"), transport=transport,
    ) as client:
        with pytest.raises(ConnectorException) as captured:
            await client.get_balance()

    assert captured.value.status_code == 400
    assert captured.value.method == "GET"
    assert "invalid" in captured.value.response_body
    assert len(transport.requests) == 1
    assert urlsplit(transport.requests[0].url).path.endswith("/balance")


@pytest.mark.asyncio
async def test_service_now_encodes_identifiers_boolean_query_and_response() -> None:
    """Preserve dynamic response records and escape URL path/query values."""
    transport = RecordingTransport(create_response(content=b'{"result":{"sys_id":"abc"}}'))
    async with ServiceNowClient(
        RUNTIME_URL, AzureKeyCredential("test-key"), transport=transport,
    ) as client:
        record = await client.get_record(
            table_type="incident/urgent", sysid="a/b",
            sysparm_display_value=True, sysparm_fields="sys_id,number",
        )

    assert record == {"result": {"sys_id": "abc"}}
    request, = transport.requests
    assert request.method == "GET"
    assert urlsplit(request.url).path.endswith("/api/now/v2/table/incident%2Furgent/a%2Fb")
    assert parse_qs(urlsplit(request.url).query) == {
        "sysparm_display_value": ["true"], "sysparm_fields": ["sys_id,number"],
    }


@pytest.mark.asyncio
async def test_service_now_error_response_is_not_silently_returned() -> None:
    """Propagate a mocked read failure without calling any remote connector."""
    transport = RecordingTransport(create_response(status=404, content=b'{"error":"missing"}'))
    async with ServiceNowClient(
        RUNTIME_URL, AzureKeyCredential("test-key"), transport=transport,
    ) as client:
        with pytest.raises(ConnectorException) as captured:
            await client.get_record(table_type="incident", sysid="missing")

    assert captured.value.status_code == 404
    assert "missing" in captured.value.response_body
    assert len(transport.requests) == 1


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("module_name", "result", "label"),
    [
        ("dataflowssms", {}, "SMS balance: {}"),
        ("dataflowssms", {"balance": 8}, "SMS balance: {'balance': 8}"),
        ("service_now", {}, "Incident record: {}"),
        ("service_now", {"result": {"sys_id": "abc"}},
         "Incident record: {'result': {'sys_id': 'abc'}}"),
    ],
)
async def test_read_only_samples_print_empty_and_populated_results(
    module_name: str, result: dict, label: str,
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str],
) -> None:
    """Execute each sample without Azure credentials or live connector actions."""
    import importlib.util
    from pathlib import Path

    sample_path = Path(__file__).parent.parent / "samples" / "sample_connector_usage" / (
        f"sample_connector_usage_{module_name}.py"
    )
    specification = importlib.util.spec_from_file_location(
        f"sample_connector_usage_{module_name}", sample_path,
    )
    assert specification is not None and specification.loader is not None
    sample = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(sample)

    class MockAsyncContext:
        async def __aenter__(self) -> MockAsyncContext:
            return self

        async def __aexit__(self, *_args: object) -> None:
            return None

        async def get_balance(self) -> dict:
            return result

        async def get_record(self, *, table_type: str, sysid: str) -> dict:
            assert (table_type, sysid) == ("incident", "abc")
            return result

    monkeypatch.setattr(sample, "CONNECTION_RUNTIME_URL", RUNTIME_URL)
    if module_name == "service_now":
        monkeypatch.setattr(sample, "RECORD_ID", "abc")
    monkeypatch.setattr(sample, "DefaultAzureCredential", MockAsyncContext)
    monkeypatch.setattr(
        sample, "DataflowssmsClient" if module_name == "dataflowssms" else "ServiceNowClient",
        lambda *_args: MockAsyncContext(),
    )
    await sample.main()
    assert capsys.readouterr().out.strip() == label
