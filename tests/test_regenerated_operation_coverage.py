# Copyright (c) Microsoft Corporation. All rights reserved.

"""Focused HTTP contract tests for newly generated connector operations."""

from __future__ import annotations

import inspect
import json
from types import ModuleType
from typing import Any
from unittest.mock import AsyncMock, patch
from urllib.parse import urlsplit

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

PAGEABLE_OPERATION_CASES = [
    operation_case for operation_case in OPERATION_CASES
    if inspect.isasyncgenfunction(getattr(operation_case[1], f"{operation_case[2]}_async"))
]


@pytest.mark.parametrize("empty_first_page", [False, True])
@pytest.mark.parametrize(
    CASE_PARAMETER_NAMES,
    PAGEABLE_OPERATION_CASES,
    ids=[f"{case[0].__name__}.{case[2]}" for case in PAGEABLE_OPERATION_CASES],
)
@pytest.mark.asyncio
async def test_newly_generated_pageable_contract_follows_later_pages(
    connector_module: ModuleType,
    client_type: type[Any],
    operation: str,
    expected_method: str,
    expected_path: str,
    expects_body: bool,
    empty_first_page: bool,
    mock_token_provider: Any,
) -> None:
    """Test concrete ARM value/nextLink contracts through each generated operation."""
    first_items = [] if empty_first_page else [{"id": "item-1", "name": "First"}]
    last_items = [{"id": "item-2", "details": {"name": "Second"}}]
    continuation_path = urlsplit(expected_path).path + "?$skiptoken=page-2"
    async with client_type(
        "https://example.azure.com/connections/test",
        token_provider=mock_token_provider,
    ) as client:
        with patch.object(
            client._http_client,
            "send_async",
            new_callable=AsyncMock,
            side_effect=[
                MockResponse(status=200, text=json.dumps({
                    "value": first_items,
                    "nextLink": "https://management.azure.com" + continuation_path,
                })),
                MockResponse(status=200, text=json.dumps({"value": last_items, "nextLink": None})),
            ],
        ) as transport:
            items = await invoke_generated_operation(
                client, operation, connector_module, include_optional_parameters=True,
            )

        assert items == first_items + last_items
        assert transport.await_count == 2
        assert transport.await_args_list[0].args[0] == expected_method
        assert expected_path in transport.await_args_list[0].args[1]
        assert transport.await_args_list[1].args == (
            "GET", "https://example.azure.com/connections/test" + continuation_path,
        )
        assert (transport.await_args_list[0].kwargs["body"] is not None) is expects_body
        assert transport.await_args_list[1].kwargs == {"body": None}


@pytest.mark.parametrize("status,body", [(200, ""), (200, '{"value": []}'), (204, "")])
@pytest.mark.parametrize(
    CASE_PARAMETER_NAMES,
    PAGEABLE_OPERATION_CASES,
    ids=[f"{case[0].__name__}.{case[2]}" for case in PAGEABLE_OPERATION_CASES],
)
@pytest.mark.asyncio
async def test_newly_generated_pageable_contract_preserves_empty_response(
    connector_module: ModuleType,
    client_type: type[Any],
    operation: str,
    expected_method: str,
    expected_path: str,
    expects_body: bool,
    status: int,
    body: str,
    mock_token_provider: Any,
) -> None:
    """Test no-content responses terminate without a spurious continuation request."""
    async with client_type(
        "https://example.azure.com/connections/test",
        token_provider=mock_token_provider,
    ) as client:
        with patch.object(
            client._http_client,
            "send_async",
            new_callable=AsyncMock,
            return_value=MockResponse(status=status, text=body),
        ) as transport:
            items = await invoke_generated_operation(client, operation, connector_module)

        assert items == []
        transport.assert_awaited_once()
        assert transport.await_args.args[0] == expected_method
        assert expected_path in transport.await_args.args[1]


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
