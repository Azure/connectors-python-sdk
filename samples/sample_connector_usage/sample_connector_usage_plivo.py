"""Plivo connector SDK sample."""

import asyncio
import os

from azure.identity.aio import DefaultAzureCredential

from azure.connectors import ConnectorException
from azure.connectors.plivo import PlivoClient, SMS


CONNECTION_RUNTIME_URL = os.environ.get("PLIVO_CONNECTION_URL", "")


async def send_sms() -> None:
    """Send an SMS message."""
    credential = DefaultAzureCredential()
    async with PlivoClient(CONNECTION_RUNTIME_URL, credential) as client:
        result = await client.send_sms_async(
            input=SMS(
                src="15550000000",
                dst="15551111111",
                text="Hello from the Azure Connectors Python SDK.",
            ),
            auth_id="PLIVO_AUTH_ID",
        )
        print(f"Send result: {result}")


async def list_messages() -> None:
    """List messages for an account."""
    credential = DefaultAzureCredential()
    async with PlivoClient(CONNECTION_RUNTIME_URL, credential) as client:
        messages = await client.list_messages_async(auth_id="PLIVO_AUTH_ID")
        print(f"Messages: {messages}")


async def main() -> None:
    """Run Plivo connector examples."""
    if not CONNECTION_RUNTIME_URL:
        print("Set PLIVO_CONNECTION_URL to run this sample.")
        return

    try:
        await list_messages()
        await send_sms()
    except ConnectorException as ex:
        print(f"Connector error: {ex}")


if __name__ == "__main__":
    asyncio.run(main())