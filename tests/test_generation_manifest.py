# ------------------------------------------------------------
# Copyright (c) Microsoft Corporation.  All rights reserved.
# ------------------------------------------------------------

"""Tests for generated connector provenance."""

from __future__ import annotations

import ast
import hashlib
import json
from pathlib import Path
from typing import Any

from azure.connectors._client_registry import CLIENT_REGISTRY


REPOSITORY_ROOT = Path(__file__).resolve().parent.parent
MANIFEST_PATH = REPOSITORY_ROOT / "generation.manifest.json"
CONNECTOR_DIRECTORY = REPOSITORY_ROOT / "src" / "azure" / "connectors"
ASYNC_CONNECTOR_DIRECTORY = CONNECTOR_DIRECTORY / "aio"
SNAPSHOT_DIRECTORY = REPOSITORY_ROOT / "swagger-cache"
EXPECTED_GENERATOR_REVISION = "dfbac0cf23422c8a339aa3c384e3a05f48c5ca48"


def canonical_sha256(path: Path) -> str:
    """Return the SHA-256 of UTF-8 text with canonical LF line endings."""
    text = path.read_text(encoding="utf-8").replace("\r\n", "\n").replace("\r", "\n")
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def load_manifest() -> dict[str, Any]:
    """Load the generation manifest."""
    return json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))


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


def test_generation_manifest_covers_exact_connector_inventory() -> None:
    """Verify every generated module and snapshot has one manifest entry."""
    manifest = load_manifest()
    manifest_names = [entry["apiName"] for entry in manifest["connectors"]]
    connector_names = sorted(
        path.stem
        for path in CONNECTOR_DIRECTORY.glob("*.py")
        if not path.name.startswith("_")
    )
    async_connector_names = sorted(
        path.stem
        for path in ASYNC_CONNECTOR_DIRECTORY.glob("*.py")
        if path.name != "__init__.py"
    )
    snapshot_names = sorted(
        path.name.removesuffix(".swagger.json")
        for path in SNAPSHOT_DIRECTORY.glob("*.swagger.json")
    )

    assert manifest["manifestVersion"] == 1
    assert manifest["generator"]["revision"] == EXPECTED_GENERATOR_REVISION
    assert manifest_names == sorted(manifest_names)
    assert manifest_names == connector_names
    assert manifest_names == async_connector_names
    assert manifest_names == snapshot_names


def test_generation_manifest_hashes_match_committed_files() -> None:
    """Verify snapshot and generated output hashes match the manifest."""
    manifest = load_manifest()

    for entry in manifest["connectors"]:
        assert canonical_sha256(
            REPOSITORY_ROOT / entry["swaggerSnapshot"]
        ) == entry["swaggerSha256"]
        assert canonical_sha256(
            REPOSITORY_ROOT / entry["outputFile"]
        ) == entry["outputSha256"]
        assert canonical_sha256(
            REPOSITORY_ROOT / entry["asyncOutputFile"]
        ) == entry["asyncOutputSha256"]

    for artifact in manifest["packageArtifacts"].values():
        assert canonical_sha256(
            REPOSITORY_ROOT / artifact["path"]
        ) == artifact["sha256"]


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
    assert stub_client_names(
        ASYNC_CONNECTOR_DIRECTORY / "__init__.pyi"
    ) == expected_client_names


def test_generated_operations_have_structured_docstrings() -> None:
    """Require structured public API documentation in both client surfaces."""
    operation_count = 0
    violations: list[str] = []
    connector_paths = [
        *CONNECTOR_DIRECTORY.glob("*.py"),
        *ASYNC_CONNECTOR_DIRECTORY.glob("*.py"),
    ]

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
