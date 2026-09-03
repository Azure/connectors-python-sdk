# Copyright (c) Microsoft Corporation. All rights reserved.

"""
Azure Cosmos DB (DocumentDB) Connector SDK Sample

This sample demonstrates how to use the Azure Cosmos DB connector SDK
to query documents in Cosmos DB containers.

Note: The connector name "documentdb" reflects the original Azure DocumentDB
branding; it connects to Azure Cosmos DB accounts.

Prerequisites:
1. Azure subscription with Azure Cosmos DB connection
2. DocumentDB connection in Connector Namespaces (with access configured)
3. Connection runtime URL from Azure Portal
4. Azure Cosmos DB account with a database and container

Installation:
    pip install azure-connectors

Usage:
    Set environment variables:
    $env:DOCUMENTDB_CONNECTION_URL = "https://...apihub.net/apim/documentdb/..."
    $env:DOCUMENTDB_ACCOUNT = "<cosmos-db-account-name>"
    $env:DOCUMENTDB_DATABASE = "<database-id>"
    $env:DOCUMENTDB_CONTAINER = "<container-id>"

    python sample_connector_usage_documentdb.py
"""

import asyncio
import os
from azure.identity.aio import DefaultAzureCredential
from azure.connectors import ConnectorException
from azure.connectors.documentdb import DocumentdbClient

# Connection runtime URL format:
# https://[region].azure-apihub.net/apim/documentdb/[connection-id]
CONNECTION_RUNTIME_URL = os.environ.get(
    "DOCUMENTDB_CONNECTION_URL",
    ""
)

# Cosmos DB account name
COSMOS_DB_ACCOUNT = os.environ.get("DOCUMENTDB_ACCOUNT", "")

# Database ID
DATABASE_ID = os.environ.get("DOCUMENTDB_DATABASE", "")

# Container ID
CONTAINER_ID = os.environ.get("DOCUMENTDB_CONTAINER", "")


async def example_1_query_all_documents():
    """Example 1: Query all documents in a container."""
    print("\n=== Example 1: Query All Documents ===")

    if not COSMOS_DB_ACCOUNT or not DATABASE_ID or not CONTAINER_ID:
        print("Set environment variables to query documents:")
        print("  $env:DOCUMENTDB_ACCOUNT = '<cosmos-db-account-name>'")
        print("  $env:DOCUMENTDB_DATABASE = '<database-id>'")
        print("  $env:DOCUMENTDB_CONTAINER = '<container-id>'")
        return

    credential = DefaultAzureCredential()

    async with DocumentdbClient(CONNECTION_RUNTIME_URL, credential) as client:
        try:
            result = await client.query_documents_async(
                cosmos_db_account_name=COSMOS_DB_ACCOUNT,
                database_id=DATABASE_ID,
                container_id=CONTAINER_ID,
                query_text="SELECT * FROM c"
            )

            if result:
                documents = result.get("value", [])
                count = result.get("count", len(documents))
                print(f"Found {count} document(s) in container '{CONTAINER_ID}':")
                for i, doc in enumerate(documents[:3], 1):  # Show first 3
                    doc_id = doc.get("id", "N/A")
                    print(f"  {i}. id: {doc_id}")
                if count > 3:
                    print(f"  ... and {count - 3} more documents")
            else:
                print("No documents found or empty response.")

        except ConnectorException as ex:
            print(f"Connector error (status {ex.status_code}): {ex}")
        except Exception as ex:
            print(f"Error: {ex}")


async def example_2_query_with_filter():
    """Example 2: Query documents with a filter condition."""
    print("\n=== Example 2: Query with Filter ===")

    if not COSMOS_DB_ACCOUNT or not DATABASE_ID or not CONTAINER_ID:
        print("Set environment variables to query documents.")
        return

    credential = DefaultAzureCredential()

    async with DocumentdbClient(CONNECTION_RUNTIME_URL, credential) as client:
        try:
            # Query with WHERE clause - adjust field names for your schema
            result = await client.query_documents_async(
                cosmos_db_account_name=COSMOS_DB_ACCOUNT,
                database_id=DATABASE_ID,
                container_id=CONTAINER_ID,
                query_text="SELECT * FROM c WHERE c.type = 'sample'"
            )

            if result:
                documents = result.get("value", [])
                count = result.get("count", len(documents))
                print(f"Found {count} document(s) matching filter:")
                for doc in documents[:5]:
                    doc_id = doc.get("id", "N/A")
                    doc_type = doc.get("type", "N/A")
                    print(f"  - id: {doc_id}, type: {doc_type}")
            else:
                print("No matching documents found.")

        except ConnectorException as ex:
            print(f"Connector error (status {ex.status_code}): {ex}")
        except Exception as ex:
            print(f"Error: {ex}")


