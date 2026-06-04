# Copyright (c) Microsoft Corporation. All rights reserved.

"""
Azure Resource Manager (ARM) Connector SDK Sample

This sample demonstrates how to use the ARM connector SDK to interact
with Azure Resource Manager APIs.

Prerequisites:
1. Azure subscription with ARM connection
2. ARM connection in Connector Namespaces (with OAuth consent)
3. Connection runtime URL from Azure Portal

Installation:
    pip install azure-connectors

Usage:
    Set environment variable:
    $env:ARM_CONNECTION_URL = "https://[region].azure-apihub.net/apim/arm/[connection-id]"

    python sample_connector_usage_arm.py

Note:
    The ARM connector uses OAuth (user-delegated Azure AD token).
    The connection requires OAuth consent via the consent link flow.
"""

import asyncio
import os
from azure.identity.aio import DefaultAzureCredential
from azure.connectors import ConnectorException
from azure.connectors.arm import ArmClient

# Connection runtime URL format:
# https://[region].azure-apihub.net/apim/arm/[connection-id]
CONNECTION_RUNTIME_URL = os.environ.get(
    "ARM_CONNECTION_URL",
    ""
)


async def example_1_list_subscriptions():
    """Example 1: List all subscriptions accessible to the authenticated user."""
    print("\n=== Example 1: List Subscriptions ===")

    credential = DefaultAzureCredential()

    async with ArmClient(CONNECTION_RUNTIME_URL, credential) as client:
        try:
            result = await client.subscriptions_list_async()

            if result and "value" in result:
                subscriptions = result["value"]
                print(f"Found {len(subscriptions)} subscription(s):")
                for sub in subscriptions:
                    sub_id = sub.get("subscriptionId", "N/A")
                    display_name = sub.get("displayName", "N/A")
                    state = sub.get("state", "N/A")
                    print(f"  - {display_name}")
                    print(f"      ID: {sub_id}")
                    print(f"      State: {state}")
            else:
                print("No subscriptions found or empty response.")

        except ConnectorException as ex:
            print(f"Connector error: {ex}")
        except Exception as ex:
            print(f"Error: {ex}")


async def example_2_list_subscriptions_with_details():
    """Example 2: List subscriptions with full details."""
    print("\n=== Example 2: List Subscriptions with Details ===")

    credential = DefaultAzureCredential()

    async with ArmClient(CONNECTION_RUNTIME_URL, credential) as client:
        try:
            result = await client.subscriptions_list_async()

            if result and "value" in result:
                subscriptions = result["value"]
                print(f"Retrieved {len(subscriptions)} subscription(s) with details:\n")

                for i, sub in enumerate(subscriptions, 1):
                    print(f"Subscription {i}:")
                    print(f"  Display Name: {sub.get('displayName', 'N/A')}")
                    print(f"  Subscription ID: {sub.get('subscriptionId', 'N/A')}")
                    print(f"  Tenant ID: {sub.get('tenantId', 'N/A')}")
                    print(f"  State: {sub.get('state', 'N/A')}")
                    print(f"  Full ID: {sub.get('id', 'N/A')}")

                    # Check for subscription policies
                    policies = sub.get("subscriptionPolicies", {})
                    if policies:
                        print("  Policies:")
                        print(f"    Quota ID: {policies.get('quotaId', 'N/A')}")
                        print(f"    Spending Limit: {policies.get('spendingLimit', 'N/A')}")

                    auth_source = sub.get("authorizationSource", "N/A")
                    print(f"  Authorization Source: {auth_source}")
                    print()

                # Check for pagination
                next_link = result.get("nextLink")
                if next_link:
                    print(f"More results available. Next link: {next_link}")
            else:
                print("No subscriptions found.")

        except ConnectorException as ex:
            print(f"Connector error: {ex}")
        except Exception as ex:
            print(f"Error: {ex}")


async def example_3_filter_enabled_subscriptions():
    """Example 3: List only enabled subscriptions."""
    print("\n=== Example 3: Filter Enabled Subscriptions ===")

    credential = DefaultAzureCredential()

    async with ArmClient(CONNECTION_RUNTIME_URL, credential) as client:
        try:
            result = await client.subscriptions_list_async()

            if result and "value" in result:
                all_subs = result["value"]
                enabled_subs = [
                    sub for sub in all_subs
                    if sub.get("state", "").lower() == "enabled"
                ]

                print(f"Found {len(enabled_subs)} enabled subscription(s) "
                      f"out of {len(all_subs)} total:\n")

                for sub in enabled_subs:
                    print(f"  - {sub.get('displayName', 'N/A')}")
                    print(f"      ID: {sub.get('subscriptionId', 'N/A')}")

                # Show disabled/warned subscriptions if any
                other_subs = [
                    sub for sub in all_subs
                    if sub.get("state", "").lower() != "enabled"
                ]
                if other_subs:
                    print(f"\nSubscriptions with other states ({len(other_subs)}):")
                    for sub in other_subs:
                        print(f"  - {sub.get('displayName', 'N/A')} "
                              f"({sub.get('state', 'N/A')})")
            else:
                print("No subscriptions found.")

        except ConnectorException as ex:
            print(f"Connector error: {ex}")
        except Exception as ex:
            print(f"Error: {ex}")


async def main():
    """Run all examples."""
    print("Azure Resource Manager (ARM) Connector SDK - Sample Usage")
    print("=" * 60)

    if not CONNECTION_RUNTIME_URL:
        print("\nWARNING: ARM_CONNECTION_URL environment variable not set.")
        print("Set it to your connection runtime URL to run actual API calls.")
        print("Format: https://[region].azure-apihub.net/apim/arm/[connection-id]")
        return

    await example_1_list_subscriptions()
    await example_2_list_subscriptions_with_details()
    await example_3_filter_enabled_subscriptions()

    print("\n" + "=" * 60)
    print("Sample completed!")


if __name__ == "__main__":
    asyncio.run(main())
