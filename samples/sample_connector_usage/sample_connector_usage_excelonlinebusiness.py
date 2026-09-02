# Copyright (c) Microsoft Corporation. All rights reserved.

"""
Excel Online (Business) Connector SDK Sample

This sample demonstrates how to use the Excel Online Business connector SDK
to work with Excel files stored in SharePoint document libraries.

Prerequisites:
1. Azure subscription with Excel Online (Business) connection
2. Excel Online connection in Connector Namespaces (with OAuth consent)
3. Connection runtime URL from Azure Portal
4. SharePoint site with Excel files containing tables

Installation:
    pip install azure-connectors

Usage:
    Set environment variables:
    $env:EXCELONLINE_CONNECTION_URL = "https://...apihub.net/apim/excelonlinebusiness/..."
    $env:EXCELONLINE_DRIVE_ID = "<drive-id>"
    $env:EXCELONLINE_FILE_ID = "<file-id>"
    $env:EXCELONLINE_TABLE_NAME = "<table-name>"

    python sample_connector_usage_excelonlinebusiness.py
"""

import asyncio
import os
from azure.identity.aio import DefaultAzureCredential
from azure.connectors import ConnectorException
from azure.connectors.excelonlinebusiness import (
    ExcelonlinebusinessClient,
    TableToCreate,
    Item,
)

# Connection runtime URL format:
# https://[region].azure-apihub.net/apim/excelonlinebusiness/[connection-id]
CONNECTION_RUNTIME_URL = os.environ.get(
    "EXCELONLINE_CONNECTION_URL",
    ""
)

# SharePoint drive ID (document library)
DRIVE_ID = os.environ.get("EXCELONLINE_DRIVE_ID", "")

# Excel file ID or path
FILE_ID = os.environ.get("EXCELONLINE_FILE_ID", "")

# Table name in the Excel file
TABLE_NAME = os.environ.get("EXCELONLINE_TABLE_NAME", "")

# SharePoint site URL (source parameter)
SOURCE_URL = os.environ.get("EXCELONLINE_SOURCE_URL", "")


async def example_1_list_table_rows():
    """Example 1: List rows in an Excel table."""
    print("\n=== Example 1: List Table Rows ===")

    if not DRIVE_ID or not FILE_ID or not TABLE_NAME:
        print("Set environment variables to list table rows:")
        print("  $env:EXCELONLINE_DRIVE_ID = '<drive-id>'")
        print("  $env:EXCELONLINE_FILE_ID = '<file-id>'")
        print("  $env:EXCELONLINE_TABLE_NAME = '<table-name>'")
        print("  $env:EXCELONLINE_SOURCE_URL = '<sharepoint-site-url>'  (optional)")
        return

    credential = DefaultAzureCredential()

    async with ExcelonlinebusinessClient(CONNECTION_RUNTIME_URL, credential) as client:
        try:
            result = await client.get_items_async(
                drive=DRIVE_ID,
                file=FILE_ID,
                table=TABLE_NAME,
                source=SOURCE_URL if SOURCE_URL else None,
                top=10,  # Limit to 10 rows
            )

            if result and "value" in result:
                rows = result["value"]
                print(f"Found {len(rows)} row(s) in table '{TABLE_NAME}':")
                for i, row in enumerate(rows[:5], 1):
                    print(f"  Row {i}: {row}")
                if len(rows) > 5:
                    print(f"  ... and {len(rows) - 5} more rows")
            else:
                print("No rows found or empty response.")

        except ConnectorException as ex:
            print(f"Connector error: {ex}")
        except Exception as ex:
            print(f"Error: {ex}")


async def example_2_get_specific_row():
    """Example 2: Get a specific row by key value."""
    print("\n=== Example 2: Get Specific Row ===")

    row_id = os.environ.get("EXCELONLINE_ROW_ID", "")
    id_column = os.environ.get("EXCELONLINE_ID_COLUMN", "")

    if not DRIVE_ID or not FILE_ID or not TABLE_NAME or not row_id:
        print("Set environment variables to get a specific row:")
        print("  $env:EXCELONLINE_DRIVE_ID = '<drive-id>'")
        print("  $env:EXCELONLINE_FILE_ID = '<file-id>'")
        print("  $env:EXCELONLINE_TABLE_NAME = '<table-name>'")
        print("  $env:EXCELONLINE_ROW_ID = '<row-key-value>'")
        print("  $env:EXCELONLINE_ID_COLUMN = '<key-column-name>'  (optional)")
        return

    credential = DefaultAzureCredential()

    async with ExcelonlinebusinessClient(CONNECTION_RUNTIME_URL, credential) as client:
        try:
            result = await client.get_item_async(
                drive=DRIVE_ID,
                file=FILE_ID,
                table=TABLE_NAME,
                id=row_id,
                source=SOURCE_URL if SOURCE_URL else None,
                id_column=id_column if id_column else None,
            )

            if result:
                print(f"Row with ID '{row_id}':")
                for key, value in result.items():
                    if not key.startswith("@"):
                        print(f"  {key}: {value}")
            else:
                print("Row not found or empty response.")

        except ConnectorException as ex:
            print(f"Connector error: {ex}")
        except Exception as ex:
            print(f"Error: {ex}")


