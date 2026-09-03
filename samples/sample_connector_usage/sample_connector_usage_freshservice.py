"""
Freshservice Connector SDK Sample

This sample demonstrates how to use the Freshservice connector SDK.

Prerequisites:
1. Azure subscription with Freshservice connection
2. Freshservice connection in Connector Namespaces
3. Connection runtime URL from Azure Portal

Installation:
    pip install azure-connectors

Usage:
    Set environment variable:
    $env:FRESHSERVICE_CONNECTION_URL = "https://[region].azure-apihub.net/apim/freshservice/[id]"

    python sample_connector_usage_freshservice.py
"""

import asyncio
import os

from azure.identity.aio import DefaultAzureCredential

from azure.connectors import ConnectorException
from azure.connectors.freshservice import (
    AddNoteRequest,
    CreateTicketRequest,
    FreshserviceClient,
    UpdateTicketRequest,
)


# Connection runtime URL format:
# https://[region].azure-apihub.net/apim/freshservice/[connection-id]
CONNECTION_RUNTIME_URL = os.environ.get("FRESHSERVICE_CONNECTION_URL", "")


async def example_1_create_ticket() -> None:
    """Example 1: Create a ticket."""
    print("\n=== Example 1: Create Ticket ===")

    credential = DefaultAzureCredential()
    async with FreshserviceClient(CONNECTION_RUNTIME_URL, credential) as client:
        request = CreateTicketRequest(
            subject="SDK sample ticket",
            description="Created from the freshservice SDK sample.",
            email="requester@example.com",
            priority="1",
            status="2",
        )

        created = await client.create_ticket_async(input=request)
        ticket = created.get("ticket", {}) if created else {}
        print(f"Created ticket: {ticket.get('id')}")


async def example_2_update_ticket() -> None:
    """Example 2: Update an existing ticket."""
    print("\n=== Example 2: Update Ticket ===")

    credential = DefaultAzureCredential()
    async with FreshserviceClient(CONNECTION_RUNTIME_URL, credential) as client:
        request = UpdateTicketRequest(priority="3", status="3")

        updated = await client.update_ticket_async(input=request, ticket_id=1)
        ticket = updated.get("ticket", {}) if updated else {}
        print(f"Updated ticket: {ticket.get('id')}")


async def example_3_add_note() -> None:
    """Example 3: Add a note to a ticket."""
    print("\n=== Example 3: Add Note ===")

    credential = DefaultAzureCredential()
    async with FreshserviceClient(CONNECTION_RUNTIME_URL, credential) as client:
        request = AddNoteRequest(
            body="Note added from the freshservice SDK sample.",
            private=True,
        )

        note = await client.add_note_async(input=request, ticket_id=1)
        conversation = note.get("conversation", {}) if note else {}
        print(f"Added note: {conversation.get('id')}")


async def main() -> None:
    """Run Freshservice connector examples."""
    if not CONNECTION_RUNTIME_URL:
        print("Error: FRESHSERVICE_CONNECTION_URL environment variable not set.")
        print("Set it to your connection runtime URL from Azure Portal.")
        return

    print("Freshservice Connector SDK - Sample Usage")
    print("=" * 50)

    try:
        # Uncomment to create, update, or annotate a ticket in Freshservice.
        # await example_1_create_ticket()
        # await example_2_update_ticket()
        # await example_3_add_note()
        print("Set the example calls in main() to run against your instance.")

    except ConnectorException as ex:
        print(f"Connector error: {ex}")
    except Exception as ex:
        print(f"Unexpected error: {ex}")


if __name__ == "__main__":
    asyncio.run(main())
