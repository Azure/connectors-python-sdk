# Sample Connector Usage

This directory contains samples demonstrating how to use the Azure Connectors SDK for Python.

## Prerequisites

1. **Python 3.10+**
2. **Azure Connectors SDK**: `pip install azure-connectors`
3. **Connection runtime URL** from Azure Portal

## Samples

Each sample file (`sample_connector_usage_*.py`) demonstrates a specific connector's operations. Run any sample with:

```bash
python sample_connector_usage_<connector>.py
```

| Sample | Connector | Environment Variable |
|--------|-----------|---------------------|
| `sample_connector_usage_arm.py` | Azure Resource Manager | `ARM_CONNECTION_URL` |
| `sample_connector_usage_azureautomation.py` | Azure Automation | `AZUREAUTOMATION_CONNECTION_URL` |
| `sample_connector_usage_azuread.py` | Azure AD (Entra ID) | `AZUREAD_CONNECTION_URL` |
| `sample_connector_usage_azureblob.py` | Azure Blob Storage | `AZUREBLOB_CONNECTION_URL` |
| `sample_connector_usage_box.py` | Box | `BOX_CONNECTION_URL` |
| `sample_connector_usage_azuredatafactory.py` | Azure Data Factory | `AZUREDATAFACTORY_CONNECTION_URL` |
| `sample_connector_usage_azuredigitaltwins.py` | Azure Digital Twins | `AZUREDIGITALTWINS_CONNECTION_URL` |
| `sample_connector_usage_azuremonitorlogs.py` | Azure Monitor Logs | `AZUREMONITORLOGS_CONNECTION_URL` |
| `sample_connector_usage_azurequeues.py` | Azure Storage Queues | `AZUREQUEUES_CONNECTION_URL` |
| `sample_connector_usage_azuretables.py` | Azure Storage Tables | `AZURETABLES_CONNECTION_URL` |
| `sample_connector_usage_azurevm.py` | Azure VM | `AZUREVM_CONNECTION_URL` |
| `sample_connector_usage_commondataservice.py` | Microsoft Dataverse | `COMMONDATASERVICE_CONNECTION_URL` |
| `sample_connector_usage_documentdb.py` | Azure Cosmos DB | `DOCUMENTDB_CONNECTION_URL` |
| `sample_connector_usage_dropbox.py` | Dropbox | `DROPBOX_CONNECTION_URL` |
| `sample_connector_usage_docusign.py` | DocuSign | `DOCUSIGN_CONNECTION_URL` |
| `sample_connector_usage_kusto.py` | Azure Data Explorer | `KUSTO_CONNECTION_URL` |
| `sample_connector_usage_eventhubs.py` | Azure Event Hubs | `EVENTHUBS_CONNECTION_URL` |
| `sample_connector_usage_excelonline.py` | Excel Online | `EXCELONLINE_CONNECTION_URL` |
| `sample_connector_usage_ftp.py` | FTP | `FTP_CONNECTION_URL` |
| `sample_connector_usage_github.py` | GitHub | `GITHUB_CONNECTION_URL` |
| `sample_connector_usage_googlecalendar.py` | Google Calendar | `GOOGLECALENDAR_CONNECTION_URL` |
| `sample_connector_usage_googletasks.py` | Google Tasks | `GOOGLETASKS_CONNECTION_URL` |
| `sample_connector_usage_googledrive.py` | Google Drive | `GOOGLEDRIVE_CONNECTION_URL` |
| `sample_connector_usage_keyvault.py` | Azure Key Vault | `KEYVAULT_CONNECTION_URL` |
| `sample_connector_usage_jira.py` | Jira | `JIRA_CONNECTION_URL` |
| `sample_connector_usage_freshservice.py` | Freshservice | `FRESHSERVICE_CONNECTION_URL` |
| `sample_connector_usage_infusionsoft.py` | Infusionsoft (Keap) | `INFUSIONSOFT_CONNECTION_URL` |
| `sample_connector_usage_insightly.py` | Insightly | `INSIGHTLY_CONNECTION_URL` |
| `sample_connector_usage_monday.py` | Monday.com | `MONDAY_CONNECTION_URL` |
| `sample_connector_usage_projectplace.py` | Projectplace | `PROJECTPLACE_CONNECTION_URL` |
| `sample_connector_usage_mailchimp.py` | Mailchimp | `MAILCHIMP_CONNECTION_URL` |
| `sample_connector_usage_sendgrid.py` | SendGrid | `SENDGRID_CONNECTION_URL` |
| `sample_connector_usage_webex.py` | Webex | `WEBEX_CONNECTION_URL` |
| `sample_connector_usage_campfire.py` | Campfire | `CAMPFIRE_CONNECTION_URL` |
| `sample_connector_usage_clicksendsms.py` | ClickSend SMS | `CLICKSENDSMS_CONNECTION_URL` |
| `sample_connector_usage_textrequest.py` | TextRequest | `TEXTREQUEST_CONNECTION_URL` |
| `sample_connector_usage_trello.py` | Trello | `TRELLO_CONNECTION_URL` |
| `sample_connector_usage_twitter.py` | Twitter | `TWITTER_CONNECTION_URL` |
| `sample_connector_usage_wordpress.py` | WordPress | `WORDPRESS_CONNECTION_URL` |
| `sample_connector_usage_plivo.py` | Plivo | `PLIVO_CONNECTION_URL` |
| `sample_connector_usage_revai.py` | Rev.ai | `REVAI_CONNECTION_URL` |
| `sample_connector_usage_starmind.py` | Starmind | `STARMIND_CONNECTION_URL` |
| `sample_connector_usage_tallyfy.py` | Tallyfy | `TALLYFY_CONNECTION_URL` |
| `sample_connector_usage_excelonlinebusiness.py` | Excel Online (Business) | `EXCELONLINE_CONNECTION_URL` |
| `sample_connector_usage_mq.py` | IBM MQ | `MQ_CONNECTION_URL` |
| `sample_connector_usage_microsoftbookings.py` | Microsoft Bookings | `MICROSOFTBOOKINGS_CONNECTION_URL` |
| `sample_connector_usage_microsoftforms.py` | Microsoft Forms | `MICROSOFTFORMS_CONNECTION_URL` |
| `sample_connector_usage_msgraph.py` | MS Graph Groups & Users | `MSGRAPH_CONNECTION_URL` |
| `sample_connector_usage_office365.py` | Office 365 Outlook | `OFFICE365_CONNECTION_URL` |
| `sample_connector_usage_office365groups.py` | Office 365 Groups | `OFFICE365GROUPS_CONNECTION_URL` |
| `sample_connector_usage_office365groupsmail.py` | Office 365 Groups Mail | `OFFICE365GROUPSMAIL_CONNECTION_URL` |
| `sample_connector_usage_office365users.py` | Office 365 Users | `OFFICE365USERS_CONNECTION_URL` |
| `sample_connector_usage_onedrive.py` | OneDrive (Personal) | `ONEDRIVE_CONNECTION_URL` |
| `sample_connector_usage_onedriveforbusiness.py` | OneDrive for Business | `ONEDRIVEFORBUSINESS_CONNECTION_URL` |
| `sample_connector_usage_onenote.py` | OneNote | `ONENOTE_CONNECTION_URL` |
| `sample_connector_usage_outlook.py` | Outlook.com | `OUTLOOK_CONNECTION_URL` |
| `sample_connector_usage_planner.py` | Microsoft Planner | `PLANNER_CONNECTION_URL` |
| `sample_connector_usage_powerbi.py` | Power BI | `POWERBI_CONNECTION_URL` |
| `sample_connector_usage_rss.py` | RSS | `RSS_CONNECTION_URL` |
| `sample_connector_usage_salesforce.py` | Salesforce | `SALESFORCE_CONNECTION_URL` |
| `sample_connector_usage_servicebus.py` | Azure Service Bus | `SERVICEBUS_CONNECTION_URL` |
| `sample_connector_usage_sharepoint.py` | SharePoint Online | `SHAREPOINT_CONNECTION_URL` |
| `sample_connector_usage_shifts.py` | Shifts | `SHIFTS_CONNECTION_URL` |
| `sample_connector_usage_slack.py` | Slack | `SLACK_CONNECTION_URL` |
| `sample_connector_usage_smtp.py` | SMTP | `SMTP_CONNECTION_URL` |
| `sample_connector_usage_teams.py` | Microsoft Teams | `TEAMS_CONNECTION_URL` |
| `sample_connector_usage_todo.py` | Microsoft To Do | `TODO_CONNECTION_URL` |
| `sample_connector_usage_universalprint.py` | Universal Print | `UNIVERSALPRINT_CONNECTION_URL` |
| `sample_connector_usage_wdatp.py` | Windows Defender ATP | `WDATP_CONNECTION_URL` |
| `sample_connector_usage_wordonlinebusiness.py` | Word Online (Business) | `WORDONLINEBUSINESS_CONNECTION_URL` |
| `sample_connector_usage_yammer.py` | Yammer (Viva Engage) | `YAMMER_CONNECTION_URL` |
| `sample_connector_usage_azureeventgrid.py` | Azure Event Grid | `AZUREEVENTGRID_CONNECTION_URL` |
| `sample_connector_usage_azureiotcentral.py` | Azure IoT Central | `AZUREIOTCENTRAL_CONNECTION_URL` |
| `sample_connector_usage_cloudconvert.py` | CloudConvert | `CLOUDCONVERT_CONNECTION_URL` |
| `sample_connector_usage_cloudmersiveconvert.py` | Cloudmersive Document Conversion | `CLOUDMERSIVECONVERT_CONNECTION_URL` |
| `sample_connector_usage_dynamicsax.py` | Fin & Ops Apps (Dynamics 365) | `DYNAMICSAX_CONNECTION_URL` |
| `sample_connector_usage_pdfco.py` | PDF.co | `PDFCO_CONNECTION_URL` |
| `sample_connector_usage_plumsail.py` | Plumsail Documents | `PLUMSAIL_CONNECTION_URL` |
| `sample_connector_usage_sql.py` | SQL Server | `SQL_CONNECTION_URL` |
| `sample_connector_usage_zendesk.py` | Zendesk | `ZENDESK_CONNECTION_URL` |
| `sample_connector_usage_pipedrive.py` | Pipedrive | `PIPEDRIVE_CONNECTION_URL` |
| `sample_connector_usage_docuware.py` | DocuWare | `DOCUWARE_CONNECTION_URL` |
| `sample_connector_usage_signinghub.py` | SigningHub | `SIGNINGHUB_CONNECTION_URL` |
| `sample_connector_usage_eventbrite.py` | Eventbrite | `EVENTBRITE_CONNECTION_URL` |
| `sample_connector_usage_formstackforms.py` | Formstack Forms | `FORMSTACKFORMS_CONNECTION_URL` |
| `sample_connector_usage_typeform.py` | Typeform | `TYPEFORM_CONNECTION_URL` |
| `sample_connector_usage_ticketmaster.py` | Ticketmaster | `TICKETMASTER_CONNECTION_URL` |
| `sample_connector_usage_seismicplanner.py` | Seismic Planner | `SEISMICPLANNER_CONNECTION_URL`, `SEISMICPLANNER_SPACE_ID` |
| `sample_connector_usage_waywedo.py` | Way We Do | `WAYWEDO_CONNECTION_URL` |
| `sample_connector_usage_meetingroommap.py` | Meeting Room Map | `MEETINGROOMMAP_CONNECTION_URL` |
| `sample_connector_usage_starrezrestv1.py` | StarRez REST V1 | `STARREZRESTV1_CONNECTION_URL` |
| `sample_connector_usage_replicon.py` | Replicon | `REPLICON_CONNECTION_URL` |
| `sample_connector_usage_elfsquaddata.py` | Elfsquad Data | `ELFSQUADDATA_CONNECTION_URL`, `ELFSQUADDATA_ENTITY_NAME` |
| `sample_connector_usage_etsy.py` | Etsy | `ETSY_CONNECTION_URL` |
| `sample_connector_usage_impexium.py` | Impexium | `IMPEXIUM_CONNECTION_URL` |
| `sample_connector_usage_jedoxodatahub.py` | Jedox OData Hub | `JEDOXODATAHUB_CONNECTION_URL` |
| `sample_connector_usage_orderful.py` | Orderful | `ORDERFUL_CONNECTION_URL` |
| `sample_connector_usage_zohosign.py` | Zoho Sign | `ZOHOSIGN_CONNECTION_URL`, `ZOHOSIGN_REQUEST_ID` |

