# Copyright (c) Microsoft Corporation. All rights reserved.

"""Contract tests for samples affected by connector regeneration."""

from __future__ import annotations

import ast
import importlib.util
from pathlib import Path

import pytest

from scripts.validate_connector_samples import SampleVisitor, validate_samples


SAMPLE_DIRECTORY = (
    Path(__file__).parent.parent / "samples" / "sample_connector_usage"
)


SAMPLE_PATHS = sorted(SAMPLE_DIRECTORY.glob("sample_connector_usage_*.py"))


class TypedClient:
    """Provide a typed client surface for sample validator tests."""

    def __init__(self, connection_runtime_url: str) -> None:
        """Initialize the test client."""

    async def list_items_async(self, *, top: int) -> None:
        """Represent a generated method with an integer argument."""


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

    assert len(sample_paths) == 98
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
