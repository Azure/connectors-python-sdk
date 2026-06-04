# Copyright (c) Microsoft Corporation. All rights reserved.

"""
Windows Defender ATP (Microsoft Defender for Endpoint) Connector SDK Sample

This sample demonstrates how to use the Windows Defender ATP connector SDK
to interact with Microsoft Defender for Endpoint for security operations.

Prerequisites:
1. Azure subscription with Windows Defender ATP connection
2. WDATP connection in Connector Namespaces (with access configured)
3. Connection runtime URL from Azure Portal
4. Microsoft Defender for Endpoint subscription

Installation:
    pip install azure-connectors

Usage:
    Set environment variable:
    $env:WDATP_CONNECTION_URL = "https://...apihub.net/apim/wdatp/..."

    python sample_connector_usage_wdatp.py
"""

import asyncio
import os
from azure.identity.aio import DefaultAzureCredential
from azure.connectors import ConnectorException
from azure.connectors.wdatp import (
    WdatpClient,
    AdvancedHuntingInput,
    PatchAlertInput,
)

# Connection runtime URL format:
# https://[region].azure-apihub.net/apim/wdatp/[connection-id]
CONNECTION_RUNTIME_URL = os.environ.get(
    "WDATP_CONNECTION_URL",
    ""
)


async def example_1_list_alerts():
    """Example 1: List recent security alerts."""
    print("\n=== Example 1: List Security Alerts ===")

    credential = DefaultAzureCredential()

    async with WdatpClient(CONNECTION_RUNTIME_URL, credential) as client:
        try:
            result = await client.get_alerts_async(
                top="5",
                orderby="alertCreationTime desc"
            )

            if result and result.get("value"):
                print(f"Found {result.get('count', len(result['value']))} alerts:")
                for alert in result["value"][:5]:
                    print(f"  - [{alert.get('severity', 'N/A')}] {alert.get('title', 'N/A')}")
                    print(f"    ID: {alert.get('id', 'N/A')}")
                    print(f"    Status: {alert.get('status', 'N/A')}")
            else:
                print("No alerts found.")

        except ConnectorException as ex:
            print(f"Connector error (status {ex.status_code}): {ex}")
        except Exception as ex:
            print(f"Error: {ex}")


async def example_2_get_machines():
    """Example 2: List machines in the organization."""
    print("\n=== Example 2: List Machines ===")

    credential = DefaultAzureCredential()

    async with WdatpClient(CONNECTION_RUNTIME_URL, credential) as client:
        try:
            result = await client.get_machines_async(top="10")

            if result and result.get("value"):
                print(f"Found {result.get('count', len(result['value']))} machines:")
                for machine in result["value"][:5]:
                    print(f"  - {machine.get('computerDnsName', 'N/A')}")
                    print(f"    ID: {machine.get('id', 'N/A')}")
                    print(f"    OS: {machine.get('osPlatform', 'N/A')}")
                    print(f"    Health: {machine.get('healthStatus', 'N/A')}")
            else:
                print("No machines found.")

        except ConnectorException as ex:
            print(f"Connector error (status {ex.status_code}): {ex}")
        except Exception as ex:
            print(f"Error: {ex}")


async def example_3_advanced_hunting():
    """Example 3: Run an advanced hunting query."""
    print("\n=== Example 3: Advanced Hunting Query ===")

    credential = DefaultAzureCredential()

    async with WdatpClient(CONNECTION_RUNTIME_URL, credential) as client:
        try:
            # Query for device information
            query = "DeviceInfo | take 5 | project DeviceName, OSPlatform, PublicIP"
            input_data = AdvancedHuntingInput(query=query)

            result = await client.advanced_hunting_async(input=input_data)

            if result and result.get("results"):
                print(f"Query returned {len(result['results'])} results:")
                for row in result["results"]:
                    print(f"  - {row}")
            else:
                print("No results from query.")

            if result and result.get("stats"):
                print(f"Execution time: {result['stats'].get('executionTime', 'N/A')}s")

        except ConnectorException as ex:
            print(f"Connector error (status {ex.status_code}): {ex}")
        except Exception as ex:
            print(f"Error: {ex}")


