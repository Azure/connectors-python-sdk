# Copyright (c) Microsoft Corporation. All rights reserved.

"""
Azure Logic Apps Connector SDK for Python.

This package provides infrastructure for calling Azure Logic Apps connectors
from Python applications, including authentication, HTTP clients, and strongly-typed
generated connector clients.
"""

from .sdk.client_base import ConnectorClientBase
from .sdk.options import ConnectorClientOptions
from .sdk.authentication import TokenProvider, ManagedIdentityTokenProvider, ConnectionStringTokenProvider, AzureIdentityTokenProvider
from .sdk.exceptions import ConnectorException
from .sdk.trigger_payload import TriggerCallbackPayload, TriggerCallbackBody

# Generated connector clients — some may have import errors from incomplete
# code generation (e.g., undefined type references). Wrap each import so
# a single broken connector doesn't prevent the SDK core from loading.
# See: https://github.com/Azure/connectors-python-sdk/issues/13
try:
    from .kusto import KustoClient
except (ImportError, NameError):
    KustoClient = None  # type: ignore[assignment,misc]
try:
    from .office365 import Office365Client
except (ImportError, NameError):
    Office365Client = None  # type: ignore[assignment,misc]
try:
    from .sharepointonline import SharepointonlineClient
except (ImportError, NameError):
    SharepointonlineClient = None  # type: ignore[assignment,misc]
try:
    from .teams import TeamsClient
except (ImportError, NameError):
    TeamsClient = None  # type: ignore[assignment,misc]
try:
    from .msgraph import MsgraphgroupsanduserClient
except (ImportError, NameError):
    MsgraphgroupsanduserClient = None  # type: ignore[assignment,misc]

__version__ = "0.1.0"

__all__ = [
    "ConnectorClientBase",
    "ConnectorClientOptions",
    "TokenProvider",
    "ManagedIdentityTokenProvider",
    "ConnectionStringTokenProvider",
    "AzureIdentityTokenProvider",
    "ConnectorException",
    "TriggerCallbackPayload",
    "TriggerCallbackBody",
    "KustoClient",
    "Office365Client",
    "SharepointonlineClient",
    "TeamsClient",
    "MsgraphgroupsanduserClient",
]
