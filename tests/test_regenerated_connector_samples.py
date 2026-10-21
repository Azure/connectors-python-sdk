# Copyright (c) Microsoft Corporation. All rights reserved.

"""Contract tests for samples affected by connector regeneration."""

from __future__ import annotations

import ast
import importlib
import importlib.util
import inspect
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import pytest
from azure.core.async_paging import AsyncItemPaged

from scripts.validate_connector_samples import SampleVisitor, validate_samples


SAMPLE_DIRECTORY = (
    Path(__file__).parent.parent / "samples" / "sample_connector_usage"
)


SAMPLE_PATHS = sorted(SAMPLE_DIRECTORY.glob("sample_connector_usage_*.py"))


@dataclass
class TypedInput:
    """Provide a typed request model for sample validator tests."""

    value: str


class TypedAsyncClient:
    """Provide a typed asynchronous client surface for sample validator tests."""

    def __init__(self, connection_runtime_url: str) -> None:
        """Initialize the test client."""

    async def __aenter__(self) -> TypedAsyncClient:
        """Expose the async lifecycle used to recognize generated clients."""
        return self

    async def list_items(self, *, top: int) -> None:
        """Represent a generated method with an integer argument."""

    async def create_item(self, *, input: TypedInput) -> None:
        """Represent a generated method with a typed request body."""

    def get_items(self) -> AsyncItemPaged[dict[str, str]]:
        """Represent a generated asynchronous pageable method."""


async def invoke_sample(module: object, function_name: str, *arguments: str) -> None:
    """Require and await the async root sample entry point."""
    function = getattr(module, function_name)
    assert inspect.iscoroutinefunction(function), function_name
    await function(*arguments)


@pytest.mark.parametrize(
    "sample_path",
    SAMPLE_PATHS,
    ids=lambda sample_path: f"{sample_path.parent.name}-{sample_path.stem}",
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

    assert len(SAMPLE_PATHS) == 99
    assert set(sample_paths) == set(SAMPLE_PATHS)
    assert not (SAMPLE_DIRECTORY / "aio").exists()
    assert not (SAMPLE_DIRECTORY / "sync").exists()
    assert issues == []


def test_connector_samples_have_no_undefined_names() -> None:
    """Test every sample resolves all names used by executable code."""
    repo_root = Path(__file__).parent.parent
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "flake8",
            "--isolated",
            "--select",
            "F821",
            str(SAMPLE_DIRECTORY),
        ],
        check=False,
        capture_output=True,
        cwd=repo_root,
        text=True,
    )

    assert result.returncode == 0, result.stdout + result.stderr


def test_sample_validator_rejects_unscoped_async_credential() -> None:
    """Test asynchronous credentials must use an async context manager."""
    tree = ast.parse(
        "from azure.identity.aio import DefaultAzureCredential\n"
        "async def main():\n"
        "    credential = DefaultAzureCredential()\n"
    )
    visitor = SampleVisitor(Path("sample.py"), modules={})

    visitor.visit(tree)

    assert [issue.message for issue in visitor.issues] == [
        "asynchronous DefaultAzureCredential must use an async context manager",
    ]


def test_sample_validator_rejects_sync_credential() -> None:
    """Reject synchronous credentials even when their lifecycle is scoped."""
    tree = ast.parse(
        "from azure.identity import DefaultAzureCredential\n"
        "with DefaultAzureCredential() as credential:\n"
        "    pass\n"
    )
    visitor = SampleVisitor(Path("sample.py"), modules={})

    visitor.visit(tree)

    assert [issue.message for issue in visitor.issues] == [
        "connector samples require azure.identity.aio credentials",
    ]


@pytest.mark.parametrize(
    "module_name", ["azure.connectors.aio.office365", "azure.connectors.sdk.aio"],
)
def test_sample_validator_rejects_aio_connector_namespace(module_name: str) -> None:
    """Reject stale aio connector imports rather than accepting a second surface."""
    visitor = SampleVisitor(Path("sample.py"), modules={})

    visitor.visit(ast.parse(f"from {module_name} import Office365Client\n"))

    assert [issue.message for issue in visitor.issues] == [
        "import async clients from root connector modules, not aio",
    ]


