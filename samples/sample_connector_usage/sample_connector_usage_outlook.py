# Copyright (c) Microsoft Corporation. All rights reserved.

"""
Outlook.com Connector SDK Sample

This sample demonstrates how to use the Outlook connector SDK
to interact with Outlook.com calendars, contacts, and email.

Note: This connector is for Outlook.com (personal Microsoft accounts).
For Office 365/work accounts, see the Office 365 Outlook connector.

Prerequisites:
1. Azure subscription with Outlook connection
2. Outlook connection in Connector Namespaces (with access configured)
3. Connection runtime URL from Azure Portal
4. Microsoft account (Outlook.com/Hotmail/Live)

Installation:
    pip install azure-connectors

Usage:
    Set environment variables:
    $env:OUTLOOK_CONNECTION_URL = "https://...apihub.net/apim/outlook/..."

    python sample_connector_usage_outlook.py
"""

import asyncio
import os
from azure.identity.aio import DefaultAzureCredential
from azure.connectors import ConnectorException
from azure.connectors.outlook import (
    OutlookClient,
    ClientSendHtmlMessage,
)

# Connection runtime URL format:
# https://[region].azure-apihub.net/apim/outlook/[connection-id]
CONNECTION_RUNTIME_URL = os.environ.get(
    "OUTLOOK_CONNECTION_URL",
    ""
)


async def example_1_list_calendars():
    """Example 1: List available calendars."""
    print("\n=== Example 1: List Calendars ===")

    credential = DefaultAzureCredential()

    async with OutlookClient(CONNECTION_RUNTIME_URL, credential) as client:
        try:
            result = await client.calendar_get_tables_async()

            if result:
                calendars = result.get("value", [])
                print(f"Found {len(calendars)} calendar(s):")
                for cal in calendars:
                    name = cal.get("Name", cal.get("name", "N/A"))
                    cal_id = cal.get("Id", cal.get("id", "N/A"))
                    print(f"  - {name}")
                    cal_id_str = str(cal_id)
                    if len(cal_id_str) > 40:
                        print(f"    ID: {cal_id_str[:40]}...")
                    else:
                        print(f"    ID: {cal_id_str}")
            else:
                print("No calendars found.")

        except ConnectorException as ex:
            print(f"Connector error (status {ex.status_code}): {ex}")
        except Exception as ex:
            print(f"Error: {ex}")


async def example_2_list_contact_folders():
    """Example 2: List available contact folders."""
    print("\n=== Example 2: List Contact Folders ===")

    credential = DefaultAzureCredential()

    async with OutlookClient(CONNECTION_RUNTIME_URL, credential) as client:
        try:
            result = await client.contact_get_tables_async()

            if result:
                folders = result.get("value", [])
                print(f"Found {len(folders)} contact folder(s):")
                for folder in folders:
                    name = folder.get("Name", folder.get("name", "N/A"))
                    folder_id = folder.get("Id", folder.get("id", "N/A"))
                    print(f"  - {name}")
                    if len(str(folder_id)) > 40:
                        print(f"    ID: {folder_id[:40]}...")
                    else:
                        print(f"    ID: {folder_id}")
            else:
                print("No contact folders found.")

        except ConnectorException as ex:
            print(f"Connector error (status {ex.status_code}): {ex}")
        except Exception as ex:
            print(f"Error: {ex}")


async def example_3_get_calendar_events():
    """Example 3: Get calendar events."""
    print("\n=== Example 3: Get Calendar Events ===")

    # Calendar ID - use 'Calendar' for default calendar or get ID from Example 1
    calendar_id = os.environ.get("OUTLOOK_CALENDAR_ID", "Calendar")

    credential = DefaultAzureCredential()

    async with OutlookClient(CONNECTION_RUNTIME_URL, credential) as client:
        try:
            result = await client.calendar_get_items_async(
                table=calendar_id,
                top="5"  # Get up to 5 events
            )

            if result:
                events = result.get("value", [])
                print(f"Found {len(events)} event(s) in calendar:")
                for event in events[:5]:
                    subject = event.get("Subject", event.get("subject", "N/A"))
                    start = event.get("Start", event.get("start", "N/A"))
                    print(f"  - {subject}")
                    print(f"    Start: {start}")
            else:
                print("No events found.")

        except ConnectorException as ex:
            print(f"Connector error (status {ex.status_code}): {ex}")
        except Exception as ex:
            print(f"Error: {ex}")


async def example_4_get_contacts():
    """Example 4: Get contacts from a contact folder."""
    print("\n=== Example 4: Get Contacts ===")

    # Contact folder ID - use 'Contacts' for default folder or get ID from Example 2
    folder_id = os.environ.get("OUTLOOK_CONTACTS_FOLDER_ID", "Contacts")

    credential = DefaultAzureCredential()

    async with OutlookClient(CONNECTION_RUNTIME_URL, credential) as client:
        try:
            result = await client.contact_get_items_async(
                table=folder_id,
                top="10"  # Get up to 10 contacts
            )

            if result:
                contacts = result.get("value", [])
                print(f"Found {len(contacts)} contact(s):")
                for contact in contacts[:5]:
                    display_name = contact.get("DisplayName", "N/A")
                    email = contact.get("EmailAddresses", [])
                    email_str = email[0].get("Address", "N/A") if email else "N/A"
                    print(f"  - {display_name}")
                    print(f"    Email: {email_str}")
                if len(contacts) > 5:
                    print(f"  ... and {len(contacts) - 5} more contacts")
            else:
                print("No contacts found.")

        except ConnectorException as ex:
            print(f"Connector error (status {ex.status_code}): {ex}")
        except Exception as ex:
            print(f"Error: {ex}")


async def example_5_send_email():
    """Example 5: Send an email."""
    print("\n=== Example 5: Send Email ===")

    recipient = os.environ.get("OUTLOOK_RECIPIENT_EMAIL", "")
    if not recipient:
        print("Set OUTLOOK_RECIPIENT_EMAIL environment variable to send email.")
        print("Example: $env:OUTLOOK_RECIPIENT_EMAIL = 'recipient@example.com'")
        print("Skipping email send example...")
        return

    credential = DefaultAzureCredential()

    async with OutlookClient(CONNECTION_RUNTIME_URL, credential) as client:
        try:
            email = ClientSendHtmlMessage(
                to=recipient,
                subject="Test from Azure Connectors SDK for Python",
                body="<html><body><h1>Hello!</h1>"
                     "<p>This email was sent using the Azure Connectors SDK.</p>"
                     "</body></html>",
                importance="Normal"
            )

            await client.send_email_async(input=email)

            print("Email sent successfully!")
            print(f"  To: {recipient}")
            print(f"  Subject: {email.subject}")

        except ConnectorException as ex:
            print(f"Connector error (status {ex.status_code}): {ex}")
        except Exception as ex:
            print(f"Error: {ex}")


async def main():
    """Run all examples."""
    print("Outlook.com Connector SDK - Sample Usage")
    print("=" * 60)

    if not CONNECTION_RUNTIME_URL:
        print("\nWARNING: OUTLOOK_CONNECTION_URL environment variable not set.")
        print("Set it to your connection runtime URL to run actual API calls.")
        print("Format: https://[region].azure-apihub.net/apim/outlook/[id]")
        return

    await example_1_list_calendars()
    await example_2_list_contact_folders()
    await example_3_get_calendar_events()
    await example_4_get_contacts()
    await example_5_send_email()

    print("\n" + "=" * 60)
    print("Sample completed!")


if __name__ == "__main__":
    asyncio.run(main())
