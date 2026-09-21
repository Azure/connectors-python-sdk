# ------------------------------------------------------------
# Copyright (c) Microsoft Corporation.  All rights reserved.
# ------------------------------------------------------------

"""Tests for API documentation generation and validation."""

from __future__ import annotations

from pathlib import Path

import pytest

from scripts import generate_api_reference, validate_api_docs


RENDERED_API_CONTENT = '<div class="doc doc-object doc-module"></div>'


def test_defined_public_names_filters_source_symbols(tmp_path: Path) -> None:
    """Include public declarations once while excluding private and typing names."""
    source_path = tmp_path / "synthetic.py"
    source_path.write_text(
        """from typing import ParamSpec, TypeVar, TypeVarTuple

ResponseT = TypeVar("ResponseT")
ParametersT = ParamSpec("ParametersT")
ItemsT = TypeVarTuple("ItemsT")
PUBLIC_VALUE = 1
duplicate = 1
duplicate = 2
private_value = 1
_hidden_value = 1
x = 1

class PublicModel:
    pass

class _PrivateModel:
    pass

def public_function():
    pass

def _private_function():
    pass

async def public_operation():
    pass
""",
        encoding="utf-8",
    )

    assert generate_api_reference._defined_public_names(source_path) == [
        "PUBLIC_VALUE",
        "duplicate",
        "private_value",
        "PublicModel",
        "public_function",
        "public_operation",
    ]


def test_defined_public_names_handles_empty_module(tmp_path: Path) -> None:
    """Return no API symbols for a module without public declarations."""
    source_path = tmp_path / "empty.py"
    source_path.write_text('"""No public declarations."""\n', encoding="utf-8")

    assert generate_api_reference._defined_public_names(source_path) == []


def _create_source_tree(package_root: Path) -> None:
    """Create a minimal connector package for validator tests."""
    sdk_root = package_root / "sdk"
    sdk_root.mkdir(parents=True)
    (package_root / "connector.py").write_text("PUBLIC_VALUE = 1\n", encoding="utf-8")
    (sdk_root / "core.py").write_text("PUBLIC_VALUE = 1\n", encoding="utf-8")


def _write_api_page(
    site_root: Path,
    section: str,
    module_name: str,
    content: str = RENDERED_API_CONTENT,
) -> Path:
    """Write one built API page and return its path."""
    page_path = site_root / "api" / section / module_name / "index.html"
    page_path.parent.mkdir(parents=True, exist_ok=True)
    page_path.write_text(content, encoding="utf-8")
    return page_path


@pytest.fixture
def documentation_tree(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Create matching source and built documentation trees."""
    package_root = tmp_path / "src" / "azure" / "connectors"
    site_root = tmp_path / "site"
    _create_source_tree(package_root)
    monkeypatch.setattr(validate_api_docs, "PACKAGE_ROOT", package_root)
    _write_api_page(site_root, "core", "core")
    _write_api_page(site_root, "connectors", "connector")
    api_landing_page = site_root / "api" / "index.html"
    api_landing_page.parent.mkdir(parents=True, exist_ok=True)
    api_landing_page.write_text("<html>API reference</html>", encoding="utf-8")
    return site_root


def test_validate_api_docs_accepts_complete_site(documentation_tree: Path) -> None:
    """Accept built pages containing rendered module API content."""
    assert validate_api_docs.validate_api_docs(documentation_tree) == []


def test_validate_api_docs_reports_missing_page(documentation_tree: Path) -> None:
    """Report a source module whose built page is missing."""
    (documentation_tree / "api" / "connectors" / "connector" / "index.html").unlink()

    assert validate_api_docs.validate_api_docs(documentation_tree) == [
        "Missing connectors API pages: connector",
    ]


@pytest.mark.parametrize("page_content", ["", "<html></html>"])
def test_validate_api_docs_rejects_page_without_api_content(
    documentation_tree: Path,
    page_content: str,
) -> None:
    """Reject empty pages and nonempty HTML shells without API symbols."""
    page_path = documentation_tree / "api" / "connectors" / "connector" / "index.html"
    page_path.write_text(page_content, encoding="utf-8")

    assert validate_api_docs.validate_api_docs(documentation_tree) == [
        "Missing connectors API pages: connector",
    ]


def test_validate_api_docs_reports_stale_page(documentation_tree: Path) -> None:
    """Report a built API page without a corresponding source module."""
    _write_api_page(documentation_tree, "connectors", "stale")

    assert validate_api_docs.validate_api_docs(documentation_tree) == [
        "Unexpected connectors API pages: stale",
    ]
