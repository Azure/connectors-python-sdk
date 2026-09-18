# ------------------------------------------------------------
# Copyright (c) Microsoft Corporation.  All rights reserved.
# ------------------------------------------------------------

"""Validate that built API documentation matches the Python source tree."""

from __future__ import annotations

import argparse
from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
PACKAGE_ROOT = REPOSITORY_ROOT / "src" / "azure" / "connectors"


def _source_module_names(directory: Path) -> set[str]:
    """Return public Python module names from a package directory."""
    return {
        path.stem
        for path in directory.glob("*.py")
        if path.name != "__init__.py" and not path.stem.startswith("_")
    }


def _built_module_names(directory: Path) -> set[str]:
    """Return module names represented by nonempty built HTML pages."""
    if not directory.is_dir():
        return set()

    return {
        path.parent.name
        for path in directory.glob("*/index.html")
        if path.stat().st_size > 0
    }


def _format_difference(label: str, values: set[str]) -> list[str]:
    """Format one validation difference for terminal output."""
    if not values:
        return []

    return [f"{label}: {', '.join(sorted(values))}"]


def validate_api_docs(site_directory: Path) -> list[str]:
    """Return validation errors for a built documentation site."""
    errors: list[str] = []
    api_directory = site_directory / "api"
    landing_page = api_directory / "index.html"

    if not landing_page.is_file() or landing_page.stat().st_size == 0:
        errors.append(f"Missing or empty API landing page: '{landing_page}'.")

    sections = (
        ("core", PACKAGE_ROOT / "sdk"),
        ("connectors", PACKAGE_ROOT),
    )

    for section, source_directory in sections:
        expected = _source_module_names(source_directory)
        actual = _built_module_names(api_directory / section)
        errors.extend(_format_difference(f"Missing {section} API pages", expected - actual))
        errors.extend(_format_difference(f"Unexpected {section} API pages", actual - expected))

    return errors


def main() -> int:
    """Validate command-line arguments and report API documentation coverage."""
    parser = argparse.ArgumentParser(
        description="Validate generated API documentation completeness.",
    )
    parser.add_argument(
        "--site-dir",
        type=Path,
        default=REPOSITORY_ROOT / "site",
        help="Built MkDocs site directory. Defaults to './site'.",
    )
    arguments = parser.parse_args()
    site_directory = arguments.site_dir.resolve()
    errors = validate_api_docs(site_directory)

    if errors:
        print("API documentation validation failed:")
        for error in errors:
            print(f"- {error}")
        return 1

    connector_count = len(_source_module_names(PACKAGE_ROOT))
    core_count = len(_source_module_names(PACKAGE_ROOT / "sdk"))
    print(
        "API documentation validation passed: "
        f"{core_count} core modules and {connector_count} connector modules.",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