Set the appropriate environment variable to your connection runtime URL before running:

```bash
# PowerShell
$env:OFFICE365_CONNECTION_URL = "https://[region].azure-apihub.net/apim/office365/[connection-id]"

# Bash
export OFFICE365_CONNECTION_URL="https://[region].azure-apihub.net/apim/office365/[connection-id]"
```

## Usage Pattern

All connector clients follow the same async context manager pattern:

```python
import asyncio
from azure.identity.aio import DefaultAzureCredential
from azure.connectors import ConnectorException
from azure.connectors.<connector> import <Connector>Client

CONNECTION_URL = "https://[region].azure-apihub.net/apim/<connector>/[connection-id]"

async def main():
    credential = DefaultAzureCredential()
    
    async with <Connector>Client(CONNECTION_URL, credential) as client:
        try:
            result = await client.<operation>_async()
            print(result)
        except ConnectorException as ex:
            print(f"Connector error: {ex}")

asyncio.run(main())
```

## Error Handling

The SDK provides structured error handling via `ConnectorException`:

```python
from azure.connectors import ConnectorException

try:
    result = await client.some_operation_async()
except ConnectorException as ex:
    print(f"Status: {ex.status_code}, Message: {ex}")
```

## Next Steps

1. Set up a connection in Azure Portal (see [connection-setup.md](../../docs/connection-setup.md))
2. Set the connection runtime URL environment variable
3. Run the sample for your connector
4. Use typed clients in your application
5. Deploy to Azure Functions or run locally

## Reference

- Python SDK: [PythonSDK/src/azure_workflows_connectors_sdk](../../src/azure_workflows_connectors_sdk)
- Generation Guide: [GENERATION.md](../../GENERATION.md)
- .NET Sample: [DotnetSDK/samples/SampleConnectorUsage](../../../DotnetSDK/samples/SampleConnectorUsage)
