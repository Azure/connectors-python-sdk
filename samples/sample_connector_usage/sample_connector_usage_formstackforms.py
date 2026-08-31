"""Formstack Forms connector SDK sample."""

import asyncio
import os

from azure.identity.aio import DefaultAzureCredential

from azure.connectors import AzureIdentityTokenProvider, ConnectorException
from azure.connectors.formstackforms import FormstackformsClient


CONNECTION_RUNTIME_URL = os.environ.get("FORMSTACKFORMS_CONNECTION_URL", "")


async def main() -> None:
    """List available Formstack forms."""
    if not CONNECTION_RUNTIME_URL:
        print("Set FORMSTACKFORMS_CONNECTION_URL to run this sample.")
        return

    token_provider = AzureIdentityTokenProvider(DefaultAzureCredential())
    try:
        async with FormstackformsClient(
            CONNECTION_RUNTIME_URL,
            token_provider,
        ) as client:
            forms = await client.get_available_forms_async()
            print(f"Forms: {forms}")
    except ConnectorException as ex:
        print(f"Connector error: {ex}")


if __name__ == "__main__":
    asyncio.run(main())
