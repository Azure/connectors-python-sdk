# Copyright (c) Microsoft Corporation. All rights reserved.

"""
Microsoft Dataverse (Common Data Service) Connector SDK Sample

This sample demonstrates how to use the Microsoft Dataverse connector SDK.
This connector was formerly known as Common Data Service (legacy) and
replaces the Dynamics 365 connector.

Prerequisites:
1. Azure subscription with Microsoft Dataverse connection
2. Microsoft Dataverse connection in Connector Namespaces
3. Connection runtime URL from Azure Portal

Installation:
    pip install azure-connectors

Usage:
    Set environment variable:
    $env:COMMONDATASERVICE_CONNECTION_URL = `
        "https://[region].azure-apihub.net/apim/commondataservice/[connection-id]"

    python sample_connector_usage_commondataservice.py
"""

import asyncio
import os
from azure.identity.aio import DefaultAzureCredential
from azure.connectors import ConnectorException
from azure.connectors.commondataservice import (
    CommondataserviceClient,
    CreateRecordInput,
    UpdateRecordInput,
    SearchRequestBody,
)

# Connection runtime URL format:
# https://[region].azure-apihub.net/apim/commondataservice/[connection-id]
CONNECTION_RUNTIME_URL = os.environ.get(
    "COMMONDATASERVICE_CONNECTION_URL",
    ""
)


async def example_1_list_accounts():
    """Example 1: List accounts from Dataverse.

    Retrieves a list of account records with selected columns.
    """
    print("\n=== Example 1: List Accounts ===")

    credential = DefaultAzureCredential()

    async with CommondataserviceClient(CONNECTION_RUNTIME_URL, credential) as client:
        try:
            # List accounts with selected columns and filtering
            result = await client.list_records_async(
                entity_name="accounts",
                select="name,revenue,industrycode",
                filter="statecode eq 0",  # Active accounts only
                orderby="name asc",
                top="10"
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


async def example_2_create_account():
    """Example 2: Create a new account in Dataverse.

    Creates a new account record with specified field values.
    """
    print("\n=== Example 2: Create Account ===")

    credential = DefaultAzureCredential()

    async with CommondataserviceClient(CONNECTION_RUNTIME_URL, credential) as client:
        try:
            # Create a new account record
            new_account = CreateRecordInput(
                additional_properties={
                    "name": "Contoso Ltd.",
                    "description": "Sample account created via SDK",
                    "industrycode": 1,  # Accounting
                    "revenue": 1000000.00,
                    "websiteurl": "https://contoso.com"
                }
            )

            result = await client.create_record_async(
                input=new_account,
                entity_name="accounts"
            )

            if result:
                print(f"Account created with ID: {result.get('accountid', 'N/A')}")
            else:
                print("Account created successfully")

        except ConnectorException as ex:
            print(f"Connector error: {ex}")
        except Exception as ex:
            print(f"Error: {ex}")


async def example_3_get_account_by_id():
    """Example 3: Get a specific account by ID.

    Retrieves a single account record by its unique identifier.
    """
    print("\n=== Example 3: Get Account by ID ===")

    credential = DefaultAzureCredential()

    # Replace with an actual account ID from your Dataverse environment
    account_id = "00000000-0000-0000-0000-000000000000"

    async with CommondataserviceClient(CONNECTION_RUNTIME_URL, credential) as client:
        try:
            result = await client.get_item_codeless_async(
                entity_name="accounts",
                record_id=account_id,
                select="name,revenue,createdon",
                expand="primarycontactid"
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


async def example_4_update_account():
    """Example 4: Update an existing account.

    Updates specific fields on an existing account record.
    """
    print("\n=== Example 4: Update Account ===")

    credential = DefaultAzureCredential()

    # Replace with an actual account ID
    account_id = "00000000-0000-0000-0000-000000000000"

    async with CommondataserviceClient(CONNECTION_RUNTIME_URL, credential) as client:
        try:
            # Update account fields
            update_data = UpdateRecordInput(
                additional_properties={
                    "description": "Updated via SDK",
                    "revenue": 2000000.00
                }
            )

            await client.update_record_async(
                input=update_data,
                entity_name="accounts",
                record_id=account_id
            )

            print("Account updated successfully")

        except ConnectorException as ex:
            print(f"Connector error: {ex}")
        except Exception as ex:
            print(f"Error: {ex}")


async def example_5_search_records():
    """Example 5: Search records using Relevance Search.

    Uses Dataverse Relevance Search to find records matching a search term.
    """
    print("\n=== Example 5: Search Records ===")

    credential = DefaultAzureCredential()

    async with CommondataserviceClient(CONNECTION_RUNTIME_URL, credential) as client:
        try:
            search_request = SearchRequestBody(
                search="Contoso",
                searchtype="simple",
                searchmode="any",
                top=10,
                entities=["account", "contact"]
            )

            result = await client.get_relevant_rows_async(input=search_request)

            if result and result.get("value"):
                print(f"Found {len(result['value'])} matching records")
                total = result.get("totalrecordcount", -1)
                if total >= 0:
                    print(f"Total available: {total}")
            else:
                print("No matching records found")

        except ConnectorException as ex:
            print(f"Connector error: {ex}")
        except Exception as ex:
            print(f"Error: {ex}")


async def example_6_delete_account():
    """Example 6: Delete an account.

    Deletes an account record from Dataverse.
    """
    print("\n=== Example 6: Delete Account ===")

    credential = DefaultAzureCredential()

    # Replace with an actual account ID to delete
    account_id = "00000000-0000-0000-0000-000000000000"

    async with CommondataserviceClient(CONNECTION_RUNTIME_URL, credential) as client:
        try:
            await client.delete_record_async(
                entity_name="accounts",
                record_id=account_id
            )

            print("Account deleted successfully")

        except ConnectorException as ex:
            print(f"Connector error: {ex}")
        except Exception as ex:
            print(f"Error: {ex}")


async def example_7_list_contacts():
    """Example 7: List contacts with pagination.

    Demonstrates listing contacts with pagination support.
    """
    print("\n=== Example 7: List Contacts with Pagination ===")

    credential = DefaultAzureCredential()

    async with CommondataserviceClient(CONNECTION_RUNTIME_URL, credential) as client:
        try:
            # Get first page of contacts
            result = await client.list_records_async(
                entity_name="contacts",
                select="fullname,emailaddress1,telephone1",
                top="5"
            )

            if result and result.get("value"):
                print("Contacts (page 1):")
                for contact in result["value"]:
                    print(f"  - {contact.get('fullname', 'N/A')}")

                # Check for next page
                next_link = result.get("@odata.nextLink")
                if next_link:
                    print("  ... more contacts available")
            else:
                print("No contacts found")

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

    await example_1_list_accounts()
    await example_2_create_account()
    await example_3_get_account_by_id()
    await example_4_update_account()
    await example_5_search_records()
    # Uncomment to test delete (use with caution):
    # await example_6_delete_account()
    await example_7_list_contacts()

    print("\n=== All examples completed ===")


if __name__ == "__main__":
    asyncio.run(main())
