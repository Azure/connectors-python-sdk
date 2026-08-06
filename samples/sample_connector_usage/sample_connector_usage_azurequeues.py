# Copyright (c) Microsoft Corporation. All rights reserved.

"""
Azure Storage Queues Connector SDK Sample

This sample demonstrates how to use the Azure Storage Queues connector SDK
to interact with Azure Storage Queue messages.

Prerequisites:
1. Azure subscription with Azure Storage Queues connection
2. Azure Queues connection in Connector Namespaces (with access configured)
3. Connection runtime URL from Azure Portal
4. Azure Storage Account with queue storage

Installation:
    pip install azure-connectors

Usage:
    Set environment variables:
    $env:AZUREQUEUES_CONNECTION_URL = "https://...apihub.net/apim/azurequeues/..."
    $env:AZUREQUEUES_STORAGE_ACCOUNT = "<storage-account-name>"
    $env:AZUREQUEUES_QUEUE_NAME = "<queue-name>"

    python sample_connector_usage_azurequeues.py
"""

import asyncio
import os
from azure.identity.aio import DefaultAzureCredential
from azure.connectors import ConnectorException
from azure.connectors.azurequeues import (
    AzurequeuesClient,
    PutMessageInput,
)

# Connection runtime URL format:
# https://[region].azure-apihub.net/apim/azurequeues/[connection-id]
CONNECTION_RUNTIME_URL = os.environ.get(
    "AZUREQUEUES_CONNECTION_URL",
    ""
)

# Storage account name or queue endpoint
STORAGE_ACCOUNT = os.environ.get("AZUREQUEUES_STORAGE_ACCOUNT", "")

# Queue name for message operations
QUEUE_NAME = os.environ.get("AZUREQUEUES_QUEUE_NAME", "")


async def example_1_list_queues():
    """Example 1: List all queues in a storage account."""
    print("\n=== Example 1: List Queues ===")

    if not STORAGE_ACCOUNT:
        print("Set AZUREQUEUES_STORAGE_ACCOUNT environment variable.")
        print("Example: $env:AZUREQUEUES_STORAGE_ACCOUNT = 'mystorageaccount'")
        return

    credential = DefaultAzureCredential()

    async with AzurequeuesClient(CONNECTION_RUNTIME_URL, credential) as client:
        try:
            result = await client.list_queues_async(
                storage_account_name=STORAGE_ACCOUNT
            )

            if result:
                print(f"Queues in storage account '{STORAGE_ACCOUNT}':")
                # Result may be a list or dict with queue names
                if isinstance(result, list):
                    for queue in result:
                        if isinstance(queue, dict):
                            print(f"  - {queue.get('name', queue)}")
                        else:
                            print(f"  - {queue}")
                elif isinstance(result, dict):
                    print(f"  Response: {result}")
            else:
                print("No queues found or empty response.")

        except ConnectorException as ex:
            print(f"Connector error: {ex}")
        except Exception as ex:
            print(f"Error: {ex}")


async def example_2_create_queue():
    """Example 2: Create a new queue."""
    print("\n=== Example 2: Create Queue ===")

    new_queue_name = os.environ.get("AZUREQUEUES_NEW_QUEUE_NAME", "")
    if not STORAGE_ACCOUNT or not new_queue_name:
        print("Set environment variables to create a queue:")
        print("  $env:AZUREQUEUES_STORAGE_ACCOUNT = '<storage-account-name>'")
        print("  $env:AZUREQUEUES_NEW_QUEUE_NAME = 'my-new-queue'")
        return

    credential = DefaultAzureCredential()

    async with AzurequeuesClient(CONNECTION_RUNTIME_URL, credential) as client:
        try:
            result = await client.put_queue_async(
                storage_account_name=STORAGE_ACCOUNT,
                queue_name=new_queue_name
            )

            print(f"Queue '{new_queue_name}' created successfully.")
            if result:
                print(f"Response: {result}")

        except ConnectorException as ex:
            print(f"Connector error: {ex}")
        except Exception as ex:
            print(f"Error: {ex}")


async def example_3_put_message():
    """Example 3: Put a message on a queue."""
    print("\n=== Example 3: Put Message ===")

    if not STORAGE_ACCOUNT or not QUEUE_NAME:
        print("Set environment variables to put a message:")
        print("  $env:AZUREQUEUES_STORAGE_ACCOUNT = '<storage-account-name>'")
        print("  $env:AZUREQUEUES_QUEUE_NAME = '<queue-name>'")
        return

    credential = DefaultAzureCredential()

    async with AzurequeuesClient(CONNECTION_RUNTIME_URL, credential) as client:
        try:
            # Create the message input
            message_input = PutMessageInput(
                additional_properties={
                    "message": "Hello from Azure Connectors SDK for Python!"
                }
            )

            await client.put_message_async(
                input=message_input,
                storage_account_name=STORAGE_ACCOUNT,
                queue_name=QUEUE_NAME
            )

            print(f"Message sent to queue '{QUEUE_NAME}':")
            print(f"  Content: {message_input.additional_properties.get('message')}")

        except ConnectorException as ex:
            print(f"Connector error: {ex}")
        except Exception as ex:
            print(f"Error: {ex}")


