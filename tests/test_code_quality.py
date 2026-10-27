# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

import ast
import pathlib
import subprocess
import sys
import unittest
from typing import NamedTuple


ROOT_PATH = pathlib.Path(__file__).parent.parent


class LintViolation(NamedTuple):
    """A lint violation in generated code."""

    file: str
    line: int
    message: str


class TestCodeQuality(unittest.TestCase):
    def test_mypy(self):
        try:
            import mypy  # NoQA
        except ImportError:
            raise unittest.SkipTest('mypy module is missing')

        src_path = ROOT_PATH / 'src' / 'azure' / 'connectors'
        try:
            subprocess.run(
                [sys.executable, '-m', 'mypy', str(src_path),
                 '--ignore-missing-imports'],
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=str(ROOT_PATH))
        except subprocess.CalledProcessError as ex:
            output = ex.output.decode()
            raise AssertionError(
                f'mypy validation failed:\n{output}') from None

    def test_flake8(self):
        try:
            import flake8  # NoQA
        except ImportError:
            raise unittest.SkipTest('flake8 module is missing')

        config_path = ROOT_PATH / '.flake8'
        if not config_path.exists():
            raise unittest.SkipTest('could not locate the .flake8 file')

        try:
            subprocess.run(
                [sys.executable, '-m', 'flake8', '--config', str(config_path),
                 "--extend-ignore=D"],
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=str(ROOT_PATH))
        except subprocess.CalledProcessError as ex:
            output = ex.output.decode()
            raise AssertionError(
                f'flake8 validation failed:\n{output}') from None

    def test_no_unchecked_send_calls(self):
        """Verify all async send calls capture their response.

        Generated connector code must not discard send responses.
        This check catches the most egregious error: calling send
        without capturing the response at all (fire-and-forget). It does
        NOT validate that the captured response is checked with the correct
        status guard pattern — that requires manual review or regeneration.

        See GENERATION.md "Generated Client Acceptance Criteria" for details.
        """
        connector_dir = ROOT_PATH / 'src' / 'azure' / 'connectors'
        skip_files = {'__init__.py', 'sdk.py'}

        violations: list[LintViolation] = []

        connector_paths = sorted(connector_dir.glob('*.py'))
        for filepath in connector_paths:
            if filepath.name in skip_files:
                continue

            violations.extend(self._find_unchecked_send(filepath))

        if violations:
            messages = [
                f"  {v.file}:{v.line}: {v.message}"
                for v in sorted(
                    violations,
                    key=lambda violation: (violation.file, violation.line),
                )
            ]
            violation_text = "\n".join(messages)

            raise AssertionError(
                f"Found {len(violations)} unchecked send call(s).\n"
                f"All async send calls must capture the response.\n"
                f"Fix the generator (see GENERATION.md) and regenerate, "
                f"or regenerate with the latest generator.\n\n"
                f"{violation_text}"
            )

    def test_only_explicit_resource_deletes_accept_not_found(self):
        """Verify only explicitly idempotent resource deletes accept HTTP 404."""
        connector_dir = ROOT_PATH / 'src' / 'azure' / 'connectors'
        expected_operations = {
            ('arm.py', 'deployments_delete'),
        }
        connector_paths = sorted(connector_dir.glob('*.py'))
        actual_operations: set[tuple[str, str]] = set()

        for filepath in connector_paths:
            if filepath.name.startswith('_'):
                continue

            tree = ast.parse(filepath.read_text(encoding='utf-8'))
            for function in (
                node for node in ast.walk(tree)
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
            ):
                if not self._sends_request(function):
                    continue

                accepts_not_found = self._accepts_not_found(function)
                if accepts_not_found:
                    relative_path = filepath.relative_to(connector_dir).as_posix()
                    actual_operations.add((relative_path, function.name))
                    assert self._uses_http_method(function, 'DELETE'), (
                        f'{relative_path}:{function.lineno}: '
                        f'{function.name} accepts 404 without using HTTP DELETE'
                    )

        assert actual_operations == expected_operations, (
            'Generated HTTP 404 guards do not match the explicit idempotent '
            f'resource-delete policy: {sorted(actual_operations)}'
        )

    @staticmethod
    def _sends_request(function: ast.AST) -> bool:
        """Return whether a function sends an HTTP request."""
        return any(
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and node.func.attr == 'send'
            for node in ast.walk(function)
        )

    @staticmethod
    def _uses_http_method(function: ast.AST, method: str) -> bool:
        """Return whether a function sends the specified HTTP method."""
        return any(
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and node.func.attr == 'send'
            and node.args
            and isinstance(node.args[0], ast.Constant)
            and node.args[0].value == method
            for node in ast.walk(function)
        )

    @staticmethod
    def _accepts_not_found(function: ast.AST) -> bool:
        """Return whether a function returns None for HTTP 404."""
        for node in ast.walk(function):
            if not isinstance(node, ast.If) or not isinstance(node.test, ast.Compare):
                continue

            comparison = node.test
            if (
                len(comparison.ops) == 1
                and isinstance(comparison.ops[0], ast.Eq)
                and len(comparison.comparators) == 1
                and isinstance(comparison.comparators[0], ast.Constant)
                and comparison.comparators[0].value == 404
                and any(
                    isinstance(statement, ast.Return)
                    and isinstance(statement.value, ast.Constant)
                    and statement.value.value is None
                    for statement in node.body
                )
            ):
                return True

        return False

    def _find_unchecked_send(
        self, filepath: pathlib.Path
    ) -> list[LintViolation]:
        """Find async send calls whose result is not captured.

        Detects the pattern:
            self.http_client.send(...)  # Result discarded!
            await self.http_client.send(...)  # Result discarded!

        This is a minimal check that catches discarded responses. It does
        NOT validate that captured responses are checked with the correct
        guard (e.g., `if not (200 <= response.status < 300):`).
        """
        violations: list[LintViolation] = []

        try:
            source = filepath.read_text(encoding='utf-8')
            tree = ast.parse(source)
        except SyntaxError:
            # NOTE(victoriahall): Syntax errors are caught by mypy/flake8.
            return violations

        for node in ast.walk(tree):
            # NOTE(victoriahall): ast.Expr means the value is discarded, not assigned.
            if not isinstance(node, ast.Expr):
                continue

            expression = node.value
            if isinstance(expression, ast.Await):
                expression = expression.value

            if not isinstance(expression, ast.Call):
                continue

            function = expression.func
            if not isinstance(function, ast.Attribute) or function.attr != 'send':
                continue

            if isinstance(function.value, ast.Attribute):
                attribute_name = function.value.attr
                if attribute_name in ('http_client', '_http_client'):
                    violations.append(LintViolation(
                        file=filepath.relative_to(ROOT_PATH).as_posix(),
                        line=node.lineno,
                        message='Unchecked send call'
                    ))

        return violations
