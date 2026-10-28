# ------------------------------------------------------------
# Copyright (c) Microsoft Corporation.  All rights reserved.
# ------------------------------------------------------------

"""Tests for generated connector contracts."""

from __future__ import annotations

import ast
from pathlib import Path

from azure.connectors._client_registry import CLIENT_REGISTRY


REPOSITORY_ROOT = Path(__file__).resolve().parent.parent
CONNECTOR_DIRECTORY = REPOSITORY_ROOT / "src" / "azure" / "connectors"


def generated_client_name(path: Path) -> str:
    """Return the generated client class declared by a connector module."""
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    client_names = [
        node.name
        for node in tree.body
        if isinstance(node, ast.ClassDef)
        and any(
            isinstance(base, ast.Name) and base.id == "ConnectorClientBase"
            for base in node.bases
        )
    ]
    assert len(client_names) == 1, path
    return client_names[0]


def stub_client_names(path: Path) -> set[str]:
    """Return connector client names imported by a package type stub."""
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    return {
        alias.asname
        for node in tree.body
        if isinstance(node, ast.ImportFrom)
        and node.module is not None
        and not node.module.startswith("sdk.")
        for alias in node.names
        if alias.asname is not None and alias.asname.endswith("Client")
    }


def test_generated_inventory_has_only_root_connectors() -> None:
    """Keep all 101 connectors at root without duplicate client namespaces."""
    connector_names = {
        path.stem
        for path in CONNECTOR_DIRECTORY.glob("*.py")
        if not path.name.startswith("_")
    }
    assert len(connector_names) == 101
    assert connector_names == set(CLIENT_REGISTRY.values())
    assert not (CONNECTOR_DIRECTORY / "aio").exists()
    assert not (CONNECTOR_DIRECTORY / "sync").exists()


def test_generated_registry_and_type_stubs_cover_every_client() -> None:
    """Keep runtime and static package exports aligned with generated clients."""
    expected_registry = {
        generated_client_name(path): path.stem
        for path in sorted(CONNECTOR_DIRECTORY.glob("*.py"))
        if not path.name.startswith("_")
    }
    expected_client_names = set(expected_registry)

    assert CLIENT_REGISTRY == expected_registry
    assert stub_client_names(CONNECTOR_DIRECTORY / "__init__.pyi") == expected_client_names


def test_generated_operations_have_structured_docstrings() -> None:
    """Require structured public API documentation in the async root surface."""
    operation_count = 0
    violations: list[str] = []
    connector_paths = sorted(CONNECTOR_DIRECTORY.glob("*.py"))

    for path in connector_paths:
        if path.name.startswith("_"):
            continue

        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for client in (
            node
            for node in tree.body
            if isinstance(node, ast.ClassDef)
            and any(
                isinstance(base, ast.Name) and base.id == "ConnectorClientBase"
                for base in node.bases
            )
        ):
            for method in (
                node
                for node in client.body
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
                and not node.name.startswith("_")
                and any(
                    isinstance(descendant, ast.Call)
                    and isinstance(descendant.func, ast.Attribute)
                    and descendant.func.attr == "send"
                    for descendant in ast.walk(node)
                )
            ):
                operation_count += 1
                docstring = ast.get_docstring(method) or ""
                if not all(
                    section in docstring
                    for section in ("Args:", "Returns:", "Raises:")
                ):
                    violations.append(
                        f"{path.relative_to(REPOSITORY_ROOT).as_posix()}:"
                        f"{method.lineno}: {method.name}"
                    )

    assert operation_count > 0
    assert not violations, "Generated operations missing structured docs:\n" + "\n".join(
        violations
    )
