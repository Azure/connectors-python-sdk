# Copyright (c) Microsoft Corporation. All rights reserved.

"""
SharePoint Online Connector SDK Sample

This sample demonstrates how to use the SharePoint Online connector SDK.

Prerequisites:
1. Azure subscription with SharePoint Online connection
2. SharePoint Online connection in Connector Namespaces
3. Connection runtime URL from Azure Portal
4. SharePoint site URL

Installation:
    pip install azure-connectors

Usage:
    Set environment variables:
    $env:SHAREPOINT_CONNECTION_URL = (
        "https://[region].azure-apihub.net/apim/sharepointonline/[connection-id]"
    )
    $env:SHAREPOINT_SITE_URL = "https://[tenant].sharepoint.com/sites/[site-name]"

    python sample_connector_usage_sharepoint.py
"""

import asyncio
import os

try:
    from azure.identity.aio import DefaultAzureCredential
    from azure.connectors import ConnectorException
    from azure.connectors.sharepointonline import (
        SharepointonlineClient,
    )
    IMPORTS_AVAILABLE = True
except ImportError as import_error:
    IMPORTS_AVAILABLE = False
    IMPORT_ERROR = str(import_error)

#  Connection runtime URL format:
# https://[region].azure-apihub.net/apim/sharepointonline/[connection-id]
CONNECTION_RUNTIME_URL = os.environ.get(
    "SHAREPOINT_CONNECTION_URL",
    ""
)

#  SharePoint site URL format:
# https://[tenant].sharepoint.com/sites/[site-name]
SHAREPOINT_SITE_URL = os.environ.get(
    "SHAREPOINT_SITE_URL",
    ""
)


async def example_1_get_lists():
    """Example 1: Get all lists and libraries from a SharePoint site."""
    print("\n=== Example 1: Get Lists and Libraries ===")

    credential = DefaultAzureCredential()

    async with SharepointonlineClient(CONNECTION_RUNTIME_URL, credential) as client:
        try:
            lists = await client.get_tables_async(dataset=SHAREPOINT_SITE_URL)

            if lists and 'value' in lists:
                print(f"Found {len(lists['value'])} lists and libraries:")
                for list_item in lists['value'][:5]:
                    display_name = list_item.get('DisplayName', 'Unknown')
                    name = list_item.get('Name', 'Unknown')
                    print(f"  - {display_name} ({name})")
            else:
                print("No lists found or unexpected response format.")

        except ConnectorException as ex:
            print(f"Connector error: {ex}")
            print(f"Status code: {ex.status_code}")
        except Exception as ex:
            print(f"Error: {ex}")


async def example_2_get_list_items():
    """Example 2: Get items from a SharePoint list."""
    print("\n=== Example 2: Get List Items ===")

    list_name = os.environ.get("TEST_LIST_NAME", "18050732-97a3-4509-b510-a094a5a35947")

    credential = DefaultAzureCredential()

    async with SharepointonlineClient(CONNECTION_RUNTIME_URL, credential) as client:
        try:
            items = await client.get_items_async(
                dataset=SHAREPOINT_SITE_URL,
                table=list_name,
            )

            if items and 'value' in items:
                print(f"Found {len(items['value'])} items in '{list_name}' list:")
                for item in items['value']:
                    title = item.get('Title', 'No Title')
                    item_id = item.get('Id', 'Unknown')
                    print(f"  - [{item_id}] {title}")
            else:
                print(f"No items found in '{list_name}' list.")
                print("Note: Set TEST_LIST_NAME environment variable to query a different list")

        except ConnectorException as ex:
            print(f"Connector error: {ex}")
            print(f"Status code: {ex.status_code}")
            if ex.status_code == 404:
                print(f"Hint: List '{list_name}' may not exist. Check the list name.")
        except Exception as ex:
            print(f"Error: {ex}")


