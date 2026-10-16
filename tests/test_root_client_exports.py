# ------------------------------------------------------------
# Copyright (c) Microsoft Corporation.  All rights reserved.
# ------------------------------------------------------------

"""Tests for lazy package-root connector exports."""

from __future__ import annotations

import subprocess
import sys

import pytest

import azure.connectors as connectors
import azure.connectors.aio as aio_connectors


@pytest.mark.parametrize(
    ("package_name", "module_name"),
    [
        ("azure.connectors", "azure.connectors.arm"),
        ("azure.connectors.aio", "azure.connectors.aio.arm"),
    ],
)
def test_client_export_is_loaded_lazily(
    package_name: str,
    module_name: str,
) -> None:
    """Keep connector modules unloaded until a package export is requested."""
    script = f"""
import importlib
import sys

package = importlib.import_module("{package_name}")
assert "{module_name}" not in sys.modules
client_type = package.ArmClient
assert "{module_name}" in sys.modules
assert client_type is sys.modules["{module_name}"].ArmClient
"""

    subprocess.run([sys.executable, "-c", script], check=True)


@pytest.mark.parametrize("package", [connectors, aio_connectors])
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
    """Expose every generated client through both package roots."""
    expected_names = set(connectors.CLIENT_REGISTRY)

    assert expected_names <= set(dir(connectors))
    assert expected_names <= set(connectors.__all__)
    assert expected_names <= set(dir(aio_connectors))
    assert expected_names <= set(aio_connectors.__all__)
