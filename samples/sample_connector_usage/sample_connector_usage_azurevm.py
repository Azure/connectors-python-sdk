# Copyright (c) Microsoft Corporation. All rights reserved.

"""
Azure VM Connector SDK Sample

This sample demonstrates how to use the Azure VM connector SDK to manage
virtual machines and VM scale sets.

Prerequisites:
1. Azure subscription with Azure VM connection
2. Azure VM connection in Connector Namespaces
3. Connection runtime URL from Azure Portal

Installation:
    pip install azure-connectors

Usage:
    Set environment variable:
    $env:AZUREVM_CONNECTION_URL = "https://[region].azure-apihub.net/apim/azurevm/[connection-id]"

    python sample_connector_usage_azurevm.py
"""

import asyncio
import os
from azure.identity.aio import DefaultAzureCredential
from azure.connectors import ConnectorException
from azure.connectors.azurevm import AzurevmClient

# Connection runtime URL format:
# https://[region].azure-apihub.net/apim/azurevm/[connection-id]
CONNECTION_RUNTIME_URL = os.environ.get(
    "AZUREVM_CONNECTION_URL",
    ""
)

# Sample resource identifiers (replace with your own)
SUBSCRIPTION_ID = os.environ.get("AZURE_SUBSCRIPTION_ID", "your-subscription-id")
RESOURCE_GROUP = os.environ.get("AZURE_RESOURCE_GROUP", "your-resource-group")
VM_NAME = os.environ.get("AZURE_VM_NAME", "your-vm-name")
VMSS_NAME = os.environ.get("AZURE_VMSS_NAME", "your-vmss-name")
VMSS_INSTANCE_ID = os.environ.get("AZURE_VMSS_INSTANCE_ID", "0")


async def example_1_get_virtual_machine():
    """Example 1: Get details of a virtual machine."""
    print("\n=== Example 1: Get Virtual Machine ===")

    credential = DefaultAzureCredential()

    async with AzurevmClient(CONNECTION_RUNTIME_URL, credential) as client:
        try:
            result = await client.virtual_machine_get_async(
                subscription_id=SUBSCRIPTION_ID,
                resource_group_name=RESOURCE_GROUP,
                virtual_machine_name=VM_NAME
            )

            if result:
                print(f"VM Name: {result.get('name')}")
                print(f"VM ID: {result.get('id')}")
                props = result.get('properties', {})
                print(f"Provisioning State: {props.get('provisioningState')}")
            else:
                print("No VM found")

        except ConnectorException as ex:
            print(f"Connector error: {ex}")
        except Exception as ex:
            print(f"Error: {ex}")


async def example_2_start_virtual_machine():
    """Example 2: Start a virtual machine."""
    print("\n=== Example 2: Start Virtual Machine ===")

    credential = DefaultAzureCredential()

    async with AzurevmClient(CONNECTION_RUNTIME_URL, credential) as client:
        try:
            await client.virtual_machine_start_async(
                subscription_id=SUBSCRIPTION_ID,
                resource_group_name=RESOURCE_GROUP,
                virtual_machine_name=VM_NAME
            )

            print(f"Start command sent for VM: {VM_NAME}")
            print("Note: VM start is an async operation. Check Azure Portal for status.")

        except ConnectorException as ex:
            print(f"Connector error: {ex}")
        except Exception as ex:
            print(f"Error: {ex}")


async def example_3_deallocate_virtual_machine():
    """Example 3: Deallocate (stop and release resources) a virtual machine."""
    print("\n=== Example 3: Deallocate Virtual Machine ===")

    credential = DefaultAzureCredential()

    async with AzurevmClient(CONNECTION_RUNTIME_URL, credential) as client:
        try:
            await client.virtual_machine_deallocate_async(
                subscription_id=SUBSCRIPTION_ID,
                resource_group_name=RESOURCE_GROUP,
                virtual_machine_name=VM_NAME
            )

            print(f"Deallocate command sent for VM: {VM_NAME}")
            print("Note: This releases compute resources. You won't be billed while deallocated.")

        except ConnectorException as ex:
            print(f"Connector error: {ex}")
        except Exception as ex:
            print(f"Error: {ex}")


