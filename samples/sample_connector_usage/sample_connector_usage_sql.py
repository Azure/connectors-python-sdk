# Copyright (c) Microsoft Corporation. All rights reserved.

"""
SQL Server Connector SDK Sample

This sample demonstrates how to use the SQL Server connector SDK.

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

import asyncio
import os

from azure.identity.aio import DefaultAzureCredential
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


async def example_1_list_servers_and_databases():
    """Example 1: Discover servers, databases, and tables."""
    print("\n=== Example 1: List Servers, Databases, and Tables ===")

    credential = DefaultAzureCredential()

    async with SqlClient(CONNECTION_RUNTIME_URL, credential) as client:
        servers = await client.get_servers_async()
        server_values = servers.get("value", []) if servers else []
        print(f"Found {len(server_values)} server(s).")

        if not SERVER:
            print("Set SQL_SERVER to list databases and tables.")
            return

        databases = await client.get_databases_async(server=SERVER)
        database_values = databases.get("value", []) if databases else []
        print(f"Found {len(database_values)} database(s) on '{SERVER}'.")

        if not DATABASE:
            print("Set SQL_DATABASE to list tables.")
            return

        tables = await client.get_tables_async(server=SERVER, database=DATABASE)
        table_values = tables.get("value", []) if tables else []
        print(f"Found {len(table_values)} table(s) in '{DATABASE}'.")
        for table in table_values[:10]:
            print(f"  - {table.get('DisplayName', table.get('Name', 'N/A'))}")


async def example_2_read_rows():
    """Example 2: Read rows from a table."""
    print("\n=== Example 2: Get Rows ===")

    if not (SERVER and DATABASE and TABLE):
        print("Set SQL_SERVER, SQL_DATABASE, and SQL_TABLE to run this example.")
        return

    credential = DefaultAzureCredential()

    async with SqlClient(CONNECTION_RUNTIME_URL, credential) as client:
        try:
            result = await client.get_items_async(
                server=SERVER,
                database=DATABASE,
                table=TABLE,
                top="5",
                orderby="Id desc",
            )
            rows = result.get("value", []) if result else []
            print(f"Retrieved {len(rows)} row(s) from '{TABLE}'.")
        except ConnectorException as ex:
            print(f"Connector error: {ex}")


async def example_3_insert_update_delete_row():
    """Example 3: Insert, update, and delete a row."""
    print("\n=== Example 3: Insert, Update, and Delete a Row ===")

    if not (SERVER and DATABASE and TABLE):
        print("Set SQL_SERVER, SQL_DATABASE, and SQL_TABLE to run this example.")
        return

    credential = DefaultAzureCredential()

    async with SqlClient(CONNECTION_RUNTIME_URL, credential) as client:
        try:
            inserted = await client.post_item_async(
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

            await client.patch_item_async(
                input=PatchItemInput(additional_properties={"Status": "Updated"}),
                server=SERVER,
                database=DATABASE,
                table=TABLE,
                id=row_id,
            )
            print(f"Updated row id: {row_id}")

            await client.delete_item_async(
                server=SERVER,
                database=DATABASE,
                table=TABLE,
                id=row_id,
            )
            print(f"Deleted row id: {row_id}")
        except ConnectorException as ex:
            print(f"Connector error: {ex}")


async def example_4_query_and_procedures():
    """Example 4: Execute a pass-through query and stored procedures."""
    print("\n=== Example 4: Query and Stored Procedures ===")

    if not (SERVER and DATABASE):
        print("Set SQL_SERVER and SQL_DATABASE to run this example.")
        return

    credential = DefaultAzureCredential()

    async with SqlClient(CONNECTION_RUNTIME_URL, credential) as client:
        try:
            query_result = await client.execute_pass_through_native_query_async(
                input=SqlPassThroughNativeQueryBody(query="SELECT TOP 1 * FROM sys.tables"),
                server=SERVER,
                database=DATABASE,
            )
            result_sets = (query_result or {}).get("resultSets", {})
            print(f"Query returned {len(result_sets)} result set(s).")

            procedures = await client.get_procedures_v2_async(
                server=SERVER,
                database=DATABASE,
            )
            procedure_values = procedures.get("value", []) if procedures else []
            print(f"Found {len(procedure_values)} stored procedure(s).")

            if procedure_values:
                procedure_name = procedure_values[0].get("Name")
                if procedure_name:
                    await client.execute_procedure_async(
                        input=ExecuteProcedureInput(),
                        server=SERVER,
                        database=DATABASE,
                        procedure=procedure_name,
                    )
                    print(f"Executed stored procedure '{procedure_name}'.")
        except ConnectorException as ex:
            print(f"Connector error: {ex}")


async def main():
    """Run all SQL Server connector examples."""
    if not CONNECTION_RUNTIME_URL:
        print("Error: SQL_CONNECTION_URL environment variable is not set.")
        print("Set it to your SQL Server connector runtime URL from Azure Portal.")
        return

    print(f"Using connection URL: {CONNECTION_RUNTIME_URL[:50]}...")

    await example_1_list_servers_and_databases()
    await example_2_read_rows()
    await example_3_insert_update_delete_row()
    await example_4_query_and_procedures()

    print("\n=== SQL Server sample completed ===")


if __name__ == "__main__":
    asyncio.run(main())
