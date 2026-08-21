"""Rev.ai connector SDK sample."""

import asyncio
import os

from azure.identity.aio import DefaultAzureCredential

from azure.connectors import ConnectorException
from azure.connectors.revai import RevaiClient, TranscriptionInput


CONNECTION_RUNTIME_URL = os.environ.get("REVAI_CONNECTION_URL", "")


async def get_account() -> None:
    """Get account information."""
    credential = DefaultAzureCredential()
    async with RevaiClient(CONNECTION_RUNTIME_URL, credential) as client:
        account = await client.account_get_async()
        print(f"Account: {account}")


async def submit_transcription() -> None:
    """Submit an audio file for transcription."""
    credential = DefaultAzureCredential()
    async with RevaiClient(CONNECTION_RUNTIME_URL, credential) as client:
        job = await client.transcription_async(
            input=TranscriptionInput(
                source_config={"url": "https://example.com/audio.wav"},
                metadata="connector-sdk-sample",
            ),
        )
        print(f"Transcription job: {job}")


async def main() -> None:
    """Run Rev.ai connector examples."""
    if not CONNECTION_RUNTIME_URL:
        print("Set REVAI_CONNECTION_URL to run this sample.")
        return

    try:
        await get_account()
        await submit_transcription()
    except ConnectorException as ex:
        print(f"Connector error: {ex}")


if __name__ == "__main__":
    asyncio.run(main())