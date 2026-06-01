# Copyright (c) Microsoft Corporation. All rights reserved.

"""
Azure AD (Microsoft Entra ID) Connector SDK Sample

This sample demonstrates how to use the Azure AD connector SDK.

Prerequisites:
1. Azure subscription with Azure AD connection
2. Azure AD connection in Connector Namespaces (with OAuth consent)
3. Connection runtime URL from Azure Portal

Installation:
    pip install azure-connectors

Usage:
    Set environment variable:
    $env:AZUREAD_CONNECTION_URL = "https://[region].azure-apihub.net/apim/azuread/[connection-id]"

    python sample_connector_usage_azuread.py
"""

import asyncio
import os
from azure.identity.aio import DefaultAzureCredential
from azure.connectors import ConnectorException
from azure.connectors.azuread import (
    AzureadClient,
    CreateOffice365GroupInput,
    CreateSecurityGroupInput,
    CreateGroupInput,
    CreateUserRequest,
)

# Connection runtime URL format:
# https://[region].azure-apihub.net/apim/azuread/[connection-id]
CONNECTION_RUNTIME_URL = os.environ.get(
    "AZUREAD_CONNECTION_URL",
    ""
)


async def example_1_create_office365_group():
    """Example 1: Create an Office 365 group."""
    print("\n=== Example 1: Create Office 365 Group ===")

    group_name = os.environ.get("TEST_O365_GROUP_NAME", "")
    if not group_name:
        print("Set TEST_O365_GROUP_NAME environment variable to create a group.")
        print("Example: $env:TEST_O365_GROUP_NAME = 'SDK Test Group'")
        return

    credential = DefaultAzureCredential()

    async with AzureadClient(CONNECTION_RUNTIME_URL, credential) as client:
        try:
            input_data = CreateOffice365GroupInput(
                display_name=group_name,
                description="Created via Azure Connectors SDK for Python",
                mail_nickname=group_name.replace(" ", "-").lower(),
                group_types=["Unified"],
                security_enabled=False,
                mail_enabled=True,
            )

            result = await client.create_office365_group_async(input=input_data)

            if result:
                print("Office 365 group created:")
                print(f"  ID: {result.get('id', 'N/A')}")
                print(f"  Display Name: {result.get('displayName', 'N/A')}")
                print(f"  Mail: {result.get('mail', 'N/A')}")
                print(f"  Created: {result.get('createdDateTime', 'N/A')}")
            else:
                print("Group created (no response returned).")

        except ConnectorException as ex:
            print(f"Connector error: {ex}")
        except Exception as ex:
            print(f"Error: {ex}")


async def example_2_create_security_group():
    """Example 2: Create a security group."""
    print("\n=== Example 2: Create Security Group ===")

    group_name = os.environ.get("TEST_SECURITY_GROUP_NAME", "")
    if not group_name:
        print("Set TEST_SECURITY_GROUP_NAME environment variable to create a group.")
        print("Example: $env:TEST_SECURITY_GROUP_NAME = 'SDK Security Group'")
        return

    credential = DefaultAzureCredential()

    async with AzureadClient(CONNECTION_RUNTIME_URL, credential) as client:
        try:
            input_data = CreateSecurityGroupInput(
                display_name=group_name,
                description="Security group created via Azure Connectors SDK",
                mail_nickname=group_name.replace(" ", "-").lower(),
                security_enabled=True,
                mail_enabled=False,
            )

            result = await client.create_security_group_async(input=input_data)

            if result:
                print("Security group created:")
                print(f"  ID: {result.get('id', 'N/A')}")
                print(f"  Display Name: {result.get('displayName', 'N/A')}")
                print(f"  Security Enabled: {result.get('securityEnabled', 'N/A')}")
            else:
                print("Security group created (no response returned).")

        except ConnectorException as ex:
            print(f"Connector error: {ex}")
        except Exception as ex:
            print(f"Error: {ex}")


