# ------------------------------------------------------------
# Copyright (c) Microsoft Corporation.  All rights reserved.
# ------------------------------------------------------------

"""Validate connector sample imports and generated API call signatures."""

from __future__ import annotations

import argparse
import ast
import importlib
import importlib.util
import inspect
import sys
from dataclasses import dataclass
from pathlib import Path
from types import ModuleType, UnionType
from typing import Any, Literal, Union, get_args, get_origin, get_type_hints


@dataclass(frozen=True)
class ValidationIssue:
    """Describe an API compatibility issue in a sample."""

    path: Path
    line: int
    message: str


class SampleVisitor(ast.NodeVisitor):
    """Validate one sample against imported connector declarations."""

    def __init__(self, path: Path, modules: dict[str, ModuleType]) -> None:
        """Initialize the visitor for a sample path and connector modules."""
        self.path = path
        self.modules = modules
        self.imported_symbols: dict[str, Any] = {}
        self.client_variables: dict[str, type[Any]] = {}
        self.variable_types: dict[str, type[Any]] = {}
        self.issues: list[ValidationIssue] = []

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        """Resolve imports from concrete connector modules."""
        module_name = node.module or ""
        if not module_name.startswith("azure.connectors"):
            return

        module = self.modules.get(module_name)
        if module is None:
            self._add_issue(node, f"connector module '{module_name}' does not exist")
            return

        for imported_name in node.names:
            if imported_name.name == "*":
                self._add_issue(node, "wildcard connector imports cannot be validated")
                continue

            if not hasattr(module, imported_name.name):
                self._add_issue(
                    node,
                    f"'{imported_name.name}' does not exist in '{module_name}'",
                )
                continue

            local_name = imported_name.asname or imported_name.name
            self.imported_symbols[local_name] = getattr(module, imported_name.name)

    def visit_Assign(self, node: ast.Assign) -> None:
        """Track client instances and statically typed values assigned to names."""
        client_type = self._client_type_from_expression(node.value)
        value_type = self._infer_static_type(node.value)
        for target in node.targets:
            if isinstance(target, ast.Name):
                if client_type is not None:
                    self.client_variables[target.id] = client_type
                if value_type is not None:
                    self.variable_types[target.id] = value_type
        self.generic_visit(node)

    def visit_AsyncWith(self, node: ast.AsyncWith) -> None:
        """Track generated clients introduced by async context managers."""
        for item in node.items:
            client_type = self._client_type_from_expression(item.context_expr)
            if client_type is not None and isinstance(item.optional_vars, ast.Name):
                self.client_variables[item.optional_vars.id] = client_type
        self.generic_visit(node)

    def visit_Call(self, node: ast.Call) -> None:
        """Validate generated model construction and client method calls."""
        if isinstance(node.func, ast.Name):
            target = self.imported_symbols.get(node.func.id)
            if inspect.isclass(target):
                self._validate_signature(node, target, include_instance=False)
        elif isinstance(node.func, ast.Attribute):
            client_type = self._client_type_for_receiver(node.func.value)
            if client_type is not None:
                method_name = node.func.attr
                method = getattr(client_type, method_name, None)
                if method is None or not callable(method):
                    self._add_issue(
                        node,
                        f"'{client_type.__name__}' has no method '{method_name}'",
                    )
                else:
                    self._validate_signature(node, method, include_instance=True)

        self.generic_visit(node)

    def _client_type_from_expression(self, node: ast.AST) -> type[Any] | None:
        """Resolve a generated client type from a constructor expression."""
        if not isinstance(node, ast.Call) or not isinstance(node.func, ast.Name):
            return None

        target = self.imported_symbols.get(node.func.id)
        if inspect.isclass(target) and target.__name__.endswith("Client"):
            return target
        return None

    def _client_type_for_receiver(self, node: ast.AST) -> type[Any] | None:
        """Resolve the generated client type for a method receiver."""
        if isinstance(node, ast.Name):
            return self.client_variables.get(node.id)
        return self._client_type_from_expression(node)

    def _infer_static_type(self, node: ast.AST) -> type[Any] | None:
        """Infer the type of a literal, simple name, environment value, or cast."""
        if isinstance(node, ast.Name):
            return self.variable_types.get(node.id)

        try:
            return type(ast.literal_eval(node))
        except (ValueError, TypeError, SyntaxError):
            pass

        container_types: tuple[tuple[type[ast.AST], type[Any]], ...] = (
            (ast.Dict, dict),
            (ast.List, list),
            (ast.Set, set),
            (ast.Tuple, tuple),
        )
        for node_type, container_type in container_types:
            if isinstance(node, node_type):
                return container_type

        if not isinstance(node, ast.Call):
            return None

        if isinstance(node.func, ast.Name) and node.func.id in {
            "bool",
            "float",
            "int",
            "str",
        }:
            return {
                "bool": bool,
                "float": float,
                "int": int,
                "str": str,
            }[node.func.id]

        if (
            isinstance(node.func, ast.Attribute)
            and node.func.attr in {"get", "getenv"}
            and isinstance(node.func.value, ast.Name)
            and node.func.value.id == "os"
        ):
            return str

        if (
            isinstance(node.func, ast.Attribute)
            and node.func.attr == "get"
            and isinstance(node.func.value, ast.Attribute)
            and isinstance(node.func.value.value, ast.Name)
            and node.func.value.value.id == "os"
            and node.func.value.attr == "environ"
        ):
            return str

        return None

    def _validate_signature(
        self,
        node: ast.Call,
        callable_object: Any,
        *,
        include_instance: bool,
    ) -> None:
        """Validate an AST call against a runtime signature without executing it."""
        try:
            signature = inspect.signature(callable_object)
        except (TypeError, ValueError):
            return

        instance_argument = object()
        positional_arguments: list[Any] = list(node.args)
        if include_instance:
            positional_arguments.insert(0, instance_argument)

        keyword_arguments = {
            keyword.arg: keyword.value
            for keyword in node.keywords
            if keyword.arg is not None
        }
        has_unpacking = any(
            isinstance(argument, ast.Starred) for argument in node.args
        ) or any(keyword.arg is None for keyword in node.keywords)

        try:
            if has_unpacking:
                bound_arguments = signature.bind_partial(
                    *positional_arguments,
                    **keyword_arguments,
                )
            else:
                bound_arguments = signature.bind(
                    *positional_arguments,
                    **keyword_arguments,
                )
        except TypeError as error:
            name = getattr(callable_object, "__qualname__", repr(callable_object))
            self._add_issue(node, f"call to '{name}' is invalid: {error}")
            return

        try:
            type_hints = get_type_hints(callable_object)
        except (NameError, TypeError):
            type_hints = {}

        for parameter_name, argument_node in bound_arguments.arguments.items():
            if argument_node is instance_argument or not isinstance(
                argument_node,
                ast.AST,
            ):
                continue

            parameter = signature.parameters[parameter_name]
            annotation = type_hints.get(parameter_name, parameter.annotation)
            self._validate_literal_type(
                argument_node,
                annotation,
                parameter_name,
            )

    def _validate_literal_type(
        self,
        node: ast.AST,
        annotation: Any,
        parameter_name: str,
    ) -> None:
        """Validate a statically resolvable value against an annotation."""
        try:
            value = ast.literal_eval(node)
        except (ValueError, TypeError, SyntaxError):
            value_type = self._infer_static_type(node)
            if value_type is None or _type_matches_annotation(
                value_type,
                annotation,
            ):
                return
        else:
            if _value_matches_annotation(value, annotation):
                return
            value_type = type(value)

        annotation_name = (
            getattr(annotation, "__name__", str(annotation))
            if get_origin(annotation) is None
            else str(annotation).replace("typing.", "")
        )
        self._add_issue(
            node,
            f"argument '{parameter_name}' has type '{value_type.__name__}', "
            f"expected '{annotation_name}'",
        )

    def _add_issue(self, node: ast.AST, message: str) -> None:
        """Record an issue at an AST node."""
        self.issues.append(
            ValidationIssue(
                path=self.path,
                line=getattr(node, "lineno", 1),
                message=message,
            )
        )


