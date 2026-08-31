"""Elfsquad Data connector SDK sample."""

import asyncio
import os

from azure.identity.aio import DefaultAzureCredential

from azure.connectors import AzureIdentityTokenProvider, ConnectorException
from azure.connectors.elfsquaddata import ElfsquaddataClient


CONNECTION_RUNTIME_URL = os.environ.get("ELFSQUADDATA_CONNECTION_URL", "")
ENTITY_NAME = os.environ.get("ELFSQUADDATA_ENTITY_NAME", "")


async def main() -> None:
    """List entities from an Elfsquad Data entity set."""
    if not CONNECTION_RUNTIME_URL or not ENTITY_NAME:
        print(
            "Set ELFSQUADDATA_CONNECTION_URL and ELFSQUADDATA_ENTITY_NAME "
            "to run this sample."
        )
        return

    token_provider = AzureIdentityTokenProvider(DefaultAzureCredential())
    try:
        async with ElfsquaddataClient(
            CONNECTION_RUNTIME_URL,
            token_provider,
        ) as client:
            entities = await client.get_entities_async(
                entity_name=ENTITY_NAME,
                top=10,
            )
            print(f"Entities: {entities}")
    except ConnectorException as ex:
        print(f"Connector error: {ex}")


if __name__ == "__main__":
    asyncio.run(main())
