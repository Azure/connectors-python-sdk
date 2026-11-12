# Sample Connector Usage

This directory contains samples demonstrating how to use the Azure Connectors SDK for Python.

## Prerequisites

1. **Python 3.10+**
2. **Azure Connectors SDK**: `pip install azure-connectors`
3. **Connection runtime URL** from Azure Portal

## Samples

Each of the 103 connectors has one async sample in this directory. Clients and
models use root connector imports and unsuffixed operation names. Run a sample with:

```bash
python sample_connector_usage_<connector>.py
```

| Sample | Connector | Environment Variable |
|--------|-----------|---------------------|
| `sample_connector_usage_arm.py` | Azure Resource Manager | `ARM_CONNECTION_URL` |
| `sample_connector_usage_azure_automation.py` | Azure Automation | `AZUREAUTOMATION_CONNECTION_URL` |
| `sample_connector_usage_azure_ad.py` | Azure AD (Entra ID) | `AZUREAD_CONNECTION_URL` |
| `sample_connector_usage_azure_blob.py` | Azure Blob Storage | `AZUREBLOB_CONNECTION_URL` |
| `sample_connector_usage_box.py` | Box | `BOX_CONNECTION_URL` |
| `sample_connector_usage_azure_data_factory.py` | Azure Data Factory | `AZUREDATAFACTORY_CONNECTION_URL` |
| `sample_connector_usage_azure_digital_twins.py` | Azure Digital Twins | `AZUREDIGITALTWINS_CONNECTION_URL` |
| `sample_connector_usage_azure_monitor_logs.py` | Azure Monitor Logs | `AZUREMONITORLOGS_CONNECTION_URL` |
| `sample_connector_usage_azure_queues.py` | Azure Storage Queues | `AZUREQUEUES_CONNECTION_URL` |
| `sample_connector_usage_azure_tables.py` | Azure Storage Tables | `AZURETABLES_CONNECTION_URL` |
| `sample_connector_usage_azure_vm.py` | Azure VM | `AZUREVM_CONNECTION_URL` |
| `sample_connector_usage_common_data_service.py` | Microsoft Dataverse | `COMMONDATASERVICE_CONNECTION_URL` |
| `sample_connector_usage_dataflows.py` | Power Query Dataflows | `DATAFLOWS_CONNECTION_URL`, `DATAFLOWS_WORKSPACE_TYPE` (optional) |
| `sample_connector_usage_data_flows_sms.py` | Dataflows SMS | `DATAFLOWSSMS_CONNECTION_URL` |
| `sample_connector_usage_document_db.py` | Azure Cosmos DB | `DOCUMENTDB_CONNECTION_URL` |
| `sample_connector_usage_dropbox.py` | Dropbox | `DROPBOX_CONNECTION_URL` |
| `sample_connector_usage_docusign.py` | DocuSign | `DOCUSIGN_CONNECTION_URL` |
| `sample_connector_usage_kusto.py` | Azure Data Explorer | `KUSTO_CONNECTION_URL` |
| `sample_connector_usage_event_hubs.py` | Azure Event Hubs | `EVENTHUBS_CONNECTION_URL` |
| `sample_connector_usage_excel_online.py` | Excel Online | `EXCELONLINE_CONNECTION_URL` |
| `sample_connector_usage_ftp.py` | FTP | `FTP_CONNECTION_URL` |
| `sample_connector_usage_git_hub.py` | GitHub | `GITHUB_CONNECTION_URL` |
| `sample_connector_usage_google_calendar.py` | Google Calendar | `GOOGLECALENDAR_CONNECTION_URL` |
| `sample_connector_usage_google_tasks.py` | Google Tasks | `GOOGLETASKS_CONNECTION_URL` |
| `sample_connector_usage_google_drive.py` | Google Drive | `GOOGLEDRIVE_CONNECTION_URL` |
| `sample_connector_usage_key_vault.py` | Azure Key Vault | `KEYVAULT_CONNECTION_URL` |
| `sample_connector_usage_jira.py` | Jira | `JIRA_CONNECTION_URL` |
| `sample_connector_usage_freshservice.py` | Freshservice | `FRESHSERVICE_CONNECTION_URL` |
| `sample_connector_usage_infusionsoft.py` | Infusionsoft (Keap) | `INFUSIONSOFT_CONNECTION_URL` |
| `sample_connector_usage_insightly.py` | Insightly | `INSIGHTLY_CONNECTION_URL` |
| `sample_connector_usage_monday.py` | Monday.com | `MONDAY_CONNECTION_URL` |
| `sample_connector_usage_projectplace.py` | Projectplace | `PROJECTPLACE_CONNECTION_URL` |
| `sample_connector_usage_mailchimp.py` | Mailchimp | `MAILCHIMP_CONNECTION_URL` |
| `sample_connector_usage_send_grid.py` | SendGrid | `SENDGRID_CONNECTION_URL` |
| `sample_connector_usage_webex.py` | Webex | `WEBEX_CONNECTION_URL` |
| `sample_connector_usage_campfire.py` | Campfire | `CAMPFIRE_CONNECTION_URL` |
| `sample_connector_usage_click_send_sms.py` | ClickSend SMS | `CLICKSENDSMS_CONNECTION_URL` |
| `sample_connector_usage_text_request.py` | TextRequest | `TEXTREQUEST_CONNECTION_URL` |
| `sample_connector_usage_trello.py` | Trello | `TRELLO_CONNECTION_URL` |
| `sample_connector_usage_twitter.py` | Twitter | `TWITTER_CONNECTION_URL` |
| `sample_connector_usage_word_press.py` | WordPress | `WORDPRESS_CONNECTION_URL` |
| `sample_connector_usage_plivo.py` | Plivo | `PLIVO_CONNECTION_URL` |
| `sample_connector_usage_rev_ai.py` | Rev.ai | `REVAI_CONNECTION_URL` |
| `sample_connector_usage_starmind.py` | Starmind | `STARMIND_CONNECTION_URL` |
| `sample_connector_usage_tallyfy.py` | Tallyfy | `TALLYFY_CONNECTION_URL` |
| `sample_connector_usage_excel_online_business.py` | Excel Online (Business) | `EXCELONLINE_CONNECTION_URL` |
| `sample_connector_usage_mq.py` | IBM MQ | `MQ_CONNECTION_URL` |
| `sample_connector_usage_microsoft_bookings.py` | Microsoft Bookings | `MICROSOFTBOOKINGS_CONNECTION_URL` |
| `sample_connector_usage_microsoft_forms.py` | Microsoft Forms | `MICROSOFTFORMS_CONNECTION_URL` |
| `sample_connector_usage_ms_graph_groups_and_users.py` | MS Graph Groups & Users | `MSGRAPH_CONNECTION_URL` |
| `sample_connector_usage_office365.py` | Office 365 Outlook | `OFFICE365_CONNECTION_URL` |
| `sample_connector_usage_office365_groups.py` | Office 365 Groups | `OFFICE365GROUPS_CONNECTION_URL` |
| `sample_connector_usage_office365_groups_mail.py` | Office 365 Groups Mail | `OFFICE365GROUPSMAIL_CONNECTION_URL` |
| `sample_connector_usage_office365_users.py` | Office 365 Users | `OFFICE365USERS_CONNECTION_URL` |
| `sample_connector_usage_one_drive.py` | OneDrive (Personal) | `ONEDRIVE_CONNECTION_URL` |
| `sample_connector_usage_one_drive_for_business.py` | OneDrive for Business | `ONEDRIVEFORBUSINESS_CONNECTION_URL` |
| `sample_connector_usage_onenote.py` | OneNote | `ONENOTE_CONNECTION_URL` |
| `sample_connector_usage_outlook.py` | Outlook.com | `OUTLOOK_CONNECTION_URL` |
| `sample_connector_usage_planner.py` | Microsoft Planner | `PLANNER_CONNECTION_URL` |
| `sample_connector_usage_power_bi.py` | Power BI | `POWERBI_CONNECTION_URL` |
| `sample_connector_usage_rss.py` | RSS | `RSS_CONNECTION_URL` |
| `sample_connector_usage_salesforce.py` | Salesforce | `SALESFORCE_CONNECTION_URL` |
| `sample_connector_usage_service_bus.py` | Azure Service Bus | `SERVICEBUS_CONNECTION_URL` |
| `sample_connector_usage_service_now.py` | ServiceNow | `SERVICENOW_CONNECTION_URL`, `SERVICENOW_RECORD_ID` |
| `sample_connector_usage_sharepoint.py` | SharePoint Online | `SHAREPOINT_CONNECTION_URL` |
| `sample_connector_usage_shifts.py` | Shifts | `SHIFTS_CONNECTION_URL` |
| `sample_connector_usage_slack.py` | Slack | `SLACK_CONNECTION_URL` |
| `sample_connector_usage_smtp.py` | SMTP | `SMTP_CONNECTION_URL` |
| `sample_connector_usage_teams.py` | Microsoft Teams | `TEAMS_CONNECTION_URL` |
| `sample_connector_usage_todo.py` | Microsoft To Do | `TODO_CONNECTION_URL` |
| `sample_connector_usage_universal_print.py` | Universal Print | `UNIVERSALPRINT_CONNECTION_URL` |
| `sample_connector_usage_visual_studio_team_services.py` | Azure DevOps (VSTS) | `VISUALSTUDIOTEAMSERVICES_CONNECTION_URL`, `AZURE_DEVOPS_ORGANIZATION` |
| `sample_connector_usage_wdatp.py` | Windows Defender ATP | `WDATP_CONNECTION_URL` |
| `sample_connector_usage_word_online_business.py` | Word Online (Business) | `WORDONLINEBUSINESS_CONNECTION_URL` |
| `sample_connector_usage_yammer.py` | Yammer (Viva Engage) | `YAMMER_CONNECTION_URL` |
| `sample_connector_usage_azure_event_grid.py` | Azure Event Grid | `AZUREEVENTGRID_CONNECTION_URL` |
| `sample_connector_usage_azure_iot_central.py` | Azure IoT Central | `AZUREIOTCENTRAL_CONNECTION_URL` |
| `sample_connector_usage_cloudconvert.py` | CloudConvert | `CLOUDCONVERT_CONNECTION_URL` |
| `sample_connector_usage_cloudmersive_convert.py` | Cloudmersive Document Conversion | `CLOUDMERSIVECONVERT_CONNECTION_URL` |
| `sample_connector_usage_dynamics_ax.py` | Fin & Ops Apps (Dynamics 365) | `DYNAMICSAX_CONNECTION_URL` |
| `sample_connector_usage_pdf_co.py` | PDF.co | `PDFCO_CONNECTION_URL` |
| `sample_connector_usage_plumsail.py` | Plumsail Documents | `PLUMSAIL_CONNECTION_URL` |
| `sample_connector_usage_sql.py` | SQL Server | `SQL_CONNECTION_URL` |
| `sample_connector_usage_zendesk.py` | Zendesk | `ZENDESK_CONNECTION_URL` |
| `sample_connector_usage_pipedrive.py` | Pipedrive | `PIPEDRIVE_CONNECTION_URL` |
| `sample_connector_usage_docuware.py` | DocuWare | `DOCUWARE_CONNECTION_URL` |
| `sample_connector_usage_signing_hub.py` | SigningHub | `SIGNINGHUB_CONNECTION_URL` |
| `sample_connector_usage_eventbrite.py` | Eventbrite | `EVENTBRITE_CONNECTION_URL` |
| `sample_connector_usage_formstack_forms.py` | Formstack Forms | `FORMSTACKFORMS_CONNECTION_URL` |
| `sample_connector_usage_typeform.py` | Typeform | `TYPEFORM_CONNECTION_URL` |
| `sample_connector_usage_ticketmaster.py` | Ticketmaster | `TICKETMASTER_CONNECTION_URL` |
| `sample_connector_usage_seismic_planner.py` | Seismic Planner | `SEISMICPLANNER_CONNECTION_URL`, `SEISMICPLANNER_SPACE_ID` |
| `sample_connector_usage_zepto_mail.py` | Zoho ZeptoMail | `ZEPTOMAIL_CONNECTION_URL` |
| `sample_connector_usage_waywedo.py` | Way We Do | `WAYWEDO_CONNECTION_URL` |
| `sample_connector_usage_meeting_room_map.py` | Meeting Room Map | `MEETINGROOMMAP_CONNECTION_URL` |
| `sample_connector_usage_star_rez_rest_v1.py` | StarRez REST V1 | `STARREZRESTV1_CONNECTION_URL` |
| `sample_connector_usage_replicon.py` | Replicon | `REPLICON_CONNECTION_URL` |
| `sample_connector_usage_elfsquad_data.py` | Elfsquad Data | `ELFSQUADDATA_CONNECTION_URL`, `ELFSQUADDATA_ENTITY_NAME` |
| `sample_connector_usage_etsy.py` | Etsy | `ETSY_CONNECTION_URL` |
| `sample_connector_usage_impexium.py` | Impexium | `IMPEXIUM_CONNECTION_URL` |
| `sample_connector_usage_jedox_odata_hub.py` | Jedox OData Hub | `JEDOXODATAHUB_CONNECTION_URL` |
| `sample_connector_usage_orderful.py` | Orderful | `ORDERFUL_CONNECTION_URL` |
| `sample_connector_usage_zoho_sign.py` | Zoho Sign | `ZOHOSIGN_CONNECTION_URL`, `ZOHOSIGN_REQUEST_ID` |

