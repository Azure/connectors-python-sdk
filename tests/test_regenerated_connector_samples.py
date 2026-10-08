# Copyright (c) Microsoft Corporation. All rights reserved.

"""Contract tests for samples affected by connector regeneration."""

from __future__ import annotations

import ast
import importlib
import importlib.util
from collections.abc import AsyncIterator
from dataclasses import dataclass
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import pytest

from scripts.validate_connector_samples import SampleVisitor, validate_samples


SAMPLE_DIRECTORY = (
    Path(__file__).parent.parent / "samples" / "sample_connector_usage"
)


SAMPLE_PATHS = sorted(SAMPLE_DIRECTORY.glob("sample_connector_usage_*.py"))


@dataclass
class TypedInput:
    """Provide a typed request model for sample validator tests."""

    value: str


class TypedClient:
    """Provide a typed client surface for sample validator tests."""

    def __init__(self, connection_runtime_url: str) -> None:
        """Initialize the test client."""

    async def list_items_async(self, *, top: int) -> None:
        """Represent a generated method with an integer argument."""

    async def create_item_async(self, *, input: TypedInput) -> None:
        """Represent a generated method with a typed request body."""

    async def get_items_async(self) -> AsyncIterator[dict[str, str]]:
        """Represent a generated pageable method."""
        yield {"id": "item-1"}


@pytest.mark.parametrize(
    "sample_path",
    SAMPLE_PATHS,
    ids=lambda sample_path: sample_path.stem,
)
def test_regenerated_connector_sample_imports(sample_path: Path) -> None:
    """Test every connector sample imports its current public models."""
    assert sample_path.read_bytes().endswith(b"\n")

    specification = importlib.util.spec_from_file_location(
        sample_path.stem,
        sample_path,
    )

    assert specification is not None
    assert specification.loader is not None

    module = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(module)


def test_all_connector_samples_match_generated_apis() -> None:
    """Test every sample model constructor and client method call."""
    repo_root = Path(__file__).parent.parent

    sample_paths, issues = validate_samples(repo_root)

    assert len(sample_paths) == 99
    assert issues == []


def test_sample_validator_rejects_unscoped_async_credential() -> None:
    """Test asynchronous credentials must use an async context manager."""
    tree = ast.parse(
        "async def main():\n"
        "    credential = DefaultAzureCredential()\n"
    )
    visitor = SampleVisitor(Path("sample.py"), modules={})

    visitor.visit(tree)

    assert [issue.message for issue in visitor.issues] == [
        "DefaultAzureCredential must use an async context manager",
    ]


def test_sample_validator_rejects_awaiting_pageable_method() -> None:
    """Test pageable methods require iteration rather than await."""
    tree = ast.parse(
        "client = TypedClient('https://example.azure.com/connections/test')\n"
        "await client.get_items_async()\n"
    )
    visitor = SampleVisitor(Path("sample.py"), modules={})
    visitor.imported_symbols["TypedClient"] = TypedClient

    visitor.visit(tree)

    assert [issue.message for issue in visitor.issues] == [
        "'get_items_async' must be consumed with async for",
    ]


def test_sample_validator_rejects_dictionary_access_on_collected_items() -> None:
    """Test collecting an async iterator does not permit response-envelope access."""
    tree = ast.parse(
        "items = [item async for item in client.get_items_async()]\n"
        "items.get('value', [])\n"
    )
    visitor = SampleVisitor(Path("sample.py"), modules={})

    visitor.visit(tree)

    assert [issue.message for issue in visitor.issues] == [
        "'list' has no method 'get'",
    ]


def test_sample_validator_checks_rhs_before_reassigning_the_same_name() -> None:
    """Test a same-name assignment cannot erase the invalid receiver's old list type."""
    visitor = SampleVisitor(Path("sample.py"), modules={})

    visitor.visit(ast.parse(
        "items = [item async for item in client.get_items_async()]\n"
        "items = items.get('value', [])\n"
    ))

    assert [issue.message for issue in visitor.issues] == ["'list' has no method 'get'"]


@pytest.mark.parametrize("function_kind", ["def", "async def"])
@pytest.mark.parametrize(
    "parameters", ["items: dict, client", "items: dict, /, client", "*, items: dict, client"],
)
def test_sample_validator_parameters_shadow_outer_facts(
    function_kind: str, parameters: str,
) -> None:
    """Test parameters shadow outer container and client facts without losing outer checks."""
    visitor = SampleVisitor(Path("sample.py"), modules={})
    visitor.imported_symbols["TypedClient"] = TypedClient

    visitor.visit(ast.parse(
        "items = []\n"
        "client = TypedClient('https://example.com')\n"
        f"{function_kind} consume({parameters}):\n"
        "    items.get('value', [])\n"
        "    client.unrelated_method()\n"
        "items.get('value', [])\n"
    ))

    assert [issue.message for issue in visitor.issues] == ["'list' has no method 'get'"]
    assert visitor.issues[0].line == 6


