"""Etsy connector SDK sample."""
import os

from azure.identity import DefaultAzureCredential

from azure.connectors import ConnectorException
from azure.connectors.etsy import EtsyClient


CONNECTION_RUNTIME_URL = os.environ.get("ETSY_CONNECTION_URL", "")


def main() -> None:
    """Ping the Etsy connector."""
    if not CONNECTION_RUNTIME_URL:
        print("Set ETSY_CONNECTION_URL to run this sample.")
        return

    with DefaultAzureCredential() as credential:
        try:
            with EtsyClient(CONNECTION_RUNTIME_URL, credential) as client:
                result = client.ping()
                print(f"Result: {result}")
        except ConnectorException as ex:
            print(f"Connector error: {ex}")


if __name__ == "__main__":
    main()
