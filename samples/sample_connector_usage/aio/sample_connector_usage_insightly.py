"""
Insightly sample for the Azure Connectors Python SDK

This sample demonstrates how to use the Insightly client from the Azure Connectors Python SDK.

Prerequisites:
1. Azure subscription with Insightly connection
2. Insightly connection in Connector Namespaces
3. Connection runtime URL from Azure Portal

Installation:
    pip install azure-connectors

Usage:
    Set environment variable:
    $env:INSIGHTLY_CONNECTION_URL = "https://[region].azure-apihub.net/apim/insightly/[conn-id]"

    python sample_connector_usage_insightly.py
"""

import asyncio
import os

from azure.identity.aio import DefaultAzureCredential

from azure.connectors import ConnectorException
from azure.connectors.aio.insightly import InsightlyClient
from azure.connectors.insightly import TaskRequest


# Connection runtime URL format:
# https://[region].azure-apihub.net/apim/insightly/[connection-id]
CONNECTION_RUNTIME_URL = os.environ.get("INSIGHTLY_CONNECTION_URL", "")


async def example_1_list_tasks() -> None:
    """Example 1: List tasks."""
    print("\n=== Example 1: List Tasks ===")

    async with DefaultAzureCredential() as credential:
        async with InsightlyClient(CONNECTION_RUNTIME_URL, credential) as client:
            response = [item async for item in client.list_tasks()]
            tasks = response

            print(f"Found {len(tasks)} tasks")
            for task in tasks[:5]:
                print(f"  - {task.get('TASK_ID')}: {task.get('TITLE')}")


async def example_2_list_contacts() -> None:
    """Example 2: List contacts."""
    print("\n=== Example 2: List Contacts ===")

    async with DefaultAzureCredential() as credential:
        async with InsightlyClient(CONNECTION_RUNTIME_URL, credential) as client:
            response = [item async for item in client.list_contacts()]
            contacts = response

            print(f"Found {len(contacts)} contacts")
            for contact in contacts[:5]:
                first = contact.get("FIRST_NAME", "")
                last = contact.get("LAST_NAME", "")
                print(f"  - {contact.get('CONTACT_ID')}: {first} {last}".rstrip())


async def example_3_add_task() -> None:
    """Example 3: Add a task."""
    print("\n=== Example 3: Add Task ===")

    async with DefaultAzureCredential() as credential:
        async with InsightlyClient(CONNECTION_RUNTIME_URL, credential) as client:
            request = TaskRequest(
                t_i_t_l_e="SDK sample task",
                d_e_t_a_i_l_s="Created from insightly SDK sample.",
                s_t_a_t_u_s="NOT STARTED",
                c_o_m_p_l_e_t_e_d=False,
                p_u_b_l_i_c_l_y_v_i_s_i_b_l_e=False,
            )

            created = await client.add_task(input=request)
            print(f"Created task: {created.get('TASK_ID') if created else 'n/a'}")


async def main() -> None:
    """Run Insightly connector examples."""
    if not CONNECTION_RUNTIME_URL:
        print("Error: INSIGHTLY_CONNECTION_URL environment variable not set.")
        print("Set it to your connection runtime URL from Azure Portal.")
        return

    print("Insightly sample usage for the Azure Connectors Python SDK")
    print("=" * 50)

    try:
        await example_1_list_tasks()
        await example_2_list_contacts()
        # Uncomment to create a task in your Insightly instance.
        # await example_3_add_task()

    except ConnectorException as ex:
        print(f"Connector error: {ex}")
    except Exception as ex:
        print(f"Unexpected error: {ex}")


if __name__ == "__main__":
    asyncio.run(main())
