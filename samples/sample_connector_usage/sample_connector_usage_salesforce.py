# Copyright (c) Microsoft Corporation. All rights reserved.

"""
Salesforce Connector SDK Sample

This sample demonstrates how to use the Salesforce connector SDK.

Prerequisites:
1. Azure subscription with Salesforce connection
2. Salesforce connection in Connector Namespaces
3. Connection runtime URL from Azure Portal

Installation:
    pip install azure-connectors

Usage:
    Set environment variable:
    $env:SALESFORCE_CONNECTION_URL = (
        "https://[region].azure-apihub.net/apim/salesforce/[connection-id]"
    )

    python sample_connector_usage_salesforce.py
"""
import os
from azure.identity import DefaultAzureCredential
from azure.connectors import ConnectorException
from azure.connectors.salesforce import ExecuteSoqlQueryParameters, SalesforceClient

# Connection runtime URL format:
# https://[region].azure-apihub.net/apim/salesforce/[connection-id]
CONNECTION_RUNTIME_URL = os.environ.get(
    "SALESFORCE_CONNECTION_URL",
    "",
)


def example_1_get_tables():
    """Example 1: List Salesforce object types."""
    print("\n=== Example 1: Get Tables ===")

    with DefaultAzureCredential() as credential:

        with SalesforceClient(CONNECTION_RUNTIME_URL, credential) as client:
            try:
                tables = [item for item in client.get_tables()]

                if tables:
                    print(f"Found {len(tables)} table(s):")
                    for table in tables[:10]:
                        print(
                            f"  - {table.get('name')}"
                            f" ({table.get('displayName', 'no display name')})"
                        )
                else:
                    print("No tables found.")

            except ConnectorException as ex:
                print(f"Connector error: {ex}")
            except Exception as ex:
                print(f"Error: {ex}")


def example_2_get_records():
    """Example 2: Read records from Account table."""
    print("\n=== Example 2: Get Account Records ===")

    with DefaultAzureCredential() as credential:

        with SalesforceClient(CONNECTION_RUNTIME_URL, credential) as client:
            try:
                records = [item for item in client.get_items(
                    table="account",
                    top=5,
                    select="Id,Name,Phone",
                )]

                if records:
                    print(f"Found {len(records)} account record(s):")
                    for record in records:
                        print(
                            f"  - {record.get('Name', 'Unknown')}"
                            f" (Id: {record.get('Id')})"
                        )
                else:
                    print("No account records found.")

            except ConnectorException as ex:
                print(f"Connector error: {ex}")
            except Exception as ex:
                print(f"Error: {ex}")


def example_3_execute_soql():
    """Example 3: Execute a SOQL query."""
    print("\n=== Example 3: Execute SOQL Query ===")

    with DefaultAzureCredential() as credential:

        with SalesforceClient(CONNECTION_RUNTIME_URL, credential) as client:
            try:
                query_input = ExecuteSoqlQueryParameters(
                    query="SELECT Id, Name FROM Account LIMIT 5",
                )
                result = client.execute_soql_query(input=query_input)

                if result:
                    records = result.get("records", [])
                    print(f"SOQL returned {len(records)} record(s).")
                    for record in records:
                        print(f"  - {record.get('Name', 'Unknown')} ({record.get('Id')})")
                else:
                    print("SOQL returned no data.")

            except ConnectorException as ex:
                print(f"Connector error: {ex}")
            except Exception as ex:
                print(f"Error: {ex}")


def main():
    """Run all examples."""
    if not CONNECTION_RUNTIME_URL:
        print("Error: SALESFORCE_CONNECTION_URL environment variable not set.")
        print("Set it to your connection runtime URL from Azure Portal.")
        return

    print(f"Using connection URL: {CONNECTION_RUNTIME_URL[:50]}...")

    example_1_get_tables()
    example_2_get_records()
    example_3_execute_soql()

    print("\n=== All examples completed ===")


if __name__ == "__main__":
    main()
