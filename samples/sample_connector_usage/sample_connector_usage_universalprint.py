# Copyright (c) Microsoft Corporation. All rights reserved.

"""
Universal Print sample for the Azure Connectors Python SDK

This sample demonstrates how to use the Universal Print client from the Azure Connectors Python SDK.

Prerequisites:
1. Azure subscription with a Universal Print connection
2. Universal Print connection in Connector Namespaces
3. Connection runtime URL from Azure Portal

Installation:
    pip install azure-connectors

Usage:
    Set environment variable:
    $env:UNIVERSALPRINT_CONNECTION_URL = "<connection-runtime-url>"

    python sample_connector_usage_universalprint.py
"""
import os
from pathlib import Path

from azure.identity import DefaultAzureCredential
from azure.connectors import ConnectorException
from azure.connectors.universalprint import UniversalprintClient

# Connection runtime URL format:
# https://[region].azure-apihub.net/apim/universalprint/[connection-id]
CONNECTION_RUNTIME_URL = os.environ.get(
    "UNIVERSALPRINT_CONNECTION_URL",
    "",
)


def example_1_list_recent_shares():
    """Example 1: List recently used printer shares."""
    print("\n=== Example 1: List Recent Printer Shares ===")

    with DefaultAzureCredential() as credential:

        with UniversalprintClient(CONNECTION_RUNTIME_URL, credential) as client:
            try:
                result = client.list_recent_shares()

                shares = (result or {}).get("value", []) if isinstance(result, dict) else []
                print(f"Found {len(shares)} recent printer share(s).")
                for share in shares:
                    print(f"  - {share}")

            except ConnectorException as ex:
                print(f"Connector error: {ex}")
            except Exception as ex:
                print(f"Error: {ex}")


def example_2_print_file():
    """Example 2: Print a PDF to a printer share."""
    print("\n=== Example 2: Print File ===")

    with DefaultAzureCredential() as credential:
        pdf_file_path = Path(
            os.environ.get("UNIVERSALPRINT_PDF_PATH", "document.pdf")
        )

        with UniversalprintClient(CONNECTION_RUNTIME_URL, credential) as client:
            try:
                client.print_file(
                    input=pdf_file_path.read_bytes(),
                    printer="your-printer-share-id",
                    file_name=pdf_file_path.name,
                    configuration_copies=1,
                    configuration_color_mode="color",
                    configuration_orientation="portrait",
                )

                print("Print job submitted successfully.")

            except ConnectorException as ex:
                print(f"Connector error: {ex}")
            except Exception as ex:
                print(f"Error: {ex}")


def main():
    """Run all examples."""
    if not CONNECTION_RUNTIME_URL:
        print("Error: UNIVERSALPRINT_CONNECTION_URL environment variable not set.")
        print("Set it to your connection runtime URL from Azure Portal.")
        return

    print(f"Using connection URL: {CONNECTION_RUNTIME_URL[:50]}...")

    example_1_list_recent_shares()
    example_2_print_file()

    print("\n=== All examples completed ===")


if __name__ == "__main__":
    main()
