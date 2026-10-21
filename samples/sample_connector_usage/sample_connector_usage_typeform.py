"""Typeform sample for the Azure Connectors Python SDK."""

import asyncio
import os

from azure.identity.aio import DefaultAzureCredential

from azure.connectors import ConnectorException
from azure.connectors.typeform import TypeformClient


CONNECTION_RUNTIME_URL = os.environ.get("TYPEFORM_CONNECTION_URL", "")


async def main() -> None:
    """List Typeform forms."""
    if not CONNECTION_RUNTIME_URL:
        print("Set TYPEFORM_CONNECTION_URL to run this sample.")
        return

    async with DefaultAzureCredential() as credential:
        try:
            async with TypeformClient(CONNECTION_RUNTIME_URL, credential) as client:
                forms = [form async for form in client.list_forms()]
                print(f"Forms: {forms}")
        except ConnectorException as ex:
            print(f"Connector error: {ex}")


if __name__ == "__main__":
    asyncio.run(main())
