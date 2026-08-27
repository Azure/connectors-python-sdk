"""StarRez REST V1 connector SDK sample."""

import asyncio
import os

from azure.identity.aio import DefaultAzureCredential

from azure.connectors import AzureIdentityTokenProvider, ConnectorException
from azure.connectors.starrezrestv1 import SelectBookingInput, Starrezrestv1Client


CONNECTION_RUNTIME_URL = os.environ.get("STARREZRESTV1_CONNECTION_URL", "")


async def main() -> None:
    """List up to ten StarRez bookings."""
    if not CONNECTION_RUNTIME_URL:
        print("Set STARREZRESTV1_CONNECTION_URL to run this sample.")
        return

    token_provider = AzureIdentityTokenProvider(DefaultAzureCredential())
    try:
        async with Starrezrestv1Client(
            CONNECTION_RUNTIME_URL,
            token_provider,
        ) as client:
            bookings = await client.select_booking_async(
                input=SelectBookingInput(
                    return_empty_array_on_no_result=True,
                    page_size=10,
                )
            )
            print(f"Bookings: {bookings}")
    except ConnectorException as ex:
        print(f"Connector error: {ex}")


if __name__ == "__main__":
    asyncio.run(main())
