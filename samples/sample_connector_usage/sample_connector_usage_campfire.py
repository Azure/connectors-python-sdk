"""
Campfire Connector SDK Sample

This sample demonstrates how to use the Campfire connector SDK.

Prerequisites:
1. Azure subscription with a Campfire connection
2. Campfire connection in Connector Namespaces
3. Connection runtime URL from Azure Portal

Installation:
    pip install azure-connectors

Usage:
    Set environment variable:
    $env:CAMPFIRE_CONNECTION_URL = "https://[region].azure-apihub.net/apim/campfire/[id]"

    python sample_connector_usage_campfire.py
"""

import asyncio
import os

from azure.identity.aio import DefaultAzureCredential

from azure.connectors import ConnectorException
from azure.connectors.campfire import CampfireClient


# Connection runtime URL format:
# https://[region].azure-apihub.net/apim/campfire/[connection-id]
CONNECTION_RUNTIME_URL = os.environ.get("CAMPFIRE_CONNECTION_URL", "")


async def example_1_list_accounts() -> None:
    """Example 1: List accounts this user has access to."""
    print("\n=== Example 1: List Accounts ===")

    credential = DefaultAzureCredential()
    async with CampfireClient(CONNECTION_RUNTIME_URL, credential) as client:
        accounts = await client.list_accounts_async()
        print(f"Accounts: {accounts}")


async def example_2_list_rooms() -> None:
    """Example 2: List the rooms in an account."""
    print("\n=== Example 2: List Rooms ===")

    credential = DefaultAzureCredential()
    async with CampfireClient(CONNECTION_RUNTIME_URL, credential) as client:
        rooms = await client.list_rooms_async(account="ACCOUNT_ID")
        print(f"Rooms: {rooms}")


async def example_3_create_message() -> None:
    """Example 3: Send a message to a room."""
    print("\n=== Example 3: Create Message ===")

    credential = DefaultAzureCredential()
    async with CampfireClient(CONNECTION_RUNTIME_URL, credential) as client:
        result = await client.create_message_async(
            room_id="ROOM_ID",
            account="ACCOUNT_ID",
            message="Hello from the Campfire connector SDK.",
        )
        print(f"Create message result: {result}")


async def example_4_get_user() -> None:
    """Example 4: Get information about a user by ID."""
    print("\n=== Example 4: Get User ===")

    credential = DefaultAzureCredential()
    async with CampfireClient(CONNECTION_RUNTIME_URL, credential) as client:
        user = await client.get_user_async(user_id="USER_ID", account="ACCOUNT_ID")
        print(f"User: {user}")


async def main() -> None:
    """Run Campfire connector examples."""
    if not CONNECTION_RUNTIME_URL:
        print("Error: CAMPFIRE_CONNECTION_URL environment variable not set.")
        print("Set it to your connection runtime URL from Azure Portal.")
        return

    print("Campfire Connector SDK - Sample Usage")
    print("=" * 50)

    try:
        # Uncomment to list accounts/rooms, send a message, or get a user.
        # await example_1_list_accounts()
        # await example_2_list_rooms()
        # await example_3_create_message()
        # await example_4_get_user()
        print("Set the example calls in main() to run against your instance.")

    except ConnectorException as ex:
        print(f"Connector error: {ex}")
    except Exception as ex:
        print(f"Unexpected error: {ex}")


if __name__ == "__main__":
    asyncio.run(main())
