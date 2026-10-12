"""CloudConvert connector SDK sample."""
import os

from azure.identity import DefaultAzureCredential

from azure.connectors import ConnectorException
from azure.connectors.cloudconvert import CloudconvertClient


CONNECTION_RUNTIME_URL = os.environ.get("CLOUDCONVERT_CONNECTION_URL", "")


def main() -> None:
    """Get CloudConvert conversion options."""
    if not CONNECTION_RUNTIME_URL:
        print("Set CLOUDCONVERT_CONNECTION_URL to run this sample.")
        return

    with DefaultAzureCredential() as credential:
        try:
            with CloudconvertClient(CONNECTION_RUNTIME_URL, credential) as client:
                options = client.get_convert_options()
                print(f"Conversion options: {options}")
        except ConnectorException as ex:
            print(f"Connector error: {ex}")


if __name__ == "__main__":
    main()
