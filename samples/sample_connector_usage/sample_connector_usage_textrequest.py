"""
TextRequest Connector SDK Sample

This sample demonstrates how to use the TextRequest connector SDK.

Prerequisites:
1. Azure subscription with a TextRequest connection
2. TextRequest connection in Connector Namespaces
3. Connection runtime URL from Azure Portal

Installation:
    pip install azure-connectors

Usage:
    Set environment variable:
    $env:TEXTREQUEST_CONNECTION_URL = "https://[region].azure-apihub.net/apim/textrequest/[id]"

    python sample_connector_usage_textrequest.py
"""
import os

from azure.identity import DefaultAzureCredential

from azure.connectors import ConnectorException
from azure.connectors.textrequest import (
    CreateContactInput,
    SendMessageByPhoneNumberInput,
    TextrequestClient,
)


# Connection runtime URL format:
# https://[region].azure-apihub.net/apim/textrequest/[connection-id]
CONNECTION_RUNTIME_URL = os.environ.get("TEXTREQUEST_CONNECTION_URL", "")

# The id of the dashboard to make calls on.
DASHBOARD_ID = int(os.environ.get("TEXTREQUEST_DASHBOARD_ID", "0"))


def example_1_send_message() -> None:
    """Example 1: Send a message to a contact by phone number."""
    print("\n=== Example 1: Send Message ===")

    with DefaultAzureCredential() as credential:
        with TextrequestClient(CONNECTION_RUNTIME_URL, credential) as client:
            result = client.send_message_by_phone_number(
                input=SendMessageByPhoneNumberInput(
                    body="Hello from the TextRequest connector SDK.",
                    sender_name="Support Team",
                ),
                dashboard_id=DASHBOARD_ID,
                phone_number="+15553334444",
            )
            print(f"Send result: {result}")


def example_2_get_conversations() -> None:
    """Example 2: List all conversations for the dashboard."""
    print("\n=== Example 2: Get Conversations ===")

    with DefaultAzureCredential() as credential:
        with TextrequestClient(CONNECTION_RUNTIME_URL, credential) as client:
            conversations = client.get_conversations(
                dashboard_id=DASHBOARD_ID,
                page=1,
                page_size=20,
            )
            print(f"Conversations: {conversations}")


def example_3_create_contact() -> None:
    """Example 3: Create or update a contact."""
    print("\n=== Example 3: Create Contact ===")

    with DefaultAzureCredential() as credential:
        with TextrequestClient(CONNECTION_RUNTIME_URL, credential) as client:
            result = client.create_contact(
                input=CreateContactInput(
                    first_name="Ada",
                    last_name="Lovelace",
                    display_name="Ada Lovelace",
                ),
                dashboard_id=DASHBOARD_ID,
                phone_number="+15553334444",
            )
            print(f"Contact result: {result}")


def example_4_get_dashboards() -> None:
    """Example 4: Get all dashboards in the account."""
    print("\n=== Example 4: Get Dashboards ===")

    with DefaultAzureCredential() as credential:
        with TextrequestClient(CONNECTION_RUNTIME_URL, credential) as client:
            dashboards = client.get_dashboards(page=1, page_size=20)
            print(f"Dashboards: {dashboards}")


def main() -> None:
    """Run TextRequest connector examples."""
    if not CONNECTION_RUNTIME_URL:
        print("Error: TEXTREQUEST_CONNECTION_URL environment variable not set.")
        print("Set it to your connection runtime URL from Azure Portal.")
        return

    print("TextRequest Connector SDK - Sample Usage")
    print("=" * 50)

    try:
        # Uncomment to send a message, list conversations, create a contact,
        # or list dashboards.
        # await example_1_send_message()
        # await example_2_get_conversations()
        # await example_3_create_contact()
        # await example_4_get_dashboards()
        print("Set the example calls in main() to run against your instance.")

    except ConnectorException as ex:
        print(f"Connector error: {ex}")
    except Exception as ex:
        print(f"Unexpected error: {ex}")


if __name__ == "__main__":
    main()
