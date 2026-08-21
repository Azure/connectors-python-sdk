"""
Trello Connector SDK Sample

This sample demonstrates how to use the Trello connector SDK.

Prerequisites:
1. Azure subscription with a Trello connection
2. Trello connection in Connector Namespaces
3. Connection runtime URL from Azure Portal

Installation:
    pip install azure-connectors

Usage:
    Set environment variable:
    $env:TRELLO_CONNECTION_URL = "https://[region].azure-apihub.net/apim/trello/[id]"

    python sample_connector_usage_trello.py
"""

import asyncio
import os

from azure.identity.aio import DefaultAzureCredential

from azure.connectors import ConnectorException
from azure.connectors.trello import CreateBoard, CreateCard, CreateList, TrelloClient


# Connection runtime URL format:
# https://[region].azure-apihub.net/apim/trello/[connection-id]
CONNECTION_RUNTIME_URL = os.environ.get("TRELLO_CONNECTION_URL", "")


async def example_1_list_boards() -> None:
    """Example 1: List boards available to the current member."""
    print("\n=== Example 1: List Boards ===")

    credential = DefaultAzureCredential()
    async with TrelloClient(CONNECTION_RUNTIME_URL, credential) as client:
        boards = await client.list_boards_simple_async()
        print(f"Boards: {boards}")


async def example_2_create_board() -> None:
    """Example 2: Create a board."""
    print("\n=== Example 2: Create Board ===")

    credential = DefaultAzureCredential()
    async with TrelloClient(CONNECTION_RUNTIME_URL, credential) as client:
        board = await client.create_board_async(
            input=CreateBoard(
                name="SDK sample board",
                desc="Created from the Trello connector SDK sample.",
                default_lists="false",
            )
        )
        print(f"Created board: {board}")


async def example_3_create_list() -> None:
    """Example 3: Create a list on an existing board."""
    print("\n=== Example 3: Create List ===")

    credential = DefaultAzureCredential()
    async with TrelloClient(CONNECTION_RUNTIME_URL, credential) as client:
        created_list = await client.create_list_async(
            input=CreateList(
                name="SDK sample list",
                id_board="board-id",
                pos="bottom",
            )
        )
        print(f"Created list: {created_list}")


async def example_4_create_card() -> None:
    """Example 4: Create a card in an existing list."""
    print("\n=== Example 4: Create Card ===")

    credential = DefaultAzureCredential()
    async with TrelloClient(CONNECTION_RUNTIME_URL, credential) as client:
        card = await client.create_card_async(
            input=CreateCard(
                id_list="list-id",
                name="SDK sample card",
                desc="Created from the Trello connector SDK sample.",
            ),
            board_id="board-id",
        )
        print(f"Created card: {card}")


async def main() -> None:
    """Run Trello connector examples."""
    if not CONNECTION_RUNTIME_URL:
        print("Error: TRELLO_CONNECTION_URL environment variable not set.")
        print("Set it to your connection runtime URL from Azure Portal.")
        return

    print("Trello Connector SDK - Sample Usage")
    print("=" * 50)

    try:
        # Uncomment the examples to run them against your Trello connection.
        # await example_1_list_boards()
        # await example_2_create_board()
        # await example_3_create_list()
        # await example_4_create_card()
        print("Set the example calls in main() to run against your instance.")

    except ConnectorException as ex:
        print(f"Connector error: {ex}")
    except Exception as ex:
        print(f"Unexpected error: {ex}")


if __name__ == "__main__":
    asyncio.run(main())
