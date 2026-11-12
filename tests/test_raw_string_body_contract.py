# ------------------------------------------------------------
# Copyright (c) Microsoft Corporation.  All rights reserved.
# ------------------------------------------------------------

"""Transport-level contracts for generated raw string body operations."""

from __future__ import annotations

import json
from collections import UserDict
from dataclasses import dataclass
from importlib import import_module
from pathlib import Path
from typing import Any

import pytest
from azure.core.credentials import AzureKeyCredential
from azure.core.pipeline.transport import HttpRequest

from azure.connectors.azure_blob import AzureBlobClient
from azure.connectors.azure_monitor_logs import AzureMonitorLogsClient
from azure.connectors.azure_queues import AzureQueuesClient
from azure.connectors.azure_tables import AzureTablesClient, CreateEntityInput
from azure.connectors.document_db import DocumentDBClient
from azure.connectors.onenote import OnenoteClient
from azure.connectors.power_bi import PowerBIClient
from azure.connectors.sdk import ConnectorClientBase, ConnectorException
from azure.connectors.teams import TeamsClient
from tests.test_sdk_azure_core_pipeline import RecordingTransport, create_response

RUNTIME_URL = "https://connector.example.test/connections/test"
TABLE_NAME = "RegressionTable"
SPECIAL_TEXT = 'caf\u00e9 \u6771\u4eac \U0001f600 "quoted"\nsecond line\\folder\r\nend'


@dataclass(frozen=True)
class RawOperation:
    """Describe one generated operation without replacing its implementation."""

    client_type: type[ConnectorClientBase]
    method: str
    parameters: dict[str, str]
    media_type: str = "application/json"


RAW_OPERATIONS = [
    RawOperation(
        AzureMonitorLogsClient,
        "query_schema",
        {
            "subscriptions": "subscription",
            "resourcegroups": "group",
            "resourcetype": "Microsoft.OperationalInsights/workspaces",
            "resourcename": "workspace",
        },
    ),
    RawOperation(
        AzureQueuesClient,
        "put_message",
        {"storage_account_name": "account", "queue_name": "queue"},
    ),
    RawOperation(
        AzureTablesClient,
        "create_table",
        {"storage_account_name": "account"},
    ),
    RawOperation(
        DocumentDBClient,
        "execute_stored_procedure",
        {
            "cosmos_db_account_name": "account",
            "database_id": "database",
            "collection_id": "collection",
            "sproc_id": "procedure",
        },
    ),
    RawOperation(
        OnenoteClient,
        "create_page_in_section",
        {"notebook_key": "notebook", "section_id": "section"},
        "text/plain",
    ),
    RawOperation(OnenoteClient, "create_page_in_quick_notes", {}),
    RawOperation(
        PowerBIClient,
        "goal_value_checkin_note",
        {
            "groupid": "group",
            "scorecard_id": "scorecard",
            "goal_id": "goal",
            "goal_checkin": "checkin",
        },
    ),
    RawOperation(
        TeamsClient,
        "get_flow_continuation_subscription_with_poster_output_metadata",
        {"poster": "Flow bot", "recipient_type": "Channel"},
    ),
]
OPERATION_IDS = [
    "logs", "queues", "tables", "cosmos", "section", "quick", "powerbi", "teams",
]


class BodyRecordingTransport(RecordingTransport):
    """Capture the final Azure Core request body without any network access."""

    def __init__(self, *, validate_table_name: bool = False) -> None:
        """Configure a normal response or a request-sensitive Tables response."""
        super().__init__(create_response(status=201))
        self.bodies: list[bytes | None] = []
        self.validate_table_name = validate_table_name

    async def send(self, request: HttpRequest, **kwargs: Any) -> Any:
        """Record UTF-8 bytes as a real transport would send them."""
        body = request.body
        content = body.encode("utf-8") if isinstance(body, str) else body
        assert content is None or isinstance(content, bytes)
        self.bodies.append(content)
        if self.validate_table_name:
            accepted = content == TABLE_NAME.encode("utf-8")
            self.responses = [
                create_response(
                    status=201 if accepted else 400,
                    content=(
                        b'{"TableName":"RegressionTable"}'
                        if accepted else b'{"error":"Invalid table name"}'
                    ),
                ),
            ]
        return await super().send(request, **kwargs)


def test_generated_clients_are_loaded_from_this_checkout() -> None:
    """Guard against an editable install silently importing another checkout."""
    source_root = (Path(__file__).resolve().parents[1] / "src").resolve()
    for client_type in [
        *(operation.client_type for operation in RAW_OPERATIONS), AzureBlobClient,
    ]:
        module = import_module(client_type.__module__)
        assert module.__file__ is not None
        assert Path(module.__file__).resolve().is_relative_to(source_root)


