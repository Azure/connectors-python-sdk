# Copyright (c) Microsoft Corporation. All rights reserved.

"""Asynchronous generated connector clients."""

from importlib import import_module
from typing import Any

from .._client_registry import CLIENT_REGISTRY


def __getattr__(name: str) -> Any:
    """Load a generated asynchronous client when requested from the package root."""
    module_name = CLIENT_REGISTRY.get(name)
    if module_name is None:
        raise AttributeError(f"Module '{__name__}' has no attribute '{name}'.")

    client_type = getattr(import_module(f".{module_name}", __name__), name)
    globals()[name] = client_type
    return client_type


def __dir__() -> list[str]:
    """List lazily available asynchronous connector clients."""
    return sorted(set(globals()) | CLIENT_REGISTRY.keys())


__all__ = [*CLIENT_REGISTRY]
