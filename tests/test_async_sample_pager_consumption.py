# ------------------------------------------------------------
# Copyright (c) Microsoft Corporation.  All rights reserved.
# ------------------------------------------------------------

"""Execute asynchronous sample consumers against real, multi-page AsyncItemPaged values."""

from __future__ import annotations

import ast
import importlib.util
import inspect
import re
from functools import lru_cache
from pathlib import Path
from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest
from azure.core.async_paging import AsyncItemPaged

ROOT = Path(__file__).resolve().parent.parent
SAMPLES = ROOT / "samples" / "sample_connector_usage"


def top_level_imports(tree: ast.Module) -> list[ast.ImportFrom]:
    """Find imports under module-level guards without entering local scopes."""
    imports = []
    pending = list(tree.body)
    while pending:
        node = pending.pop()
        if isinstance(node, ast.ImportFrom):
            imports.append(node)
            continue
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            continue
        pending.extend(ast.iter_child_nodes(node))
    return imports


@lru_cache(maxsize=None)
def pageable_methods(sample_path: Path) -> dict[str, set[str]]:
    """Resolve imported async clients' pageable methods from generated annotations."""
    clients = {}
    tree = ast.parse(sample_path.read_text(encoding="utf-8-sig"))
    for node in top_level_imports(tree):
        if not node.module:
            continue
        if not node.module.startswith("azure.connectors."):
            continue
        if node.module.startswith("azure.connectors.sdk"):
            continue
        source_path = ROOT / "src" / Path(*node.module.split(".")).with_suffix(".py")
        source = ast.parse(source_path.read_text(encoding="utf-8-sig"))
        for alias in node.names:
            for declaration in source.body:
                if not isinstance(declaration, ast.ClassDef):
                    continue
                if declaration.name != alias.name:
                    continue
                clients[alias.asname or alias.name] = {
                    method.name
                    for method in declaration.body
                    if isinstance(method, (ast.FunctionDef, ast.AsyncFunctionDef))
                    and method.returns is not None
                    and "AsyncItemPaged" in ast.unparse(method.returns)
                }
    return clients


def sample_cases() -> list[tuple[Path, str, str, tuple[str, ...]]]:
    """Discover all actual sample functions calling generated pageable operations."""
    cases = []
    for sample_path in sorted(SAMPLES.glob("sample_connector_usage_*.py")):
        tree = ast.parse(sample_path.read_text(encoding="utf-8-sig"))
        for client_name, operations in pageable_methods(sample_path).items():
            for function in tree.body:
                if not isinstance(function, ast.AsyncFunctionDef):
                    continue
                called_operations = {
                    node.func.attr
                    for node in ast.walk(function)
                    if isinstance(node, ast.Call)
                    and isinstance(node.func, ast.Attribute)
                    and node.func.attr in operations
                }
                if called_operations:
                    if sample_path.stem == "sample_connector_usage_azureblob":
                        for operation in sorted(called_operations):
                            cases.append((
                                sample_path, client_name, function.name, (operation,),
                            ))
                    else:
                        cases.append((
                            sample_path, client_name, function.name,
                            tuple(sorted(called_operations)),
                        ))
    return cases


CASES = sample_cases()


def test_sharepoint_pageable_call_sites_are_discovered() -> None:
    """Prove imports under SharePoint's top-level try block remain in the sweep."""
    discovered = {
        (sample_path.stem, function_name, operation)
        for sample_path, _, function_name, operations in CASES
        for operation in operations
    }
    assert (
        "sample_connector_usage_sharepoint",
        "example_1_get_lists",
        "list_tables",
    ) in discovered
    assert (
        "sample_connector_usage_sharepoint",
        "example_6_file_operations",
        "list_root_folder",
    ) in discovered
    assert (
        "sample_connector_usage_sharepoint",
        "example_6_file_operations",
        "list_folder",
    ) in discovered


def load_sample(sample_path: Path) -> Any:
    """Load the actual worktree sample independently of other tests' module caches."""
    specification = importlib.util.spec_from_file_location(
        f"async_pager_review_{sample_path.stem}", sample_path,
    )
    assert specification is not None and specification.loader is not None
    module = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(module)
    return module


