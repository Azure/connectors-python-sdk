"""Way We Do connector SDK sample."""

import asyncio
import os

from azure.identity.aio import DefaultAzureCredential

from azure.connectors import AzureIdentityTokenProvider, ConnectorException
from azure.connectors.waywedo import WaywedoClient


CONNECTION_RUNTIME_URL = os.environ.get("WAYWEDO_CONNECTION_URL", "")


async def main() -> None:
    """Find Way We Do checklists."""
    if not CONNECTION_RUNTIME_URL:
        print("Set WAYWEDO_CONNECTION_URL to run this sample.")
        return

    token_provider = AzureIdentityTokenProvider(DefaultAzureCredential())
    try:
        async with WaywedoClient(CONNECTION_RUNTIME_URL, token_provider) as client:
            checklists = await client.find_checklist_async()
            print(f"Checklists: {checklists}")
    except ConnectorException as ex:
        print(f"Connector error: {ex}")


if __name__ == "__main__":
    asyncio.run(main())
