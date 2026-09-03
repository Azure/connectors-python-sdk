# Copyright (c) Microsoft Corporation. All rights reserved.

"""
Azure Data Factory Connector SDK Sample

This sample demonstrates how to use the Azure Data Factory connector SDK
to create, monitor, and cancel pipeline runs.

Prerequisites:
1. Azure subscription with Azure Data Factory
2. Azure Data Factory connection in Connector Namespaces
3. Connection runtime URL from Azure Portal

Installation:
    pip install azure-connectors

Usage:
    Set environment variable:
    $env:AZUREDATAFACTORY_CONNECTION_URL = "https://....azure-apihub.net/apim/..."

    python sample_connector_usage_azuredatafactory.py

Available operations:
- Create pipeline runs
- Get pipeline run status
- Cancel pipeline runs
"""

import asyncio
import os
from azure.identity.aio import DefaultAzureCredential
from azure.connectors import ConnectorException
from azure.connectors.azuredatafactory import (
    AzuredatafactoryClient,
    ParameterValueSpecification,
    CreatePipelineRunResponse,
    PipelineRun,
)

# Connection runtime URL format:
# https://[region].azure-apihub.net/apim/azuredatafactory/[connection-id]
CONNECTION_RUNTIME_URL = os.environ.get(
    "AZUREDATAFACTORY_CONNECTION_URL",
    ""
)

# Azure resource details - update these for your environment
SUBSCRIPTION_ID = os.environ.get("AZURE_SUBSCRIPTION_ID", "your-subscription-id")
RESOURCE_GROUP = os.environ.get("AZURE_RESOURCE_GROUP", "your-resource-group")
DATA_FACTORY_NAME = os.environ.get("ADF_NAME", "your-data-factory")
PIPELINE_NAME = os.environ.get("ADF_PIPELINE_NAME", "your-pipeline")


async def example_1_create_pipeline_run():
    """Example 1: Create a new pipeline run."""
    print("\n=== Example 1: Create Pipeline Run ===")

    credential = DefaultAzureCredential()

    async with AzuredatafactoryClient(
        CONNECTION_RUNTIME_URL, credential
    ) as client:
        try:
            # Create parameters for the pipeline run
            parameters = ParameterValueSpecification(
                additional_properties={
                    # Add your pipeline parameters here
                    # "inputPath": "/data/input",
                    # "outputPath": "/data/output",
                }
            )

            # Create the pipeline run
            result = await client.create_pipeline_run_async(
                input=parameters,
                subscription_id=SUBSCRIPTION_ID,
                resource_group_name=RESOURCE_GROUP,
                data_factory_name=DATA_FACTORY_NAME,
                pipeline_name=PIPELINE_NAME,
            )

            if result:
                run_id = result.get("runId", "Unknown")
                print("Pipeline run created successfully!")
                print(f"Run ID: {run_id}")
                return run_id
            else:
                print("Pipeline run created (no response body)")
                return None

        except ConnectorException as ex:
            print(f"Connector error: {ex.status_code} - {ex.response_body}")
            return None
        except Exception as ex:
            print(f"Error: {ex}")
            return None


async def example_2_get_pipeline_run_status(run_id: str):
    """Example 2: Get the status of a pipeline run."""
    print("\n=== Example 2: Get Pipeline Run Status ===")

    if not run_id:
        print("No run ID provided, skipping...")
        return

    credential = DefaultAzureCredential()

    async with AzuredatafactoryClient(
        CONNECTION_RUNTIME_URL, credential
    ) as client:
        try:
            # Get the pipeline run status
            result = await client.get_pipeline_run_async(
                subscription_id=SUBSCRIPTION_ID,
                resource_group_name=RESOURCE_GROUP,
                data_factory_name=DATA_FACTORY_NAME,
                pipeline_run_name=run_id,
            )

            if result:
                print(f"Pipeline: {result.get('pipelineName', 'N/A')}")
                print(f"Run ID: {result.get('runId', 'N/A')}")
                print(f"Status: {result.get('status', 'Unknown')}")
                print(f"Start Time: {result.get('runStart', 'N/A')}")
                print(f"End Time: {result.get('runEnd', 'N/A')}")
                duration = result.get('durationInMs')
                if duration:
                    print(f"Duration: {duration}ms ({duration / 1000:.2f}s)")
                message = result.get('message')
                if message:
                    print(f"Message: {message}")
            else:
                print("No run status returned")

        except ConnectorException as ex:
            print(f"Connector error: {ex.status_code}")
        except Exception as ex:
            print(f"Error: {ex}")


