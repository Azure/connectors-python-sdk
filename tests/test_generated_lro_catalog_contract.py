# Copyright (c) Microsoft Corporation. All rights reserved.

"""Catalog-wide contract tests for generated long-running operations."""

from __future__ import annotations

import ast
import importlib
import inspect
from pathlib import Path
from types import ModuleType
from typing import Any, get_args, get_origin, get_type_hints
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from azure.core.polling import AsyncLROPoller

import azure.connectors as connectors_package
from azure.connectors.sdk import ConnectorClientBase, ConnectorException
from tests.conftest import MockResponse
from tests.generated_connector_test_utils import (
    get_generated_operations,
    invoke_generated_operation,
)


EXPECTED_LRO_OPERATIONS = {
    "kusto": {
        "begin_list_kusto_results",
        "begin_list_kusto_show_command_results",
        "begin_run_async_control_command_and_wait",
        "begin_run_kusto_command_and_visualize_results",
        "begin_run_kusto_query_and_visualize_results",
    },
    "plumsail": {
        "begin_flow_v1_documents_jobs_add_watermark_to_pdf",
        "begin_flow_v1_documents_jobs_any2_pdf_v2",
        "begin_flow_v1_documents_jobs_apply_docx",
        "begin_flow_v1_documents_jobs_apply_docx_template",
        "begin_flow_v1_documents_jobs_apply_html",
        "begin_flow_v1_documents_jobs_apply_pptx",
        "begin_flow_v1_documents_jobs_apply_xlsx_template",
        "begin_flow_v1_documents_jobs_compress_pdf",
        "begin_flow_v1_documents_jobs_create_archive",
        "begin_flow_v1_documents_jobs_csv2_xlsx",
        "begin_flow_v1_documents_jobs_doc2_docx",
        "begin_flow_v1_documents_jobs_docx2_pdf",
        "begin_flow_v1_documents_jobs_email2_pdf",
        "begin_flow_v1_documents_jobs_extract_archive",
        "begin_flow_v1_documents_jobs_extract_text_from_pdf",
        "begin_flow_v1_documents_jobs_fill_in_pdf_form",
        "begin_flow_v1_documents_jobs_get_pdf_form",
        "begin_flow_v1_documents_jobs_get_pdf_protection_info",
        "begin_flow_v1_documents_jobs_html2_docx",
        "begin_flow_v1_documents_jobs_html2_pdf",
        "begin_flow_v1_documents_jobs_image2_pdf",
        "begin_flow_v1_documents_jobs_json2_csv",
        "begin_flow_v1_documents_jobs_json2_xlsx",
        "begin_flow_v1_documents_jobs_merge_any_to_pdf_v2",
        "begin_flow_v1_documents_jobs_merge_docx",
        "begin_flow_v1_documents_jobs_merge_xlsx",
        "begin_flow_v1_documents_jobs_parse_csv",
        "begin_flow_v1_documents_jobs_pdf2_image_v2",
        "begin_flow_v1_documents_jobs_ppt2_pptx",
        "begin_flow_v1_documents_jobs_pptx2_pdf",
        "begin_flow_v1_documents_jobs_protect_pdf",
        "begin_flow_v1_documents_jobs_reg_exp_match",
        "begin_flow_v1_documents_jobs_reg_exp_replace",
        "begin_flow_v1_documents_jobs_reg_exp_test",
        "begin_flow_v1_documents_jobs_split_pdf_v2",
        "begin_flow_v1_documents_jobs_xls2_xlsx",
        "begin_flow_v1_documents_jobs_xslx2_pdf",
        "begin_flow_v1_processes_flow_jobs_execute_process",
        "begin_flow_v1_processes_flow_jobs_execute_process_with_generated_data",
    },
}


assert connectors_package.__file__ is not None
CONNECTOR_DIRECTORY = Path(connectors_package.__file__).parent
CONNECTOR_MODULE_NAMES = sorted(
    path.stem
    for path in CONNECTOR_DIRECTORY.glob("*.py")
    if path.name != "__init__.py" and not path.name.startswith("_")
)


def get_generated_client_type(
    module: ModuleType,
) -> type[Any]:
    """Return the generated client declared by a connector module."""
    client_types = [
        value
        for value in vars(module).values()
        if inspect.isclass(value)
        and issubclass(value, ConnectorClientBase)
        and value is not ConnectorClientBase
        and value.__module__ == module.__name__
    ]
    assert len(client_types) == 1, module.__name__
    return client_types[0]


def get_lro_operations(client_type: type[Any]) -> set[str]:
    """Return generated begin methods declared by a connector client."""
    return {
        name
        for name, member in vars(client_type).items()
        if name.startswith("begin_") and callable(member)
    }


