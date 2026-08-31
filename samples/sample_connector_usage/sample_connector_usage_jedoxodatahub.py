"""Jedox OData Hub connector SDK sample."""

import asyncio
import os

from azure.identity.aio import DefaultAzureCredential

from azure.connectors import AzureIdentityTokenProvider, ConnectorException
from azure.connectors.jedoxodatahub import JedoxodatahubClient


CONNECTION_RUNTIME_URL = os.environ.get("JEDOXODATAHUB_CONNECTION_URL", "")


async def main() -> None:
    """List Jedox databases."""
    if not CONNECTION_RUNTIME_URL:
        print("Set JEDOXODATAHUB_CONNECTION_URL to run this sample.")
        return

    token_provider = AzureIdentityTokenProvider(DefaultAzureCredential())
    try:
        async with JedoxodatahubClient(
            CONNECTION_RUNTIME_URL,
            token_provider,
        ) as client:
            databases = await client.databases_async()
            print(f"Databases: {databases}")
    except ConnectorException as ex:
        print(f"Connector error: {ex}")


if __name__ == "__main__":
    asyncio.run(main())
