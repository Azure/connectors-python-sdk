# Copyright (c) Microsoft Corporation. All rights reserved.

"""
DocuWare sample for the Azure Connectors Python SDK

This sample demonstrates how to use the DocuWare client from the Azure Connectors Python SDK.

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
import os

from azure.identity import DefaultAzureCredential

from azure.connectors import ConnectorException
from azure.connectors.docuware import (
    DocuwareClient,
    SearchForDocumentsInFileCabinetInput,
)

# Connection runtime URL format:
# https://[region].azure-apihub.net/apim/docuware/[connection-id]
CONNECTION_RUNTIME_URL = os.environ.get("DOCUWARE_CONNECTION_URL", "")


def example_1_get_file_cabinets():
    """Example 1: List available file cabinets and document trays."""
    print("\n=== Example 1: Get file cabinets ===")

    with DefaultAzureCredential() as credential:

        with DocuwareClient(CONNECTION_RUNTIME_URL, credential) as client:
            try:
                result = client.get_file_cabinets(
                    file_cabinet_type="<file-cabinet-type>",
                )

                print(f"File cabinets result: {result}")

            except ConnectorException as ex:
                print(f"Connector error: {ex}")
            except Exception as ex:
                print(f"Error: {ex}")


def example_2_search_documents():
    """Example 2: Search a file cabinet for matching documents."""
    print("\n=== Example 2: Search documents in file cabinet ===")

    with DefaultAzureCredential() as credential:

        with DocuwareClient(CONNECTION_RUNTIME_URL, credential) as client:
            try:
                request = SearchForDocumentsInFileCabinetInput()

                result = client.search_for_documents_in_file_cabinet(
                    input=request,
                    file_cabinet="<file-cabinet-id>",
                    search_dialog_id="<search-dialog-id>",
                )

                print(f"Search result: {result}")

            except ConnectorException as ex:
                print(f"Connector error: {ex}")
            except Exception as ex:
                print(f"Error: {ex}")


def main():
    """Run all examples."""
    if not CONNECTION_RUNTIME_URL:
        print("Error: DOCUWARE_CONNECTION_URL environment variable not set.")
        print("Set it to your connection runtime URL from Azure Portal.")
        return

    print(f"Using connection URL: {CONNECTION_RUNTIME_URL[:50]}...")

    example_1_get_file_cabinets()
    example_2_search_documents()

    print("\n=== All examples completed ===")


if __name__ == "__main__":
    main()
