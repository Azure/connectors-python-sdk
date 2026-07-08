"""
Power BI Connector SDK Sample

This sample demonstrates how to use the Power BI connector SDK.

Prerequisites:
1. Azure subscription with Power BI connection
2. Power BI connection in Connector Namespaces
3. Connection runtime URL from Azure Portal

Installation:
    pip install azure-connectors

Usage:
    Set environment variable:
    $env:POWERBI_CONNECTION_URL = "https://[region].azure-apihub.net/apim/powerbi/[connection-id]"

    python sample_connector_usage_powerbi.py
"""

import asyncio
import os

from azure.identity.aio import DefaultAzureCredential

from azure.connectors import ConnectorException
from azure.connectors.powerbi import PowerbiClient


# Connection runtime URL format:
# https://[region].azure-apihub.net/apim/powerbi/[connection-id]
CONNECTION_RUNTIME_URL = os.environ.get("POWERBI_CONNECTION_URL", "")


async def example_1_list_groups() -> list[dict]:
    """Example 1: List Power BI workspaces (groups)."""
    print("\n=== Example 1: List Groups ===")

    credential = DefaultAzureCredential()
    async with PowerbiClient(CONNECTION_RUNTIME_URL, credential) as client:
        groups_response = await client.list_groups_async()
        groups = groups_response.get("value", []) if groups_response else []

        print(f"Found {len(groups)} groups")
        for group in groups[:5]:
            print(f"  - {group.get('name')} ({group.get('id')})")

        return groups


async def example_2_list_datasets(group_id: str) -> list[dict]:
    """Example 2: List datasets in a specific workspace."""
    print("\n=== Example 2: List Datasets ===")

    credential = DefaultAzureCredential()
    async with PowerbiClient(CONNECTION_RUNTIME_URL, credential) as client:
        datasets_response = await client.list_datasets_async(groupid=group_id)
        datasets = datasets_response.get("value", []) if datasets_response else []

        print(f"Found {len(datasets)} datasets in group '{group_id}'")
        for dataset in datasets[:5]:
            print(f"  - {dataset.get('name')} ({dataset.get('id')})")

        return datasets


async def example_3_refresh_dataset(group_id: str, dataset_id: str) -> None:
    """Example 3: Trigger dataset refresh."""
    print("\n=== Example 3: Refresh Dataset ===")

    credential = DefaultAzureCredential()
    async with PowerbiClient(CONNECTION_RUNTIME_URL, credential) as client:
        await client.refresh_dataset_async(groupid=group_id, datasetid=dataset_id)
        print(f"Refresh requested for dataset '{dataset_id}'")


async def main() -> None:
    """Run all examples."""
    if not CONNECTION_RUNTIME_URL:
        print("Error: POWERBI_CONNECTION_URL environment variable not set.")
        print("Set it to your connection runtime URL from Azure Portal.")
        return

    print("Power BI Connector SDK - Sample Usage")
    print("=" * 50)

    try:
        groups = await example_1_list_groups()

        if groups:
            first_group_id = groups[0].get("id")
            if first_group_id:
                datasets = await example_2_list_datasets(first_group_id)

                # Optional: trigger a refresh if at least one dataset exists.
                if datasets:
                    first_dataset_id = datasets[0].get("id")
                    if first_dataset_id:
                        await example_3_refresh_dataset(first_group_id, first_dataset_id)
            else:
                print("No group id found in first group record; skipping dataset examples.")
        else:
            print("No groups found; skipping dataset examples.")

    except ConnectorException as ex:
        print(f"Connector error: {ex}")
    except Exception as ex:
        print(f"Unexpected error: {ex}")


if __name__ == "__main__":
    asyncio.run(main())
