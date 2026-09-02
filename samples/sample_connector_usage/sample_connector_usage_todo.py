"""
Microsoft To Do Connector SDK Sample

This sample demonstrates how to use the Microsoft To Do connector SDK.

Prerequisites:
1. Azure subscription with Microsoft To Do connection
2. Microsoft To Do connection in Connector Namespaces
3. Connection runtime URL from Azure Portal

Installation:
    pip install azure-connectors

Usage:
    Set environment variable:
    $env:TODO_CONNECTION_URL = "https://[region].azure-apihub.net/apim/todo/[connection-id]"

    python sample_connector_usage_todo.py
"""

import asyncio
import os

from azure.identity.aio import DefaultAzureCredential

from azure.connectors import ConnectorException
from azure.connectors.todo import CreateToDo, CreateToDoList, TodoClient, UpdateToDo


# Connection runtime URL format:
# https://[region].azure-apihub.net/apim/todo/[connection-id]
CONNECTION_RUNTIME_URL = os.environ.get("TODO_CONNECTION_URL", "")


async def example_1_list_lists() -> list[dict]:
    """Example 1: List all to-do lists."""
    print("\n=== Example 1: List To-Do Lists ===")

    credential = DefaultAzureCredential()
    async with TodoClient(CONNECTION_RUNTIME_URL, credential) as client:
        lists_response = await client.get_all_todo_lists_async()
        lists = lists_response.get("value", []) if lists_response else []

        print(f"Found {len(lists)} lists")
        for todo_list in lists[:10]:
            print(f"  - {todo_list.get('displayName')} ({todo_list.get('id')})")

        return lists


async def example_2_create_list() -> str | None:
    """Example 2: Create a to-do list."""
    print("\n=== Example 2: Create To-Do List ===")

    credential = DefaultAzureCredential()
    async with TodoClient(CONNECTION_RUNTIME_URL, credential) as client:
        request = CreateToDoList(display_name="SDK Sample List")
        created = await client.create_to_do_list_async(input=request)

        if not created:
            print("No list was created")
            return None

        list_id = created.get("id")
        print(f"Created list id: {list_id}")
        return list_id


async def example_3_create_and_update_todo(list_id: str) -> None:
    """Example 3: Create and update a to-do item."""
    print("\n=== Example 3: Create And Update To-Do ===")

    credential = DefaultAzureCredential()
    async with TodoClient(CONNECTION_RUNTIME_URL, credential) as client:
        create_request = CreateToDo(title="SDK sample task", status="notStarted")
        created_todo = await client.create_to_do_async(input=create_request, folder_id=list_id)

        if not created_todo:
            print("No to-do item returned from create operation")
            return

        todo_id = created_todo.get("id")
        print(f"Created to-do id: {todo_id}")

        if not todo_id:
            return

        update_request = UpdateToDo(title="SDK sample task (updated)", status="inProgress")
        updated_todo = await client.update_to_do_async(
            input=update_request,
            folder_id=list_id,
            id=todo_id,
        )
        print(f"Updated title: {updated_todo.get('title') if updated_todo else 'n/a'}")


async def main() -> None:
    """Run all examples."""
    if not CONNECTION_RUNTIME_URL:
        print("Error: TODO_CONNECTION_URL environment variable not set.")
        print("Set it to your connection runtime URL from Azure Portal.")
        return

    print("Microsoft To Do Connector SDK - Sample Usage")
    print("=" * 50)

    try:
        await example_1_list_lists()
        list_id = await example_2_create_list()

        if list_id:
            await example_3_create_and_update_todo(list_id)
        else:
            print("Skipping to-do create/update because no list id was returned.")

    except ConnectorException as ex:
        print(f"Connector error: {ex}")
    except Exception as ex:
        print(f"Unexpected error: {ex}")


if __name__ == "__main__":
    asyncio.run(main())
