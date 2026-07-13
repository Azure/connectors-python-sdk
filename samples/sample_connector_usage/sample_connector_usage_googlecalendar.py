# Copyright (c) Microsoft Corporation. All rights reserved.

"""
Google Calendar Connector SDK Sample

This sample demonstrates how to use the Google Calendar connector SDK.

Prerequisites:
1. Azure subscription with Google Calendar connection
2. Google Calendar connection in Connector Namespaces
3. Connection runtime URL from Azure Portal

Installation:
    pip install azure-connectors

Usage:
    Set environment variable:
    $env:GOOGLECALENDAR_CONNECTION_URL = (
        "https://[region].azure-apihub.net/apim/googlecalendar/[connection-id]"
    )

    python sample_connector_usage_googlecalendar.py
"""

import asyncio
import os

from azure.identity.aio import DefaultAzureCredential
from azure.connectors import ConnectorException
from azure.connectors.googlecalendar import (
    GooglecalendarClient,
    RequestEvent,
)

# Connection runtime URL format:
# https://[region].azure-apihub.net/apim/googlecalendar/[connection-id]
CONNECTION_RUNTIME_URL = os.environ.get(
    "GOOGLECALENDAR_CONNECTION_URL",
    "",
)


async def example_1_list_calendars():
    """Example 1: List calendars visible to the connection account."""
    print("\n=== Example 1: List Calendars ===")

    credential = DefaultAzureCredential()

    async with GooglecalendarClient(CONNECTION_RUNTIME_URL, credential) as client:
        result = await client.list_calendars_async(min_access_role="reader")

        items = result.get("items", []) if result else []
        print(f"Found {len(items)} calendar(s).")
        for calendar in items[:10]:
            print(f"  - {calendar.get('summary', 'N/A')} ({calendar.get('id', 'N/A')})")


async def example_2_list_events():
    """Example 2: List events for a configured calendar."""
    print("\n=== Example 2: List Events ===")

    calendar_id = os.environ.get("GOOGLECALENDAR_TEST_CALENDAR_ID", "")
    if not calendar_id:
        print("Set GOOGLECALENDAR_TEST_CALENDAR_ID to run this example.")
        return

    credential = DefaultAzureCredential()

    async with GooglecalendarClient(CONNECTION_RUNTIME_URL, credential) as client:
        result = await client.list_events_async(calendar_id=calendar_id)

        events = result.get("items", []) if result else []
        print(f"Found {len(events)} event(s) in calendar '{calendar_id}'.")
        for event in events[:10]:
            print(f"  - {event.get('summary', 'N/A')} ({event.get('id', 'N/A')})")


async def example_3_create_event():
    """Example 3: Create a test event in the configured calendar."""
    print("\n=== Example 3: Create Event ===")

    calendar_id = os.environ.get("GOOGLECALENDAR_TEST_CALENDAR_ID", "")
    if not calendar_id:
        print("Set GOOGLECALENDAR_TEST_CALENDAR_ID to run this example.")
        return

    credential = DefaultAzureCredential()

    async with GooglecalendarClient(CONNECTION_RUNTIME_URL, credential) as client:
        try:
            payload = RequestEvent(
                summary="SDK Sample Event",
                start="2026-07-09T15:00:00Z",
                end="2026-07-09T15:30:00Z",
                description="Created by azure-connectors sample.",
                location="Online",
                status="confirmed",
            )

            created = await client.create_event_async(input=payload, calendar_id=calendar_id)
            if created:
                print(f"Created event id: {created.get('id', 'N/A')}")
            else:
                print("Create completed with no response body.")
        except ConnectorException as ex:
            print(f"Connector error: {ex}")


async def example_4_trigger_poll_examples():
    """Example 4: Poll trigger endpoints for calendar event changes."""
    print("\n=== Example 4: Trigger Poll Calls ===")

    calendar_id = os.environ.get("GOOGLECALENDAR_TEST_CALENDAR_ID", "")
    if not calendar_id:
        print("Set GOOGLECALENDAR_TEST_CALENDAR_ID to run this example.")
        return

    credential = DefaultAzureCredential()

    async with GooglecalendarClient(CONNECTION_RUNTIME_URL, credential) as client:
        try:
            changed = await client.on_changed_event_in_calendar_async(
                calendar_id=calendar_id,
                single_events="true",
            )
            started = await client.on_event_started_async(calendar_id=calendar_id)

            changed_items = len(changed.get("items", [])) if changed else 0
            started_items = len(started.get("items", [])) if started else 0
            print(f"Changed trigger returned {changed_items} event(s).")
            print(f"Started trigger returned {started_items} event(s).")
        except ConnectorException as ex:
            print(f"Connector error: {ex}")


async def main():
    """Run all Google Calendar connector examples."""
    if not CONNECTION_RUNTIME_URL:
        print("Error: GOOGLECALENDAR_CONNECTION_URL environment variable is not set.")
        print("Set it to your Google Calendar connector runtime URL from Azure Portal.")
        return

    print(f"Using connection URL: {CONNECTION_RUNTIME_URL[:50]}...")

    await example_1_list_calendars()
    await example_2_list_events()
    await example_3_create_event()
    await example_4_trigger_poll_examples()

    print("\n=== Google Calendar sample completed ===")


if __name__ == "__main__":
    asyncio.run(main())
