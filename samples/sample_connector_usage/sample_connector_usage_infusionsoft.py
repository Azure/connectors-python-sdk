"""
Infusionsoft (Keap) Connector SDK Sample

This sample demonstrates how to use the Infusionsoft connector SDK.

Prerequisites:
1. Azure subscription with Infusionsoft connection
2. Infusionsoft connection in Connector Namespaces
3. Connection runtime URL from Azure Portal

Installation:
    pip install azure-connectors

Usage:
    Set environment variable:
    $env:INFUSIONSOFT_CONNECTION_URL = "https://[region].azure-apihub.net/apim/infusionsoft/[id]"

    python sample_connector_usage_infusionsoft.py
"""

import asyncio
import os

from azure.identity.aio import DefaultAzureCredential

from azure.connectors import ConnectorException
from azure.connectors.infusionsoft import CreateTaskRequest, InfusionsoftClient


# Connection runtime URL format:
# https://[region].azure-apihub.net/apim/infusionsoft/[connection-id]
CONNECTION_RUNTIME_URL = os.environ.get("INFUSIONSOFT_CONNECTION_URL", "")


async def example_1_list_tasks() -> None:
    """Example 1: List tasks ordered by due date."""
    print("\n=== Example 1: List Tasks ===")

    credential = DefaultAzureCredential()
    async with InfusionsoftClient(CONNECTION_RUNTIME_URL, credential) as client:
        response = await client.list_tasks_async()
        tasks = response.get("tasks", []) if response else []

        print(f"Found {len(tasks)} tasks")
        for task in tasks[:5]:
            print(f"  - {task.get('id')}: {task.get('title')}")


async def example_2_create_task() -> None:
    """Example 2: Create a task."""
    print("\n=== Example 2: Create Task ===")

    credential = DefaultAzureCredential()
    async with InfusionsoftClient(CONNECTION_RUNTIME_URL, credential) as client:
        request = CreateTaskRequest(
            title="SDK sample task",
            description="Created from the infusionsoft SDK sample.",
            priority=1,
        )

        created = await client.create_task_async(input=request)
        print(f"Created task: {created.get('id') if created else 'n/a'}")


async def example_3_update_task() -> None:
    """Example 3: Update an existing task."""
    print("\n=== Example 3: Update Task ===")

    credential = DefaultAzureCredential()
    async with InfusionsoftClient(CONNECTION_RUNTIME_URL, credential) as client:
        request = CreateTaskRequest(
            title="Updated SDK sample task",
            description="Updated from the infusionsoft SDK sample.",
        )

        updated = await client.update_task_async(input=request, id=1)
        print(f"Updated task: {updated.get('id') if updated else 'n/a'}")


async def main() -> None:
    """Run Infusionsoft connector examples."""
    if not CONNECTION_RUNTIME_URL:
        print("Error: INFUSIONSOFT_CONNECTION_URL environment variable not set.")
        print("Set it to your connection runtime URL from Azure Portal.")
        return

    print("Infusionsoft (Keap) Connector SDK - Sample Usage")
    print("=" * 50)

    try:
        await example_1_list_tasks()
        # Uncomment to create or update a task in your Infusionsoft instance.
        # await example_2_create_task()
        # await example_3_update_task()

    except ConnectorException as ex:
        print(f"Connector error: {ex}")
    except Exception as ex:
        print(f"Unexpected error: {ex}")


if __name__ == "__main__":
    asyncio.run(main())
