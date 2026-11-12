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
| `azure.connectors.dataflowssms.DataflowssmsClient` | `azure.connectors.data_flows_sms.DataFlowsSmsClient` |
| `azure.connectors.jedoxodatahub.JedoxodatahubClient` | `azure.connectors.jedox_odata_hub.JedoxODataHubClient` |
| `azure.connectors.msgraphgroupsanduser.MsgraphgroupsanduserClient` | `azure.connectors.ms_graph_groups_and_users.MSGraphGroupsAndUsersClient` |

Types use their documented PascalCase spelling, generated operations and
model attributes use snake_case, and constants and enum members use uppercase
names. For example, `RemoveWhitespaceFromTextRequest` is now
`RemoveWhiteSpaceFromTextRequest`, and its attribute
`text_containing_white_space` still serializes to `TextContainingWhitespace`.
Versioned operations retain their version tokens; consult the regenerated
client signature before changing a call.

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
