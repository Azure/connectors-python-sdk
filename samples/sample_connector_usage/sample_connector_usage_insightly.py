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
import os

from azure.identity import DefaultAzureCredential

from azure.connectors import ConnectorException
from azure.connectors.insightly import InsightlyClient, TaskRequest


# Connection runtime URL format:
# https://[region].azure-apihub.net/apim/insightly/[connection-id]
CONNECTION_RUNTIME_URL = os.environ.get("INSIGHTLY_CONNECTION_URL", "")


def example_1_list_tasks() -> None:
    """Example 1: List tasks."""
    print("\n=== Example 1: List Tasks ===")

    with DefaultAzureCredential() as credential:
        with InsightlyClient(CONNECTION_RUNTIME_URL, credential) as client:
            tasks = list(client.list_tasks())

            print(f"Found {len(tasks)} tasks")
            for task in tasks[:5]:
                print(f"  - {task.get('TASK_ID')}: {task.get('TITLE')}")


def example_2_list_contacts() -> None:
    """Example 2: List contacts."""
    print("\n=== Example 2: List Contacts ===")

    with DefaultAzureCredential() as credential:
        with InsightlyClient(CONNECTION_RUNTIME_URL, credential) as client:
            contacts = list(client.list_contacts())

            print(f"Found {len(contacts)} contacts")
            for contact in contacts[:5]:
                first = contact.get("FIRST_NAME", "")
                last = contact.get("LAST_NAME", "")
                print(f"  - {contact.get('CONTACT_ID')}: {first} {last}".rstrip())


def example_3_add_task() -> None:
    """Example 3: Add a task."""
    print("\n=== Example 3: Add Task ===")

    with DefaultAzureCredential() as credential:
        with InsightlyClient(CONNECTION_RUNTIME_URL, credential) as client:
            request = TaskRequest(
                t_i_t_l_e="SDK sample task",
                d_e_t_a_i_l_s="Created from insightly SDK sample.",
                s_t_a_t_u_s="NOT STARTED",
                c_o_m_p_l_e_t_e_d=False,
                p_u_b_l_i_c_l_y_v_i_s_i_b_l_e=False,
            )

            created = client.add_task(input=request)
            print(f"Created task: {created.get('TASK_ID') if created else 'n/a'}")


def main() -> None:
    """Run Insightly connector examples."""
    if not CONNECTION_RUNTIME_URL:
        print("Error: INSIGHTLY_CONNECTION_URL environment variable not set.")
        print("Set it to your connection runtime URL from Azure Portal.")
        return

    print("Insightly sample usage for the Azure Connectors Python SDK")
    print("=" * 50)

    try:
        example_1_list_tasks()
        example_2_list_contacts()
        # Uncomment to create a task in your Insightly instance.
        # await example_3_add_task()

    except ConnectorException as ex:
        print(f"Connector error: {ex}")
    except Exception as ex:
        print(f"Unexpected error: {ex}")


if __name__ == "__main__":
    main()
