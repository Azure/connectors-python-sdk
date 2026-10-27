# ------------------------------------------------------------
# Copyright (c) Microsoft Corporation.  All rights reserved.
# ------------------------------------------------------------

"""List Power Query Dataflows workspaces or environments with an async client."""

import asyncio
import os

from azure.identity.aio import DefaultAzureCredential

from azure.connectors.dataflows import DataflowsClient


CONNECTION_RUNTIME_URL = os.environ.get("DATAFLOWS_CONNECTION_URL", "")
WORKSPACE_TYPE = os.environ.get("DATAFLOWS_WORKSPACE_TYPE", "Workspace")


async def main() -> None:
    """List groups available to the connection without starting a refresh."""
    if not CONNECTION_RUNTIME_URL:
        print("Set DATAFLOWS_CONNECTION_URL to run this sample.")
        return

    async with DefaultAzureCredential() as credential:
        async with DataflowsClient(CONNECTION_RUNTIME_URL, credential) as client:
            groups = [
                group
                async for group in client.list_groups_for_refresh_dataflow(
                    workspace_type=WORKSPACE_TYPE,
                )
            ]
            print(f"Workspaces or environments: {groups}")


if __name__ == "__main__":
    asyncio.run(main())
