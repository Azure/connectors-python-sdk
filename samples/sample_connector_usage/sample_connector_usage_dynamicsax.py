# Copyright (c) Microsoft Corporation. All rights reserved.

"""
Dynamics 365 for Finance and Operations (Dynamics AX) Connector SDK Sample

This sample demonstrates how to use the Dynamics AX connector SDK.

Prerequisites:
1. Azure subscription with a Dynamics AX connection
2. Dynamics AX connection in Connector Namespaces
3. Connection runtime URL from Azure Portal

Installation:
    pip install azure-connectors

Usage:
    Set environment variables:
    $env:DYNAMICSAX_CONNECTION_URL = (
        "https://[region].azure-apihub.net/apim/dynamicsax/[connection-id]"
    )
    $env:DYNAMICSAX_DATASET = "https://[your-instance].operations.dynamics.com"

    python sample_connector_usage_dynamicsax.py
"""
import os

from azure.identity import DefaultAzureCredential
from azure.connectors import ConnectorException
from azure.connectors.dynamicsax import (
    DynamicsaxClient,
    PostItemInput,
)

# Connection runtime URL format:
# https://[region].azure-apihub.net/apim/dynamicsax/[connection-id]
CONNECTION_RUNTIME_URL = os.environ.get(
    "DYNAMICSAX_CONNECTION_URL",
    "",
)

# The Dynamics 365 for Finance and Operations instance URL.
DATASET = os.environ.get("DYNAMICSAX_DATASET", "")


def example_1_list_instances():
    """Example 1: List accessible Dynamics 365 Fin & Ops instances."""
    print("\n=== Example 1: List Instances ===")

    with DefaultAzureCredential() as credential:

        with DynamicsaxClient(CONNECTION_RUNTIME_URL, credential) as client:
            result = client.get_data_sets()
            datasets = result.get("value", []) if result else []

            print(f"Found {len(datasets)} instance(s).")
            for dataset in datasets[:10]:
                print(f"  - {dataset.get('name', 'N/A')}")


def example_2_list_tables():
    """Example 2: List entities (tables) for an instance."""
    print("\n=== Example 2: List Tables ===")

    if not DATASET:
        print("Set DYNAMICSAX_DATASET to run this example.")
        return

    with DefaultAzureCredential() as credential:

        with DynamicsaxClient(CONNECTION_RUNTIME_URL, credential) as client:
            result = client.get_tables(dataset=DATASET)
            tables = result.get("value", []) if result else []

            print(f"Found {len(tables)} table(s).")
            for table in tables[:10]:
                print(f"  - {table.get('name', 'N/A')}")


def example_3_create_record():
    """Example 3: Create a new record in an entity."""
    print("\n=== Example 3: Create Record ===")

    table = os.environ.get("DYNAMICSAX_TABLE", "")

    if not (DATASET and table):
        print("Set DYNAMICSAX_DATASET and DYNAMICSAX_TABLE to run this example.")
        return

    with DefaultAzureCredential() as credential:

        with DynamicsaxClient(CONNECTION_RUNTIME_URL, credential) as client:
            try:
                record = PostItemInput()
                record.additional_properties = {"Name": "SDK Sample"}
                result = client.post_item(
                    input=record,
                    dataset=DATASET,
                    table=table,
                )
                print(f"Record created: {result}")
            except ConnectorException as ex:
                print(f"Connector error: {ex}")


def main():
    """Run all Dynamics AX connector examples."""
    if not CONNECTION_RUNTIME_URL:
        print("Error: DYNAMICSAX_CONNECTION_URL environment variable is not set.")
        print("Set it to your Dynamics AX connector runtime URL from Azure Portal.")
        return

    print(f"Using connection URL: {CONNECTION_RUNTIME_URL[:50]}...")

    example_1_list_instances()
    example_2_list_tables()
    example_3_create_record()

    print("\n=== Dynamics AX sample completed ===")


if __name__ == "__main__":
    main()
