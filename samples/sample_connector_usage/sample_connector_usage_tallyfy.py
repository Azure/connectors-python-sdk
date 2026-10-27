"""Tallyfy sample for the Azure Connectors Python SDK."""

import asyncio
import os

from azure.identity.aio import DefaultAzureCredential

from azure.connectors import ConnectorException
from azure.connectors.tallyfy import TallyfyClient
from azure.connectors.tallyfy import CreateRunInput


CONNECTION_RUNTIME_URL = os.environ.get("TALLYFY_CONNECTION_URL", "")


async def list_organizations() -> None:
    """List organizations available to the current user."""
    async with DefaultAzureCredential() as credential:
        async with TallyfyClient(CONNECTION_RUNTIME_URL, credential) as client:
            organizations = await client.get_user_organizations()
            print(f"Organizations: {organizations}")


async def create_run() -> None:
    """Create a run from a checklist."""
    async with DefaultAzureCredential() as credential:
        async with TallyfyClient(CONNECTION_RUNTIME_URL, credential) as client:
            run = await client.create_run(
                input=CreateRunInput(
                    name="Quarterly review",
                    checklist_id="CHECKLIST_ID",
                    summary="Created with the Azure Connectors Python SDK.",
                ),
                org="ORGANIZATION_ID",
            )
            print(f"Created run: {run}")


async def main() -> None:
    """Run Tallyfy connector examples."""
    if not CONNECTION_RUNTIME_URL:
        print("Set TALLYFY_CONNECTION_URL to run this sample.")
        return

    try:
        await list_organizations()
        await create_run()
    except ConnectorException as ex:
        print(f"Connector error: {ex}")


if __name__ == "__main__":
    asyncio.run(main())
