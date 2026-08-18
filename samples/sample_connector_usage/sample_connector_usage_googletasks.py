# Copyright (c) Microsoft Corporation. All rights reserved.

"""
Google Tasks Connector SDK Sample

This sample demonstrates how to use the Google Tasks connector SDK.

Prerequisites:
1. Azure subscription with Google Tasks connection
2. Google Tasks connection in Connector Namespaces
3. Connection runtime URL from Azure Portal

Installation:
    pip install azure-connectors

Usage:
    Set environment variable:
    $env:GOOGLETASKS_CONNECTION_URL = (
        "https://[region].azure-apihub.net/apim/googletasks/[connection-id]"
    )

    python sample_connector_usage_googletasks.py
"""

import asyncio
import os

from azure.identity.aio import DefaultAzureCredential
from azure.connectors import ConnectorException
from azure.connectors.googletasks import (
    GoogletasksClient,
    TRIGGER_OPERATIONS,
    TaskCreate,
    TaskListCreate,
)

# Connection runtime URL format:
# https://[region].azure-apihub.net/apim/googletasks/[connection-id]
CONNECTION_RUNTIME_URL = os.environ.get(
    "GOOGLETASKS_CONNECTION_URL",
    "",
)


async def example_1_list_task_lists():
    """Example 1: List task lists."""
    print("\n=== Example 1: List Task Lists ===")

    credential = DefaultAzureCredential()

    async with GoogletasksClient(CONNECTION_RUNTIME_URL, credential) as client:
        result = await client.list_task_lists_async()
        items = result.get("items", []) if result else []

        print(f"Found {len(items)} task list(s).")
        for task_list in items[:10]:
            print(f"  - {task_list.get('title', 'N/A')} ({task_list.get('id', 'N/A')})")


async def example_2_create_task_list_and_task():
    """Example 2: Create a task list and task."""
    print("\n=== Example 2: Create Task List and Task ===")

    credential = DefaultAzureCredential()

    async with GoogletasksClient(CONNECTION_RUNTIME_URL, credential) as client:
        try:
            list_result = await client.create_task_list_async(
                input=TaskListCreate(title="SDK Sample List"),
            )
            task_list_id = list_result.get("id") if list_result else None

            if not task_list_id:
                print("Task list creation returned no id.")
                return

            task_result = await client.craete_task_async(
                input=TaskCreate(
                    title="Follow up sample",
                    notes="Created by azure-connectors sample.",
                    due="2026-07-10T12:00:00Z",
                ),
                task_list_id=task_list_id,
            )

            print(f"Created list id: {task_list_id}")
            print(f"Created task id: {(task_result or {}).get('id', 'N/A')}")
        except ConnectorException as ex:
            print(f"Connector error: {ex}")


def example_3_list_triggers():
    """Example 3: List trigger operations available for registration."""
    print("\n=== Example 3: Trigger Operations ===")

    for operation_id, metadata in TRIGGER_OPERATIONS.items():
        parameters = ", ".join(metadata["required_parameters"]) or "none"
        print(f"{operation_id}: required parameters: {parameters}")


async def main():
    """Run all Google Tasks connector examples."""
    if not CONNECTION_RUNTIME_URL:
        print("Error: GOOGLETASKS_CONNECTION_URL environment variable is not set.")
        print("Set it to your Google Tasks connector runtime URL from Azure Portal.")
        return

    print(f"Using connection URL: {CONNECTION_RUNTIME_URL[:50]}...")

    await example_1_list_task_lists()
    await example_2_create_task_list_and_task()
    example_3_list_triggers()

    print("\n=== Google Tasks sample completed ===")


if __name__ == "__main__":
    asyncio.run(main())
