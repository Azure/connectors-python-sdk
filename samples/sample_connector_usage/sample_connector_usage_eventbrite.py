"""Eventbrite sample for the Azure Connectors Python SDK."""
import os

from azure.identity import DefaultAzureCredential

from azure.connectors import ConnectorException
from azure.connectors.eventbrite import EventbriteClient


CONNECTION_RUNTIME_URL = os.environ.get("EVENTBRITE_CONNECTION_URL", "")


def main() -> None:
    """List Eventbrite event categories."""
    if not CONNECTION_RUNTIME_URL:
        print("Set EVENTBRITE_CONNECTION_URL to run this sample.")
        return

    with DefaultAzureCredential() as credential:
        try:
            with EventbriteClient(CONNECTION_RUNTIME_URL, credential) as client:
                categories = client.list_categories()
                print(f"Categories: {categories}")
        except ConnectorException as ex:
            print(f"Connector error: {ex}")


if __name__ == "__main__":
    main()
