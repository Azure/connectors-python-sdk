# Copyright (c) Microsoft Corporation. All rights reserved.

"""Contract tests for samples affected by connector regeneration."""

from __future__ import annotations

import ast
import importlib
import importlib.util
from contextlib import AbstractAsyncContextManager
from dataclasses import dataclass
from pathlib import Path
from typing import AsyncIterator

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

    async def page_items_async(self) -> AsyncIterator[dict[str, str]]:
        """Represent a generated pageable method."""
        yield {"id": "item"}


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


def test_sample_validator_rejects_awaited_async_iterator() -> None:
    """Test pageable generated operations must be consumed with async iteration."""
    tree = ast.parse(
        "async def main():\n"
        "    client = TypedClient('https://example.azure.com/connections/test')\n"
        "    await client.page_items_async()\n"
    )
    visitor = SampleVisitor(Path("sample.py"), modules={})
    visitor.imported_symbols["TypedClient"] = TypedClient

    visitor.visit(tree)

    assert [issue.message for issue in visitor.issues] == [
        "async iterator 'TypedClient.page_items_async' must use async iteration",
    ]


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


@pytest.mark.asyncio
async def test_zendesk_sample_reports_collected_items(
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test the Zendesk sample displays nonempty pageable results."""
    sample_module = importlib.import_module(
        "samples.sample_connector_usage.sample_connector_usage_zendesk"
    )
    sent_requests: list[dict[str, object]] = []

    class RecordingCredential(AbstractAsyncContextManager[object]):
        """Provide an async credential context for the sample."""

        async def __aexit__(self, *args: object) -> None:
            """Exit the credential context."""

    class RecordingClient(AbstractAsyncContextManager[object]):
        """Record the generated client call and yield one synthetic item."""

        def __init__(self, connection_runtime_url: str, credential: object) -> None:
            """Initialize the recording client."""
            del connection_runtime_url, credential

        async def __aexit__(self, *args: object) -> None:
            """Exit the client context."""

        async def get_items_async(
            self,
            **kwargs: object,
        ) -> AsyncIterator[dict[str, str]]:
            """Record request arguments and yield one ticket."""
            sent_requests.append(kwargs)
            yield {"id": "synthetic-ticket"}

    monkeypatch.setattr(
        sample_module,
        "DefaultAzureCredential",
        RecordingCredential,
    )
    monkeypatch.setattr(sample_module, "ZendeskClient", RecordingClient)

    await sample_module.example_2_get_items()

    assert sent_requests == [{"table": "tickets", "top": 10}]
    assert "Retrieved 1 item(s)." in capsys.readouterr().out
