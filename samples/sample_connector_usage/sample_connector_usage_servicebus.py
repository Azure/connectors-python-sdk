# Copyright (c) Microsoft Corporation. All rights reserved.

"""
Azure Service Bus Connector SDK Sample

This sample demonstrates how to use the Azure Service Bus connector SDK
to send and receive messages from Azure Service Bus queues and topics.

Prerequisites:
1. Azure subscription with Azure Service Bus connection
2. Service Bus connection in Connector Namespaces (with access configured)
3. Connection runtime URL from Azure Portal
4. Azure Service Bus namespace with queues and/or topics

Installation:
    pip install azure-connectors

Usage:
    Set environment variables:
    $env:SERVICEBUS_CONNECTION_URL = "https://...apihub.net/apim/servicebus/..."
    $env:SERVICEBUS_QUEUE_NAME = "<queue-name>"
    $env:SERVICEBUS_TOPIC_NAME = "<topic-name>"
    $env:SERVICEBUS_SUBSCRIPTION_NAME = "<subscription-name>"

    python sample_connector_usage_servicebus.py
"""

import asyncio
import json
import os
from azure.identity.aio import DefaultAzureCredential
from azure.connectors import ConnectorException
from azure.connectors.servicebus import (
    ServicebusClient,
    ServiceBusMessage,
)

# Connection runtime URL format:
# https://[region].azure-apihub.net/apim/servicebus/[connection-id]
CONNECTION_RUNTIME_URL = os.environ.get(
    "SERVICEBUS_CONNECTION_URL",
    ""
)

# Service Bus entity names
QUEUE_NAME = os.environ.get("SERVICEBUS_QUEUE_NAME", "")
TOPIC_NAME = os.environ.get("SERVICEBUS_TOPIC_NAME", "")
SUBSCRIPTION_NAME = os.environ.get("SERVICEBUS_SUBSCRIPTION_NAME", "")


async def example_1_send_message_to_queue():
    """Example 1: Send a single message to a Service Bus queue."""
    print("\n=== Example 1: Send Message to Queue ===")

    if not QUEUE_NAME:
        print("Set SERVICEBUS_QUEUE_NAME environment variable.")
        print("Example: $env:SERVICEBUS_QUEUE_NAME = 'my-queue'")
        return

    credential = DefaultAzureCredential()

    async with ServicebusClient(CONNECTION_RUNTIME_URL, credential) as client:
        try:
            # Create a message
            message = ServiceBusMessage(
                content_data=json.dumps({
                    "orderId": "ORD-12345",
                    "customerId": "CUST-001",
                    "amount": 99.99,
                    "timestamp": "2024-01-15T10:30:00Z"
                }),
                content_type="application/json",
                label="order-created",
                correlation_id="corr-abc-123"
            )

            await client.send_message_async(
                input=message,
                entity_name=QUEUE_NAME
            )

            print(f"Message sent to queue '{QUEUE_NAME}':")
            print(f"  Content: {message.content_data[:50]}...")
            print(f"  Label: {message.label}")
            print(f"  Correlation ID: {message.correlation_id}")

        except ConnectorException as ex:
            print(f"Connector error (status {ex.status_code}): {ex}")
        except Exception as ex:
            print(f"Error: {ex}")


async def example_2_receive_message_from_queue():
    """Example 2: Receive a message from a Service Bus queue (auto-complete)."""
    print("\n=== Example 2: Receive Message from Queue (Auto-Complete) ===")

    if not QUEUE_NAME:
        print("Set SERVICEBUS_QUEUE_NAME environment variable.")
        return

    credential = DefaultAzureCredential()

    async with ServicebusClient(CONNECTION_RUNTIME_URL, credential) as client:
        try:
            result = await client.get_message_from_queue_async(
                queue_name=QUEUE_NAME
            )

            if result:
                print(f"Message received from queue '{QUEUE_NAME}':")
                print(f"  Message ID: {result.get('messageId', 'N/A')}")
                print(f"  Content: {result.get('contentData', 'N/A')}")
                print(f"  Content Type: {result.get('contentType', 'N/A')}")
            else:
                print(f"No messages available in queue '{QUEUE_NAME}'.")

        except ConnectorException as ex:
            print(f"Connector error (status {ex.status_code}): {ex}")
        except Exception as ex:
            print(f"Error: {ex}")


