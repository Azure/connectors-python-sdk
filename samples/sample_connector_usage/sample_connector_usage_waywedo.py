"""Way We Do connector SDK sample."""
import os

from azure.identity import DefaultAzureCredential

from azure.connectors import ConnectorException
from azure.connectors.waywedo import WaywedoClient


CONNECTION_RUNTIME_URL = os.environ.get("WAYWEDO_CONNECTION_URL", "")


def main() -> None:
    """Find Way We Do checklists."""
    if not CONNECTION_RUNTIME_URL:
        print("Set WAYWEDO_CONNECTION_URL to run this sample.")
        return

    with DefaultAzureCredential() as credential:
        try:
            with WaywedoClient(CONNECTION_RUNTIME_URL, credential) as client:
                checklists = client.find_checklist()
                print(f"Checklists: {checklists}")
        except ConnectorException as ex:
            print(f"Connector error: {ex}")


if __name__ == "__main__":
    main()
