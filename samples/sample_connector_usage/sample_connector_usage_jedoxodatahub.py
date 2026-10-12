"""Jedox OData Hub connector SDK sample."""
import os

from azure.identity import DefaultAzureCredential

from azure.connectors import ConnectorException
from azure.connectors.jedoxodatahub import JedoxodatahubClient


CONNECTION_RUNTIME_URL = os.environ.get("JEDOXODATAHUB_CONNECTION_URL", "")


def main() -> None:
    """List Jedox databases."""
    if not CONNECTION_RUNTIME_URL:
        print("Set JEDOXODATAHUB_CONNECTION_URL to run this sample.")
        return

    with DefaultAzureCredential() as credential:
        try:
            with JedoxodatahubClient(
                CONNECTION_RUNTIME_URL,
                credential,
            ) as client:
                databases = client.databases()
                print(f"Databases: {databases}")
        except ConnectorException as ex:
            print(f"Connector error: {ex}")


if __name__ == "__main__":
    main()
