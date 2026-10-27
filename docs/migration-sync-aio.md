# Migrate to unsuffixed async operations

Clients remain asynchronous at `azure.connectors.<connector>`, as in the
earlier preview. The SDK provides no synchronous mirror, an intentional
divergence from the Azure SDK guideline aligned with the .NET connector SDK.
Compatibility aliases for `_async` operation names are not provided.

## Choose a client

Import async clients and models from each root connector module.

| Use case | Client import | Credential |
|---|---|---|
| Asynchronous code | `azure.connectors.<connector>` | `azure.core.credentials_async.AsyncTokenCredential` |

Connections that expect API keys also accept `AzureKeyCredential`.

## Update asynchronous code

Keep the root client import and remove `_async` from operation names:

```python
from azure.identity.aio import DefaultAzureCredential

from azure.connectors.office365 import Office365Client, SendEmailInput


async def send_email(connection_url: str) -> None:
    async with DefaultAzureCredential() as credential:
        async with Office365Client(connection_url, credential) as client:
            await client.send_email(
                input=SendEmailInput(
                    to="recipient@example.com",
                    subject="Hello",
                    body="Sent with Azure Connectors.",
                )
            )
```

Before this release, the client was imported from
`azure.connectors.office365` and the operation was named `send_email_async`.

## Keep the new request contract

Async-only is not a return to the old signatures or response shapes:

- Pass optional operation parameters and request controls by keyword.
- Replace legacy token providers and `ConnectorClientOptions` with caller-owned
    `AsyncTokenCredential` or `AzureKeyCredential` and direct client options.
- Inject `AsyncHttpTransport` implementations. Clients close transports;
    callers close their async credentials.
- Catch `ConnectorException` or its Azure Core base `HttpResponseError`.
- If you evaluated the intermediate dual-mode branch, replace
    `azure.connectors.aio.<connector>` imports with `azure.connectors.<connector>`;
    retain `await` and `async with`.

## Migrate pageable operations

Pageable operations no longer return `AsyncIterator`. They return Azure Core `AsyncItemPaged`
pagers and continue to yield connector items directly.

```python
# Async: azure.core.async_paging.AsyncItemPaged
async for item in client.list_items(dataset=site_url, table=list_name):
    process(item)
```

Do not await pager construction. Use `by_page(continuation_token=...)` when
page boundaries or a saved continuation token are required.

## Removed preview forms

- `_async` operation names; root asynchronous clients remain.
- Awaiting pageable operations as response dictionaries.
- Treating collected page items as a response envelope with a `value` field.

Generated clients are also available as lazy exports from `azure.connectors`.
Prefer concrete connector-module imports so clients and models share one import
location.

Location-backed Kusto and Plumsail operations now use `begin_*` methods. Root
clients return `AsyncLROPoller` after awaiting
the `begin_*` call. Resolve the terminal payload with `await poller.result()` and keep
the connector client open until polling completes.
