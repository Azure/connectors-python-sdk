# Copyright (c) Microsoft Corporation. All rights reserved.

"""
Google Calendar sample for the Azure Connectors Python SDK

This sample demonstrates how to use the Google Calendar client from the Azure Connectors Python SDK.

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
import os

from azure.identity import DefaultAzureCredential
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


def example_1_list_calendars():
    """Example 1: List calendars visible to the connection account."""
    print("\n=== Example 1: List Calendars ===")

    with DefaultAzureCredential() as credential:

        with GooglecalendarClient(CONNECTION_RUNTIME_URL, credential) as client:
            items = list(client.list_calendars(min_access_role="reader"))
            print(f"Found {len(items)} calendar(s).")
            for calendar in items[:10]:
                print(f"  - {calendar.get('summary', 'N/A')} ({calendar.get('id', 'N/A')})")


def example_2_list_events():
    """Example 2: List events for a configured calendar."""
    print("\n=== Example 2: List Events ===")

    calendar_id = os.environ.get("GOOGLECALENDAR_TEST_CALENDAR_ID", "")
    if not calendar_id:
        print("Set GOOGLECALENDAR_TEST_CALENDAR_ID to run this example.")
        return

    with DefaultAzureCredential() as credential:

        with GooglecalendarClient(CONNECTION_RUNTIME_URL, credential) as client:
            events = list(client.list_events(calendar_id=calendar_id))
            print(f"Found {len(events)} event(s) in calendar '{calendar_id}'.")
            for event in events[:10]:
                print(f"  - {event.get('summary', 'N/A')} ({event.get('id', 'N/A')})")


def example_3_create_event():
    """Example 3: Create a test event in the configured calendar."""
    print("\n=== Example 3: Create Event ===")

    calendar_id = os.environ.get("GOOGLECALENDAR_TEST_CALENDAR_ID", "")
    if not calendar_id:
        print("Set GOOGLECALENDAR_TEST_CALENDAR_ID to run this example.")
        return

    with DefaultAzureCredential() as credential:

        with GooglecalendarClient(CONNECTION_RUNTIME_URL, credential) as client:
            try:
                payload = RequestEvent(
                    summary="SDK Sample Event",
                    start="2026-07-09T15:00:00Z",
                    end="2026-07-09T15:30:00Z",
                    description="Created by azure-connectors sample.",
                    location="Online",
                    status="confirmed",
                )

                created = client.create_event(input=payload, calendar_id=calendar_id)
                if created:
                    print(f"Created event id: {created.get('id', 'N/A')}")
                else:
                    print("Create completed with no response body.")
            except ConnectorException as ex:
                print(f"Connector error: {ex}")


def example_4_list_events_for_polling():
    """Example 4: List events in a time window for polling logic."""
    print("\n=== Example 4: List Events for Polling ===")

    calendar_id = os.environ.get("GOOGLECALENDAR_TEST_CALENDAR_ID", "")
    if not calendar_id:
        print("Set GOOGLECALENDAR_TEST_CALENDAR_ID to run this example.")
        return

    with DefaultAzureCredential() as credential:

        with GooglecalendarClient(CONNECTION_RUNTIME_URL, credential) as client:
            try:
                events = list(client.list_events(
                    calendar_id=calendar_id,
                    time_min="2026-07-09T00:00:00Z",
                    time_max="2026-07-10T00:00:00Z",
                ))
                print(f"Time-window query returned {len(events)} event(s).")
                print("Persist event IDs and update times to implement change polling.")
            except ConnectorException as ex:
                print(f"Connector error: {ex}")


def main():
    """Run all Google Calendar connector examples."""
    if not CONNECTION_RUNTIME_URL:
        print("Error: GOOGLECALENDAR_CONNECTION_URL environment variable is not set.")
        print("Set it to your Google Calendar connector runtime URL from Azure Portal.")
        return

    print(f"Using connection URL: {CONNECTION_RUNTIME_URL[:50]}...")

    example_1_list_calendars()
    example_2_list_events()
    example_3_create_event()
    example_4_list_events_for_polling()

    print("\n=== Google Calendar sample completed ===")


if __name__ == "__main__":
    main()
