"""
Shifts Connector SDK Sample

This sample demonstrates how to use the Shifts connector SDK.

Prerequisites:
1. Azure subscription with Shifts connection
2. Shifts connection in Connector Namespaces
3. Connection runtime URL from Azure Portal

Installation:
    pip install azure-connectors

Usage:
    Set environment variable:
    $env:SHIFTS_CONNECTION_URL = "https://[region].azure-apihub.net/apim/shifts/[connection-id]"

    python sample_connector_usage_shifts.py
"""
import os

from azure.identity import DefaultAzureCredential

from azure.connectors import ConnectorException
from azure.connectors.shifts import ShiftsClient


# Connection runtime URL format:
# https://[region].azure-apihub.net/apim/shifts/[connection-id]
CONNECTION_RUNTIME_URL = os.environ.get("SHIFTS_CONNECTION_URL", "")


def example_1_list_teams() -> list[dict]:
    """Example 1: List joined teams."""
    print("\n=== Example 1: List Teams ===")

    with DefaultAzureCredential() as credential:
        with ShiftsClient(CONNECTION_RUNTIME_URL, credential) as client:
            teams_response = client.get_all_teams()
            teams = teams_response.get("value", []) if teams_response else []

            print(f"Found {len(teams)} teams")
            for team in teams[:10]:
                print(f"  - {team.get('displayName')} ({team.get('id')})")

            return teams


def example_2_get_schedule(team_id: str) -> None:
    """Example 2: Get a team's schedule."""
    print("\n=== Example 2: Get Schedule ===")

    with DefaultAzureCredential() as credential:
        with ShiftsClient(CONNECTION_RUNTIME_URL, credential) as client:
            schedule = client.get_schedule(team_id=team_id)

            if not schedule:
                print("No schedule returned")
                return

            print(f"Schedule ID: {schedule.get('id')}")
            print(f"Time Zone: {schedule.get('timeZone')}")
            print(f"Provision Status: {schedule.get('provisionStatus')}")


def example_3_list_shifts(team_id: str) -> None:
    """Example 3: List shifts for a team."""
    print("\n=== Example 3: List Shifts ===")

    with DefaultAzureCredential() as credential:
        with ShiftsClient(CONNECTION_RUNTIME_URL, credential) as client:
            shifts_response = [item for item in client.list_shifts(team_id=team_id, top=10)]
            shifts = shifts_response if shifts_response else []

            print(f"Found {len(shifts)} shifts")
            for shift in shifts[:10]:
                print(f"  - {shift.get('id')} assigned to {shift.get('userId')}")


def main() -> None:
    """Run all examples."""
    if not CONNECTION_RUNTIME_URL:
        print("Error: SHIFTS_CONNECTION_URL environment variable not set.")
        print("Set it to your connection runtime URL from Azure Portal.")
        return

    print("Shifts Connector SDK - Sample Usage")
    print("=" * 50)

    try:
        teams = example_1_list_teams()
        if teams:
            first_team_id = teams[0].get("id")
            if first_team_id:
                example_2_get_schedule(first_team_id)
                example_3_list_shifts(first_team_id)
            else:
                print("No team id found in first record; skipping team-specific examples.")
        else:
            print("No teams found; skipping team-specific examples.")

    except ConnectorException as ex:
        print(f"Connector error: {ex}")
    except Exception as ex:
        print(f"Unexpected error: {ex}")


if __name__ == "__main__":
    main()
