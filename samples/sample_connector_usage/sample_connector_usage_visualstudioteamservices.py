# ------------------------------------------------------------
# Copyright (c) Microsoft Corporation.  All rights reserved.
# ------------------------------------------------------------

"""List Azure DevOps projects with an async VSTS connector client."""

import asyncio
import os

from azure.identity.aio import DefaultAzureCredential

from azure.connectors.visualstudioteamservices import VisualstudioteamservicesClient


CONNECTION_RUNTIME_URL = os.environ.get("VISUALSTUDIOTEAMSERVICES_CONNECTION_URL", "")
ORGANIZATION = os.environ.get("AZURE_DEVOPS_ORGANIZATION", "")


async def main() -> None:
    """List projects available to the connection without changing Azure DevOps."""
    if not CONNECTION_RUNTIME_URL or not ORGANIZATION:
        print(
            "Set VISUALSTUDIOTEAMSERVICES_CONNECTION_URL and "
            "AZURE_DEVOPS_ORGANIZATION to run this sample."
        )
        return

    async with DefaultAzureCredential() as credential:
        async with VisualstudioteamservicesClient(CONNECTION_RUNTIME_URL, credential) as client:
            projects = [project async for project in client.list_projects(account=ORGANIZATION)]
            print(f"Projects: {projects}")


if __name__ == "__main__":
    asyncio.run(main())
