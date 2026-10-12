"""Elfsquad Data sample for the Azure Connectors Python SDK."""
import os

from azure.identity import DefaultAzureCredential

from azure.connectors import ConnectorException
from azure.connectors.elfsquaddata import ElfsquaddataClient


CONNECTION_RUNTIME_URL = os.environ.get("ELFSQUADDATA_CONNECTION_URL", "")
ENTITY_NAME = os.environ.get("ELFSQUADDATA_ENTITY_NAME", "")


def main() -> None:
    """List entities from an Elfsquad Data entity set."""
    if not CONNECTION_RUNTIME_URL or not ENTITY_NAME:
        print(
            "Set ELFSQUADDATA_CONNECTION_URL and ELFSQUADDATA_ENTITY_NAME "
            "to run this sample."
        )
        return

    with DefaultAzureCredential() as credential:
        try:
            with ElfsquaddataClient(
                CONNECTION_RUNTIME_URL,
                credential,
            ) as client:
                entities = [item for item in client.list_entities(
                    entity_name=ENTITY_NAME,
                    top=10,
                )]
                print(f"Entities: {entities}")
        except ConnectorException as ex:
            print(f"Connector error: {ex}")


if __name__ == "__main__":
    main()
