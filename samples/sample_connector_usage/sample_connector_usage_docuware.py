# Copyright (c) Microsoft Corporation. All rights reserved.

"""
DocuWare Connector SDK Sample

This sample demonstrates how to use the DocuWare connector SDK.

Prerequisites:
1. Azure subscription with a DocuWare connection
2. DocuWare connection in Connector Namespaces
3. Connection runtime URL from Azure Portal

Installation:
    pip install azure-connectors

Usage:
    Set environment variable:
    $env:DOCUWARE_CONNECTION_URL =
        "https://[region].azure-apihub.net/apim/docuware/[connection-id]"

    python sample_connector_usage_docuware.py
"""

import asyncio
import os

from azure.identity.aio import DefaultAzureCredential

from azure.connectors import ConnectorException
from azure.connectors.docuware import (
    DocuwareClient,
    SearchForDocumentsInFileCabinetInput,
)

# Connection runtime URL format:
# https://[region].azure-apihub.net/apim/docuware/[connection-id]
CONNECTION_RUNTIME_URL = os.environ.get("DOCUWARE_CONNECTION_URL", "")


async def example_1_get_file_cabinets():
    """Example 1: List available file cabinets and document trays."""
    print("\n=== Example 1: Get file cabinets ===")

    credential = DefaultAzureCredential()

    async with DocuwareClient(CONNECTION_RUNTIME_URL, credential) as client:
        try:
            result = await client.get_file_cabinets_async(
                file_cabinet_type=None,
            )

            print(f"File cabinets result: {result}")

        except ConnectorException as ex:
            print(f"Connector error: {ex}")
        except Exception as ex:
            print(f"Error: {ex}")


async def example_2_search_documents():
    """Example 2: Search a file cabinet for matching documents."""
    print("\n=== Example 2: Search documents in file cabinet ===")

    credential = DefaultAzureCredential()

    async with DocuwareClient(CONNECTION_RUNTIME_URL, credential) as client:
        try:
            request = SearchForDocumentsInFileCabinetInput()

            result = await client.search_for_documents_in_file_cabinet_async(
                input=request,
                file_cabinet="<file-cabinet-id>",
                search_dialog_id=None,
            )

            print(f"Search result: {result}")

        except ConnectorException as ex:
            print(f"Connector error: {ex}")
        except Exception as ex:
            print(f"Error: {ex}")


async def main():
    """Run all examples."""
    if not CONNECTION_RUNTIME_URL:
        print("Error: DOCUWARE_CONNECTION_URL environment variable not set.")
        print("Set it to your connection runtime URL from Azure Portal.")
        return

    print(f"Using connection URL: {CONNECTION_RUNTIME_URL[:50]}...")

    await example_1_get_file_cabinets()
    await example_2_search_documents()

    print("\n=== All examples completed ===")


if __name__ == "__main__":
    asyncio.run(main())
