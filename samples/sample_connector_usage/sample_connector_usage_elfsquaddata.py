"""Elfsquad Data connector SDK sample."""

import asyncio
import os

from azure.identity.aio import DefaultAzureCredential

from azure.connectors import ConnectorException
from azure.connectors.elfsquaddata import ElfsquaddataClient


CONNECTION_RUNTIME_URL = os.environ.get("ELFSQUADDATA_CONNECTION_URL", "")


async def main() -> None:
    """List Elfsquad Data schemas."""
    if not CONNECTION_RUNTIME_URL:
        print("Set ELFSQUADDATA_CONNECTION_URL to run this sample.")
        return

    credential = DefaultAzureCredential()
    try:
        async with ElfsquaddataClient(CONNECTION_RUNTIME_URL, credential) as client:
            schemas = await client.get_schemas_async()
            print(f"Schemas: {schemas}")
    except ConnectorException as ex:
        print(f"Connector error: {ex}")


if __name__ == "__main__":
    asyncio.run(main())
