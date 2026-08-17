"""
Microsoft Planner Connector SDK Sample

This sample demonstrates how to use the Planner connector SDK.

Prerequisites:
1. Azure subscription with Planner connection
2. Planner connection in Connector Namespaces
3. Connection runtime URL from Azure Portal

Installation:
    pip install azure-connectors

Usage:
    Set environment variable:
    $env:PLANNER_CONNECTION_URL = "https://[region].azure-apihub.net/apim/planner/[connection-id]"

    python sample_connector_usage_planner.py
"""

import asyncio
import os
from azure.identity.aio import DefaultAzureCredential
from azure.connectors.planner import (
    PlannerClient,
    CreateTaskRequest,
    CreateBucketInput,
    UpdateTaskRequest,
)

# Connection runtime URL format:
# https://[region].azure-apihub.net/apim/planner/[connection-id]
CONNECTION_RUNTIME_URL = os.environ.get(
    "PLANNER_CONNECTION_URL",
    ""
)


async def example_1_list_my_tasks():
    """Example 1: List all tasks assigned to me"""
    print("\n=== Example 1: List My Tasks ===")

    credential = DefaultAzureCredential()
    client = PlannerClient(CONNECTION_RUNTIME_URL, credential)

    try:
        tasks = await client.list_my_tasks_async()

        if tasks and tasks.get('value'):
            print(f"Found {len(tasks.get('value', []))} tasks assigned to me")
            for task in tasks.get('value', [])[:5]:  # Show first 5
                print(f"  - {task.get('title')} ({task.get('percentComplete')}% complete)")
        else:
            print("No tasks assigned to me")

    except Exception as ex:
        print(f"Error: {ex}")


async def example_2_list_group_plans(group_id: str):
    """Example 2: List all plans in a group"""
    print("\n=== Example 2: List Group Plans ===")

    credential = DefaultAzureCredential()
    client = PlannerClient(CONNECTION_RUNTIME_URL, credential)

    try:
        plans = await client.list_group_plans_async(group_id=group_id)

        if plans and plans.get('value'):
            print(f"Found {len(plans.get('value', []))} plans in group")
            for plan in plans.get('value', [])[:5]:  # Show first 5
                print(f"  - {plan.get('title')} ({plan.get('id')})")
        else:
            print("No plans found in group")

    except Exception as ex:
        print(f"Error: {ex}")


async def example_3_get_task_details(task_id: str):
    """Example 3: Get task and task details"""
    print("\n=== Example 3: Get Task Details ===")

    credential = DefaultAzureCredential()
    client = PlannerClient(CONNECTION_RUNTIME_URL, credential)

    try:
        # Get basic task info
        task = await client.get_task_async(id=task_id)
        if task:
            print(f"Task: {task.get('title')}")
            print(f"  - Percent Complete: {task.get('percentComplete')}%")
            print(f"  - Created: {task.get('createdDateTime')}")

        # Get detailed task info
        details = await client.get_task_details_async(id=task_id)
        if details:
            print(f"  - Description: {details.get('description', 'No description')}")

    except Exception as ex:
        print(f"Error: {ex}")


async def example_4_create_bucket(group_id: str, plan_id: str):
    """Example 4: Create a new bucket in a plan"""
    print("\n=== Example 4: Create Bucket ===")

    credential = DefaultAzureCredential()
    client = PlannerClient(CONNECTION_RUNTIME_URL, credential)

    try:
        bucket_input = CreateBucketInput(
            name="New Bucket",
            group_id=group_id,
            plan_id=plan_id
        )

        bucket = await client.create_bucket_async(input=bucket_input)

        if bucket:
            print(f"Created bucket: {bucket.get('name')} ({bucket.get('id')})")

    except Exception as ex:
        print(f"Error: {ex}")


async def example_5_create_and_update_task(group_id: str, plan_id: str, bucket_id: str):
    """Example 5: Create and update a task"""
    print("\n=== Example 5: Create and Update Task ===")

    credential = DefaultAzureCredential()
    client = PlannerClient(CONNECTION_RUNTIME_URL, credential)

    try:
        # Create a new task
        task_input = CreateTaskRequest(
            group_id=group_id,
            plan_id=plan_id,
            bucket_id=bucket_id,
            title="Sample Task from SDK",
            priority=5  # Medium priority
        )

        task = await client.create_task_async(input=task_input)

        if task:
            task_id = task.get('id')
            print(f"Created task: {task.get('title')} ({task_id})")

            # Update the task
            update_input = UpdateTaskRequest(
                title="Updated Sample Task",
                percent_complete=50
            )

            updated = await client.update_task_async(input=update_input, id=task_id)

            if updated:
                print("Updated task to 50% complete")

            # Clean up - delete the task
            await client.delete_task_async(id=task_id)
            print("Deleted task")

    except Exception as ex:
        print(f"Error: {ex}")


async def example_6_get_plan_details(plan_id: str):
    """Example 6: Get plan details"""
    print("\n=== Example 6: Get Plan Details ===")

    credential = DefaultAzureCredential()
    client = PlannerClient(CONNECTION_RUNTIME_URL, credential)

    try:
        details = await client.get_plan_details_async(id=plan_id)

        if details:
            print(f"Plan ID: {details.get('id')}")
            categories = details.get('categoryDescriptions', {})
            if categories:
                print("Categories:")
                for key, value in categories.items():
                    if value:
                        print(f"  - {key}: {value}")

    except Exception as ex:
        print(f"Error: {ex}")


async def main():
    """Run all examples"""
    print("Planner Connector SDK - Sample Usage")
    print("=" * 50)
    print()

    # Example 1: List my tasks (no parameters needed)
    await example_1_list_my_tasks()

    # Examples 2-6 require IDs from your Planner
    # Replace these with actual values from your environment
    group_id = ""  # Microsoft 365 Group ID
    plan_id = ""  # Plan ID
    task_id = ""  # Task ID

    if group_id:
        await example_2_list_group_plans(group_id)

    if task_id:
        await example_3_get_task_details(task_id)

    if plan_id:
        await example_6_get_plan_details(plan_id)

    # NOTE: Examples 4 and 5 create resources
    # Uncomment to run them with valid IDs:
    # bucket_id = ""  # Bucket ID
    # if group_id and plan_id:
    #     await example_4_create_bucket(group_id, plan_id)
    # if group_id and plan_id and bucket_id:
    #     await example_5_create_and_update_task(group_id, plan_id, bucket_id)

    print("\n" + "=" * 50)
    print("Sample completed!")


if __name__ == "__main__":
    asyncio.run(main())


if __name__ == "__main__":
    asyncio.run(main())
