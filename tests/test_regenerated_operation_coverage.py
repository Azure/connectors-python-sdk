# Copyright (c) Microsoft Corporation. All rights reserved.

"""Focused HTTP contract tests for newly generated connector operations."""

from __future__ import annotations

import json
from types import ModuleType
from typing import Any, get_origin, get_type_hints
from unittest.mock import AsyncMock, patch
from urllib.parse import urlsplit

import pytest
from azure.core.async_paging import AsyncItemPaged

import azure.connectors.azureautomation as azureautomation
import azure.connectors.azureblob as azureblob
import azure.connectors.azuredatafactory as azuredatafactory
import azure.connectors.azurevm as azurevm
import azure.connectors.excelonlinebusiness as excelonlinebusiness
import azure.connectors.teams as teams
import azure.connectors.wdatp as wdatp
from azure.connectors.aio.azureautomation import AzureautomationClient
from azure.connectors.aio.azureblob import AzureblobClient
from azure.connectors.aio.azuredatafactory import AzuredatafactoryClient
from azure.connectors.aio.azurevm import AzurevmClient
from azure.connectors.aio.excelonlinebusiness import ExcelonlinebusinessClient
from azure.connectors.aio.teams import TeamsClient
from azure.connectors.aio.wdatp import WdatpClient
from azure.connectors.sdk import ConnectorException
from tests.conftest import MockResponse
from tests.generated_connector_test_utils import (
    generated_pager_response_text,
    invoke_generated_operation,
)


