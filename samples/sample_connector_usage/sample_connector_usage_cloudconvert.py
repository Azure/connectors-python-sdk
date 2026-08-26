"""CloudConvert connector SDK sample."""

import asyncio
import os

from azure.identity.aio import DefaultAzureCredential

from azure.connectors import AzureIdentityTokenProvider, ConnectorException
from azure.connectors.cloudconvert import CloudconvertClient


CONNECTION_RUNTIME_URL = os.environ.get("CLOUDCONVERT_CONNECTION_URL", "")


async def main() -> None:
    """Get CloudConvert conversion options."""
    if not CONNECTION_RUNTIME_URL:
        print("Set CLOUDCONVERT_CONNECTION_URL to run this sample.")
        return

    token_provider = AzureIdentityTokenProvider(DefaultAzureCredential())
    try:
        async with CloudconvertClient(CONNECTION_RUNTIME_URL, token_provider) as client:
            options = await client.get_convert_options_async()
            print(f"Conversion options: {options}")
    except ConnectorException as ex:
        print(f"Connector error: {ex}")


if __name__ == "__main__":
    asyncio.run(main())
