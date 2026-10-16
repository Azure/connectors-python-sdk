# Azure SDK guideline alignment

This SDK follows the Azure SDK Design Guidelines for Python where they fit the
managed connector execution model. The table records intentional Phase 2
decisions so future changes preserve the public contract.

| Area | Decision | Status |
|---|---|---|
| Sync and async APIs | Provide synchronous clients at the connector root and asynchronous clients under `.aio`. | Follow |
| Method names | Use the same unsuffixed operation name on sync and aio clients. | Follow |
| Credentials | Accept caller-owned `TokenCredential`/`AsyncTokenCredential` or `AzureKeyCredential`. | Follow |
| Transports | Accept Azure Core `HttpTransport`/`AsyncHttpTransport` implementations. | Follow |
| Paging | Return `ItemPaged`/`AsyncItemPaged` and support `by_page(continuation_token=...)`. | Follow |
| Models | Define wire models once in the root connector module and share object identity with aio. | Project convention |
| Imports | Export clients lazily from package roots while retaining direct per-connector imports. | Follow |
| Errors | Derive connector service errors from Azure Core `HttpResponseError`. | Follow |
| Request options | Expose keyword-only `timeout`, `headers`, `client_request_id`, and `response_hook` on both modes. | Follow |
| Long-running operations | Return `LROPoller`/`AsyncLROPoller` for retained operations with an HTTP 202 `Location` contract. | Follow |
| API versions | Use each generated operation's managed-connector Swagger version; do not expose a client-level `api_version` override. | Intentional deviation |
| Return values | Return connector payloads directly rather than Azure Core `Response[T]` wrappers. | Intentional deviation |

## Namespace shape

```python
# Synchronous client and shared models
from azure.connectors.office365 import Office365Client, SendEmailInput

# Asynchronous client; models still come from the root module
from azure.connectors.aio.office365 import Office365Client
from azure.connectors.office365 import SendEmailInput

# Clients are also available as lazy package-root exports
from azure.connectors import Office365Client
from azure.connectors.aio import Office365Client
```

The two clients have distinct identities and runtimes. Models, type aliases,
enums, and `TRIGGER_OPERATIONS` have shared identity across the paired modules.

Location-backed operations use the same `begin_*` name in both modes. Azure
status-document protocols, poller continuation tokens, and cancellation are
not part of the current contract.

Managed connectors can route operations to different service API versions
within one client. Generated operations therefore retain their Swagger-declared
internal version defaults instead of accepting one constructor-level
`api_version` that could override unrelated routes.

## Compatibility policy

The pre-1.0 async-only surface is replaced rather than shimmed. Root modules do
not retain asynchronous client aliases, and aio methods do not retain `_async`
aliases. Package-root exports are lazy so importing `azure.connectors` does not
load every generated module. See the [migration guide](migration-sync-aio.md)
for mechanical changes.
