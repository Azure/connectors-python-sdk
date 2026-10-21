# ------------------------------------------------------------
# Copyright (c) Microsoft Corporation.  All rights reserved.
# ------------------------------------------------------------

"""Offline regression tests for asynchronous sample entry points."""

from __future__ import annotations

import ast
import gc
import importlib.util
import warnings
from pathlib import Path
from unittest.mock import AsyncMock

import pytest


def test_sharepoint_main_guard_awaits_examples_without_coroutine_warnings(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Run the actual main guard with only the seven example functions mocked."""
    sample_path = (
        Path(__file__).resolve().parent.parent
        / "samples/sample_connector_usage/sample_connector_usage_sharepoint.py"
    )
    tree = ast.parse(sample_path.read_text(encoding="utf-8"), filename=str(sample_path))
    guard, = (
        node for node in tree.body
        if isinstance(node, ast.If) and ast.unparse(node.test) == "__name__ == '__main__'"
    )
    specification = importlib.util.spec_from_file_location("sharepoint_entry_point", sample_path)
    assert specification is not None and specification.loader is not None
    module = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(module)
    assert module.IMPORTS_AVAILABLE

    example_names = (
        "example_1_get_lists",
        "example_2_get_list_items",
        "example_3_create_list_item",
        "example_4_update_list_item",
        "example_5_query_with_filters",
        "example_6_file_operations",
        "example_7_error_handling",
    )
    examples = {name: AsyncMock(name=name) for name in example_names}
    for name, example in examples.items():
        monkeypatch.setattr(module, name, example)
    module.__name__ = "__main__"

    with warnings.catch_warnings(record=True) as recorded_warnings:
        warnings.simplefilter("always", RuntimeWarning)
        exec(compile(ast.Module(body=[guard], type_ignores=[]), str(sample_path), "exec"),
             vars(module))
        gc.collect()

    for example in examples.values():
        example.assert_awaited_once_with()
    assert "Sample completed!" in capsys.readouterr().out
    assert not [
        str(warning.message) for warning in recorded_warnings
        if issubclass(warning.category, RuntimeWarning)
        and "was never awaited" in str(warning.message)
    ]
