# Copyright (c) Microsoft Corporation. All rights reserved.

"""
Word Online (Business) Connector SDK Sample

This sample demonstrates how to use the Word Online (Business) connector SDK.

Prerequisites:
1. Azure subscription with Word Online (Business) connection
2. Word Online (Business) connection in Connector Namespaces
3. Connection runtime URL from Azure Portal

Installation:
    pip install azure-connectors

Usage:
    Set environment variable:
    $env:WORDONLINEBUSINESS_CONNECTION_URL = `
        "https://[region].azure-apihub.net/apim/wordonlinebusiness/[connection-id]"

    python sample_connector_usage_wordonlinebusiness.py
"""

import asyncio
import os
from azure.identity.aio import DefaultAzureCredential
from azure.connectors import ConnectorException
from azure.connectors.wordonlinebusiness import (
    WordonlinebusinessClient,
    CreateFileItemInput,
    ContentBody,
)

# Connection runtime URL format:
# https://[region].azure-apihub.net/apim/wordonlinebusiness/[connection-id]
CONNECTION_RUNTIME_URL = os.environ.get(
    "WORDONLINEBUSINESS_CONNECTION_URL",
    ""
)
SOURCE = os.environ.get("WORDONLINEBUSINESS_SOURCE", "me")
DRIVE = os.environ.get("WORDONLINEBUSINESS_DRIVE", "")
FILE = os.environ.get("WORDONLINEBUSINESS_FILE", "")


async def example_1_populate_word_template():
    """Example 1: Populate a Microsoft Word template.

    Reads a Microsoft Word template and fills template fields with dynamic values
    to generate a Word Document.
    """
    print("\n=== Example 1: Populate Word Template ===")

    credential = DefaultAzureCredential()

    async with WordonlinebusinessClient(CONNECTION_RUNTIME_URL, credential) as client:
        try:
            # Create input with template field values
            # The additional_properties dict contains the template field mappings
            input_data = CreateFileItemInput(
                additional_properties={
                    "templateId": "your-template-id",
                    "field_Name": "John Doe",
                    "field_Date": "2024-01-15",
                    "field_Company": "Contoso Ltd.",
                }
            )

            result = await client.create_file_item_async(
                input=input_data,
                source=SOURCE,
                drive=DRIVE,
                file=FILE
            )

            print(f"Generated document size: {len(result)} bytes")

        except ConnectorException as ex:
            print(f"Connector error: {ex}")
        except Exception as ex:
            print(f"Error: {ex}")


async def example_2_create_word_document():
    """Example 2: Create a Word document with content.

    Creates a new Microsoft Word file with the given content.
    """
    print("\n=== Example 2: Create Word Document ===")

    credential = DefaultAzureCredential()

    async with WordonlinebusinessClient(CONNECTION_RUNTIME_URL, credential) as client:
        try:
            # Create document content
            content = ContentBody(
                content="This is the content of my Word document.\n\n"
                        "It can include multiple paragraphs and formatting."
            )

            result = await client.create_word_file_with_content_async(
                input=content,
                file_name="MyDocument.docx"
            )

            if result:
                print(f"Document created with ID: {result.get('id', 'N/A')}")
                print(f"Document name: {result.get('name', 'N/A')}")
            else:
                print("Document created successfully")

        except ConnectorException as ex:
            print(f"Connector error: {ex}")
        except Exception as ex:
            print(f"Error: {ex}")


async def example_3_create_word_document_without_filename():
    """Example 3: Create a Word document without specifying filename.

    Creates a new Microsoft Word file with auto-generated filename.
    """
    print("\n=== Example 3: Create Word Document (Auto-named) ===")

    credential = DefaultAzureCredential()

    async with WordonlinebusinessClient(CONNECTION_RUNTIME_URL, credential) as client:
        try:
            content = ContentBody(content="Auto-generated document content.")

            result = await client.create_word_file_with_content_async(input=content)

            if result:
                print(f"Document created: {result}")
            else:
                print("Document created successfully")

        except ConnectorException as ex:
            print(f"Connector error: {ex}")
        except Exception as ex:
            print(f"Error: {ex}")


async def example_4_convert_word_to_pdf():
    """Example 4: Convert a Word document to PDF.

    Gets a PDF version of a selected Word file.
    """
    print("\n=== Example 4: Convert Word to PDF ===")

    credential = DefaultAzureCredential()

    async with WordonlinebusinessClient(CONNECTION_RUNTIME_URL, credential) as client:
        try:
            result = await client.get_file_pdf_async(
                source=SOURCE,
                drive=DRIVE,
                file=FILE
            )

            print(f"PDF generated, size: {len(result)} bytes")

        except ConnectorException as ex:
            print(f"Connector error: {ex}")
        except Exception as ex:
            print(f"Error: {ex}")


async def example_5_convert_with_sensitivity_labels():
    """Example 5: Convert Word to PDF with sensitivity label extraction.

    Converts a Word document to PDF while extracting sensitivity label metadata.
    """
    print("\n=== Example 5: Convert with Sensitivity Labels ===")

    credential = DefaultAzureCredential()

    async with WordonlinebusinessClient(CONNECTION_RUNTIME_URL, credential) as client:
        try:
            result = await client.get_file_pdf_async(
                source=SOURCE,
                drive=DRIVE,
                file=FILE,
                extract_sensitivity_label=True,
                fetch_sensitivity_label_metadata=True
            )

            print(f"PDF generated with sensitivity labels, size: {len(result)} bytes")

        except ConnectorException as ex:
            print(f"Connector error: {ex}")
        except Exception as ex:
            print(f"Error: {ex}")


async def main():
    """Run all examples."""
    if not CONNECTION_RUNTIME_URL:
        print("Error: WORDONLINEBUSINESS_CONNECTION_URL environment variable not set.")
        print("Set it to your connection runtime URL from Azure Portal.")
        return

    if not DRIVE or not FILE:
        print("Error: WORDONLINEBUSINESS_DRIVE and WORDONLINEBUSINESS_FILE must be set.")
        return

    print(f"Using connection URL: {CONNECTION_RUNTIME_URL[:50]}...")

    await example_1_populate_word_template()
    await example_2_create_word_document()
    await example_3_create_word_document_without_filename()
    await example_4_convert_word_to_pdf()
    await example_5_convert_with_sensitivity_labels()

    print("\n=== All examples completed ===")


if __name__ == "__main__":
    asyncio.run(main())
