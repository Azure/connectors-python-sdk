"""
Plivo Connector SDK Sample

This sample demonstrates how to use the Plivo connector SDK.

Prerequisites:
1. Azure subscription with a Plivo connection
2. Plivo connection in Connector Namespaces
3. Connection runtime URL from Azure Portal

Installation:
    pip install azure-connectors

Usage:
    Set environment variable:
    $env:PLIVO_CONNECTION_URL = "https://[region].azure-apihub.net/apim/plivo/[id]"

    python sample_connector_usage_plivo.py
"""

import asyncio
import os

from azure.identity.aio import DefaultAzureCredential

from azure.connectors import ConnectorException
from azure.connectors.plivo import (
    Call,
    PlivoClient,
    SMS,
)


# Connection runtime URL format:
# https://[region].azure-apihub.net/apim/plivo/[connection-id]
CONNECTION_RUNTIME_URL = os.environ.get("PLIVO_CONNECTION_URL", "")

# Your Plivo Auth ID.
AUTH_ID = os.environ.get("PLIVO_AUTH_ID", "")


async def example_1_send_sms() -> None:
    """Example 1: Send an SMS message."""
    print("\n=== Example 1: Send SMS ===")

    credential = DefaultAzureCredential()
    async with PlivoClient(CONNECTION_RUNTIME_URL, credential) as client:
        result = await client.send_s_m_s_async(
            input=SMS(
                src="+15551112222",
                dst="+15553334444",
                text="Hello from the Plivo connector SDK.",
            ),
            auth_id=AUTH_ID,
        )
        print(f"Send result: {result}")


async def example_2_list_messages() -> None:
    """Example 2: List all messages."""
    print("\n=== Example 2: List Messages ===")

    credential = DefaultAzureCredential()
    async with PlivoClient(CONNECTION_RUNTIME_URL, credential) as client:
        messages = await client.list_messages_async(auth_id=AUTH_ID)
        print(f"Messages: {messages}")


async def example_3_make_call() -> None:
    """Example 3: Make a call."""
    print("\n=== Example 3: Make a Call ===")

    credential = DefaultAzureCredential()
    async with PlivoClient(CONNECTION_RUNTIME_URL, credential) as client:
        result = await client.make_call_async(
            input=Call(
                from_="+15551112222",
                to="+15553334444",
                answer_url="https://example.com/answer",
                answer_method="GET",
            ),
            auth_id=AUTH_ID,
        )
        print(f"Call result: {result}")


async def example_4_get_message() -> None:
    """Example 4: Get a message by ID."""
    print("\n=== Example 4: Get Message ===")

    credential = DefaultAzureCredential()
    async with PlivoClient(CONNECTION_RUNTIME_URL, credential) as client:
        message = await client.get_message_async(
            auth_id=AUTH_ID,
            message_uuid="00000000-0000-0000-0000-000000000000",
        )
        print(f"Message: {message}")


async def main() -> None:
    """Run Plivo connector examples."""
    if not CONNECTION_RUNTIME_URL:
        print("Error: PLIVO_CONNECTION_URL environment variable not set.")
        print("Set it to your connection runtime URL from Azure Portal.")
        return

    print("Plivo Connector SDK - Sample Usage")
    print("=" * 50)

    try:
        # Uncomment to send an SMS, list messages, make a call, or get a message.
        # await example_1_send_sms()
        # await example_2_list_messages()
        # await example_3_make_call()
        # await example_4_get_message()
        print("Set the example calls in main() to run against your instance.")

    except ConnectorException as ex:
        print(f"Connector error: {ex}")
    except Exception as ex:
        print(f"Unexpected error: {ex}")


if __name__ == "__main__":
    asyncio.run(main())
