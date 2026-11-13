# Migrate generated Python names

This early-preview update corrects Python module word boundaries and generated
identifiers. The old module and type spellings are not compatibility aliases.
Update both direct imports and package-root client imports, then update model
fields and method references using the current generated API reference.

| Before | After |
|---|---|
| `azure.connectors.azuread.AzureadClient` | `azure.connectors.azure_ad.AzureADClient` |
| `azure.connectors.azuredatafactory.AzuredatafactoryClient` | `azure.connectors.azure_data_factory.AzureDataFactoryClient` |
| `azure.connectors.azureiotcentral.AzureiotcentralClient` | `azure.connectors.azure_iot_central.AzureIoTCentralClient` |
| `azure.connectors.cloudconvert.CloudconvertClient` | `azure.connectors.cloud_convert.CloudConvertClient` |
| `azure.connectors.dataflowssms.DataflowssmsClient` | `azure.connectors.data_flows_sms.DataFlowsSmsClient` |
| `azure.connectors.docuware.DocuwareClient` | `azure.connectors.docu_ware.DocuWareClient` |
| `azure.connectors.jedoxodatahub.JedoxodatahubClient` | `azure.connectors.jedox_odata_hub.JedoxODataHubClient` |
| `azure.connectors.msgraphgroupsanduser.MsgraphgroupsanduserClient` | `azure.connectors.ms_graph_groups_and_users.MSGraphGroupsAndUsersClient` |
| `azure.connectors.onenote.OnenoteClient` | `azure.connectors.one_note.OneNoteClient` |
| `azure.connectors.waywedo.WaywedoClient` | `azure.connectors.way_we_do.WayWeDoClient` |

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
