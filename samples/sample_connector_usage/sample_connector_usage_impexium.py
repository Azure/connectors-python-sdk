"""Impexium connector SDK sample."""
import os

from azure.identity import DefaultAzureCredential

from azure.connectors import ConnectorException
from azure.connectors.impexium import ImpexiumClient


CONNECTION_RUNTIME_URL = os.environ.get("IMPEXIUM_CONNECTION_URL", "")


def main() -> None:
    """List countries from Impexium."""
    if not CONNECTION_RUNTIME_URL:
        print("Set IMPEXIUM_CONNECTION_URL to run this sample.")
        return

    with DefaultAzureCredential() as credential:
        try:
            with ImpexiumClient(CONNECTION_RUNTIME_URL, credential) as client:
                countries = client.list_all_countries(page_number=1)
                print(f"Countries: {countries}")
        except ConnectorException as ex:
            print(f"Connector error: {ex}")


if __name__ == "__main__":
    main()
