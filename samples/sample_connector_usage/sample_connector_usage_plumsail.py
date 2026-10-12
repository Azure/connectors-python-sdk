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
import os

from azure.identity import DefaultAzureCredential

from azure.connectors import ConnectorException
from azure.connectors.plumsail import (
    PlumsailClient,
    Pdf2TextRequest,
)

# Connection runtime URL format:
# https://[region].azure-apihub.net/apim/plumsail/[connection-id]
CONNECTION_RUNTIME_URL = os.environ.get("PLUMSAIL_CONNECTION_URL", "")


def example_1_get_profile():
    """Example 1: Get the current account profile."""
    print("\n=== Example 1: Get current profile ===")

    with DefaultAzureCredential() as credential:

        with PlumsailClient(CONNECTION_RUNTIME_URL, credential) as client:
            try:
                result = client.profiles_me_get()

                print(f"Profile result: {result}")

            except ConnectorException as ex:
                print(f"Connector error: {ex}")
            except Exception as ex:
                print(f"Error: {ex}")


def example_2_extract_text_from_pdf():
    """Example 2: Extract text content from a PDF document."""
    print("\n=== Example 2: Extract text from PDF ===")

    with DefaultAzureCredential() as credential:

        with PlumsailClient(CONNECTION_RUNTIME_URL, credential) as client:
            try:
                request = Pdf2TextRequest(
                    document_content="<base64-encoded-pdf-content>",
                    result_type="Raw",
                )

                poller = client.begin_flow_v1_documents_jobs_extract_text_from_pdf(
                    input=request,
                )
                result = poller.result()

                print(f"Extracted text result: {result}")

            except ConnectorException as ex:
                print(f"Connector error: {ex}")
            except Exception as ex:
                print(f"Error: {ex}")


def main():
    """Run all examples."""
    if not CONNECTION_RUNTIME_URL:
        print("Error: PLUMSAIL_CONNECTION_URL environment variable not set.")
        print("Set it to your connection runtime URL from Azure Portal.")
        return

    print(f"Using connection URL: {CONNECTION_RUNTIME_URL[:50]}...")

    example_1_get_profile()
    example_2_extract_text_from_pdf()

    print("\n=== All examples completed ===")


if __name__ == "__main__":
    main()
