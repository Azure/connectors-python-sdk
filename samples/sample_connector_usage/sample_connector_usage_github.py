"""
GitHub sample for the Azure Connectors Python SDK

This sample demonstrates how to use the GitHub client from the Azure Connectors Python SDK.

Prerequisites:
1. Azure subscription with GitHub connection
2. GitHub connection in Connector Namespaces
3. Connection runtime URL from Azure Portal

Installation:
    pip install azure-connectors

Usage:
    Set environment variable:
    $env:GITHUB_CONNECTION_URL = "https://[region].azure-apihub.net/apim/github/[connection-id]"

    python sample_connector_usage_github.py
"""
import os

from azure.identity import DefaultAzureCredential

from azure.connectors import ConnectorException
from azure.connectors.github import GithubClient, IssueBasicDetailsModel


# Connection runtime URL format:
# https://[region].azure-apihub.net/apim/github/[connection-id]
CONNECTION_RUNTIME_URL = os.environ.get("GITHUB_CONNECTION_URL", "")


def example_1_get_authenticated_user() -> None:
    """Example 1: Get authenticated GitHub user."""
    print("\n=== Example 1: Get Authenticated User ===")

    with DefaultAzureCredential() as credential:
        with GithubClient(CONNECTION_RUNTIME_URL, credential) as client:
            user = client.get_user()
            print(f"Authenticated as: {user.get('login') if user else 'unknown'}")


def example_2_list_issues(repository_owner: str, repository_name: str) -> None:
    """Example 2: List open issues in a repository."""
    print("\n=== Example 2: List Issues ===")

    with DefaultAzureCredential() as credential:
        with GithubClient(CONNECTION_RUNTIME_URL, credential) as client:
            issues = client.list_issues(
                repository_owner=repository_owner,
                repository_name=repository_name,
                state="open",
                per_page=5,
            )

            issue_list = issues if isinstance(issues, list) else []
            print(f"Found {len(issue_list)} issues")
            for issue in issue_list[:5]:
                print(f"  - #{issue.get('number')}: {issue.get('title')}")


def example_3_create_issue(repository_owner: str, repository_name: str) -> None:
    """Example 3: Create a new issue in a repository."""
    print("\n=== Example 3: Create Issue ===")

    with DefaultAzureCredential() as credential:
        with GithubClient(CONNECTION_RUNTIME_URL, credential) as client:
            request = IssueBasicDetailsModel(
                title="SDK sample issue",
                body="Created from github Python SDK sample.",
            )
            created = client.create_issue(
                input=request,
                repository_owner=repository_owner,
                repository_name=repository_name,
            )

            print(f"Created issue: #{created.get('number') if created else 'n/a'}")


def main() -> None:
    """Run GitHub connector examples."""
    if not CONNECTION_RUNTIME_URL:
        print("Error: GITHUB_CONNECTION_URL environment variable not set.")
        print("Set it to your connection runtime URL from Azure Portal.")
        return

    # Update to a repository you can access with your GitHub connector auth.
    repository_owner = "octocat"
    repository_name = "hello-world"

    print("GitHub sample usage for the Azure Connectors Python SDK")
    print("=" * 50)

    try:
        example_1_get_authenticated_user()
        example_2_list_issues(repository_owner, repository_name)
        # Uncomment after confirming write permissions.
        # await example_3_create_issue(repository_owner, repository_name)

    except ConnectorException as ex:
        print(f"Connector error: {ex}")
    except Exception as ex:
        print(f"Unexpected error: {ex}")


if __name__ == "__main__":
    main()
