# Copyright (c) Microsoft Corporation. All rights reserved.

"""List monday.com workspaces with the generated connector client."""

import asyncio
import os

from azure.identity.aio import DefaultAzureCredential

from azure.connectors import AzureIdentityTokenProvider, ConnectorException
from azure.connectors.monday import MondayClient


CONNECTION_URL = os.environ.get("MONDAY_CONNECTION_URL", "")


async def main() -> None:
    """List workspaces through an existing Connector Namespace connection."""
    if not CONNECTION_URL:
        raise ValueError("Environment variable 'MONDAY_CONNECTION_URL' is required.")

    async with DefaultAzureCredential() as credential:
        token_provider = AzureIdentityTokenProvider(credential)
        async with MondayClient(CONNECTION_URL, token_provider=token_provider) as client:
            try:
                print(await client.get_workspaces_async())
            except ConnectorException as error:
                print(f"monday.com request failed: {error}")


if __name__ == "__main__":
    asyncio.run(main())
