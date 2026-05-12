# Copyright (c) Microsoft Corporation. All rights reserved.

"""
IBM MQ Connector SDK Sample

This sample demonstrates how to use the IBM MQ connector SDK.

Prerequisites:
1. Azure subscription with IBM MQ connection
2. IBM MQ connection in Azure Logic Apps
3. Connection runtime URL from Azure Portal

Note: IBM MQ uses parameter-based auth (server, queue manager, channel, credentials).
The connection must be created with parameterValues — no OAuth consent flow.

Installation:
    pip install azure-connectors

Usage:
    Set environment variables:
    $env:MQ_CONNECTION_URL = "https://[region].azure-apihub.net/apim/mq/[connection-id]"

    python sample_connector_usage_mq.py
"""

import asyncio
import os
from azure.identity.aio import DefaultAzureCredential
from azure.connectors import ConnectorException
from azure.connectors.mq import (
    MqClient,
    SendValidDataOptions,
    SingleGetValidOptions,
    MultipleGetValidOptions,
)

# Connection runtime URL format:
# https://[region].azure-apihub.net/apim/mq/[connection-id]
CONNECTION_RUNTIME_URL = os.environ.get(
    "MQ_CONNECTION_URL",
    ""
)

# Optional: Override queue name (otherwise uses connection default)
DEFAULT_QUEUE = os.environ.get("TEST_MQ_QUEUE", None)


async def example_1_send_message():
    """Example 1: Send a message to an IBM MQ queue."""
    print("\n=== Example 1: Send Message ===")

    message_content = os.environ.get(
        "TEST_MQ_MESSAGE",
        "Hello from Azure Connectors SDK for Python!"
    )

    credential = DefaultAzureCredential()

    async with MqClient(CONNECTION_RUNTIME_URL, credential) as client:
        try:
            options = SendValidDataOptions(
                message=message_content,
                queue=DEFAULT_QUEUE,
            )

            result = await client.send_async(input=options)

            if result:
                print("Message sent successfully:")
                print(f"  Message ID: {result.get('messageId', 'N/A')}")
                print(f"  Correlation ID: {result.get('correlationId', 'N/A')}")
            else:
                print("Message sent (no response returned).")

        except ConnectorException as ex:
            print(f"Connector error: {ex}")
        except Exception as ex:
            print(f"Error: {ex}")


async def example_2_browse_message():
    """Example 2: Browse (peek) a single message without removing it."""
    print("\n=== Example 2: Browse Message ===")

    credential = DefaultAzureCredential()

    async with MqClient(CONNECTION_RUNTIME_URL, credential) as client:
        try:
            options = SingleGetValidOptions(
                queue=DEFAULT_QUEUE,
                include_info="true",
            )

            result = await client.read_async(input=options)

            if result:
                print("Browsed message:")
                print(f"  Message ID: {result.get('messageId', 'N/A')}")
                print(f"  Correlation ID: {result.get('correlationId', 'N/A')}")
                message_data = result.get("messageData", "")
                preview = message_data[:100] if message_data else "(empty)"
                print(f"  Data preview: {preview}")
            else:
                print("No message available in queue.")

        except ConnectorException as ex:
            print(f"Connector error: {ex}")
        except Exception as ex:
            print(f"Error: {ex}")


async def example_3_browse_messages_batch():
    """Example 3: Browse multiple messages without removing them."""
    print("\n=== Example 3: Browse Messages (Batch) ===")

    batch_size = int(os.environ.get("TEST_MQ_BATCH_SIZE", "10"))

    credential = DefaultAzureCredential()

    async with MqClient(CONNECTION_RUNTIME_URL, credential) as client:
        try:
            options = MultipleGetValidOptions(
                queue=DEFAULT_QUEUE,
                batch_size=batch_size,
                include_info="true",
            )

            result = await client.read_all_async(input=options)

            if result and isinstance(result, list):
                print(f"Browsed {len(result)} messages:")
                for i, msg in enumerate(result[:5]):  # Show first 5
                    msg_id = msg.get("messageId", "N/A")
                    data = msg.get("messageData", "")
                    preview = data[:50] if data else "(empty)"
                    print(f"  {i + 1}. ID: {msg_id}, Data: {preview}...")
            else:
                print("No messages available in queue.")

        except ConnectorException as ex:
            print(f"Connector error: {ex}")
        except Exception as ex:
            print(f"Error: {ex}")


async def example_4_receive_message():
    """Example 4: Receive (destructive get) a single message from the queue."""
    print("\n=== Example 4: Receive Message (Destructive) ===")

    credential = DefaultAzureCredential()

    async with MqClient(CONNECTION_RUNTIME_URL, credential) as client:
        try:
            options = SingleGetValidOptions(
                queue=DEFAULT_QUEUE,
                include_info="true",
            )

            result = await client.receive_async(input=options)

            if result:
                print("Received message (removed from queue):")
                print(f"  Message ID: {result.get('messageId', 'N/A')}")
                print(f"  Correlation ID: {result.get('correlationId', 'N/A')}")
                message_data = result.get("messageData", "")
                preview = message_data[:100] if message_data else "(empty)"
                print(f"  Data preview: {preview}")
            else:
                print("No message available in queue.")

        except ConnectorException as ex:
            print(f"Connector error: {ex}")
        except Exception as ex:
            print(f"Error: {ex}")


async def example_5_delete_message():
    """Example 5: Delete a single message from the queue."""
    print("\n=== Example 5: Delete Message ===")

    credential = DefaultAzureCredential()

    async with MqClient(CONNECTION_RUNTIME_URL, credential) as client:
        try:
            options = SingleGetValidOptions(
                queue=DEFAULT_QUEUE,
            )

            result = await client.delete_async(input=options)

            if result:
                print("Deleted message:")
                print(f"  Message ID: {result.get('messageId', 'N/A')}")
                print("  Success: True")
            else:
                print("No message available to delete.")

        except ConnectorException as ex:
            print(f"Connector error: {ex}")
        except Exception as ex:
            print(f"Error: {ex}")


async def main():
    """Run all examples."""
    print("IBM MQ Connector SDK - Sample Usage")
    print("=" * 60)

    if not CONNECTION_RUNTIME_URL:
        print("\nWARNING: MQ_CONNECTION_URL environment variable not set.")
        print("Set it to your connection runtime URL to run actual API calls.")
        print("Format: https://[region].azure-apihub.net/apim/mq/[connection-id]")
        return

    await example_1_send_message()
    await example_2_browse_message()
    await example_3_browse_messages_batch()
    await example_4_receive_message()
    await example_5_delete_message()

    print("\n" + "=" * 60)
    print("Sample completed!")


if __name__ == "__main__":
    asyncio.run(main())