async def example_3_create_list_item():
    """Example 3: Create a new item in a SharePoint list."""
    print("\n=== Example 3: Create List Item ===")

    list_name = os.environ.get("TEST_LIST_NAME", "Tasks")

    credential = DefaultAzureCredential()

    async with SharepointonlineClient(CONNECTION_RUNTIME_URL, credential) as client:
        try:
            new_item = {
                'Title': 'Test Task from Python SDK',
            }

            created = await client.post_item_async(
                dataset=SHAREPOINT_SITE_URL,
                table=list_name,
                input=new_item,
            )

            if created and 'Id' in created:
                item_id = created['Id']
                print(f"Created item successfully with ID: {item_id}")
                print(f"Title: {created.get('Title', 'N/A')}")

                # Clean up: delete the item we just created
                await client.delete_item_async(
                    dataset=SHAREPOINT_SITE_URL,
                    table=list_name,
                    id=str(item_id),
                )
                print(f"Cleaned up: Deleted test item {item_id}")
            else:
                print("Item created but no ID returned.")

        except ConnectorException as ex:
            print(f"Connector error: {ex}")
            if ex.status_code == 404:
                print(f"Hint: List '{list_name}' may not exist.")
        except Exception as ex:
            print(f"Error: {ex}")


async def example_4_update_list_item():
    """Example 4: Create, update, and delete a list item."""
    print("\n=== Example 4: Update List Item (Full CRUD) ===")

    list_name = os.environ.get("TEST_LIST_NAME", "Tasks")

    credential = DefaultAzureCredential()

    async with SharepointonlineClient(CONNECTION_RUNTIME_URL, credential) as client:
        try:
            # CREATE
            print("Creating item...")
            new_item = {
                'Title': 'Task to Update',
            }
            created = await client.post_item_async(
                dataset=SHAREPOINT_SITE_URL,
                table=list_name,
                input=new_item,
            )
            item_id = created['Id']
            print(f"  Created item {item_id}: {created.get('Title')}")

            # READ
            print("Reading item...")
            item = await client.get_item_async(
                dataset=SHAREPOINT_SITE_URL,
                table=list_name,
                id=str(item_id),
            )
            print(f"  Read item {item_id}: {item.get('Title')}")

            # UPDATE
            print("Updating item...")
            updates = {
                'Title': 'Updated Task Title',
            }
            await client.patch_item_async(
                dataset=SHAREPOINT_SITE_URL,
                table=list_name,
                id=str(item_id),
                input=updates,
            )

            # Verify update
            updated_item = await client.get_item_async(
                dataset=SHAREPOINT_SITE_URL,
                table=list_name,
                id=str(item_id),
            )
            print(f"  Updated item {item_id}: {updated_item.get('Title')}")

            # DELETE
            print("Deleting item...")
            await client.delete_item_async(
                dataset=SHAREPOINT_SITE_URL,
                table=list_name,
                id=str(item_id),
            )
            print(f"  Deleted item {item_id}")

        except ConnectorException as ex:
            print(f"Connector error: {ex}")
            print(f"Status code: {ex.status_code}")
        except Exception as ex:
            print(f"Error: {ex}")


async def example_5_query_with_filters():
    """Example 5: Query list items with OData filters."""
    print("\n=== Example 5: Query with Filters ===")

    list_name = os.environ.get("TEST_LIST_NAME", "Tasks")

    credential = DefaultAzureCredential()

    async with SharepointonlineClient(CONNECTION_RUNTIME_URL, credential) as client:
        try:
            # Create some test items first
            print("Creating test items...")
            for i in range(3):
                await client.post_item_async(
                    dataset=SHAREPOINT_SITE_URL,
                    table=list_name,
                    input={'Title': f'Test Item {i + 1}'},
                )
            print("  Created 3 test items")

            # Query with filters
            print("\nQuerying items (ordered by creation date, top 5)...")
            items = await client.get_items_async(
                dataset=SHAREPOINT_SITE_URL,
                table=list_name,
                filter=None,
                orderby='Created desc',
                top=5,
            )

            if items and 'value' in items:
                print(f"Found {len(items['value'])} items:")
                for item in items['value']:
                    title = item.get('Title', 'No Title')
                    created = item.get('Created', 'Unknown')
                    print(f"  - {title} (Created: {created})")

            # Clean up test items
            print("\nCleaning up test items...")
            for item in items.get('value', [])[:3]:
                if 'Test Item' in item.get('Title', ''):
                    await client.delete_item_async(
                        dataset=SHAREPOINT_SITE_URL,
                        table=list_name,
                        id=str(item['Id']),
                    )
            print("  Cleaned up test items")

        except ConnectorException as ex:
            print(f"Connector error: {ex}")
            print(f"Status code: {ex.status_code}")
        except Exception as ex:
            print(f"Error: {ex}")


