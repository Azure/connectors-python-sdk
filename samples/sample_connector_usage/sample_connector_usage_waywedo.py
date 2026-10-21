"""Way We Do sample for the Azure Connectors Python SDK."""

import asyncio
import os

from azure.identity.aio import DefaultAzureCredential

from azure.connectors import ConnectorException
from azure.connectors.waywedo import WaywedoClient


CONNECTION_RUNTIME_URL = os.environ.get("WAYWEDO_CONNECTION_URL", "")


async def main() -> None:
    """Find Way We Do checklists."""
    if not CONNECTION_RUNTIME_URL:
        print("Set WAYWEDO_CONNECTION_URL to run this sample.")
        return

    async with DefaultAzureCredential() as credential:
        try:
            async with WaywedoClient(CONNECTION_RUNTIME_URL, credential) as client:
                checklists = [item async for item in client.list_find_checklist()]
                print(f"Checklists: {checklists}")
        except ConnectorException as ex:
            print(f"Connector error: {ex}")


if __name__ == "__main__":
    asyncio.run(main())
