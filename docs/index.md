# Azure Connectors Python SDK

Build type-safe Python integrations with Azure managed connectors for services such as Microsoft 365, Azure, Salesforce, and GitHub.

!!! warning "Early preview"
    This SDK is under active development and is not intended for production use. Breaking API and model changes should be expected before the first stable release.

## Install

```bash
python -m pip install azure-connectors
```

The SDK requires Python 3.10 or later and provides asynchronous connector clients, typed request and response models, and Azure Identity integration.

## Create a client

```python
from azure.connectors.office365 import Office365Client
from azure.connectors.sdk import ManagedIdentityTokenProvider


async def list_messages(connection_url: str) -> None:
    token_provider = ManagedIdentityTokenProvider()

    async with Office365Client(connection_url, token_provider) as client:
        messages = await client.get_emails_async(
            folder_path="Inbox",
        )
        print(messages)
```

Connector signatures are generated from their managed connector contracts. Consult the [API reference](api/index.md) for the exact client method and model names in the current branch.

## Next steps

- [Set up a connector connection](connection-setup.md)
- [Browse the API reference](api/index.md)
- [Understand Azure Functions SDK-type bindings](sdk-type-bindings.md)
