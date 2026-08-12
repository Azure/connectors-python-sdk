# Copyright (c) Microsoft Corporation. All rights reserved.

"""Call Etsy's connectivity operation with the generated connector client."""

import asyncio
import os

from azure.identity.aio import DefaultAzureCredential

from azure.connectors import AzureIdentityTokenProvider, ConnectorException
from azure.connectors.etsy import EtsyClient


CONNECTION_URL = os.environ.get("ETSY_CONNECTION_URL", "")


async def main() -> None:
    """Ping Etsy through an existing Connector Namespace connection."""
    if not CONNECTION_URL:
        raise ValueError("Environment variable 'ETSY_CONNECTION_URL' is required.")

    async with DefaultAzureCredential() as credential:
        token_provider = AzureIdentityTokenProvider(credential)
        async with EtsyClient(CONNECTION_URL, token_provider=token_provider) as client:
            try:
                print(await client.ping_async())
            except ConnectorException as error:
                print(f"Etsy request failed: {error}")


if __name__ == "__main__":
    asyncio.run(main())
