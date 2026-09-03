# Copyright (c) Microsoft Corporation. All rights reserved.

"""
OneNote Connector SDK Sample

This sample demonstrates how to use the OneNote connector SDK
for notebook, section, and page operations.

Prerequisites:
1. Azure subscription with OneNote connection
2. OneNote connection in Connector Namespaces
3. Connection runtime URL from Azure Portal

Installation:
    pip install azure-connectors

Usage:
    Set environment variable:
    $env:ONENOTE_CONNECTION_URL = "<connection-url>"

    python sample_connector_usage_onenote.py
"""

import asyncio
import os
from azure.identity.aio import DefaultAzureCredential
from azure.connectors import ConnectorException
from azure.connectors.onenote import (
    OnenoteClient,
    CreateSectionRequest,
)

# Connection runtime URL format:
# https://[region].azure-apihub.net/apim/onenote/[connection-id]
CONNECTION_RUNTIME_URL = os.environ.get(
    "ONENOTE_CONNECTION_URL",
    ""
)


async def example_1_list_notebooks():
    """Example 1: List recent notebooks."""
    print("\n=== Example 1: List Notebooks ===")

    credential = DefaultAzureCredential()

    async with OnenoteClient(CONNECTION_RUNTIME_URL, credential) as client:
        try:
            result = await client.get_notebooks_async()

            if result and "value" in result:
                notebooks = result["value"]
                print(f"Found {len(notebooks)} notebooks:")
                for nb in notebooks[:5]:
                    print(f"  - {nb.get('fileName', 'N/A')} (key: {nb.get('key', 'N/A')})")
            else:
                print("No notebooks found.")

        except ConnectorException as ex:
            print(f"Connector error: {ex}")
        except Exception as ex:
            print(f"Error: {ex}")


async def example_2_list_sections():
    """Example 2: List sections in a notebook."""
    print("\n=== Example 2: List Sections ===")

    # Replace with your actual notebook key
    NOTEBOOK_KEY = "your-notebook-key-here"

    credential = DefaultAzureCredential()

    async with OnenoteClient(CONNECTION_RUNTIME_URL, credential) as client:
        try:
            result = await client.get_sections_in_notebook_async(
                notebook_key=NOTEBOOK_KEY
            )

            if result and "value" in result:
                sections = result["value"]
                print(f"Found {len(sections)} sections:")
                for section in sections[:5]:
                    print(f"  - {section.get('name', 'N/A')} (id: {section.get('id', 'N/A')})")
            else:
                print("No sections found.")

        except ConnectorException as ex:
            print(f"Connector error: {ex}")
        except Exception as ex:
            print(f"Error: {ex}")


async def example_3_get_pages_in_section():
    """Example 3: Get pages in a section."""
    print("\n=== Example 3: Get Pages ===")

    # Replace with your actual values
    NOTEBOOK_KEY = "your-notebook-key-here"
    SECTION_ID = "your-section-id-here"

    credential = DefaultAzureCredential()

    async with OnenoteClient(CONNECTION_RUNTIME_URL, credential) as client:
        try:
            result = await client.get_pages_in_section_async(
                notebook_key=NOTEBOOK_KEY,
                section_id=SECTION_ID
            )

            if result and "value" in result:
                pages = result["value"]
                print(f"Found {len(pages)} pages:")
                for page in pages[:5]:
                    print(f"  - {page.get('title', 'Untitled')} (id: {page.get('id', 'N/A')})")
            else:
                print("No pages found.")

        except ConnectorException as ex:
            print(f"Connector error: {ex}")
        except Exception as ex:
            print(f"Error: {ex}")


async def example_4_create_section():
    """Example 4: Create a new section in a notebook."""
    print("\n=== Example 4: Create Section ===")

    # Replace with your actual notebook key
    NOTEBOOK_KEY = "your-notebook-key-here"

    credential = DefaultAzureCredential()

    async with OnenoteClient(CONNECTION_RUNTIME_URL, credential) as client:
        try:
            section_request = CreateSectionRequest(name="SDK Test Section")

            result = await client.create_section_in_notebook_async(
                input=section_request,
                notebook_key=NOTEBOOK_KEY
            )

            if result:
                print("Section created successfully!")
                print(f"Section ID: {result.get('id')}")
                print(f"Section Name: {result.get('name')}")
            else:
                print("Section creation completed (no response body)")

        except ConnectorException as ex:
            print(f"Connector error: {ex}")
        except Exception as ex:
            print(f"Error: {ex}")


async def example_5_create_quick_note():
    """Example 5: Create a page in Quick Notes."""
    print("\n=== Example 5: Create Quick Note ===")

    credential = DefaultAzureCredential()

    async with OnenoteClient(CONNECTION_RUNTIME_URL, credential) as client:
        try:
            page_input = (
                "<html><head><title>Quick Note</title></head>"
                "<body><p>Created via Azure Connectors Python SDK</p></body></html>"
            )

            result = await client.create_page_in_quick_notes_async(input=page_input)

            if result:
                print("Quick note created successfully!")
                print(f"Page ID: {result.get('id')}")
                print(f"Title: {result.get('title')}")
            else:
                print("Quick note creation completed (no response body)")

        except ConnectorException as ex:
            print(f"Connector error: {ex}")
        except Exception as ex:
            print(f"Error: {ex}")


async def example_6_get_page_content():
    """Example 6: Get page content."""
    print("\n=== Example 6: Get Page Content ===")

    # Replace with your actual values
    NOTEBOOK_KEY = "your-notebook-key-here"
    SECTION_ID = "your-section-id-here"
    PAGE_ID = "your-page-id-here"

    credential = DefaultAzureCredential()

    async with OnenoteClient(CONNECTION_RUNTIME_URL, credential) as client:
        try:
            result = await client.get_page_content_async(
                notebook_key=NOTEBOOK_KEY,
                section_id=SECTION_ID,
                page_id=PAGE_ID,
            )

            if result:
                print("Page content retrieved successfully!")
                content = str(result)[:200]
                print(f"Content preview: {content}...")
            else:
                print("No content returned.")

        except ConnectorException as ex:
            print(f"Connector error: {ex}")
        except Exception as ex:
            print(f"Error: {ex}")


async def main():
    """Run all examples."""
    if not CONNECTION_RUNTIME_URL:
        print("Error: ONENOTE_CONNECTION_URL environment variable not set.")
        print("Set it to your connection runtime URL from Azure Portal.")
        return

    print(f"Using connection URL: {CONNECTION_RUNTIME_URL[:50]}...")

    await example_1_list_notebooks()

    # The following examples require valid IDs:
    # await example_2_list_sections()
    # await example_3_get_pages_in_section()
    # await example_4_create_section()
    # await example_5_create_quick_note()
    # await example_6_get_page_content()

    print("\n=== All examples completed ===")


if __name__ == "__main__":
    asyncio.run(main())
