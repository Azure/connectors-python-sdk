# Copyright (c) Microsoft Corporation. All rights reserved.

"""
Pipedrive Connector SDK Sample

This sample demonstrates how to use the Pipedrive connector SDK.

Prerequisites:
1. Azure subscription with a Pipedrive connection
2. Pipedrive connection in Connector Namespaces
3. Connection runtime URL from Azure Portal

Installation:
    pip install azure-connectors

Usage:
    Set environment variable:
    $env:PIPEDRIVE_CONNECTION_URL = "<connection-runtime-url>"

    python sample_connector_usage_pipedrive.py
"""

import asyncio
import os

from azure.identity.aio import DefaultAzureCredential
from azure.connectors import ConnectorException
from azure.connectors.pipedrive import (
    AddDealRequest,
    PipedriveClient,
)

# Connection runtime URL format:
# https://[region].azure-apihub.net/apim/pipedrive/[connection-id]
CONNECTION_RUNTIME_URL = os.environ.get(
    "PIPEDRIVE_CONNECTION_URL",
    "",
)


async def example_1_list_deals():
    """Example 1: List deals for the authorized account."""
    print("\n=== Example 1: List Deals ===")

    credential = DefaultAzureCredential()

    async with PipedriveClient(CONNECTION_RUNTIME_URL, credential) as client:
        try:
            result = await client.list_deals_async()

            deals = (result or {}).get("data", []) if isinstance(result, dict) else []
            print(f"Found {len(deals)} deal(s).")

        except ConnectorException as ex:
            print(f"Connector error: {ex}")
        except Exception as ex:
            print(f"Error: {ex}")


async def example_2_get_deal():
    """Example 2: Retrieve a single deal by id."""
    print("\n=== Example 2: Get Deal ===")

    credential = DefaultAzureCredential()

    async with PipedriveClient(CONNECTION_RUNTIME_URL, credential) as client:
        try:
            result = await client.get_deal_async(deal_id=1)
            print(f"Deal: {result}")

        except ConnectorException as ex:
            print(f"Connector error: {ex}")
        except Exception as ex:
            print(f"Error: {ex}")


async def example_3_add_deal():
    """Example 3: Create a new deal for the authorized account."""
    print("\n=== Example 3: Add Deal ===")

    credential = DefaultAzureCredential()

    async with PipedriveClient(CONNECTION_RUNTIME_URL, credential) as client:
        try:
            new_deal = AddDealRequest(
                title="Sample deal",
            )

            result = await client.add_deal_async(input=new_deal)
            print(f"Created deal: {result}")

        except ConnectorException as ex:
            print(f"Connector error: {ex}")
        except Exception as ex:
            print(f"Error: {ex}")


async def main():
    """Run all examples."""
    if not CONNECTION_RUNTIME_URL:
        print("Error: PIPEDRIVE_CONNECTION_URL environment variable not set.")
        print("Set it to your connection runtime URL from Azure Portal.")
        return

    print(f"Using connection URL: {CONNECTION_RUNTIME_URL[:50]}...")

    await example_1_list_deals()
    await example_2_get_deal()
    await example_3_add_deal()

    print("\n=== All examples completed ===")


if __name__ == "__main__":
    asyncio.run(main())
