# ------------------------------------------------------------
# Copyright (c) Microsoft Corporation.  All rights reserved.
# ------------------------------------------------------------

"""Tests for lazy package-root connector exports."""

from __future__ import annotations

import ast
import inspect
import subprocess
import sys
from pathlib import Path

import pytest

import azure.connectors as connectors
from azure.connectors import sdk


@pytest.mark.parametrize(
    ("package_name", "module_name"),
    [
        ("azure.connectors", "azure.connectors.arm"),
    ],
)
def test_client_export_is_loaded_lazily(
    package_name: str,
    module_name: str,
) -> None:
    """Keep connector modules unloaded until a package export is requested."""
    script = f"""
import importlib
import inspect
import sys

package = importlib.import_module("{package_name}")
assert "{module_name}" not in sys.modules
client_type = package.ArmClient
assert "{module_name}" in sys.modules
assert client_type is sys.modules["{module_name}"].ArmClient
assert issubclass(client_type, package.ConnectorClientBase)
assert inspect.iscoroutinefunction(client_type.close)
assert inspect.iscoroutinefunction(client_type.__aenter__)
assert not hasattr(client_type, "__enter__")
"""

    subprocess.run([sys.executable, "-c", script], check=True)


@pytest.mark.parametrize("package", [connectors])
def test_client_export_propagates_import_error(
    package: object,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Raise a connector import failure instead of hiding it."""
    monkeypatch.delitem(vars(package), "ArmClient", raising=False)

    def fail_import(name: str, package_name: str) -> None:
        raise ImportError(f"Failed to import '{name}' from '{package_name}'.")

    monkeypatch.setattr(package, "import_module", fail_import)

    with pytest.raises(ImportError, match="Failed to import '.arm'"):
        getattr(package, "ArmClient")


def test_client_inventory_matches_generated_registry() -> None:
    """Expose every generated async client through the package root."""
    expected_names = set(connectors.CLIENT_REGISTRY)

    assert expected_names <= set(dir(connectors))
    assert expected_names <= set(connectors.__all__)


def test_root_runtime_exports_are_the_async_sdk_types() -> None:
    """Keep runtime exports identical to the single async SDK implementation."""
    assert connectors.ConnectorClientBase is sdk.ConnectorClientBase
    assert connectors.ConnectorHttpClient is sdk.ConnectorHttpClient
    assert inspect.iscoroutinefunction(connectors.ConnectorClientBase.close)
    assert inspect.iscoroutinefunction(connectors.ConnectorHttpClient.send)
    assert inspect.iscoroutinefunction(connectors.ConnectorHttpClient.close)
    assert not hasattr(connectors.ConnectorClientBase, "__enter__")


def test_client_type_exports_match_root_connector_modules() -> None:
    """Keep static client exports aligned with the root lazy-loading registry."""
    stub_path = Path(connectors.__file__).with_suffix(".pyi")
    declarations = ast.parse(stub_path.read_text(encoding="utf-8"))
    client_imports = {
        alias.asname or alias.name: declaration.module
        for declaration in declarations.body
        if isinstance(declaration, ast.ImportFrom)
        and declaration.level == 1
        for alias in declaration.names
        if alias.name.endswith("Client")
        and alias.name != "ConnectorHttpClient"
    }

    assert client_imports == connectors.CLIENT_REGISTRY
