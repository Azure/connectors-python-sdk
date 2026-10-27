# Azure Connectors Python SDK

Build type-safe Python integrations with Azure managed connectors for services such as Microsoft 365, Azure, Salesforce, and GitHub.

!!! warning "Early preview"
    This SDK is under active development and is not intended for production use. Breaking API and model changes should be expected before the first stable release.

## Install

```bash
python -m pip install azure-connectors
```

The SDK requires Python 3.10 or later and provides async-only root connector clients, typed models, and Azure Identity integration. Non-pageable responses return payload values; pageable operations return `AsyncItemPaged`. No synchronous mirror is provided, aligned with the .NET connector SDK.

## Create a client

Generated clients require a caller-owned `AsyncTokenCredential` or `AzureKeyCredential`. Import clients and models from the root connector module. Operations do not use an `_async` suffix.

```python
from azure.identity.aio import DefaultAzureCredential

from azure.connectors.office365 import Office365Client


async def list_messages(connection_url: str) -> None:
    async with DefaultAzureCredential() as credential:
        async with Office365Client(connection_url, credential) as client:
            messages = [message async for message in client.list_emails()]
            print(messages)
```

Connector signatures are generated from their managed connector contracts. Consult the [API reference](api/index.md) for the exact client method and model names in the current branch.

## Next steps

- [Set up a connector connection](connection-setup.md)
- [Migrate to unsuffixed async operations](migration-sync-aio.md)
- [Browse the API reference](api/index.md)
- [Review the generated contract](generated-contract.md)
- [Understand Azure Functions SDK-type bindings](sdk-type-bindings.md)