Set the appropriate environment variable to your connection runtime URL before running:

```bash
# PowerShell
$env:OFFICE365_CONNECTION_URL = "https://[region].azure-apihub.net/apim/office365/[connection-id]"

# Bash
export OFFICE365_CONNECTION_URL="https://[region].azure-apihub.net/apim/office365/[connection-id]"
```

## Usage Patterns

Root connector modules provide async-only clients and models. Use async
credentials and context managers:

```python
import asyncio

from azure.identity.aio import DefaultAzureCredential

from azure.connectors import ConnectorException
from azure.connectors.<connector> import <Connector>Client
from azure.connectors.<connector> import <RequestModel>

CONNECTION_URL = "https://[region].azure-apihub.net/apim/<connector>/[connection-id]"


async def main():
    async with DefaultAzureCredential() as credential:
        async with <Connector>Client(CONNECTION_URL, credential) as client:
            try:
                result = await client.<operation>(<RequestModel>())
                print(result)
            except ConnectorException as ex:
                print(f"Connector error: {ex}")


asyncio.run(main())
```

Pageable operations return `AsyncItemPaged`. Consume them with `async for`;
do not await pager construction. Await `begin_*` operations to obtain an
`AsyncLROPoller`, then await `poller.result()` while the client remains open.

## Error Handling

The SDK provides structured error handling via `ConnectorException`, which
derives from Azure Core `HttpResponseError`:

```python
try:
    result = await client.some_operation()
except ConnectorException as ex:
    print(f"Status: {ex.status_code}, Message: {ex}")
```

## Next Steps

1. Set up a connection in Azure Portal (see [connection-setup.md](../../docs/connection-setup.md))
2. Set the connection runtime URL environment variable
3. Run the async sample for your connector
4. Use typed clients in your application
5. Deploy to Azure Functions or run locally

## Reference

- API Reference: [Azure Connectors Python SDK](https://azure.github.io/connectors-python-sdk/)
- Generation Guide: [GENERATION.md](../../GENERATION.md)
- Migration Guide: [Unsuffixed async operations](../../docs/migration-sync-aio.md)