async def example_6_file_operations():
    """Example 6: File operations - list folders and get file metadata."""
    print("\n=== Example 6: File Operations ===")

    credential = DefaultAzureCredential()

    async with SharepointonlineClient(CONNECTION_RUNTIME_URL, credential) as client:
        try:
            # List root folder
            print("Listing root folder...")
            root_folder = await client.list_root_folder_async(dataset=SHAREPOINT_SITE_URL)

            if root_folder and 'value' in root_folder:
                print(f"Found {len(root_folder['value'])} items in root folder:")
                for item in root_folder['value'][:5]:
                    name = item.get('Name', 'Unknown')
                    is_folder = item.get('IsFolder', False)
                    item_type = 'Folder' if is_folder else 'File'
                    print(f"  - {name} ({item_type})")
            else:
                print("Root folder is empty or unexpected response format.")

            # List a specific folder (Shared Documents is common)
            print("\nListing 'Shared Documents' folder...")
            folder = await client.list_folder_async(
                dataset=SHAREPOINT_SITE_URL,
                id='/Shared Documents',
            )

            if folder and 'value' in folder:
                print(f"Found {len(folder['value'])} items in Shared Documents:")
                for item in folder['value'][:5]:
                    name = item.get('Name', 'Unknown')
                    is_folder = item.get('IsFolder', False)
                    size = item.get('Size', 0)
                    item_type = 'Folder' if is_folder else 'File'
                    print(f"  - {name} ({item_type}, {size} bytes)")

        except ConnectorException as ex:
            print(f"Connector error: {ex}")
            print(f"Status code: {ex.status_code}")
            if ex.status_code == 404:
                print("Hint: The folder may not exist or you may not have access.")
        except Exception as ex:
            print(f"Error: {ex}")


async def example_7_error_handling():
    """Example 7: Demonstrate error handling."""
    print("\n=== Example 7: Error Handling ===")

    credential = DefaultAzureCredential()

    async with SharepointonlineClient(CONNECTION_RUNTIME_URL, credential) as client:
        try:
            # Attempt to get an item with an invalid ID
            invalid_item_id = "99999"
            list_name = os.environ.get("TEST_LIST_NAME", "Tasks")

            item = await client.get_item_async(
                dataset=SHAREPOINT_SITE_URL,
                table=list_name,
                id=invalid_item_id,
            )
            print(f"Unexpected success: {item}")

        except ConnectorException as ex:
            print("Expected error caught:")
            print(f"  Message: {ex}")
        except Exception as ex:
            print(f"Unexpected error type: {type(ex).__name__}")
            print(f"  Message: {ex}")


async def main():
    """Run all examples."""
    print("SharePoint Online Connector SDK - Sample Usage")
    print("=" * 50)
    print()

    await example_1_get_lists()
    await example_2_get_list_items()
    await example_3_create_list_item()
    await example_4_update_list_item()
    await example_5_query_with_filters()
    await example_6_file_operations()
    await example_7_error_handling()

    print("\n" + "=" * 50)
    print("Sample completed!")


if __name__ == "__main__":
    asyncio.run(main())
