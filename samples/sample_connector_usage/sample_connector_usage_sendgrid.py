"""
SendGrid sample for the Azure Connectors Python SDK

This sample demonstrates how to use the SendGrid client from the Azure Connectors Python SDK.

Prerequisites:
1. Azure subscription with a SendGrid connection
2. SendGrid connection in Connector Namespaces
3. Connection runtime URL from Azure Portal

Installation:
    pip install azure-connectors

Usage:
    Set environment variable:
    $env:SENDGRID_CONNECTION_URL = "https://[region].azure-apihub.net/apim/sendgrid/[id]"

    python sample_connector_usage_sendgrid.py
"""
import os

from azure.identity import DefaultAzureCredential

from azure.connectors import ConnectorException
from azure.connectors.sendgrid import (
    EmailRequest,
    SendgridClient,
)


# Connection runtime URL format:
# https://[region].azure-apihub.net/apim/sendgrid/[connection-id]
CONNECTION_RUNTIME_URL = os.environ.get("SENDGRID_CONNECTION_URL", "")


def example_1_send_email() -> None:
    """Example 1: Send an email."""
    print("\n=== Example 1: Send Email ===")

    with DefaultAzureCredential() as credential:
        with SendgridClient(CONNECTION_RUNTIME_URL, credential) as client:
            result = client.send_email(
                input=EmailRequest(
                    from_="sender@example.com",
                    to="recipient@example.com",
                    subject="Hello from the SDK sample",
                    text="This message was sent via the SendGrid client from the Azure Connectors Python SDK.",
                ),
            )
            print(f"Send result: {result}")


def example_2_list_recipient_lists() -> None:
    """Example 2: List recipient lists."""
    print("\n=== Example 2: List Recipient Lists ===")

    with DefaultAzureCredential() as credential:
        with SendgridClient(CONNECTION_RUNTIME_URL, credential) as client:
            lists = client.list_recipient_lists()
            print(f"Recipient lists: {lists}")


def example_3_list_recipients() -> None:
    """Example 3: List recipients."""
    print("\n=== Example 3: List Recipients ===")

    with DefaultAzureCredential() as credential:
        with SendgridClient(CONNECTION_RUNTIME_URL, credential) as client:
            recipients = client.list_recipients()
            print(f"Recipients: {recipients}")


def example_4_get_bounce() -> None:
    """Example 4: Get a bounce record for an email address."""
    print("\n=== Example 4: Get Bounce ===")

    with DefaultAzureCredential() as credential:
        with SendgridClient(CONNECTION_RUNTIME_URL, credential) as client:
            bounce = client.get_bounce(email="recipient@example.com")
            print(f"Bounce: {bounce}")


def main() -> None:
    """Run SendGrid connector examples."""
    if not CONNECTION_RUNTIME_URL:
        print("Error: SENDGRID_CONNECTION_URL environment variable not set.")
        print("Set it to your connection runtime URL from Azure Portal.")
        return

    print("SendGrid sample usage for the Azure Connectors Python SDK")
    print("=" * 50)

    try:
        # Uncomment to send email, list recipient lists/recipients, or get bounces.
        # await example_1_send_email()
        # await example_2_list_recipient_lists()
        # await example_3_list_recipients()
        # await example_4_get_bounce()
        print("Set the example calls in main() to run against your instance.")

    except ConnectorException as ex:
        print(f"Connector error: {ex}")
    except Exception as ex:
        print(f"Unexpected error: {ex}")


if __name__ == "__main__":
    main()
