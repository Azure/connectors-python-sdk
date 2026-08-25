# Copyright (c) Microsoft Corporation. All rights reserved.

"""Zoho Sign connector SDK sample."""

import asyncio
import os

from azure.identity.aio import DefaultAzureCredential

from azure.connectors import ConnectorException
from azure.connectors.zohosign import ZohosignClient


CONNECTION_RUNTIME_URL = os.environ.get("ZOHOSIGN_CONNECTION_URL", "")
REQUEST_ID = os.environ.get("ZOHOSIGN_REQUEST_ID", "")


async def list_templates() -> None:
    """List available Zoho Sign templates."""
    credential = DefaultAzureCredential()
    async with ZohosignClient(CONNECTION_RUNTIME_URL, credential) as client:
        templates = await client.get_templates_async()
        print(f"Templates: {templates}")


async def get_document() -> None:
    """Get a Zoho Sign document request."""
    if not REQUEST_ID:
        print("Set ZOHOSIGN_REQUEST_ID to retrieve a document request.")
        return

    credential = DefaultAzureCredential()
    async with ZohosignClient(CONNECTION_RUNTIME_URL, credential) as client:
        document = await client.get_document_async(request_id=int(REQUEST_ID))
        print(f"Document: {document}")


async def main() -> None:
    """Run the Zoho Sign examples."""
    if not CONNECTION_RUNTIME_URL:
        print("Error: ZOHOSIGN_CONNECTION_URL environment variable not set.")
        return

    try:
        await list_templates()
        await get_document()
    except ConnectorException as ex:
        print(f"Connector error: {ex}")


if __name__ == "__main__":
    asyncio.run(main())