async def example_3_list_workbook_comments():
    """Example 3: List comments in an Excel workbook."""
    print("\n=== Example 3: List Workbook Comments ===")

    if not DRIVE_ID or not FILE_ID:
        print("Set environment variables to list comments:")
        print("  $env:EXCELONLINE_DRIVE_ID = '<drive-id>'")
        print("  $env:EXCELONLINE_FILE_ID = '<file-id>'")
        return

    credential = DefaultAzureCredential()

    async with ExcelonlinebusinessClient(CONNECTION_RUNTIME_URL, credential) as client:
        try:
            result = await client.get_comments_async(
                drive=DRIVE_ID,
                file=FILE_ID,
                source=SOURCE_URL if SOURCE_URL else None,
            )

            if result and "value" in result:
                comments = result["value"]
                print(f"Found {len(comments)} comment(s):")
                for comment in comments[:5]:
                    comment_id = comment.get("id", "N/A")
                    content = comment.get("content", "N/A")
                    print(f"  [{comment_id}]: {content[:50]}...")
                if len(comments) > 5:
                    print(f"  ... and {len(comments) - 5} more comments")
            else:
                print("No comments found.")

        except ConnectorException as ex:
            print(f"Connector error: {ex}")
        except Exception as ex:
            print(f"Error: {ex}")


async def example_4_create_table():
    """Example 4: Create a new table in an Excel workbook."""
    print("\n=== Example 4: Create Table ===")

    new_table_name = os.environ.get("EXCELONLINE_NEW_TABLE_NAME", "")
    table_range = os.environ.get("EXCELONLINE_TABLE_RANGE", "")
    column_names = os.environ.get("EXCELONLINE_COLUMN_NAMES", "")

    if not DRIVE_ID or not FILE_ID or not new_table_name:
        print("Set environment variables to create a table:")
        print("  $env:EXCELONLINE_DRIVE_ID = '<drive-id>'")
        print("  $env:EXCELONLINE_FILE_ID = '<file-id>'")
        print("  $env:EXCELONLINE_NEW_TABLE_NAME = 'NewTable'")
        print("  $env:EXCELONLINE_TABLE_RANGE = 'A1:C10'  (optional)")
        print("  $env:EXCELONLINE_COLUMN_NAMES = 'Name;Email;Phone'  (optional)")
        return

    credential = DefaultAzureCredential()

    async with ExcelonlinebusinessClient(CONNECTION_RUNTIME_URL, credential) as client:
        try:
            table_input = TableToCreate(
                table_name=new_table_name,
                range=table_range if table_range else None,
                columns_names=column_names if column_names else None,
            )

            result = await client.create_table_async(
                input=table_input,
                drive=DRIVE_ID,
                file=FILE_ID,
                source=SOURCE_URL if SOURCE_URL else None,
            )

            if result:
                print("Table created:")
                print(f"  Name: {result.get('name', 'N/A')}")
                print(f"  Title: {result.get('title', 'N/A')}")
            else:
                print("Table created (no response returned).")

        except ConnectorException as ex:
            print(f"Connector error: {ex}")
        except Exception as ex:
            print(f"Error: {ex}")


async def example_5_update_row():
    """Example 5: Update a row in an Excel table."""
    print("\n=== Example 5: Update Row ===")

    row_id = os.environ.get("EXCELONLINE_ROW_ID", "")
    id_column = os.environ.get("EXCELONLINE_ID_COLUMN", "")

    if not DRIVE_ID or not FILE_ID or not TABLE_NAME or not row_id:
        print("Set environment variables to update a row:")
        print("  $env:EXCELONLINE_DRIVE_ID = '<drive-id>'")
        print("  $env:EXCELONLINE_FILE_ID = '<file-id>'")
        print("  $env:EXCELONLINE_TABLE_NAME = '<table-name>'")
        print("  $env:EXCELONLINE_ROW_ID = '<row-key-value>'")
        print("  $env:EXCELONLINE_ID_COLUMN = '<key-column-name>'  (optional)")
        return

    credential = DefaultAzureCredential()

    async with ExcelonlinebusinessClient(CONNECTION_RUNTIME_URL, credential) as client:
        try:
            # Create an Item with the fields to update
            # The dynamic_properties dict contains column-value pairs
            update_data = Item(
                dynamic_properties={
                    "Status": "Updated via SDK",
                    "LastModified": "2024-01-15",
                }
            )

            result = await client.patch_item_async(
                input=update_data,
                drive=DRIVE_ID,
                file=FILE_ID,
                table=TABLE_NAME,
                id=row_id,
                source=SOURCE_URL if SOURCE_URL else None,
                id_column=id_column if id_column else None,
            )

            if result:
                print(f"Row '{row_id}' updated:")
                for key, value in result.items():
                    if not key.startswith("@"):
                        print(f"  {key}: {value}")
            else:
                print("Row updated (no response returned).")

        except ConnectorException as ex:
            print(f"Connector error: {ex}")
        except Exception as ex:
            print(f"Error: {ex}")


async def main():
    """Run all examples."""
    print("Excel Online (Business) Connector SDK - Sample Usage")
    print("=" * 60)

    if not CONNECTION_RUNTIME_URL:
        print("\nWARNING: EXCELONLINE_CONNECTION_URL environment variable not set.")
        print("Set it to your connection runtime URL to run actual API calls.")
        print("Format: https://[region].azure-apihub.net/apim/excelonlinebusiness/[connection-id]")
        return

    await example_1_list_table_rows()
    await example_2_get_specific_row()
    await example_3_list_workbook_comments()
    await example_4_create_table()
    await example_5_update_row()

    print("\n" + "=" * 60)
    print("Sample completed!")


if __name__ == "__main__":
    asyncio.run(main())