async def example_4_get_messages():
    """Example 4: Get messages from a queue."""
    print("\n=== Example 4: Get Messages ===")

    if not STORAGE_ACCOUNT or not QUEUE_NAME:
        print("Set environment variables to get messages:")
        print("  $env:AZUREQUEUES_STORAGE_ACCOUNT = '<storage-account-name>'")
        print("  $env:AZUREQUEUES_QUEUE_NAME = '<queue-name>'")
        return

    credential = DefaultAzureCredential()

    async with AzurequeuesClient(CONNECTION_RUNTIME_URL, credential) as client:
        try:
            result = await client.get_messages_async(
                storage_account_name=STORAGE_ACCOUNT,
                queue_name=QUEUE_NAME,
                numofmessages="5",  # Get up to 5 messages
                visibilitytimeout="30"  # Hide messages for 30 seconds
            )

            if result:
                queue_messages_list = result.get("QueueMessagesList", {})
                messages = queue_messages_list.get("QueueMessage", [])
                if isinstance(messages, list):
                    print(f"Retrieved {len(messages)} message(s) from '{QUEUE_NAME}':")
                    for i, msg in enumerate(messages, 1):
                        print(f"  Message {i}:")
                        print(f"    ID: {msg.get('MessageId', 'N/A')}")
                        print(f"    Text: {msg.get('MessageText', 'N/A')[:50]}...")
                        print(f"    Pop Receipt: {msg.get('PopReceipt', 'N/A')[:20]}...")
                        print(f"    Dequeue Count: {msg.get('DequeueCount', 'N/A')}")
                        print(f"    Next Visible: {msg.get('TimeNextVisible', 'N/A')}")
                else:
                    print(f"Response: {result}")
            else:
                print("No messages found or queue is empty.")

        except ConnectorException as ex:
            print(f"Connector error: {ex}")
        except Exception as ex:
            print(f"Error: {ex}")


async def example_5_delete_message():
    """Example 5: Delete a message from a queue."""
    print("\n=== Example 5: Delete Message ===")

    message_id = os.environ.get("AZUREQUEUES_MESSAGE_ID", "")
    pop_receipt = os.environ.get("AZUREQUEUES_POP_RECEIPT", "")

    if not STORAGE_ACCOUNT or not QUEUE_NAME or not message_id or not pop_receipt:
        print("Set environment variables to delete a message:")
        print("  $env:AZUREQUEUES_STORAGE_ACCOUNT = '<storage-account-name>'")
        print("  $env:AZUREQUEUES_QUEUE_NAME = '<queue-name>'")
        print("  $env:AZUREQUEUES_MESSAGE_ID = '<message-id>'")
        print("  $env:AZUREQUEUES_POP_RECEIPT = '<pop-receipt>'")
        print("\nNote: Get message ID and pop receipt from Example 4.")
        return

    credential = DefaultAzureCredential()

    async with AzurequeuesClient(CONNECTION_RUNTIME_URL, credential) as client:
        try:
            await client.delete_message_async(
                storage_account_name=STORAGE_ACCOUNT,
                queue_name=QUEUE_NAME,
                message_id=message_id,
                popreceipt=pop_receipt
            )

            print(f"Message '{message_id}' deleted from queue '{QUEUE_NAME}'.")

        except ConnectorException as ex:
            print(f"Connector error: {ex}")
        except Exception as ex:
            print(f"Error: {ex}")


async def main():
    """Run all examples."""
    print("Azure Storage Queues Connector SDK - Sample Usage")
    print("=" * 60)

    if not CONNECTION_RUNTIME_URL:
        print("\nWARNING: AZUREQUEUES_CONNECTION_URL environment variable not set.")
        print("Set it to your connection runtime URL to run actual API calls.")
        print("Format: https://[region].azure-apihub.net/apim/azurequeues/[id]")
        return

    await example_1_list_queues()
    await example_2_create_queue()
    await example_3_put_message()
    await example_4_get_messages()
    await example_5_delete_message()

    print("\n" + "=" * 60)
    print("Sample completed!")


if __name__ == "__main__":
    asyncio.run(main())
