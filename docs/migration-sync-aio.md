# Migrate to sync and aio clients

The sync/aio release replaces the asynchronous-only preview API. This is a
clean break: compatibility aliases for the old imports and `_async` operation
names are not provided.

## Choose a client

Synchronous clients live in each root connector module. Asynchronous clients
live in the matching `aio` module. Both clients expose the same unsuffixed
operation names.

| Use case | Client import | Credential |
|---|---|---|
| Synchronous code | `azure.connectors.<connector>` | `azure.core.credentials.TokenCredential` |
| Asynchronous code | `azure.connectors.aio.<connector>` | `azure.core.credentials_async.AsyncTokenCredential` |

Import request and response models from the root connector module in both
modes. The aio module re-exports those same objects, but root imports make model
ownership explicit and avoid coupling application models to an execution mode.

## Update asynchronous code

Move the client import under `aio` and remove `_async` from every operation:

```python
from azure.identity.aio import DefaultAzureCredential

from azure.connectors.aio.office365 import Office365Client
from azure.connectors.office365 import SendEmailInput


async def send_email(connection_url: str) -> None:
    async with DefaultAzureCredential() as credential:
        async with Office365Client(connection_url, credential) as client:
            await client.send_email(
                SendEmailInput(
                    to="recipient@example.com",
                    subject="Hello",
                    body="Sent with Azure Connectors.",
                )
            )
```

Before this release, the client was imported from
`azure.connectors.office365` and the operation was named `send_email_async`.

## Use the synchronous default

Root clients use synchronous Azure Identity credentials and context managers:

```python
from azure.identity import DefaultAzureCredential

from azure.connectors.office365 import Office365Client, SendEmailInput


def send_email(connection_url: str) -> None:
    with DefaultAzureCredential() as credential:
        with Office365Client(connection_url, credential) as client:
            client.send_email(
                SendEmailInput(
                    to="recipient@example.com",
                    subject="Hello",
                    body="Sent with Azure Connectors.",
                )
            )
```

## Migrate pageable operations

Pageable operations no longer return `AsyncIterator`. They return Azure Core
pagers and continue to yield connector items directly.

```python
# Sync: azure.core.paging.ItemPaged
for item in sync_client.list_items(dataset=site_url, table=list_name):
    process(item)

# Async: azure.core.async_paging.AsyncItemPaged
async for item in async_client.list_items(dataset=site_url, table=list_name):
    process(item)
```

Do not await pager construction. Use `by_page(continuation_token=...)` when
page boundaries or a saved continuation token are required.

## Removed preview forms

- Root asynchronous clients and `_async` operation names.
- Awaiting pageable operations as response dictionaries.
- Treating collected page items as a response envelope with a `value` field.
- Importing a generated client from a package-level barrel module.

Location-backed Kusto and Plumsail operations now use `begin_*` methods. Root
clients return `LROPoller`; aio clients return `AsyncLROPoller` after awaiting
the `begin_*` call. Resolve the terminal payload with `poller.result()` and keep
the connector client open until polling completes.