def _value_matches_annotation(value: Any, annotation: Any) -> bool:
    """Return whether a literal value is compatible with an annotation."""
    if annotation is Any or annotation is inspect.Parameter.empty:
        return True

    origin = get_origin(annotation)
    annotation_arguments = get_args(annotation)
    if origin in (Union, UnionType):
        return any(
            _value_matches_annotation(value, item_type)
            for item_type in annotation_arguments
        )

    if origin is Literal:
        return any(
            type(value) is type(literal_value) and value == literal_value
            for literal_value in annotation_arguments
        )

    if origin in (list, dict, tuple, set):
        return type(value) is origin

    if annotation is float:
        return type(value) in (int, float)

    if inspect.isclass(annotation):
        return type(value) is annotation

    return True


def _type_matches_annotation(value_type: type[Any], annotation: Any) -> bool:
    """Return whether a statically inferred type is compatible with an annotation."""
    if annotation is Any or annotation is inspect.Parameter.empty:
        return True

    origin = get_origin(annotation)
    annotation_arguments = get_args(annotation)
    if origin in (Union, UnionType):
        return any(
            _type_matches_annotation(value_type, item_type)
            for item_type in annotation_arguments
        )

    if origin is Literal:
        return any(
            value_type is type(literal_value)
            for literal_value in annotation_arguments
        )

    if origin in (list, dict, tuple, set):
        return value_type is origin

    if annotation is float:
        return value_type in (int, float)

    if inspect.isclass(annotation):
        return value_type is annotation

    return True