def configure_sample(
    module: Any, sample_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> MagicMock:
    """Supply async context managers and local configuration without live I/O."""
    tree = ast.parse(sample_path.read_text(encoding="utf-8-sig"))
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call) or not isinstance(node.func, ast.Attribute):
            continue
        if node.func.attr not in {"get", "getenv"} or not node.args:
            continue
        if ast.unparse(node.func.value) not in {"os", "os.environ"}:
            continue
        if isinstance(node.args[0], ast.Constant):
            monkeypatch.setenv(node.args[0].value, "sample-value")
    for name, value in vars(module).copy().items():
        if name.isupper() and isinstance(value, str):
            monkeypatch.setattr(module, name, "sample-value")
    credential = MagicMock()
    credential.__aenter__.return_value = credential
    monkeypatch.setattr(module, "DefaultAzureCredential", MagicMock(return_value=credential))
    client = MagicMock()
    client.__aenter__.return_value = client
    return client


def sample_item(tree: ast.Module, index: int) -> dict[str, Any]:
    """Provide recognizable values for the actual sample display fields."""
    marker = f"pager-review-item-{index}"
    item = {
        node.args[0].value: marker
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr == "get"
        and node.args
        and isinstance(node.args[0], ast.Constant)
        and isinstance(node.args[0].value, str)
    }
    item.update({
        "id": marker, "name": marker, "Name": marker, "contentData": marker,
        "fields": {"summary": marker}, "EmailAddresses": [{"Address": marker}],
        "lockToken": marker, "subscriptionPolicies": {"quotaId": marker},
    })
    return item


def create_pager(items: list[Any], visits: list[str | None]) -> AsyncItemPaged[Any]:
    """Include empty initial and intermediate pages before final-page termination."""
    pages = {
        None: ("first-items", []),
        "first-items": ("empty-middle", items[:1]),
        "empty-middle": ("last-items", []),
        "last-items": (None, items[1:]),
    }

    async def get_next(continuation: str | None) -> tuple[str | None, list[Any]]:
        """Record every lazy page request, including requests after empty pages."""
        visits.append(continuation)
        return pages[continuation]

    async def extract_data(page: tuple[str | None, list[Any]]) -> tuple[str | None, list[Any]]:
        """Expose the continuation and flattened item sequence to Azure Core."""
        return page

    return AsyncItemPaged(get_next, extract_data)


