"""
Projectplace Connector SDK Sample

This sample demonstrates how to use the Projectplace connector SDK.

Prerequisites:
1. Azure subscription with a Projectplace connection
2. Projectplace connection in Connector Namespaces
3. Connection runtime URL from Azure Portal

Installation:
    pip install azure-connectors

Usage:
    Set environment variable:
    $env:PROJECTPLACE_CONNECTION_URL = "https://[region].azure-apihub.net/apim/projectplace/[id]"

    python sample_connector_usage_projectplace.py
"""

import asyncio
import os

from azure.identity.aio import DefaultAzureCredential

from azure.connectors import ConnectorException
from azure.connectors.projectplace import (
    CreateCardInput,
    MoveCardInput,
    ProjectplaceClient,
)


# Connection runtime URL format:
# https://[region].azure-apihub.net/apim/projectplace/[connection-id]
CONNECTION_RUNTIME_URL = os.environ.get("PROJECTPLACE_CONNECTION_URL", "")


async def example_1_list_boards() -> None:
    """Example 1: List the boards the user has access to."""
    print("\n=== Example 1: List Boards ===")

    credential = DefaultAzureCredential()
    async with ProjectplaceClient(CONNECTION_RUNTIME_URL, credential) as client:
        boards = await client.list_boards_async()
        print(f"Boards: {boards}")


async def example_2_create_card() -> None:
    """Example 2: Create a card on a board."""
    print("\n=== Example 2: Create Card ===")

    credential = DefaultAzureCredential()
    async with ProjectplaceClient(CONNECTION_RUNTIME_URL, credential) as client:
        card = await client.create_card_async(
            input=CreateCardInput(
                column_id=123456,
                title="SDK sample card",
                description="Created from the projectplace SDK sample.",
            ),
            board_id=789012,
        )
        print(f"Created card: {card}")


async def example_3_move_card() -> None:
    """Example 3: Move a card to another column."""
    print("\n=== Example 3: Move Card ===")

    credential = DefaultAzureCredential()
    async with ProjectplaceClient(CONNECTION_RUNTIME_URL, credential) as client:
        card = await client.move_card_async(
            input=MoveCardInput(card_id=123456, column_id=654321),
            board_id=789012,
        )
        print(f"Moved card: {card}")


async def main() -> None:
    """Run Projectplace connector examples."""
    if not CONNECTION_RUNTIME_URL:
        print("Error: PROJECTPLACE_CONNECTION_URL environment variable not set.")
        print("Set it to your connection runtime URL from Azure Portal.")
        return

    print("Projectplace Connector SDK - Sample Usage")
    print("=" * 50)

    try:
        # Uncomment to list boards, create cards, or move cards in Projectplace.
        # await example_1_list_boards()
        # await example_2_create_card()
        # await example_3_move_card()
        print("Set the example calls in main() to run against your instance.")

    except ConnectorException as ex:
        print(f"Connector error: {ex}")
    except Exception as ex:
        print(f"Unexpected error: {ex}")


if __name__ == "__main__":
    asyncio.run(main())
