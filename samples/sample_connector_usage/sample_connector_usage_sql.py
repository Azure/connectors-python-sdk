# Copyright (c) Microsoft Corporation. All rights reserved.

"""
SQL Server sample for the Azure Connectors Python SDK

This sample demonstrates how to use the SQL Server client from the Azure Connectors Python SDK.

Prerequisites:
1. Azure subscription with a SQL Server connection
2. SQL Server connection in Connector Namespaces
3. Connection runtime URL from Azure Portal

Installation:
    pip install azure-connectors

Usage:
    Set environment variable:
    $env:SQL_CONNECTION_URL = (
        "https://[region].azure-apihub.net/apim/sql/[connection-id]"
    )

    python sample_connector_usage_sql.py
"""
import os

from azure.identity import DefaultAzureCredential
from azure.connectors import ConnectorException
from azure.connectors.sql import (
    SqlClient,
    ExecuteProcedureInput,
    PatchItemInput,
    PostItemInput,
    SqlPassThroughNativeQueryBody,
)

# Connection runtime URL format:
# https://[region].azure-apihub.net/apim/sql/[connection-id]
CONNECTION_RUNTIME_URL = os.environ.get(
    "SQL_CONNECTION_URL",
    "",
)

# Target server/database/table used by the data examples.
SERVER = os.environ.get("SQL_SERVER", "")
DATABASE = os.environ.get("SQL_DATABASE", "")
TABLE = os.environ.get("SQL_TABLE", "")


def example_1_list_servers_and_databases():
    """Example 1: Discover servers, databases, and tables."""
    print("\n=== Example 1: List Servers, Databases, and Tables ===")

    with DefaultAzureCredential() as credential:

        with SqlClient(CONNECTION_RUNTIME_URL, credential) as client:
            server_values = list(client.list_servers())
            print(f"Found {len(server_values)} server(s).")

            if not SERVER:
                print("Set SQL_SERVER to list databases and tables.")
                return

            database_values = list(client.list_databases(server=SERVER))
            print(f"Found {len(database_values)} database(s) on '{SERVER}'.")

            if not DATABASE:
                print("Set SQL_DATABASE to list tables.")
                return

            table_values = list(
                client.list_tables(server=SERVER, database=DATABASE)
            )
            print(f"Found {len(table_values)} table(s) in '{DATABASE}'.")
            for table in table_values[:10]:
                print(f"  - {table.get('DisplayName', table.get('Name', 'N/A'))}")


def example_2_read_rows():
    """Example 2: Read rows from a table."""
    print("\n=== Example 2: Get Rows ===")

    if not (SERVER and DATABASE and TABLE):
        print("Set SQL_SERVER, SQL_DATABASE, and SQL_TABLE to run this example.")
        return

    with DefaultAzureCredential() as credential:

        with SqlClient(CONNECTION_RUNTIME_URL, credential) as client:
            try:
                rows = [item for item in client.list_items(
                    server=SERVER,
                    database=DATABASE,
                    table=TABLE,
                    top=5,
                    orderby="Id desc",
                )]
                print(f"Retrieved {len(rows)} row(s) from '{TABLE}'.")
            except ConnectorException as ex:
                print(f"Connector error: {ex}")


def example_3_insert_update_delete_row():
    """Example 3: Insert, update, and delete a row."""
    print("\n=== Example 3: Insert, Update, and Delete a Row ===")

    if not (SERVER and DATABASE and TABLE):
        print("Set SQL_SERVER, SQL_DATABASE, and SQL_TABLE to run this example.")
        return

    with DefaultAzureCredential() as credential:

        with SqlClient(CONNECTION_RUNTIME_URL, credential) as client:
            try:
                inserted = client.post_item(
                    input=PostItemInput(
                        additional_properties={"Name": "Contoso", "Status": "Active"},
                    ),
                    server=SERVER,
                    database=DATABASE,
                    table=TABLE,
                )
                row_id = str((inserted or {}).get("Id", "")) if inserted else ""
                print(f"Inserted row id: {row_id or 'N/A'}")

                if not row_id:
                    return

                client.patch_item(
                    input=PatchItemInput(additional_properties={"Status": "Updated"}),
                    server=SERVER,
                    database=DATABASE,
                    table=TABLE,
                    id=row_id,
                )
                print(f"Updated row id: {row_id}")

                client.delete_item(
                    server=SERVER,
                    database=DATABASE,
                    table=TABLE,
                    id=row_id,
                )
                print(f"Deleted row id: {row_id}")
            except ConnectorException as ex:
                print(f"Connector error: {ex}")


def example_4_query_and_procedures():
    """Example 4: Execute a pass-through query and stored procedures."""
    print("\n=== Example 4: Query and Stored Procedures ===")

    if not (SERVER and DATABASE):
        print("Set SQL_SERVER and SQL_DATABASE to run this example.")
        return

    with DefaultAzureCredential() as credential:

        with SqlClient(CONNECTION_RUNTIME_URL, credential) as client:
            try:
                query_result = client.execute_pass_through_native_query(
                    input=SqlPassThroughNativeQueryBody(query="SELECT TOP 1 * FROM sys.tables"),
                    server=SERVER,
                    database=DATABASE,
                )
                result_sets = (query_result or {}).get("resultSets", {})
                print(f"Query returned {len(result_sets)} result set(s).")

                procedure_values = list(client.list_procedures_v2(
                    server=SERVER,
                    database=DATABASE,
                ))
                print(f"Found {len(procedure_values)} stored procedure(s).")

                if procedure_values:
                    procedure_name = procedure_values[0].get("Name")
                    if procedure_name:
                        client.execute_procedure(
                            input=ExecuteProcedureInput(),
                            server=SERVER,
                            database=DATABASE,
                            procedure=procedure_name,
                        )
                        print(f"Executed stored procedure '{procedure_name}'.")
            except ConnectorException as ex:
                print(f"Connector error: {ex}")


def main():
    """Run all SQL Server connector examples."""
    if not CONNECTION_RUNTIME_URL:
        print("Error: SQL_CONNECTION_URL environment variable is not set.")
        print("Set it to your SQL Server connector runtime URL from Azure Portal.")
        return

    print(f"Using connection URL: {CONNECTION_RUNTIME_URL[:50]}...")

    example_1_list_servers_and_databases()
    example_2_read_rows()
    example_3_insert_update_delete_row()
    example_4_query_and_procedures()

    print("\n=== SQL Server sample completed ===")


if __name__ == "__main__":
    main()
