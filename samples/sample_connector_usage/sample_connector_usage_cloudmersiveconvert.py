# Copyright (c) Microsoft Corporation. All rights reserved.

"""
Cloudmersive Convert Connector SDK Sample

This sample demonstrates how to use the Cloudmersive Convert connector SDK.

Prerequisites:
1. Azure subscription with a Cloudmersive Convert connection
2. Cloudmersive Convert connection in Connector Namespaces
3. Connection runtime URL from Azure Portal

Installation:
    pip install azure-connectors

Usage:
    Set environment variable:
    $env:CLOUDMERSIVECONVERT_CONNECTION_URL =
        "https://[region].azure-apihub.net/apim/cloudmersiveconvert/[connection-id]"

    python sample_connector_usage_cloudmersiveconvert.py
"""

import asyncio
import os

from azure.identity.aio import DefaultAzureCredential

from azure.connectors import ConnectorException
from azure.connectors.cloudmersiveconvert import (
    CloudmersiveconvertClient,
    GetDocxBodyRequest,
)

# Connection runtime URL format:
# https://[region].azure-apihub.net/apim/cloudmersiveconvert/[connection-id]
CONNECTION_RUNTIME_URL = os.environ.get("CLOUDMERSIVECONVERT_CONNECTION_URL", "")


async def example_1_autodetect_get_info():
    """Example 1: Auto-detect document type information."""
    print("\n=== Example 1: Auto-detect document info ===")

    credential = DefaultAzureCredential()

    async with CloudmersiveconvertClient(CONNECTION_RUNTIME_URL, credential) as client:
        try:
            result = await client.convert_document_autodetect_get_info_async()

            print(f"Document info result: {result}")

        except ConnectorException as ex:
            print(f"Connector error: {ex}")
        except Exception as ex:
            print(f"Error: {ex}")


async def example_2_get_docx_body():
    """Example 2: Get the body content from a Word DOCX document."""
    print("\n=== Example 2: Get DOCX body ===")

    credential = DefaultAzureCredential()

    async with CloudmersiveconvertClient(CONNECTION_RUNTIME_URL, credential) as client:
        try:
            request = GetDocxBodyRequest(
                input_file_url="https://example.com/document.docx",
            )

            result = await client.edit_document_docx_body_async(input=request)

            print(f"DOCX body result: {result}")

        except ConnectorException as ex:
            print(f"Connector error: {ex}")
        except Exception as ex:
            print(f"Error: {ex}")


async def main():
    """Run all examples."""
    if not CONNECTION_RUNTIME_URL:
        print("Error: CLOUDMERSIVECONVERT_CONNECTION_URL environment variable not set.")
        print("Set it to your connection runtime URL from Azure Portal.")
        return

    print(f"Using connection URL: {CONNECTION_RUNTIME_URL[:50]}...")

    await example_1_autodetect_get_info()
    await example_2_get_docx_body()

    print("\n=== All examples completed ===")


if __name__ == "__main__":
    asyncio.run(main())
