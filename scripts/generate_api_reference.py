# ------------------------------------------------------------
# Copyright (c) Microsoft Corporation.  All rights reserved.
# ------------------------------------------------------------

"""Generate MkDocs API pages from the Python source tree."""

from __future__ import annotations

import ast
from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
PACKAGE_ROOT = REPOSITORY_ROOT / "src" / "azure" / "connectors"
API_ROOT = Path("api")


def _is_public_name(name: str) -> bool:
    """Return whether a source-level name belongs in the API reference."""
    return not name.startswith("_") and len(name) > 1


def _is_type_variable(node: ast.AST | None) -> bool:
    """Return whether an assignment creates a typing type variable."""
    if not isinstance(node, ast.Call):
        return False

    function = node.func
    return isinstance(function, ast.Name) and function.id in {
        "ParamSpec",
        "TypeVar",
        "TypeVarTuple",
    }


def _defined_public_names(source_path: Path) -> list[str]:
    """Collect public symbols defined directly by a Python module."""
    tree = ast.parse(source_path.read_text(encoding="utf-8"), filename=str(source_path))
    names: list[str] = []

    for node in tree.body:
        if isinstance(node, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
            if _is_public_name(node.name):
                names.append(node.name)
        elif isinstance(node, ast.Assign) and not _is_type_variable(node.value):
            names.extend(
                target.id
                for target in node.targets
                if isinstance(target, ast.Name) and _is_public_name(target.id)
            )
        elif isinstance(node, ast.AnnAssign) and not _is_type_variable(node.value):
            if isinstance(node.target, ast.Name) and _is_public_name(node.target.id):
                names.append(node.target.id)

    return list(dict.fromkeys(names))


def _module_title(source_path: Path, names: list[str]) -> str:
    """Create a readable navigation title for a source module."""
    client_names = [name for name in names if name.endswith("Client")]
    if source_path.parent == PACKAGE_ROOT and len(client_names) == 1:
        return client_names[0]

    return source_path.stem.replace("_", " ").title()


def _write_module_page(
    source_path: Path,
    section: str,
    module_name: str,
    names: list[str],
) -> Path:
    """Write one virtual Markdown page for a Python module."""
    import mkdocs_gen_files

    document_path = API_ROOT / section / f"{source_path.stem}.md"
    title = _module_title(source_path, names)

    with mkdocs_gen_files.open(document_path, "w") as document:
        document.write(f"# {title}\n\n")
        document.write(f"::: {module_name}\n")
        document.write("    options:\n")
        document.write("      members:\n")
        for name in names:
            document.write(f"        - {name}\n")

    mkdocs_gen_files.set_edit_path(
        document_path,
        source_path.relative_to(REPOSITORY_ROOT),
    )
    return document_path


def _source_modules(directory: Path) -> list[Path]:
    """Return public Python modules from a package directory."""
    return sorted(
        path
        for path in directory.glob("*.py")
        if path.name != "__init__.py" and not path.stem.startswith("_")
    )


def _generate_reference() -> None:
    """Generate API pages and the literate navigation file."""
    import mkdocs_gen_files

    navigation = mkdocs_gen_files.Nav()
    navigation["Home"] = "index.md"
    navigation[("Guides", "Connection setup")] = "connection-setup.md"
    navigation[("Guides", "SDK-type bindings")] = "sdk-type-bindings.md"
    navigation[("API reference",)] = "api/index.md"

    sections = (
        ("Core SDK", "core", PACKAGE_ROOT / "sdk", "azure.connectors.sdk"),
        ("Connectors", "connectors", PACKAGE_ROOT, "azure.connectors"),
    )

    for navigation_title, section, directory, package_name in sections:
        navigation[("API reference", navigation_title)] = f"api/{section}/index.md"
        with mkdocs_gen_files.open(API_ROOT / section / "index.md", "w") as index:
            index.write(f"# {navigation_title}\n")

        for source_path in _source_modules(directory):
            names = _defined_public_names(source_path)
            if not names:
                continue

            module_name = f"{package_name}.{source_path.stem}"
            document_path = _write_module_page(
                source_path=source_path,
                section=section,
                module_name=module_name,
                names=names,
            )
            navigation[
                (
                    "API reference",
                    navigation_title,
                    _module_title(source_path, names),
                )
            ] = document_path.as_posix()

    with mkdocs_gen_files.open("SUMMARY.md", "w") as navigation_file:
        navigation_file.writelines(navigation.build_literate_nav())


if __name__ in {"__main__", "<run_path>"}:
    _generate_reference()
