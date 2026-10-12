"""Plivo connector SDK sample."""
import os

from azure.identity import DefaultAzureCredential

from azure.connectors import ConnectorException
from azure.connectors.plivo import PlivoClient, SMS


CONNECTION_RUNTIME_URL = os.environ.get("PLIVO_CONNECTION_URL", "")


def send_sms() -> None:
    """Send an SMS message."""
    with DefaultAzureCredential() as credential:
        with PlivoClient(CONNECTION_RUNTIME_URL, credential) as client:
            result = client.send_sms(
                input=SMS(
                    src="15550000000",
                    dst="15551111111",
                    text="Hello from the Azure Connectors Python SDK.",
                ),
                auth_id="PLIVO_AUTH_ID",
            )
            print(f"Send result: {result}")


def list_messages() -> None:
    """List messages for an account."""
    with DefaultAzureCredential() as credential:
        with PlivoClient(CONNECTION_RUNTIME_URL, credential) as client:
            messages = client.list_messages(auth_id="PLIVO_AUTH_ID")
            print(f"Messages: {messages}")


def main() -> None:
    """Run Plivo connector examples."""
    if not CONNECTION_RUNTIME_URL:
        print("Set PLIVO_CONNECTION_URL to run this sample.")
        return

    try:
        list_messages()
        send_sms()
    except ConnectorException as ex:
        print(f"Connector error: {ex}")


if __name__ == "__main__":
    main()
