"""Zoho ZeptoMail connector SDK sample."""
import os

from azure.identity import DefaultAzureCredential

from azure.connectors import ConnectorException
from azure.connectors.zeptomail import ZeptomailClient


CONNECTION_RUNTIME_URL = os.environ.get("ZEPTOMAIL_CONNECTION_URL", "")


def main() -> None:
    """List the configured ZeptoMail mail agents."""
    if not CONNECTION_RUNTIME_URL:
        print("Set ZEPTOMAIL_CONNECTION_URL to run this sample.")
        return

    with DefaultAzureCredential() as credential:
        try:
            with ZeptomailClient(
                CONNECTION_RUNTIME_URL,
                credential,
            ) as client:
                mail_agents = client.get_mail_agent()
                print(f"Mail agents: {mail_agents}")
        except ConnectorException as ex:
            print(f"Connector error: {ex}")


if __name__ == "__main__":
    main()
