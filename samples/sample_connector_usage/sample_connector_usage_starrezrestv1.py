"""StarRez REST V1 sample for the Azure Connectors Python SDK."""
import os

from azure.identity import DefaultAzureCredential

from azure.connectors import ConnectorException
from azure.connectors.starrezrestv1 import SelectBookingInput, Starrezrestv1Client


CONNECTION_RUNTIME_URL = os.environ.get("STARREZRESTV1_CONNECTION_URL", "")


def main() -> None:
    """List up to ten StarRez bookings."""
    if not CONNECTION_RUNTIME_URL:
        print("Set STARREZRESTV1_CONNECTION_URL to run this sample.")
        return

    with DefaultAzureCredential() as credential:
        try:
            with Starrezrestv1Client(
                CONNECTION_RUNTIME_URL,
                credential,
            ) as client:
                bookings = client.list_select_booking(
                    input=SelectBookingInput(
                        return_empty_array_on_no_result=True,
                        page_size=10,
                        page_index=1,
                    )
                )
                print(f"Bookings: {bookings}")
        except ConnectorException as ex:
            print(f"Connector error: {ex}")


if __name__ == "__main__":
    main()
