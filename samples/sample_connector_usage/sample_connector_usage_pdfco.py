# Copyright (c) Microsoft Corporation. All rights reserved.

"""
PDF.co Connector SDK Sample

This sample demonstrates how to use the PDF.co connector SDK.

Prerequisites:
1. Azure subscription with a PDF.co connection
2. PDF.co connection in Connector Namespaces
3. Connection runtime URL from Azure Portal

Installation:
    pip install azure-connectors

Usage:
    Set environment variable:
    $env:PDFCO_CONNECTION_URL =
        "https://[region].azure-apihub.net/apim/pdfco/[connection-id]"

    python sample_connector_usage_pdfco.py
"""

import asyncio
import os

from azure.identity.aio import DefaultAzureCredential

from azure.connectors import ConnectorException
from azure.connectors.pdfco import (
    PdfcoClient,
    HtmlToPdfInput,
    UrlToPdfInput,
)

# Connection runtime URL format:
# https://[region].azure-apihub.net/apim/pdfco/[connection-id]
CONNECTION_RUNTIME_URL = os.environ.get("PDFCO_CONNECTION_URL", "")


async def example_1_html_to_pdf():
    """Example 1: Convert an HTML snippet to a PDF."""
    print("\n=== Example 1: HTML to PDF ===")

    credential = DefaultAzureCredential()

    async with PdfcoClient(CONNECTION_RUNTIME_URL, credential) as client:
        try:
            request = HtmlToPdfInput(
                html="<h1>Hello from PDF.co</h1>",
            )

            result = await client.html_to_pdf_async(input=request)

            print(f"HTML to PDF result: {result}")

        except ConnectorException as ex:
            print(f"Connector error: {ex}")
        except Exception as ex:
            print(f"Error: {ex}")


async def example_2_url_to_pdf():
    """Example 2: Create a PDF from a public URL."""
    print("\n=== Example 2: URL to PDF ===")

    credential = DefaultAzureCredential()

    async with PdfcoClient(CONNECTION_RUNTIME_URL, credential) as client:
        try:
            request = UrlToPdfInput(
                url="https://example.com",
            )

            result = await client.url_to_pdf_async(input=request)

            print(f"URL to PDF result: {result}")

        except ConnectorException as ex:
            print(f"Connector error: {ex}")
        except Exception as ex:
            print(f"Error: {ex}")


async def main():
    """Run all examples."""
    if not CONNECTION_RUNTIME_URL:
        print("Error: PDFCO_CONNECTION_URL environment variable not set.")
        print("Set it to your connection runtime URL from Azure Portal.")
        return

    print(f"Using connection URL: {CONNECTION_RUNTIME_URL[:50]}...")

    await example_1_html_to_pdf()
    await example_2_url_to_pdf()

    print("\n=== All examples completed ===")


if __name__ == "__main__":
    asyncio.run(main())
