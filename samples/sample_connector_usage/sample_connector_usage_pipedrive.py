# Copyright (c) Microsoft Corporation. All rights reserved.

"""
Pipedrive sample for the Azure Connectors Python SDK

This sample demonstrates how to use the Pipedrive client from the Azure Connectors Python SDK.

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
import os

from azure.identity import DefaultAzureCredential
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


def example_1_list_deals():
    """Example 1: List deals for the authorized account."""
    print("\n=== Example 1: List Deals ===")

    with DefaultAzureCredential() as credential:

        with PipedriveClient(CONNECTION_RUNTIME_URL, credential) as client:
            try:
                result = client.list_deals()

                deals = (result or {}).get("data", []) if isinstance(result, dict) else []
                print(f"Found {len(deals)} deal(s).")

            except ConnectorException as ex:
                print(f"Connector error: {ex}")
            except Exception as ex:
                print(f"Error: {ex}")


def example_2_get_deal():
    """Example 2: Retrieve a single deal by id."""
    print("\n=== Example 2: Get Deal ===")

    with DefaultAzureCredential() as credential:

        with PipedriveClient(CONNECTION_RUNTIME_URL, credential) as client:
            try:
                result = client.get_deal(deal_id=1)
                print(f"Deal: {result}")

            except ConnectorException as ex:
                print(f"Connector error: {ex}")
            except Exception as ex:
                print(f"Error: {ex}")


def example_3_add_deal():
    """Example 3: Create a new deal for the authorized account."""
    print("\n=== Example 3: Add Deal ===")

    with DefaultAzureCredential() as credential:

        with PipedriveClient(CONNECTION_RUNTIME_URL, credential) as client:
            try:
                new_deal = AddDealRequest(
                    title="Sample deal",
                )

                result = client.add_deal(input=new_deal)
                print(f"Created deal: {result}")

            except ConnectorException as ex:
                print(f"Connector error: {ex}")
            except Exception as ex:
                print(f"Error: {ex}")


def main():
    """Run all examples."""
    if not CONNECTION_RUNTIME_URL:
        print("Error: PIPEDRIVE_CONNECTION_URL environment variable not set.")
        print("Set it to your connection runtime URL from Azure Portal.")
        return

    print(f"Using connection URL: {CONNECTION_RUNTIME_URL[:50]}...")

    example_1_list_deals()
    example_2_get_deal()
    example_3_add_deal()

    print("\n=== All examples completed ===")


if __name__ == "__main__":
    main()
