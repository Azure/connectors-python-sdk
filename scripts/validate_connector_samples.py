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

from azure.core.async_paging import AsyncItemPaged
from azure.core.paging import ItemPaged


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
        self.credential_modes: dict[str, str] = {}
        self.scoped_sync_credentials: set[int] = set()
        self.scoped_async_credentials: set[int] = set()
        self.awaited_calls: set[int] = set()
        self.issues: list[ValidationIssue] = []

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        """Resolve imports from concrete connector modules."""
        module_name = node.module or ""
        if module_name in {"azure.identity", "azure.identity.aio"}:
            mode = "async" if module_name.endswith(".aio") else "sync"
            for imported_name in node.names:
                if imported_name.name == "DefaultAzureCredential":
                    local_name = imported_name.asname or imported_name.name
                    self.credential_modes[local_name] = mode
            return

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
        self.visit(node.value)
        for target in node.targets:
            if isinstance(target, ast.Name):
                if (
                    isinstance(node.value, ast.IfExp)
                    and isinstance(node.value.body, ast.Name)
                    and isinstance(node.value.test, ast.Name)
                    and node.value.body.id == target.id == node.value.test.id
                    and isinstance(node.value.orelse, ast.List)
                    and not node.value.orelse.elts
                    and self.variable_types.get(target.id) is list
                ):
                    self._add_issue(node, "remove redundant fallback for collected items")
                if (
                    target.id == "result"
                    and isinstance(node.value, ast.ListComp)
                    and any(generator.is_async for generator in node.value.generators)
                ):
                    self._add_issue(
                        node, "capture collected items in a semantic name instead of 'result'"
                    )
                if client_type is not None:
                    self.client_variables[target.id] = client_type
                else:
                    self.client_variables.pop(target.id, None)
                if value_type is not None:
                    self.variable_types[target.id] = value_type
                else:
                    self.variable_types.pop(target.id, None)
            self.visit(target)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        """Keep local variable facts from leaking into another sample function."""
        self._visit_function(node)

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        """Validate synchronous functions with the same parameter scope rules."""
        self._visit_function(node)

    def _visit_function(self, node: ast.FunctionDef | ast.AsyncFunctionDef) -> None:
        """Clear inherited parameter facts and restore the enclosing scope after visiting."""
        for decorator in node.decorator_list:
            self.visit(decorator)
        self.visit(node.args)
        if node.returns is not None:
            self.visit(node.returns)
        variable_types = self.variable_types.copy()
        client_variables = self.client_variables.copy()
        parameters = [*node.args.posonlyargs, *node.args.args, *node.args.kwonlyargs]
        if node.args.vararg is not None:
            parameters.append(node.args.vararg)
        if node.args.kwarg is not None:
            parameters.append(node.args.kwarg)
        try:
            for parameter in parameters:
                self.variable_types.pop(parameter.arg, None)
                self.client_variables.pop(parameter.arg, None)
            for statement in node.body:
                self.visit(statement)
        finally:
            self.variable_types = variable_types
            self.client_variables = client_variables

    def visit_AsyncWith(self, node: ast.AsyncWith) -> None:
        """Track generated clients introduced by async context managers."""
        for item in node.items:
            if (
                isinstance(item.context_expr, ast.Call)
                and isinstance(item.context_expr.func, ast.Name)
                and self.credential_modes.get(item.context_expr.func.id) == "async"
            ):
                self.scoped_async_credentials.add(id(item.context_expr))

            client_type = self._client_type_from_expression(item.context_expr)
            if client_type is not None:
                if not self._is_async_client(client_type):
                    self._add_issue(
                        item.context_expr,
                        "synchronous connector clients must use a context manager",
                    )
                elif isinstance(item.optional_vars, ast.Name):
                    self.client_variables[item.optional_vars.id] = client_type
        self.generic_visit(node)

    def visit_With(self, node: ast.With) -> None:
        """Track generated clients introduced by synchronous context managers."""
        for item in node.items:
            if (
                isinstance(item.context_expr, ast.Call)
                and isinstance(item.context_expr.func, ast.Name)
                and self.credential_modes.get(item.context_expr.func.id) == "sync"
            ):
                self.scoped_sync_credentials.add(id(item.context_expr))

            client_type = self._client_type_from_expression(item.context_expr)
            if client_type is not None:
                if self._is_async_client(client_type):
                    self._add_issue(
                        item.context_expr,
                        "asynchronous connector clients must use an async context manager",
                    )
                elif isinstance(item.optional_vars, ast.Name):
                    self.client_variables[item.optional_vars.id] = client_type
        self.generic_visit(node)

    def visit_ListComp(self, node: ast.ListComp) -> None:
        """Validate list comprehensions with local target facts."""
        self._visit_comprehension(node)

    def visit_SetComp(self, node: ast.SetComp) -> None:
        """Validate set comprehensions with local target facts."""
        self._visit_comprehension(node)

    def visit_DictComp(self, node: ast.DictComp) -> None:
        """Validate dictionary comprehensions with local target facts."""
        self._visit_comprehension(node)

    def visit_GeneratorExp(self, node: ast.GeneratorExp) -> None:
        """Validate generator expressions without leaking target facts."""
        self._visit_comprehension(node)

    def _visit_comprehension(
        self, node: ast.ListComp | ast.SetComp | ast.DictComp | ast.GeneratorExp,
    ) -> None:
        """Visit iterables before binding targets and restore the enclosing facts."""
        variable_types = self.variable_types.copy()
        client_variables = self.client_variables.copy()
        try:
            for generator in node.generators:
                self._validate_pageable_iteration(
                    generator.iter,
                    is_async=bool(generator.is_async),
                )
                self.visit(generator.iter)
                for target in ast.walk(generator.target):
                    if isinstance(target, ast.Name) and isinstance(target.ctx, ast.Store):
                        self.variable_types.pop(target.id, None)
                        self.client_variables.pop(target.id, None)
                self.visit(generator.target)
                for condition in generator.ifs:
                    self.visit(condition)
            if isinstance(node, ast.DictComp):
                self.visit(node.key)
                self.visit(node.value)
            else:
                self.visit(node.elt)
        finally:
            self.variable_types = variable_types
            self.client_variables = client_variables

    def visit_Await(self, node: ast.Await) -> None:
        """Reject awaiting a generated pageable operation instead of iterating it."""
        call = node.value
        if isinstance(call, ast.Call) and isinstance(call.func, ast.Attribute):
            self.awaited_calls.add(id(call))
            client_type = self._client_type_for_receiver(call.func.value)
            method = getattr(client_type, call.func.attr, None)
            pageable_type = self._get_pageable_type(method)
            if pageable_type is AsyncItemPaged:
                self._add_issue(node, f"'{call.func.attr}' must be consumed with async for")
            elif pageable_type is ItemPaged:
                self._add_issue(node, f"'{call.func.attr}' must be consumed with for")
            elif method is not None and not inspect.iscoroutinefunction(method):
                self._add_issue(node, f"synchronous method '{call.func.attr}' cannot be awaited")
        self.generic_visit(node)

    def visit_AsyncFor(self, node: ast.AsyncFor) -> None:
        """Require asynchronous iteration only for asynchronous pagers."""
        self._validate_pageable_iteration(node.iter, is_async=True)
        self.generic_visit(node)

    def visit_For(self, node: ast.For) -> None:
        """Require synchronous iteration only for synchronous pagers."""
        self._validate_pageable_iteration(node.iter, is_async=False)
        self.generic_visit(node)

    def visit_BoolOp(self, node: ast.BoolOp) -> None:
        """Reject repeated simple-name conditions in sample consumer code."""
        if isinstance(node.op, ast.And):
            names = [value.id for value in node.values if isinstance(value, ast.Name)]
            if len(names) != len(set(names)):
                self._add_issue(node, "remove repeated conditions")
        self.generic_visit(node)

    def visit_Call(self, node: ast.Call) -> None:
        """Validate generated model construction and client method calls."""
        if (
            isinstance(node.func, ast.Name)
            and node.func.id in self.credential_modes
        ):
            credential_mode = self.credential_modes[node.func.id]
            if (
                credential_mode == "async"
                and id(node) not in self.scoped_async_credentials
            ):
                self._add_issue(
                    node,
                    "asynchronous DefaultAzureCredential must use an async context manager",
                )
            elif (
                credential_mode == "sync"
                and id(node) not in self.scoped_sync_credentials
            ):
                self._add_issue(
                    node,
                    "synchronous DefaultAzureCredential must use a context manager",
                )

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
                    if (
                        inspect.iscoroutinefunction(method)
                        and id(node) not in self.awaited_calls
                    ):
                        self._add_issue(
                            node,
                            f"asynchronous method '{method_name}' must be awaited",
                        )
            else:
                receiver_type = self._infer_static_type(node.func.value)
                if receiver_type in {list, dict, set, tuple} and not hasattr(
                    receiver_type, node.func.attr
                ):
                    self._add_issue(
                        node, f"'{receiver_type.__name__}' has no method '{node.func.attr}'"
                    )

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

    @staticmethod
    def _is_async_client(client_type: type[Any]) -> bool:
        """Return whether a generated client belongs to the aio package."""
        return client_type.__module__.startswith("azure.connectors.aio.")

    @staticmethod
    def _get_pageable_type(method: Any) -> type[Any] | None:
        """Resolve the Azure Core pager type returned by a generated method."""
        if method is None:
            return None

        try:
            method_module = importlib.import_module(method.__module__)
            return_annotation = get_type_hints(
                method,
                globalns=vars(method_module),
            ).get("return")
        except (NameError, TypeError):
            return_annotation = inspect.signature(method).return_annotation

        return_origin = get_origin(return_annotation) or return_annotation
        if return_origin in {ItemPaged, AsyncItemPaged}:
            return return_origin
        return None

    def _validate_pageable_iteration(
        self,
        expression: ast.AST,
        *,
        is_async: bool,
    ) -> None:
        """Validate that a generated pager uses its matching iteration mode."""
        if not isinstance(expression, ast.Call) or not isinstance(
            expression.func,
            ast.Attribute,
        ):
            return

        client_type = self._client_type_for_receiver(expression.func.value)
        method = getattr(client_type, expression.func.attr, None)
        pageable_type = self._get_pageable_type(method)
        if pageable_type is ItemPaged and is_async:
            self._add_issue(
                expression,
                f"'{expression.func.attr}' must be consumed with for",
            )
        elif pageable_type is AsyncItemPaged and not is_async:
            self._add_issue(
                expression,
                f"'{expression.func.attr}' must be consumed with async for",
            )

    def _infer_static_type(self, node: ast.AST) -> type[Any] | None:
        """Infer the type of a literal, simple name, environment value, or cast."""
        if isinstance(node, ast.Name):
            return self.variable_types.get(node.id)

        if isinstance(node, ast.IfExp):
            body_type = self._infer_static_type(node.body)
            if body_type is not None and body_type is self._infer_static_type(node.orelse):
                return body_type
            return None

        try:
            return type(ast.literal_eval(node))
        except (ValueError, TypeError, SyntaxError):
            pass

        container_types: tuple[tuple[type[ast.AST], type[Any]], ...] = (
            (ast.Dict, dict),
            (ast.DictComp, dict),
            (ast.List, list),
            (ast.ListComp, list),
            (ast.Set, set),
            (ast.SetComp, set),
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
    aio_package = importlib.import_module("azure.connectors.aio")
    modules: dict[str, ModuleType] = {
        "azure.connectors": connector_package,
        "azure.connectors.aio": aio_package,
    }
    connector_root = source_root / "azure" / "connectors"
    module_paths = [
        *connector_root.glob("*.py"),
        *(connector_root / "aio").glob("*.py"),
    ]
    for module_path in sorted(module_paths):
        if module_path.name == "__init__.py":
            continue

        package_name = (
            "azure.connectors.aio"
            if module_path.parent.name == "aio"
            else "azure.connectors"
        )
        module_name = f"{package_name}.{module_path.stem}"
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
    sample_root = repo_root / "samples" / "sample_connector_usage"
    sample_paths = sorted(
        [
            *sample_root.glob("sample_connector_usage_*.py"),
            *(sample_root / "aio").glob("sample_connector_usage_*.py"),
        ]
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
