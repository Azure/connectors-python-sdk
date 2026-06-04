# Copyright (c) Microsoft Corporation. All rights reserved.

"""
Azure Storage Tables Connector SDK Sample

This sample demonstrates how to use the Azure Storage Tables connector SDK
to interact with Azure Table Storage.

Prerequisites:
1. Azure subscription with Azure Storage Tables connection
2. Azure Tables connection in Connector Namespaces (with access configured)
3. Connection runtime URL from Azure Portal
4. Azure Storage Account with table storage

Installation:
    pip install azure-connectors

Usage:
    Set environment variables:
    $env:AZURETABLES_CONNECTION_URL = "https://...apihub.net/apim/azuretables/..."
    $env:AZURETABLES_STORAGE_ACCOUNT = "<storage-account-name>"
    $env:AZURETABLES_TABLE_NAME = "<table-name>"

    python sample_connector_usage_azuretables.py
"""

import asyncio
import os
from azure.identity.aio import DefaultAzureCredential
from azure.connectors import ConnectorException
from azure.connectors.azuretables import (
    AzuretablesClient,
    CreateTableInput,
    CreateEntityInput,
)

# Connection runtime URL format:
# https://[region].azure-apihub.net/apim/azuretables/[connection-id]
CONNECTION_RUNTIME_URL = os.environ.get(
    "AZURETABLES_CONNECTION_URL",
    ""
)

# Storage account name
STORAGE_ACCOUNT = os.environ.get("AZURETABLES_STORAGE_ACCOUNT", "")

# Table name for entity operations
TABLE_NAME = os.environ.get("AZURETABLES_TABLE_NAME", "")


async def example_1_list_tables():
    """Example 1: List all tables in a storage account."""
    print("\n=== Example 1: List Tables ===")

    if not STORAGE_ACCOUNT:
        print("Set AZURETABLES_STORAGE_ACCOUNT environment variable.")
        print("Example: $env:AZURETABLES_STORAGE_ACCOUNT = 'mystorageaccount'")
        return

    credential = DefaultAzureCredential()

    async with AzuretablesClient(CONNECTION_RUNTIME_URL, credential) as client:
        try:
            result = await client.get_tables_async(
                storage_account_name=STORAGE_ACCOUNT
            )

            if result:
                print(f"Tables in storage account '{STORAGE_ACCOUNT}':")
                # Response contains 'value' with list of tables
                tables = result.get("value", [])
                if tables:
                    for table in tables:
                        table_name = table.get("TableName", table)
                        print(f"  - {table_name}")
                else:
                    print("  No tables found.")
            else:
                print("No tables found or empty response.")

        except ConnectorException as ex:
            print(f"Connector error (status {ex.status_code}): {ex}")
        except Exception as ex:
            print(f"Error: {ex}")


async def example_2_create_table():
    """Example 2: Create a new table in the storage account."""
    print("\n=== Example 2: Create Table ===")

    new_table_name = os.environ.get("AZURETABLES_NEW_TABLE_NAME", "")
    if not STORAGE_ACCOUNT or not new_table_name:
        print("Set environment variables to create a table:")
        print("  $env:AZURETABLES_STORAGE_ACCOUNT = '<storage-account-name>'")
        print("  $env:AZURETABLES_NEW_TABLE_NAME = 'MyNewTable'")
        return

    credential = DefaultAzureCredential()

    async with AzuretablesClient(CONNECTION_RUNTIME_URL, credential) as client:
        try:
            # Create table input with table name in additional_properties
            table_input = CreateTableInput(
                additional_properties={"TableName": new_table_name}
            )

            result = await client.create_table_async(
                input=table_input,
                storage_account_name=STORAGE_ACCOUNT
            )

            print(f"Table '{new_table_name}' created successfully.")
            if result:
                print(f"  OData ID: {result.get('odata.id', 'N/A')}")
                print(f"  Table Name: {result.get('TableName', 'N/A')}")

        except ConnectorException as ex:
            print(f"Connector error (status {ex.status_code}): {ex}")
        except Exception as ex:
            print(f"Error: {ex}")


async def example_3_create_entity():
    """Example 3: Insert a new entity into a table."""
    print("\n=== Example 3: Create Entity ===")

    if not STORAGE_ACCOUNT or not TABLE_NAME:
        print("Set environment variables to create an entity:")
        print("  $env:AZURETABLES_STORAGE_ACCOUNT = '<storage-account-name>'")
        print("  $env:AZURETABLES_TABLE_NAME = '<table-name>'")
        return

    credential = DefaultAzureCredential()

    async with AzuretablesClient(CONNECTION_RUNTIME_URL, credential) as client:
        try:
            # Create entity with PartitionKey, RowKey, and custom properties
            entity_input = CreateEntityInput(
                additional_properties={
                    "PartitionKey": "SamplePartition",
                    "RowKey": "SampleRow001",
                    "Name": "Sample Entity",
                    "Description": "Created by Azure Connectors SDK for Python",
                    "Count": 42,
                    "IsActive": True
                }
            )

            result = await client.create_entity_async(
                input=entity_input,
                storage_account_name=STORAGE_ACCOUNT,
                table_name=TABLE_NAME
            )

            print(f"Entity created in table '{TABLE_NAME}':")
            if result:
                print(f"  Partition Key: {result.get('PartitionKey', 'N/A')}")
                print(f"  Row Key: {result.get('RowKey', 'N/A')}")
            else:
                print("  Entity created (no response body).")

        except ConnectorException as ex:
            print(f"Connector error (status {ex.status_code}): {ex}")
        except Exception as ex:
            print(f"Error: {ex}")


