"""
Jira Connector SDK Sample

This sample demonstrates how to use the Jira connector SDK.

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

import asyncio
import os

from azure.identity.aio import DefaultAzureCredential

from azure.connectors import ConnectorException
from azure.connectors.jira import JiraClient, CreateIssueInput


# Connection runtime URL format:
# https://[region].azure-apihub.net/apim/jira/[connection-id]
CONNECTION_RUNTIME_URL = os.environ.get("JIRA_CONNECTION_URL", "")


async def example_1_list_resources() -> list[dict]:
    """Example 1: List accessible Jira cloud resources."""
    print("\n=== Example 1: List Resources ===")

    credential = DefaultAzureCredential()
    async with JiraClient(CONNECTION_RUNTIME_URL, credential) as client:
        resources_response = await client.list_resources_async()
        resources = (
            resources_response
            if isinstance(resources_response, list)
            else resources_response.get("value", []) if resources_response else []
        )

        print(f"Found {len(resources)} resources")
        for resource in resources[:5]:
            print(f"  - {resource.get('name')} ({resource.get('id')})")

        return resources


async def example_2_list_issues(cloud_id: str) -> None:
    """Example 2: List issues in a Jira site."""
    print("\n=== Example 2: List Issues ===")

    credential = DefaultAzureCredential()
    async with JiraClient(CONNECTION_RUNTIME_URL, credential) as client:
        del cloud_id

        issues_response = await client.list_issues_async()

        issues = issues_response.get("issues", []) if issues_response else []
        print(f"Found {len(issues)} issues")
        for issue in issues[:5]:
            print(f"  - {issue.get('key')}: {issue.get('fields', {}).get('summary')}")


async def example_3_create_issue(cloud_id: str) -> None:
    """Example 3: Create an issue (requires valid project + issue type)."""
    print("\n=== Example 3: Create Issue ===")

    credential = DefaultAzureCredential()
    async with JiraClient(CONNECTION_RUNTIME_URL, credential) as client:
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

        created = await client.create_issue_async(
            input=request,
            project_key="PROJ",
            issue_type_ids="10001",
        )
        print(f"Created issue: {created.get('key') if created else 'n/a'}")


async def main() -> None:
    """Run Jira connector examples."""
    if not CONNECTION_RUNTIME_URL:
        print("Error: JIRA_CONNECTION_URL environment variable not set.")
        print("Set it to your connection runtime URL from Azure Portal.")
        return

    print("Jira Connector SDK - Sample Usage")
    print("=" * 50)

    try:
        resources = await example_1_list_resources()

        if resources:
            cloud_id = resources[0].get("id")
            if cloud_id:
                await example_2_list_issues(cloud_id)
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
    asyncio.run(main())
