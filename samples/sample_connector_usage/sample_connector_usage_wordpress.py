"""WordPress sample for the Azure Connectors Python SDK."""
import os

from azure.identity import DefaultAzureCredential

from azure.connectors import ConnectorException
from azure.connectors.wordpress import CreatePostModel, WordpressClient


CONNECTION_RUNTIME_URL = os.environ.get("WORDPRESS_CONNECTION_URL", "")


def list_sites() -> None:
    """List WordPress sites available to the connection."""
    with DefaultAzureCredential() as credential:
        with WordpressClient(CONNECTION_RUNTIME_URL, credential) as client:
            sites = client.list_sites()
            print(f"Sites: {sites}")


def create_post() -> None:
    """Create a draft WordPress post."""
    with DefaultAzureCredential() as credential:
        with WordpressClient(CONNECTION_RUNTIME_URL, credential) as client:
            post = client.create(
                input=CreatePostModel(
                    title="Generated connector sample",
                    content="Created with the Azure Connectors Python SDK.",
                    status="draft",
                ),
                site_id="SITE_ID",
            )
            print(f"Created post: {post}")


def main() -> None:
    """Run WordPress connector examples."""
    if not CONNECTION_RUNTIME_URL:
        print("Set WORDPRESS_CONNECTION_URL to run this sample.")
        return

    try:
        list_sites()
        create_post()
    except ConnectorException as ex:
        print(f"Connector error: {ex}")


if __name__ == "__main__":
    main()
