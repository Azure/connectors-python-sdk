"""Tallyfy connector SDK sample."""
import os

from azure.identity import DefaultAzureCredential

from azure.connectors import ConnectorException
from azure.connectors.tallyfy import CreateRunInput, TallyfyClient


CONNECTION_RUNTIME_URL = os.environ.get("TALLYFY_CONNECTION_URL", "")


def list_organizations() -> None:
    """List organizations available to the current user."""
    with DefaultAzureCredential() as credential:
        with TallyfyClient(CONNECTION_RUNTIME_URL, credential) as client:
            organizations = client.get_user_organizations()
            print(f"Organizations: {organizations}")


def create_run() -> None:
    """Create a run from a checklist."""
    with DefaultAzureCredential() as credential:
        with TallyfyClient(CONNECTION_RUNTIME_URL, credential) as client:
            run = client.create_run(
                input=CreateRunInput(
                    name="Quarterly review",
                    checklist_id="CHECKLIST_ID",
                    summary="Created with the Azure Connectors Python SDK.",
                ),
                org="ORGANIZATION_ID",
            )
            print(f"Created run: {run}")


def main() -> None:
    """Run Tallyfy connector examples."""
    if not CONNECTION_RUNTIME_URL:
        print("Set TALLYFY_CONNECTION_URL to run this sample.")
        return

    try:
        list_organizations()
        create_run()
    except ConnectorException as ex:
        print(f"Connector error: {ex}")


if __name__ == "__main__":
    main()
