"""Etsy connector SDK sample."""

import asyncio
import os

from azure.identity.aio import DefaultAzureCredential

from azure.connectors import AzureIdentityTokenProvider, ConnectorException
from azure.connectors.etsy import EtsyClient


CONNECTION_RUNTIME_URL = os.environ.get("ETSY_CONNECTION_URL", "")


async def main() -> None:
    """Ping the Etsy connector."""
    if not CONNECTION_RUNTIME_URL:
        print("Set ETSY_CONNECTION_URL to run this sample.")
        return

    token_provider = AzureIdentityTokenProvider(DefaultAzureCredential())
    try:
        async with EtsyClient(CONNECTION_RUNTIME_URL, token_provider) as client:
            result = await client.ping_async()
            print(f"Result: {result}")
    except ConnectorException as ex:
        print(f"Connector error: {ex}")


if __name__ == "__main__":
    asyncio.run(main())
