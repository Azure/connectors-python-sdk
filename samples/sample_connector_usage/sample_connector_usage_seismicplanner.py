"""Seismic Planner connector SDK sample."""

import asyncio
import os

from azure.identity.aio import DefaultAzureCredential

from azure.connectors import ConnectorException
from azure.connectors.seismicplanner import SeismicplannerClient


CONNECTION_RUNTIME_URL = os.environ.get("SEISMICPLANNER_CONNECTION_URL", "")
SPACE_ID = os.environ.get("SEISMICPLANNER_SPACE_ID", "")


async def main() -> None:
    """List projects in a Seismic Planner space."""
    if not CONNECTION_RUNTIME_URL or not SPACE_ID:
        print("Set SEISMICPLANNER_CONNECTION_URL and SEISMICPLANNER_SPACE_ID to run this sample.")
        return

    credential = DefaultAzureCredential()
    try:
        async with SeismicplannerClient(CONNECTION_RUNTIME_URL, credential) as client:
            projects = await client.get_projects_async(space_id=SPACE_ID)
            print(f"Projects: {projects}")
    except ConnectorException as ex:
        print(f"Connector error: {ex}")


if __name__ == "__main__":
    asyncio.run(main())