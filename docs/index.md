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

## Generated property-map contracts

When a connector schema explicitly limits property-map values to strings,
numbers, and Booleans, generated Python models annotate each declared type
(for example, `Dict[str, str | int | float | bool]`). JSON `number` includes
integers. A map with an explicit `null` alternative can retain `None` entries;
`Optional[Dict[...]]` alone only makes the map itself optional. Generated
models reject nested object and list values in a scalar-only map, and the SDK
serializer checks those model fields again before sending JSON. Open dynamic
maps and structured object-valued maps keep their distinct contracts. No
existing client schema was reinterpreted to add scalar alternatives.

The pinned generated fixture verifies model types, scalar wire serialization,
and generated-operation success/error dispatch against the merged async runtime.
Network responses are mocked; this does not establish live-backend support for
the synthetic endpoint. See the [generation guide](https://github.com/Azure/connectors-python-sdk/blob/main/GENERATION.md)
for the exact schema forms and validation boundary.

## Next steps

- [Set up a connector connection](connection-setup.md)
- [Migrate to unsuffixed async operations](migration-sync-aio.md)
- [Browse the API reference](api/index.md)
- [Review the generated contract](generated-contract.md)
- [Understand Azure Functions SDK-type bindings](sdk-type-bindings.md)
