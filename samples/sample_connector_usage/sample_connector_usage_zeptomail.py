"""Zoho ZeptoMail connector SDK sample."""

import asyncio
import os

from azure.identity.aio import DefaultAzureCredential

from azure.connectors import AzureIdentityTokenProvider, ConnectorException
from azure.connectors.zeptomail import ZeptomailClient


CONNECTION_RUNTIME_URL = os.environ.get("ZEPTOMAIL_CONNECTION_URL", "")


async def main() -> None:
    """List the configured ZeptoMail mail agents."""
    if not CONNECTION_RUNTIME_URL:
        print("Set ZEPTOMAIL_CONNECTION_URL to run this sample.")
        return

    token_provider = AzureIdentityTokenProvider(DefaultAzureCredential())
    try:
        async with ZeptomailClient(
            CONNECTION_RUNTIME_URL,
            token_provider,
        ) as client:
            mail_agents = await client.get_mail_agent_async()
            print(f"Mail agents: {mail_agents}")
    except ConnectorException as ex:
        print(f"Connector error: {ex}")


if __name__ == "__main__":
    asyncio.run(main())
