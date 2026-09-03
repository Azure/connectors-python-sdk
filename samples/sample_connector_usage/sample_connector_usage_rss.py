# Copyright (c) Microsoft Corporation. All rights reserved.

"""Sample usage for the RSS connector client."""

import asyncio
import os

from azure.connectors.rss import RssClient


async def main() -> None:
    """Run a simple RSS sample flow."""
    connection_url = os.getenv("RSS_CONNECTION_URL")
    if not connection_url:
        raise ValueError("Set RSS_CONNECTION_URL environment variable")

    feed_url = os.getenv("RSS_FEED_URL", "https://devblogs.microsoft.com/python/feed/")

    async with RssClient(connection_url) as client:
        items = await client.list_feed_items_async(
            feed_url=feed_url,
            since_property="PublishDate",
        )
        print(f"Retrieved {len(items or [])} item(s) from '{feed_url}'.")

        latest_items = await client.list_feed_items_async(
            feed_url=feed_url,
            since_property="PublishDate",
        )
        values = (latest_items or {}).get("value", [])
        print(f"Polling query returned {len(values)} item(s).")


if __name__ == "__main__":
    asyncio.run(main())