def test_generated_lro_inventory_uses_async_root_pollers() -> None:
    """Keep the retained 44-operation LRO surface exact across all 101 clients."""
    assert len(CONNECTOR_MODULE_NAMES) == 101

    for module_name in CONNECTOR_MODULE_NAMES:
        root_module = importlib.import_module(f"azure.connectors.{module_name}")
        root_client = get_generated_client_type(root_module)
        expected_operations = EXPECTED_LRO_OPERATIONS.get(module_name, set())

        assert get_lro_operations(root_client) == expected_operations, module_name

        for operation_name in expected_operations:
            root_method = getattr(root_client, operation_name)
            root_return = get_type_hints(
                root_method,
                globalns=vars(root_module),
            )["return"]
            assert get_origin(root_return) is AsyncLROPoller, operation_name
            assert len(get_args(root_return)) == 1, operation_name
            assert inspect.iscoroutinefunction(root_method), operation_name
            assert operation_name.removeprefix("begin_") not in get_generated_operations(
                root_client
            ), operation_name

    assert sum(map(len, EXPECTED_LRO_OPERATIONS.values())) == 44


def test_generated_lro_operations_use_only_location_polling() -> None:
    """Require every retained poller to use the supported Location protocol."""
    for module_name, expected_operations in EXPECTED_LRO_OPERATIONS.items():
        tree = ast.parse(
            (CONNECTOR_DIRECTORY / f"{module_name}.py").read_text(encoding="utf-8")
        )
        actual_headers = {}
        for node in ast.walk(tree):
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            if node.name not in expected_operations:
                continue
            for child in ast.walk(node):
                if not isinstance(child, ast.Call):
                    continue
                if not isinstance(child.func, ast.Name):
                    continue
                if child.func.id != "ConnectorPollingMethod":
                    continue
                header_keyword = next(
                    keyword
                    for keyword in child.keywords
                    if keyword.arg == "polling_header_name"
                )
                assert isinstance(header_keyword.value, ast.Constant)
                actual_headers[node.name] = header_keyword.value.value

        assert set(actual_headers) == expected_operations
        assert all(
            isinstance(header, str) and header.casefold() == "location"
            for header in actual_headers.values()
        )


@pytest.mark.parametrize("terminal_status", [200, 400])
@pytest.mark.parametrize(
    "module_name,operation_name",
    [
        (module_name, operation_name)
        for module_name, operations in EXPECTED_LRO_OPERATIONS.items()
        for operation_name in sorted(operations)
    ],
)
@pytest.mark.asyncio
async def test_generated_lro_follows_location_and_preserves_controls(
    module_name: str,
    operation_name: str,
    terminal_status: int,
    mock_credential: Any,
) -> None:
    """Await each root LRO through polling, deserialization, and terminal errors."""
    module = importlib.import_module(f"azure.connectors.{module_name}")
    client_type = get_generated_client_type(module)
    response_hook = MagicMock()
    controls = {
        "timeout": 5.0,
        "headers": {"x-test": "value"},
        "client_request_id": "request-id",
        "response_hook": response_hook,
    }
    async with client_type(
        "https://example.azure.com/connections/test",
        credential=mock_credential,
    ) as client:
        with patch.object(
            client._http_client,
            "send",
            new_callable=AsyncMock,
            side_effect=[
                MockResponse(
                    status=202,
                    headers={
                        "Location": "https://backend.example/jobs/42",
                        "Retry-After": "0",
                    },
                ),
                MockResponse(status=terminal_status, text='{"ok": true}'),
            ],
        ) as send, patch(
            "azure.connectors.sdk.polling.asyncio.sleep",
            new_callable=AsyncMock,
        ):
            if terminal_status == 400:
                with pytest.raises(ConnectorException):
                    await invoke_generated_operation(
                        client, operation_name, module, request_controls=controls,
                    )
            else:
                result = await invoke_generated_operation(
                    client, operation_name, module, request_controls=controls,
                )
                return_type = get_type_hints(getattr(client_type, operation_name))["return"]
                result_type = get_args(return_type)[0]
                if result_type is bytes:
                    assert result == b'{"ok": true}'
                elif result_type is type(None):
                    assert result is None
                else:
                    assert result == {"ok": True}

        assert send.await_count == send.call_count == 2
        assert send.await_args_list[1].args == (
            "GET", "https://example.azure.com/connections/test/jobs/42",
        )
        assert send.await_args_list[1].kwargs["body"] is None
        for call in send.await_args_list:
            for name, value in controls.items():
                assert call.kwargs[name] == value, (operation_name, name)
