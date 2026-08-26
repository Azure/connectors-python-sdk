"""Ticketmaster connector SDK sample."""

import asyncio
import os

from azure.identity.aio import DefaultAzureCredential

from azure.connectors import AzureIdentityTokenProvider, ConnectorException
from azure.connectors.ticketmaster import TicketmasterClient


CONNECTION_RUNTIME_URL = os.environ.get("TICKETMASTER_CONNECTION_URL", "")


async def main() -> None:
    """List Ticketmaster attractions."""
    if not CONNECTION_RUNTIME_URL:
        print("Set TICKETMASTER_CONNECTION_URL to run this sample.")
        return

    token_provider = AzureIdentityTokenProvider(DefaultAzureCredential())
    try:
        async with TicketmasterClient(CONNECTION_RUNTIME_URL, token_provider) as client:
            attractions = await client.attractions_get_async()
            print(f"Attractions: {attractions}")
    except ConnectorException as ex:
        print(f"Connector error: {ex}")


if __name__ == "__main__":
    asyncio.run(main())