async def example_4_get_entities():
    """Example 4: Query entities from a table."""
    print("\n=== Example 4: Get Entities ===")

    if not STORAGE_ACCOUNT or not TABLE_NAME:
        print("Set environment variables to query entities:")
        print("  $env:AZURETABLES_STORAGE_ACCOUNT = '<storage-account-name>'")
        print("  $env:AZURETABLES_TABLE_NAME = '<table-name>'")
        return

    credential = DefaultAzureCredential()

    async with AzuretablesClient(CONNECTION_RUNTIME_URL, credential) as client:
        try:
            # Query entities with optional filter
            result = await client.get_entities_async(
                storage_account_name=STORAGE_ACCOUNT,
                table_name=TABLE_NAME,
                # Optional: filter entities
                # filter="PartitionKey eq 'SamplePartition'",
                # Optional: select specific columns
                # select="PartitionKey,RowKey,Name"
            )

            if result:
                entities = result.get("value", [])
                print(f"Entities in table '{TABLE_NAME}':")
                if entities:
                    for i, entity in enumerate(entities[:5], 1):  # Show first 5
                        pk = entity.get("PartitionKey", "N/A")
                        rk = entity.get("RowKey", "N/A")
                        print(f"  {i}. PartitionKey: {pk}, RowKey: {rk}")
                    if len(entities) > 5:
                        print(f"  ... and {len(entities) - 5} more entities")
                else:
                    print("  No entities found.")
            else:
                print("No entities found or empty response.")

        except ConnectorException as ex:
            print(f"Connector error (status {ex.status_code}): {ex}")
        except Exception as ex:
            print(f"Error: {ex}")


async def example_5_get_entity():
    """Example 5: Get a specific entity by PartitionKey and RowKey."""
    print("\n=== Example 5: Get Entity ===")

    partition_key = os.environ.get("AZURETABLES_PARTITION_KEY", "SamplePartition")
    row_key = os.environ.get("AZURETABLES_ROW_KEY", "SampleRow001")

    if not STORAGE_ACCOUNT or not TABLE_NAME:
        print("Set environment variables to get an entity:")
        print("  $env:AZURETABLES_STORAGE_ACCOUNT = '<storage-account-name>'")
        print("  $env:AZURETABLES_TABLE_NAME = '<table-name>'")
        print("Optional:")
        print("  $env:AZURETABLES_PARTITION_KEY = '<partition-key>'")
        print("  $env:AZURETABLES_ROW_KEY = '<row-key>'")
        return

    credential = DefaultAzureCredential()

    async with AzuretablesClient(CONNECTION_RUNTIME_URL, credential) as client:
        try:
            result = await client.get_entity_async(
                storage_account_name=STORAGE_ACCOUNT,
                table_name=TABLE_NAME,
                partition_key=partition_key,
                row_key=row_key
            )

            if result:
                print(f"Entity found in '{TABLE_NAME}':")
                print(f"  Partition Key: {result.get('PartitionKey', 'N/A')}")
                print(f"  Row Key: {result.get('RowKey', 'N/A')}")
                # Print custom properties (excluding system properties)
                system_props = {
                    'PartitionKey', 'RowKey', 'Timestamp',
                    'odata.metadata', 'odata.etag'
                }
                custom_props = {
                    k: v for k, v in result.items() if k not in system_props
                }
                if custom_props:
                    print("  Custom properties:")
                    for key, value in custom_props.items():
                        print(f"    {key}: {value}")
            else:
                print("Entity not found.")

        except ConnectorException as ex:
            print(f"Connector error (status {ex.status_code}): {ex}")
        except Exception as ex:
            print(f"Error: {ex}")


async def main():
    """Run all examples."""
    print("Azure Storage Tables Connector SDK - Sample Usage")
    print("=" * 60)

    if not CONNECTION_RUNTIME_URL:
        print("\nWARNING: AZURETABLES_CONNECTION_URL environment variable not set.")
        print("Set it to your connection runtime URL to run actual API calls.")
        print("Format: https://[region].azure-apihub.net/apim/azuretables/[id]")
        return

    await example_1_list_tables()
    await example_2_create_table()
    await example_3_create_entity()
    await example_4_get_entities()
    await example_5_get_entity()

    print("\n" + "=" * 60)
    print("Sample completed!")


if __name__ == "__main__":
    asyncio.run(main())
