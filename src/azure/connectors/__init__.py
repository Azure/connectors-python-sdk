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
from .kusto import KustoClient
from .office365 import Office365Client
from .sharepointonline import SharepointonlineClient
from .teams import TeamsClient
from .msgraph import MsgraphgroupsanduserClient

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
