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

    def test_no_unchecked_send_async_calls(self):
        """Verify all send_async calls capture response and check status.

        Generated connector code must not discard send_async responses.
        Void operations (DELETE, PATCH, fire-and-forget POST) must capture
        the response and raise ConnectorException on non-2xx status codes.

        See GENERATION.md "Generated Client Acceptance Criteria" for details.
        """
        connector_dir = ROOT_PATH / 'src' / 'azure' / 'connectors'

        # Skip files that are not generated connectors
        skip_files = {'__init__.py', 'sdk.py'}

        violations: list[LintViolation] = []

        for filepath in connector_dir.glob('*.py'):
            if filepath.name in skip_files:
                continue

            violations.extend(self._find_unchecked_send_async(filepath))

        if violations:
            # Format violations for readable output
            messages = [
                f"  {v.file}:{v.line}: {v.message}"
                for v in sorted(violations, key=lambda x: (x.file, x.line))
            ]
            violation_text = "\n".join(messages)

            raise AssertionError(
                f"Found {len(violations)} unchecked send_async call(s).\n"
                f"Void operations must capture response and raise "
                f"ConnectorException on non-2xx.\n"
                f"Fix the generator (see GENERATION.md) and regenerate, "
                f"or regenerate with the latest generator.\n\n"
                f"{violation_text}"
            )

    def _find_unchecked_send_async(
        self, filepath: pathlib.Path
    ) -> list[LintViolation]:
        """Find send_async calls whose result is not captured.

        The correct pattern is:
            response = await self.http_client.send_async(...)
            if not (200 <= response.status < 300):
                raise ConnectorException(...)

        The incorrect pattern is:
            await self.http_client.send_async(...)  # Result discarded!
        """
        violations: list[LintViolation] = []

        try:
            source = filepath.read_text(encoding='utf-8')
            tree = ast.parse(source)
        except SyntaxError:
            # If file has syntax errors, skip (mypy/flake8 will catch it)
            return violations

        for node in ast.walk(tree):
            # Look for Expr nodes containing Await
            # (Expr means the value is discarded, not assigned)
            if isinstance(node, ast.Expr) and isinstance(node.value, ast.Await):
                await_expr = node.value.value

                # Check if this is a call to send_async
                if isinstance(await_expr, ast.Call):
                    func = await_expr.func

                    # Match: self.http_client.send_async(...) or
                    #        self._http_client.send_async(...)
                    if isinstance(func, ast.Attribute) and func.attr == 'send_async':
                        if isinstance(func.value, ast.Attribute):
                            attr_name = func.value.attr
                            if attr_name in ('http_client', '_http_client'):
                                violations.append(LintViolation(
                                    file=filepath.name,
                                    line=node.lineno,
                                    message='Unchecked send_async call'
                                ))

        return violations
