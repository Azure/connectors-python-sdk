"""Meeting Room Map sample for the Azure Connectors Python SDK."""
import os

from azure.identity import DefaultAzureCredential

from azure.connectors import ConnectorException
from azure.connectors.meetingroommap import MeetingroommapClient


CONNECTION_RUNTIME_URL = os.environ.get("MEETINGROOMMAP_CONNECTION_URL", "")


def main() -> None:
    """List Meeting Room Map location categories."""
    if not CONNECTION_RUNTIME_URL:
        print("Set MEETINGROOMMAP_CONNECTION_URL to run this sample.")
        return

    with DefaultAzureCredential() as credential:
        try:
            with MeetingroommapClient(
                CONNECTION_RUNTIME_URL,
                credential,
            ) as client:
                categories = client.get_categories()
                print(f"Categories: {categories}")
        except ConnectorException as ex:
            print(f"Connector error: {ex}")


if __name__ == "__main__":
    main()
