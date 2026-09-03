# Copyright (c) Microsoft Corporation. All rights reserved.

"""
Kusto (Azure Data Explorer) Connector SDK Sample

This sample demonstrates how to use the Kusto connector SDK.

Prerequisites:
1. Azure subscription with Kusto (Azure Data Explorer) cluster
2. Kusto connection in Connector Namespaces
3. Connection runtime URL from Azure Portal
4. Kusto cluster URL and database name

Installation:
    pip install azure-workflows-connectors-sdk

Usage:
    Set environment variables:
    $env:KUSTO_CONNECTION_URL = "https://[region].azure-apihub.net/apim/kusto/[connection-id]"
    $env:KUSTO_CLUSTER_URL = "https://[cluster-name].[region].kusto.windows.net"
    $env:KUSTO_DATABASE = "[database-name]"

    python sample_connector_usage_kusto.py
"""

import asyncio
import os

try:
    from azure.identity.aio import DefaultAzureCredential
    from azure.connectors import ConnectorException
    from azure.connectors.kusto import (
        KustoClient,
        QueryAndListSchema,
        ControlCommandAndListSchema,
        QueryAndVisualizeSchema,
    )
    IMPORTS_AVAILABLE = True
except ImportError as import_error:
    IMPORTS_AVAILABLE = False
    IMPORT_ERROR = str(import_error)


# Connection runtime URL format:
# https://[region].azure-apihub.net/apim/kusto/[connection-id]
CONNECTION_RUNTIME_URL = os.environ.get(
    "KUSTO_CONNECTION_URL",
    ""
)

# Kusto cluster URL format:
# https://[cluster-name].[region].kusto.windows.net
KUSTO_CLUSTER_URL = os.environ.get(
    "KUSTO_CLUSTER_URL",
    "https://help.kusto.windows.net"
)

KUSTO_DATABASE = os.environ.get(
    "KUSTO_DATABASE",
    "Samples"
)

KUSTO_TABLE = os.environ.get(
    "KUSTO_TABLE",
    "StormEvents"
)


async def example_1_simple_kql_query():
    """Example 1: Run a simple KQL query."""
    print("\n=== Example 1: Simple KQL Query ===")

    credential = DefaultAzureCredential()

    async with KustoClient(CONNECTION_RUNTIME_URL, credential) as client:
        try:
            query = f"{KUSTO_TABLE} | take 5"

            query_request = QueryAndListSchema(
                cluster=KUSTO_CLUSTER_URL,
                db=KUSTO_DATABASE,
                csl=query,
            )

            results = await client.list_kusto_results_async(input=query_request)

            if results and 'value' in results:
                print(f"Query executed successfully. Found {len(results['value'])} rows:")
                for i, row in enumerate(results['value'][:5], 1):
                    print(f"  Row {i}: {row}")
            else:
                print("Query executed but returned no data.")

        except ConnectorException as ex:
            print(f"Connector error: {ex}")
        except Exception as ex:
            print(f"Error: {ex}")


async def example_2_aggregation_query():
    """Example 2: Run a KQL query with aggregation."""
    print("\n=== Example 2: Aggregation Query ===")

    credential = DefaultAzureCredential()

    async with KustoClient(CONNECTION_RUNTIME_URL, credential) as client:
        try:
            query = f"""
                {KUSTO_TABLE}
                | summarize EventCount = count() by State
                | top 5 by EventCount desc
            """

            query_request = QueryAndListSchema(
                cluster=KUSTO_CLUSTER_URL,
                db=KUSTO_DATABASE,
                csl=query,
            )

            results = await client.list_kusto_results_async(input=query_request)

            if results and 'value' in results:
                print("Top 5 states by event count:")
                for row in results['value']:
                    state = row.get('State', 'Unknown')
                    count = row.get('EventCount', 0)
                    print(f"  {state}: {count} events")
            else:
                print("Query returned no results.")

        except ConnectorException as ex:
            print(f"Connector error: {ex}")
        except Exception as ex:
            print(f"Error: {ex}")


async def example_3_time_based_filtering():
    """Example 3: Query with time-based filtering."""
    print("\n=== Example 3: Time-Based Filtering ===")

    credential = DefaultAzureCredential()

    async with KustoClient(CONNECTION_RUNTIME_URL, credential) as client:
        try:
            query = f"""
                {KUSTO_TABLE}
                | where StartTime > ago(365d)
                | summarize count() by EventType
                | order by count_ desc
                | take 5
            """

            query_request = QueryAndListSchema(
                cluster=KUSTO_CLUSTER_URL,
                db=KUSTO_DATABASE,
                csl=query,
            )

            results = await client.list_kusto_results_async(input=query_request)

            if results and 'value' in results:
                print("Top 5 event types in the last year:")
                for row in results['value']:
                    event_type = row.get('EventType', 'Unknown')
                    count = row.get('count_', 0)
                    print(f"  {event_type}: {count} events")
            else:
                print("Query returned no results.")

        except ConnectorException as ex:
            print(f"Connector error: {ex}")
        except Exception as ex:
            print(f"Error: {ex}")


async def example_4_visualize_results():
    """Example 4: Query and visualize results as a chart."""
    print("\n=== Example 4: Visualize Query Results ===")

    credential = DefaultAzureCredential()

    async with KustoClient(CONNECTION_RUNTIME_URL, credential) as client:
        try:
            query = f"""
                {KUSTO_TABLE}
                | summarize EventCount = count() by bin(StartTime, 30d)
                | order by StartTime asc
            """

            visualize_request = QueryAndVisualizeSchema(
                cluster=KUSTO_CLUSTER_URL,
                db=KUSTO_DATABASE,
                csl=query,
                chart_type="Time Chart",
            )

            chart = await client.run_kusto_query_and_visualize_results_async(
                input=visualize_request
            )

            if chart:
                print("Chart data generated successfully")
                if isinstance(chart, dict):
                    if 'value' in chart:
                        print(f"  Data points: {len(chart['value'])}")
                    print("  Chart type: timechart")
                else:
                    print("  Chart object returned")
            else:
                print("Visualization completed but no chart data returned.")

        except ConnectorException as ex:
            print(f"Connector error: {ex}")
        except Exception as ex:
            print(f"Error: {ex}")


