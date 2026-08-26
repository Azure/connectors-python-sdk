"""Replicon connector SDK sample."""

import asyncio
import os

from azure.identity.aio import DefaultAzureCredential

from azure.connectors import AzureIdentityTokenProvider, ConnectorException
from azure.connectors.replicon import RepliconClient


CONNECTION_RUNTIME_URL = os.environ.get("REPLICON_CONNECTION_URL", "")


async def main() -> None:
    """Get Replicon tenant endpoint details."""
    if not CONNECTION_RUNTIME_URL:
        print("Set REPLICON_CONNECTION_URL to run this sample.")
        return

    token_provider = AzureIdentityTokenProvider(DefaultAzureCredential())
    try:
        async with RepliconClient(CONNECTION_RUNTIME_URL, token_provider) as client:
            endpoint = await client.get_my_tenant_endpoint_details_async()
            print(f"Tenant endpoint: {endpoint}")
    except ConnectorException as ex:
        print(f"Connector error: {ex}")


if __name__ == "__main__":
    asyncio.run(main())
