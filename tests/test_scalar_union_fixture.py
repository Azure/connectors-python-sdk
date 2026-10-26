# Copyright (c) Microsoft Corporation. All rights reserved.

"""Exercise the pinned generated scalar-only map fixture on the SDK runtime."""

from __future__ import annotations

import ast
import importlib.util
import json
import os
import shutil
import subprocess
import sys
from dataclasses import fields
from pathlib import Path
from typing import get_type_hints

import pytest

from azure.connectors.sdk.serialization import to_wire


FIXTURE_PATH = Path(__file__).parent / "fixtures" / "scalarunionfixture.py"


def _load_fixture():
    """Load the complete generated module without importing it as a client."""
    spec = importlib.util.spec_from_file_location("scalarunionfixture", FIXTURE_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


fixture = _load_fixture()


def test_generated_output_compiles_and_preserves_typed_annotations():
    """The generated model keeps all explicit kinds and typed controls."""
    compile(FIXTURE_PATH.read_text(encoding="utf-8"), str(FIXTURE_PATH), "exec")
    hints = get_type_hints(fixture.ScalarMaps, vars(fixture))
    assert str(hints["properties"]) == "typing.Dict[str, str | int | float | bool]"
    assert "str" in str(hints["other_values"])
    assert "int" in str(hints["other_values"])
    assert "None" in str(hints["nullable_values"])
    assert "Any" in str(hints["dynamic_values"])
    assert "Inner" in str(hints["structured"])
    assert "ScalarItem" in str(next(
        item.type for item in fields(fixture.ScalarMaps)
        if item.name == "scalar_ref_values"
    ))
    for name in ("scalar_ref_values", "scalar_ref_value"):
        assert "int" in str(hints[name])
        assert "bool" in str(hints[name])
        assert "Mapping" not in str(hints[name])
    model_fields = {item.name: item for item in fields(fixture.ScalarMaps)}
    assert model_fields["properties"].metadata["wire_name"] == "Properties"
    assert model_fields["properties"].metadata["scalar_map_types"] == (
        str, int, float, bool
    )
    assert model_fields["nullable_values"].metadata["scalar_map_nullable"]


def test_generated_model_serializes_mixed_scalars_and_nullable_maps():
    """Use generated fields and real SDK serializer without coercion."""
    model = fixture.ScalarMaps(
        properties={"eventType": "sample", "attempt": 1,
                    "ratio": 1.5, "enabled": True},
        other_values={"attempt": 3, "name": "sample"},
        nullable_values={"absent": None, "present": "value"},
        structured={"child": fixture.Inner(value="nested")},
        scalar_ref_values={"count": 3, "flag": True},
        scalar_ref_value=3,
        dynamic_values={"nested": {"list": [1, True]}},
    )
    wire = to_wire(model)
    assert wire == {
        "Properties": {"eventType": "sample", "attempt": 1,
                       "ratio": 1.5, "enabled": True},
        "otherValues": {"attempt": 3, "name": "sample"},
        "nullableValues": {"absent": None, "present": "value"},
        "structured": {"child": {"value": "nested"}},
        "scalarRefValues": {"count": 3, "flag": True},
        "scalarRefValue": 3,
        "dynamicValues": {"nested": {"list": [1, True]}},
    }
    assert json.loads(json.dumps(wire)) == wire


@pytest.mark.parametrize("bad_value", [{"value": 1}, [1], None])
def test_generated_model_rejects_invalid_non_nullable_map_values(bad_value):
    """Reject nested objects, arrays, and undeclared nulls at construction."""
    with pytest.raises(TypeError, match="properties"):
        fixture.ScalarMaps(properties={"invalid": bad_value})


def test_generated_model_rejects_bool_for_integer_only_map():
    """Python bool subclasses int, but Swagger integer excludes booleans."""
    with pytest.raises(TypeError, match="other_values"):
        fixture.ScalarMaps(properties={}, other_values={"invalid": True})


def test_generated_model_allows_open_maps_and_valid_nullable_values():
    """No scalar restriction is inferred for an empty additionalProperties."""
    model = fixture.ScalarMaps(
        properties={},
        nullable_values={"missing": None},
        dynamic_values={"nested": [1, {"test": True}]},
    )
    assert to_wire(model)["nullableValues"] == {"missing": None}
    assert to_wire(model)["dynamicValues"] == {
        "nested": [1, {"test": True}]
    }


def test_generated_model_rejects_mutation_on_serialization():
    """The SDK checks a scalar map again before it goes on the wire."""
    model = fixture.ScalarMaps(properties={"initial": 1},
                               scalar_ref_values={"valid": 1})
    model.scalar_ref_values["invalid"] = [1]
    with pytest.raises(TypeError, match="scalarRefValues"):
        to_wire(model)
    model.scalar_ref_values.pop("invalid")
    model.properties["invalid"] = [1]
    with pytest.raises(TypeError, match="Properties"):
        to_wire(model)


@pytest.mark.skipif(shutil.which("mypy") is None, reason="mypy is not installed")
def test_generated_model_static_positive_and_negative_controls(tmp_path):
    """Mypy accepts scalar consumers and rejects object, array, and null."""
    valid = tmp_path / "valid_scalar_consumer.py"
    valid.write_text(
        "from scalarunionfixture import ScalarMaps, Inner\n"
        "ScalarMaps(properties={'name': 'x', 'int': 1, 'float': 1.5, "
        "'bool': True}, other_values={'count': 1, 'name': 'x'}, "
        "nullable_values={'empty': None}, "
        "structured={'child': Inner(value='ok')}, "
        "scalar_ref_values={'count': 3, 'flag': True}, "
        "scalar_ref_value=3)\n",
        encoding="utf-8",
    )
    invalid = tmp_path / "invalid_scalar_consumer.py"
    invalid.write_text(
        "from scalarunionfixture import ScalarMaps\n"
        "ScalarMaps(properties={'nested': {'value': 1}})\n"
        "ScalarMaps(properties={'array': [1]})\n"
        "ScalarMaps(properties={'null': None})\n"
        "ScalarMaps(properties={}, scalar_ref_values={'nested': {'x': 1}})\n"
        "ScalarMaps(properties={}, scalar_ref_value={'nested': 1})\n",
        encoding="utf-8",
    )
    # Type-check the exact emitted models without the client method, which
    # belongs to the separate Azure Core runtime migration (#103).
    parsed = ast.parse(FIXTURE_PATH.read_text(encoding="utf-8"))
    models = [
        node for node in parsed.body
        if (isinstance(node, ast.ClassDef)
            and node.name in ("ScalarMaps", "Inner"))
        or (isinstance(node, ast.Assign)
            and any(isinstance(target, ast.Name) and target.id == "ScalarItem"
                    for target in node.targets))
    ]
    model_module = tmp_path / "scalarunionfixture.py"
    model_source = "\n\n".join(ast.unparse(model) for model in models)
    model_module.write_text(
        "from __future__ import annotations\n"
        "from dataclasses import dataclass, field as dataclass_field\n"
        "from typing import Any, Dict, Mapping, Optional\n\n"
        f"{model_source}\n",
        encoding="utf-8",
    )
    environment = dict(os.environ)
    environment["MYPYPATH"] = str(tmp_path)
    result = subprocess.run(
        [sys.executable, "-m", "mypy", "--no-incremental",
         "--follow-imports=normal", "--disable-error-code=import-untyped",
         str(valid), str(invalid)],
        capture_output=True,
        text=True,
        check=False,
        env=environment,
        timeout=120,
    )
    assert result.returncode == 1, result.stdout + result.stderr
    assert f"{valid}:" not in result.stdout, result.stdout
    assert result.stdout.count(f"{invalid.name}:2:") == 1, result.stdout
    assert result.stdout.count(f"{invalid.name}:3:") == 1, result.stdout
    assert result.stdout.count(f"{invalid.name}:4:") == 1, result.stdout
    assert result.stdout.count(f"{invalid.name}:5:") == 1, result.stdout
    assert result.stdout.count(f"{invalid.name}:6:") == 1, result.stdout
