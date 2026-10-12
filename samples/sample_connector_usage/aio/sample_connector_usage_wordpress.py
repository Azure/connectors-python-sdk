"""WordPress sample for the Azure Connectors Python SDK."""

import asyncio
import os

from azure.identity.aio import DefaultAzureCredential

from azure.connectors import ConnectorException
from azure.connectors.aio.wordpress import WordpressClient
from azure.connectors.wordpress import CreatePostModel


CONNECTION_RUNTIME_URL = os.environ.get("WORDPRESS_CONNECTION_URL", "")


async def list_sites() -> None:
    """List WordPress sites available to the connection."""
    async with DefaultAzureCredential() as credential:
        async with WordpressClient(CONNECTION_RUNTIME_URL, credential) as client:
            sites = await client.list_sites()
            print(f"Sites: {sites}")


async def create_post() -> None:
    """Create a draft WordPress post."""
    async with DefaultAzureCredential() as credential:
        async with WordpressClient(CONNECTION_RUNTIME_URL, credential) as client:
            post = await client.create(
                input=CreatePostModel(
                    title="Generated connector sample",
                    content="Created with the Azure Connectors Python SDK.",
                    status="draft",
                ),
                site_id="SITE_ID",
            )
            print(f"Created post: {post}")


async def main() -> None:
    """Run WordPress connector examples."""
    if not CONNECTION_RUNTIME_URL:
        print("Set WORDPRESS_CONNECTION_URL to run this sample.")
        return

    try:
        await list_sites()
        await create_post()
    except ConnectorException as ex:
        print(f"Connector error: {ex}")


if __name__ == "__main__":
    asyncio.run(main())