def load_connector_modules(source_root: Path) -> dict[str, ModuleType]:
    """Import connector modules from the checked-out source tree."""
    connector_package = importlib.import_module("azure.connectors")
    modules: dict[str, ModuleType] = {
        "azure.connectors": connector_package,
    }
    for module_path in sorted((source_root / "azure" / "connectors").glob("*.py")):
        if module_path.name == "__init__.py":
            continue

        module_name = f"azure.connectors.{module_path.stem}"
        module = importlib.import_module(module_name)
        resolved_path = Path(module.__file__ or "").resolve()
        if resolved_path != module_path.resolve():
            raise RuntimeError(
                f"Module '{module_name}' resolved to '{resolved_path}', "
                f"not '{module_path.resolve()}'."
            )
        modules[module_name] = module
    return modules


def validate_samples(repo_root: Path) -> tuple[list[Path], list[ValidationIssue]]:
    """Validate every connector usage sample in the repository."""
    source_root = repo_root / "src"
    sys.path.insert(0, str(source_root))
    modules = load_connector_modules(source_root)
    sample_paths = sorted(
        (repo_root / "samples" / "sample_connector_usage").glob("*.py")
    )
    issues: list[ValidationIssue] = []

    for sample_path in sample_paths:
        module_name = f"sample_validation_{sample_path.stem}"
        specification = importlib.util.spec_from_file_location(
            module_name,
            sample_path,
        )
        if specification is None or specification.loader is None:
            issues.append(
                ValidationIssue(
                    path=sample_path,
                    line=1,
                    message="sample import specification could not be created",
                )
            )
            continue

        try:
            module = importlib.util.module_from_spec(specification)
            specification.loader.exec_module(module)
        except Exception as error:
            issues.append(
                ValidationIssue(
                    path=sample_path,
                    line=1,
                    message=f"sample import failed: {error!r}",
                )
            )
            continue

        try:
            tree = ast.parse(sample_path.read_text(encoding="utf-8"))
        except SyntaxError as error:
            issues.append(
                ValidationIssue(
                    path=sample_path,
                    line=error.lineno or 1,
                    message=f"syntax error: {error.msg}",
                )
            )
            continue

        visitor = SampleVisitor(sample_path, modules)
        visitor.visit(tree)
        issues.extend(visitor.issues)

    return sample_paths, issues


def main() -> int:
    """Run connector sample validation and print actionable diagnostics."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=Path(__file__).resolve().parents[1],
        help="Path to the connectors-python-sdk repository.",
    )
    arguments = parser.parse_args()
    repo_root = arguments.repo_root.resolve()
    sample_paths, issues = validate_samples(repo_root)

    for issue in issues:
        relative_path = issue.path.relative_to(repo_root)
        print(f"{relative_path}:{issue.line}: {issue.message}")

    print(
        f"Validated {len(sample_paths)} sample files; "
        f"found {len(issues)} API compatibility issue(s)."
    )
    return 1 if issues else 0


if __name__ == "__main__":
    raise SystemExit(main())