async def example_3_create_group():
    """Example 3: Create a generic group."""
    print("\n=== Example 3: Create Group ===")

    group_name = os.environ.get("TEST_GROUP_NAME", "")
    if not group_name:
        print("Set TEST_GROUP_NAME environment variable to create a group.")
        print("Example: $env:TEST_GROUP_NAME = 'SDK Generic Group'")
        return

    # Group type: 'Unified' for O365, empty list for security group
    group_type = os.environ.get("TEST_GROUP_TYPE", "Unified")
    group_types = [group_type] if group_type else []

    credential = DefaultAzureCredential()

    async with AzureadClient(CONNECTION_RUNTIME_URL, credential) as client:
        try:
            input_data = CreateGroupInput(
                display_name=group_name,
                description="Group created via Azure Connectors SDK",
                mail_nickname=group_name.replace(" ", "-").lower(),
                group_types=group_types,
                security_enabled=not bool(group_types),
                mail_enabled=bool(group_types),
            )

            result = await client.create_group_async(input=input_data)

            if result:
                print("Group created:")
                print(f"  ID: {result.get('id', 'N/A')}")
                print(f"  Display Name: {result.get('displayName', 'N/A')}")
                print(f"  Group Types: {result.get('groupTypes', [])}")
                print(f"  Mail Enabled: {result.get('mailEnabled', 'N/A')}")
                print(f"  Security Enabled: {result.get('securityEnabled', 'N/A')}")
            else:
                print("Group created (no response returned).")

        except ConnectorException as ex:
            print(f"Connector error: {ex}")
        except Exception as ex:
            print(f"Error: {ex}")


async def example_4_create_user():
    """Example 4: Create a new user."""
    print("\n=== Example 4: Create User ===")

    user_principal_name = os.environ.get("TEST_USER_UPN", "")
    display_name = os.environ.get("TEST_USER_DISPLAY_NAME", "")
    temp_password = os.environ.get("TEST_USER_PASSWORD", "")

    if not user_principal_name or not display_name:
        print("Set environment variables to create a user:")
        print("  $env:TEST_USER_UPN = 'newuser@yourdomain.onmicrosoft.com'")
        print("  $env:TEST_USER_DISPLAY_NAME = 'New User'")
        print("  $env:TEST_USER_PASSWORD = 'TempPassword123!'")
        return

    credential = DefaultAzureCredential()

    async with AzureadClient(CONNECTION_RUNTIME_URL, credential) as client:
        try:
            input_data = CreateUserRequest(
                account_enabled=True,
                display_name=display_name,
                mail_nickname=user_principal_name.split("@")[0],
                user_principal_name=user_principal_name,
                password_profile={
                    "password": temp_password or "TempPassword123!",
                    "forceChangePasswordNextSignIn": True,
                },
            )

            result = await client.create_user_async(input=input_data)

            if result:
                print("User created:")
                print(f"  ID: {result.get('id', 'N/A')}")
                print(f"  Display Name: {result.get('displayName', 'N/A')}")
                print(f"  UPN: {result.get('userPrincipalName', 'N/A')}")
                print(f"  Mail: {result.get('mail', 'N/A')}")
            else:
                print("User created (no response returned).")

        except ConnectorException as ex:
            print(f"Connector error: {ex}")
        except Exception as ex:
            print(f"Error: {ex}")


async def example_5_remove_member_from_group():
    """Example 5: Remove a member from a group."""
    print("\n=== Example 5: Remove Member From Group ===")

    group_id = os.environ.get("TEST_GROUP_ID", "")
    member_id = os.environ.get("TEST_MEMBER_ID", "")

    if not group_id or not member_id:
        print("Set environment variables to remove a member:")
        print("  $env:TEST_GROUP_ID = '<group-object-id>'")
        print("  $env:TEST_MEMBER_ID = '<user-object-id>'")
        return

    credential = DefaultAzureCredential()

    async with AzureadClient(CONNECTION_RUNTIME_URL, credential) as client:
        try:
            await client.remove_member_from_group_async(
                group_id=group_id,
                member_id=member_id,
            )

            print("Member removed from group:")
            print(f"  Group ID: {group_id}")
            print(f"  Member ID: {member_id}")

        except ConnectorException as ex:
            print(f"Connector error: {ex}")
        except Exception as ex:
            print(f"Error: {ex}")


async def main():
    """Run all examples."""
    print("Azure AD (Microsoft Entra ID) Connector SDK - Sample Usage")
    print("=" * 60)

    if not CONNECTION_RUNTIME_URL:
        print("\nWARNING: AZUREAD_CONNECTION_URL environment variable not set.")
        print("Set it to your connection runtime URL to run actual API calls.")
        print("Format: https://[region].azure-apihub.net/apim/azuread/[connection-id]")
        return

    await example_1_create_office365_group()
    await example_2_create_security_group()
    await example_3_create_group()
    await example_4_create_user()
    await example_5_remove_member_from_group()

    print("\n" + "=" * 60)
    print("Sample completed!")


if __name__ == "__main__":
    asyncio.run(main())