async def example_3_receive_with_peek_lock():
    """Example 3: Receive a message with peek-lock and complete it."""
    print("\n=== Example 3: Receive with Peek-Lock and Complete ===")

    if not QUEUE_NAME:
        print("Set SERVICEBUS_QUEUE_NAME environment variable.")
        return

    credential = DefaultAzureCredential()

    async with ServicebusClient(CONNECTION_RUNTIME_URL, credential) as client:
        try:
            # Receive message with peek-lock (message is locked, not removed)
            result = await client.get_new_message_from_queue_with_peek_lock_async(
                queue_name=QUEUE_NAME
            )

            if result:
                lock_token = result.get("lockToken")
                print("Message received with peek-lock:")
                print(f"  Lock Token: {lock_token}")
                print(f"  Content: {result.get('contentData', 'N/A')}")

                # Process the message...
                print("  Processing message...")

                # Complete the message (remove from queue)
                await client.complete_message_in_queue_async(
                    queue_name=QUEUE_NAME,
                    lock_token=lock_token
                )
                print("  Message completed successfully.")
            else:
                print(f"No messages available in queue '{QUEUE_NAME}'.")

        except ConnectorException as ex:
            print(f"Connector error (status {ex.status_code}): {ex}")
        except Exception as ex:
            print(f"Error: {ex}")


async def example_4_receive_and_abandon():
    """Example 4: Receive a message and abandon it (return to queue)."""
    print("\n=== Example 4: Receive and Abandon Message ===")

    if not QUEUE_NAME:
        print("Set SERVICEBUS_QUEUE_NAME environment variable.")
        return

    credential = DefaultAzureCredential()

    async with ServicebusClient(CONNECTION_RUNTIME_URL, credential) as client:
        try:
            result = await client.get_new_message_from_queue_with_peek_lock_async(
                queue_name=QUEUE_NAME
            )

            if result:
                lock_token = result.get("lockToken")
                print("Message received with peek-lock:")
                print(f"  Content: {result.get('contentData', 'N/A')}")

                # Abandon the message (return to queue for retry)
                await client.abandon_message_in_queue_async(
                    queue_name=QUEUE_NAME,
                    lock_token=lock_token
                )
                print("  Message abandoned and returned to queue.")
            else:
                print(f"No messages available in queue '{QUEUE_NAME}'.")

        except ConnectorException as ex:
            print(f"Connector error (status {ex.status_code}): {ex}")
        except Exception as ex:
            print(f"Error: {ex}")


async def example_5_send_message_to_topic():
    """Example 5: Send a message to a Service Bus topic."""
    print("\n=== Example 5: Send Message to Topic ===")

    if not TOPIC_NAME:
        print("Set SERVICEBUS_TOPIC_NAME environment variable.")
        print("Example: $env:SERVICEBUS_TOPIC_NAME = 'my-topic'")
        return

    credential = DefaultAzureCredential()

    async with ServicebusClient(CONNECTION_RUNTIME_URL, credential) as client:
        try:
            message = ServiceBusMessage(
                content_data=json.dumps({
                    "eventType": "user.created",
                    "userId": "USR-789",
                    "email": "user@example.com"
                }),
                content_type="application/json",
                label="user-event"
            )

            await client.send_message_async(
                input=message,
                entity_name=TOPIC_NAME
            )

            print(f"Message sent to topic '{TOPIC_NAME}':")
            print(f"  Content: {message.content_data}")

        except ConnectorException as ex:
            print(f"Connector error (status {ex.status_code}): {ex}")
        except Exception as ex:
            print(f"Error: {ex}")


