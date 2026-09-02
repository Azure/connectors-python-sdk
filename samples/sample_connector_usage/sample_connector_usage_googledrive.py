# Copyright (c) Microsoft Corporation. All rights reserved.

"""
Google Drive Connector SDK Sample

This sample demonstrates how to use the Google Drive connector SDK.

Prerequisites:
1. Azure subscription with Google Drive connection
2. Google Drive connection in Connector Namespaces
3. Connection runtime URL from Azure Portal

Installation:
    pip install azure-connectors

Usage:
    Set environment variable:
    $env:GOOGLEDRIVE_CONNECTION_URL = (
        "https://[region].azure-apihub.net/apim/googledrive/[connection-id]"
    )

    python sample_connector_usage_googledrive.py
"""

import asyncio
import os

from azure.identity.aio import DefaultAzureCredential
from azure.connectors import ConnectorException
from azure.connectors.googledrive import GoogledriveClient

# Connection runtime URL format:
# https://[region].azure-apihub.net/apim/googledrive/[connection-id]
CONNECTION_RUNTIME_URL = os.environ.get(
    "GOOGLEDRIVE_CONNECTION_URL",
    "",
)


async def example_1_list_root_folder():
    """Example 1: List items in the root folder."""
    print("\n=== Example 1: List Root Folder ===")

    credential = DefaultAzureCredential()

    async with GoogledriveClient(CONNECTION_RUNTIME_URL, credential) as client:
        result = await client.list_root_folder_async()

        if result and "value" in result:
            print(f"Found {len(result['value'])} items in root folder:")
            for item in result["value"][:10]:
                icon = "[DIR]" if item.get("IsFolder") else "[FILE]"
                print(f"  {icon} {item.get('Name', 'N/A')}")
        else:
            print("No root-folder items returned.")


async def example_2_get_file_metadata_by_path():
    """Example 2: Retrieve file metadata by path."""
    print("\n=== Example 2: Get Metadata by Path ===")

    file_path = os.environ.get("GOOGLEDRIVE_TEST_FILE_PATH", "")
    if not file_path:
        print("Set GOOGLEDRIVE_TEST_FILE_PATH, for example '/Documents/report.pdf'.")
        return

    credential = DefaultAzureCredential()

    async with GoogledriveClient(CONNECTION_RUNTIME_URL, credential) as client:
        try:
            metadata = await client.get_file_metadata_by_path_async(path=file_path)

            if metadata:
                print(f"Name: {metadata.get('Name', 'N/A')}")
                print(f"Size: {metadata.get('Size', 'N/A')} bytes")
                print(f"LastModified: {metadata.get('LastModified', 'N/A')}")
            else:
                print("No metadata returned.")
        except ConnectorException as ex:
            print(f"Connector error: {ex}")


async def example_3_create_file():
    """Example 3: Upload a text file."""
    print("\n=== Example 3: Create File ===")

    destination_folder = os.environ.get("GOOGLEDRIVE_TEST_DEST_FOLDER", "/Documents")
    destination_name = os.environ.get("GOOGLEDRIVE_TEST_FILE_NAME", "sdk-sample.txt")

    credential = DefaultAzureCredential()

    async with GoogledriveClient(CONNECTION_RUNTIME_URL, credential) as client:
        try:
            result = await client.create_file_async(
                input=b"Hello from azure-connectors Google Drive sample!",
                folder_id=destination_folder,
                name=destination_name,
            )

            if result:
                print(f"Created file id: {result.get('Id', 'N/A')}")
            else:
                print("Create operation completed with no response body.")
        except ConnectorException as ex:
            print(f"Connector error: {ex}")


async def example_4_list_drive_items_for_sheet_selection():
    """Example 4: List Drive items to locate a Google Sheet file."""
    print("\n=== Example 4: Find Google Sheet Files ===")

    folder_id = os.environ.get("GOOGLEDRIVE_TEST_SHEET_FOLDER", "")
    if not folder_id:
        print("Set GOOGLEDRIVE_TEST_SHEET_FOLDER to a Drive folder id.")
        return

    credential = DefaultAzureCredential()

    async with GoogledriveClient(CONNECTION_RUNTIME_URL, credential) as client:
        try:
            result = await client.list_folder_async(id=folder_id)

            if result and "value" in result:
                print(f"Found {len(result['value'])} Drive item(s):")
                for item in result["value"]:
                    print(f"  - {item.get('Name', 'N/A')}")
            else:
                print("No Drive items returned.")
        except ConnectorException as ex:
            print(f"Connector error: {ex}")


async def main():
    """Run all Google Drive connector examples."""
    if not CONNECTION_RUNTIME_URL:
        print("Error: GOOGLEDRIVE_CONNECTION_URL environment variable is not set.")
        print("Set it to your Google Drive connector runtime URL from Azure Portal.")
        return

    print(f"Using connection URL: {CONNECTION_RUNTIME_URL[:50]}...")

    await example_1_list_root_folder()
    await example_2_get_file_metadata_by_path()
    await example_3_create_file()
    await example_4_list_drive_items_for_sheet_selection()

    print("\n=== Google Drive sample completed ===")


if __name__ == "__main__":
    asyncio.run(main())
