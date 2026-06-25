# Copyright (c) Microsoft Corporation. All rights reserved.

"""
Azure Digital Twins Connector SDK Sample

This sample demonstrates how to use the Azure Digital Twins connector SDK
to manage digital twins, models, relationships, and queries.

Prerequisites:
1. Azure subscription with Azure Digital Twins instance
2. Azure Digital Twins connection in Connector Namespaces
3. Connection runtime URL from Azure Portal

Installation:
    pip install azure-connectors

Usage:
    Set environment variable:
    $env:AZUREDIGITALTWINS_CONNECTION_URL = "https://....azure-apihub.net/apim/..."

    python sample_connector_usage_azuredigitaltwins.py

Available operations:
- Model management (list, get, delete)
- Twin management (create, get, update, delete)
- Relationship management
- Query twins
- Send telemetry
"""

import asyncio
import os
from azure.identity.aio import DefaultAzureCredential
from azure.connectors import ConnectorException
from azure.connectors.azuredigitaltwins import (
    AzuredigitaltwinsClient,
    QueryTwinsInput,
    SendTelemetryInput,
    TwinRelationship,
    IncomingRelationship,
)

# Connection runtime URL format:
# https://[region].azure-apihub.net/apim/azuredigitaltwins/[connection-id]
CONNECTION_RUNTIME_URL = os.environ.get(
    "AZUREDIGITALTWINS_CONNECTION_URL",
    ""
)


async def example_1_list_models():
    """Example 1: List all models in the instance."""
    print("\n=== Example 1: List Models ===")

    credential = DefaultAzureCredential()

    async with AzuredigitaltwinsClient(
        CONNECTION_RUNTIME_URL, credential
    ) as client:
        try:
            # List all models
            result = await client.list_models_async(
                include_model_definition="true"
            )

            if result and result.get("value"):
                print(f"Found {len(result['value'])} models:")
                for model in result["value"]:
                    print(f"  - {model.get('id', 'Unknown')}")
            else:
                print("No models found")

        except ConnectorException as ex:
            print(f"Connector error: {ex.status_code} - {ex.response_body}")
        except Exception as ex:
            print(f"Error: {ex}")


async def example_2_get_twin():
    """Example 2: Get a specific digital twin."""
    print("\n=== Example 2: Get Twin ===")

    credential = DefaultAzureCredential()
    twin_id = "room1"  # Replace with your twin ID

    async with AzuredigitaltwinsClient(
        CONNECTION_RUNTIME_URL, credential
    ) as client:
        try:
            # Get a twin by ID
            result = await client.get_twin_by_id_async(twinid=twin_id)

            if result:
                print(f"Twin ID: {result.get('$dtId', 'Unknown')}")
                metadata = result.get("$metadata", {})
                print(f"Model: {metadata.get('$model', 'Unknown')}")

                # Print properties
                for key, value in result.items():
                    if not key.startswith("$"):
                        print(f"  {key}: {value}")
            else:
                print(f"Twin '{twin_id}' not found")

        except ConnectorException as ex:
            print(f"Connector error: {ex.status_code}")
        except Exception as ex:
            print(f"Error: {ex}")


async def example_3_query_twins():
    """Example 3: Query digital twins."""
    print("\n=== Example 3: Query Twins ===")

    credential = DefaultAzureCredential()

    async with AzuredigitaltwinsClient(
        CONNECTION_RUNTIME_URL, credential
    ) as client:
        try:
            # Query all twins
            query_input = QueryTwinsInput(
                query="SELECT * FROM digitaltwins"
            )
            result = await client.query_twins_async(input=query_input)

            if result and result.get("value"):
                print(f"Query results: {result['value']}")
            else:
                print("No twins found matching query")

            # Check for continuation token for pagination
            if result and result.get("continuation_token"):
                print("More results available (use continuation_token)")

        except ConnectorException as ex:
            print(f"Connector error: {ex.status_code}")
        except Exception as ex:
            print(f"Error: {ex}")


