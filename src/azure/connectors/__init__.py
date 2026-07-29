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
    from .office365groupsmail import Office365groupsmailClient
except (ImportError, NameError):
    Office365groupsmailClient = None  # type: ignore[assignment,misc]
try:
    from .azureblob import AzureblobClient
except (ImportError, NameError):
    AzureblobClient = None  # type: ignore[assignment,misc]
try:
    from .box import BoxClient
except (ImportError, NameError):
    BoxClient = None  # type: ignore[assignment,misc]
try:
    from .dropbox import DropboxClient
except (ImportError, NameError):
    DropboxClient = None  # type: ignore[assignment,misc]
try:
    from .mq import MqClient
except (ImportError, NameError):
    MqClient = None  # type: ignore[assignment,misc]
try:
    from .onedrive import OnedriveClient
except (ImportError, NameError):
    OnedriveClient = None  # type: ignore[assignment,misc]
try:
    from .onedriveforbusiness import OnedriveforbusinessClient
except (ImportError, NameError):
    OnedriveforbusinessClient = None  # type: ignore[assignment,misc]
try:
    from .onenote import OnenoteClient
except (ImportError, NameError):
    OnenoteClient = None  # type: ignore[assignment,misc]
try:
    from .planner import PlannerClient
except (ImportError, NameError):
    PlannerClient = None  # type: ignore[assignment,misc]
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
    from .excelonline import ExcelonlineClient
except (ImportError, NameError):
    ExcelonlineClient = None  # type: ignore[assignment,misc]
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
    from .ftp import FtpClient
except (ImportError, NameError):
    FtpClient = None  # type: ignore[assignment,misc]
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

try:
    from .azuremonitorlogs import AzuremonitorlogsClient
except (ImportError, NameError):
    AzuremonitorlogsClient = None  # type: ignore[assignment,misc]

try:
    from .docusign import DocusignClient
except (ImportError, NameError):
    DocusignClient = None  # type: ignore[assignment,misc]

try:
    from .github import GithubClient
except (ImportError, NameError):
    GithubClient = None  # type: ignore[assignment,misc]

try:
    from .googlecalendar import GooglecalendarClient
except (ImportError, NameError):
    GooglecalendarClient = None  # type: ignore[assignment,misc]

try:
    from .googletasks import GoogletasksClient
except (ImportError, NameError):
    GoogletasksClient = None  # type: ignore[assignment,misc]

try:
    from .googledrive import GoogledriveClient
except (ImportError, NameError):
    GoogledriveClient = None  # type: ignore[assignment,misc]

try:
    from .jira import JiraClient
except (ImportError, NameError):
    JiraClient = None  # type: ignore[assignment,misc]

try:
    from .microsoftforms import MicrosoftformsClient
except (ImportError, NameError):
    MicrosoftformsClient = None  # type: ignore[assignment,misc]

try:
    from .powerbi import PowerbiClient
except (ImportError, NameError):
    PowerbiClient = None  # type: ignore[assignment,misc]

try:
    from .rss import RssClient
except (ImportError, NameError):
    RssClient = None  # type: ignore[assignment,misc]

try:
    from .salesforce import SalesforceClient
except (ImportError, NameError):
    SalesforceClient = None  # type: ignore[assignment,misc]

try:
    from .shifts import ShiftsClient
except (ImportError, NameError):
    ShiftsClient = None  # type: ignore[assignment,misc]

try:
    from .slack import SlackClient
except (ImportError, NameError):
    SlackClient = None  # type: ignore[assignment,misc]

try:
    from .todo import TodoClient
except (ImportError, NameError):
    TodoClient = None  # type: ignore[assignment,misc]

try:
    from .insightly import InsightlyClient
except (ImportError, NameError):
    InsightlyClient = None  # type: ignore[assignment,misc]

try:
    from .infusionsoft import InfusionsoftClient
except (ImportError, NameError):
    InfusionsoftClient = None  # type: ignore[assignment,misc]

try:
    from .freshservice import FreshserviceClient
except (ImportError, NameError):
    FreshserviceClient = None  # type: ignore[assignment,misc]

try:
    from .monday import MondayClient
except (ImportError, NameError):
    MondayClient = None  # type: ignore[assignment,misc]

try:
    from .projectplace import ProjectplaceClient
except (ImportError, NameError):
    ProjectplaceClient = None  # type: ignore[assignment,misc]

try:
    from .mailchimp import MailchimpClient
except (ImportError, NameError):
    MailchimpClient = None  # type: ignore[assignment,misc]

try:
    from .sendgrid import SendgridClient
except (ImportError, NameError):
    SendgridClient = None  # type: ignore[assignment,misc]

