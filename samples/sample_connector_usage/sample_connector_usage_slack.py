"""
Slack Connector SDK Sample

This sample demonstrates how to use the Slack connector SDK.

Prerequisites:
1. Azure subscription with Slack connection
2. Slack connection in Connector Namespaces
3. Connection runtime URL from Azure Portal

Installation:
    pip install azure-connectors

Usage:
    Set environment variable:
    $env:SLACK_CONNECTION_URL = "https://[region].azure-apihub.net/apim/slack/[connection-id]"

    python sample_connector_usage_slack.py
"""

import asyncio
import os

from azure.identity.aio import DefaultAzureCredential

from azure.connectors import ConnectorException
from azure.connectors.slack import PostMessageRequest, SlackClient


# Connection runtime URL format:
# https://[region].azure-apihub.net/apim/slack/[connection-id]
CONNECTION_RUNTIME_URL = os.environ.get("SLACK_CONNECTION_URL", "")


async def example_1_list_channels() -> None:
    """Example 1: List channels."""
    print("\n=== Example 1: List Channels ===")

    credential = DefaultAzureCredential()
    async with SlackClient(CONNECTION_RUNTIME_URL, credential) as client:
        channels_response = await client.list_channels_async()
        channels = channels_response.get("value", []) if channels_response else []

        print(f"Found {len(channels)} channels")
        for channel in channels[:5]:
            print(f"  - {channel.get('name')} ({channel.get('id')})")


async def example_2_create_channel() -> None:
    """Example 2: Create a channel."""
    print("\n=== Example 2: Create Channel ===")

    credential = DefaultAzureCredential()
    async with SlackClient(CONNECTION_RUNTIME_URL, credential) as client:
        created = await client.create_channel_async(
            name="sdk-sample-channel",
            is_private="false",
        )
        channel = created.get("channel", {}) if created else {}
        print(f"Created channel: {channel.get('name')} ({channel.get('id')})")


async def example_3_post_message() -> None:
    """Example 3: Post a message to a channel."""
    print("\n=== Example 3: Post Message ===")

    credential = DefaultAzureCredential()
    async with SlackClient(CONNECTION_RUNTIME_URL, credential) as client:
        payload = PostMessageRequest(channel="#general", text="Hello from Slack Python SDK sample")
        posted = await client.post_message_async(input=payload)
        print(f"Posted: ok={posted.get('ok') if posted else None}, ts={posted.get('ts') if posted else None}")


async def main() -> None:
    """Run Slack connector examples."""
    if not CONNECTION_RUNTIME_URL:
        print("Error: SLACK_CONNECTION_URL environment variable not set.")
        print("Set it to your connection runtime URL from Azure Portal.")
        return

    print("Slack Connector SDK - Sample Usage")
    print("=" * 50)

    try:
        await example_1_list_channels()
        # Uncomment after confirming your app has channel-create permission.
        # await example_2_create_channel()
        await example_3_post_message()

    except ConnectorException as ex:
        print(f"Connector error: {ex}")
    except Exception as ex:
        print(f"Unexpected error: {ex}")


if __name__ == "__main__":
    asyncio.run(main())
