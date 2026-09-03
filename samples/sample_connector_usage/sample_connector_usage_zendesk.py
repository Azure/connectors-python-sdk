# Copyright (c) Microsoft Corporation. All rights reserved.

"""
Zendesk Connector SDK Sample

This sample demonstrates how to use the Zendesk connector SDK.

Prerequisites:
1. Azure subscription with a Zendesk connection
2. Zendesk connection in Connector Namespaces
3. Connection runtime URL from Azure Portal

Installation:
    pip install azure-connectors

Usage:
    Set environment variable:
    $env:ZENDESK_CONNECTION_URL = "https://[region].azure-apihub.net/apim/zendesk/[connection-id]"

    python sample_connector_usage_zendesk.py
"""

import asyncio
import os

from azure.identity.aio import DefaultAzureCredential
from azure.connectors import ConnectorException
from azure.connectors.zendesk import (
    Item,
    ZendeskClient,
)

# Connection runtime URL format:
# https://[region].azure-apihub.net/apim/zendesk/[connection-id]
CONNECTION_RUNTIME_URL = os.environ.get(
    "ZENDESK_CONNECTION_URL",
    "",
)


async def example_1_get_tables():
    """Example 1: List the available Zendesk tables (object types)."""
    print("\n=== Example 1: Get Tables ===")

    credential = DefaultAzureCredential()

    async with ZendeskClient(CONNECTION_RUNTIME_URL, credential) as client:
        try:
            result = await client.get_tables_async()

            tables = (result or {}).get("value", []) if isinstance(result, dict) else []
            print(f"Found {len(tables)} table(s).")
            for table in tables:
                print(f"  - {table}")

        except ConnectorException as ex:
            print(f"Connector error: {ex}")
        except Exception as ex:
            print(f"Error: {ex}")


async def example_2_get_items():
    """Example 2: Retrieve items from a Zendesk table."""
    print("\n=== Example 2: Get Items ===")

    credential = DefaultAzureCredential()

    async with ZendeskClient(CONNECTION_RUNTIME_URL, credential) as client:
        try:
            result = await client.get_items_async(
                table="tickets",
                top=10,
            )

            items = (result or {}).get("value", []) if isinstance(result, dict) else []
            print(f"Retrieved {len(items)} item(s).")

        except ConnectorException as ex:
            print(f"Connector error: {ex}")
        except Exception as ex:
            print(f"Error: {ex}")


async def example_3_create_item():
    """Example 3: Create a new item in a Zendesk table."""
    print("\n=== Example 3: Create Item ===")

    credential = DefaultAzureCredential()

    async with ZendeskClient(CONNECTION_RUNTIME_URL, credential) as client:
        try:
            new_item = Item(
                dynamic_properties={
                    "subject": "Sample ticket",
                    "description": "Created from the Zendesk SDK sample.",
                },
            )

            result = await client.post_item_async(input=new_item, table="tickets")
            print(f"Created item: {result}")

        except ConnectorException as ex:
            print(f"Connector error: {ex}")
        except Exception as ex:
            print(f"Error: {ex}")


async def example_4_search_articles():
    """Example 4: Search Zendesk Help Center articles."""
    print("\n=== Example 4: Search Articles ===")

    credential = DefaultAzureCredential()

    async with ZendeskClient(CONNECTION_RUNTIME_URL, credential) as client:
        try:
            result = await client.search_articles_async(
                query="password reset",
                locale="en-us",
            )

            articles = (result or {}).get("results", []) if isinstance(result, dict) else []
            print(f"Found {len(articles)} article(s).")

        except ConnectorException as ex:
            print(f"Connector error: {ex}")
        except Exception as ex:
            print(f"Error: {ex}")


async def main():
    """Run all examples."""
    if not CONNECTION_RUNTIME_URL:
        print("Error: ZENDESK_CONNECTION_URL environment variable not set.")
        print("Set it to your connection runtime URL from Azure Portal.")
        return

    print(f"Using connection URL: {CONNECTION_RUNTIME_URL[:50]}...")

    await example_1_get_tables()
    await example_2_get_items()
    await example_3_create_item()
    await example_4_search_articles()

    print("\n=== All examples completed ===")


if __name__ == "__main__":
    asyncio.run(main())
