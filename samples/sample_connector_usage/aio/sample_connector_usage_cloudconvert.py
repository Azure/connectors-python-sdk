"""CloudConvert sample for the Azure Connectors Python SDK."""

import asyncio
import os

from azure.identity.aio import DefaultAzureCredential

from azure.connectors import ConnectorException
from azure.connectors.aio.cloudconvert import CloudconvertClient


CONNECTION_RUNTIME_URL = os.environ.get("CLOUDCONVERT_CONNECTION_URL", "")


async def main() -> None:
    """Get CloudConvert conversion options."""
    if not CONNECTION_RUNTIME_URL:
        print("Set CLOUDCONVERT_CONNECTION_URL to run this sample.")
        return

    async with DefaultAzureCredential() as credential:
        try:
            async with CloudconvertClient(CONNECTION_RUNTIME_URL, credential) as client:
                options = await client.get_convert_options()
                print(f"Conversion options: {options}")
        except ConnectorException as ex:
            print(f"Connector error: {ex}")


if __name__ == "__main__":
    asyncio.run(main())
