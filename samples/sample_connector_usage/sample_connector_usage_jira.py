"""
Jira sample for the Azure Connectors Python SDK

This sample demonstrates how to use the Jira client from the Azure Connectors Python SDK.

Prerequisites:
1. Azure subscription with Jira connection
2. Jira connection in Connector Namespaces
3. Connection runtime URL from Azure Portal

Installation:
    pip install azure-connectors

Usage:
    Set environment variable:
    $env:JIRA_CONNECTION_URL = "https://[region].azure-apihub.net/apim/jira/[connection-id]"

    python sample_connector_usage_jira.py
"""
import os

from azure.identity import DefaultAzureCredential

from azure.connectors import ConnectorException
from azure.connectors.jira import JiraClient, CreateIssueInput


# Connection runtime URL format:
# https://[region].azure-apihub.net/apim/jira/[connection-id]
CONNECTION_RUNTIME_URL = os.environ.get("JIRA_CONNECTION_URL", "")


def example_1_list_resources() -> list[dict]:
    """Example 1: List accessible Jira cloud resources."""
    print("\n=== Example 1: List Resources ===")

    with DefaultAzureCredential() as credential:
        with JiraClient(CONNECTION_RUNTIME_URL, credential) as client:
            resources = list(client.list_resources())

            print(f"Found {len(resources)} resources")
            for resource in resources[:5]:
                print(f"  - {resource.get('name')} ({resource.get('id')})")

            return resources


def example_2_list_issues(cloud_id: str) -> None:
    """Example 2: List issues in a Jira site."""
    print("\n=== Example 2: List Issues ===")

    with DefaultAzureCredential() as credential:
        with JiraClient(CONNECTION_RUNTIME_URL, credential) as client:
            del cloud_id

            issues = list(client.list_issues())
            print(f"Found {len(issues)} issues")
            for issue in issues[:5]:
                print(f"  - {issue.get('key')}: {issue.get('fields', {}).get('summary')}")


def example_3_create_issue(cloud_id: str) -> None:
    """Example 3: Create an issue (requires valid project + issue type)."""
    print("\n=== Example 3: Create Issue ===")

    with DefaultAzureCredential() as credential:
        with JiraClient(CONNECTION_RUNTIME_URL, credential) as client:
            del cloud_id

            request = CreateIssueInput(
                additional_properties={
                    "fields": {
                        "project": {"key": "PROJ"},
                        "summary": "SDK sample issue",
                        "issuetype": {"name": "Task"},
                        "description": {
                            "type": "doc",
                            "version": 1,
                            "content": [{
                                "type": "paragraph",
                                "content": [{
                                    "type": "text",
                                    "text": "Created from jira SDK sample.",
                                }],
                            }],
                        },
                    }
                }
            )

            created = client.create_issue(
                input=request,
                project_key="PROJ",
                issue_type_ids="10001",
            )
            print(f"Created issue: {created.get('key') if created else 'n/a'}")


def main() -> None:
    """Run Jira connector examples."""
    if not CONNECTION_RUNTIME_URL:
        print("Error: JIRA_CONNECTION_URL environment variable not set.")
        print("Set it to your connection runtime URL from Azure Portal.")
        return

    print("Jira sample usage for the Azure Connectors Python SDK")
    print("=" * 50)

    try:
        resources = example_1_list_resources()

        if resources:
            cloud_id = resources[0].get("id")
            if cloud_id:
                example_2_list_issues(cloud_id)
                # Uncomment after setting valid project/issuetype in example_3_create_issue.
                # await example_3_create_issue(cloud_id)
            else:
                print("No cloud id found in first resource; skipping issue examples.")
        else:
            print("No resources returned; skipping issue examples.")

    except ConnectorException as ex:
        print(f"Connector error: {ex}")
    except Exception as ex:
        print(f"Unexpected error: {ex}")


if __name__ == "__main__":
    main()
