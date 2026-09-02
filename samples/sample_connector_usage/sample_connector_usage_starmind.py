"""Starmind connector SDK sample."""

import asyncio
import os

from azure.identity.aio import DefaultAzureCredential

from azure.connectors import ConnectorException
from azure.connectors.starmind import FindExpertsInput, StarmindClient


CONNECTION_RUNTIME_URL = os.environ.get("STARMIND_CONNECTION_URL", "")


async def find_questions() -> None:
    """Find questions matching a query."""
    credential = DefaultAzureCredential()
    async with StarmindClient(CONNECTION_RUNTIME_URL, credential) as client:
        questions = await client.find_questions_async(
            query="distributed systems",
            limit=10,
        )
        print(f"Questions: {questions}")


async def find_experts() -> None:
    """Find experts for a topic."""
    credential = DefaultAzureCredential()
    async with StarmindClient(CONNECTION_RUNTIME_URL, credential) as client:
        experts = await client.find_experts_async(
            input=FindExpertsInput(text_query="distributed systems"),
        )
        print(f"Experts: {experts}")


async def main() -> None:
    """Run Starmind connector examples."""
    if not CONNECTION_RUNTIME_URL:
        print("Set STARMIND_CONNECTION_URL to run this sample.")
        return

    try:
        await find_questions()
        await find_experts()
    except ConnectorException as ex:
        print(f"Connector error: {ex}")


if __name__ == "__main__":
    asyncio.run(main())
