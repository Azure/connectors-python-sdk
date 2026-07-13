# Copyright (c) Microsoft Corporation. All rights reserved.

"""Sample usage for the Office 365 Groups Mail connector client."""

import asyncio
import os

from azure.connectors.office365groupsmail import Office365groupsmailClient


async def main() -> None:
    """Run a simple Office 365 Groups Mail sample flow."""
    connection_url = os.getenv("OFFICE365GROUPSMAIL_CONNECTION_URL")
    if not connection_url:
        raise ValueError("Set OFFICE365GROUPSMAIL_CONNECTION_URL environment variable")

    group_id = os.getenv("OFFICE365GROUPSMAIL_GROUP_ID")
    if not group_id:
        raise ValueError("Set OFFICE365GROUPSMAIL_GROUP_ID environment variable")

    async with Office365groupsmailClient(connection_url) as client:
        conversations = await client.list_conversations_async(group_id=group_id)
        conversation_count = len((conversations or {}).get("value", []))
        print(f"Found {conversation_count} conversation(s) in group '{group_id}'.")

        groups = await client.list_groups_async()
        group_count = len((groups or {}).get("value", []))
        print(f"Current user is in {group_count} Office 365 group(s).")


if __name__ == "__main__":
    asyncio.run(main())
