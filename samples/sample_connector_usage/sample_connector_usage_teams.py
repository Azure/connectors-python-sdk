"""
Microsoft Teams sample for the Azure Connectors Python SDK

This sample demonstrates how to use the Teams client from the Azure Connectors Python SDK.

Prerequisites:
1. Azure subscription with Teams connection
2. Teams connection in Connector Namespaces
3. Connection runtime URL from Azure Portal

Installation:
    pip install azure-connectors

Usage:
    python sample_teams_usage.py
"""
from azure.identity import DefaultAzureCredential
from azure.connectors.teams import TeamsClient

# Connection runtime URL format:
# https://[region].azure-apihub.net/apim/teams/[connection-id]
CONNECTION_RUNTIME_URL = ""


def example_1_list_joined_teams():
    """Example 1: List all Teams you're a member of"""
    print("\n=== Example 1: List Joined Teams ===")

    with DefaultAzureCredential() as credential:
        client = TeamsClient(CONNECTION_RUNTIME_URL, credential)

        try:
            teams = client.get_all_teams()

            print(f"Found {len(teams.get('value', []))} teams")
            for team in teams.get('value', [])[:3]:  # Show first 3
                print(f"  - {team.get('displayName')} ({team.get('id')})")

        except Exception as ex:
            print(f"Error: {ex}")


def example_2_list_associated_teams():
    """Example 2: List associated teams (direct membership + shared channels)"""
    print("\n=== Example 2: List Associated Teams ===")

    with DefaultAzureCredential() as credential:
        client = TeamsClient(CONNECTION_RUNTIME_URL, credential)

        try:
            teams = client.get_all_associated_teams()

            print(f"Found {len(teams.get('value', []))} associated teams")
            for team in teams.get('value', [])[:3]:  # Show first 3
                print(f"  - {team.get('displayName')}")

        except Exception as ex:
            print(f"Error: {ex}")


def main():
    """Run all examples"""
    print("Teams sample usage for the Azure Connectors Python SDK")
    print("=" * 50)
    print()

    example_1_list_joined_teams()
    example_2_list_associated_teams()

    print("\n" + "=" * 50)
    print("Sample completed!")


if __name__ == "__main__":
    main()
