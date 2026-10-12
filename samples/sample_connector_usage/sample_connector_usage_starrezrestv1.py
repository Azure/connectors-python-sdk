"""StarRez REST V1 connector SDK sample."""
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
                bookings = client.select_booking(
                    input=SelectBookingInput(
                        return_empty_array_on_no_result=True,
                        page_size=10,
                    )
                )
                print(f"Bookings: {bookings}")
        except ConnectorException as ex:
            print(f"Connector error: {ex}")


if __name__ == "__main__":
    main()
