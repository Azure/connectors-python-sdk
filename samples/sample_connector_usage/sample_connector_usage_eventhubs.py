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
                event_hub_name=EVENT_HUB_NAME
            )

            events = batch_input.additional_properties.get("events", [])
            print(f"Batch of {len(events)} events sent to '{EVENT_HUB_NAME}':")
            for i, evt in enumerate(events, 1):
                print(f"  {i}. {evt.get('contentData', 'N/A')[:40]}...")

        except ConnectorException as ex:
            print(f"Connector error (status {ex.status_code}): {ex}")
        except Exception as ex:
            print(f"Error: {ex}")


async def example_4_receive_events():
    """Example 4: Receive events from Event Hub."""
    print("\n=== Example 4: Receive Events ===")

    if not EVENT_HUB_NAME:
        print("Set EVENTHUBS_HUB_NAME environment variable.")
        return

    credential = DefaultAzureCredential()

    async with EventhubsClient(CONNECTION_RUNTIME_URL, credential) as client:
        try:
            # Receive up to 10 events
            result = await client.on_new_events_async(
                event_hub_name=EVENT_HUB_NAME,
                maximum_events_count="10"
            )

            if result:
                events = result if isinstance(result, list) else [result]
                print(f"Received {len(events)} event(s) from '{EVENT_HUB_NAME}':")
                for i, event in enumerate(events[:5], 1):
                    if isinstance(event, dict):
                        content = event.get("contentData", event.get("content_data", "N/A"))
                        sys_props = event.get("systemProperties", {})
                        seq_num = sys_props.get("sequenceNumber", "N/A")
                        print(f"  {i}. Sequence: {seq_num}")
                        if content:
                            content_str = str(content)[:50]
                            print(f"     Content: {content_str}...")
                if len(events) > 5:
                    print(f"  ... and {len(events) - 5} more events")
            else:
                print("No events available in Event Hub.")

        except ConnectorException as ex:
            print(f"Connector error (status {ex.status_code}): {ex}")
        except Exception as ex:
            print(f"Error: {ex}")


async def example_5_receive_with_consumer_group():
    """Example 5: Receive events using a specific consumer group."""
    print("\n=== Example 5: Receive with Consumer Group ===")

    if not EVENT_HUB_NAME:
        print("Set EVENTHUBS_HUB_NAME environment variable.")
        return

    consumer_group = os.environ.get("EVENTHUBS_CONSUMER_GROUP", "$Default")
    credential = DefaultAzureCredential()

    async with EventhubsClient(CONNECTION_RUNTIME_URL, credential) as client:
        try:
            result = await client.on_new_events_async(
                event_hub_name=EVENT_HUB_NAME,
                consumer_group_name=consumer_group,
                maximum_events_count="5",
                content_type="application/json"
            )

            if result:
                events = result if isinstance(result, list) else [result]
                print(f"Consumer group '{consumer_group}': {len(events)} event(s)")
                for i, event in enumerate(events, 1):
                    if isinstance(event, dict):
                        sys_props = event.get("systemProperties", {})
                        enqueued = sys_props.get("enqueuedTimeUtc", "N/A")
                        partition = sys_props.get("partitionKey", "N/A")
                        print(f"  {i}. Enqueued: {enqueued}, Partition: {partition}")
            else:
                print(f"No events in consumer group '{consumer_group}'.")

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
    await example_4_receive_events()
    await example_5_receive_with_consumer_group()

    print("\n" + "=" * 60)
    print("Sample completed!")


if __name__ == "__main__":
    asyncio.run(main())
