"""Twitter connector SDK sample."""

import asyncio
import os

from azure.identity.aio import DefaultAzureCredential

from azure.connectors import ConnectorException
from azure.connectors.twitter import TwitterClient


CONNECTION_RUNTIME_URL = os.environ.get("TWITTER_CONNECTION_URL", "")


async def list_user_timeline() -> None:
    """List recent posts from a user's timeline."""
    credential = DefaultAzureCredential()
    async with TwitterClient(CONNECTION_RUNTIME_URL, credential) as client:
        timeline = await client.user_timeline_async(
            user_name="Azure",
            max_results=10,
        )
        print(f"Timeline: {timeline}")


async def search_posts() -> None:
    """Search recent posts."""
    credential = DefaultAzureCredential()
    async with TwitterClient(CONNECTION_RUNTIME_URL, credential) as client:
        results = await client.search_tweet_async(
            search_query="Azure Logic Apps",
            max_results=10,
        )
        print(f"Search results: {results}")


async def main() -> None:
    """Run Twitter connector examples."""
    if not CONNECTION_RUNTIME_URL:
        print("Set TWITTER_CONNECTION_URL to run this sample.")
        return

    try:
        await list_user_timeline()
        await search_posts()
    except ConnectorException as ex:
        print(f"Connector error: {ex}")


if __name__ == "__main__":
    asyncio.run(main())
