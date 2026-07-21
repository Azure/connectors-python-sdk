"""
ClickSend SMS Connector SDK Sample

This sample demonstrates how to use the ClickSend SMS connector SDK.

Prerequisites:
1. Azure subscription with a ClickSend SMS connection
2. ClickSend SMS connection in Connector Namespaces
3. Connection runtime URL from Azure Portal

Installation:
    pip install azure-connectors

Usage:
    Set environment variable:
    $env:CLICKSENDSMS_CONNECTION_URL = "https://[region].azure-apihub.net/apim/clicksendsms/[id]"

    python sample_connector_usage_clicksendsms.py
"""

import asyncio
import os

from azure.identity.aio import DefaultAzureCredential

from azure.connectors import ConnectorException
from azure.connectors.clicksendsms import (
    ClicksendsmsClient,
    CreateListInput,
    SmsSendInput,
)


# Connection runtime URL format:
# https://[region].azure-apihub.net/apim/clicksendsms/[connection-id]
CONNECTION_RUNTIME_URL = os.environ.get("CLICKSENDSMS_CONNECTION_URL", "")


async def example_1_send_sms() -> None:
    """Example 1: Send an SMS message."""
    print("\n=== Example 1: Send SMS ===")

    credential = DefaultAzureCredential()
    async with ClicksendsmsClient(CONNECTION_RUNTIME_URL, credential) as client:
        result = await client.sms_send_async(
            input=SmsSendInput(
                messages=[
                    {
                        "to": "+61411111111",
                        "body": "Hello from the ClickSend SMS connector SDK.",
                    }
                ],
            ),
        )
        print(f"Send result: {result}")


async def example_2_get_contact_lists() -> None:
    """Example 2: Get contact lists."""
    print("\n=== Example 2: Get Contact Lists ===")

    credential = DefaultAzureCredential()
    async with ClicksendsmsClient(CONNECTION_RUNTIME_URL, credential) as client:
        lists = await client.get_contact_lists_async(page="1", limit="10")
        print(f"Contact lists: {lists}")


async def example_3_create_list() -> None:
    """Example 3: Create a new contact list."""
    print("\n=== Example 3: Create Contact List ===")

    credential = DefaultAzureCredential()
    async with ClicksendsmsClient(CONNECTION_RUNTIME_URL, credential) as client:
        result = await client.create_list_async(
            input=CreateListInput(list_name="My New List"),
        )
        print(f"Created list: {result}")


async def example_4_search_contact_lists() -> None:
    """Example 4: Search contact lists."""
    print("\n=== Example 4: Search Contact Lists ===")

    credential = DefaultAzureCredential()
    async with ClicksendsmsClient(CONNECTION_RUNTIME_URL, credential) as client:
        results = await client.search_contact_list_async(q="friends")
        print(f"Search results: {results}")


async def main() -> None:
    """Run ClickSend SMS connector examples."""
    if not CONNECTION_RUNTIME_URL:
        print("Error: CLICKSENDSMS_CONNECTION_URL environment variable not set.")
        print("Set it to your connection runtime URL from Azure Portal.")
        return

    print("ClickSend SMS Connector SDK - Sample Usage")
    print("=" * 50)

    try:
        # Uncomment to send an SMS, list/create/search contact lists.
        # await example_1_send_sms()
        # await example_2_get_contact_lists()
        # await example_3_create_list()
        # await example_4_search_contact_lists()
        print("Set the example calls in main() to run against your instance.")

    except ConnectorException as ex:
        print(f"Connector error: {ex}")
    except Exception as ex:
        print(f"Unexpected error: {ex}")


if __name__ == "__main__":
    asyncio.run(main())
