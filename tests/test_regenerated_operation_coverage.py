# Copyright (c) Microsoft Corporation. All rights reserved.

"""Focused HTTP contract tests for newly generated connector operations."""

from __future__ import annotations

import hashlib
import inspect
import json
from pathlib import Path
from types import ModuleType
from typing import Any
from unittest.mock import AsyncMock, patch

import pytest

import azure.connectors.azureautomation as azureautomation
import azure.connectors.azureblob as azureblob
import azure.connectors.azuredatafactory as azuredatafactory
import azure.connectors.azurevm as azurevm
import azure.connectors.excelonlinebusiness as excelonlinebusiness
import azure.connectors.teams as teams
import azure.connectors.wdatp as wdatp
from azure.connectors.sdk import ConnectorException
from tests.conftest import MockResponse
from tests.generated_connector_test_utils import invoke_generated_operation


REPOSITORY_ROOT = Path(__file__).parent.parent
GENERATION_MANIFEST = json.loads(
    (REPOSITORY_ROOT / "generation.manifest.json").read_text(encoding="utf-8")
)


def canonical_text_hash(relative_path: str) -> str:
    """Hash the same canonical text recorded by the generator manifest."""
    text = (REPOSITORY_ROOT / relative_path).read_text(encoding="utf-8")
    return hashlib.sha256(text.replace("\r\n", "\n").encode("utf-8")).hexdigest()


@pytest.mark.parametrize(
    "connector", GENERATION_MANIFEST["connectors"], ids=lambda connector: connector["apiName"]
)
def test_regenerated_client_matches_pinned_inputs(connector: dict[str, Any]) -> None:
    """Test every committed generated output and Swagger hash matches its provenance."""
    assert canonical_text_hash(connector["swaggerSnapshot"]) == connector["swaggerSha256"]
    assert canonical_text_hash(connector["outputFile"]) == connector["outputSha256"]


def test_regeneration_records_merged_source_and_minimal_catalog() -> None:
    """Test the complete shipped inventory uses one unpatched source and minimal catalog."""
    assert GENERATION_MANIFEST["status"] == "generated"
    generator = GENERATION_MANIFEST["generator"]
    assert generator["bpmBaseCommit"] == generator["bpmHeadCommit"]
    assert len(generator["bpmHeadCommit"]) == 40
    assert "sourcePatch" not in generator
    assert generator["assemblyVersion"]
    source = GENERATION_MANIFEST["swaggerSource"]
    assert canonical_text_hash(source["managedApisSnapshot"]) == source["managedApisSha256"]
    catalog = json.loads((REPOSITORY_ROOT / source["managedApisSnapshot"]).read_text())
    assert {entry["name"] for entry in catalog["value"]} == {
        connector["apiName"] for connector in GENERATION_MANIFEST["connectors"]
    }
    assert len(GENERATION_MANIFEST["connectors"]) == 99
    for entry in catalog["value"]:
        assert set(entry) == {"name", "properties"}
        assert set(entry["properties"]) == {"generalInformation"}
        assert set(entry["properties"]["generalInformation"]) == {"displayName"}


