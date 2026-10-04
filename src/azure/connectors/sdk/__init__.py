# Copyright (c) Microsoft Corporation. All rights reserved.

"""
Azure Connectors SDK for Python.

This package provides infrastructure for calling Azure Connectors
from Python applications, including authentication, HTTP clients,
and strongly-typed generated connector clients.
"""

from .client_base import ConnectorClientBase
from .exceptions import ConnectorException
from .http_client import ConnectorHttpClient, ConnectorResponse
from .response import ConnectorResponseHook, ConnectorResponseSnapshot
from .trigger_payload import TriggerCallbackPayload, TriggerCallbackBody

__version__ = "0.1.0"

__all__ = [
    "ConnectorClientBase",
    "ConnectorException",
    "ConnectorHttpClient",
    "ConnectorResponse",
    "ConnectorResponseHook",
    "ConnectorResponseSnapshot",
    "TriggerCallbackPayload",
    "TriggerCallbackBody",
]
