"""Orderful connector SDK sample."""

import asyncio
import os

from azure.identity.aio import DefaultAzureCredential

from azure.connectors import ConnectorException
from azure.connectors.orderful import OrderfulClient


CONNECTION_RUNTIME_URL = os.environ.get("ORDERFUL_CONNECTION_URL", "")


async def main() -> None:
    """List Orderful transactions."""
    if not CONNECTION_RUNTIME_URL:
        print("Set ORDERFUL_CONNECTION_URL to run this sample.")
        return

    credential = DefaultAzureCredential()
    try:
        async with OrderfulClient(CONNECTION_RUNTIME_URL, credential) as client:
            await client.list_transactions_async()
            print("Transactions requested.")
    except ConnectorException as ex:
        print(f"Connector error: {ex}")


if __name__ == "__main__":
    asyncio.run(main())
