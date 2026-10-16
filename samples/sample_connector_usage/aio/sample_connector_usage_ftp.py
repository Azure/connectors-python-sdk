# Copyright (c) Microsoft Corporation. All rights reserved.

"""Sample usage for the FTP connector client."""

import asyncio
import os

from azure.identity.aio import DefaultAzureCredential

from azure.connectors.aio.ftp import FtpClient


async def main() -> None:
    """Run a simple FTP sample flow."""
    connection_url = os.getenv("FTP_CONNECTION_URL")
    if not connection_url:
        raise ValueError("Set FTP_CONNECTION_URL environment variable")

    folder_path = os.getenv("FTP_FOLDER_PATH", "/inbound")
    file_name = os.getenv("FTP_FILE_NAME", "sample-from-sdk.txt")

    async with DefaultAzureCredential() as credential:
        async with FtpClient(connection_url, credential) as client:
            root_listing = [item async for item in client.list_root_folder()]
            print("root listing", root_listing)

            created = await client.create_file(
                input=b"hello from azure-connectors ftp sample",
                folder_path=folder_path,
                name=file_name,
            )
            print("created file", created)

            folder_items = [item async for item in client.list_folder(id=folder_path)]
            print("folder items available for polling", folder_items)


if __name__ == "__main__":
    asyncio.run(main())
