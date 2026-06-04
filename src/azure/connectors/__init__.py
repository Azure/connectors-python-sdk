# Copyright (c) Microsoft Corporation. All rights reserved.

"""
Azure Connectors SDK for Python.

This package provides infrastructure for calling Azure Connectors
from Python applications, including authentication, HTTP clients, and
strongly-typed generated connector clients.
"""

from .sdk.client_base import ConnectorClientBase
from .sdk.options import ConnectorClientOptions
from .sdk.authentication import (
    TokenProvider,
    ManagedIdentityTokenProvider,
    ConnectionStringTokenProvider,
    AzureIdentityTokenProvider,
)
from .sdk.exceptions import ConnectorException
from .sdk.trigger_payload import TriggerCallbackPayload, TriggerCallbackBody

# Generated connector clients — some may have import errors from incomplete
# code generation (e.g., undefined type references). Wrap each import so
# a single broken connector doesn't prevent the SDK core from loading.
# See: https://github.com/Azure/connectors-python-sdk/issues/13
try:
    from .arm import ArmClient
except (ImportError, NameError):
    ArmClient = None  # type: ignore[assignment,misc]
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
    from .msgraphgroupsanduser import MsgraphgroupsanduserClient
except (ImportError, NameError):
    MsgraphgroupsanduserClient = None  # type: ignore[assignment,misc]
try:
    from .office365users import Office365usersClient
except (ImportError, NameError):
    Office365usersClient = None  # type: ignore[assignment,misc]
try:
    from .azureblob import AzureblobClient
except (ImportError, NameError):
    AzureblobClient = None  # type: ignore[assignment,misc]
try:
    from .mq import MqClient
except (ImportError, NameError):
    MqClient = None  # type: ignore[assignment,misc]
try:
    from .onedrive import OnedriveClient
except (ImportError, NameError):
    OnedriveClient = None  # type: ignore[assignment,misc]
try:
    from .azuread import AzureadClient
except (ImportError, NameError):
    AzureadClient = None  # type: ignore[assignment,misc]
try:
    from .smtp import SmtpClient
except (ImportError, NameError):
    SmtpClient = None  # type: ignore[assignment,misc]
try:
    from .azureeventgrid import AzureeventgridClient
except (ImportError, NameError):
    AzureeventgridClient = None  # type: ignore[assignment,misc]
try:
    from .excelonlinebusiness import ExcelonlinebusinessClient
except (ImportError, NameError):
    ExcelonlinebusinessClient = None  # type: ignore[assignment,misc]
try:
    from .azurequeues import AzurequeuesClient
except (ImportError, NameError):
    AzurequeuesClient = None  # type: ignore[assignment,misc]
try:
    from .azuretables import AzuretablesClient
except (ImportError, NameError):
    AzuretablesClient = None  # type: ignore[assignment,misc]
try:
    from .documentdb import DocumentdbClient
except (ImportError, NameError):
    DocumentdbClient = None  # type: ignore[assignment,misc]
try:
    from .eventhubs import EventhubsClient
except (ImportError, NameError):
    EventhubsClient = None  # type: ignore[assignment,misc]
try:
    from .outlook import OutlookClient
except (ImportError, NameError):
    OutlookClient = None  # type: ignore[assignment,misc]
try:
    from .commondataservice import CommondataserviceClient
except (ImportError, NameError):
    CommondataserviceClient = None  # type: ignore[assignment,misc]

__version__ = '0.2.0b2'

__all__ = [
    'ConnectorClientBase',
    'ConnectorClientOptions',
    'TokenProvider',
    'ManagedIdentityTokenProvider',
    'ConnectionStringTokenProvider',
    'AzureIdentityTokenProvider',
    'ConnectorException',
    'TriggerCallbackPayload',
    'TriggerCallbackBody',
    'KustoClient',
    'Office365Client',
    'SharepointonlineClient',
    'TeamsClient',
    'MsgraphgroupsanduserClient',
    'Office365usersClient',
    'AzureblobClient',
    'MqClient',
    'OnedriveClient',
    'AzureadClient',
    'SmtpClient',
    'AzureeventgridClient',
    'ExcelonlinebusinessClient',
    'AzurequeuesClient',
    'AzuretablesClient',
    'DocumentdbClient',
    'EventhubsClient',
    'OutlookClient',
    'CommondataserviceClient',
]
