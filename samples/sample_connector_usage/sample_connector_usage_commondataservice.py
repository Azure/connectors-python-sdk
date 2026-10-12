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
import os
from azure.identity import DefaultAzureCredential
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


def example_1_list_datasets():
    """Example 1: List the datasets (environments) available to the connection."""
    print("\n=== Example 1: List Datasets ===")

    with DefaultAzureCredential() as credential:

        with CommondataserviceClient(CONNECTION_RUNTIME_URL, credential) as client:
            try:
                result = client.get_data_sets()

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


def example_2_list_accounts():
    """Example 2: List rows from the 'accounts' table.

    Retrieves account rows with OData query options.
    """
    print("\n=== Example 2: List Accounts ===")

    with DefaultAzureCredential() as credential:

        with CommondataserviceClient(CONNECTION_RUNTIME_URL, credential) as client:
            try:
                accounts = [
                    account
                    for account in client.get_items(
                        dataset=DATASET,
                        table="accounts",
                        filter="statecode eq 0",  # Active accounts only
                        orderby="name asc",
                        top=10,
                    )
                ]

                if accounts:
                    print(f"Found {len(accounts)} accounts:")
                    for account in accounts[:5]:
                        print(f"  - {account.get('name', 'N/A')}")
                else:
                    print("No accounts found")

            except ConnectorException as ex:
                print(f"Connector error: {ex}")
            except Exception as ex:
                print(f"Error: {ex}")


def example_3_get_account_by_id():
    """Example 3: Get a single account row by its primary id."""
    print("\n=== Example 3: Get Account by ID ===")

    with DefaultAzureCredential() as credential:

        # Replace with an actual account id from your Dataverse environment.
        account_id = "00000000-0000-0000-0000-000000000000"

        with CommondataserviceClient(CONNECTION_RUNTIME_URL, credential) as client:
            try:
                result = client.get_item(
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


def example_4_create_account():
    """Example 4: Add a new row to the 'accounts' table."""
    print("\n=== Example 4: Create Account ===")

    with DefaultAzureCredential() as credential:

        with CommondataserviceClient(CONNECTION_RUNTIME_URL, credential) as client:
            try:
                new_account = PostItemInput(
                    additional_properties={
                        "name": "Contoso Ltd.",
                        "description": "Sample account created via SDK",
                        "revenue": 1000000.00,
                        "websiteurl": "https://contoso.com",
                    }
                )

                result = client.post_item(
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


def example_5_update_account():
    """Example 5: Update an existing row in the 'accounts' table."""
    print("\n=== Example 5: Update Account ===")

    with DefaultAzureCredential() as credential:

        # Replace with an actual account id.
        account_id = "00000000-0000-0000-0000-000000000000"

        with CommondataserviceClient(CONNECTION_RUNTIME_URL, credential) as client:
            try:
                update_data = PatchItemInput(
                    additional_properties={
                        "description": "Updated via SDK",
                        "revenue": 2000000.00,
                    }
                )

                client.patch_item(
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


def example_6_create_attachment():
    """Example 6: Add a note attachment to an account row."""
    print("\n=== Example 6: Create Account Attachment ===")

    with DefaultAzureCredential() as credential:

        # Replace with an actual account id from your Dataverse environment.
        account_id = "00000000-0000-0000-0000-000000000000"

        with CommondataserviceClient(CONNECTION_RUNTIME_URL, credential) as client:
            try:
                result = client.create_attachment(
                    input=b"Sample attachment content",
                    dataset=DATASET,
                    table="accounts",
                    id=account_id,
                    display_name="sample-note.txt",
                )

                if result:
                    print(f"Attachment created with id: {result.get('annotationid', 'N/A')}")
                else:
                    print("Attachment created successfully")

            except ConnectorException as ex:
                print(f"Connector error: {ex}")
            except Exception as ex:
                print(f"Error: {ex}")


def example_7_get_table_metadata():
    """Example 7: Get metadata for the 'accounts' table."""
    print("\n=== Example 7: Get Table Metadata ===")

    with DefaultAzureCredential() as credential:

        with CommondataserviceClient(CONNECTION_RUNTIME_URL, credential) as client:
            try:
                result = client.get_table(
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


def main():
    """Run all examples."""
    if not CONNECTION_RUNTIME_URL:
        print("Error: COMMONDATASERVICE_CONNECTION_URL environment variable not set.")
        print("Set it to your connection runtime URL from Azure Portal.")
        return

    print(f"Using connection URL: {CONNECTION_RUNTIME_URL[:50]}...")
    print(f"Using dataset: {DATASET}")

    example_1_list_datasets()
    example_2_list_accounts()
    example_3_get_account_by_id()
    example_4_create_account()
    example_5_update_account()
    example_6_create_attachment()
    example_7_get_table_metadata()

    print("\n=== All examples completed ===")


if __name__ == "__main__":
    main()
