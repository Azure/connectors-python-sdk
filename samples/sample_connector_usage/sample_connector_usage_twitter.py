"""Twitter sample for the Azure Connectors Python SDK."""
import os

from azure.identity import DefaultAzureCredential

from azure.connectors import ConnectorException
from azure.connectors.twitter import TwitterClient


CONNECTION_RUNTIME_URL = os.environ.get("TWITTER_CONNECTION_URL", "")


def list_user_timeline() -> None:
    """List recent posts from a user's timeline."""
    with DefaultAzureCredential() as credential:
        with TwitterClient(CONNECTION_RUNTIME_URL, credential) as client:
            timeline = client.list_user_timeline(
                user_name="Azure",
                max_results=10,
            )
            print(f"Timeline: {timeline}")


def search_posts() -> None:
    """Search recent posts."""
    with DefaultAzureCredential() as credential:
        with TwitterClient(CONNECTION_RUNTIME_URL, credential) as client:
            results = client.list_search_tweet(
                search_query="Azure Logic Apps",
                max_results=10,
            )
            print(f"Search results: {results}")


def main() -> None:
    """Run Twitter connector examples."""
    if not CONNECTION_RUNTIME_URL:
        print("Set TWITTER_CONNECTION_URL to run this sample.")
        return

    try:
        list_user_timeline()
        search_posts()
    except ConnectorException as ex:
        print(f"Connector error: {ex}")


if __name__ == "__main__":
    main()
