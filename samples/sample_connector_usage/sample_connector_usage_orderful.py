"""Orderful sample for the Azure Connectors Python SDK."""
import os

from azure.identity import DefaultAzureCredential

from azure.connectors import ConnectorException
from azure.connectors.orderful import OrderfulClient


CONNECTION_RUNTIME_URL = os.environ.get("ORDERFUL_CONNECTION_URL", "")


def main() -> None:
    """List Orderful transactions."""
    if not CONNECTION_RUNTIME_URL:
        print("Set ORDERFUL_CONNECTION_URL to run this sample.")
        return

    with DefaultAzureCredential() as credential:
        try:
            with OrderfulClient(CONNECTION_RUNTIME_URL, credential) as client:
                client.list_transactions()
                print("Transactions requested.")
        except ConnectorException as ex:
            print(f"Connector error: {ex}")


if __name__ == "__main__":
    main()
