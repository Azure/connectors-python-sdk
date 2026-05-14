# Copyright (c) Microsoft Corporation. All rights reserved.

"""
MS Graph Groups & Users Connector SDK Sample

This sample demonstrates how to use the MS Graph Groups & Users connector SDK.

Prerequisites:
1. Azure subscription with MS Graph Groups & Users connection
2. MS Graph connection in Azure Logic Apps
3. Connection runtime URL from Azure Portal

Installation:
    pip install azure-connectors

Usage:
    Set environment variable:
    $env:MSGRAPH_CONNECTION_URL = "https://[region].azure-apihub.net/apim/msgraphgroupsanduser/[connection-id]"
    
    python sample_connector_usage_msgraphgroupsanduser.py
"""

import asyncio
import os
from azure.identity.aio import DefaultAzureCredential
from azure.connectors import ConnectorException
from azure.connectors.msgraphgroupsanduser import MsgraphgroupsanduserClient

# Connection runtime URL format:
# https://[region].azure-apihub.net/apim/msgraphgroupsanduser/[connection-id]
CONNECTION_RUNTIME_URL = os.environ.get(
    "MSGRAPH_CONNECTION_URL",
    ""
)


async def example_1_list_users():
    """Example 1: List users in the tenant."""
    print("\n=== Example 1: List Users ===")
    
    credential = DefaultAzureCredential()
    
    async with MsgraphgroupsanduserClient(CONNECTION_RUNTIME_URL, credential) as client:
        try:
            users = await client.list_users_async()
            
            if users and "value" in users:
                print(f"Found {len(users['value'])} users:")
                for user in users["value"][:5]:  # Show first 5
                    display_name = user.get("displayName", "Unknown")
                    user_principal = user.get("userPrincipalName", "N/A")
                    print(f"  - {display_name} ({user_principal})")
            else:
                print("No users found or unexpected response format.")
                
        except ConnectorException as ex:
            print(f"Connector error: {ex}")
        except Exception as ex:
            print(f"Error: {ex}")


async def example_2_list_groups():
    """Example 2: Search for groups by display name."""
    print("\n=== Example 2: List Groups (Search) ===")
    
    search_term = os.environ.get("TEST_GROUP_SEARCH", None)
    
    credential = DefaultAzureCredential()
    
    async with MsgraphgroupsanduserClient(CONNECTION_RUNTIME_URL, credential) as client:
        try:
            groups = await client.list_groups_by_display_name_search_async(
                count="true",
                search=search_term,
            )
            
            search_display = search_term or "(all)"
            if groups and "value" in groups:
                print(f"Search: {search_display}")
                print(f"Found {len(groups['value'])} groups:")
                for group in groups["value"][:5]:  # Show first 5
                    display_name = group.get("displayName", "Unknown")
                    group_id = group.get("id", "N/A")
                    mail = group.get("mail", "No email")
                    print(f"  - {display_name}")
                    print(f"    ID: {group_id}")
                    print(f"    Mail: {mail}")
            else:
                print(f"No groups found for search: {search_display}")
                
        except ConnectorException as ex:
            print(f"Connector error: {ex}")
        except Exception as ex:
            print(f"Error: {ex}")


async def example_3_get_group_properties():
    """Example 3: Get properties of a specific group."""
    print("\n=== Example 3: Get Group Properties ===")
    
    group_id = os.environ.get("TEST_GROUP_ID", "")
    if not group_id:
        print("Set TEST_GROUP_ID environment variable to test this example.")
        print("You can get a group ID from Example 2 output.")
        return
    
    credential = DefaultAzureCredential()
    
    async with MsgraphgroupsanduserClient(CONNECTION_RUNTIME_URL, credential) as client:
        try:
            group = await client.get_group_properties_async(group_id=group_id)
            
            if group:
                print(f"Group properties for '{group.get('displayName', 'Unknown')}':")
                print(f"  ID: {group.get('id', 'N/A')}")
                print(f"  Description: {group.get('description', 'N/A')}")
                print(f"  Mail: {group.get('mail', 'N/A')}")
                print(f"  Mail Enabled: {group.get('mailEnabled', 'N/A')}")
                print(f"  Security Enabled: {group.get('securityEnabled', 'N/A')}")
                print(f"  Visibility: {group.get('visibility', 'N/A')}")
            else:
                print(f"Group not found: {group_id}")
                
        except ConnectorException as ex:
            print(f"Connector error: {ex}")
        except Exception as ex:
            print(f"Error: {ex}")


async def example_4_list_group_members():
    """Example 4: List direct members of a group."""
    print("\n=== Example 4: List Group Members ===")
    
    group_id = os.environ.get("TEST_GROUP_ID", "")
    if not group_id:
        print("Set TEST_GROUP_ID environment variable to test this example.")
        print("You can get a group ID from Example 2 output.")
        return
    
    credential = DefaultAzureCredential()
    
    async with MsgraphgroupsanduserClient(CONNECTION_RUNTIME_URL, credential) as client:
        try:
            members = await client.list_direct_group_members_async(
                group_id=group_id,
                count="true",
            )
            
            if members and "value" in members:
                print(f"Found {len(members['value'])} members:")
                for member in members["value"][:5]:  # Show first 5
                    display_name = member.get("displayName", "Unknown")
                    member_type = member.get("@odata.type", "Unknown type")
                    print(f"  - {display_name} ({member_type})")
            else:
                print("No members found or unexpected response format.")
                
        except ConnectorException as ex:
            print(f"Connector error: {ex}")
        except Exception as ex:
            print(f"Error: {ex}")


async def example_5_list_subscribed_skus():
    """Example 5: List organization's subscribed license SKUs."""
    print("\n=== Example 5: List Subscribed SKUs ===")
    
    credential = DefaultAzureCredential()
    
    async with MsgraphgroupsanduserClient(CONNECTION_RUNTIME_URL, credential) as client:
        try:
            skus = await client.list_subscribed_skus_async()
            
            if skus and "value" in skus:
                print(f"Found {len(skus['value'])} subscribed SKUs:")
                for sku in skus["value"][:5]:  # Show first 5
                    sku_part_number = sku.get("skuPartNumber", "Unknown")
                    consumed = sku.get("consumedUnits", 0)
                    print(f"  - {sku_part_number} (Consumed: {consumed} units)")
            else:
                print("No subscribed SKUs found or unexpected response format.")
                
        except ConnectorException as ex:
            print(f"Connector error: {ex}")
        except Exception as ex:
            print(f"Error: {ex}")


async def main():
    """Run all examples."""
    print("MS Graph Groups & Users Connector SDK - Sample Usage")
    print("=" * 60)
    
    if not CONNECTION_RUNTIME_URL:
        print("\nWARNING: MSGRAPH_CONNECTION_URL environment variable not set.")
        print("Set it to your connection runtime URL to run actual API calls.")
        print("Format: https://[region].azure-apihub.net/apim/msgraphgroupsanduser/[connection-id]")
        return
    
    await example_1_list_users()
    await example_2_list_groups()
    await example_3_get_group_properties()
    await example_4_list_group_members()
    await example_5_list_subscribed_skus()
    
    print("\n" + "=" * 60)
    print("Sample completed!")


if __name__ == "__main__":
    asyncio.run(main())
