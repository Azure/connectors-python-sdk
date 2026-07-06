"""
Microsoft Forms Connector SDK Sample

This sample demonstrates how to use the Microsoft Forms connector SDK.

Prerequisites:
1. Azure subscription with Microsoft Forms connection
2. Microsoft Forms connection in Connector Namespaces
3. Connection runtime URL from Azure Portal

Installation:
    pip install azure-connectors

Usage:
    Set environment variable:
    $env:MICROSOFTFORMS_CONNECTION_URL = "https://[region].azure-apihub.net/apim/microsoftforms/[connection-id]"

    python sample_connector_usage_microsoftforms.py
"""

import asyncio
import os

from azure.identity.aio import DefaultAzureCredential

from azure.connectors import ConnectorException
from azure.connectors.microsoftforms import MicrosoftformsClient


# Connection runtime URL format:
# https://[region].azure-apihub.net/apim/microsoftforms/[connection-id]
CONNECTION_RUNTIME_URL = os.environ.get("MICROSOFTFORMS_CONNECTION_URL", "")


async def example_1_list_forms() -> list[dict]:
    """Example 1: List available forms."""
    print("\n=== Example 1: List Forms ===")

    credential = DefaultAzureCredential()
    async with MicrosoftformsClient(CONNECTION_RUNTIME_URL, credential) as client:
        forms_response = await client.list_forms_async()
        forms = forms_response.get("value", []) if forms_response else []

        print(f"Found {len(forms)} forms")
        for form in forms[:5]:
            print(f"  - {form.get('title')} ({form.get('id')})")

        return forms


async def example_2_get_form_details(form_id: str) -> None:
    """Example 2: Get details for one form."""
    print("\n=== Example 2: Get Form Details ===")

    credential = DefaultAzureCredential()
    async with MicrosoftformsClient(CONNECTION_RUNTIME_URL, credential) as client:
        details = await client.get_form_details_by_id_async(form_id=form_id)

        if not details:
            print("No details returned")
            return

        print(f"Title: {details.get('title')}")
        print(f"Status: {details.get('status')}")
        print(f"Created: {details.get('createdDate')}")
        print(f"Last Modified: {details.get('modifiedDate')}")


async def example_3_get_questions(form_id: str) -> None:
    """Example 3: Get form questions."""
    print("\n=== Example 3: Get Questions ===")

    credential = DefaultAzureCredential()
    async with MicrosoftformsClient(CONNECTION_RUNTIME_URL, credential) as client:
        questions_response = await client.get_questions_async(form_id=form_id)
        questions = questions_response.get("value", []) if questions_response else []

        print(f"Found {len(questions)} questions")
        for question in questions[:10]:
            print(f"  - {question.get('title')} ({question.get('id')})")


async def main() -> None:
    """Run all examples."""
    if not CONNECTION_RUNTIME_URL:
        print("Error: MICROSOFTFORMS_CONNECTION_URL environment variable not set.")
        print("Set it to your connection runtime URL from Azure Portal.")
        return

    print("Microsoft Forms Connector SDK - Sample Usage")
    print("=" * 50)

    try:
        forms = await example_1_list_forms()

        if forms:
            first_form_id = forms[0].get("id")
            if first_form_id:
                await example_2_get_form_details(first_form_id)
                await example_3_get_questions(first_form_id)
            else:
                print("No form id found in first record; skipping detail examples.")
        else:
            print("No forms returned from the API.")

    except ConnectorException as ex:
        print(f"Connector error: {ex}")
    except Exception as ex:
        print(f"Unexpected error: {ex}")


if __name__ == "__main__":
    asyncio.run(main())
