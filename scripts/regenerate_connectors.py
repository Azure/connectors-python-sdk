# ------------------------------------------------------------
# Copyright (c) Microsoft Corporation.  All rights reserved.
# ------------------------------------------------------------

"""Regenerate connector clients from committed Swagger snapshots."""

from __future__ import annotations

import argparse
import ast
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
from typing import Any


REPOSITORY_ROOT = Path(__file__).resolve().parent.parent
CONNECTOR_DIRECTORY = REPOSITORY_ROOT / "src" / "azure" / "connectors"
ASYNC_CONNECTOR_DIRECTORY = CONNECTOR_DIRECTORY / "aio"
SNAPSHOT_DIRECTORY = REPOSITORY_ROOT / "swagger-cache"
MANIFEST_PATH = REPOSITORY_ROOT / "generation.manifest.json"
CLIENT_REGISTRY_PATH = CONNECTOR_DIRECTORY / "_client_registry.py"
ROOT_STUB_PATH = CONNECTOR_DIRECTORY / "__init__.pyi"
ASYNC_ROOT_STUB_PATH = ASYNC_CONNECTOR_DIRECTORY / "__init__.pyi"
GENERATOR_REPOSITORY = "https://msazure.visualstudio.com/One/_git/AzureUX-BPM"


def canonical_sha256(path: Path) -> str:
    """Return the SHA-256 of UTF-8 text with canonical LF line endings."""
    text = path.read_text(encoding="utf-8").replace("\r\n", "\n").replace("\r", "\n")
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def file_sha256(path: Path) -> str:
    """Return the SHA-256 of a file's bytes."""
    return hashlib.sha256(path.read_bytes()).hexdigest()


def connector_names() -> list[str]:
    """Return the generated connector module names in ordinal order."""
    return sorted(
        path.stem
        for path in CONNECTOR_DIRECTORY.glob("*.py")
        if not path.name.startswith("_")
    )


def generated_client_name(path: Path) -> str:
    """Return the one generated client class in a connector module."""
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
    if len(client_names) != 1:
        raise ValueError(
            f"Expected one generated client in '{path}', found {len(client_names)}."
        )
    return client_names[0]


def write_package_artifacts(names: list[str]) -> None:
    """Write lazy export registries and static package-root type declarations."""
    entries = [
        (generated_client_name(CONNECTOR_DIRECTORY / f"{name}.py"), name)
        for name in names
    ]
    client_names = [client_name for client_name, _ in entries]
    if len(client_names) != len(set(client_names)):
        raise ValueError("Generated connector client class names must be unique.")

    registry_lines = [
        "# ------------------------------------------------------------",
        "# Copyright (c) Microsoft Corporation.  All rights reserved.",
        "# ------------------------------------------------------------",
        "",
        '"""Generated registry of public connector clients. Do not edit."""',
        "",
        "from typing import Final",
        "",
        "",
        "CLIENT_REGISTRY: Final[dict[str, str]] = {",
        *(
            f'    "{client_name}": "{module_name}",'
            for client_name, module_name in entries
        ),
        "}",
        "",
    ]
    CLIENT_REGISTRY_PATH.write_text(
        "\n".join(registry_lines),
        encoding="utf-8",
        newline="\n",
    )

    root_stub_lines = [
        "# ------------------------------------------------------------",
        "# Copyright (c) Microsoft Corporation.  All rights reserved.",
        "# ------------------------------------------------------------",
        "",
        '"""Generated type declarations for package-root exports. Do not edit."""',
        "",
        "from .sdk.client_base import ConnectorClientBase as ConnectorClientBase",
        "from .sdk.exceptions import ConnectorException as ConnectorException",
        "from .sdk.http_client import ConnectorHttpClient as ConnectorHttpClient",
        "from .sdk.http_client import ConnectorResponse as ConnectorResponse",
        "from .sdk.response import ConnectorResponseHook as ConnectorResponseHook",
        "from .sdk.response import ConnectorResponseSnapshot as ConnectorResponseSnapshot",
        "from .sdk.trigger_payload import TriggerCallbackBody as TriggerCallbackBody",
        "from .sdk.trigger_payload import TriggerCallbackPayload as TriggerCallbackPayload",
        *(
            f"from .{module_name} import {client_name} as {client_name}"
            for client_name, module_name in entries
        ),
        "",
        "__version__: str",
        "__all__: list[str]",
        "",
    ]
    ROOT_STUB_PATH.write_text(
        "\n".join(root_stub_lines),
        encoding="utf-8",
        newline="\n",
    )

    async_stub_lines = [
        "# ------------------------------------------------------------",
        "# Copyright (c) Microsoft Corporation.  All rights reserved.",
        "# ------------------------------------------------------------",
        "",
        '"""Generated type declarations for asynchronous package-root exports."""',
        "",
        *(
            f"from .{module_name} import {client_name} as {client_name}"
            for client_name, module_name in entries
        ),
        "",
        "__all__: list[str]",
        "",
    ]
    ASYNC_ROOT_STUB_PATH.write_text(
        "\n".join(async_stub_lines),
        encoding="utf-8",
        newline="\n",
    )


def validate_snapshot_inventory(names: list[str]) -> None:
    """Require exactly one committed Swagger snapshot per connector."""
    expected = {f"{name}.swagger.json" for name in names}
    actual = {path.name for path in SNAPSHOT_DIRECTORY.glob("*.swagger.json")}
    if expected != actual:
        missing = sorted(expected - actual)
        extra = sorted(actual - expected)
        raise ValueError(
            f"Swagger snapshot inventory mismatch. Missing: {missing}; extra: {extra}."
        )