CONNECTOR_OPERATION_CASES = [
    (
        azureautomation,
        azureautomation.AzureautomationClient,
        [
            ("subscriptions_list", "GET", "/subscriptions?", False),
            ("resource_groups_list", "GET", "/resourcegroups?", False),
            ("automation_accounts_list", "GET", "/automationAccounts?", False),
            ("runbooks_list", "GET", "/runbooks?", False),
            ("get_runbook", "GET", "/runbooks/value?", False),
        ],
    ),
    (
        azureblob,
        azureblob.AzureblobClient,
        [("get_data_sets", "GET", "/v2/codeless/GetDataSets", False)],
    ),
    (
        azuredatafactory,
        azuredatafactory.AzuredatafactoryClient,
        [
            ("list_subscriptions", "GET", "/subscriptions?", False),
            ("list_resource_groups", "GET", "/resourcegroups?", False),
            (
                "list_data_factories",
                "GET",
                "/Microsoft.DataFactory/factories?",
                False,
            ),
            ("list_pipelines", "GET", "/pipelines?", False),
        ],
    ),
    (
        azurevm,
        azurevm.AzurevmClient,
        [
            ("subscriptions_list", "GET", "/subscriptions?", False),
            ("resource_groups_list", "GET", "/resourcegroups?", False),
            (
                "virtual_machine_scale_sets_list",
                "GET",
                "/virtualMachineScaleSets?",
                False,
            ),
            (
                "virtual_machines_in_scale_set_list",
                "GET",
                "/virtualMachineScaleSets/value/virtualMachines?",
                False,
            ),
            (
                "virtual_machines_list",
                "GET",
                "/Microsoft.Compute/virtualMachines?",
                False,
            ),
        ],
    ),
    (
        excelonlinebusiness,
        excelonlinebusiness.ExcelonlinebusinessClient,
        [
            ("get_sources", "GET", "/codeless/v1.0/sources?", False),
            ("get_drives", "GET", "/codeless/v1.0/drives?", False),
            ("get_columns", "GET", "/workbook/tables/value/columns?", False),
            ("get_table", "GET", "/workbook/tables/value/metadata?", False),
            (
                "get_single_script",
                "GET",
                "/v2/officescripting/api/storage/script?",
                False,
            ),
        ],
    ),
    (
        teams,
        teams.TeamsClient,
        [
            (
                "archive_channel",
                "POST",
                "/teams/value/channels/value/archive",
                True,
            ),
            (
                "get_subscription_scope_schema",
                "GET",
                "/internalparameters/triggers/subscriptionscope/value/schema",
                False,
            ),
        ],
    ),
    (
        wdatp,
        wdatp.WdatpClient,
        [
            (
                "advanced_hunting_schema",
                "POST",
                "/api/advancedqueries/schema",
                True,
            ),
        ],
    ),
]


OPERATION_CASES = [
    (connector_module, client_type, *operation_case)
    for connector_module, client_type, operation_cases in CONNECTOR_OPERATION_CASES
    for operation_case in operation_cases
]


CASE_PARAMETER_NAMES = (
    "connector_module,client_type,operation,expected_method,"
    "expected_path,expects_body"
)


@pytest.mark.parametrize(
    CASE_PARAMETER_NAMES,
    OPERATION_CASES,
    ids=[operation_case[2] for operation_case in OPERATION_CASES],
)
@pytest.mark.asyncio
async def test_newly_generated_operation_success_contract(
    connector_module: ModuleType,
    client_type: type[Any],
    operation: str,
    expected_method: str,
    expected_path: str,
    expects_body: bool,
    mock_token_provider: Any,
) -> None:
    """Test a newly generated operation's route, body, and response."""
    client = client_type(
        "https://example.azure.com/connections/test",
        token_provider=mock_token_provider,
    )
    is_pageable = inspect.isasyncgenfunction(getattr(client, f"{operation}_async"))
    response_payload = {"value": [{"id": "item-1"}]} if is_pageable else {"ok": True}

    with patch.object(
        client._http_client,
        "send_async",
        new_callable=AsyncMock,
        return_value=MockResponse(status=200, text=json.dumps(response_payload)),
    ) as mock_send:
        result = await invoke_generated_operation(
            client,
            operation,
            connector_module,
            include_optional_parameters=True,
        )

    method, request_url = mock_send.call_args.args[:2]
    assert method == expected_method
    assert expected_path in request_url
    assert (mock_send.call_args.kwargs["body"] is not None) is expects_body
    assert result == (response_payload["value"] if is_pageable else response_payload)


@pytest.mark.parametrize(
    CASE_PARAMETER_NAMES,
    OPERATION_CASES,
    ids=[operation_case[2] for operation_case in OPERATION_CASES],
)
@pytest.mark.asyncio
async def test_newly_generated_operation_rejects_error_response(
    connector_module: ModuleType,
    client_type: type[Any],
    operation: str,
    expected_method: str,
    expected_path: str,
    expects_body: bool,
    mock_token_provider: Any,
) -> None:
    """Test a newly generated operation raises for an error response."""
    client = client_type(
        "https://example.azure.com/connections/test",
        token_provider=mock_token_provider,
    )

    with patch.object(
        client._http_client,
        "send_async",
        new_callable=AsyncMock,
        return_value=MockResponse(status=400, text="bad request"),
    ):
        with pytest.raises(ConnectorException):
            await invoke_generated_operation(
                client,
                operation,
                connector_module,
            )
