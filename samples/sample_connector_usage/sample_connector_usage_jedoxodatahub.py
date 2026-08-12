# Copyright (c) Microsoft Corporation. All rights reserved.

"""List Jedox databases with the generated connector client."""

import asyncio
import os

from azure.identity.aio import DefaultAzureCredential

from azure.connectors import AzureIdentityTokenProvider, ConnectorException
from azure.connectors.jedoxodatahub import JedoxodatahubClient


CONNECTION_URL = os.environ.get("JEDOXODATAHUB_CONNECTION_URL", "")


async def main() -> None:
    """List databases through an existing Connector Namespace connection."""
    if not CONNECTION_URL:
        raise ValueError("Environment variable 'JEDOXODATAHUB_CONNECTION_URL' is required.")

    async with DefaultAzureCredential() as credential:
        token_provider = AzureIdentityTokenProvider(credential)
        async with JedoxodatahubClient(
            CONNECTION_URL,
            token_provider=token_provider,
        ) as client:
            try:
                print(await client.databases_async())
            except ConnectorException as error:
                print(f"Jedox OData Hub request failed: {error}")


if __name__ == "__main__":
    asyncio.run(main())
