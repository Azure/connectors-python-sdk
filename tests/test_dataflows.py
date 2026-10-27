# ------------------------------------------------------------
# Copyright (c) Microsoft Corporation.  All rights reserved.
# ------------------------------------------------------------

"""Tests for the Power Query Dataflows connector."""

from __future__ import annotations

import json
from unittest.mock import AsyncMock, patch
from urllib.parse import parse_qs, urlsplit

import pytest
from azure.core.credentials import AzureKeyCredential

from azure.connectors import dataflows
from azure.connectors.dataflows import DataflowsClient, TRIGGER_OPERATIONS
from tests.conftest import MockResponse
from tests.generated_connector_test_utils import GeneratedConnectorContractTests


BASE_URL = "https://example.azure.com/connections/dataflows"


class TestDataflowsClient(GeneratedConnectorContractTests):
    """Check every callable operation and all generated model wire names."""

    client_type = DataflowsClient
    connector_module = dataflows
    connector_name = "dataflows"
    operation_contracts = {
        "refresh_dataflow": ("POST", False),
        "list_groups_for_refresh_dataflow": ("GET", False),
        "list_dataflows_for_refresh_dataflow": ("GET", False),
        "list_groups_for_on_refresh_complete": ("GET", False),
        "list_dataflows_for_on_refresh_complete": ("GET", False),
    }


@pytest.mark.asyncio
@pytest.mark.parametrize("items", [[], [{"id": "workspace-1", "name": "Workspace"}]])
async def test_list_groups_returns_items_and_stops(items: list[dict[str, str]]) -> None:
    """Preserve empty and populated bounded collections without extra requests."""
    async with DataflowsClient(BASE_URL, AzureKeyCredential("test-key")) as client:
        with patch.object(
            client.http_client,
            "send",
            new_callable=AsyncMock,
            return_value=MockResponse(200, json.dumps({"value": items})),
        ) as send:
            groups = [
                group
                async for group in client.list_groups_for_refresh_dataflow(
                    workspace_type="Workspace",
                )
            ]

    assert groups == items
    send.assert_awaited_once()
    assert send.call_args.args[0] == "GET"
    assert urlsplit(send.call_args.args[1]).path.endswith("/api/listgroups/forrefreshdataflow")
    assert parse_qs(urlsplit(send.call_args.args[1]).query) == {"workspaceType": ["Workspace"]}


@pytest.mark.asyncio
async def test_refresh_dataflow_encodes_identifiers_and_preserves_response() -> None:
    """Keep refresh route identifiers separate and forward request controls."""
    async with DataflowsClient(BASE_URL, AzureKeyCredential("test-key")) as client:
        with patch.object(
            client.http_client,
            "send",
            new_callable=AsyncMock,
            return_value=MockResponse(200, '{"dataflowId": "flow-1", "dataflowName": "Sales"}'),
        ) as send:
            refreshed = await client.refresh_dataflow(
                group_id_for_refresh_dataflow="workspace/name",
                dataflow_id_for_refresh_dataflow="flow id",
                workspace_type="Environment",
                timeout=12.0,
                headers={"x-test": "refresh"},
                client_request_id="refresh-request",
            )

    assert refreshed == {"dataflowId": "flow-1", "dataflowName": "Sales"}
    assert send.call_args.args == (
        "POST",
        BASE_URL + "/api/groups/workspace%2Fname/dataflows/flow%20id/refreshdataflow"
        "?workspaceType=Environment",
    )
    assert send.call_args.kwargs["body"] is None
    assert send.call_args.kwargs["timeout"] == 12.0
    assert send.call_args.kwargs["headers"] == {"x-test": "refresh"}
    assert send.call_args.kwargs["client_request_id"] == "refresh-request"


def test_refresh_trigger_metadata_preserves_callback_contract() -> None:
    """Expose the refresh callback as metadata, not a callable client method."""
    trigger = TRIGGER_OPERATIONS["OnRefreshComplete"]
    assert trigger["callback_payload_type"] == "RefreshModel"
    assert trigger["required_parameters"] == [
        "workspaceType", "groupIdForOnRefreshComplete", "dataflowIdForOnRefreshComplete",
    ]
    assert trigger["path"].endswith("/{dataflowIdForOnRefreshComplete}/onrefreshcomplete")
    assert not hasattr(DataflowsClient, "on_refresh_complete")
