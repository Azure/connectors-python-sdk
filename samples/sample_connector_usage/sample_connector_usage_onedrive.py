# Copyright (c) Microsoft Corporation. All rights reserved.

"""
OneDrive Connector SDK Sample

This sample demonstrates how to use the OneDrive connector SDK.

Prerequisites:
1. Azure subscription with OneDrive connection
2. OneDrive connection in Connector Namespaces (with OAuth consent)
3. Connection runtime URL from Azure Portal

Installation:
    pip install azure-connectors

Usage:
    Set environment variables:
    $env:ONEDRIVE_CONNECTION_URL = "https://[region].azure-apihub.net/apim/onedrive/[connection-id]"

    python sample_connector_usage_onedrive.py
"""

import asyncio
import os
from azure.identity.aio import DefaultAzureCredential
from azure.connectors import ConnectorException
from azure.connectors.onedrive import OnedriveClient

# Connection runtime URL format:
# https://[region].azure-apihub.net/apim/onedrive/[connection-id]
CONNECTION_RUNTIME_URL = os.environ.get(
    "ONEDRIVE_CONNECTION_URL",
    ""
)


async def example_1_list_root_folder():
    """Example 1: List files in root folder."""
    print("\n=== Example 1: List Root Folder ===")

    credential = DefaultAzureCredential()

    async with OnedriveClient(CONNECTION_RUNTIME_URL, credential) as client:
        result = await client.list_root_folder_async()

        if result and "value" in result:
            print(f"Found {len(result['value'])} items in root folder:")
            for item in result["value"][:10]:  # Show first 10
                item_type = "📁" if item.get("IsFolder") else "📄"
                print(f"  {item_type} {item.get('Name', 'N/A')}")
        else:
            print("No items found in root folder.")


async def example_2_get_file_metadata():
    """Example 2: Get file metadata by path."""
    print("\n=== Example 2: Get File Metadata ===")

    file_path = os.environ.get("TEST_FILE_PATH", "")
    if not file_path:
        print("Set TEST_FILE_PATH environment variable to a file path.")
        print("Example: $env:TEST_FILE_PATH = '/Documents/report.docx'")
        return

    credential = DefaultAzureCredential()

    async with OnedriveClient(CONNECTION_RUNTIME_URL, credential) as client:
        try:
            metadata = await client.get_file_metadata_by_path_async(path=file_path)

            if metadata:
                print(f"File Metadata for '{file_path}':")
                print(f"  ID: {metadata.get('Id', 'N/A')}")
                print(f"  Name: {metadata.get('Name', 'N/A')}")
                print(f"  Size: {metadata.get('Size', 'N/A')} bytes")
                print(f"  Last Modified: {metadata.get('LastModified', 'N/A')}")
                print(f"  Media Type: {metadata.get('MediaType', 'N/A')}")
            else:
                print(f"No metadata returned for: {file_path}")
        except ConnectorException as e:
            print(f"Error getting file metadata: {e}")


async def example_3_download_file():
    """Example 3: Download file content."""
    print("\n=== Example 3: Download File Content ===")

    file_path = os.environ.get("TEST_FILE_PATH", "")
    if not file_path:
        print("Set TEST_FILE_PATH environment variable to a file path.")
        return

    credential = DefaultAzureCredential()

    async with OnedriveClient(CONNECTION_RUNTIME_URL, credential) as client:
        try:
            content = await client.get_file_content_by_path_async(path=file_path)

            if content:
                print(f"Downloaded {len(content)} bytes")
                # Show first 100 characters if text-like
                try:
                    preview = content[:100].decode('utf-8')
                    print(f"Content preview: {preview}...")
                except UnicodeDecodeError:
                    print("Content is binary data.")
            else:
                print("No content returned.")
        except ConnectorException as e:
            print(f"Error downloading file: {e}")


async def example_4_list_folder():
    """Example 4: List files in a specific folder."""
    print("\n=== Example 4: List Folder Contents ===")

    folder_id = os.environ.get("TEST_FOLDER_ID", "")
    if not folder_id:
        print("Set TEST_FOLDER_ID environment variable to a folder ID.")
        print("You can get folder IDs from list_root_folder_async results.")
        return

    credential = DefaultAzureCredential()

    async with OnedriveClient(CONNECTION_RUNTIME_URL, credential) as client:
        try:
            result = await client.list_folder_async(id=folder_id)

            if result and "value" in result:
                print(f"Found {len(result['value'])} items:")
                for item in result["value"][:10]:
                    item_type = "📁" if item.get("IsFolder") else "📄"
                    size = item.get("Size", 0)
                    print(f"  {item_type} {item.get('Name', 'N/A')} ({size} bytes)")
            else:
                print("No items found in folder.")
        except ConnectorException as e:
            print(f"Error listing folder: {e}")