def run_generator(compiler: Path, names: list[str], output_directory: Path) -> None:
    """Run the compiler against only the committed Swagger snapshots."""
    compiler_command = (
        ["dotnet", str(compiler)]
        if compiler.suffix.lower() == ".dll"
        else [str(compiler)]
    )
    command = [
        *compiler_command,
        str(output_directory),
        "--directClient",
        "--language=python",
        f"--connectors={','.join(names)}",
        f"--swagger-input-directory={SNAPSHOT_DIRECTORY}",
    ]
    result = subprocess.run(
        command,
        check=False,
        capture_output=True,
        encoding="utf-8",
        errors="replace",
        cwd=output_directory.parent,
    )
    failure_path = output_directory.parent / "failed.txt"
    failures = failure_path.read_text(encoding="utf-8") if failure_path.exists() else ""
    if result.returncode != 0 or failures:
        raise RuntimeError(
            "Connector generation failed.\n"
            f"Exit code: {result.returncode}\n"
            f"stdout:\n{result.stdout}\n"
            f"stderr:\n{result.stderr}\n"
            f"failures:\n{failures}"
        )

    expected = {f"{name}.py" for name in names}
    actual = {path.name for path in output_directory.glob("*.py")}
    async_output_directory = output_directory / "aio"
    actual_async = {
        path.name
        for path in async_output_directory.glob("*.py")
        if path.name != "__init__.py"
    }
    if expected != actual or expected != actual_async:
        raise RuntimeError(
            "Generated output inventory mismatch. "
            f"Sync missing: {sorted(expected - actual)}; "
            f"sync extra: {sorted(actual - expected)}; "
            f"async missing: {sorted(expected - actual_async)}; "
            f"async extra: {sorted(actual_async - expected)}."
        )


def build_manifest(
    compiler: Path,
    generator_revision: str,
    names: list[str],
    captured_at_utc: str,
) -> dict[str, Any]:
    """Build deterministic provenance for snapshots and generated clients."""
    return {
        "manifestVersion": 1,
        "generator": {
            "repository": GENERATOR_REPOSITORY,
            "tool": "CodefulSdkGenerator (LogicAppsCompiler)",
            "revision": generator_revision,
            "compilerSha256": file_sha256(compiler),
        },
        "command": (
            "python scripts/regenerate_connectors.py <LogicAppsCompiler> "
            f"--generator-revision={generator_revision} "
            f"--captured-at-utc={captured_at_utc}"
        ),
        "swaggerSource": {
            "kind": "live-arm-metadata",
            "location": "westus",
            "capturedAtUtc": captured_at_utc,
            "primarySubscriptionId": "29374ed4-cdf5-4269-8f87-a1c68dd60276",
            "subscriptionExceptions": {
                "f34b22a3-2202-4fb1-b040-1332bd928c84": [
                    "onedrive",
                    "orderful",
                    "universalprint",
                ]
            },
        },
        "packageArtifacts": {
            "clientRegistry": {
                "path": "src/azure/connectors/_client_registry.py",
                "sha256": canonical_sha256(CLIENT_REGISTRY_PATH),
            },
            "rootStub": {
                "path": "src/azure/connectors/__init__.pyi",
                "sha256": canonical_sha256(ROOT_STUB_PATH),
            },
            "asyncRootStub": {
                "path": "src/azure/connectors/aio/__init__.pyi",
                "sha256": canonical_sha256(ASYNC_ROOT_STUB_PATH),
            },
        },
        "connectors": [
            {
                "apiName": name,
                "outputFile": f"src/azure/connectors/{name}.py",
                "asyncOutputFile": f"src/azure/connectors/aio/{name}.py",
                "swaggerSnapshot": f"swagger-cache/{name}.swagger.json",
                "swaggerSha256": canonical_sha256(
                    SNAPSHOT_DIRECTORY / f"{name}.swagger.json"
                ),
                "outputSha256": canonical_sha256(CONNECTOR_DIRECTORY / f"{name}.py"),
                "asyncOutputSha256": canonical_sha256(
                    ASYNC_CONNECTOR_DIRECTORY / f"{name}.py"
                ),
            }
            for name in names
        ],
    }


def main() -> None:
    """Regenerate all clients and write their package and provenance artifacts."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("compiler", type=Path, help="Path to LogicAppsCompiler.dll or executable.")
    parser.add_argument(
        "--generator-revision",
        required=True,
        help="AzureUX-BPM commit containing the generator changes.",
    )
    parser.add_argument(
        "--captured-at-utc",
        required=True,
        help="UTC timestamp for the committed Swagger capture.",
    )
    arguments = parser.parse_args()
    compiler = arguments.compiler.resolve()
    if not compiler.is_file():
        raise FileNotFoundError(f"Compiler '{compiler}' does not exist.")

    names = connector_names()
    validate_snapshot_inventory(names)

    with tempfile.TemporaryDirectory(prefix="connectors-python-generation-") as directory:
        output_directory = Path(directory) / "output"
        output_directory.mkdir()
        run_generator(compiler, names, output_directory)
        for name in names:
            shutil.copyfile(
                output_directory / f"{name}.py",
                CONNECTOR_DIRECTORY / f"{name}.py",
            )
            shutil.copyfile(
                output_directory / "aio" / f"{name}.py",
                ASYNC_CONNECTOR_DIRECTORY / f"{name}.py",
            )

    write_package_artifacts(names)
    manifest = build_manifest(
        compiler,
        arguments.generator_revision,
        names,
        arguments.captured_at_utc,
    )
    MANIFEST_PATH.write_text(
        json.dumps(manifest, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )


if __name__ == "__main__":
    main()
