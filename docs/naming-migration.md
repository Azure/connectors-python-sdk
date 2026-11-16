# Migrate generated Python names

This early-preview update corrects Python module word boundaries and generated
identifiers. The old module and type spellings are not compatibility aliases.
The table lists every client whose import changes, compared with the previous
release. Update direct imports (`from azure.connectors.azure_blob import
AzureBlobClient`) to the new module and class. Package-root imports
(`from azure.connectors import AzureBlobClient`) do not name a module, so they
only need the new class name. Then update model fields and method references
using the current generated API reference.

A brand written as one word or in PascalCase stays one Python token, and a
brand is split only where its own name has a space, hyphen or dot. GitHub is
`github`, SharePoint Online is `sharepoint_online` and ClickSend SMS is
`clicksend_sms`, but PDF.co is `pdf_co` and Way We Do is `way_we_do`. Modules such as `cloudconvert`,
`github` and `onenote` therefore keep their previous name; only their client
class changes.

| Before | After |
|---|---|
| `azure.connectors.azuread.AzureadClient` | `azure.connectors.azure_ad.AzureADClient` |
| `azure.connectors.azureautomation.AzureautomationClient` | `azure.connectors.azure_automation.AzureAutomationClient` |
| `azure.connectors.azureblob.AzureblobClient` | `azure.connectors.azure_blob.AzureBlobClient` |
| `azure.connectors.azuredatafactory.AzuredatafactoryClient` | `azure.connectors.azure_data_factory.AzureDataFactoryClient` |
| `azure.connectors.azuredigitaltwins.AzuredigitaltwinsClient` | `azure.connectors.azure_digital_twins.AzureDigitalTwinsClient` |
| `azure.connectors.azureeventgrid.AzureeventgridClient` | `azure.connectors.azure_event_grid.AzureEventGridClient` |
| `azure.connectors.azureiotcentral.AzureiotcentralClient` | `azure.connectors.azure_iot_central.AzureIoTCentralClient` |
| `azure.connectors.azuremonitorlogs.AzuremonitorlogsClient` | `azure.connectors.azure_monitor_logs.AzureMonitorLogsClient` |
| `azure.connectors.azurequeues.AzurequeuesClient` | `azure.connectors.azure_queues.AzureQueuesClient` |
| `azure.connectors.azuretables.AzuretablesClient` | `azure.connectors.azure_tables.AzureTablesClient` |
| `azure.connectors.azurevm.AzurevmClient` | `azure.connectors.azure_vm.AzureVMClient` |
| `azure.connectors.clicksendsms.ClicksendsmsClient` | `azure.connectors.clicksend_sms.ClickSendSmsClient` |
| `azure.connectors.cloudconvert.CloudconvertClient` | `azure.connectors.cloudconvert.CloudConvertClient` |
| `azure.connectors.cloudmersiveconvert.CloudmersiveconvertClient` | `azure.connectors.cloudmersive_convert.CloudmersiveConvertClient` |
| `azure.connectors.commondataservice.CommondataserviceClient` | `azure.connectors.common_data_service.CommonDataServiceClient` |
| `azure.connectors.documentdb.DocumentdbClient` | `azure.connectors.documentdb.DocumentDBClient` |
| `azure.connectors.docuware.DocuwareClient` | `azure.connectors.docuware.DocuWareClient` |
| `azure.connectors.dynamicsax.DynamicsaxClient` | `azure.connectors.dynamics_ax.DynamicsAXClient` |
| `azure.connectors.elfsquaddata.ElfsquaddataClient` | `azure.connectors.elfsquad_data.ElfsquadDataClient` |
| `azure.connectors.eventhubs.EventhubsClient` | `azure.connectors.event_hubs.EventHubsClient` |
| `azure.connectors.excelonline.ExcelonlineClient` | `azure.connectors.excel_online.ExcelOnlineClient` |
| `azure.connectors.excelonlinebusiness.ExcelonlinebusinessClient` | `azure.connectors.excel_online_business.ExcelOnlineBusinessClient` |
| `azure.connectors.formstackforms.FormstackformsClient` | `azure.connectors.formstack_forms.FormstackFormsClient` |
| `azure.connectors.github.GithubClient` | `azure.connectors.github.GitHubClient` |
| `azure.connectors.googlecalendar.GooglecalendarClient` | `azure.connectors.google_calendar.GoogleCalendarClient` |
| `azure.connectors.googledrive.GoogledriveClient` | `azure.connectors.google_drive.GoogleDriveClient` |
| `azure.connectors.googletasks.GoogletasksClient` | `azure.connectors.google_tasks.GoogleTasksClient` |
| `azure.connectors.jedoxodatahub.JedoxodatahubClient` | `azure.connectors.jedox_odata_hub.JedoxODataHubClient` |
| `azure.connectors.keyvault.KeyvaultClient` | `azure.connectors.key_vault.KeyVaultClient` |
| `azure.connectors.meetingroommap.MeetingroommapClient` | `azure.connectors.meeting_room_map.MeetingRoomMapClient` |
| `azure.connectors.microsoftbookings.MicrosoftbookingsClient` | `azure.connectors.microsoft_bookings.MicrosoftBookingsClient` |
| `azure.connectors.microsoftforms.MicrosoftformsClient` | `azure.connectors.microsoft_forms.MicrosoftFormsClient` |
| `azure.connectors.mq.MqClient` | `azure.connectors.mq.MQClient` |
| `azure.connectors.msgraphgroupsanduser.MsgraphgroupsanduserClient` | `azure.connectors.ms_graph_groups_and_users.MSGraphGroupsAndUsersClient` |
| `azure.connectors.office365groups.Office365groupsClient` | `azure.connectors.office365_groups.Office365GroupsClient` |
| `azure.connectors.office365groupsmail.Office365groupsmailClient` | `azure.connectors.office365_groups_mail.Office365GroupsMailClient` |
| `azure.connectors.office365users.Office365usersClient` | `azure.connectors.office365_users.Office365UsersClient` |
| `azure.connectors.onedrive.OnedriveClient` | `azure.connectors.onedrive.OneDriveClient` |
| `azure.connectors.onedriveforbusiness.OnedriveforbusinessClient` | `azure.connectors.onedrive_for_business.OneDriveForBusinessClient` |
| `azure.connectors.onenote.OnenoteClient` | `azure.connectors.onenote.OneNoteClient` |
| `azure.connectors.pdfco.PdfcoClient` | `azure.connectors.pdf_co.PdfCoClient` |
| `azure.connectors.powerbi.PowerbiClient` | `azure.connectors.power_bi.PowerBIClient` |
| `azure.connectors.projectplace.ProjectplaceClient` | `azure.connectors.projectplace.ProjectPlaceClient` |
| `azure.connectors.revai.RevaiClient` | `azure.connectors.rev_ai.RevAIClient` |
| `azure.connectors.seismicplanner.SeismicplannerClient` | `azure.connectors.seismic_planner.SeismicPlannerClient` |
| `azure.connectors.sendgrid.SendgridClient` | `azure.connectors.sendgrid.SendGridClient` |
| `azure.connectors.servicebus.ServicebusClient` | `azure.connectors.service_bus.ServiceBusClient` |
| `azure.connectors.sharepointonline.SharepointonlineClient` | `azure.connectors.sharepoint_online.SharePointOnlineClient` |
| `azure.connectors.signinghub.SigninghubClient` | `azure.connectors.signinghub.SigningHubClient` |
| `azure.connectors.starrezrestv1.Starrezrestv1Client` | `azure.connectors.starrez_rest_v1.StarRezRestV1Client` |
| `azure.connectors.textrequest.TextrequestClient` | `azure.connectors.text_request.TextRequestClient` |
| `azure.connectors.universalprint.UniversalprintClient` | `azure.connectors.universal_print.UniversalPrintClient` |
| `azure.connectors.visualstudioteamservices.VisualstudioteamservicesClient` | `azure.connectors.visual_studio_team_services.VisualStudioTeamServicesClient` |
| `azure.connectors.waywedo.WaywedoClient` | `azure.connectors.way_we_do.WayWeDoClient` |
| `azure.connectors.wordonlinebusiness.WordonlinebusinessClient` | `azure.connectors.word_online_business.WordOnlineBusinessClient` |
| `azure.connectors.wordpress.WordpressClient` | `azure.connectors.wordpress.WordPressClient` |
| `azure.connectors.zeptomail.ZeptomailClient` | `azure.connectors.zeptomail.ZeptoMailClient` |
| `azure.connectors.zohosign.ZohosignClient` | `azure.connectors.zoho_sign.ZohoSignClient` |

