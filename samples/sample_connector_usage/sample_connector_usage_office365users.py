# Copyright (c) Microsoft Corporation. All rights reserved.

"""
Office 365 Users Connector SDK Sample

This sample demonstrates how to use the Office 365 Users connector SDK.

Prerequisites:
1. Azure subscription with Office 365 Users connection
2. Office 365 Users connection in Connector Namespaces
3. Connection runtime URL from Azure Portal

Installation:
    pip install azure-connectors

Usage:
    Set environment variable:
    $env:OFFICE365USERS_CONNECTION_URL = (
        "https://[region].azure-apihub.net/apim/office365users/[connection-id]"
    )

    python sample_connector_usage_office365users.py
"""

import asyncio
import os
from azure.identity.aio import DefaultAzureCredential
from azure.connectors import ConnectorException
from azure.connectors.office365users import Office365usersClient

# Connection runtime URL format:
# https://[region].azure-apihub.net/apim/office365users/[connection-id]
CONNECTION_RUNTIME_URL = os.environ.get(
    "OFFICE365USERS_CONNECTION_URL",
    ""
)


async def example_1_get_my_profile():
    """Example 1: Get the current user's profile."""
    print("\n=== Example 1: Get My Profile ===")

    credential = DefaultAzureCredential()

    async with Office365usersClient(CONNECTION_RUNTIME_URL, credential) as client:
        try:
            profile = await client.my_profile_async()

            if profile:
                print("My Profile:")
                print(f"  Display Name: {profile.get('displayName', 'N/A')}")
                print(f"  Email: {profile.get('mail', 'N/A')}")
                print(f"  Job Title: {profile.get('jobTitle', 'N/A')}")
                print(f"  Department: {profile.get('department', 'N/A')}")
                print(f"  Office: {profile.get('officeLocation', 'N/A')}")
            else:
                print("No profile returned.")

        except ConnectorException as ex:
            print(f"Connector error: {ex}")
        except Exception as ex:
            print(f"Error: {ex}")


async def example_2_get_user_profile():
    """Example 2: Get a specific user's profile."""
    print("\n=== Example 2: Get User Profile ===")

    user_id = os.environ.get("TEST_USER_ID", "")
    if not user_id:
        print("Set TEST_USER_ID environment variable to a user's ID or UPN.")
        print("Example: $env:TEST_USER_ID = 'john.doe@contoso.com'")
        return

    credential = DefaultAzureCredential()

    async with Office365usersClient(CONNECTION_RUNTIME_URL, credential) as client:
        try:
            profile = await client.user_profile_async(id=user_id)

            if profile:
                print(f"User Profile for '{user_id}':")
                print(f"  Display Name: {profile.get('displayName', 'N/A')}")
                print(f"  Email: {profile.get('mail', 'N/A')}")
                print(f"  Job Title: {profile.get('jobTitle', 'N/A')}")
                print(f"  Department: {profile.get('department', 'N/A')}")
                print(f"  Office: {profile.get('officeLocation', 'N/A')}")
            else:
                print(f"User not found: {user_id}")

        except ConnectorException as ex:
            print(f"Connector error: {ex}")
        except Exception as ex:
            print(f"Error: {ex}")


async def example_3_get_manager():
    """Example 3: Get a user's manager."""
    print("\n=== Example 3: Get Manager ===")

    user_id = os.environ.get("TEST_USER_ID", "")
    if not user_id:
        print("Set TEST_USER_ID environment variable to a user's ID or UPN.")
        print("Example: $env:TEST_USER_ID = 'john.doe@contoso.com'")
        return

    credential = DefaultAzureCredential()

    async with Office365usersClient(CONNECTION_RUNTIME_URL, credential) as client:
        try:
            manager = await client.manager_async(id=user_id)

            if manager:
                print(f"Manager for '{user_id}':")
                print(f"  Display Name: {manager.get('displayName', 'N/A')}")
                print(f"  Email: {manager.get('mail', 'N/A')}")
                print(f"  Job Title: {manager.get('jobTitle', 'N/A')}")
            else:
                print(f"No manager found for: {user_id}")

        except ConnectorException as ex:
            print(f"Connector error: {ex}")
        except Exception as ex:
            print(f"Error: {ex}")


async def example_4_get_direct_reports():
    """Example 4: Get a user's direct reports."""
    print("\n=== Example 4: Get Direct Reports ===")

    user_id = os.environ.get("TEST_USER_ID", "")
    if not user_id:
        print("Set TEST_USER_ID environment variable to a user's ID or UPN.")
        print("Example: $env:TEST_USER_ID = 'john.doe@contoso.com'")
        return

    credential = DefaultAzureCredential()

    async with Office365usersClient(CONNECTION_RUNTIME_URL, credential) as client:
        try:
            reports = await client.direct_reports_async(id=user_id)

            if reports and "value" in reports:
                print(f"Direct reports for '{user_id}':")
                print(f"  Found {len(reports['value'])} reports")
                for report in reports["value"][:5]:  # Show first 5
                    display_name = report.get("displayName", "N/A")
                    job_title = report.get("jobTitle", "N/A")
                    print(f"    - {display_name} ({job_title})")
            else:
                print(f"No direct reports found for: {user_id}")

        except ConnectorException as ex:
            print(f"Connector error: {ex}")
        except Exception as ex:
            print(f"Error: {ex}")


async def example_5_search_users():
    """Example 5: Search for users."""
    print("\n=== Example 5: Search Users ===")

    search_term = os.environ.get("TEST_SEARCH_TERM", "")
    if not search_term:
        print("Set TEST_SEARCH_TERM environment variable to search for users.")
        print("Example: $env:TEST_SEARCH_TERM = 'John'")
        return

    credential = DefaultAzureCredential()

    async with Office365usersClient(CONNECTION_RUNTIME_URL, credential) as client:
        try:
            results = await client.search_user_async(
                search_term=search_term,
                top=10,
            )

            if results and "value" in results:
                print(f"Search results for '{search_term}':")
                print(f"  Found {len(results['value'])} users")
                for user in results["value"][:5]:  # Show first 5
                    display_name = user.get("DisplayName", "N/A")
                    mail = user.get("Mail", "N/A")
                    print(f"    - {display_name} ({mail})")
            else:
                print(f"No users found matching: {search_term}")

        except ConnectorException as ex:
            print(f"Connector error: {ex}")
        except Exception as ex:
            print(f"Error: {ex}")


async def main():
    """Run all examples."""
    print("Office 365 Users Connector SDK - Sample Usage")
    print("=" * 60)

    if not CONNECTION_RUNTIME_URL:
        print("\nWARNING: OFFICE365USERS_CONNECTION_URL environment variable not set.")
        print("Set it to your connection runtime URL to run actual API calls.")
        print("Format: https://[region].azure-apihub.net/apim/office365users/[connection-id]")
        return

    await example_1_get_my_profile()
    await example_2_get_user_profile()
    await example_3_get_manager()
    await example_4_get_direct_reports()
    await example_5_search_users()

    print("\n" + "=" * 60)
    print("Sample completed!")


if __name__ == "__main__":
    asyncio.run(main())