async def example_5_search_files():
    """Example 5: Search for files in a folder."""
    print("\n=== Example 5: Search Files ===")

    folder_id = os.environ.get("TEST_FOLDER_ID", "")
    search_query = os.environ.get("TEST_SEARCH_QUERY", "report")

    if not folder_id:
        print("Set TEST_FOLDER_ID environment variable to search in a folder.")
        return

    credential = DefaultAzureCredential()

    async with OnedriveClient(CONNECTION_RUNTIME_URL, credential) as client:
        try:
            result = await client.find_files_async(
                id=folder_id,
                query=search_query,
                find_mode="search"
            )

            if result and "value" in result:
                print(f"Found {len(result['value'])} files matching '{search_query}':")
                for item in result["value"]:
                    print(f"  📄 {item.get('Name', 'N/A')}")
            else:
                print(f"No files found matching '{search_query}'.")
        except ConnectorException as e:
            print(f"Error searching files: {e}")


async def example_6_create_share_link():
    """Example 6: Create a share link for a file."""
    print("\n=== Example 6: Create Share Link ===")

    file_id = os.environ.get("TEST_FILE_ID", "")
    if not file_id:
        print("Set TEST_FILE_ID environment variable to create a share link.")
        return

    credential = DefaultAzureCredential()

    async with OnedriveClient(CONNECTION_RUNTIME_URL, credential) as client:
        try:
            result = await client.create_share_link_async(
                id=file_id,
                type_="view"  # "view" or "edit"
            )

            if result and "webUrl" in result:
                print("Share link created:")
                print(f"  URL: {result['webUrl']}")
            else:
                print("Failed to create share link.")
        except ConnectorException as e:
            print(f"Error creating share link: {e}")


async def example_7_file_tags():
    """Example 7: Manage file tags."""
    print("\n=== Example 7: Manage File Tags ===")

    file_id = os.environ.get("TEST_FILE_ID", "")
    if not file_id:
        print("Set TEST_FILE_ID environment variable to manage tags.")
        return

    credential = DefaultAzureCredential()

    async with OnedriveClient(CONNECTION_RUNTIME_URL, credential) as client:
        try:
            # Get existing tags
            tags_result = await client.get_file_tags_async(id=file_id)

            if tags_result and "tags" in tags_result:
                print(f"Current tags: {', '.join(tags_result['tags'])}")
            else:
                print("No tags found on file.")

            # Add a new tag
            print("Adding tag 'sdk-sample'...")
            await client.add_file_tag_async(id=file_id, tag="sdk-sample")

            # Get updated tags
            tags_result = await client.get_file_tags_async(id=file_id)
            if tags_result and "tags" in tags_result:
                print(f"Updated tags: {', '.join(tags_result['tags'])}")
        except ConnectorException as e:
            print(f"Error managing tags: {e}")


async def example_8_copy_file():
    """Example 8: Copy a file within OneDrive."""
    print("\n=== Example 8: Copy File ===")

    file_id = os.environ.get("TEST_FILE_ID", "")
    dest_folder = os.environ.get("TEST_DEST_FOLDER", "/Documents/Copies")

    if not file_id:
        print("Set TEST_FILE_ID environment variable to copy a file.")
        return

    credential = DefaultAzureCredential()

    async with OnedriveClient(CONNECTION_RUNTIME_URL, credential) as client:
        try:
            result = await client.copy_drive_file_async(
                id=file_id,
                destination=dest_folder,
                overwrite="false"
            )

            if result:
                print("File copied successfully:")
                print(f"  New ID: {result.get('Id', 'N/A')}")
                print(f"  New Name: {result.get('Name', 'N/A')}")
            else:
                print("Copy operation returned no result.")
        except ConnectorException as e:
            print(f"Error copying file: {e}")


async def main():
    """Run all examples."""
    if not CONNECTION_RUNTIME_URL:
        print("ERROR: ONEDRIVE_CONNECTION_URL environment variable not set.")
        print("\nTo get your connection URL:")
        print("1. Go to Azure Portal > Connector Namespaces")
        print("2. Create or select a OneDrive connection")
        print("3. Copy the 'Connection Runtime URL'")
        print("\nExample:")
        url_example = "https://eastus.azure-apihub.net/apim/onedrive/abc123"
        print(f"$env:ONEDRIVE_CONNECTION_URL = '{url_example}'")
        return

    print("OneDrive Connector SDK Sample")
    print("=" * 50)
    print(f"Connection URL: {CONNECTION_RUNTIME_URL[:50]}...")

    try:
        await example_1_list_root_folder()
        await example_2_get_file_metadata()
        await example_3_download_file()
        await example_4_list_folder()
        await example_5_search_files()
        await example_6_create_share_link()
        await example_7_file_tags()
        await example_8_copy_file()
    except Exception as e:
        print(f"\nUnexpected error: {e}")
        raise

    print("\n" + "=" * 50)
    print("Sample completed!")


if __name__ == "__main__":
    asyncio.run(main())