async def example_6_receive_from_topic_subscription():
    """Example 6: Receive a message from a topic subscription."""
    print("\n=== Example 6: Receive from Topic Subscription ===")

    if not TOPIC_NAME or not SUBSCRIPTION_NAME:
        print("Set SERVICEBUS_TOPIC_NAME and SERVICEBUS_SUBSCRIPTION_NAME.")
        return

    credential = DefaultAzureCredential()

    async with ServicebusClient(CONNECTION_RUNTIME_URL, credential) as client:
        try:
            result = await client.get_message_from_topic_async(
                topic_name=TOPIC_NAME,
                subscription_name=SUBSCRIPTION_NAME
            )

            if result:
                print(f"Message received from '{TOPIC_NAME}/{SUBSCRIPTION_NAME}':")
                print(f"  Message ID: {result.get('messageId', 'N/A')}")
                print(f"  Content: {result.get('contentData', 'N/A')}")
            else:
                print(f"No messages in subscription '{SUBSCRIPTION_NAME}'.")

        except ConnectorException as ex:
            print(f"Connector error (status {ex.status_code}): {ex}")
        except Exception as ex:
            print(f"Error: {ex}")


async def example_7_dead_letter_message():
    """Example 7: Move a message to the dead-letter queue."""
    print("\n=== Example 7: Dead-Letter a Message ===")

    if not QUEUE_NAME:
        print("Set SERVICEBUS_QUEUE_NAME environment variable.")
        return

    credential = DefaultAzureCredential()

    async with ServicebusClient(CONNECTION_RUNTIME_URL, credential) as client:
        try:
            result = await client.get_new_message_from_queue_with_peek_lock_async(
                queue_name=QUEUE_NAME
            )

            if result:
                lock_token = result.get("lockToken")
                print("Message received:")
                print(f"  Content: {result.get('contentData', 'N/A')}")

                # Move to dead-letter queue
                await client.dead_letter_message_in_queue_async(
                    queue_name=QUEUE_NAME,
                    lock_token=lock_token,
                    dead_letter_reason="Processing failed",
                    dead_letter_error_description="Max retries exceeded"
                )
                print("  Message moved to dead-letter queue.")
            else:
                print(f"No messages available in queue '{QUEUE_NAME}'.")

        except ConnectorException as ex:
            print(f"Connector error (status {ex.status_code}): {ex}")
        except Exception as ex:
            print(f"Error: {ex}")


async def example_8_batch_receive():
    """Example 8: Receive multiple messages in batch."""
    print("\n=== Example 8: Batch Receive Messages ===")

    if not QUEUE_NAME:
        print("Set SERVICEBUS_QUEUE_NAME environment variable.")
        return

    credential = DefaultAzureCredential()

    async with ServicebusClient(CONNECTION_RUNTIME_URL, credential) as client:
        try:
            result = await client.get_messages_from_queue_async(
                queue_name=QUEUE_NAME,
                max_message_count="5"
            )

            if result:
                print(f"Received {len(result)} messages from '{QUEUE_NAME}':")
                for i, msg in enumerate(result, 1):
                    print(f"  {i}. {msg.get('contentData', 'N/A')[:50]}...")
            else:
                print(f"No messages available in queue '{QUEUE_NAME}'.")

        except ConnectorException as ex:
            print(f"Connector error (status {ex.status_code}): {ex}")
        except Exception as ex:
            print(f"Error: {ex}")


async def main():
    """Run all examples."""
    if not CONNECTION_RUNTIME_URL:
        print("Error: SERVICEBUS_CONNECTION_URL environment variable not set.")
        print("Set it to your connection runtime URL from Azure Portal.")
        print("\nExample:")
        print('$env:SERVICEBUS_CONNECTION_URL = ')
        print('  "https://[region].azure-apihub.net/apim/servicebus/[id]"')
        return

    print(f"Using connection URL: {CONNECTION_RUNTIME_URL[:50]}...")

    # Queue operations
    await example_1_send_message_to_queue()
    await example_2_receive_message_from_queue()
    await example_3_receive_with_peek_lock()
    await example_4_receive_and_abandon()

    # Topic operations
    await example_5_send_message_to_topic()
    await example_6_receive_from_topic_subscription()

    # Advanced operations
    await example_7_dead_letter_message()
    await example_8_batch_receive()

    print("\n=== All examples completed ===")


if __name__ == "__main__":
    asyncio.run(main())
