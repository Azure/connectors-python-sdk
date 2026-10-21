# Copyright (c) Microsoft Corporation. All rights reserved.

"""Shared runtime contracts for the Azure Connectors SDK for Python."""

from importlib import import_module
from typing import Any

from ._client_registry import CLIENT_REGISTRY
from .sdk.client_base import ConnectorClientBase
from .sdk.exceptions import ConnectorException
from .sdk.http_client import ConnectorHttpClient, ConnectorResponse
from .sdk.response import ConnectorResponseHook, ConnectorResponseSnapshot
from .sdk.trigger_payload import TriggerCallbackBody, TriggerCallbackPayload


__version__ = "0.5.0b1"


def __getattr__(name: str) -> Any:
    """Load a generated connector client when requested from the package root."""
    module_name = CLIENT_REGISTRY.get(name)
    if module_name is None:
        raise AttributeError(f"Module '{__name__}' has no attribute '{name}'.")

    client_type = getattr(import_module(f".{module_name}", __name__), name)
    globals()[name] = client_type
    return client_type


def __dir__() -> list[str]:
    """List core exports and lazily available connector clients."""
    return sorted(set(globals()) | CLIENT_REGISTRY.keys())


__all__ = [
    "ConnectorClientBase",
    "ConnectorException",
    "ConnectorHttpClient",
    "ConnectorResponse",
    "ConnectorResponseHook",
    "ConnectorResponseSnapshot",
    "TriggerCallbackBody",
    "TriggerCallbackPayload",
    *CLIENT_REGISTRY,
]
