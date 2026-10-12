"""Rev.ai sample for the Azure Connectors Python SDK."""
import os

from azure.identity import DefaultAzureCredential

from azure.connectors import ConnectorException
from azure.connectors.revai import RevaiClient, TranscriptionInput


CONNECTION_RUNTIME_URL = os.environ.get("REVAI_CONNECTION_URL", "")


def get_account() -> None:
    """Get account information."""
    with DefaultAzureCredential() as credential:
        with RevaiClient(CONNECTION_RUNTIME_URL, credential) as client:
            account = client.account_get()
            print(f"Account: {account}")


def submit_transcription() -> None:
    """Submit an audio file for transcription."""
    with DefaultAzureCredential() as credential:
        with RevaiClient(CONNECTION_RUNTIME_URL, credential) as client:
            job = client.transcription(
                input=TranscriptionInput(
                    source_config={"url": "https://example.com/audio.wav"},
                    metadata="connector-sdk-sample",
                ),
            )
            print(f"Transcription job: {job}")


def main() -> None:
    """Run Rev.ai connector examples."""
    if not CONNECTION_RUNTIME_URL:
        print("Set REVAI_CONNECTION_URL to run this sample.")
        return

    try:
        get_account()
        submit_transcription()
    except ConnectorException as ex:
        print(f"Connector error: {ex}")


if __name__ == "__main__":
    main()
