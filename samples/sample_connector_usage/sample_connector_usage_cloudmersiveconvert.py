# Copyright (c) Microsoft Corporation. All rights reserved.

"""
Cloudmersive Convert sample for the Azure Connectors Python SDK

This sample demonstrates how to use the Cloudmersive Convert client from the Azure Connectors Python SDK.

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
import os

from azure.identity import DefaultAzureCredential

from azure.connectors import ConnectorException
from azure.connectors.cloudmersiveconvert import (
    CloudmersiveconvertClient,
    GetDocxBodyRequest,
    ScreenshotRequest,
)

# Connection runtime URL format:
# https://[region].azure-apihub.net/apim/cloudmersiveconvert/[connection-id]
CONNECTION_RUNTIME_URL = os.environ.get("CLOUDMERSIVECONVERT_CONNECTION_URL", "")


def example_1_convert_url_to_pdf():
    """Example 1: Convert a web page URL to a PDF document."""
    print("\n=== Example 1: Convert URL to PDF ===")

    with DefaultAzureCredential() as credential:

        with CloudmersiveconvertClient(CONNECTION_RUNTIME_URL, credential) as client:
            try:
                request = ScreenshotRequest(
                    url="https://www.example.com",
                )

                result = client.convert_web_url_to_pdf(input=request)

                print(f"Converted PDF byte length: {len(result) if result else 0}")

            except ConnectorException as ex:
                print(f"Connector error: {ex}")
            except Exception as ex:
                print(f"Error: {ex}")


def example_2_get_docx_body():
    """Example 2: Get the body content from a Word DOCX document."""
    print("\n=== Example 2: Get DOCX body ===")

    with DefaultAzureCredential() as credential:

        with CloudmersiveconvertClient(CONNECTION_RUNTIME_URL, credential) as client:
            try:
                request = GetDocxBodyRequest(
                    input_file_url="https://example.com/document.docx",
                )

                result = client.edit_document_docx_body(input=request)

                print(f"DOCX body result: {result}")

            except ConnectorException as ex:
                print(f"Connector error: {ex}")
            except Exception as ex:
                print(f"Error: {ex}")


def main():
    """Run all examples."""
    if not CONNECTION_RUNTIME_URL:
        print("Error: CLOUDMERSIVECONVERT_CONNECTION_URL environment variable not set.")
        print("Set it to your connection runtime URL from Azure Portal.")
        return

    print(f"Using connection URL: {CONNECTION_RUNTIME_URL[:50]}...")

    example_1_convert_url_to_pdf()
    example_2_get_docx_body()

    print("\n=== All examples completed ===")


if __name__ == "__main__":
    main()
