"""
Webex Connector SDK Sample

This sample demonstrates how to use the Webex connector SDK.

Prerequisites:
1. Azure subscription with a Webex connection
2. Webex connection in Connector Namespaces
3. Connection runtime URL from Azure Portal

Installation:
    pip install azure-connectors

Usage:
    Set environment variable:
    $env:WEBEX_CONNECTION_URL = "https://[region].azure-apihub.net/apim/webex/[id]"

    python sample_connector_usage_webex.py
"""

import asyncio
import os

from azure.identity.aio import DefaultAzureCredential

from azure.connectors import ConnectorException
from azure.connectors.webex import (
    CreateSpaceInput,
    SendMessageInput,
    WebexClient,
)


# Connection runtime URL format:
# https://[region].azure-apihub.net/apim/webex/[connection-id]
CONNECTION_RUNTIME_URL = os.environ.get("WEBEX_CONNECTION_URL", "")


async def example_1_send_message() -> None:
    """Example 1: Send a message to a space."""
    print("\n=== Example 1: Send Message ===")

    credential = DefaultAzureCredential()
    async with WebexClient(CONNECTION_RUNTIME_URL, credential) as client:
        result = await client.send_message_async(
            input=SendMessageInput(
                room_id="ROOM_ID",
                text="Hello from the Webex connector SDK.",
            ),
        )
        print(f"Send result: {result}")


async def example_2_get_spaces() -> None:
    """Example 2: List spaces."""
    print("\n=== Example 2: Get Spaces ===")

    credential = DefaultAzureCredential()
    async with WebexClient(CONNECTION_RUNTIME_URL, credential) as client:
        spaces = await client.get_spaces_async()
        print(f"Spaces: {spaces}")


async def example_3_create_space() -> None:
    """Example 3: Create a space."""
    print("\n=== Example 3: Create Space ===")

    credential = DefaultAzureCredential()
    async with WebexClient(CONNECTION_RUNTIME_URL, credential) as client:
        space = await client.create_space_async(
            input=CreateSpaceInput(title="My New Space"),
        )
        print(f"Created space: {space}")


async def example_4_get_my_own_details() -> None:
    """Example 4: Get details about the authenticated user."""
    print("\n=== Example 4: Get My Own Details ===")

    credential = DefaultAzureCredential()
    async with WebexClient(CONNECTION_RUNTIME_URL, credential) as client:
        me = await client.get_my_own_details_async()
        print(f"My details: {me}")


async def main() -> None:
    """Run Webex connector examples."""
    if not CONNECTION_RUNTIME_URL:
        print("Error: WEBEX_CONNECTION_URL environment variable not set.")
        print("Set it to your connection runtime URL from Azure Portal.")
        return

    print("Webex Connector SDK - Sample Usage")
    print("=" * 50)

    try:
        # Uncomment to send a message, list/create spaces, or get your details.
        # await example_1_send_message()
        # await example_2_get_spaces()
        # await example_3_create_space()
        # await example_4_get_my_own_details()
        print("Set the example calls in main() to run against your instance.")

    except ConnectorException as ex:
        print(f"Connector error: {ex}")
    except Exception as ex:
        print(f"Unexpected error: {ex}")


if __name__ == "__main__":
    asyncio.run(main())
