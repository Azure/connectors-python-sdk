"""Eventbrite sample for the Azure Connectors Python SDK."""

import asyncio
import os

from azure.identity.aio import DefaultAzureCredential

from azure.connectors import ConnectorException
from azure.connectors.eventbrite import EventbriteClient


CONNECTION_RUNTIME_URL = os.environ.get("EVENTBRITE_CONNECTION_URL", "")


async def main() -> None:
    """List Eventbrite event categories."""
    if not CONNECTION_RUNTIME_URL:
        print("Set EVENTBRITE_CONNECTION_URL to run this sample.")
        return

    async with DefaultAzureCredential() as credential:
        try:
            async with EventbriteClient(CONNECTION_RUNTIME_URL, credential) as client:
                categories = [item async for item in client.list_categories()]
                print(f"Categories: {categories}")
        except ConnectorException as ex:
            print(f"Connector error: {ex}")


if __name__ == "__main__":
    asyncio.run(main())
