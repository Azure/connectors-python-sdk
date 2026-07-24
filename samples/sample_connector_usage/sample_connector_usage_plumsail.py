# Copyright (c) Microsoft Corporation. All rights reserved.

"""
Plumsail Connector SDK Sample

This sample demonstrates how to use the Plumsail connector SDK.

Prerequisites:
1. Azure subscription with a Plumsail connection
2. Plumsail connection in Connector Namespaces
3. Connection runtime URL from Azure Portal

Installation:
    pip install azure-connectors

Usage:
    Set environment variable:
    $env:PLUMSAIL_CONNECTION_URL =
        "https://[region].azure-apihub.net/apim/plumsail/[connection-id]"

    python sample_connector_usage_plumsail.py
"""

import asyncio
import os

from azure.identity.aio import DefaultAzureCredential

from azure.connectors import ConnectorException
from azure.connectors.plumsail import (
    PlumsailClient,
    Pdf2TextRequest,
)

# Connection runtime URL format:
# https://[region].azure-apihub.net/apim/plumsail/[connection-id]
CONNECTION_RUNTIME_URL = os.environ.get("PLUMSAIL_CONNECTION_URL", "")


async def example_1_get_profile():
    """Example 1: Get the current account profile."""
    print("\n=== Example 1: Get current profile ===")

    credential = DefaultAzureCredential()

    async with PlumsailClient(CONNECTION_RUNTIME_URL, credential) as client:
        try:
            result = await client.profiles_me_get_async()

            print(f"Profile result: {result}")

        except ConnectorException as ex:
            print(f"Connector error: {ex}")
        except Exception as ex:
            print(f"Error: {ex}")


async def example_2_extract_text_from_pdf():
    """Example 2: Extract text content from a PDF document."""
    print("\n=== Example 2: Extract text from PDF ===")

    credential = DefaultAzureCredential()

    async with PlumsailClient(CONNECTION_RUNTIME_URL, credential) as client:
        try:
            request = Pdf2TextRequest(
                document_content="<base64-encoded-pdf-content>",
                result_type="Raw",
            )

            result = await client.flow_v1_documents_jobs_extract_text_from_pdf_async(
                input=request,
            )

            print(f"Extracted text result: {result}")

        except ConnectorException as ex:
            print(f"Connector error: {ex}")
        except Exception as ex:
            print(f"Error: {ex}")


async def main():
    """Run all examples."""
    if not CONNECTION_RUNTIME_URL:
        print("Error: PLUMSAIL_CONNECTION_URL environment variable not set.")
        print("Set it to your connection runtime URL from Azure Portal.")
        return

    print(f"Using connection URL: {CONNECTION_RUNTIME_URL[:50]}...")

    await example_1_get_profile()
    await example_2_extract_text_from_pdf()

    print("\n=== All examples completed ===")


if __name__ == "__main__":
    asyncio.run(main())
