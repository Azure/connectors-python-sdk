"""Ticketmaster sample for the Azure Connectors Python SDK."""
import os

from azure.identity import DefaultAzureCredential

from azure.connectors import ConnectorException
from azure.connectors.ticketmaster import TicketmasterClient


CONNECTION_RUNTIME_URL = os.environ.get("TICKETMASTER_CONNECTION_URL", "")


def main() -> None:
    """List Ticketmaster attractions."""
    if not CONNECTION_RUNTIME_URL:
        print("Set TICKETMASTER_CONNECTION_URL to run this sample.")
        return

    with DefaultAzureCredential() as credential:
        try:
            with TicketmasterClient(CONNECTION_RUNTIME_URL, credential) as client:
                attractions = client.attractions_get()
                print(f"Attractions: {attractions}")
        except ConnectorException as ex:
            print(f"Connector error: {ex}")


if __name__ == "__main__":
    main()
