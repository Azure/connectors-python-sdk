# Azure SDK guideline alignment

This SDK follows the Azure SDK Design Guidelines for Python where they fit the
managed connector execution model. The table records intentional Phase 2
decisions so future changes preserve the public contract.

| Area | Decision | Status |
|---|---|---|
| Synchronous APIs | Provide async-only clients, aligned with the .NET connector SDK. Do not add a synchronous mirror. | Intentional deviation |
| Method names | Use unsuffixed async operation names. | Follow |
| Credentials | Accept caller-owned `AsyncTokenCredential` or `AzureKeyCredential`. | Follow |
| Transports | Accept Azure Core `AsyncHttpTransport` implementations. | Follow |
| Paging | Return `AsyncItemPaged` and support `by_page(continuation_token=...)`. | Follow |
| Models | Define wire models in each root connector module. | Project convention |
| Imports | Export clients lazily from package roots while retaining direct per-connector imports. | Follow |
| Errors | Derive connector service errors from Azure Core `HttpResponseError`. | Follow |
| Request options | Expose keyword-only `timeout`, `headers`, `client_request_id`, and `response_hook`. | Follow |
| Long-running operations | Return `AsyncLROPoller` for retained operations with an HTTP 202 `Location` contract. | Follow |
| API versions | Use each generated operation's managed-connector Swagger version; do not expose a client-level `api_version` override. | Intentional deviation |
| Return values | Return connector payloads directly rather than Azure Core `Response[T]` wrappers. | Intentional deviation |

## Namespace shape

```python
# Async client and models
from azure.connectors.office365 import Office365Client, SendEmailInput

# Clients are also available as lazy package-root exports
from azure.connectors import Office365Client
```

Clients, models, type aliases, enums, and `TRIGGER_OPERATIONS` live in the same
root connector module. There is no separate aio client catalog.

Location-backed operations use awaited `begin_*` calls. Azure
status-document protocols, poller continuation tokens, and cancellation are
not part of the current contract.

Managed connectors can route operations to different service API versions
within one client. Generated operations therefore retain their Swagger-declared
internal version defaults instead of accepting one constructor-level
`api_version` that could override unrelated routes.

## Compatibility policy

Async-only does not restore the old preview API. Operations no longer use
`_async` suffixes, optional parameters and request controls remain keyword-only,
and Azure Core credentials, errors, pagers, and pollers remain. Package-root
exports are lazy so importing `azure.connectors` does not
load every generated module. See the [migration guide](migration-sync-aio.md)
for mechanical changes.
