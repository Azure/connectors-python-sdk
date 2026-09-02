"""
DocuSign Connector SDK Sample

This sample demonstrates how to use the DocuSign connector SDK.

Prerequisites:
1. Azure subscription with DocuSign connection
2. DocuSign connection in Connector Namespaces
3. Connection runtime URL from Azure Portal

Installation:
    pip install azure-connectors

Usage:
    Set environment variable:
    $env:DOCUSIGN_CONNECTION_URL = "https://[region].azure-apihub.net/apim/docusign/[connection-id]"

    python sample_connector_usage_docusign.py
"""

import asyncio
import os

from azure.identity.aio import DefaultAzureCredential

from azure.connectors import ConnectorException
from azure.connectors.docusign import DocusignClient


# Connection runtime URL format:
# https://[region].azure-apihub.net/apim/docusign/[connection-id]
CONNECTION_RUNTIME_URL = os.environ.get("DOCUSIGN_CONNECTION_URL", "")


async def example_1_get_login_accounts() -> list[dict]:
    """Example 1: Get available DocuSign accounts."""
    print("\n=== Example 1: Get Login Accounts ===")

    credential = DefaultAzureCredential()
    async with DocusignClient(CONNECTION_RUNTIME_URL, credential) as client:
        accounts_response = await client.get_login_accounts_async()
        accounts = accounts_response.get("accounts", []) if accounts_response else []

        print(f"Found {len(accounts)} accounts")
        for account in accounts[:10]:
            print(f"  - {account.get('accountName')} ({account.get('accountId')})")

        return accounts


async def example_2_search_envelopes(account_id: str) -> None:
    """Example 2: Search envelopes for an account."""
    print("\n=== Example 2: Search Envelopes ===")

    credential = DefaultAzureCredential()
    async with DocusignClient(CONNECTION_RUNTIME_URL, credential) as client:
        envelopes_response = await client.search_list_envelopes_async(
            account_id=account_id,
            top=5,
        )

        envelopes = envelopes_response.get("value", []) if envelopes_response else []
        print(f"Found {len(envelopes)} envelopes")
        for envelope in envelopes[:5]:
            print(f"  - {envelope.get('envelopeId')} ({envelope.get('status')})")


async def main() -> None:
    """Run all examples."""
    if not CONNECTION_RUNTIME_URL:
        print("Error: DOCUSIGN_CONNECTION_URL environment variable not set.")
        print("Set it to your connection runtime URL from Azure Portal.")
        return

    print("DocuSign Connector SDK - Sample Usage")
    print("=" * 50)

    try:
        accounts = await example_1_get_login_accounts()
        if accounts:
            first_account_id = accounts[0].get("accountId")
            if first_account_id:
                await example_2_search_envelopes(first_account_id)
            else:
                print("No account id found in first record; skipping envelope search.")
        else:
            print("No accounts found; skipping account-specific examples.")

    except ConnectorException as ex:
        print(f"Connector error: {ex}")
    except Exception as ex:
        print(f"Unexpected error: {ex}")


if __name__ == "__main__":
    asyncio.run(main())
