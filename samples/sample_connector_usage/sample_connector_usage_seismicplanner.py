"""Seismic Planner sample for the Azure Connectors Python SDK."""
import os

from azure.identity import DefaultAzureCredential

from azure.connectors import ConnectorException
from azure.connectors.seismicplanner import SeismicplannerClient


CONNECTION_RUNTIME_URL = os.environ.get("SEISMICPLANNER_CONNECTION_URL", "")
SPACE_ID = os.environ.get("SEISMICPLANNER_SPACE_ID", "")


def main() -> None:
    """List projects in a Seismic Planner space."""
    if not CONNECTION_RUNTIME_URL or not SPACE_ID:
        print("Set SEISMICPLANNER_CONNECTION_URL and SEISMICPLANNER_SPACE_ID to run this sample.")
        return

    with DefaultAzureCredential() as credential:
        try:
            with SeismicplannerClient(
                CONNECTION_RUNTIME_URL,
                credential,
            ) as client:
                projects = client.get_projects(space_id=SPACE_ID)
                print(f"Projects: {projects}")
        except ConnectorException as ex:
            print(f"Connector error: {ex}")


if __name__ == "__main__":
    main()
