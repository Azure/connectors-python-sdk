# Copyright (c) Microsoft Corporation. All rights reserved.

"""
Microsoft Bookings Connector SDK Sample

This sample demonstrates how to use the Microsoft Bookings connector SDK to
manage booking businesses and appointment webhooks.

Prerequisites:
1. Azure subscription with Microsoft Bookings connection
2. Microsoft Bookings connection in Connector Namespaces
3. Connection runtime URL from Azure Portal

Installation:
    pip install azure-connectors

Usage:
    Set environment variable:
    $env:MICROSOFTBOOKINGS_CONNECTION_URL = "<connection-url>"

    python sample_connector_usage_microsoftbookings.py
"""

import asyncio
import os
from azure.identity.aio import DefaultAzureCredential
from azure.connectors import ConnectorException
from azure.connectors.microsoftbookings import (
    MicrosoftbookingsClient,
    CreateAppointmentInput,
    UpdateAppointmentInput,
    CancelAppointmentInput,
)

# Connection runtime URL format:
# https://[region].azure-apihub.net/apim/microsoftbookings/[connection-id]
CONNECTION_RUNTIME_URL = os.environ.get(
    "MICROSOFTBOOKINGS_CONNECTION_URL",
    ""
)

# Sample booking business SMTP address (replace with your own)
BOOKING_SMTP_ADDRESS = os.environ.get(
    "BOOKING_SMTP_ADDRESS",
    "bookings@contoso.com"
)

# Webhook callback URL for trigger events
WEBHOOK_CALLBACK_URL = os.environ.get(
    "WEBHOOK_CALLBACK_URL",
    "https://your-function-app.azurewebsites.net/api/BookingsCallback"
)


async def example_1_list_booking_businesses():
    """Example 1: List booking businesses where user is an admin."""
    print("\n=== Example 1: List Booking Businesses ===")

    credential = DefaultAzureCredential()

    async with MicrosoftbookingsClient(CONNECTION_RUNTIME_URL, credential) as client:
        try:
            result = await client.list_bookings_business_user_as_admin_async()

            if result and result.get("mailboxes"):
                mailboxes = result["mailboxes"]
                print(f"Found {len(mailboxes)} booking business(es):")
                for mailbox in mailboxes:
                    print(f"  - {mailbox.get('display_name')}")
                    print(f"    Email: {mailbox.get('email')}")
            else:
                print("No booking businesses found where you are an admin")

        except ConnectorException as ex:
            print(f"Connector error: {ex}")
        except Exception as ex:
            print(f"Error: {ex}")


async def example_2_build_create_webhook():
    """Example 2: Build an appointment-created webhook payload."""
    print("\n=== Example 2: Build Create Appointment Webhook ===")

    webhook_input = CreateAppointmentInput(
        webhook={"callbackUrl": WEBHOOK_CALLBACK_URL}
    )
    print(f"Business: {BOOKING_SMTP_ADDRESS}")
    print(f"Create webhook payload: {webhook_input.webhook}")


async def example_3_build_update_webhook():
    """Example 3: Build an appointment-updated webhook payload."""
    print("\n=== Example 3: Build Update Appointment Webhook ===")

    webhook_input = UpdateAppointmentInput(
        webhook={"callbackUrl": WEBHOOK_CALLBACK_URL}
    )
    print(f"Update webhook payload: {webhook_input.webhook}")


async def example_4_build_cancel_webhook():
    """Example 4: Build an appointment-cancelled webhook payload."""
    print("\n=== Example 4: Build Cancel Appointment Webhook ===")

    webhook_input = CancelAppointmentInput(
        webhook={"callbackUrl": WEBHOOK_CALLBACK_URL}
    )
    print(f"Cancel webhook payload: {webhook_input.webhook}")


async def main():
    """Run all examples."""
    if not CONNECTION_RUNTIME_URL:
        print("Error: MICROSOFTBOOKINGS_CONNECTION_URL environment variable not set.")
        print("Set it to your connection runtime URL from Azure Portal.")
        return

    print(f"Using connection URL: {CONNECTION_RUNTIME_URL[:50]}...")

    # Run read-only example by default
    await example_1_list_booking_businesses()

    # The current generated action client exposes payload models but not the
    # webhook registration trigger operations.
    await example_2_build_create_webhook()
    await example_3_build_update_webhook()
    await example_4_build_cancel_webhook()

    print("\n=== All examples completed ===")


if __name__ == "__main__":
    asyncio.run(main())
