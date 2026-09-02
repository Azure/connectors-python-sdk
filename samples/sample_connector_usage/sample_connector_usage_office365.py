# Copyright (c) Microsoft Corporation. All rights reserved.

"""
Office365 Connector SDK Sample

This sample demonstrates how to use the Office365 connector SDK.

Prerequisites:
1. Azure subscription with Office365 connection
2. Office365 connection in Connector Namespaces
3. Connection runtime URL from Azure Portal

Installation:
    pip install azure-connectors

Usage:
    Set environment variable:
    $env:OFFICE365_CONNECTION_URL = (
        "https://[region].azure-apihub.net/apim/office365/[connection-id]"
    )

    python sample_connector_usage_office365.py
"""

import asyncio
import os
from azure.identity.aio import DefaultAzureCredential
from azure.connectors import ConnectorException
from azure.connectors.office365 import (
    DraftEmailInput,
    Office365Client,
    SendEmailInput,
)

# Connection runtime URL format:
# https://[region].azure-apihub.net/apim/office365/[connection-id]
CONNECTION_RUNTIME_URL = os.environ.get(
    "OFFICE365_CONNECTION_URL",
    ""
)


async def example_1_get_outlook_categories():
    """Example 1: Get Outlook category names."""
    print("\n=== Example 1: Get Outlook Category Names ===")

    credential = DefaultAzureCredential()

    async with Office365Client(CONNECTION_RUNTIME_URL, credential) as client:
        try:
            categories = await client.get_outlook_category_names_async()

            if categories and 'value' in categories:
                print(f"Found {len(categories['value'])} Outlook categories:")
                for category in categories['value'][:5]:
                    display_name = category.get('DisplayName', 'Unknown')
                    color = category.get('Color', 'N/A')
                    print(f"  - {display_name} (Color: {color})")
            else:
                print("No categories found or unexpected response format.")

        except ConnectorException as ex:
            print(f"Connector error: {ex}")
        except Exception as ex:
            print(f"Error: {ex}")


async def example_2_send_email():
    """Example 2: Send an HTML email."""
    print("\n=== Example 2: Send Email ===")

    to_address = os.environ.get("TEST_EMAIL_TO", "<YOUR-EMAIL>@microsoft.com")

    credential = DefaultAzureCredential()

    async with Office365Client(CONNECTION_RUNTIME_URL, credential) as client:
        try:
            email = SendEmailInput(
                to=to_address,
                subject="Test Email from Office365 Connector SDK",
                body=(
                    "<p>This is a test email sent from the "
                    "<strong>Python Office365 Connector SDK</strong>.</p>"
                ),
            )

            await client.send_email_async(email)
            print(f"Email sent successfully to {to_address}")
            print("Note: Set TEST_EMAIL_TO environment variable to send to a real address")

        except ConnectorException as ex:
            print(f"Connector error: {ex}")
        except Exception as ex:
            print(f"Error: {ex}")


async def example_3_get_emails():
    """Example 3: Get emails from inbox."""
    print("\n=== Example 3: Get Emails from Inbox ===")

    credential = DefaultAzureCredential()

    async with Office365Client(CONNECTION_RUNTIME_URL, credential) as client:
        try:
            emails = await client.get_emails_async()

            if emails and 'value' in emails:
                print(f"Found {len(emails['value'])} emails:")
                for email in emails['value']:
                    subject = email.get('Subject', 'No Subject')
                    from_addr = email.get('From', 'Unknown')
                    received = email.get('DateTimeReceived', 'Unknown')
                    print(f"  - {subject}")
                    print(f"    From: {from_addr}")
                    print(f"    Received: {received}")
            else:
                print("No emails found or unexpected response format.")

        except ConnectorException as ex:
            print(f"Connector error: {ex}")
        except Exception as ex:
            print(f"Error: {ex}")


async def example_4_draft_and_send_email():
    """Example 4: Draft an email and then send it."""
    print("\n=== Example 4: Draft and Send Email ===")

    to_address = os.environ.get("TEST_EMAIL_TO", "<YOUR-EMAIL>@microsoft.com")

    credential = DefaultAzureCredential()

    async with Office365Client(CONNECTION_RUNTIME_URL, credential) as client:
        try:
            draft = DraftEmailInput(
                to=to_address,
                subject="Draft Email from SDK",
                body="<p>This email was created as a draft first.</p>",
            )

            draft_response = await client.draft_email_async(draft)
            print("Draft created successfully")

            if draft_response and 'Id' in draft_response:
                message_id = draft_response['Id']
                print(f"Draft message ID: {message_id}")

                await client.send_draft_email_async(message_id=message_id)
                print(f"Draft email sent successfully to {to_address}")
            else:
                print("Draft created but no ID returned.")

        except ConnectorException as ex:
            print(f"Connector error: {ex}")
        except Exception as ex:
            print(f"Error: {ex}")


async def example_5_error_handling():
    """Example 5: Demonstrate error handling."""
    print("\n=== Example 5: Error Handling ===")

    credential = DefaultAzureCredential()

    async with Office365Client(CONNECTION_RUNTIME_URL, credential) as client:
        try:
            # Attempt to get an email with an invalid ID
            invalid_message_id = "invalid-message-id-12345"
            email = await client.get_email_async(message_id=invalid_message_id)
            print(f"Unexpected success: {email}")

        except ConnectorException as ex:
            print("Expected error caught:")
            print(f"  Message: {ex}")
        except Exception as ex:
            print(f"Unexpected error type: {type(ex).__name__}")
            print(f"  Message: {ex}")


async def main():
    """Run all examples."""
    print("Office365 Connector SDK - Sample Usage")
    print("=" * 50)
    print()

    await example_1_get_outlook_categories()
    await example_2_send_email()
    await example_3_get_emails()
    await example_4_draft_and_send_email()
    await example_5_error_handling()

    print("\n" + "=" * 50)
    print("Sample completed!")


if __name__ == "__main__":
    asyncio.run(main())
