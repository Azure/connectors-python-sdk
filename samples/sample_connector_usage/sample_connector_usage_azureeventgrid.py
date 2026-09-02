# Copyright (c) Microsoft Corporation. All rights reserved.

"""
Azure Event Grid Connector SDK Sample

This sample demonstrates how to use the Azure Event Grid connector SDK.

Prerequisites:
1. Azure subscription with an Azure Event Grid connection
2. Azure Event Grid connection in Connector Namespaces
3. Connection runtime URL from Azure Portal

Installation:
    pip install azure-connectors

Usage:
    Set environment variable:
    $env:AZUREEVENTGRID_CONNECTION_URL = (
        "https://[region].azure-apihub.net/apim/azureeventgrid/[connection-id]"
    )

    python sample_connector_usage_azureeventgrid.py
"""

import asyncio
import os

from azure.identity.aio import DefaultAzureCredential
from azure.connectors.azureeventgrid import (
    AzureeventgridClient,
    EventRequest,
)

# Connection runtime URL format:
# https://[region].azure-apihub.net/apim/azureeventgrid/[connection-id]
CONNECTION_RUNTIME_URL = os.environ.get(
    "AZUREEVENTGRID_CONNECTION_URL",
    "",
)


async def example_1_list_subscriptions():
    """Example 1: List Azure subscriptions available to the principal."""
    print("\n=== Example 1: List Subscriptions ===")

    credential = DefaultAzureCredential()

    async with AzureeventgridClient(CONNECTION_RUNTIME_URL, credential) as client:
        result = await client.subscriptions_list_async()
        subscriptions = result.get("value", []) if result else []

        print(f"Found {len(subscriptions)} subscription(s).")
        for subscription in subscriptions[:10]:
            display_name = subscription.get("displayName", "N/A")
            subscription_id = subscription.get("subscriptionId", "N/A")
            print(f"  - {display_name} ({subscription_id})")


async def example_2_list_topic_types():
    """Example 2: List Event Grid topic types."""
    print("\n=== Example 2: List Topic Types ===")

    credential = DefaultAzureCredential()

    async with AzureeventgridClient(CONNECTION_RUNTIME_URL, credential) as client:
        result = await client.topic_types_list_async()
        topic_types = result.get("value", []) if result else []

        print(f"Found {len(topic_types)} topic type(s).")
        for topic_type in topic_types[:10]:
            print(f"  - {topic_type.get('name', 'N/A')}")


async def example_3_build_event_request():
    """Example 3: Build an Event Grid request payload."""
    print("\n=== Example 3: Build Event Request ===")

    subscription_id = os.environ.get("AZUREEVENTGRID_SUBSCRIPTION_ID", "")
    resource_type = os.environ.get("AZUREEVENTGRID_RESOURCE_TYPE", "")

    if not (subscription_id and resource_type):
        print(
            "Set AZUREEVENTGRID_SUBSCRIPTION_ID and AZUREEVENTGRID_RESOURCE_TYPE "
            "to run this example."
        )
        return

    request = EventRequest(properties={
        "subscriptionId": subscription_id,
        "resourceType": resource_type,
        "subscriptionName": "sdk-sample-subscription",
    })
    print(f"Prepared Event Grid request properties: {request.properties}")
    print("The generated client exposes discovery operations, not subscription creation.")


async def main():
    """Run all Azure Event Grid connector examples."""
    if not CONNECTION_RUNTIME_URL:
        print("Error: AZUREEVENTGRID_CONNECTION_URL environment variable is not set.")
        print("Set it to your Azure Event Grid connector runtime URL from Azure Portal.")
        return

    print(f"Using connection URL: {CONNECTION_RUNTIME_URL[:50]}...")

    await example_1_list_subscriptions()
    await example_2_list_topic_types()
    await example_3_build_event_request()

    print("\n=== Azure Event Grid sample completed ===")


if __name__ == "__main__":
    asyncio.run(main())
