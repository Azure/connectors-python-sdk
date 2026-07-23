# Copyright (c) Microsoft Corporation. All rights reserved.

"""
Microsoft Dataverse (Common Data Service) Connector SDK Sample

This sample demonstrates how to use the Microsoft Dataverse connector SDK.
This connector was formerly known as Common Data Service (legacy).

Prerequisites:
1. Azure subscription with Microsoft Dataverse connection
2. Microsoft Dataverse connection in Connector Namespaces
3. Connection runtime URL from Azure Portal

Installation:
    pip install azure-connectors

Usage:
    Set environment variables:
    $env:COMMONDATASERVICE_CONNECTION_URL = `
        "https://[region].azure-apihub.net/apim/commondataservice/[connection-id]"

    # The dataset is the Dataverse environment/organization URL. Because it
    # contains "://", the SDK URL-encodes it twice so it survives apihub
    # gateway routing.
    $env:COMMONDATASERVICE_DATASET = "https://orgXXXXXXXX.crm.dynamics.com"

    python sample_connector_usage_commondataservice.py
"""

import asyncio
import os
from azure.identity.aio import DefaultAzureCredential
from azure.connectors import ConnectorException
from azure.connectors.commondataservice import (
    CommondataserviceClient,
    PostItemInput,
    PatchItemInput,
)

# Connection runtime URL format:
# https://[region].azure-apihub.net/apim/commondataservice/[connection-id]
CONNECTION_RUNTIME_URL = os.environ.get(
    "COMMONDATASERVICE_CONNECTION_URL",
    ""
)

# The dataset is the Dataverse environment/organization URL, e.g.
# "https://orgXXXXXXXX.crm.dynamics.com". The SDK double-encodes this path
# segment automatically.
DATASET = os.environ.get(
    "COMMONDATASERVICE_DATASET",
    "https://orgXXXXXXXX.crm.dynamics.com"
)


async def example_1_list_datasets():
    """Example 1: List the datasets (environments) available to the connection."""
    print("\n=== Example 1: List Datasets ===")

    credential = DefaultAzureCredential()

    async with CommondataserviceClient(CONNECTION_RUNTIME_URL, credential) as client:
        try:
            result = await client.get_data_sets_async()

            if result and result.get("value"):
                print(f"Found {len(result['value'])} datasets:")
                for dataset in result["value"][:5]:
                    print(f"  - {dataset.get('Name', dataset.get('DisplayName', 'N/A'))}")
            else:
                print("No datasets found")

        except ConnectorException as ex:
            print(f"Connector error: {ex}")
        except Exception as ex:
            print(f"Error: {ex}")


async def example_2_list_accounts():
    """Example 2: List rows from the 'accounts' table.

    Retrieves account rows with OData query options.
    """
    print("\n=== Example 2: List Accounts ===")

    credential = DefaultAzureCredential()

    async with CommondataserviceClient(CONNECTION_RUNTIME_URL, credential) as client:
        try:
            result = await client.get_items_async(
                dataset=DATASET,
                table="accounts",
                filter="statecode eq 0",  # Active accounts only
                orderby="name asc",
                top="10",
            )

            if result and result.get("value"):
                print(f"Found {len(result['value'])} accounts:")
                for account in result["value"][:5]:
                    print(f"  - {account.get('name', 'N/A')}")
            else:
                print("No accounts found")

        except ConnectorException as ex:
            print(f"Connector error: {ex}")
        except Exception as ex:
            print(f"Error: {ex}")


async def example_3_get_account_by_id():
    """Example 3: Get a single account row by its primary id."""
    print("\n=== Example 3: Get Account by ID ===")

    credential = DefaultAzureCredential()

    # Replace with an actual account id from your Dataverse environment.
    account_id = "00000000-0000-0000-0000-000000000000"

    async with CommondataserviceClient(CONNECTION_RUNTIME_URL, credential) as client:
        try:
            result = await client.get_item_async(
                dataset=DATASET,
                table="accounts",
                id=account_id,
            )

            if result:
                print(f"Account: {result.get('name', 'N/A')}")
                print(f"Revenue: {result.get('revenue', 'N/A')}")
            else:
                print("Account not found")

        except ConnectorException as ex:
            print(f"Connector error: {ex}")
        except Exception as ex:
            print(f"Error: {ex}")


async def example_4_create_account():
    """Example 4: Add a new row to the 'accounts' table."""
    print("\n=== Example 4: Create Account ===")

    credential = DefaultAzureCredential()

    async with CommondataserviceClient(CONNECTION_RUNTIME_URL, credential) as client:
        try:
            new_account = PostItemInput(
                additional_properties={
                    "name": "Contoso Ltd.",
                    "description": "Sample account created via SDK",
                    "revenue": 1000000.00,
                    "websiteurl": "https://contoso.com",
                }
            )

            result = await client.post_item_async(
                input=new_account,
                dataset=DATASET,
                table="accounts",
            )

            if result:
                print(f"Account created with id: {result.get('accountid', 'N/A')}")
            else:
                print("Account created successfully")

        except ConnectorException as ex:
            print(f"Connector error: {ex}")
        except Exception as ex:
            print(f"Error: {ex}")


async def example_5_update_account():
    """Example 5: Update an existing row in the 'accounts' table."""
    print("\n=== Example 5: Update Account ===")

    credential = DefaultAzureCredential()

    # Replace with an actual account id.
    account_id = "00000000-0000-0000-0000-000000000000"

    async with CommondataserviceClient(CONNECTION_RUNTIME_URL, credential) as client:
        try:
            update_data = PatchItemInput(
                additional_properties={
                    "description": "Updated via SDK",
                    "revenue": 2000000.00,
                }
            )

            await client.patch_item_async(
                input=update_data,
                dataset=DATASET,
                table="accounts",
                id=account_id,
            )

            print("Account updated successfully")

        except ConnectorException as ex:
            print(f"Connector error: {ex}")
        except Exception as ex:
            print(f"Error: {ex}")


async def example_6_get_table_metadata():
    """Example 6: Get metadata for the 'accounts' table."""
    print("\n=== Example 6: Get Table Metadata ===")

    credential = DefaultAzureCredential()

    async with CommondataserviceClient(CONNECTION_RUNTIME_URL, credential) as client:
        try:
            result = await client.get_table_async(
                dataset=DATASET,
                table="accounts",
            )

            if result:
                print(f"Table: {result.get('Name', result.get('DisplayName', 'N/A'))}")
            else:
                print("Table metadata not found")

        except ConnectorException as ex:
            print(f"Connector error: {ex}")
        except Exception as ex:
            print(f"Error: {ex}")


async def main():
    """Run all examples."""
    if not CONNECTION_RUNTIME_URL:
        print("Error: COMMONDATASERVICE_CONNECTION_URL environment variable not set.")
        print("Set it to your connection runtime URL from Azure Portal.")
        return

    print(f"Using connection URL: {CONNECTION_RUNTIME_URL[:50]}...")
    print(f"Using dataset: {DATASET}")

    await example_1_list_datasets()
    await example_2_list_accounts()
    await example_3_get_account_by_id()
    await example_4_create_account()
    await example_5_update_account()
    await example_6_get_table_metadata()

    print("\n=== All examples completed ===")


if __name__ == "__main__":
    asyncio.run(main())