CONNECTOR_OPERATION_CASES = [
    (
        azureautomation,
        AzureautomationClient,
        [
            ("list_subscriptions", "GET", "/subscriptions?", False),
            ("list_resource_groups", "GET", "/resourcegroups?", False),
            ("list_automation_accounts", "GET", "/automationAccounts?", False),
            ("list_runbooks", "GET", "/runbooks?", False),
            ("list_runbook", "GET", "/runbooks/value?", False),
        ],
    ),
    (
        azureblob,
        AzureblobClient,
        [("list_data_sets", "GET", "/v2/codeless/GetDataSets", False)],
    ),
    (
        azuredatafactory,
        AzuredatafactoryClient,
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
        AzurevmClient,
        [
            ("list_subscriptions", "GET", "/subscriptions?", False),
            ("list_resource_groups", "GET", "/resourcegroups?", False),
            (
                "list_virtual_machine_scale_sets",
                "GET",
                "/virtualMachineScaleSets?",
                False,
            ),
            (
                "list_virtual_machines_in_scale_set",
                "GET",
                "/virtualMachineScaleSets/value/virtualMachines?",
                False,
            ),
            (
                "list_virtual_machines",
                "GET",
                "/Microsoft.Compute/virtualMachines?",
                False,
            ),
        ],
    ),
    (
        excelonlinebusiness,
        ExcelonlinebusinessClient,
        [
            ("list_sources", "GET", "/codeless/v1.0/sources?", False),
            ("list_drives", "GET", "/codeless/v1.0/drives?", False),
            ("list_columns", "GET", "/workbook/tables/value/columns?", False),
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
        TeamsClient,
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
        WdatpClient,
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

EXPECTED_PAGEABLE_OPERATIONS = {
    (AzureautomationClient, "list_subscriptions"),
    (AzureautomationClient, "list_resource_groups"),
    (AzureautomationClient, "list_automation_accounts"),
    (AzureautomationClient, "list_runbooks"),
    (AzureautomationClient, "list_runbook"),
    (AzureblobClient, "list_data_sets"),
    (AzuredatafactoryClient, "list_subscriptions"),
    (AzuredatafactoryClient, "list_resource_groups"),
    (AzuredatafactoryClient, "list_data_factories"),
    (AzuredatafactoryClient, "list_pipelines"),
    (AzurevmClient, "list_subscriptions"),
    (AzurevmClient, "list_resource_groups"),
    (AzurevmClient, "list_virtual_machine_scale_sets"),
    (AzurevmClient, "list_virtual_machines_in_scale_set"),
    (AzurevmClient, "list_virtual_machines"),
    (ExcelonlinebusinessClient, "list_sources"),
    (ExcelonlinebusinessClient, "list_drives"),
    (ExcelonlinebusinessClient, "list_columns"),
}

CONTINUATION_PAGEABLE_OPERATIONS = {
    (AzureautomationClient, "list_subscriptions"),
    (AzureautomationClient, "list_resource_groups"),
    (AzuredatafactoryClient, "list_subscriptions"),
    (AzuredatafactoryClient, "list_resource_groups"),
    (AzuredatafactoryClient, "list_data_factories"),
    (AzuredatafactoryClient, "list_pipelines"),
    (AzurevmClient, "list_subscriptions"),
    (AzurevmClient, "list_resource_groups"),
    (AzurevmClient, "list_virtual_machine_scale_sets"),
    (AzurevmClient, "list_virtual_machines_in_scale_set"),
    (AzurevmClient, "list_virtual_machines"),
}

PAGEABLE_OPERATION_CASES = [
    operation_case for operation_case in OPERATION_CASES
    if (operation_case[1], operation_case[2]) in EXPECTED_PAGEABLE_OPERATIONS
]

CONTINUATION_PAGEABLE_OPERATION_CASES = [
    operation_case for operation_case in OPERATION_CASES
    if (operation_case[1], operation_case[2]) in CONTINUATION_PAGEABLE_OPERATIONS
]


def test_expected_pageable_operations_remain_iterator_contracts() -> None:
    """Test every declared pageable operation returns an asynchronous pager."""
    assert {(case[1], case[2]) for case in PAGEABLE_OPERATION_CASES} == EXPECTED_PAGEABLE_OPERATIONS
    assert len(PAGEABLE_OPERATION_CASES) == 18
    for client_type, operation in EXPECTED_PAGEABLE_OPERATIONS:
        return_type = get_type_hints(getattr(client_type, operation))["return"]
        assert get_origin(return_type) is AsyncItemPaged, operation


@pytest.mark.parametrize("empty_first_page", [False, True])
@pytest.mark.parametrize(
    CASE_PARAMETER_NAMES,
    CONTINUATION_PAGEABLE_OPERATION_CASES,
    ids=[
        f"{case[0].__name__}.{case[2]}"
        for case in CONTINUATION_PAGEABLE_OPERATION_CASES
    ],
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
    mock_credential: Any,
) -> None:
    """Test concrete ARM value/nextLink contracts through each generated operation."""
    first_items = [] if empty_first_page else [{"id": "item-1", "name": "First"}]
    last_items = [{"id": "item-2", "details": {"name": "Second"}}]
    continuation_path = urlsplit(expected_path).path + "?$skiptoken=page-2"
    async with client_type(
        "https://example.azure.com/connections/test",
        credential=mock_credential,
    ) as client:
        with patch.object(
            client._http_client,
            "send",
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
        assert transport.await_args_list[1].kwargs == {
            "body": None,
            "timeout": None,
            "headers": None,
            "client_request_id": None,
            "response_hook": None,
        }


@pytest.mark.asyncio
async def test_relative_continuation_resolves_against_current_page(
    mock_credential: Any,
) -> None:
    """Test a bare relative continuation keeps the current nested route."""
    async with AzurevmClient(
        "https://example.azure.com/connections/test",
        credential=mock_credential,
    ) as client:
        with patch.object(
            client._http_client,
            "send",
            new_callable=AsyncMock,
            side_effect=[
                MockResponse(
                    status=200,
                    text=json.dumps({"value": [], "nextLink": "next-page"}),
                ),
                MockResponse(
                    status=200,
                    text=json.dumps({"value": [{"id": "vm-2"}]}),
                ),
            ],
        ) as transport:
            items = [
                item async for item in client.list_virtual_machines_in_scale_set(
                    subscription_id="subscription",
                    resource_group_name="group",
                    virtual_machine_scale_set_name="scale-set",
                )
            ]

    assert items == [{"id": "vm-2"}]
    assert transport.await_args_list[1].args == (
        "GET",
        "https://example.azure.com/connections/test/subscriptions/subscription/"
        "resourcegroups/group/providers/Microsoft.Compute/virtualMachineScaleSets/"
        "scale-set/next-page",
    )


@pytest.mark.parametrize("status,body", [(200, ""), (200, '{"value": []}'), (204, "")])
@pytest.mark.parametrize(
    CASE_PARAMETER_NAMES,
    CONTINUATION_PAGEABLE_OPERATION_CASES,
    ids=[
        f"{case[0].__name__}.{case[2]}"
        for case in CONTINUATION_PAGEABLE_OPERATION_CASES
    ],
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
    mock_credential: Any,
) -> None:
    """Test no-content responses terminate without a spurious continuation request."""
    async with client_type(
        "https://example.azure.com/connections/test",
        credential=mock_credential,
    ) as client:
        with patch.object(
            client._http_client,
            "send",
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
    mock_credential: Any,
) -> None:
    """Test a newly generated operation's route, body, and response."""
    client = client_type(
        "https://example.azure.com/connections/test",
        credential=mock_credential,
    )
    is_pageable = (client_type, operation) in EXPECTED_PAGEABLE_OPERATIONS
    response_text = (
        generated_pager_response_text(getattr(client_type, operation))
        if is_pageable
        else '{"ok": true}'
    )

    with patch.object(
        client._http_client,
        "send",
        new_callable=AsyncMock,
        return_value=MockResponse(status=200, text=response_text),
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
    assert result == ([{"ok": True}] if is_pageable else {"ok": True})


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
    mock_credential: Any,
) -> None:
    """Test a newly generated operation raises for an error response."""
    client = client_type(
        "https://example.azure.com/connections/test",
        credential=mock_credential,
    )

    with patch.object(
        client._http_client,
        "send",
        new_callable=AsyncMock,
        return_value=MockResponse(status=400, text="bad request"),
    ):
        with pytest.raises(ConnectorException):
            await invoke_generated_operation(
                client,
                operation,
                connector_module,
            )