def test_sample_validator_function_defaults_use_outer_facts() -> None:
    """Test default expressions are validated before a parameter shadows its outer name."""
    visitor = SampleVisitor(Path("sample.py"), modules={})
    visitor.imported_symbols["TypedClient"] = TypedClient

    visitor.visit(ast.parse(
        "client = TypedClient('https://example.com')\n"
        "async def consume(client=client.missing_method()):\n"
        "    pass\n"
    ))

    assert [issue.message for issue in visitor.issues] == [
        "'TypedClient' has no method 'missing_method'",
    ]


@pytest.mark.parametrize(
    "expression",
    [
        "[item.get('id') for item in [{'id': 'entry-1'}]]",
        "{item.get('id') for item in [{'id': 'entry-1'}]}",
        "{item.get('id'): item for item in [{'id': 'entry-1'}]}",
        "(item.get('id') for item in [{'id': 'entry-1'}])",
    ],
)
def test_sample_validator_comprehension_targets_shadow_outer_facts(expression: str) -> None:
    """Test valid dictionary iteration is not confused with the outer same-name list."""
    visitor = SampleVisitor(Path("sample.py"), modules={})

    visitor.visit(ast.parse("item = []\nidentifiers = " + expression))

    assert visitor.issues == []
    assert visitor.variable_types["item"] is list


def test_sample_validator_comprehension_clears_client_target_facts() -> None:
    """Test comprehension-local receivers do not retain an outer generated client type."""
    visitor = SampleVisitor(Path("sample.py"), modules={})
    visitor.imported_symbols["TypedClient"] = TypedClient

    visitor.visit(ast.parse(
        "client = TypedClient('https://example.com')\n"
        "identifiers = [client.get('id') for client in [{'id': 'entry-1'}]]\n"
    ))

    assert visitor.issues == []
    assert visitor.client_variables["client"] is TypedClient


def test_sample_validator_comprehension_iterable_uses_outer_facts() -> None:
    """Test the iterable is checked before its target shadows an invalid outer receiver."""
    visitor = SampleVisitor(Path("sample.py"), modules={})

    visitor.visit(ast.parse(
        "item = []\n"
        "identifiers = [item for item in item.get('value', [])]\n"
    ))

    assert [issue.message for issue in visitor.issues] == ["'list' has no method 'get'"]


@pytest.mark.parametrize(
    "source,expected_messages",
    [
        (
            "result = [item async for item in client.get_items_async()]",
            ["capture collected items in a semantic name instead of 'result'"],
        ),
        ("if items and items:\n    pass", ["remove repeated conditions"]),
        ("items = [item async for item in client.get_items_async()]", []),
        ("if items and ready:\n    pass", []),
        ("if response and response.get('value'):\n    pass", []),
        (
            "items = [item async for item in client.get_items_async()]\n"
            "items = items if items else []",
            ["remove redundant fallback for collected items"],
        ),
        ("response = response if response else []", []),
    ],
)
def test_sample_validator_checks_consumer_principles(
    source: str, expected_messages: list[str],
) -> None:
    """Test the reported patterns are rejected without rejecting distinct conditions."""
    visitor = SampleVisitor(Path("sample.py"), modules={})

    visitor.visit(ast.parse(source))

    assert [issue.message for issue in visitor.issues] == expected_messages


