"""Starmind sample for the Azure Connectors Python SDK."""
import os

from azure.identity import DefaultAzureCredential

from azure.connectors import ConnectorException
from azure.connectors.starmind import FindExpertsInput, StarmindClient


CONNECTION_RUNTIME_URL = os.environ.get("STARMIND_CONNECTION_URL", "")


def find_questions() -> None:
    """Find questions matching a query."""
    with DefaultAzureCredential() as credential:
        with StarmindClient(CONNECTION_RUNTIME_URL, credential) as client:
            questions = client.find_questions(
                query="distributed systems",
                limit=10,
            )
            print(f"Questions: {questions}")


def find_experts() -> None:
    """Find experts for a topic."""
    with DefaultAzureCredential() as credential:
        with StarmindClient(CONNECTION_RUNTIME_URL, credential) as client:
            experts = client.find_experts(
                input=FindExpertsInput(text_query="distributed systems"),
            )
            print(f"Experts: {experts}")


def main() -> None:
    """Run Starmind connector examples."""
    if not CONNECTION_RUNTIME_URL:
        print("Set STARMIND_CONNECTION_URL to run this sample.")
        return

    try:
        find_questions()
        find_experts()
    except ConnectorException as ex:
        print(f"Connector error: {ex}")


if __name__ == "__main__":
    main()
