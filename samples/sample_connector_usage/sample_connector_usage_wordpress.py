"""WordPress connector SDK sample."""

import asyncio
import os

from azure.identity.aio import DefaultAzureCredential

from azure.connectors import ConnectorException
from azure.connectors.wordpress import CreatePostModel, WordpressClient


CONNECTION_RUNTIME_URL = os.environ.get("WORDPRESS_CONNECTION_URL", "")


async def list_sites() -> None:
    """List WordPress sites available to the connection."""
    credential = DefaultAzureCredential()
    async with WordpressClient(CONNECTION_RUNTIME_URL, credential) as client:
        sites = await client.list_sites_async()
        print(f"Sites: {sites}")


async def create_post() -> None:
    """Create a draft WordPress post."""
    credential = DefaultAzureCredential()
    async with WordpressClient(CONNECTION_RUNTIME_URL, credential) as client:
        post = await client.create_async(
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
