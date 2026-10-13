"""
Mailchimp sample for the Azure Connectors Python SDK

This sample demonstrates how to use the Mailchimp client from the Azure Connectors Python SDK.

Prerequisites:
1. Azure subscription with a Mailchimp connection
2. Mailchimp connection in Connector Namespaces
3. Connection runtime URL from Azure Portal

Installation:
    pip install azure-connectors

Usage:
    Set environment variable:
    $env:MAILCHIMP_CONNECTION_URL = "https://[region].azure-apihub.net/apim/mailchimp/[id]"

    python sample_connector_usage_mailchimp.py
"""
import os

from azure.identity import DefaultAzureCredential

from azure.connectors import ConnectorException
from azure.connectors.mailchimp import (
    CampaignDefaults,
    Contact,
    MailchimpClient,
    NewListRequest,
    NewMemberInListRequest,
)


# Connection runtime URL format:
# https://[region].azure-apihub.net/apim/mailchimp/[connection-id]
CONNECTION_RUNTIME_URL = os.environ.get("MAILCHIMP_CONNECTION_URL", "")


def example_1_list_campaigns() -> None:
    """Example 1: List campaigns in the account."""
    print("\n=== Example 1: List Campaigns ===")

    with DefaultAzureCredential() as credential:
        with MailchimpClient(CONNECTION_RUNTIME_URL, credential) as client:
            campaigns = client.list_campaigns()
            print(f"Campaigns: {campaigns}")


def example_2_get_lists() -> None:
    """Example 2: Get all audience lists."""
    print("\n=== Example 2: Get Lists ===")

    with DefaultAzureCredential() as credential:
        with MailchimpClient(CONNECTION_RUNTIME_URL, credential) as client:
            lists = client.get_lists(count=10, offset=0)
            print(f"Lists: {lists}")


def example_3_new_list() -> None:
    """Example 3: Create a new audience list."""
    print("\n=== Example 3: New List ===")

    with DefaultAzureCredential() as credential:
        with MailchimpClient(CONNECTION_RUNTIME_URL, credential) as client:
            new_list = client.newlist(
                input=NewListRequest(
                    name="SDK sample list",
                    permission_reminder="You signed up via the SDK sample.",
                    contact=Contact(
                        company="Contoso",
                        address1="1 Microsoft Way",
                        city="Redmond",
                        state="WA",
                        zip="98052",
                        country="US",
                        phone="425-555-0100",
                    ),
                    campaign_defaults=CampaignDefaults(
                        from_name="SDK Sample",
                        from_email="sample@example.com",
                        subject="Welcome",
                        language="en",
                    ),
                    email_type_option=True,
                ),
            )
            print(f"Created list: {new_list}")


def example_4_add_member() -> None:
    """Example 4: Add a member to an audience list."""
    print("\n=== Example 4: Add Member ===")

    with DefaultAzureCredential() as credential:
        with MailchimpClient(CONNECTION_RUNTIME_URL, credential) as client:
            member = client.addmember(
                input=NewMemberInListRequest(
                    email_address="sample.user@example.com",
                    status="subscribed",
                ),
                list_id="123456",
            )
            print(f"Added member: {member}")


def main() -> None:
    """Run Mailchimp connector examples."""
    if not CONNECTION_RUNTIME_URL:
        print("Error: MAILCHIMP_CONNECTION_URL environment variable not set.")
        print("Set it to your connection runtime URL from Azure Portal.")
        return

    print("Mailchimp sample usage for the Azure Connectors Python SDK")
    print("=" * 50)

    try:
        # Uncomment to list campaigns/lists, create lists, or add members.
        # await example_1_list_campaigns()
        # await example_2_get_lists()
        # await example_3_new_list()
        # await example_4_add_member()
        print("Set the example calls in main() to run against your instance.")

    except ConnectorException as ex:
        print(f"Connector error: {ex}")
    except Exception as ex:
        print(f"Unexpected error: {ex}")


if __name__ == "__main__":
    main()
