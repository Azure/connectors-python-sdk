# Copyright (c) Microsoft Corporation. All rights reserved.

"""
Zendesk sample for the Azure Connectors Python SDK

This sample demonstrates how to use the Zendesk client from the Azure Connectors Python SDK.

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
import os

from azure.identity import DefaultAzureCredential
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


def example_1_get_tables():
    """Example 1: List the available Zendesk tables (object types)."""
    print("\n=== Example 1: Get Tables ===")

    with DefaultAzureCredential() as credential:

        with ZendeskClient(CONNECTION_RUNTIME_URL, credential) as client:
            try:
                result = client.list_tables()

                tables = (result or {}).get("value", []) if isinstance(result, dict) else []
                print(f"Found {len(tables)} table(s).")
                for table in tables:
                    print(f"  - {table}")

            except ConnectorException as ex:
                print(f"Connector error: {ex}")
            except Exception as ex:
                print(f"Error: {ex}")


def example_2_get_items():
    """Example 2: Retrieve items from a Zendesk table."""
    print("\n=== Example 2: Get Items ===")

    with DefaultAzureCredential() as credential:

        with ZendeskClient(CONNECTION_RUNTIME_URL, credential) as client:
            try:
                items = [item for item in client.list_items(
                    table="tickets",
                    top=10,
                )]

                print(f"Retrieved {len(items)} item(s).")

            except ConnectorException as ex:
                print(f"Connector error: {ex}")
            except Exception as ex:
                print(f"Error: {ex}")


def example_3_create_item():
    """Example 3: Create a new item in a Zendesk table."""
    print("\n=== Example 3: Create Item ===")

    with DefaultAzureCredential() as credential:

        with ZendeskClient(CONNECTION_RUNTIME_URL, credential) as client:
            try:
                new_item = Item(
                    dynamic_properties={
                        "subject": "Sample ticket",
                        "description": "Created from the Zendesk SDK sample.",
                    },
                )

                result = client.post_item(input=new_item, table="tickets")
                print(f"Created item: {result}")

            except ConnectorException as ex:
                print(f"Connector error: {ex}")
            except Exception as ex:
                print(f"Error: {ex}")


def example_4_search_articles():
    """Example 4: Search Zendesk Help Center articles."""
    print("\n=== Example 4: Search Articles ===")

    with DefaultAzureCredential() as credential:

        with ZendeskClient(CONNECTION_RUNTIME_URL, credential) as client:
            try:
                result = client.list_search_articles(
                    query="password reset",
                    locale="en-us",
                )

                articles = (result or {}).get("results", []) if isinstance(result, dict) else []
                print(f"Found {len(articles)} article(s).")

            except ConnectorException as ex:
                print(f"Connector error: {ex}")
            except Exception as ex:
                print(f"Error: {ex}")


def main():
    """Run all examples."""
    if not CONNECTION_RUNTIME_URL:
        print("Error: ZENDESK_CONNECTION_URL environment variable not set.")
        print("Set it to your connection runtime URL from Azure Portal.")
        return

    print(f"Using connection URL: {CONNECTION_RUNTIME_URL[:50]}...")

    example_1_get_tables()
    example_2_get_items()
    example_3_create_item()
    example_4_search_articles()

    print("\n=== All examples completed ===")


if __name__ == "__main__":
    main()
