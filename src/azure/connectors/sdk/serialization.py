# Copyright (c) Microsoft Corporation. All rights reserved.

"""Wire serialization for connector request bodies.

Generated connector models expose idiomatic Python ``snake_case`` attribute
names, but the connector service contract is the Swagger JSON property name.
This module converts model instances into their wire representation, reading
the Swagger property name from each dataclass field's
``metadata['wire_name']`` and falling back to the attribute name when no
metadata is present. This keeps the public Python surface idiomatic without
changing the payload sent to the connector service.
"""

from __future__ import annotations

from dataclasses import fields, is_dataclass
from typing import Any

WIRE_NAME_METADATA_KEY = "wire_name"
ADDITIONAL_PROPERTIES_FIELD = "additional_properties"


def to_wire(value: Any) -> Any:
    """Recursively convert a value to its JSON wire representation.

    Dataclasses become dictionaries keyed by their Swagger property names
    (from ``metadata['wire_name']`` when present, otherwise the attribute
    name). ``None`` dataclass fields and ``None`` map values are omitted.
    ``additional_properties`` are merged into the containing object, mirroring
    the .NET ``[JsonExtensionData]`` behavior. Lists and tuples are converted
    element-by-element, and dictionaries are converted value-by-value with
    their keys preserved. Raw ``bytes`` and ``bytearray`` are returned
    unchanged so binary payloads are never JSON-encoded. All other scalar
    values pass through unchanged.

    Args:
        value: The model, collection, or scalar to convert.

    Returns:
        The wire-format representation of ``value``.
    """
    if isinstance(value, (bytes, bytearray)):
        return value

    if is_dataclass(value) and not isinstance(value, type):
        return _dataclass_to_wire(value)

    if isinstance(value, dict):
        return {
            key: to_wire(item)
            for key, item in value.items()
            if item is not None
        }

    if isinstance(value, (list, tuple)):
        return [to_wire(item) for item in value]

    return value


def _dataclass_to_wire(instance: Any) -> dict:
    """Convert a dataclass instance into a wire-format dictionary.

    Args:
        instance: The dataclass instance to convert.

    Returns:
        A dictionary keyed by Swagger property names with ``None`` fields
        omitted and ``additional_properties`` merged into the result.
    """
    result: dict = {}
    for model_field in fields(instance):
        attribute_value = getattr(instance, model_field.name)
        if attribute_value is None:
            continue

        if model_field.name == ADDITIONAL_PROPERTIES_FIELD:
            # NOTE(victoriahall): additional_properties hold dynamic overflow
            # keys that merge into the containing object rather than nesting
            # under an 'additional_properties' key (mirrors .NET
            # [JsonExtensionData]).
            for key, item in attribute_value.items():
                if item is not None:
                    result[key] = to_wire(item)
            continue

        wire_name = model_field.metadata.get(
            WIRE_NAME_METADATA_KEY, model_field.name
        )
        result[wire_name] = to_wire(attribute_value)

    return result