@pytest.mark.parametrize("item_count", [0, 2])
@pytest.mark.parametrize(
    "sample_path,client_name,function_name,operations", CASES,
    ids=[f"{case[0].stem}-{case[2]}-{'-'.join(case[3])}" for case in CASES],
)
@pytest.mark.asyncio
async def test_async_sample_consumes_pages_and_reports_items(
    sample_path: Path,
    client_name: str,
    function_name: str,
    operations: tuple[str, ...],
    item_count: int,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Exercise real sample functions, including populated results after empty pages."""
    module = load_sample(sample_path)
    client = configure_sample(module, sample_path, monkeypatch)
    if sample_path.stem == "sample_connector_usage_azureblob":
        monkeypatch.setenv(
            "TEST_FOLDER_ID", "" if operations == ("list_root_folder",) else "sample-value",
        )
    tree = ast.parse(sample_path.read_text(encoding="utf-8-sig"))
    generated_client = getattr(module, client_name)
    all_operations = pageable_methods(sample_path)[client_name]
    page_visits: list[list[str | None]] = []

    def pager_for_operation(operation: str) -> AsyncItemPaged[Any]:
        """Create a fresh real pager for each invocation, not an awaitable mock."""
        visits: list[str | None] = []
        page_visits.append(visits)
        items = [
            f"pager-review-item-{index}"
            if operation == "list_file_tags" else sample_item(tree, index)
            for index in range(item_count)
        ]
        return create_pager(items, visits)

    for name, member in inspect.getmembers(generated_client, inspect.isfunction):
        if name.startswith("_"):
            continue
        if name in all_operations:
            getattr(client, name).side_effect = (
                lambda *args, operation=name, **kwargs: pager_for_operation(operation)
            )
        elif inspect.iscoroutinefunction(member):
            setattr(client, name, AsyncMock(return_value={}))
    monkeypatch.setattr(module, client_name, MagicMock(return_value=client))
    function = getattr(module, function_name)
    arguments = {
        name: "sample-value"
        for name, parameter in inspect.signature(function).parameters.items()
        if parameter.default is inspect.Parameter.empty
    }

    await function(**arguments)

    output = capsys.readouterr().out
    assert "error" not in output.casefold(), output
    assert "AsyncItemPaged object" not in output, output
    for operation in operations:
        assert getattr(client, operation).called, operation
    assert page_visits, output
    assert all(
        visits == [None, "first-items", "empty-middle", "last-items"]
        for visits in page_visits
    ), page_visits
    body = "\n".join(
        line for line in output.splitlines() if not line.startswith("===")
    )
    if item_count:
        assert (
            "pager-review-item-0" in body
            or re.search(r"\b2\b", body)
            or body.count("[REDACTED]") == 2
        ), output
        if sample_path.stem in {
            "sample_connector_usage_office365", "sample_connector_usage_office365users",
        }:
            assert "pager-review-item-1" in body, output
    else:
        assert "pager-review-item-" not in body
        assert re.search(r"\b0\b|\bno\b|empty|\[\]", body, re.IGNORECASE), output
    if sample_path.stem == "sample_connector_usage_rss":
        assert f"Retrieved {item_count} item(s)" in body
        assert f"Polling query returned {item_count} item(s)." in body


def test_all_async_pageable_call_sites_are_explicitly_consumed() -> None:
    """Sweep every sample using generated return types, not operation-name guesses."""
    paths = sorted(SAMPLES.glob("sample_connector_usage_*.py"))
    assert len(paths) == 99
    pageable_sample_count = 0
    call_count = 0
    for sample_path in paths:
        tree = ast.parse(sample_path.read_text(encoding="utf-8-sig"))
        clients = pageable_methods(sample_path)
        operations = set().union(*clients.values()) if clients else set()
        parents = {
            child: node for node in ast.walk(tree) for child in ast.iter_child_nodes(node)
        }
        calls = [
            node for node in ast.walk(tree)
            if isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and node.func.attr in operations
        ]
        pageable_sample_count += bool(calls)
        call_count += len(calls)
        for call in calls:
            parent = parents[call]
            assert (
                isinstance(parent, ast.comprehension)
                and parent.is_async
                and parent.iter is call
            ) or (
                isinstance(parent, ast.AsyncFor) and parent.iter is call
            ), (sample_path.name, call.lineno, ast.unparse(call))
    assert pageable_sample_count == 75
    assert call_count == 152


@pytest.mark.parametrize("response", [None, {}, {"value": [{"id": "created"}]}])
@pytest.mark.asyncio
async def test_excel_mutation_responses_remain_eager_envelopes(
    response: dict[str, Any] | None,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Keep nullable mutation responses awaited and intact, not flattened as pagers."""
    sample_path = SAMPLES / "sample_connector_usage_excelonline.py"
    module = load_sample(sample_path)
    client = configure_sample(module, sample_path, monkeypatch)
    client.list_all_worksheets.side_effect = lambda **kwargs: create_pager([], [])
    client.list_tables.side_effect = lambda **kwargs: create_pager([], [])
    client.create_worksheet = AsyncMock(return_value=response)
    client.add_row = AsyncMock(return_value=response)
    monkeypatch.setattr(module, "ExcelonlineClient", MagicMock(return_value=client))

    await module.main()

    output = capsys.readouterr().out
    assert f"created worksheet {response}" in output
    assert f"added row {response}" in output
    assert "error" not in output.casefold()
    client.create_worksheet.assert_awaited_once()
    client.add_row.assert_awaited_once()
