# Copyright (c) Microsoft Corporation. All rights reserved.

"""
Yammer (Viva Engage) Connector SDK Sample

This sample demonstrates how to use the Yammer connector SDK to interact with
Viva Engage (formerly Yammer) networks, groups, messages, and users.

Prerequisites:
1. Azure subscription with Yammer connection
2. Yammer connection in Connector Namespaces
3. Connection runtime URL from Azure Portal

Installation:
    pip install azure-connectors

Usage:
    Set environment variable:
    $env:YAMMER_CONNECTION_URL = "https://[region].azure-apihub.net/apim/yammer/[connection-id]"

    python sample_connector_usage_yammer.py
"""

import asyncio
import os
from azure.identity.aio import DefaultAzureCredential
from azure.connectors import ConnectorException
from azure.connectors.yammer import (
    YammerClient,
    PostOperationRequest,
)

# Connection runtime URL format:
# https://[region].azure-apihub.net/apim/yammer/[connection-id]
CONNECTION_RUNTIME_URL = os.environ.get(
    "YAMMER_CONNECTION_URL",
    ""
)


async def example_1_get_networks():
    """Example 1: Get all networks the user belongs to."""
    print("\n=== Example 1: Get Networks ===")

    credential = DefaultAzureCredential()

    async with YammerClient(CONNECTION_RUNTIME_URL, credential) as client:
        try:
            networks = await client.get_networks_async()

            if networks:
                print(f"Found {len(networks)} network(s):")
                for network in networks:
                    print(f"  - {network.get('name')} (ID: {network.get('id')})")
            else:
                print("No networks found.")

        except ConnectorException as ex:
            print(f"Connector error: {ex}")
        except Exception as ex:
            print(f"Error: {ex}")


async def example_2_get_groups():
    """Example 2: Get groups in the network."""
    print("\n=== Example 2: Get Groups ===")

    credential = DefaultAzureCredential()

    async with YammerClient(CONNECTION_RUNTIME_URL, credential) as client:
        try:
            # Get only groups the user belongs to
            groups = await client.get_groups_async(mine="1")

            if groups:
                print(f"Found {len(groups)} group(s):")
                for group in groups[:5]:  # Show first 5
                    print(f"  - {group.get('full_name')} (ID: {group.get('id')})")
            else:
                print("No groups found.")

        except ConnectorException as ex:
            print(f"Connector error: {ex}")
        except Exception as ex:
            print(f"Error: {ex}")


async def example_3_get_messages():
    """Example 3: Get messages from the network."""
    print("\n=== Example 3: Get All Messages ===")

    credential = DefaultAzureCredential()

    async with YammerClient(CONNECTION_RUNTIME_URL, credential) as client:
        try:
            # Get recent messages (limit to 10)
            result = await client.get_all_messages_async(limit="10")

            if result and result.get("value"):
                messages = result["value"]
                print(f"Found {len(messages)} message(s):")
                for msg in messages[:3]:  # Show first 3
                    excerpt = msg.get("content_excerpt", "")[:50]
                    print(f"  - ID {msg.get('id')}: {excerpt}...")
            else:
                print("No messages found.")

        except ConnectorException as ex:
            print(f"Connector error: {ex}")
        except Exception as ex:
            print(f"Error: {ex}")


async def example_4_get_following_feed():
    """Example 4: Get messages from the Following feed."""
    print("\n=== Example 4: Get Following Feed ===")

    credential = DefaultAzureCredential()

    async with YammerClient(CONNECTION_RUNTIME_URL, credential) as client:
        try:
            result = await client.get_messages_following_async(limit="5")

            if result and result.get("value"):
                messages = result["value"]
                print(f"Found {len(messages)} message(s) in following feed:")
                for msg in messages[:3]:
                    sender_id = msg.get("sender_id")
                    excerpt = msg.get("content_excerpt", "")[:40]
                    print(f"  - From user {sender_id}: {excerpt}...")
            else:
                print("No messages in following feed.")

        except ConnectorException as ex:
            print(f"Connector error: {ex}")
        except Exception as ex:
            print(f"Error: {ex}")


async def example_5_post_message():
    """Example 5: Post a message to All Company feed."""
    print("\n=== Example 5: Post Message ===")

    credential = DefaultAzureCredential()

    async with YammerClient(CONNECTION_RUNTIME_URL, credential) as client:
        try:
            # Create message request (group_id=0 posts to All Company)
            message = PostOperationRequest(
                group_id=0,
                body="Hello from the Azure Connectors Python SDK!",
                title="SDK Test Message"
            )

            result = await client.post_message_async(input=message)

            if result:
                print("Message posted successfully!")
                print(f"  Message ID: {result.get('id')}")
                print(f"  Web URL: {result.get('web_url')}")
            else:
                print("Message posted (no response body).")

        except ConnectorException as ex:
            print(f"Connector error: {ex}")
        except Exception as ex:
            print(f"Error: {ex}")


async def example_6_get_user_details():
    """Example 6: Get user profile details."""
    print("\n=== Example 6: Get User Details ===")

    credential = DefaultAzureCredential()

    async with YammerClient(CONNECTION_RUNTIME_URL, credential) as client:
        try:
            # Replace with an actual user ID
            user_id = "current"  # 'current' gets the authenticated user
            user = await client.get_user_details_by_id_async(user_id=user_id)

            if user:
                print("User details:")
                print(f"  Name: {user.get('full_name')}")
                print(f"  Email: {user.get('email')}")
                print(f"  Title: {user.get('job_title')}")
                print(f"  Location: {user.get('location')}")
            else:
                print("User not found.")

        except ConnectorException as ex:
            print(f"Connector error: {ex}")
        except Exception as ex:
            print(f"Error: {ex}")


async def main():
    """Run all examples."""
    if not CONNECTION_RUNTIME_URL:
        print("Error: YAMMER_CONNECTION_URL environment variable not set.")
        print("Set it to your connection runtime URL from Azure Portal.")
        return

    print(f"Using connection URL: {CONNECTION_RUNTIME_URL[:50]}...")

    await example_1_get_networks()
    await example_2_get_groups()
    await example_3_get_messages()
    await example_4_get_following_feed()
    # Uncomment to test posting (be careful in production!)
    # await example_5_post_message()
    await example_6_get_user_details()

    print("\n=== All examples completed ===")


if __name__ == "__main__":
    asyncio.run(main())