async def example_5_control_command():
    """Example 5: Run a control command to show database schema."""
    print("\n=== Example 5: Control Command (Show Tables) ===")

    credential = DefaultAzureCredential()

    async with KustoClient(CONNECTION_RUNTIME_URL, credential) as client:
        try:
            command = ".show tables"

            command_request = ControlCommandAndListSchema(
                cluster=KUSTO_CLUSTER_URL,
                db=KUSTO_DATABASE,
                csl=command,
            )

            results = await client.list_kusto_show_command_results_async(
                input=command_request
            )

            if results and 'value' in results:
                print(f"Found {len(results['value'])} tables in database '{KUSTO_DATABASE}':")
                for row in results['value'][:10]:
                    table_name = row.get('TableName', 'Unknown')
                    folder = row.get('Folder', '')
                    print(f"  - {table_name}" + (f" (Folder: {folder})" if folder else ""))
            else:
                print("Command executed but returned no results.")

        except ConnectorException as ex:
            print(f"Connector error: {ex}")
        except Exception as ex:
            print(f"Error: {ex}")


async def example_6_table_schema():
    """Example 6: Get schema information for a specific table."""
    print("\n=== Example 6: Show Table Schema ===")

    credential = DefaultAzureCredential()

    async with KustoClient(CONNECTION_RUNTIME_URL, credential) as client:
        try:
            command = f".show table {KUSTO_TABLE} schema as json"

            command_request = ControlCommandAndListSchema(
                cluster=KUSTO_CLUSTER_URL,
                db=KUSTO_DATABASE,
                csl=command,
            )

            results = await client.list_kusto_show_command_results_async(
                input=command_request
            )

            if results and 'value' in results and len(results['value']) > 0:
                print(f"Schema for table '{KUSTO_TABLE}':")
                schema_row = results['value'][0]
                if 'Schema' in schema_row:
                    import json
                    schema_json = json.loads(schema_row['Schema'])
                    if 'OrderedColumns' in schema_json:
                        for col in schema_json['OrderedColumns'][:10]:
                            col_name = col.get('Name', 'Unknown')
                            col_type = col.get('Type', 'Unknown')
                            print(f"  - {col_name}: {col_type}")
                else:
                    print(f"  Schema data: {schema_row}")
            else:
                print("Command executed but returned no schema.")

        except ConnectorException as ex:
            print(f"Connector error: {ex}")
        except Exception as ex:
            print(f"Error: {ex}")


async def example_7_statistical_analysis():
    """Example 7: Statistical analysis with percentiles."""
    print("\n=== Example 7: Statistical Analysis ===")

    credential = DefaultAzureCredential()

    async with KustoClient(CONNECTION_RUNTIME_URL, credential) as client:
        try:
            query = f"""
                {KUSTO_TABLE}
                | where isnotnull(DamageProperty)
                | summarize
                    p50 = percentile(DamageProperty, 50),
                    p95 = percentile(DamageProperty, 95),
                    p99 = percentile(DamageProperty, 99),
                    max = max(DamageProperty)
            """

            query_request = QueryAndListSchema(
                cluster=KUSTO_CLUSTER_URL,
                db=KUSTO_DATABASE,
                csl=query,
            )

            results = await client.list_kusto_results_async(input=query_request)

            if results and 'value' in results and len(results['value']) > 0:
                stats = results['value'][0]
                print("Property damage statistics:")
                print(f"  50th percentile (median): ${stats.get('p50', 0):,.2f}")
                print(f"  95th percentile: ${stats.get('p95', 0):,.2f}")
                print(f"  99th percentile: ${stats.get('p99', 0):,.2f}")
                print(f"  Maximum: ${stats.get('max', 0):,.2f}")
            else:
                print("Query returned no statistics.")

        except ConnectorException as ex:
            print(f"Connector error: {ex}")
        except Exception as ex:
            print(f"Error: {ex}")


async def example_8_error_handling():
    """Example 8: Demonstrate error handling with invalid query."""
    print("\n=== Example 8: Error Handling ===")

    credential = DefaultAzureCredential()

    async with KustoClient(CONNECTION_RUNTIME_URL, credential) as client:
        try:
            # Intentionally use an invalid table name
            query = "NonExistentTable | take 10"

            query_request = QueryAndListSchema(
                cluster=KUSTO_CLUSTER_URL,
                db=KUSTO_DATABASE,
                csl=query,
            )

            results = await client.list_kusto_results_async(input=query_request)
            print(f"Unexpected success: {results}")

        except ConnectorException as ex:
            print("Expected error caught:")
            print(f"  Message: {ex}")
        except Exception as ex:
            print(f"Unexpected error type: {type(ex).__name__}")
            print(f"  Message: {ex}")


async def main():
    """Run all examples."""
    print("Kusto (Azure Data Explorer) Connector SDK - Sample Usage")
    print("=" * 60)
    print()

    await example_1_simple_kql_query()
    await example_2_aggregation_query()
    await example_3_time_based_filtering()
    await example_4_visualize_results()
    await example_5_control_command()
    await example_6_table_schema()
    await example_7_statistical_analysis()
    await example_8_error_handling()

    print("\n" + "=" * 60)
    print("Sample completed!")


if __name__ == "__main__":
    asyncio.run(main())
