# Copyright (c) Microsoft Corporation. All rights reserved.

"""Catalog-wide contract tests for generated long-running operations."""

from __future__ import annotations

import ast
import importlib
import inspect
from pathlib import Path
from types import ModuleType
from typing import Any, get_args, get_origin, get_type_hints

from azure.core.polling import AsyncLROPoller, LROPoller

import azure.connectors as connectors_package
from azure.connectors.sdk import ConnectorClientBase as SyncConnectorClientBase
from azure.connectors.sdk.aio import ConnectorClientBase as AioConnectorClientBase


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
    base_type: type[Any],
) -> type[Any]:
    """Return the generated client declared by a connector module."""
    client_types = [
        value
        for value in vars(module).values()
        if inspect.isclass(value)
        and issubclass(value, base_type)
        and value is not base_type
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


def test_generated_lro_inventory_and_sync_aio_parity() -> None:
    """Keep the retained 44-operation LRO surface exact across all 99 pairs."""
    assert len(CONNECTOR_MODULE_NAMES) == 99

    for module_name in CONNECTOR_MODULE_NAMES:
        root_module = importlib.import_module(f"azure.connectors.{module_name}")
        aio_module = importlib.import_module(f"azure.connectors.aio.{module_name}")
        root_client = get_generated_client_type(
            root_module,
            SyncConnectorClientBase,
        )
        aio_client = get_generated_client_type(
            aio_module,
            AioConnectorClientBase,
        )
        expected_operations = EXPECTED_LRO_OPERATIONS.get(module_name, set())

        assert get_lro_operations(root_client) == expected_operations, module_name
        assert get_lro_operations(aio_client) == expected_operations, module_name

        for operation_name in expected_operations:
            root_method = getattr(root_client, operation_name)
            aio_method = getattr(aio_client, operation_name)
            root_return = get_type_hints(
                root_method,
                globalns=vars(root_module),
            )["return"]
            aio_return = get_type_hints(
                aio_method,
                globalns=vars(aio_module),
            )["return"]

            assert get_origin(root_return) is LROPoller, operation_name
            assert get_origin(aio_return) is AsyncLROPoller, operation_name
            assert get_args(root_return) == get_args(aio_return), operation_name
            assert not inspect.iscoroutinefunction(root_method), operation_name
            assert inspect.iscoroutinefunction(aio_method), operation_name

    assert sum(map(len, EXPECTED_LRO_OPERATIONS.values())) == 44


def test_generated_lro_operations_use_only_location_polling() -> None:
    """Require every retained poller to use the supported Location protocol."""
    for module_name, expected_operations in EXPECTED_LRO_OPERATIONS.items():
        for package_directory in (
            CONNECTOR_DIRECTORY,
            CONNECTOR_DIRECTORY / "aio",
        ):
            tree = ast.parse(
                (package_directory / f"{module_name}.py").read_text(
                    encoding="utf-8"
                )
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
