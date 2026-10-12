# Copyright (c) Microsoft Corporation. All rights reserved.

"""Sample usage for the RSS connector client."""
import os

from azure.identity import DefaultAzureCredential

from azure.connectors.rss import RssClient


def main() -> None:
    """Run a simple RSS sample flow."""
    connection_url = os.getenv("RSS_CONNECTION_URL")
    if not connection_url:
        raise ValueError("Set RSS_CONNECTION_URL environment variable")

    feed_url = os.getenv("RSS_FEED_URL", "https://devblogs.microsoft.com/python/feed/")

    with DefaultAzureCredential() as credential:
        with RssClient(connection_url, credential) as client:
            items = client.list_feed_items(
                feed_url=feed_url,
                since_property="PublishDate",
            )
            print(f"Retrieved {len(items or [])} item(s) from '{feed_url}'.")

            latest_items = client.list_feed_items(
                feed_url=feed_url,
                since_property="PublishDate",
            )
            values = (latest_items or {}).get("value", [])
            print(f"Polling query returned {len(values)} item(s).")


if __name__ == "__main__":
    main()
