# Copyright (c) Microsoft Corporation. All rights reserved.

"""Sample usage for the FTP connector client."""

import asyncio
import os

from azure.connectors.ftp import FtpClient


async def main() -> None:
    """Run a simple FTP sample flow."""
    connection_url = os.getenv("FTP_CONNECTION_URL")
    if not connection_url:
        raise ValueError("Set FTP_CONNECTION_URL environment variable")

    folder_path = os.getenv("FTP_FOLDER_PATH", "/inbound")
    file_name = os.getenv("FTP_FILE_NAME", "sample-from-sdk.txt")

    async with FtpClient(connection_url) as client:
        root_listing = await client.list_root_folder_async()
        print("root listing", root_listing)

        created = await client.create_file_async(
            input=b"hello from azure-connectors ftp sample",
            folder_path=folder_path,
            name=file_name,
        )
        print("created file", created)

        folder_items = await client.list_folder_async(id=folder_path)
        print("folder items available for polling", folder_items)


if __name__ == "__main__":
    asyncio.run(main())