Types use their documented PascalCase spelling, generated operations and
model attributes use snake_case, and constants and enum members use uppercase
names. For example, `RemoveWhitespaceFromTextRequest` is now
`RemoveWhiteSpaceFromTextRequest`, its attribute
`text_containing_whitespace` still serializes to `TextContainingWhitespace`, and
`user_name` attributes and parameters use the Python closed-word spelling
`username` (while `file_name` remains `file_name`).
Versioned operations retain their version tokens; consult the regenerated
client signature before changing a call.

Model fields whose wire names are SCREAMING_SNAKE_CASE now keep each word
instead of splitting every letter. For example, Insightly
`p_u_b_l_i_c_l_y_v_i_s_i_b_l_e`, `o_w_n_e_r_u_s_e_r_id`, `v_i_s_i_b_l_e_t_o` and
`d_a_t_e_c_r_e_a_t_e_d_u_t_c` become `publicly_visible`, `owner_user_id`,
`visible_to` and `date_created_utc`; their wire names (`PUBLICLY_VISIBLE`,
`OWNER_USER_ID`, `VISIBLE_TO`, `DATE_CREATED_UTC`) are unchanged.

Fields and parameters follow the same brand rule where the wire name writes the
brand as one word: Impexium `linked_in` becomes `linkedin` (wire `linkedIn`),
and OneNote `one_note_client_url` and `one_note_web_url` become
`onenote_client_url` and `onenote_web_url`. A wire name that already separates
the words, such as SigningHub `one_drive`, keeps its spelling.

