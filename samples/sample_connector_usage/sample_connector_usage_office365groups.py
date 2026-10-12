# Copyright (c) Microsoft Corporation. All rights reserved.

"""
Office 365 Groups Connector SDK Sample

This sample demonstrates how to use the Office 365 Groups connector SDK
for group management and calendar operations.

Prerequisites:
1. Azure subscription with Office 365 Groups connection
2. Office 365 Groups connection in Connector Namespaces
3. Connection runtime URL from Azure Portal

Installation:
    pip install azure-connectors

Usage:
    Set environment variable:
    $env:OFFICE365GROUPS_CONNECTION_URL = "<connection-url>"

    python sample_connector_usage_office365groups.py
"""
import os
from azure.identity import DefaultAzureCredential
from azure.connectors import ConnectorException
from azure.connectors.office365groups import (
    Office365groupsClient,
    UpdateCalendarEventHTMLRequest,
)

# Connection runtime URL format:
# https://[region].azure-apihub.net/apim/office365groups/[connection-id]
CONNECTION_RUNTIME_URL = os.environ.get(
    "OFFICE365GROUPS_CONNECTION_URL",
    ""
)


def example_1_list_groups():
    """Example 1: List all groups in the organization."""
    print("\n=== Example 1: List Groups ===")

    with DefaultAzureCredential() as credential:

        with Office365groupsClient(CONNECTION_RUNTIME_URL, credential) as client:
            try:
                groups = [item for item in client.list_groups(top=10)]

                if groups:
                    print(f"Found {len(groups)} groups:")
                    for group in groups[:5]:
                        print(f"  - {group.get('displayName', 'N/A')} ({group.get('id', 'N/A')})")
                else:
                    print("No groups found.")

            except ConnectorException as ex:
                print(f"Connector error: {ex}")
            except Exception as ex:
                print(f"Error: {ex}")


def example_2_list_group_members():
    """Example 2: List members of a specific group."""
    print("\n=== Example 2: List Group Members ===")

    # Replace with your actual group ID
    GROUP_ID = "your-group-id-here"

    with DefaultAzureCredential() as credential:

        with Office365groupsClient(CONNECTION_RUNTIME_URL, credential) as client:
            try:
                members = [
                    item for item in client.list_group_members(
                        group_id=GROUP_ID
                    )
                ]

                if members:
                    print(f"Found {len(members)} members:")
                    for member in members[:5]:
                        print(f"  - {member.get('displayName', 'N/A')}")
                else:
                    print("No members found.")

            except ConnectorException as ex:
                print(f"Connector error: {ex}")
            except Exception as ex:
                print(f"Error: {ex}")


def example_3_list_owned_groups():
    """Example 3: List groups that I own and belong to."""
    print("\n=== Example 3: List My Groups ===")

    with DefaultAzureCredential() as credential:

        with Office365groupsClient(CONNECTION_RUNTIME_URL, credential) as client:
            try:
                result = client.list_owned_groups()

                if result and "value" in result:
                    groups = result["value"]
                    print(f"You own or belong to {len(groups)} groups:")
                    for group in groups[:5]:
                        print(f"  - {group.get('displayName', 'N/A')}")
                else:
                    print("No groups found.")

            except ConnectorException as ex:
                print(f"Connector error: {ex}")
            except Exception as ex:
                print(f"Error: {ex}")


def example_4_create_group_event():
    """Example 4: Create a calendar event in a group."""
    print("\n=== Example 4: Create Group Event ===")

    # Replace with your actual group ID
    GROUP_ID = "your-group-id-here"

    with DefaultAzureCredential() as credential:

        with Office365groupsClient(CONNECTION_RUNTIME_URL, credential) as client:
            try:
                event_input = UpdateCalendarEventHTMLRequest(
                    subject="Team Standup",
                    is_all_day=False,
                    is_reminder_on=True,
                    reminder_minutes_before_start=15,
                    importance="Normal",
                    start={
                        "dateTime": "2026-06-15T09:00:00",
                        "timeZone": "Pacific Standard Time"
                    },
                    end={
                        "dateTime": "2026-06-15T09:30:00",
                        "timeZone": "Pacific Standard Time"
                    },
                    body={
                        "contentType": "HTML",
                        "content": "<p>Daily standup meeting</p>"
                    }
                )

                result = client.create_calendar_event(
                    input=event_input,
                    group_id=GROUP_ID
                )

                if result:
                    print("Event created successfully!")
                    print(f"Event ID: {result.get('id')}")
                    print(f"Subject: {result.get('subject')}")
                else:
                    print("Event creation completed (no response body)")

            except ConnectorException as ex:
                print(f"Connector error: {ex}")
            except Exception as ex:
                print(f"Error: {ex}")


def example_5_add_member_to_group():
    """Example 5: Add a member to a group."""
    print("\n=== Example 5: Add Member to Group ===")

    # Replace with your actual values
    GROUP_ID = "your-group-id-here"
    USER_UPN = "user@contoso.com"

    with DefaultAzureCredential() as credential:

        with Office365groupsClient(CONNECTION_RUNTIME_URL, credential) as client:
            try:
                client.add_member_to_group(
                    group_id=GROUP_ID,
                    user_upn=USER_UPN
                )

                print(f"Member {USER_UPN} added to group successfully!")

            except ConnectorException as ex:
                print(f"Connector error: {ex}")
            except Exception as ex:
                print(f"Error: {ex}")


def example_6_list_deleted_groups():
    """Example 6: List deleted groups that can be restored."""
    print("\n=== Example 6: List Deleted Groups ===")

    with DefaultAzureCredential() as credential:

        with Office365groupsClient(CONNECTION_RUNTIME_URL, credential) as client:
            try:
                groups = [
                    item for item in client.list_deleted_groups()
                ]

                if groups:
                    print(f"Found {len(groups)} deleted groups:")
                    for group in groups[:5]:
                        print(f"  - {group.get('displayName', 'N/A')} ({group.get('id', 'N/A')})")
                else:
                    print("No deleted groups found.")

            except ConnectorException as ex:
                print(f"Connector error: {ex}")
            except Exception as ex:
                print(f"Error: {ex}")


def main():
    """Run all examples."""
    if not CONNECTION_RUNTIME_URL:
        print("Error: OFFICE365GROUPS_CONNECTION_URL environment variable not set.")
        print("Set it to your connection runtime URL from Azure Portal.")
        return

    print(f"Using connection URL: {CONNECTION_RUNTIME_URL[:50]}...")

    example_1_list_groups()
    example_3_list_owned_groups()
    example_6_list_deleted_groups()

    # The following examples require valid IDs:
    # await example_2_list_group_members()
    # await example_4_create_group_event()
    # await example_5_add_member_to_group()

    print("\n=== All examples completed ===")


if __name__ == "__main__":
    main()
