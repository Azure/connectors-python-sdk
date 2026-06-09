# Copyright (c) Microsoft Corporation. All rights reserved.

"""
Azure Automation Connector SDK Sample

This sample demonstrates how to use the Azure Automation connector SDK
to interact with Azure Automation accounts, runbooks, and jobs.

Prerequisites:
1. Azure subscription with Azure Automation connection
2. Azure Automation connection in Connector Namespaces
3. Connection runtime URL from Azure Portal

Installation:
    pip install azure-connectors

Usage:
    Set environment variable:
    $env:AZUREAUTOMATION_CONNECTION_URL = "https://....azure-apihub.net/apim/..."

    python sample_connector_usage_azureautomation.py

Available operations:
- Create automation jobs
- Get job status
- Get job output
"""

import asyncio
import os
from azure.identity.aio import DefaultAzureCredential
from azure.connectors import ConnectorException
from azure.connectors.azureautomation import (
    AzureautomationClient,
    CreateJobResponse,
    Subscription,
    ResourceGroup,
)

# Connection runtime URL format:
# https://[region].azure-apihub.net/apim/azureautomation/[connection-id]
CONNECTION_RUNTIME_URL = os.environ.get(
    "AZUREAUTOMATION_CONNECTION_URL",
    ""
)


async def example_1_client_initialization():
    """Example 1: Initialize and verify the client."""
    print("\n=== Example 1: Client Initialization ===")

    credential = DefaultAzureCredential()

    async with AzureautomationClient(
        CONNECTION_RUNTIME_URL, credential
    ) as client:
        try:
            print("Client initialized successfully")
            print(f"Connector name: {client.connector_name}")
            print("Client is ready for Azure Automation operations")

        except ConnectorException as ex:
            print(f"Connector error: {ex}")
        except Exception as ex:
            print(f"Error: {ex}")


async def example_2_create_job():
    """Example 2: Create an automation job."""
    print("\n=== Example 2: Create Automation Job ===")

    credential = DefaultAzureCredential()

    async with AzureautomationClient(
        CONNECTION_RUNTIME_URL, credential
    ) as client:
        try:
            # Create a new automation job
            # Note: The connector requires subscription, resource group,
            # automation account, and runbook to be configured in the
            # connection settings.
            result = await client.create_job_async()

            if result:
                print(f"Job created: {result.get('id', 'N/A')}")
                props = result.get("properties", {})
                print(f"Status: {props.get('status', 'Unknown')}")
            else:
                print("Job created (no response body)")

        except ConnectorException as ex:
            print(f"Connector error: {ex.status_code} - {ex.response_body}")
        except Exception as ex:
            print(f"Error: {ex}")


async def example_3_create_job_and_wait():
    """Example 3: Create a job and wait for completion."""
    print("\n=== Example 3: Create Job and Wait ===")

    credential = DefaultAzureCredential()

    async with AzureautomationClient(
        CONNECTION_RUNTIME_URL, credential
    ) as client:
        try:
            # Create job with wait parameter to wait for completion
            result = await client.create_job_async(wait="true")

            if result:
                props = result.get("properties", {})
                print(f"Job completed with status: {props.get('status')}")
            else:
                print("Job completed (no response body)")

        except ConnectorException as ex:
            print(f"Connector error: {ex.status_code}")
        except Exception as ex:
            print(f"Error: {ex}")


async def example_4_get_job_status():
    """Example 4: Get the status of a job."""
    print("\n=== Example 4: Get Job Status ===")

    credential = DefaultAzureCredential()

    async with AzureautomationClient(
        CONNECTION_RUNTIME_URL, credential
    ) as client:
        try:
            # Get status of a job
            # Note: Job ID must be configured in connection settings
            result = await client.get_status_of_job_async()

            if result:
                print(f"Job ID: {result.get('id', 'N/A')}")
                props = result.get("properties", {})
                print(f"Status: {props.get('status', 'Unknown')}")
                print(f"Start time: {props.get('startTime', 'N/A')}")
                print(f"End time: {props.get('endTime', 'N/A')}")
            else:
                print("No job status returned")

        except ConnectorException as ex:
            print(f"Connector error: {ex.status_code}")
        except Exception as ex:
            print(f"Error: {ex}")


async def example_5_get_job_output():
    """Example 5: Get the output of a job."""
    print("\n=== Example 5: Get Job Output ===")

    credential = DefaultAzureCredential()

    async with AzureautomationClient(
        CONNECTION_RUNTIME_URL, credential
    ) as client:
        try:
            # Get output from a completed job
            output = await client.get_job_output_async()

            if output:
                # Output is returned as bytes
                print("Job output:")
                if isinstance(output, bytes):
                    print(output.decode("utf-8"))
                else:
                    print(output)
            else:
                print("No output returned")

        except ConnectorException as ex:
            print(f"Connector error: {ex.status_code}")
        except Exception as ex:
            print(f"Error: {ex}")


async def example_6_dataclass_usage():
    """Example 6: Working with Azure Automation data types."""
    print("\n=== Example 6: Data Types ===")

    # CreateJobResponse - represents an automation job
    job = CreateJobResponse(
        id="/subscriptions/xxx/resourceGroups/rg/providers/"
           "Microsoft.Automation/automationAccounts/account/jobs/job123",
        properties={
            "status": "Running",
            "runbook": {"name": "MyRunbook"},
            "startTime": "2024-01-15T10:00:00Z"
        }
    )
    print(f"Job ID: {job.id}")
    print(f"Job Status: {job.properties.get('status')}")

    # Subscription - Azure subscription info
    subscription = Subscription(
        subscription_id="00000000-0000-0000-0000-000000000000",
        display_name="Production Subscription",
        state="Enabled"
    )
    print(f"Subscription: {subscription.display_name}")

    # ResourceGroup - for targeting automation accounts
    rg = ResourceGroup(
        id="/subscriptions/xxx/resourceGroups/automation-rg",
        name="automation-rg"
    )
    print(f"Resource Group: {rg.name}")


async def main():
    """Run all examples."""
    if not CONNECTION_RUNTIME_URL:
        print("Error: AZUREAUTOMATION_CONNECTION_URL environment variable "
              "not set.")
        print("Set it to your connection runtime URL from Azure Portal.")
        print("\nRunning data type examples without connection...\n")
        await example_6_dataclass_usage()
        return

    print(f"Using connection URL: {CONNECTION_RUNTIME_URL[:50]}...")

    await example_1_client_initialization()
    await example_2_create_job()
    await example_3_create_job_and_wait()
    await example_4_get_job_status()
    await example_5_get_job_output()
    await example_6_dataclass_usage()

    print("\n=== All examples completed ===")


if __name__ == "__main__":
    asyncio.run(main())