async def example_3_cancel_pipeline_run(run_id: str):
    """Example 3: Cancel a running pipeline."""
    print("\n=== Example 3: Cancel Pipeline Run ===")

    if not run_id:
        print("No run ID provided, skipping...")
        return

    credential = DefaultAzureCredential()

    async with AzuredatafactoryClient(
        CONNECTION_RUNTIME_URL, credential
    ) as client:
        try:
            # Cancel the pipeline run
            await client.cancel_pipeline_run_async(
                subscription_id=SUBSCRIPTION_ID,
                resource_group_name=RESOURCE_GROUP,
                data_factory_name=DATA_FACTORY_NAME,
                pipeline_run_name=run_id,
            )

            print(f"Pipeline run {run_id} cancellation requested")

        except ConnectorException as ex:
            print(f"Connector error: {ex.status_code}")
        except Exception as ex:
            print(f"Error: {ex}")


async def example_4_dataclass_usage():
    """Example 4: Working with Azure Data Factory data types."""
    print("\n=== Example 4: Data Types ===")

    # CreatePipelineRunResponse - represents a created pipeline run
    run_response = CreatePipelineRunResponse(
        run_id="12345678-1234-1234-1234-123456789012"
    )
    print(f"Run Response ID: {run_response.run_id}")

    # PipelineRun - represents pipeline run details
    run = PipelineRun(
        run_id="12345678-1234-1234-1234-123456789012",
        pipeline_name="CopyDataPipeline",
        status="Succeeded",
        duration_in_ms=45000,
        parameters={"inputPath": "/data/input", "outputPath": "/data/output"},
        run_start="2024-01-15T10:00:00Z",
        run_end="2024-01-15T10:00:45Z"
    )
    print(f"Pipeline: {run.pipeline_name}")
    print(f"Status: {run.status}")
    print(f"Duration: {run.duration_in_ms}ms")

    # ParameterValueSpecification - for passing pipeline parameters
    params = ParameterValueSpecification(
        additional_properties={
            "sourceContainer": "raw-data",
            "targetContainer": "processed-data",
            "filePattern": "*.csv"
        }
    )
    print(f"Parameters: {params.additional_properties}")


async def main():
    """Run all examples."""
    if not CONNECTION_RUNTIME_URL:
        print("Error: AZUREDATAFACTORY_CONNECTION_URL environment variable "
              "not set.")
        print("Set it to your connection runtime URL from Azure Portal.")
        print("\nRunning data type examples without connection...\n")
        await example_4_dataclass_usage()
        return

    print(f"Using connection URL: {CONNECTION_RUNTIME_URL[:50]}...")
    print(f"Subscription: {SUBSCRIPTION_ID}")
    print(f"Resource Group: {RESOURCE_GROUP}")
    print(f"Data Factory: {DATA_FACTORY_NAME}")
    print(f"Pipeline: {PIPELINE_NAME}")

    # Create a pipeline run
    run_id = await example_1_create_pipeline_run()

    # Get the status of the run
    if run_id:
        await example_2_get_pipeline_run_status(run_id)

    # Uncomment to cancel the run (be careful with this!)
    # if run_id:
    #     await example_3_cancel_pipeline_run(run_id)

    # Show data type usage
    await example_4_dataclass_usage()

    print("\n=== All examples completed ===")


if __name__ == "__main__":
    asyncio.run(main())