async def example_4_update_alert():
    """Example 4: Update an alert status."""
    print("\n=== Example 4: Update Alert Status ===")

    # Get alert ID from environment or skip
    alert_id = os.environ.get("WDATP_ALERT_ID", "")
    if not alert_id:
        print("Set WDATP_ALERT_ID to update a specific alert.")
        print("Skipping this example.")
        return

    credential = DefaultAzureCredential()

    async with WdatpClient(CONNECTION_RUNTIME_URL, credential) as client:
        try:
            input_data = PatchAlertInput(
                status="InProgress",
                assigned_to="security-team@example.com",
                classification="TruePositive"
            )

            result = await client.patch_alert_async(
                input=input_data,
                alert_id=alert_id
            )

            print("Alert updated:")
            print(f"  ID: {result.get('id', 'N/A')}")
            print(f"  Status: {result.get('status', 'N/A')}")

        except ConnectorException as ex:
            print(f"Connector error (status {ex.status_code}): {ex}")
        except Exception as ex:
            print(f"Error: {ex}")


async def example_5_get_file_stats():
    """Example 5: Get file statistics by SHA1 hash."""
    print("\n=== Example 5: Get File Statistics ===")

    # Example SHA1 hash (use a real one from your environment)
    file_sha1 = os.environ.get("WDATP_FILE_SHA1", "")
    if not file_sha1:
        print("Set WDATP_FILE_SHA1 to check a specific file.")
        print("Skipping this example.")
        return

    credential = DefaultAzureCredential()

    async with WdatpClient(CONNECTION_RUNTIME_URL, credential) as client:
        try:
            result = await client.get_file_stats_async(file_id=file_sha1)

            print(f"File statistics for {file_sha1}:")
            print(f"  Global prevalence: {result.get('globallyPrevalence', 'N/A')}")
            print(f"  Org prevalence: {result.get('organizationPrevalence', 'N/A')}")
            print(f"  First seen globally: {result.get('globalFirstObserved', 'N/A')}")

        except ConnectorException as ex:
            print(f"Connector error (status {ex.status_code}): {ex}")
        except Exception as ex:
            print(f"Error: {ex}")


async def example_6_machine_actions():
    """Example 6: List recent machine actions."""
    print("\n=== Example 6: List Machine Actions ===")

    credential = DefaultAzureCredential()

    async with WdatpClient(CONNECTION_RUNTIME_URL, credential) as client:
        try:
            result = await client.get_machine_actions_async(
                top="5",
                orderby="creationDateTimeUtc desc"
            )

            if result and result.get("value"):
                print(f"Found {result.get('count', len(result['value']))} actions:")
                for action in result["value"][:5]:
                    print(f"  - Type: {action.get('type', 'N/A')}")
                    print(f"    Status: {action.get('status', 'N/A')}")
                    print(f"    Machine: {action.get('machineId', 'N/A')[:20]}...")
            else:
                print("No machine actions found.")

        except ConnectorException as ex:
            print(f"Connector error (status {ex.status_code}): {ex}")
        except Exception as ex:
            print(f"Error: {ex}")


async def example_7_investigations():
    """Example 7: List automated investigations."""
    print("\n=== Example 7: List Investigations ===")

    credential = DefaultAzureCredential()

    async with WdatpClient(CONNECTION_RUNTIME_URL, credential) as client:
        try:
            result = await client.get_investigations_async(top="5")

            if result and result.get("value"):
                print(f"Found {result.get('count', len(result['value']))} investigations:")
                for inv in result["value"][:5]:
                    print(f"  - ID: {inv.get('id', 'N/A')}")
                    print(f"    State: {inv.get('state', 'N/A')}")
                    print(f"    Machine: {inv.get('computerDnsName', 'N/A')}")
            else:
                print("No investigations found.")

        except ConnectorException as ex:
            print(f"Connector error (status {ex.status_code}): {ex}")
        except Exception as ex:
            print(f"Error: {ex}")


async def main():
    """Run all examples."""
    if not CONNECTION_RUNTIME_URL:
        print("Error: WDATP_CONNECTION_URL environment variable not set.")
        print("Set it to your connection runtime URL from Azure Portal.")
        print("\nExample:")
        print('$env:WDATP_CONNECTION_URL = ')
        print('  "https://[region].azure-apihub.net/apim/wdatp/[id]"')
        return

    print(f"Using connection URL: {CONNECTION_RUNTIME_URL[:50]}...")

    # Read operations
    await example_1_list_alerts()
    await example_2_get_machines()
    await example_3_advanced_hunting()
    await example_5_get_file_stats()
    await example_6_machine_actions()
    await example_7_investigations()

    # Update operations (requires specific IDs)
    await example_4_update_alert()

    print("\n=== All examples completed ===")


if __name__ == "__main__":
    asyncio.run(main())
