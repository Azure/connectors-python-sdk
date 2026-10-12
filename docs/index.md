# Azure Connectors Python SDK

Build type-safe Python integrations with Azure managed connectors for services such as Microsoft 365, Azure, Salesforce, and GitHub.

!!! warning "Early preview"
    This SDK is under active development and is not intended for production use. Breaking API and model changes should be expected before the first stable release.

## Install

```bash
python -m pip install azure-connectors
```

The SDK requires Python 3.10 or later and provides synchronous connector clients at the package root, asynchronous clients under `.aio`, shared typed models, and Azure Identity integration. Non-pageable connector responses are returned as payload values; pageable operations return Azure Core pagers.

## Create a client

Generated clients require a caller-owned Azure Identity credential or an `AzureKeyCredential`. Root clients are synchronous:

```python
from azure.identity import DefaultAzureCredential

from azure.connectors.office365 import Office365Client


def list_messages(connection_url: str) -> None:
    with DefaultAzureCredential() as credential:
        with Office365Client(connection_url, credential) as client:
            messages = client.get_emails(
                folder_path="Inbox",
            )
            print(messages)
```

Use the matching client under `azure.connectors.aio` for asynchronous code. Operation names are identical on both surfaces and never use an `_async` suffix. Models remain in the root connector module.

```python
from azure.identity.aio import DefaultAzureCredential

from azure.connectors.aio.office365 import Office365Client


async def list_messages(connection_url: str) -> None:
    async with DefaultAzureCredential() as credential:
        async with Office365Client(connection_url, credential) as client:
            messages = await client.get_emails(folder_path="Inbox")
            print(messages)
```

Connector signatures are generated from their managed connector contracts. Consult the [API reference](api/index.md) for the exact client method and model names in the current branch.

## Next steps

- [Set up a connector connection](connection-setup.md)
- [Migrate from the async-only preview](migration-sync-aio.md)
- [Browse the API reference](api/index.md)
- [Review the generated contract](generated-contract.md)
- [Understand Azure Functions SDK-type bindings](sdk-type-bindings.md)