async def example_4_list_relationships():
    """Example 4: List relationships for a twin."""
    print("\n=== Example 4: List Relationships ===")

    credential = DefaultAzureCredential()
    twin_id = "room1"  # Replace with your twin ID

    async with AzuredigitaltwinsClient(
        CONNECTION_RUNTIME_URL, credential
    ) as client:
        try:
            # List outgoing relationships
            outgoing = await client.list_relationships_async(twinid=twin_id)

            if outgoing and outgoing.get("value"):
                print(f"Outgoing relationships from {twin_id}:")
                for rel in outgoing["value"]:
                    print(f"  -> {rel.get('$targetId')} "
                          f"({rel.get('$relationshipName')})")
            else:
                print(f"No outgoing relationships from {twin_id}")

            # List incoming relationships
            incoming = await client.list_incoming_relationships_async(
                twinid=twin_id
            )

            if incoming and incoming.get("value"):
                print(f"Incoming relationships to {twin_id}:")
                for rel in incoming["value"]:
                    print(f"  <- {rel.get('$sourceId')} "
                          f"({rel.get('$relationshipName')})")
            else:
                print(f"No incoming relationships to {twin_id}")

        except ConnectorException as ex:
            print(f"Connector error: {ex.status_code}")
        except Exception as ex:
            print(f"Error: {ex}")


async def example_5_send_telemetry():
    """Example 5: Send telemetry from a twin."""
    print("\n=== Example 5: Send Telemetry ===")

    credential = DefaultAzureCredential()
    twin_id = "room1"  # Replace with your twin ID

    async with AzuredigitaltwinsClient(
        CONNECTION_RUNTIME_URL, credential
    ) as client:
        try:
            # Send telemetry
            telemetry = SendTelemetryInput(
                value='{"temperature": 72.5, "humidity": 45}'
            )
            await client.send_telemetry_async(
                input=telemetry,
                twinid=twin_id
            )

            print(f"Telemetry sent for twin '{twin_id}'")

        except ConnectorException as ex:
            print(f"Connector error: {ex.status_code}")
        except Exception as ex:
            print(f"Error: {ex}")


async def example_6_dataclass_usage():
    """Example 6: Working with Azure Digital Twins data types."""
    print("\n=== Example 6: Data Types ===")

    # TwinRelationship - represents a relationship between twins
    relationship = TwinRelationship(
        source_id="room1",
        relationship_id="rel-001",
        target_id="floor1",
        relationship_name="isPartOf",
        etag="abc123"
    )
    print(f"Relationship: {relationship.source_id} -> {relationship.target_id}")
    print(f"Type: {relationship.relationship_name}")

    # IncomingRelationship - represents an incoming relationship
    incoming = IncomingRelationship(
        source_id="building1",
        relationship_id="rel-002",
        relationship_name="contains"
    )
    print(f"Incoming: {incoming.source_id} ({incoming.relationship_name})")

    # QueryTwinsInput - for querying twins
    query = QueryTwinsInput(
        query="SELECT * FROM digitaltwins WHERE temperature > 70",
        continuation_token=None
    )
    print(f"Query: {query.query}")


async def main():
    """Run all examples."""
    if not CONNECTION_RUNTIME_URL:
        print("Error: AZUREDIGITALTWINS_CONNECTION_URL environment variable "
              "not set.")
        print("Set it to your connection runtime URL from Azure Portal.")
        print("\nRunning data type examples without connection...\n")
        await example_6_dataclass_usage()
        return

    print(f"Using connection URL: {CONNECTION_RUNTIME_URL[:50]}...")

    await example_1_list_models()
    await example_2_get_twin()
    await example_3_query_twins()
    await example_4_list_relationships()
    # Uncomment to send telemetry (requires existing twin)
    # await example_5_send_telemetry()
    await example_6_dataclass_usage()

    print("\n=== All examples completed ===")


if __name__ == "__main__":
    asyncio.run(main())
