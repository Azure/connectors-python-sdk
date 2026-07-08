# Copyright (c) Microsoft Corporation. All rights reserved.

"""
Azure Monitor Logs Connector SDK Sample

This sample demonstrates how to use the Azure Monitor Logs connector SDK.

Prerequisites:
1. Azure subscription with Azure Monitor Logs access
2. Azure Monitor Logs connection in Connector Namespace
3. Connection runtime URL from Azure Portal
4. A Log Analytics workspace or Application Insights resource

Installation:
    pip install azure-connectors

Usage:
    Set environment variable:
    $env:AZUREMONITORLOGS_CONNECTION_URL = "https://[region].azure-apihub.net/apim/azuremonitorlogs/[connection-id]"

    python sample_connector_usage_azuremonitorlogs.py
"""

import asyncio
import os

try:
    from azure.identity.aio import DefaultAzureCredential
    from azure.connectors import ConnectorException
    from azure.connectors.azuremonitorlogs import (
        AzuremonitorlogsClient,
        QueryDataInput,
        VisualizeQueryInput,
    )
    IMPORTS_AVAILABLE = True
except ImportError as import_error:
    IMPORTS_AVAILABLE = False
    IMPORT_ERROR = str(import_error)


CONNECTION_RUNTIME_URL = os.environ.get(
    "AZUREMONITORLOGS_CONNECTION_URL",
    "",
)

SUBSCRIPTION_ID = os.environ.get("AZUREMONITORLOGS_SUBSCRIPTION", "")
RESOURCE_GROUP = os.environ.get("AZUREMONITORLOGS_RESOURCE_GROUP", "")
RESOURCE_TYPE = os.environ.get(
    "AZUREMONITORLOGS_RESOURCE_TYPE",
    "Microsoft.OperationalInsights/workspaces",
)
RESOURCE_NAME = os.environ.get("AZUREMONITORLOGS_RESOURCE_NAME", "")


def _print_configuration_help():
    print("Missing required environment variables.")
    print("Please set:")
    print("  AZUREMONITORLOGS_CONNECTION_URL")
    print("  AZUREMONITORLOGS_SUBSCRIPTION")
    print("  AZUREMONITORLOGS_RESOURCE_GROUP")
    print("  AZUREMONITORLOGS_RESOURCE_NAME")


async def example_list_discovery_values():
    """List subscriptions and resource groups using discovery APIs."""
    print("\n=== Example 1: Discovery Operations ===")

    credential = DefaultAzureCredential()

    async with AzuremonitorlogsClient(CONNECTION_RUNTIME_URL, credential) as client:
        try:
            subscriptions = await client.list_subscriptions_async()
            count = len(subscriptions.get("value", [])) if subscriptions else 0
            print(f"Found {count} subscriptions.")

            resource_groups = await client.list_resource_groups_async(
                subscriptions=SUBSCRIPTION_ID
            )
            rg_count = len(resource_groups.get("value", [])) if resource_groups else 0
            print(f"Found {rg_count} resource groups in subscription.")

        except ConnectorException as ex:
            print(f"Connector error: {ex}")
        except Exception as ex:
            print(f"Error: {ex}")


async def example_run_query():
    """Run a KQL query and list tabular rows."""
    print("\n=== Example 2: Run Query Data ===")

    credential = DefaultAzureCredential()

    async with AzuremonitorlogsClient(CONNECTION_RUNTIME_URL, credential) as client:
        try:
            request = QueryDataInput(
                query="Heartbeat | take 5",
                timerangetype="SetInQuery",
            )

            result = await client.query_data_async(
                input=request,
                subscriptions=SUBSCRIPTION_ID,
                resourcegroups=RESOURCE_GROUP,
                resourcetype=RESOURCE_TYPE,
                resourcename=RESOURCE_NAME,
            )

            rows = result.get("value", []) if result else []
            print(f"Returned {len(rows)} rows.")
            for index, row in enumerate(rows[:3], 1):
                print(f"  Row {index}: {row}")

        except ConnectorException as ex:
            print(f"Connector error: {ex}")
        except Exception as ex:
            print(f"Error: {ex}")


async def example_visualize_query():
    """Run query visualization."""
    print("\n=== Example 3: Visualize Query ===")

    credential = DefaultAzureCredential()

    async with AzuremonitorlogsClient(CONNECTION_RUNTIME_URL, credential) as client:
        try:
            request = VisualizeQueryInput(
                query=(
                    "Heartbeat "
                    "| summarize Count=count() by bin(TimeGenerated, 1h) "
                    "| order by TimeGenerated asc"
                ),
                timerangetype="SetInQuery",
            )

            result = await client.visualize_query_async(
                input=request,
                subscriptions=SUBSCRIPTION_ID,
                resourcegroups=RESOURCE_GROUP,
                resourcetype=RESOURCE_TYPE,
                resourcename=RESOURCE_NAME,
                vis_type="linechart",
            )

            if result:
                print("Visualization payload returned.")
                print(f"Keys: {list(result.keys())}")
            else:
                print("Visualization completed with empty response.")

        except ConnectorException as ex:
            print(f"Connector error: {ex}")
        except Exception as ex:
            print(f"Error: {ex}")


async def main():
    """Run Azure Monitor Logs connector samples."""
    if not IMPORTS_AVAILABLE:
        print("Required imports are unavailable:")
        print(f"  {IMPORT_ERROR}")
        return

    if not CONNECTION_RUNTIME_URL:
        _print_configuration_help()
        return

    if not SUBSCRIPTION_ID or not RESOURCE_GROUP or not RESOURCE_NAME:
        _print_configuration_help()
        return

    await example_list_discovery_values()
    await example_run_query()
    await example_visualize_query()


if __name__ == "__main__":
    asyncio.run(main())
