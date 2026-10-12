# Copyright (c) Microsoft Corporation. All rights reserved.

"""Shared runtime contracts for the Azure Connectors SDK for Python."""

from .sdk.client_base import ConnectorClientBase
from .sdk.exceptions import ConnectorException
from .sdk.http_client import ConnectorHttpClient, ConnectorResponse
from .sdk.response import ConnectorResponseHook, ConnectorResponseSnapshot
from .sdk.trigger_payload import TriggerCallbackBody, TriggerCallbackPayload


__version__ = "0.5.0b1"

__all__ = [
    "ConnectorClientBase",
    "ConnectorException",
    "ConnectorHttpClient",
    "ConnectorResponse",
    "ConnectorResponseHook",
    "ConnectorResponseSnapshot",
    "TriggerCallbackBody",
    "TriggerCallbackPayload",
]
