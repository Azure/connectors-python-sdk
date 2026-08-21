"""
SendGrid Connector SDK Sample

This sample demonstrates how to use the SendGrid connector SDK.

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

import asyncio
import os

from azure.identity.aio import DefaultAzureCredential

from azure.connectors import ConnectorException
from azure.connectors.sendgrid import (
    EmailRequest,
    SendgridClient,
)


# Connection runtime URL format:
# https://[region].azure-apihub.net/apim/sendgrid/[connection-id]
CONNECTION_RUNTIME_URL = os.environ.get("SENDGRID_CONNECTION_URL", "")


async def example_1_send_email() -> None:
    """Example 1: Send an email."""
    print("\n=== Example 1: Send Email ===")

    credential = DefaultAzureCredential()
    async with SendgridClient(CONNECTION_RUNTIME_URL, credential) as client:
        result = await client.send_email_async(
            input=EmailRequest(
                from_="sender@example.com",
                to="recipient@example.com",
                subject="Hello from the SDK sample",
                text="This message was sent via the SendGrid connector SDK.",
            ),
        )
        print(f"Send result: {result}")


async def example_2_list_recipient_lists() -> None:
    """Example 2: List recipient lists."""
    print("\n=== Example 2: List Recipient Lists ===")

    credential = DefaultAzureCredential()
    async with SendgridClient(CONNECTION_RUNTIME_URL, credential) as client:
        lists = await client.list_recipient_lists_async()
        print(f"Recipient lists: {lists}")


async def example_3_list_recipients() -> None:
    """Example 3: List recipients."""
    print("\n=== Example 3: List Recipients ===")

    credential = DefaultAzureCredential()
    async with SendgridClient(CONNECTION_RUNTIME_URL, credential) as client:
        recipients = await client.list_recipients_async()
        print(f"Recipients: {recipients}")


async def example_4_get_bounce() -> None:
    """Example 4: Get a bounce record for an email address."""
    print("\n=== Example 4: Get Bounce ===")

    credential = DefaultAzureCredential()
    async with SendgridClient(CONNECTION_RUNTIME_URL, credential) as client:
        bounce = await client.get_bounce_async(email="recipient@example.com")
        print(f"Bounce: {bounce}")


async def main() -> None:
    """Run SendGrid connector examples."""
    if not CONNECTION_RUNTIME_URL:
        print("Error: SENDGRID_CONNECTION_URL environment variable not set.")
        print("Set it to your connection runtime URL from Azure Portal.")
        return

    print("SendGrid Connector SDK - Sample Usage")
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
    asyncio.run(main())
