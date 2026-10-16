"""Replicon sample for the Azure Connectors Python SDK."""
import os

from azure.identity import DefaultAzureCredential

from azure.connectors import ConnectorException
from azure.connectors.replicon import RepliconClient


CONNECTION_RUNTIME_URL = os.environ.get("REPLICON_CONNECTION_URL", "")


def main() -> None:
    """Get Replicon tenant endpoint details."""
    if not CONNECTION_RUNTIME_URL:
        print("Set REPLICON_CONNECTION_URL to run this sample.")
        return

    with DefaultAzureCredential() as credential:
        try:
            with RepliconClient(CONNECTION_RUNTIME_URL, credential) as client:
                endpoint = client.get_my_tenant_endpoint_details()
                print(f"Tenant endpoint: {endpoint}")
        except ConnectorException as ex:
            print(f"Connector error: {ex}")


if __name__ == "__main__":
    main()
