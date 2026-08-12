# Copyright (c) Microsoft Corporation. All rights reserved.

"""Search Starmind questions with the generated connector client."""

import asyncio
import os

from azure.identity.aio import DefaultAzureCredential

from azure.connectors import AzureIdentityTokenProvider, ConnectorException
from azure.connectors.starmind import StarmindClient


CONNECTION_URL = os.environ.get("STARMIND_CONNECTION_URL", "")


async def main() -> None:
    """Search questions through an existing Connector Namespace connection."""
    if not CONNECTION_URL:
        raise ValueError("Environment variable 'STARMIND_CONNECTION_URL' is required.")

    async with DefaultAzureCredential() as credential:
        token_provider = AzureIdentityTokenProvider(credential)
        async with StarmindClient(CONNECTION_URL, token_provider=token_provider) as client:
            try:
                print(await client.find_questions_async(limit="10"))
            except ConnectorException as error:
                print(f"Starmind request failed: {error}")


if __name__ == "__main__":
    asyncio.run(main())
