# Copyright (c) Microsoft Corporation. All rights reserved.

"""List WordPress sites with the generated connector client."""

import asyncio
import os

from azure.identity.aio import DefaultAzureCredential

from azure.connectors import AzureIdentityTokenProvider, ConnectorException
from azure.connectors.wordpress import WordpressClient


CONNECTION_URL = os.environ.get("WORDPRESS_CONNECTION_URL", "")


async def main() -> None:
    """List sites through an existing Connector Namespace connection."""
    if not CONNECTION_URL:
        raise ValueError("Environment variable 'WORDPRESS_CONNECTION_URL' is required.")

    async with DefaultAzureCredential() as credential:
        token_provider = AzureIdentityTokenProvider(credential)
        async with WordpressClient(CONNECTION_URL, token_provider=token_provider) as client:
            try:
                print(await client.list_sites_async())
            except ConnectorException as error:
                print(f"WordPress request failed: {error}")


if __name__ == "__main__":
    asyncio.run(main())
