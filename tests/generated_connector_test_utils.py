# Copyright (c) Microsoft Corporation. All rights reserved.

"""Shared helpers for generated connector contract tests."""

from __future__ import annotations

import dataclasses
import inspect
from types import ModuleType
from typing import Any, get_origin, get_type_hints


def get_generated_operations(client_type: type[Any]) -> set[str]:
    """Return generated async operation names without their async suffix."""
    return {
        name.removesuffix("_async")
        for name in dir(client_type)
        if name.endswith("_async")
        and inspect.iscoroutinefunction(getattr(client_type, name))
    }


async def invoke_generated_operation(
    client: Any,
    operation: str,
    module: ModuleType,
) -> Any:
    """Invoke a generated operation with representative required arguments."""
    method = getattr(client, f"{operation}_async")
    type_hints = get_type_hints(method, globalns=vars(module))
    arguments = {
        parameter.name: _representative_value(type_hints[parameter.name])
        for parameter in inspect.signature(method).parameters.values()
        if parameter.default is inspect.Parameter.empty
    }
    return await method(**arguments)


def _representative_value(annotation: Any) -> Any:
    """Create a representative value for a required generated parameter."""
    if annotation is str:
        return "value"

    if annotation is bytes:
        return b"payload"

    if get_origin(annotation) is list:
        return []

    if inspect.isclass(annotation) and dataclasses.is_dataclass(annotation):
        return annotation()

    raise AssertionError(f"Unsupported generated parameter type '{annotation}'.")
