# Copyright (c) Microsoft Corporation. All rights reserved.

"""
Azure IoT Central Connector SDK Sample

This sample demonstrates how to use the Azure IoT Central connector SDK.

Prerequisites:
1. Azure subscription with an Azure IoT Central connection
2. Azure IoT Central connection in Connector Namespaces
3. Connection runtime URL from Azure Portal

Installation:
    pip install azure-connectors

Usage:
    Set environment variables:
    $env:AZUREIOTCENTRAL_CONNECTION_URL = (
        "https://[region].azure-apihub.net/apim/azureiotcentral/[connection-id]"
    )
    $env:AZUREIOTCENTRAL_APPLICATION = "[application-host-or-id]"

    python sample_connector_usage_azureiotcentral.py
"""

import asyncio
import os

from azure.identity.aio import DefaultAzureCredential
from azure.connectors import ConnectorException
from azure.connectors.azureiotcentral import (
    AzureiotcentralClient,
    DeviceGroup,
)

# Connection runtime URL format:
# https://[region].azure-apihub.net/apim/azureiotcentral/[connection-id]
CONNECTION_RUNTIME_URL = os.environ.get(
    "AZUREIOTCENTRAL_CONNECTION_URL",
    "",
)

# The IoT Central application host or ID the operations target.
APPLICATION = os.environ.get("AZUREIOTCENTRAL_APPLICATION", "")


async def example_1_list_devices():
    """Example 1: List devices in the IoT Central application."""
    print("\n=== Example 1: List Devices ===")

    credential = DefaultAzureCredential()

    async with AzureiotcentralClient(CONNECTION_RUNTIME_URL, credential) as client:
        result = await client.devices_list_async(application=APPLICATION)
        devices = result.get("value", []) if result else []

        print(f"Found {len(devices)} device(s).")
        for device in devices[:10]:
            display_name = device.get("displayName", "N/A")
            device_id = device.get("id", "N/A")
            print(f"  - {display_name} ({device_id})")


async def example_2_list_device_groups():
    """Example 2: List device groups in the IoT Central application."""
    print("\n=== Example 2: List Device Groups ===")

    credential = DefaultAzureCredential()

    async with AzureiotcentralClient(CONNECTION_RUNTIME_URL, credential) as client:
        result = await client.device_groups_list_async(application=APPLICATION)
        device_groups = result.get("value", []) if result else []

        print(f"Found {len(device_groups)} device group(s).")
        for device_group in device_groups[:10]:
            display_name = device_group.get("displayName", "N/A")
            group_id = device_group.get("id", "N/A")
            print(f"  - {display_name} ({group_id})")


async def example_3_create_device_group():
    """Example 3: Create or update a device group."""
    print("\n=== Example 3: Create Device Group ===")

    device_group_id = os.environ.get("AZUREIOTCENTRAL_DEVICE_GROUP_ID", "")

    if not device_group_id:
        print("Set AZUREIOTCENTRAL_DEVICE_GROUP_ID to run this example.")
        return

    credential = DefaultAzureCredential()

    async with AzureiotcentralClient(CONNECTION_RUNTIME_URL, credential) as client:
        try:
            result = await client.device_groups_set_async(
                input=DeviceGroup(display_name="SDK sample group"),
                device_group_id=device_group_id,
                application=APPLICATION,
            )
            group_id = result.get("id", "N/A") if result else "N/A"
            print(f"Device group upserted: {group_id}")
        except ConnectorException as ex:
            print(f"Connector error: {ex}")


async def main():
    """Run all Azure IoT Central connector examples."""
    if not CONNECTION_RUNTIME_URL:
        print("Error: AZUREIOTCENTRAL_CONNECTION_URL environment variable is not set.")
        print("Set it to your Azure IoT Central connector runtime URL from Azure Portal.")
        return

    print(f"Using connection URL: {CONNECTION_RUNTIME_URL[:50]}...")

    await example_1_list_devices()
    await example_2_list_device_groups()
    await example_3_create_device_group()

    print("\n=== Azure IoT Central sample completed ===")


if __name__ == "__main__":
    asyncio.run(main())
