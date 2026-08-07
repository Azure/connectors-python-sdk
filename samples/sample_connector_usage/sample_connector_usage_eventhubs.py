# Copyright (c) Microsoft Corporation. All rights reserved.

"""
Azure Event Hubs Connector SDK Sample

This sample demonstrates how to use the Azure Event Hubs connector SDK
to send and receive events from Azure Event Hubs.

Prerequisites:
1. Azure subscription with Azure Event Hubs connection
2. Event Hubs connection in Connector Namespaces (with access configured)
3. Connection runtime URL from Azure Portal
4. Azure Event Hubs namespace with an event hub

Installation:
    pip install azure-connectors

Usage:
    Set environment variables:
    $env:EVENTHUBS_CONNECTION_URL = "https://...apihub.net/apim/eventhubs/..."
    $env:EVENTHUBS_HUB_NAME = "<event-hub-name>"

    python sample_connector_usage_eventhubs.py
"""

import asyncio
import json
import os
from azure.identity.aio import DefaultAzureCredential
from azure.connectors import ConnectorException
from azure.connectors.eventhubs import (
    EventhubsClient,
    SendEvent,
    SendEventsInput,
)

# Connection runtime URL format:
# https://[region].azure-apihub.net/apim/eventhubs/[connection-id]
CONNECTION_RUNTIME_URL = os.environ.get(
    "EVENTHUBS_CONNECTION_URL",
    ""
)

# Event Hub name
EVENT_HUB_NAME = os.environ.get("EVENTHUBS_HUB_NAME", "")


async def example_1_send_event():
    """Example 1: Send a single event to Event Hub."""
    print("\n=== Example 1: Send Single Event ===")

    if not EVENT_HUB_NAME:
        print("Set EVENTHUBS_HUB_NAME environment variable.")
        print("Example: $env:EVENTHUBS_HUB_NAME = 'my-event-hub'")
        return

    credential = DefaultAzureCredential()

    async with EventhubsClient(CONNECTION_RUNTIME_URL, credential) as client:
        try:
            # Create a single event
            event = SendEvent(
                content_data=json.dumps({
                    "message": "Hello from Azure Connectors SDK for Python!",
                    "timestamp": "2024-01-15T10:30:00Z",
                    "source": "python-sdk-sample"
                }),
                properties={
                    "eventType": "sample",
                    "version": "1.0"
                }
            )

            await client.send_event_async(
                input=event,
                event_hub_name=EVENT_HUB_NAME
            )

            print(f"Event sent to Event Hub '{EVENT_HUB_NAME}':")
            print(f"  Content: {event.content_data[:50]}...")
            print(f"  Properties: {event.properties}")

        except ConnectorException as ex:
            print(f"Connector error (status {ex.status_code}): {ex}")
        except Exception as ex:
            print(f"Error: {ex}")


async def example_2_send_event_with_partition_key():
    """Example 2: Send an event with a specific partition key."""
    print("\n=== Example 2: Send Event with Partition Key ===")

    if not EVENT_HUB_NAME:
        print("Set EVENTHUBS_HUB_NAME environment variable.")
        return

    partition_key = os.environ.get("EVENTHUBS_PARTITION_KEY", "partition-1")
    credential = DefaultAzureCredential()

    async with EventhubsClient(CONNECTION_RUNTIME_URL, credential) as client:
        try:
            event = SendEvent(
                content_data=json.dumps({
                    "orderId": "ORD-12345",
                    "customerId": "CUST-001",
                    "amount": 99.99
                }),
                properties={
                    "eventType": "orderCreated"
                }
            )

            await client.send_event_async(
                input=event,
                event_hub_name=EVENT_HUB_NAME,
                partition_key=partition_key
            )

            print(f"Event sent with partition key '{partition_key}':")
            print(f"  Content: {event.content_data}")

        except ConnectorException as ex:
            print(f"Connector error (status {ex.status_code}): {ex}")
        except Exception as ex:
            print(f"Error: {ex}")


async def example_3_send_batch_events():
    """Example 3: Send multiple events in a batch."""
    print("\n=== Example 3: Send Batch Events ===")

    if not EVENT_HUB_NAME:
        print("Set EVENTHUBS_HUB_NAME environment variable.")
        return

    credential = DefaultAzureCredential()

    async with EventhubsClient(CONNECTION_RUNTIME_URL, credential) as client:
        try:
            # Create batch with multiple events
            batch_input = SendEventsInput(
                additional_properties={
                    "events": [
                        {
                            "contentData": json.dumps({"id": 1, "name": "Event 1"}),
                            "properties": {"index": "1"}
                        },
                        {
                            "contentData": json.dumps({"id": 2, "name": "Event 2"}),
                            "properties": {"index": "2"}
                        },
                        {
                            "contentData": json.dumps({"id": 3, "name": "Event 3"}),
                            "properties": {"index": "3"}
                        }
                    ]
                }
            )

            await client.send_events_async(
                input=batch_input,
                event_hub_name=EVENT_HUB_NAME,
                partition_key=os.environ.get("EVENTHUBS_PARTITION_KEY", "partition-1")
            )

            events = batch_input.additional_properties.get("events", [])
            print(f"Batch of {len(events)} events sent to '{EVENT_HUB_NAME}':")
            for i, evt in enumerate(events, 1):
                print(f"  {i}. {evt.get('contentData', 'N/A')[:40]}...")

        except ConnectorException as ex:
            print(f"Connector error (status {ex.status_code}): {ex}")
        except Exception as ex:
            print(f"Error: {ex}")


async def example_4_list_event_hubs():
    """Example 4: List Event Hubs in the namespace."""
    print("\n=== Example 4: List Event Hubs ===")

    credential = DefaultAzureCredential()

    async with EventhubsClient(CONNECTION_RUNTIME_URL, credential) as client:
        try:
            result = await client.get_event_hubs_async()
            print(f"Event Hubs: {result}")

        except ConnectorException as ex:
            print(f"Connector error (status {ex.status_code}): {ex}")
        except Exception as ex:
            print(f"Error: {ex}")


async def example_5_list_consumer_groups():
    """Example 5: List consumer groups for an Event Hub."""
    print("\n=== Example 5: List Consumer Groups ===")

    if not EVENT_HUB_NAME:
        print("Set EVENTHUBS_HUB_NAME environment variable.")
        return

    credential = DefaultAzureCredential()

    async with EventhubsClient(CONNECTION_RUNTIME_URL, credential) as client:
        try:
            result = await client.get_consumer_groups_async(
                event_hub_name=EVENT_HUB_NAME
            )
            print(f"Consumer groups for '{EVENT_HUB_NAME}': {result}")

        except ConnectorException as ex:
            print(f"Connector error (status {ex.status_code}): {ex}")
        except Exception as ex:
            print(f"Error: {ex}")


async def main():
    """Run all examples."""
    print("Azure Event Hubs Connector SDK - Sample Usage")
    print("=" * 60)

    if not CONNECTION_RUNTIME_URL:
        print("\nWARNING: EVENTHUBS_CONNECTION_URL environment variable not set.")
        print("Set it to your connection runtime URL to run actual API calls.")
        print("Format: https://[region].azure-apihub.net/apim/eventhubs/[id]")
        return

    await example_1_send_event()
    await example_2_send_event_with_partition_key()
    await example_3_send_batch_events()
    await example_4_list_event_hubs()
    await example_5_list_consumer_groups()

    print("\n" + "=" * 60)
    print("Sample completed!")


if __name__ == "__main__":
    asyncio.run(main())