async def example_3_query_with_pagination():
    """Example 3: Query documents with pagination."""
    print("\n=== Example 3: Query with Pagination ===")

    if not COSMOS_DB_ACCOUNT or not DATABASE_ID or not CONTAINER_ID:
        print("Set environment variables to query documents.")
        return

    credential = DefaultAzureCredential()

    async with DocumentdbClient(CONNECTION_RUNTIME_URL, credential) as client:
        try:
            # First page - limit to 2 items
            result = await client.query_documents_async(
                cosmos_db_account_name=COSMOS_DB_ACCOUNT,
                database_id=DATABASE_ID,
                container_id=CONTAINER_ID,
                query_text="SELECT c.id, c.type FROM c",
                max_item_count=2
            )

            if result:
                documents = result.get("value", [])
                continuation = result.get("continuation_token")
                request_charge = result.get("request_charge", 0)

                print(f"Page 1: Retrieved {len(documents)} document(s)")
                print(f"  Request charge: {request_charge} RUs")
                for doc in documents:
                    print(f"  - id: {doc.get('id', 'N/A')}")

                if continuation:
                    print(f"  Continuation token available (truncated): {continuation[:30]}...")
                    print("  Use continuation_token parameter to fetch next page.")
                else:
                    print("  No more pages available.")
            else:
                print("No documents found.")

        except ConnectorException as ex:
            print(f"Connector error (status {ex.status_code}): {ex}")
        except Exception as ex:
            print(f"Error: {ex}")


async def example_4_query_with_partition_key():
    """Example 4: Query documents with a specific partition key."""
    print("\n=== Example 4: Query with Partition Key ===")

    partition_key = os.environ.get("DOCUMENTDB_PARTITION_KEY", "")
    if not COSMOS_DB_ACCOUNT or not DATABASE_ID or not CONTAINER_ID:
        print("Set environment variables to query documents.")
        return

    if not partition_key:
        print("Set DOCUMENTDB_PARTITION_KEY environment variable for this example.")
        print("Example: $env:DOCUMENTDB_PARTITION_KEY = 'myPartitionValue'")
        print("Skipping partition key example...")
        return

    credential = DefaultAzureCredential()

    async with DocumentdbClient(CONNECTION_RUNTIME_URL, credential) as client:
        try:
            # Query within a specific partition
            result = await client.query_documents_async(
                cosmos_db_account_name=COSMOS_DB_ACCOUNT,
                database_id=DATABASE_ID,
                container_id=CONTAINER_ID,
                query_text="SELECT * FROM c",
                partition_key=partition_key
            )

            if result:
                documents = result.get("value", [])
                print(f"Found {len(documents)} document(s) in partition '{partition_key}':")
                for doc in documents[:5]:
                    print(f"  - id: {doc.get('id', 'N/A')}")
            else:
                print(f"No documents found in partition '{partition_key}'.")

        except ConnectorException as ex:
            print(f"Connector error (status {ex.status_code}): {ex}")
        except Exception as ex:
            print(f"Error: {ex}")


async def example_5_query_with_consistency():
    """Example 5: Query documents with a specific consistency level."""
    print("\n=== Example 5: Query with Consistency Level ===")

    if not COSMOS_DB_ACCOUNT or not DATABASE_ID or not CONTAINER_ID:
        print("Set environment variables to query documents.")
        return

    credential = DefaultAzureCredential()

    async with DocumentdbClient(CONNECTION_RUNTIME_URL, credential) as client:
        try:
            # Query with Session consistency (common for read-your-writes)
            # Valid levels: Strong, BoundedStaleness, Session, Eventual
            result = await client.query_documents_async(
                cosmos_db_account_name=COSMOS_DB_ACCOUNT,
                database_id=DATABASE_ID,
                container_id=CONTAINER_ID,
                query_text="SELECT TOP 5 c.id FROM c ORDER BY c._ts DESC",
                consistency_level="Session"
            )

            if result:
                documents = result.get("value", [])
                session_token = result.get("session_token", "N/A")
                activity_id = result.get("activity_id", "N/A")

                print("Query completed with Session consistency:")
                print(f"  Documents retrieved: {len(documents)}")
                print(f"  Activity ID: {activity_id}")
                if session_token and session_token != "N/A":
                    token_preview = session_token[:30] if len(session_token) > 30 else session_token
                    print(f"  Session token: {token_preview}...")

                for doc in documents:
                    print(f"  - id: {doc.get('id', 'N/A')}")
            else:
                print("No documents found.")

        except ConnectorException as ex:
            print(f"Connector error (status {ex.status_code}): {ex}")
        except Exception as ex:
            print(f"Error: {ex}")


async def main():
    """Run all examples."""
    print("Azure Cosmos DB (DocumentDB) Connector SDK - Sample Usage")
    print("=" * 60)

    if not CONNECTION_RUNTIME_URL:
        print("\nWARNING: DOCUMENTDB_CONNECTION_URL environment variable not set.")
        print("Set it to your connection runtime URL to run actual API calls.")
        print("Format: https://[region].azure-apihub.net/apim/documentdb/[id]")
        return

    await example_1_query_all_documents()
    await example_2_query_with_filter()
    await example_3_query_with_pagination()
    await example_4_query_with_partition_key()
    await example_5_query_with_consistency()

    print("\n" + "=" * 60)
    print("Sample completed!")


if __name__ == "__main__":
    asyncio.run(main())