@pytest.mark.parametrize("item_count", [0, 2])
@pytest.mark.parametrize(
    "connector,function_name,client_name,operation_name,expected_noun",
    [
        ("documentdb", "example_3_query_with_pagination", "DocumentdbClient",
         "query_documents_async", "document(s)"),
        ("documentdb", "example_5_query_with_consistency", "DocumentdbClient",
         "query_documents_async", "document(s)"),
        ("office365groupsmail", "main", "Office365groupsmailClient",
         "list_conversations_async", "conversation(s)"),
        ("zendesk", "example_2_get_items", "ZendeskClient",
         "get_items_async", "item(s)"),
        ("azuretables", "example_4_get_entities", "AzuretablesClient",
         "get_entities_async", "entity(s)"),
    ],
)
async def test_pageable_samples_report_collected_items(
    connector: str,
    function_name: str,
    client_name: str,
    operation_name: str,
    expected_noun: str,
    item_count: int,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Execute empty and nonempty samples so caught errors and discarded items fail."""
    module = importlib.import_module(
        f"samples.sample_connector_usage.sample_connector_usage_{connector}"
    )

    async def items() -> AsyncIterator[dict[str, str]]:
        """Yield distinct items to expose incorrect counts or lost data."""
        for index in range(item_count):
            yield {
                "id": f"document-{index}",
                "PartitionKey": "sample-partition",
                "RowKey": f"row-{index}",
            }

    client = MagicMock()
    getattr(client, operation_name).return_value = items()
    client.list_groups_async = AsyncMock(return_value={"value": []})
    context = MagicMock()
    context.__aenter__.return_value = client
    monkeypatch.setattr(module, client_name, MagicMock(return_value=context))
    if hasattr(module, "DefaultAzureCredential"):
        monkeypatch.setattr(module, "DefaultAzureCredential", MagicMock())
    for setting in (
        "COSMOS_DB_ACCOUNT", "DATABASE_ID", "CONTAINER_ID", "STORAGE_ACCOUNT", "TABLE_NAME",
    ):
        if hasattr(module, setting):
            monkeypatch.setattr(module, setting, "sample-value")
    monkeypatch.setenv("OFFICE365GROUPSMAIL_CONNECTION_URL", "https://example.com")
    monkeypatch.setenv("OFFICE365GROUPSMAIL_GROUP_ID", "sample-group")

    await getattr(module, function_name)()

    output = capsys.readouterr().out
    assert "Error:" not in output
    assert "Connector error" not in output
    if connector == "azuretables":
        if item_count == 0:
            assert "No entities found or empty response." in output
        else:
            assert "RowKey: row-0" in output
            assert "RowKey: row-1" in output
            assert "No entities found" not in output
    elif connector == "documentdb" and item_count == 0:
        assert "No documents found." in output
    elif connector == "documentdb" and function_name.endswith("consistency"):
        assert f"Documents retrieved: {item_count}" in output
    else:
        assert f"{item_count} {expected_noun}" in output


@pytest.mark.parametrize("response_kind", ["none", "empty", "populated"])
@pytest.mark.parametrize(
    "connector,function_name,client_name,operation_name,item_key,empty_message",
    [
        ("azuredigitaltwins", "example_3_query_twins", "AzuredigitaltwinsClient",
         "query_twins_async", "value", "No twins found matching query"),
        ("planner", "example_2_list_group_plans", "PlannerClient",
         "list_group_plans_async", "value", "No plans found"),
        ("wdatp", "example_3_advanced_hunting", "WdatpClient",
         "advanced_hunting_async", "results", "No results from query."),
    ],
)
async def test_nonpageable_samples_preserve_nullable_responses(
    connector: str,
    function_name: str,
    client_name: str,
    operation_name: str,
    item_key: str,
    empty_message: str,
    response_kind: str,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Execute null, empty, and populated nullable APIs without weakening list checks."""
    module = importlib.import_module(
        f"samples.sample_connector_usage.sample_connector_usage_{connector}"
    )
    response = None if response_kind == "none" else {}
    if response_kind == "populated":
        response = {item_key: [{"id": "matched-item", "title": "matched-plan"}]}
    client = MagicMock()
    setattr(client, operation_name, AsyncMock(return_value=response))
    client.__aenter__.return_value = client
    monkeypatch.setattr(module, client_name, MagicMock(return_value=client))
    monkeypatch.setattr(module, "DefaultAzureCredential", MagicMock())

    arguments = ["sample-group"] if connector == "planner" else []
    await getattr(module, function_name)(*arguments)

    output = capsys.readouterr().out
    assert "Error:" not in output
    assert "Connector error" not in output
    if response_kind == "populated":
        assert "matched-item" in output
    else:
        assert empty_message in output


def test_sample_validator_rejects_incompatible_literal_type() -> None:
    """Test a string literal is rejected for an integer parameter."""
    tree = ast.parse(
        "client = TypedClient('https://example.azure.com/connections/test')\n"
        "client.list_items_async(top='10')\n"
    )
    visitor = SampleVisitor(Path("sample.py"), modules={})
    visitor.imported_symbols["TypedClient"] = TypedClient

    visitor.visit(tree)

    assert [issue.message for issue in visitor.issues] == [
        "argument 'top' has type 'str', expected 'int'",
    ]


def test_sample_validator_rejects_environment_string_for_integer() -> None:
    """Test an environment string is rejected for an integer parameter."""
    tree = ast.parse(
        "client = TypedClient('https://example.azure.com/connections/test')\n"
        "top = os.environ.get('TOP', '')\n"
        "client.list_items_async(top=top)\n"
    )
    visitor = SampleVisitor(Path("sample.py"), modules={})
    visitor.imported_symbols["TypedClient"] = TypedClient

    visitor.visit(tree)

    assert [issue.message for issue in visitor.issues] == [
        "argument 'top' has type 'str', expected 'int'",
    ]


def test_sample_validator_accepts_cast_environment_value() -> None:
    """Test casting an environment value satisfies an integer parameter."""
    tree = ast.parse(
        "client = TypedClient('https://example.azure.com/connections/test')\n"
        "top = int(os.environ.get('TOP', '0'))\n"
        "client.list_items_async(top=top)\n"
    )
    visitor = SampleVisitor(Path("sample.py"), modules={})
    visitor.imported_symbols["TypedClient"] = TypedClient

    visitor.visit(tree)

    assert visitor.issues == []


def test_sample_validator_rejects_dynamic_dict_for_typed_input() -> None:
    """Test a dictionary with a dynamic value is rejected for a typed input."""
    tree = ast.parse(
        "client = TypedClient('https://example.azure.com/connections/test')\n"
        "index = 0\n"
        "client.create_item_async(input={'value': f'Item {index + 1}'})\n"
    )
    visitor = SampleVisitor(Path("sample.py"), modules={})
    visitor.imported_symbols["TypedClient"] = TypedClient

    visitor.visit(tree)

    assert [issue.message for issue in visitor.issues] == [
        "argument 'input' has type 'dict', expected 'TypedInput'",
    ]
