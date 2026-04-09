"""
Microsoft Teams Connector SDK Sample

This sample demonstrates how to use the Teams connector SDK.

Prerequisites:
1. Azure subscription with Teams connection
2. Teams connection in Azure Logic Apps
3. Connection runtime URL from Azure Portal

Installation:
    pip install <TBD>

Usage:
    python sample_teams_usage.py
"""

import asyncio
from azure.identity import DefaultAzureCredential
from azure_workflows_connectors_sdk.generated.teams_client import TeamsClient

# NOTE(victoriahall): Connection runtime URL format:
# https://[region].azure-apihub.net/apim/teams/[connection-id]
CONNECTION_RUNTIME_URL = "https://westus.azure-apihub.net/apim/teams/YOUR-CONNECTION-ID"


async def example_1_list_joined_teams():
    """Example 1: List all Teams you're a member of"""
    print("\n=== Example 1: List Joined Teams ===")
    
    credential = DefaultAzureCredential()
    client = TeamsClient(CONNECTION_RUNTIME_URL, credential)
    
    try:
        teams = await client.list_joined_teams_async()
        
        print(f"Found {len(teams.get('value', []))} teams")
        for team in teams.get('value', [])[:3]:  # Show first 3
            print(f"  - {team.get('displayName')} ({team.get('id')})")
            
    except Exception as ex:
        print(f"Error: {ex}")


async def example_2_list_associated_teams():
    """Example 2: List associated teams (direct membership + shared channels)"""
    print("\n=== Example 2: List Associated Teams ===")
    
    credential = DefaultAzureCredential()
    client = TeamsClient(CONNECTION_RUNTIME_URL, credential)
    
    try:
        teams = await client.get_all_associated_teams_async()
        
        print(f"Found {len(teams.get('value', []))} associated teams")
        for team in teams.get('value', [])[:3]:  # Show first 3
            print(f"  - {team.get('displayName')}")
            
    except Exception as ex:
        print(f"Error: {ex}")


async def example_3_get_supported_timezones():
    """Example 3: Get supported Outlook timezones"""
    print("\n=== Example 3: Get Supported Timezones ===")
    
    credential = DefaultAzureCredential()
    client = TeamsClient(CONNECTION_RUNTIME_URL, credential)
    
    try:
        timezones = await client.get_my_outlook_supported_time_zones_async()
        
        print(f"Found {len(timezones.get('value', []))} timezones")
        for tz in timezones.get('value', [])[:5]:  # Show first 5
            print(f"  - {tz.get('Alias')} ({tz.get('DisplayName')})")
            
    except Exception as ex:
        print(f"Error: {ex}")


async def main():
    """Run all examples"""
    print("Teams Connector SDK - Sample Usage")
    print("=" * 50)
    print()
    print("NOTE: Update CONNECTION_RUNTIME_URL in this file before running.")
    print("Get it from Azure Portal > Logic App > Teams Connection > Properties")
    print()
    
    await example_1_list_joined_teams()
    await example_2_list_associated_teams()
    await example_3_get_supported_timezones()
    
    print("\n" + "=" * 50)
    print("Sample completed!")


if __name__ == "__main__":
    asyncio.run(main())
