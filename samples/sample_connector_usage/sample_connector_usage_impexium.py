"""Impexium connector SDK sample."""

import asyncio
import os

from azure.identity.aio import DefaultAzureCredential

from azure.connectors import ConnectorException
from azure.connectors.impexium import ImpexiumClient


CONNECTION_RUNTIME_URL = os.environ.get("IMPEXIUM_CONNECTION_URL", "")


async def main() -> None:
    """List countries from Impexium."""
    if not CONNECTION_RUNTIME_URL:
        print("Set IMPEXIUM_CONNECTION_URL to run this sample.")
        return

    credential = DefaultAzureCredential()
    try:
        async with ImpexiumClient(CONNECTION_RUNTIME_URL, credential) as client:
            countries = await client.list_all_countries_async(page_number=1)
            print(f"Countries: {countries}")
    except ConnectorException as ex:
        print(f"Connector error: {ex}")


if __name__ == "__main__":
    asyncio.run(main())
