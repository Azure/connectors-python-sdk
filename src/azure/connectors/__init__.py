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
    from .azureautomation import AzureautomationClient
except (ImportError, NameError):
    AzureautomationClient = None  # type: ignore[assignment,misc]
try:
    from .azuredatafactory import AzuredatafactoryClient
except (ImportError, NameError):
    AzuredatafactoryClient = None  # type: ignore[assignment,misc]
try:
    from .azuredigitaltwins import AzuredigitaltwinsClient
except (ImportError, NameError):
    AzuredigitaltwinsClient = None  # type: ignore[assignment,misc]
try:
    from .azuremonitorlogs import AzuremonitorlogsClient
except (ImportError, NameError):
    AzuremonitorlogsClient = None  # type: ignore[assignment,misc]
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
    from .office365groups import Office365groupsClient
except (ImportError, NameError):
    Office365groupsClient = None  # type: ignore[assignment,misc]
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
    from .onenote import OnenoteClient
except (ImportError, NameError):
    OnenoteClient = None  # type: ignore[assignment,misc]
try:
    from .planner import PlannerClient
except (ImportError, NameError):
    PlannerClient = None  # type: ignore[assignment,misc]
try:
    from .salesforce import SalesforceClient
except (ImportError, NameError):
    SalesforceClient = None  # type: ignore[assignment,misc]
try:
    from .azuread import AzureadClient
except (ImportError, NameError):
    AzureadClient = None  # type: ignore[assignment,misc]
try:
    from .smtp import SmtpClient
except (ImportError, NameError):
    SmtpClient = None  # type: ignore[assignment,misc]
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
    from .azurevm import AzurevmClient
except (ImportError, NameError):
    AzurevmClient = None  # type: ignore[assignment,misc]
try:
    from .documentdb import DocumentdbClient
except (ImportError, NameError):
    DocumentdbClient = None  # type: ignore[assignment,misc]
try:
    from .eventhubs import EventhubsClient
except (ImportError, NameError):
    EventhubsClient = None  # type: ignore[assignment,misc]
try:
    from .keyvault import KeyvaultClient
except (ImportError, NameError):
    KeyvaultClient = None  # type: ignore[assignment,misc]
try:
    from .microsoftbookings import MicrosoftbookingsClient
except (ImportError, NameError):
    MicrosoftbookingsClient = None  # type: ignore[assignment,misc]
try:
    from .outlook import OutlookClient
except (ImportError, NameError):
    OutlookClient = None  # type: ignore[assignment,misc]
try:
    from .commondataservice import CommondataserviceClient
except (ImportError, NameError):
    CommondataserviceClient = None  # type: ignore[assignment,misc]
try:
    from .servicebus import ServicebusClient
except (ImportError, NameError):
    ServicebusClient = None  # type: ignore[assignment,misc]
try:
    from .wdatp import WdatpClient
except (ImportError, NameError):
    WdatpClient = None  # type: ignore[assignment,misc]
try:
    from .wordonlinebusiness import WordonlinebusinessClient
except (ImportError, NameError):
    WordonlinebusinessClient = None  # type: ignore[assignment,misc]
try:
    from .yammer import YammerClient
except (ImportError, NameError):
    YammerClient = None  # type: ignore[assignment,misc]

__version__ = '0.3.0b2'

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
    'ArmClient',
    'AzureautomationClient',
    'AzuredatafactoryClient',
    'AzuredigitaltwinsClient',
    'AzuremonitorlogsClient',
    'KustoClient',
    'Office365Client',
    'SharepointonlineClient',
    'TeamsClient',
    'MsgraphgroupsanduserClient',
    'Office365usersClient',
    'Office365groupsClient',
    'AzureblobClient',
    'MqClient',
    'OnedriveClient',
    'OnenoteClient',
    'PlannerClient',
    'SalesforceClient',
    'AzureadClient',
    'SmtpClient',
    'ExcelonlinebusinessClient',
    'AzurequeuesClient',
    'AzuretablesClient',
    'AzurevmClient',
    'DocumentdbClient',
    'EventhubsClient',
    'KeyvaultClient',
    'MicrosoftbookingsClient',
    'OutlookClient',
    'CommondataserviceClient',
    'ServicebusClient',
    'WdatpClient',
    'WordonlinebusinessClient',
    'YammerClient',
]
