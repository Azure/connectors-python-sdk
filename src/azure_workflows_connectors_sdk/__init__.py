# Copyright (c) Microsoft Corporation. All rights reserved.

"""
Azure Logic Apps Connector SDK for Python.

This package provides infrastructure for calling Azure Logic Apps connectors
from Python applications, including authentication, HTTP clients, and strongly-typed
generated connector clients.
"""

from .client_base import ConnectorClientBase
from .options import ConnectorClientOptions
from .authentication import TokenProvider, ManagedIdentityTokenProvider, ConnectionStringTokenProvider
from .exceptions import ConnectorException
from .trigger_payload import TriggerCallbackPayload, TriggerCallbackBody

__version__ = "0.1.0"

__all__ = [
    "ConnectorClientBase",
    "ConnectorClientOptions",
    "TokenProvider",
    "ManagedIdentityTokenProvider",
    "ConnectionStringTokenProvider",
    "ConnectorException",
    "TriggerCallbackPayload",
    "TriggerCallbackBody",
]