try:
    from .webex import WebexClient
except (ImportError, NameError):
    WebexClient = None  # type: ignore[assignment,misc]
try:
    from .campfire import CampfireClient
except (ImportError, NameError):
    CampfireClient = None  # type: ignore[assignment,misc]
try:
    from .clicksendsms import ClicksendsmsClient
except (ImportError, NameError):
    ClicksendsmsClient = None  # type: ignore[assignment,misc]
try:
    from .plivo import PlivoClient
except (ImportError, NameError):
    PlivoClient = None  # type: ignore[assignment,misc]
try:
    from .textrequest import TextrequestClient
except (ImportError, NameError):
    TextrequestClient = None  # type: ignore[assignment,misc]

try:
    from .universalprint import UniversalprintClient
except (ImportError, NameError):
    UniversalprintClient = None  # type: ignore[assignment,misc]

try:
    from .azureeventgrid import AzureeventgridClient
except (ImportError, NameError):
    AzureeventgridClient = None  # type: ignore[assignment,misc]

try:
    from .azureiotcentral import AzureiotcentralClient
except (ImportError, NameError):
    AzureiotcentralClient = None  # type: ignore[assignment,misc]

try:
    from .cloudmersiveconvert import CloudmersiveconvertClient
except (ImportError, NameError):
    CloudmersiveconvertClient = None  # type: ignore[assignment,misc]

try:
    from .dynamicsax import DynamicsaxClient
except (ImportError, NameError):
    DynamicsaxClient = None  # type: ignore[assignment,misc]

try:
    from .pdfco import PdfcoClient
except (ImportError, NameError):
    PdfcoClient = None  # type: ignore[assignment,misc]

try:
    from .plumsail import PlumsailClient
except (ImportError, NameError):
    PlumsailClient = None  # type: ignore[assignment,misc]

try:
    from .sql import SqlClient
except (ImportError, NameError):
    SqlClient = None  # type: ignore[assignment,misc]

try:
    from .zendesk import ZendeskClient
except (ImportError, NameError):
    ZendeskClient = None  # type: ignore[assignment,misc]

try:
    from .pipedrive import PipedriveClient
except (ImportError, NameError):
    PipedriveClient = None  # type: ignore[assignment,misc]

try:
    from .docuware import DocuwareClient
except (ImportError, NameError):
    DocuwareClient = None  # type: ignore[assignment,misc]

try:
    from .signinghub import SigninghubClient
except (ImportError, NameError):
    SigninghubClient = None  # type: ignore[assignment,misc]

__version__ = '0.4.0b1'

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
    'KustoClient',
    'Office365Client',
    'SharepointonlineClient',
    'TeamsClient',
    'MsgraphgroupsanduserClient',
    'Office365usersClient',
    'Office365groupsClient',
    'Office365groupsmailClient',
    'AzureblobClient',
    'BoxClient',
    'DropboxClient',
    'MqClient',
    'OnedriveClient',
    'OnedriveforbusinessClient',
    'OnenoteClient',
    'PlannerClient',
    'AzureadClient',
    'SmtpClient',
    'ExcelonlineClient',
    'ExcelonlinebusinessClient',
    'AzurequeuesClient',
    'AzuretablesClient',
    'AzurevmClient',
    'DocumentdbClient',
    'EventhubsClient',
    'FtpClient',
    'KeyvaultClient',
    'MicrosoftbookingsClient',
    'OutlookClient',
    'CommondataserviceClient',
    'ServicebusClient',
    'WdatpClient',
    'WordonlinebusinessClient',
    'YammerClient',
    "AzuremonitorlogsClient",
    "DocusignClient",
    "GithubClient",
    "GooglecalendarClient",
    "GoogletasksClient",
    "GoogledriveClient",
    "JiraClient",
    "MicrosoftformsClient",
    "PowerbiClient",
    "RssClient",
    "SalesforceClient",
    "ShiftsClient",
    "SlackClient",
    "TodoClient",
    "InsightlyClient",
    "InfusionsoftClient",
    "FreshserviceClient",
    "MondayClient",
    "ProjectplaceClient",
    "MailchimpClient",
    "SendgridClient",
    "WebexClient",
    "CampfireClient",
    "ClicksendsmsClient",
    "PlivoClient",
    "TextrequestClient",
    "UniversalprintClient",
    "AzureeventgridClient",
    "AzureiotcentralClient",
    "CloudmersiveconvertClient",
    "DynamicsaxClient",
    "PdfcoClient",
    "PlumsailClient",
    "SqlClient",
    "ZendeskClient",
    "PipedriveClient",
    "DocuwareClient",
    "SigninghubClient",
]
