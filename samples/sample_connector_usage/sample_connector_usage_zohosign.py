# Copyright (c) Microsoft Corporation. All rights reserved.

"""Zoho Sign connector SDK sample."""
import os

from azure.identity import DefaultAzureCredential

from azure.connectors import ConnectorException
from azure.connectors.zohosign import ZohosignClient


CONNECTION_RUNTIME_URL = os.environ.get("ZOHOSIGN_CONNECTION_URL", "")
REQUEST_ID = os.environ.get("ZOHOSIGN_REQUEST_ID", "")


def list_templates() -> None:
    """List available Zoho Sign templates."""
    with DefaultAzureCredential() as credential:
        with ZohosignClient(CONNECTION_RUNTIME_URL, credential) as client:
            templates = client.get_templates()
            print(f"Templates: {templates}")


def get_document() -> None:
    """Get a Zoho Sign document request."""
    if not REQUEST_ID:
        print("Set ZOHOSIGN_REQUEST_ID to retrieve a document request.")
        return

    with DefaultAzureCredential() as credential:
        with ZohosignClient(CONNECTION_RUNTIME_URL, credential) as client:
            document = client.get_document(request_id=int(REQUEST_ID))
            print(f"Document: {document}")


def main() -> None:
    """Run the Zoho Sign examples."""
    if not CONNECTION_RUNTIME_URL:
        print("Error: ZOHOSIGN_CONNECTION_URL environment variable not set.")
        return

    try:
        list_templates()
        get_document()
    except ConnectorException as ex:
        print(f"Connector error: {ex}")


if __name__ == "__main__":
    main()
