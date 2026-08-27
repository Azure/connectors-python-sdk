"""Meeting Room Map connector SDK sample."""

import asyncio
import os

from azure.identity.aio import DefaultAzureCredential

from azure.connectors import AzureIdentityTokenProvider, ConnectorException
from azure.connectors.meetingroommap import MeetingroommapClient


CONNECTION_RUNTIME_URL = os.environ.get("MEETINGROOMMAP_CONNECTION_URL", "")


async def main() -> None:
    """List Meeting Room Map location categories."""
    if not CONNECTION_RUNTIME_URL:
        print("Set MEETINGROOMMAP_CONNECTION_URL to run this sample.")
        return

    token_provider = AzureIdentityTokenProvider(DefaultAzureCredential())
    try:
        async with MeetingroommapClient(
            CONNECTION_RUNTIME_URL,
            token_provider,
        ) as client:
            categories = await client.get_categories_async()
            print(f"Categories: {categories}")
    except ConnectorException as ex:
        print(f"Connector error: {ex}")


if __name__ == "__main__":
    asyncio.run(main())
