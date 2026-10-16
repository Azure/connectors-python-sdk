# ------------------------------------------------------------
# Copyright (c) Microsoft Corporation.  All rights reserved.
# ------------------------------------------------------------

"""Execute synchronous sample consumers against real, multi-page ItemPaged values."""

from __future__ import annotations

import ast
import importlib.util
import inspect
import re
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock

import pytest
from azure.core.paging import ItemPaged

ROOT = Path(__file__).resolve().parent.parent
SAMPLES = ROOT / "samples" / "sample_connector_usage"
FIXED_CONNECTORS = set("""
azureeventgrid azurequeues box campfire commondataservice docusign docuware
dropbox dynamicsax eventbrite eventhubs excelonline excelonlinebusiness ftp
github googlecalendar googledrive googletasks impexium infusionsoft insightly
jedoxodatahub jira keyvault mailchimp meetingroommap microsoftbookings
microsoftforms msgraphgroupsanduser office365 office365groups office365groupsmail
office365users onedrive onedriveforbusiness onenote outlook pipedrive plivo
powerbi projectplace rss sendgrid servicebus signinghub sql starrezrestv1 todo
trello twitter typeform universalprint waywedo webex wordpress yammer zendesk
zohosign
""".split())


def pageable_methods(tree: ast.Module) -> dict[str, set[str]]:
    """Resolve imported clients' pageable methods from their generated annotations."""
    clients = {}
    for node in tree.body:
        if not isinstance(node, ast.ImportFrom) or not node.module:
            continue
        if not node.module.startswith("azure.connectors."):
            continue
        source_path = ROOT / "src" / Path(*node.module.split(".")).with_suffix(".py")
        if not source_path.is_file():
            continue
        source = ast.parse(source_path.read_text(encoding="utf-8-sig"))
        for alias in node.names:
            for declaration in source.body:
                if not isinstance(declaration, ast.ClassDef):
                    continue
                if declaration.name != alias.name:
                    continue
                operations = {
                    method.name
                    for method in declaration.body
                    if isinstance(method, ast.FunctionDef)
                    and method.returns is not None
                    and "ItemPaged" in ast.unparse(method.returns)
                }
                if operations:
                    clients[alias.asname or alias.name] = operations
    return clients


def sample_cases() -> list[tuple[Path, str, str, tuple[str, ...]]]:
    """Discover affected functions without importing or executing sample code."""
    cases = []
    for connector in sorted(FIXED_CONNECTORS):
        sample_path = SAMPLES / f"sample_connector_usage_{connector}.py"
        tree = ast.parse(sample_path.read_text(encoding="utf-8-sig"))
        for client_name, operations in pageable_methods(tree).items():
            for function in tree.body:
                if not isinstance(function, ast.FunctionDef):
                    continue
                called_operations = {
                    node.func.attr
                    for node in ast.walk(function)
                    if isinstance(node, ast.Call)
                    and isinstance(node.func, ast.Attribute)
                    and node.func.attr in operations
                }
                if called_operations:
                    cases.append((
                        sample_path, client_name, function.name,
                        tuple(sorted(called_operations)),
                    ))
    return cases


CASES = sample_cases()


def load_sample(sample_path: Path) -> Any:
    """Load the actual worktree sample independently of other tests' module caches."""
    specification = importlib.util.spec_from_file_location(
        f"pager_review_{sample_path.stem}", sample_path,
    )
    assert specification is not None and specification.loader is not None
    module = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(module)
    return module


def configure_sample(
    module: Any, sample_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> MagicMock:
    """Supply local configuration and a mock client, never live credentials or I/O."""
    tree = ast.parse(sample_path.read_text(encoding="utf-8-sig"))
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call) or not isinstance(node.func, ast.Attribute):
            continue
        if node.func.attr not in {"get", "getenv"} or not node.args:
            continue
        receiver = ast.unparse(node.func.value)
        if receiver not in {"os", "os.environ"}:
            continue
        if isinstance(node.args[0], ast.Constant):
            monkeypatch.setenv(node.args[0].value, "sample-value")
    for name, value in vars(module).copy().items():
        if name.isupper() and isinstance(value, str):
            monkeypatch.setattr(module, name, "sample-value")
    monkeypatch.setattr(module, "DefaultAzureCredential", MagicMock())
    client = MagicMock()
    client.__enter__.return_value = client
    return client


def sample_item(tree: ast.Module, index: int) -> dict[str, Any]:
    """Provide recognizable values for the different sample display fields."""
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
        "lockToken": marker,
    })
    return item


