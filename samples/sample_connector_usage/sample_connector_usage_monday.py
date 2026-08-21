"""
Monday.com Connector SDK Sample

This sample demonstrates how to use the Monday.com connector SDK.

Prerequisites:
1. Azure subscription with a Monday.com connection
2. Monday.com connection in Connector Namespaces
3. Connection runtime URL from Azure Portal

Installation:
    pip install azure-connectors

Usage:
    Set environment variable:
    $env:MONDAY_CONNECTION_URL = "https://[region].azure-apihub.net/apim/monday/[id]"

    python sample_connector_usage_monday.py
"""

import asyncio
import os

from azure.identity.aio import DefaultAzureCredential

from azure.connectors import ConnectorException
from azure.connectors.monday import (
    CreateBoardInput,
    CreateItemInput,
    DynamicResponseGetSingleColumnSchema,
    MondayClient,
    UpdateItemColumnInput,
)


# Connection runtime URL format:
# https://[region].azure-apihub.net/apim/monday/[connection-id]
CONNECTION_RUNTIME_URL = os.environ.get("MONDAY_CONNECTION_URL", "")


async def example_1_create_board() -> None:
    """Example 1: Create a board."""
    print("\n=== Example 1: Create Board ===")

    credential = DefaultAzureCredential()
    async with MondayClient(CONNECTION_RUNTIME_URL, credential) as client:
        board = await client.create_board_async(
            input=CreateBoardInput(
                workspace_id="123456",
                board_name="SDK sample board",
            )
        )
        data = board.get("data", {}) if board else {}
        print(f"Created board: {data}")


async def example_2_create_item() -> None:
    """Example 2: Create an item in a board and group."""
    print("\n=== Example 2: Create Item ===")

    credential = DefaultAzureCredential()
    async with MondayClient(CONNECTION_RUNTIME_URL, credential) as client:
        item = await client.create_item_async(
            input=CreateItemInput(
                workspace_id="123456",
                board_id="789012",
                group_id="topics",
                item_name="SDK sample item",
            )
        )
        data = item.get("data", {}) if item else {}
        print(f"Created item: {data}")


async def example_3_update_item_column() -> None:
    """Example 3: Update a column value on an item."""
    print("\n=== Example 3: Update Item Column ===")

    credential = DefaultAzureCredential()
    async with MondayClient(CONNECTION_RUNTIME_URL, credential) as client:
        updated = await client.update_item_column_async(
            input=UpdateItemColumnInput(
                workspace_id="123456",
                board_id="789012",
                item_id="345678",
                column_id="status",
                column_values=DynamicResponseGetSingleColumnSchema(
                    additional_properties={"label": "Done"},
                ),
            )
        )
        data = updated.get("data", {}) if updated else {}
        print(f"Updated item column: {data}")


async def example_4_list_workspaces() -> None:
    """Example 4: List the available workspaces."""
    print("\n=== Example 4: List Workspaces ===")

    credential = DefaultAzureCredential()
    async with MondayClient(CONNECTION_RUNTIME_URL, credential) as client:
        workspaces = await client.get_workspaces_async()
        print(f"Workspaces: {workspaces}")


async def main() -> None:
    """Run Monday.com connector examples."""
    if not CONNECTION_RUNTIME_URL:
        print("Error: MONDAY_CONNECTION_URL environment variable not set.")
        print("Set it to your connection runtime URL from Azure Portal.")
        return

    print("Monday.com Connector SDK - Sample Usage")
    print("=" * 50)

    try:
        # Uncomment to create boards or items in Monday.com.
        # await example_1_create_board()
        # await example_2_create_item()
        # await example_3_update_item_column()
        # await example_4_list_workspaces()
        print("Set the example calls in main() to run against your instance.")

    except ConnectorException as ex:
        print(f"Connector error: {ex}")
    except Exception as ex:
        print(f"Unexpected error: {ex}")


if __name__ == "__main__":
    asyncio.run(main())
