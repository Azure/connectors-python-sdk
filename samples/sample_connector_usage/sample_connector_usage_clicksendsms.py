"""
ClickSend SMS sample for the Azure Connectors Python SDK

This sample demonstrates how to use the ClickSend SMS client from the Azure Connectors Python SDK.

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
import os

from azure.identity import DefaultAzureCredential

from azure.connectors import ConnectorException
from azure.connectors.clicksendsms import (
    ClicksendsmsClient,
    CreateListInput,
    SmsSendInput,
)


# Connection runtime URL format:
# https://[region].azure-apihub.net/apim/clicksendsms/[connection-id]
CONNECTION_RUNTIME_URL = os.environ.get("CLICKSENDSMS_CONNECTION_URL", "")


def example_1_send_sms() -> None:
    """Example 1: Send an SMS message."""
    print("\n=== Example 1: Send SMS ===")

    with DefaultAzureCredential() as credential:
        with ClicksendsmsClient(CONNECTION_RUNTIME_URL, credential) as client:
            result = client.sms_send(
                input=SmsSendInput(
                    messages=[
                        {
                            "to": "+61411111111",
                            "body": "Hello from the ClickSend SMS client in the Azure Connectors Python SDK.",
                        }
                    ],
                ),
            )
            print(f"Send result: {result}")


def example_2_get_contact_lists() -> None:
    """Example 2: Get contact lists."""
    print("\n=== Example 2: Get Contact Lists ===")

    with DefaultAzureCredential() as credential:
        with ClicksendsmsClient(CONNECTION_RUNTIME_URL, credential) as client:
            lists = client.get_contact_lists(page=1, limit=10)
            print(f"Contact lists: {lists}")


def example_3_create_list() -> None:
    """Example 3: Create a new contact list."""
    print("\n=== Example 3: Create Contact List ===")

    with DefaultAzureCredential() as credential:
        with ClicksendsmsClient(CONNECTION_RUNTIME_URL, credential) as client:
            result = client.create_list(
                input=CreateListInput(list_name="My New List"),
            )
            print(f"Created list: {result}")


def example_4_search_contact_lists() -> None:
    """Example 4: Search contact lists."""
    print("\n=== Example 4: Search Contact Lists ===")

    with DefaultAzureCredential() as credential:
        with ClicksendsmsClient(CONNECTION_RUNTIME_URL, credential) as client:
            results = client.search_contact_list(q="friends")
            print(f"Search results: {results}")


def main() -> None:
    """Run ClickSend SMS connector examples."""
    if not CONNECTION_RUNTIME_URL:
        print("Error: CLICKSENDSMS_CONNECTION_URL environment variable not set.")
        print("Set it to your connection runtime URL from Azure Portal.")
        return

    print("ClickSend SMS sample usage for the Azure Connectors Python SDK")
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
    main()