def test_sample_validator_rejects_awaiting_pageable_method() -> None:
    """Test pageable methods require iteration rather than await."""
    tree = ast.parse(
        "client = TypedAsyncClient('https://example.azure.com/connections/test')\n"
        "await client.get_items()\n"
    )
    visitor = SampleVisitor(Path("sample.py"), modules={})
    visitor.imported_symbols["TypedAsyncClient"] = TypedAsyncClient

    visitor.visit(tree)

    assert [issue.message for issue in visitor.issues] == [
        "'get_items' must be consumed with async for",
    ]


def test_sample_validator_rejects_dictionary_access_on_collected_items() -> None:
    """Test collecting an async iterator does not permit response-envelope access."""
    tree = ast.parse(
        "items = [item async for item in client.get_items()]\n"
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
        "items = [item async for item in client.get_items()]\n"
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
    visitor.imported_symbols["TypedAsyncClient"] = TypedAsyncClient

    visitor.visit(ast.parse(
        "items = []\n"
        "client = TypedAsyncClient('https://example.com')\n"
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
    visitor.imported_symbols["TypedAsyncClient"] = TypedAsyncClient

    visitor.visit(ast.parse(
        "client = TypedAsyncClient('https://example.com')\n"
        "async def consume(client=client.missing_method()):\n"
        "    pass\n"
    ))

    assert [issue.message for issue in visitor.issues] == [
        "'TypedAsyncClient' has no method 'missing_method'",
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
    visitor.imported_symbols["TypedAsyncClient"] = TypedAsyncClient

    visitor.visit(ast.parse(
        "client = TypedAsyncClient('https://example.com')\n"
        "identifiers = [client.get('id') for client in [{'id': 'entry-1'}]]\n"
    ))

    assert visitor.issues == []
    assert visitor.client_variables["client"] is TypedAsyncClient


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
            "result = [item async for item in client.get_items()]",
            ["capture collected items in a semantic name instead of 'result'"],
        ),
        ("if items and items:\n    pass", ["remove repeated conditions"]),
        ("items = [item async for item in client.get_items()]", []),
        ("if items and ready:\n    pass", []),
        ("if response and response.get('value'):\n    pass", []),
        (
            "items = [item async for item in client.get_items()]\n"
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
         "list_query_documents", "document(s)"),
        ("documentdb", "example_5_query_with_consistency", "DocumentdbClient",
         "list_query_documents", "document(s)"),
        ("office365groupsmail", "main", "Office365groupsmailClient",
         "list_conversations", "conversation(s)"),
        ("planner", "example_2_list_group_plans", "PlannerClient",
         "list_group_plans", "plans in group"),
        ("zendesk", "example_2_get_items", "ZendeskClient",
         "list_items", "item(s)"),
        ("azuretables", "example_4_get_entities", "AzuretablesClient",
         "list_entities", "entity(s)"),
    ],
)
@pytest.mark.asyncio
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

    async def async_items():
        """Yield distinct items to expose incorrect counts or lost data."""
        for index in range(item_count):
            yield {
                "id": f"document-{index}",
                "PartitionKey": "sample-partition",
                "RowKey": f"row-{index}",
            }

    client = MagicMock()
    operation = getattr(client, operation_name)
    operation.return_value = async_items()
    client.list_groups.return_value = async_items()
    client.__aenter__.return_value = client
    monkeypatch.setattr(module, client_name, MagicMock(return_value=client))
    if hasattr(module, "DefaultAzureCredential"):
        monkeypatch.setattr(module, "DefaultAzureCredential", MagicMock())
    for setting in (
        "COSMOS_DB_ACCOUNT", "DATABASE_ID", "CONTAINER_ID", "STORAGE_ACCOUNT", "TABLE_NAME",
    ):
        if hasattr(module, setting):
            monkeypatch.setattr(module, setting, "sample-value")
    monkeypatch.setenv("OFFICE365GROUPSMAIL_CONNECTION_URL", "https://example.com")
    monkeypatch.setenv("OFFICE365GROUPSMAIL_GROUP_ID", "sample-group")

    arguments = ["sample-group"] if connector == "planner" else []
    await invoke_sample(module, function_name, *arguments)

    operation.assert_called_once()
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
    elif connector == "planner" and item_count == 0:
        assert "No plans found" in output
    elif connector == "documentdb" and function_name.endswith("consistency"):
        assert f"Documents retrieved: {item_count}" in output
    else:
        assert f"{item_count} {expected_noun}" in output


@pytest.mark.parametrize("response_kind", ["none", "empty", "populated"])
@pytest.mark.parametrize(
    "connector,function_name,client_name,operation_name,item_key,empty_message",
    [
        ("azuredigitaltwins", "example_3_query_twins", "AzuredigitaltwinsClient",
         "query_twins", "value", "No twins found matching query"),
        ("wdatp", "example_3_advanced_hunting", "WdatpClient",
         "advanced_hunting", "results", "No results from query."),
    ],
)
@pytest.mark.asyncio
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
    operation = AsyncMock(return_value=response)
    setattr(client, operation_name, operation)
    client.__aenter__.return_value = client
    monkeypatch.setattr(module, client_name, MagicMock(return_value=client))
    monkeypatch.setattr(module, "DefaultAzureCredential", MagicMock())

    await invoke_sample(module, function_name)

    operation.assert_awaited_once()
    output = capsys.readouterr().out
    assert "Error:" not in output
    assert "Connector error" not in output
    if response_kind == "populated":
        assert "matched-item" in output
    else:
        assert empty_message in output


@pytest.mark.parametrize("response_kind", ["none", "empty", "populated"])
@pytest.mark.parametrize(
    "connector,function_name,client_name,operation_name,item_key,marker",
    [
        (
            "docusign",
            "example_2_search_envelopes",
            "DocusignClient",
            "search_list_envelopes",
            "value",
            "sample-envelope",
        ),
        (
            "azuremonitorlogs",
            "example_run_query",
            "AzuremonitorlogsClient",
            "query_data",
            "value",
            "sample-row",
        ),
    ],
)
@pytest.mark.asyncio
async def test_eager_list_samples_unwrap_nullable_envelopes(
    connector: str,
    function_name: str,
    client_name: str,
    operation_name: str,
    item_key: str,
    marker: str,
    response_kind: str,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Execute eager async samples without treating response envelopes as lists."""
    module = importlib.import_module(
        f"samples.sample_connector_usage.sample_connector_usage_{connector}"
    )
    response = None if response_kind == "none" else {}
    if response_kind == "populated":
        response = {item_key: [{"envelopeId": marker, "status": marker, "row": marker}]}
    client = MagicMock()
    operation = AsyncMock(return_value=response)
    setattr(client, operation_name, operation)
    client.__aenter__.return_value = client
    monkeypatch.setattr(module, client_name, MagicMock(return_value=client))
    monkeypatch.setattr(module, "DefaultAzureCredential", MagicMock())
    for setting in (
        "SUBSCRIPTION_ID",
        "RESOURCE_GROUP",
        "RESOURCE_NAME",
        "RESOURCE_TYPE",
    ):
        if hasattr(module, setting):
            monkeypatch.setattr(module, setting, "sample-value")

    arguments = ["sample-account"] if connector == "docusign" else []
    await invoke_sample(module, function_name, *arguments)

    output = capsys.readouterr().out
    assert "Error:" not in output
    assert "Connector error" not in output
    operation.assert_awaited_once()
    if response_kind == "populated":
        assert marker in output
    else:
        assert "0" in output


@pytest.mark.asyncio
async def test_eventhubs_batch_sample_passes_send_event_list(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Execute the batch sample and verify its list alias is passed directly."""
    module = importlib.import_module(
        "samples.sample_connector_usage.sample_connector_usage_eventhubs"
    )
    client = MagicMock()
    operation = AsyncMock(return_value=None)
    client.send_events = operation
    client.__aenter__.return_value = client
    monkeypatch.setattr(module, "EventhubsClient", MagicMock(return_value=client))
    monkeypatch.setattr(module, "DefaultAzureCredential", MagicMock())
    monkeypatch.setattr(module, "EVENT_HUB_NAME", "sample-hub")

    await invoke_sample(module, "example_3_send_batch_events")

    output = capsys.readouterr().out
    assert "Error:" not in output
    assert "Connector error" not in output
    operation.assert_awaited_once()
    batch_input = operation.call_args.kwargs["input"]
    assert isinstance(batch_input, list)
    assert len(batch_input) == 3
    assert all(isinstance(event, module.SendEvent) for event in batch_input)
    assert "Batch of 3 events" in output


@pytest.mark.asyncio
async def test_azuretables_create_sample_passes_scalar_table_name(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Execute the create-table sample and verify its string alias is passed directly."""
    module = importlib.import_module(
        "samples.sample_connector_usage.sample_connector_usage_azuretables"
    )
    client = MagicMock()
    operation = AsyncMock(return_value={})
    client.create_table = operation
    client.__aenter__.return_value = client
    monkeypatch.setattr(module, "AzuretablesClient", MagicMock(return_value=client))
    monkeypatch.setattr(module, "DefaultAzureCredential", MagicMock())
    monkeypatch.setattr(module, "STORAGE_ACCOUNT", "sample-account")
    monkeypatch.setenv("AZURETABLES_NEW_TABLE_NAME", "SampleTable")

    await invoke_sample(module, "example_2_create_table")

    output = capsys.readouterr().out
    assert "Error:" not in output
    assert "Connector error" not in output
    operation.assert_awaited_once()
    assert operation.call_args.kwargs["input"] == "SampleTable"
    assert "Table 'SampleTable' created successfully." in output


def test_sample_validator_rejects_incompatible_literal_type() -> None:
    """Test a string literal is rejected for an integer parameter."""
    tree = ast.parse(
        "client = TypedAsyncClient('https://example.azure.com/connections/test')\n"
        "await client.list_items(top='10')\n"
    )
    visitor = SampleVisitor(Path("sample.py"), modules={})
    visitor.imported_symbols["TypedAsyncClient"] = TypedAsyncClient

    visitor.visit(tree)

    assert [issue.message for issue in visitor.issues] == [
        "argument 'top' has type 'str', expected 'int'",
    ]


def test_sample_validator_rejects_environment_string_for_integer() -> None:
    """Test an environment string is rejected for an integer parameter."""
    tree = ast.parse(
        "client = TypedAsyncClient('https://example.azure.com/connections/test')\n"
        "top = os.environ.get('TOP', '')\n"
        "await client.list_items(top=top)\n"
    )
    visitor = SampleVisitor(Path("sample.py"), modules={})
    visitor.imported_symbols["TypedAsyncClient"] = TypedAsyncClient

    visitor.visit(tree)

    assert [issue.message for issue in visitor.issues] == [
        "argument 'top' has type 'str', expected 'int'",
    ]


def test_sample_validator_accepts_cast_environment_value() -> None:
    """Test casting an environment value satisfies an integer parameter."""
    tree = ast.parse(
        "client = TypedAsyncClient('https://example.azure.com/connections/test')\n"
        "top = int(os.environ.get('TOP', '0'))\n"
        "await client.list_items(top=top)\n"
    )
    visitor = SampleVisitor(Path("sample.py"), modules={})
    visitor.imported_symbols["TypedAsyncClient"] = TypedAsyncClient

    visitor.visit(tree)

    assert visitor.issues == []


def test_sample_validator_rejects_dynamic_dict_for_typed_input() -> None:
    """Test a dictionary with a dynamic value is rejected for a typed input."""
    tree = ast.parse(
        "client = TypedAsyncClient('https://example.azure.com/connections/test')\n"
        "index = 0\n"
        "await client.create_item(input={'value': f'Item {index + 1}'})\n"
    )
    visitor = SampleVisitor(Path("sample.py"), modules={})
    visitor.imported_symbols["TypedAsyncClient"] = TypedAsyncClient

    visitor.visit(tree)

    assert [issue.message for issue in visitor.issues] == [
        "argument 'input' has type 'dict', expected 'TypedInput'",
    ]
