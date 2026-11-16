# Azure Connectors Python SDK

Type-safe, async Python clients for Azure managed connectors. Version 1.0.0 is
the first generally available release, with 103 connector clients for services
such as Office 365, SharePoint, Teams, Dataverse, Salesforce, and GitHub.

## Install

Requires Python 3.10 or later.

```bash
pip install azure-connectors
```

## Send an email

Create a connector connection and grant your identity access before calling it.
See the [connection setup guide](https://azure.github.io/connectors-python-sdk/connection-setup/).

```python
import asyncio

from azure.identity.aio import DefaultAzureCredential
from azure.connectors.office365 import Office365Client, SendEmailInput


async def main():
    connection_url = "https://example.azure.com/connections/office365"

    async with DefaultAzureCredential() as credential:
        async with Office365Client(connection_url, credential) as client:
            await client.send_email(
                input=SendEmailInput(
                    to="recipient@example.com",
                    subject="Hello from Python",
                    body="<p>Sent with the Azure Connectors Python SDK.</p>",
                )
            )


if __name__ == "__main__":
    asyncio.run(main())
```

## Features

- Async-only clients and typed models in `azure.connectors.<connector>`.
- Caller-owned async Azure Identity or Azure Core API key credentials.
- Azure Core pipelines, request controls, and configurable retry policies.
- `AsyncItemPaged` collections and `AsyncLROPoller` long-running operations.
- Lazy client exports, type stubs, and generated API documentation.

Safe HTTP methods use configured retries. Unsafe methods make one attempt by
default; opt in to retries only when an operation can tolerate replay.

SDK general availability does not change the availability, permissions, or
service limits of the Azure connector resources and services your app uses.
Azure Functions trigger hosting and SDK-type conversion use a separate extension.

## Documentation and migration

- [Documentation and API reference](https://azure.github.io/connectors-python-sdk/)
- [Supported connectors](https://github.com/Azure/connectors-python-sdk#validated-connectors)
- [Release notes](https://github.com/Azure/connectors-python-sdk/blob/main/CHANGELOG.md)
- [Preview API migration](https://azure.github.io/connectors-python-sdk/migration-sync-aio/)
- [Preview naming migration](https://azure.github.io/connectors-python-sdk/naming-migration/)
- [Report an issue](https://github.com/Azure/connectors-python-sdk/issues)

This project uses the [MIT license](https://github.com/Azure/connectors-python-sdk/blob/main/LICENSE).