Teams AI insight types now spell `AIInsight` consistently:
`AiInsightDetailResponse`, `AiInsightActionItem`, `AiInsightMeetingNote`,
`AiInsightMeetingNoteSubpoint`, `AiInsightMentionEvent`, `AiInsightViewpoint`,
`AiInsightWebhookResponseSchema` and `DynamicAiInsightTriggerRequest` become
`AIInsightDetailResponse`, `AIInsightActionItem`, `AIInsightMeetingNote`,
`AIInsightMeetingNoteSubpoint`, `AIInsightMentionEvent`, `AIInsightViewpoint`,
`AIInsightWebhookResponseSchema` and `DynamicAIInsightTriggerRequest`, matching
`AIInsightResponse` and `AIInsightCollectionResponse`.
PdfCo request types now use the same normalized words as their response
counterparts: `PdfFromXlsxlsxInput` becomes `PdfFromXlsXlsxInput`,
`PdfUnSearchableInput` becomes `PdfUnsearchableInput`, and `XLStoCsvInput`,
`XLStoHtmlInput`, `XLStoJsonInput`, `XLStoTxtInput`, and `XLStoXmlInput`
become `XlsToCsvInput`, `XlsToHtmlInput`, `XlsToJsonInput`, `XlsToTxtInput`,
and `XlsToXmlInput`. Their JSON field names remain unchanged.

Only Python identifiers change. Connection setup still uses raw managed-API
IDs such as `azuread`, `dataflowssms`, and `service-now`; operation IDs, routes,
request/response JSON keys and enum wire values do not change because of the
naming migration. If a separate Swagger refresh changes those contracts,
review that change independently rather than treating it as a spelling fix.
Do not rewrite connection URLs or serialized payload keys.
For all 103 canonical modules and their clients, consult the
[generated API reference](api/index.md) or `azure.connectors.CLIENT_REGISTRY`.

## Separate operation selection in refreshed Swagger

These operation changes are **not** spelling aliases or changes to connection
IDs. Plumsail's deprecated revision-1 process execution endpoints are not
emitted in the refreshed client. Use
`begin_flow_v1_processes_flow_jobs_execute_process_v2` or
`begin_flow_v1_processes_flow_jobs_execute_process_with_generated_data_multiple_outputs`
for the corresponding current revision-2 process operations. Both await to
Azure Core `AsyncLROPoller` results using `Location` polling and require
`output_files_as` in addition to the request body and process ID. The
`FlowV1ProcessesFlowTriggersV2Post` trigger metadata replaces the deprecated
revision-1 `FlowV1ProcessesFlowTriggersPost` entry. Update code that inspects
trigger metadata; triggers are not callable client methods.

The Azure DevOps (VSTS) client's Preview
`get_work_item_details_v2` operation is intentionally not exposed. The
production `get_work_item_details` operation remains available at
`/_apis/wit/workitems/{id}`. Do not treat the absence of the Preview method
as a naming alias for the production method; confirm its route and parameters
before migrating a call.

The Python names above describe the current generated clients; consult the
[API reference](api/index.md) for all parameters and response types. A
separate Swagger refresh may change operations independently of the Python
identifier migration.

## Additional paging and SMS behavior

For generated pagers, `async for item in client.list_items(...)` still yields
individual items. To retain page-level fields and HTTP metadata, iterate
`client.list_items(...).by_page()` instead. Each yielded `ConnectorPage` is an
async iterator of items and exposes the parsed `page_model`, immutable
`raw_response` (`ConnectorResponseSnapshot`), and `continuation_token`. For
example, `page.page_model["sensitivityLabelInfo"]` remains available on Excel
Online (Business) table pages even though it is not itself a row.

DataFlows SMS also offers `send_sms_get` for `GET /sms/send` in addition to
`send_sms` for `POST /sms/send`. The GET route **sends** a message: the SDK
never retries it, even when `retry_unsafe_http_methods=True`. Ordinary
read-only GET calls such as `list_sms` retain their configured retry behavior.
The raw connector identity remains `dataflowssms`.
