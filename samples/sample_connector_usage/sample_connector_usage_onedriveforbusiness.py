# Copyright (c) Microsoft Corporation. All rights reserved.

"""OneDrive for Business Connector SDK sample."""

import asyncio
import os

from azure.connectors import ConnectorException
from azure.connectors.onedriveforbusiness import OnedriveforbusinessClient
from azure.identity.aio import DefaultAzureCredential

# Connection runtime URL format:
# https://[region].azure-apihub.net/apim/onedriveforbusiness/[connection-id]
CONNECTION_RUNTIME_URL = os.environ.get("ONEDRIVEFORBUSINESS_CONNECTION_URL", "")


async def example_list_root_folder() -> None:
    """List files in the root folder."""
    credential = DefaultAzureCredential()

    async with OnedriveforbusinessClient(CONNECTION_RUNTIME_URL, credential) as client:
        result = await client.list_root_folder_async()
        values = result.get("value", []) if result else []
        print(f"Found {len(values)} items in root folder.")


async def example_get_file_metadata() -> None:
    """Get file metadata by path."""
    file_path = os.environ.get("TEST_FILE_PATH", "/Documents/report.docx")
    credential = DefaultAzureCredential()

    async with OnedriveforbusinessClient(CONNECTION_RUNTIME_URL, credential) as client:
        metadata = await client.get_file_metadata_by_path_async(path=file_path)
        if metadata:
            print(f"Name: {metadata.get('name')}, Size: {metadata.get('size')} bytes")
        else:
            print("No metadata was returned.")


async def example_create_share_link() -> None:
    """Create a share link for a file ID."""
    file_id = os.environ.get("TEST_FILE_ID")
    if not file_id:
        print("Set TEST_FILE_ID to run the share-link example.")
        return

    credential = DefaultAzureCredential()

    async with OnedriveforbusinessClient(CONNECTION_RUNTIME_URL, credential) as client:
        result = await client.create_share_link_async(id=file_id, type_="view")
        if result:
            print(f"Share URL: {result.get('webUrl')}")
        else:
            print("No share link was returned.")


async def main() -> None:
    """Run sample operations."""
    if not CONNECTION_RUNTIME_URL:
        print("Set ONEDRIVEFORBUSINESS_CONNECTION_URL before running this sample.")
        return

    try:
        await example_list_root_folder()
        await example_get_file_metadata()
        await example_create_share_link()
    except ConnectorException as ex:
        print(f"Connector error ({ex.status_code}): {ex}")


if __name__ == "__main__":
    asyncio.run(main())
