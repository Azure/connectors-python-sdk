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
import os

from azure.identity import DefaultAzureCredential

from azure.connectors import ConnectorException
from azure.connectors.campfire import CampfireClient


# Connection runtime URL format:
# https://[region].azure-apihub.net/apim/campfire/[connection-id]
CONNECTION_RUNTIME_URL = os.environ.get("CAMPFIRE_CONNECTION_URL", "")


def example_1_list_accounts() -> None:
    """Example 1: List accounts this user has access to."""
    print("\n=== Example 1: List Accounts ===")

    with DefaultAzureCredential() as credential:
        with CampfireClient(CONNECTION_RUNTIME_URL, credential) as client:
            accounts = client.list_accounts()
            print(f"Accounts: {accounts}")


def example_2_list_rooms() -> None:
    """Example 2: List the rooms in an account."""
    print("\n=== Example 2: List Rooms ===")

    with DefaultAzureCredential() as credential:
        with CampfireClient(CONNECTION_RUNTIME_URL, credential) as client:
            rooms = client.list_rooms(account="ACCOUNT_ID")
            print(f"Rooms: {rooms}")


def example_3_create_message() -> None:
    """Example 3: Send a message to a room."""
    print("\n=== Example 3: Create Message ===")

    with DefaultAzureCredential() as credential:
        with CampfireClient(CONNECTION_RUNTIME_URL, credential) as client:
            result = client.create_message(
                room_id="ROOM_ID",
                account="ACCOUNT_ID",
                message="Hello from the Campfire connector SDK.",
            )
            print(f"Create message result: {result}")


def example_4_get_user() -> None:
    """Example 4: Get information about a user by ID."""
    print("\n=== Example 4: Get User ===")

    with DefaultAzureCredential() as credential:
        with CampfireClient(CONNECTION_RUNTIME_URL, credential) as client:
            user = client.get_user(user_id=12345, account="ACCOUNT_ID")
            print(f"User: {user}")


def main() -> None:
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
    main()
