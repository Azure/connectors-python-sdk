"""
Microsoft Planner sample for the Azure Connectors Python SDK

This sample demonstrates how to use the Planner client from the Azure Connectors Python SDK.

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
import os
from azure.identity import DefaultAzureCredential
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


def example_1_list_my_tasks():
    """Example 1: List all tasks assigned to me"""
    print("\n=== Example 1: List My Tasks ===")

    with DefaultAzureCredential() as credential:
        client = PlannerClient(CONNECTION_RUNTIME_URL, credential)

        try:
            tasks = [
                task for task in client.list_my_tasks()
            ]

            if tasks:
                print(f"Found {len(tasks)} tasks assigned to me")
                for task in tasks[:5]:  # Show first 5
                    print(f"  - {task.get('title')} ({task.get('percentComplete')}% complete)")
            else:
                print("No tasks assigned to me")

        except Exception as ex:
            print(f"Error: {ex}")


def example_2_list_group_plans(group_id: str):
    """Example 2: List all plans in a group"""
    print("\n=== Example 2: List Group Plans ===")

    with DefaultAzureCredential() as credential:
        client = PlannerClient(CONNECTION_RUNTIME_URL, credential)

        try:
            plans = client.list_group_plans(group_id=group_id)

            if plans and plans.get('value'):
                print(f"Found {len(plans.get('value', []))} plans in group")
                for plan in plans.get('value', [])[:5]:  # Show first 5
                    print(f"  - {plan.get('title')} ({plan.get('id')})")
            else:
                print("No plans found in group")

        except Exception as ex:
            print(f"Error: {ex}")


def example_3_get_task_details(task_id: str):
    """Example 3: Get task and task details"""
    print("\n=== Example 3: Get Task Details ===")

    with DefaultAzureCredential() as credential:
        client = PlannerClient(CONNECTION_RUNTIME_URL, credential)

        try:
            # Get basic task info
            task = client.get_task(id=task_id)
            if task:
                print(f"Task: {task.get('title')}")
                print(f"  - Percent Complete: {task.get('percentComplete')}%")
                print(f"  - Created: {task.get('createdDateTime')}")

            # Get detailed task info
            details = client.get_task_details(id=task_id)
            if details:
                print(f"  - Description: {details.get('description', 'No description')}")

        except Exception as ex:
            print(f"Error: {ex}")


def example_4_create_bucket(group_id: str, plan_id: str):
    """Example 4: Create a new bucket in a plan"""
    print("\n=== Example 4: Create Bucket ===")

    with DefaultAzureCredential() as credential:
        client = PlannerClient(CONNECTION_RUNTIME_URL, credential)

        try:
            bucket_input = CreateBucketInput(
                name="New Bucket",
                group_id=group_id,
                plan_id=plan_id
            )

            bucket = client.create_bucket(input=bucket_input)

            if bucket:
                print(f"Created bucket: {bucket.get('name')} ({bucket.get('id')})")

        except Exception as ex:
            print(f"Error: {ex}")


def example_5_create_and_update_task(group_id: str, plan_id: str, bucket_id: str):
    """Example 5: Create and update a task"""
    print("\n=== Example 5: Create and Update Task ===")

    with DefaultAzureCredential() as credential:
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

            task = client.create_task(input=task_input)

            if task:
                task_id = task.get('id')
                print(f"Created task: {task.get('title')} ({task_id})")

                # Update the task
                update_input = UpdateTaskRequest(
                    title="Updated Sample Task",
                    percent_complete=50
                )

                updated = client.update_task(input=update_input, id=task_id)

                if updated:
                    print("Updated task to 50% complete")

                # Clean up - delete the task
                client.delete_task(id=task_id)
                print("Deleted task")

        except Exception as ex:
            print(f"Error: {ex}")


def example_6_get_plan_details(plan_id: str):
    """Example 6: Get plan details"""
    print("\n=== Example 6: Get Plan Details ===")

    with DefaultAzureCredential() as credential:
        client = PlannerClient(CONNECTION_RUNTIME_URL, credential)

        try:
            details = client.get_plan_details(id=plan_id)

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


def main():
    """Run all examples"""
    print("Planner sample usage for the Azure Connectors Python SDK")
    print("=" * 50)
    print()

    # Example 1: List my tasks (no parameters needed)
    example_1_list_my_tasks()

    # Examples 2-6 require IDs from your Planner
    # Replace these with actual values from your environment
    group_id = ""  # Microsoft 365 Group ID
    plan_id = ""  # Plan ID
    task_id = ""  # Task ID

    if group_id:
        example_2_list_group_plans(group_id)

    if task_id:
        example_3_get_task_details(task_id)

    if plan_id:
        example_6_get_plan_details(plan_id)

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
    main()


if __name__ == "__main__":
    main()