@pytest.mark.asyncio
@pytest.mark.parametrize("operation", RAW_OPERATIONS, ids=OPERATION_IDS)
@pytest.mark.parametrize(
    "payload",
    [SPECIAL_TEXT, '{"query":"count\\nnext"}', TABLE_NAME, "", None],
    ids=["special", "json", "plain", "empty", "none"],
)
async def test_raw_operations_preserve_body_bytes_and_media_type(
    operation: RawOperation,
    payload: str | None,
) -> None:
    """Keep raw text intact instead of quoting or escaping it as a JSON value."""
    transport = BodyRecordingTransport()
    async with operation.client_type(
        RUNTIME_URL, AzureKeyCredential("test-key"), transport=transport,
    ) as client:
        assert transport.requests == []
        await getattr(client, operation.method)(
            input=payload, **operation.parameters,
        )

    assert transport.bodies == [
        None if payload is None else payload.encode("utf-8"),
    ]
    request, = transport.requests
    assert request.method == "POST"
    assert request.headers["Content-Type"].split(";", 1)[0] == operation.media_type
    assert transport.closed is True


@pytest.mark.asyncio
async def test_tables_accepts_exact_raw_name() -> None:
    """Exercise the success path against a fake that rejects quoted names."""
    transport = BodyRecordingTransport(validate_table_name=True)
    async with AzureTablesClient(
        RUNTIME_URL, AzureKeyCredential("test-key"), transport=transport,
    ) as client:
        response = await client.create_table(
            input=TABLE_NAME, storage_account_name="account",
        )

    assert transport.bodies == [b"RegressionTable"]
    assert response == {"TableName": TABLE_NAME}
    assert len(transport.requests) == 1


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "payload", ['"RegressionTable"', "WrongTable"], ids=["quoted", "wrong"],
)
async def test_tables_fake_rejects_nonmatching_names(payload: str) -> None:
    """Prove the fake validates bytes rather than always returning success."""
    transport = BodyRecordingTransport(validate_table_name=True)
    async with AzureTablesClient(
        RUNTIME_URL, AzureKeyCredential("test-key"), transport=transport,
    ) as client:
        with pytest.raises(ConnectorException) as error:
            await client.create_table(
                input=payload, storage_account_name="account",
            )

    assert error.value.status_code == 400
    assert "Invalid table name" in error.value.response_body
    assert len(transport.requests) == 1


@pytest.mark.asyncio
@pytest.mark.parametrize("as_mapping", [False, True], ids=["model", "mapping"])
async def test_object_operation_still_serializes_json(as_mapping: bool) -> None:
    """Serialize real object inputs once, preserving nested string values."""
    properties = {
        "PartitionKey": "partition",
        "RowKey": "row",
        "Name": SPECIAL_TEXT,
        "Nested": {"active": True, "count": 2},
        "Omitted": None,
    }
    payload = (
        UserDict(properties) if as_mapping
        else CreateEntityInput(additional_properties=properties)
    )
    transport = BodyRecordingTransport()
    async with AzureTablesClient(
        RUNTIME_URL, AzureKeyCredential("test-key"), transport=transport,
    ) as client:
        await client.create_entity(
            input=payload, storage_account_name="account", table_name=TABLE_NAME,
        )

    expected = {key: value for key, value in properties.items() if value is not None}
    content, = transport.bodies
    assert content == json.dumps(expected).encode("utf-8")
    assert json.loads(content) == expected
    request, = transport.requests
    assert request.headers["Content-Type"] == "application/json"


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "payload", [b'\x00\xff"\n\\', bytearray(b'\x00\xff"\n\\')],
    ids=["bytes", "bytearray"],
)
async def test_binary_operation_still_sends_exact_bytes(
    payload: bytes | bytearray,
) -> None:
    """Keep the generated blob operation's bytes and media type unchanged."""
    transport = BodyRecordingTransport()
    async with AzureBlobClient(
        RUNTIME_URL, AzureKeyCredential("test-key"), transport=transport,
    ) as client:
        await client.create_file(
            input=payload, dataset="account", folder_path="/folder", name="file",
        )

    assert transport.bodies == [bytes(payload)]
    request, = transport.requests
    assert request.headers["Content-Type"] == "application/octet-stream"


@pytest.mark.asyncio
@pytest.mark.parametrize("as_mapping", [False, True], ids=["model", "mapping"])
async def test_invalid_object_map_fails_before_transport(as_mapping: bool) -> None:
    """Keep object-map serialization failures ahead of network dispatch."""
    properties = {"PartitionKey": "partition", "Unsupported": {1, 2}}
    payload = (
        UserDict(properties) if as_mapping
        else CreateEntityInput(additional_properties=properties)
    )
    transport = BodyRecordingTransport()
    async with AzureTablesClient(
        RUNTIME_URL, AzureKeyCredential("test-key"), transport=transport,
    ) as client:
        with pytest.raises(TypeError):
            await client.create_entity(
                input=payload, storage_account_name="account", table_name=TABLE_NAME,
            )

    assert transport.requests == []
    assert transport.bodies == []
