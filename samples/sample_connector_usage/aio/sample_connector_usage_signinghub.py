# Copyright (c) Microsoft Corporation. All rights reserved.

"""
SigningHub sample for the Azure Connectors Python SDK

This sample demonstrates how to use the SigningHub client from the Azure Connectors Python SDK.

Prerequisites:
1. Azure subscription with a SigningHub connection
2. SigningHub connection in Connector Namespaces
3. Connection runtime URL from Azure Portal

Installation:
    pip install azure-connectors

Usage:
    Set environment variable:
    $env:SIGNINGHUB_CONNECTION_URL =
        "https://[region].azure-apihub.net/apim/signinghub/[connection-id]"

    python sample_connector_usage_signinghub.py
"""

import asyncio
import os

from azure.identity.aio import DefaultAzureCredential

from azure.connectors import ConnectorException
from azure.connectors.aio.signinghub import SigninghubClient
from azure.connectors.signinghub import (
    CheckBoxFieldRequest,
    FieldDimension,
)

# Connection runtime URL format:
# https://[region].azure-apihub.net/apim/signinghub/[connection-id]
CONNECTION_RUNTIME_URL = os.environ.get("SIGNINGHUB_CONNECTION_URL", "")


async def example_1_get_contacts():
    """Example 1: Retrieve contacts for the current user."""
    print("\n=== Example 1: Get Contacts ===")

    async with DefaultAzureCredential() as credential:

        async with SigninghubClient(CONNECTION_RUNTIME_URL, credential) as client:
            try:
                items = [item async for item in client.list_contacts_get(
                    record_per_page=10,
                    page_no=1,
                )]

                print(f"Contacts result: {items}")

            except ConnectorException as ex:
                print(f"Connector error: {ex}")
            except Exception as ex:
                print(f"Error: {ex}")


async def example_2_add_check_box_field():
    """Example 2: Add a checkbox field to a document in a package."""
    print("\n=== Example 2: Add CheckBox Field ===")

    async with DefaultAzureCredential() as credential:

        async with SigninghubClient(CONNECTION_RUNTIME_URL, credential) as client:
            try:
                request = CheckBoxFieldRequest(
                    order=1,
                    page_no=1,
                    dimensions=FieldDimension(x=120.0, y=220.0, width=18.0, height=18.0),
                    field_name="Approve",
                    value="false",
                    validation_rule="none",
                )

                result = await client.checkbox_add_check_box(
                    input=request,
                    package_id=12345,
                    document_id=67890,
                )

                print(f"Add checkbox result: {result}")

            except ConnectorException as ex:
                print(f"Connector error: {ex}")
            except Exception as ex:
                print(f"Error: {ex}")


async def example_3_delete_attachment():
    """Example 3: Delete an attachment from a document."""
    print("\n=== Example 3: Delete Attachment ===")

    async with DefaultAzureCredential() as credential:

        async with SigninghubClient(CONNECTION_RUNTIME_URL, credential) as client:
            try:
                await client.attachment_delete_attachment(
                    package_id=12345,
                    document_id=67890,
                    attachment_id=13579,
                )

                print("Attachment deleted successfully")

            except ConnectorException as ex:
                print(f"Connector error: {ex}")
            except Exception as ex:
                print(f"Error: {ex}")


async def main():
    """Run all examples."""
    if not CONNECTION_RUNTIME_URL:
        print("Error: SIGNINGHUB_CONNECTION_URL environment variable not set.")
        print("Set it to your connection runtime URL from Azure Portal.")
        return

    print(f"Using connection URL: {CONNECTION_RUNTIME_URL[:50]}...")

    await example_1_get_contacts()
    await example_2_add_check_box_field()
    await example_3_delete_attachment()

    print("\n=== All examples completed ===")


if __name__ == "__main__":
    asyncio.run(main())