@pytest.mark.parametrize("item_count", [0, 2])
@pytest.mark.parametrize(
    "sample_path,client_name,function_name,operations", CASES,
    ids=[f"{case[0].stem}-{case[2]}" for case in CASES],
)
def test_sync_sample_consumes_pages_and_reports_items(
    sample_path: Path,
    client_name: str,
    function_name: str,
    operations: tuple[str, ...],
    item_count: int,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Exercise actual functions, empty first pages, later items, and termination."""
    module = load_sample(sample_path)
    client = configure_sample(module, sample_path, monkeypatch)
    tree = ast.parse(sample_path.read_text(encoding="utf-8-sig"))
    generated_client = getattr(module, client_name)
    all_operations = pageable_methods(tree)[client_name]
    page_visits: list[list[str | None]] = []

    def create_pager(operation: str) -> ItemPaged[Any]:
        """Return a fresh pager with an empty first page and a final second page."""
        visits: list[str | None] = []
        page_visits.append(visits)
        items = [
            f"pager-review-item-{index}"
            if operation == "list_file_tags" else sample_item(tree, index)
            for index in range(item_count)
        ]

        def get_next(continuation: str | None) -> tuple[str | None, list[Any]]:
            """Record every page fetch, including the terminal continuation."""
            visits.append(continuation)
            return ("second-page", []) if continuation is None else (None, items)

        return ItemPaged(get_next, lambda page: page)

    for name, member in inspect.getmembers(generated_client, inspect.isfunction):
        if name.startswith("_"):
            continue
        if name in all_operations:
            getattr(client, name).side_effect = (
                lambda *args, operation=name, **kwargs: create_pager(operation)
            )
        else:
            getattr(client, name).return_value = {}
    monkeypatch.setattr(module, client_name, MagicMock(return_value=client))
    function = getattr(module, function_name)
    arguments = {
        name: "sample-value"
        for name, parameter in inspect.signature(function).parameters.items()
        if parameter.default is inspect.Parameter.empty
    }

    function(**arguments)

    output = capsys.readouterr().out
    assert "error" not in output.casefold(), output
    assert "ItemPaged object" not in output, output
    for operation in operations:
        assert getattr(client, operation).called, operation
    assert page_visits, output
    assert all(visits == [None, "second-page"] for visits in page_visits)
    body = "\n".join(
        line for line in output.splitlines() if not line.startswith("===")
    )
    if item_count:
        assert (
            "pager-review-item-0" in body
            or re.search(r"\b2\b", body)
            or body.count("[REDACTED]") == 2
        ), output
    else:
        assert "pager-review-item-" not in body
        assert re.search(r"\b0\b|\bno\b|empty|\[\]", body, re.IGNORECASE), output


def test_all_sync_pageable_call_sites_are_explicitly_consumed() -> None:
    """Sweep all 99 samples against generated return types, including non-list names."""
    paths = sorted(SAMPLES.glob("sample_connector_usage_*.py"))
    assert len(paths) == 99
    pageable_sample_count = 0
    call_count = 0
    for sample_path in paths:
        tree = ast.parse(sample_path.read_text(encoding="utf-8-sig"))
        clients = pageable_methods(tree)
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
            consumed = (
                isinstance(parent, ast.Call)
                and isinstance(parent.func, ast.Name)
                and parent.func.id == "list"
            ) or (
                isinstance(parent, (ast.For, ast.comprehension))
                and parent.iter is call
            )
            assert consumed, (sample_path.name, call.lineno, ast.unparse(call))
    assert pageable_sample_count == 73
    assert call_count == 145


@pytest.mark.parametrize("response", [None, {}, {"value": [{"id": "created"}]}])
def test_excel_mutation_responses_remain_eager_envelopes(
    response: dict[str, Any] | None,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Keep nullable mutation dictionaries intact rather than collecting their keys."""
    sample_path = SAMPLES / "sample_connector_usage_excelonline.py"
    module = load_sample(sample_path)
    client = configure_sample(module, sample_path, monkeypatch)
    client.list_all_worksheets.return_value = ItemPaged(
        lambda continuation: [], lambda page: (None, page),
    )
    client.list_tables.return_value = ItemPaged(
        lambda continuation: [], lambda page: (None, page),
    )
    client.create_worksheet.return_value = response
    client.add_row.return_value = response
    monkeypatch.setattr(module, "ExcelonlineClient", MagicMock(return_value=client))

    module.main()

    output = capsys.readouterr().out
    assert f"created worksheet {response}" in output
    assert f"added row {response}" in output
    assert "error" not in output.casefold()