async def example_4_restart_virtual_machine():
    """Example 4: Restart a virtual machine."""
    print("\n=== Example 4: Restart Virtual Machine ===")

    credential = DefaultAzureCredential()

    async with AzurevmClient(CONNECTION_RUNTIME_URL, credential) as client:
        try:
            await client.virtual_machine_restart_async(
                subscription_id=SUBSCRIPTION_ID,
                resource_group_name=RESOURCE_GROUP,
                virtual_machine_name=VM_NAME
            )

            print(f"Restart command sent for VM: {VM_NAME}")

        except ConnectorException as ex:
            print(f"Connector error: {ex}")
        except Exception as ex:
            print(f"Error: {ex}")


async def example_5_get_vm_in_scale_set():
    """Example 5: Get details of a VM in a scale set."""
    print("\n=== Example 5: Get VM in Scale Set ===")

    credential = DefaultAzureCredential()

    async with AzurevmClient(CONNECTION_RUNTIME_URL, credential) as client:
        try:
            result = await client.virtual_machine_in_scale_set_get_async(
                subscription_id=SUBSCRIPTION_ID,
                resource_group_name=RESOURCE_GROUP,
                virtual_machine_scale_set_name=VMSS_NAME,
                virtual_machine_in_scale_set_instance_id=VMSS_INSTANCE_ID
            )

            if result:
                print(f"VMSS Instance Name: {result.get('name')}")
                print(f"Instance ID: {result.get('instanceId')}")
                props = result.get('properties', {})
                print(f"Provisioning State: {props.get('provisioningState')}")
            else:
                print("No VMSS instance found")

        except ConnectorException as ex:
            print(f"Connector error: {ex}")
        except Exception as ex:
            print(f"Error: {ex}")


async def example_6_scale_set_operations():
    """Example 6: Perform operations on a VM in a scale set."""
    print("\n=== Example 6: Scale Set VM Operations ===")

    credential = DefaultAzureCredential()

    async with AzurevmClient(CONNECTION_RUNTIME_URL, credential) as client:
        try:
            # Start VM in scale set
            print(f"Starting VMSS instance {VMSS_INSTANCE_ID}...")
            await client.virtual_machine_in_scale_set_start_async(
                subscription_id=SUBSCRIPTION_ID,
                resource_group_name=RESOURCE_GROUP,
                virtual_machine_scale_set_name=VMSS_NAME,
                virtual_machine_in_scale_set_instance_id=VMSS_INSTANCE_ID
            )
            print("Start command sent")

            # Other available operations (commented out):
            # - virtual_machine_in_scale_set_deallocate_async
            # - virtual_machine_in_scale_set_power_off_async
            # - virtual_machine_in_scale_set_restart_async
            # - virtual_machine_in_scale_set_redeploy_async
            # - virtual_machine_in_scale_set_reimage_async

        except ConnectorException as ex:
            print(f"Connector error: {ex}")
        except Exception as ex:
            print(f"Error: {ex}")


async def main():
    """Run all examples."""
    if not CONNECTION_RUNTIME_URL:
        print("Error: AZUREVM_CONNECTION_URL environment variable not set.")
        print("Set it to your connection runtime URL from Azure Portal.")
        return

    print(f"Using connection URL: {CONNECTION_RUNTIME_URL[:50]}...")

    # Only run the read-only example by default
    await example_1_get_virtual_machine()

    # Uncomment to run VM control operations:
    # await example_2_start_virtual_machine()
    # await example_3_deallocate_virtual_machine()
    # await example_4_restart_virtual_machine()
    # await example_5_get_vm_in_scale_set()
    # await example_6_scale_set_operations()

    print("\n=== All examples completed ===")


if __name__ == "__main__":
    asyncio.run(main())
