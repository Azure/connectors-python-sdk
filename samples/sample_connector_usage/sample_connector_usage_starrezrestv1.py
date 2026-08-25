"""StarRez REST V1 connector SDK sample."""

import asyncio
import os

from azure.identity.aio import DefaultAzureCredential

from azure.connectors import ConnectorException
from azure.connectors.starrezrestv1 import CreateBookingInput, Starrezrestv1Client


CONNECTION_RUNTIME_URL = os.environ.get("STARREZRESTV1_CONNECTION_URL", "")


async def main() -> None:
    """Create a StarRez booking from a typed request model."""
    if not CONNECTION_RUNTIME_URL:
        print("Set STARREZRESTV1_CONNECTION_URL to run this sample.")
        return

    credential = DefaultAzureCredential()
    try:
        async with Starrezrestv1Client(CONNECTION_RUNTIME_URL, credential) as client:
            booking = await client.create_booking_async(input=CreateBookingInput())
            print(f"Booking: {booking}")
    except ConnectorException as ex:
        print(f"Connector error: {ex}")


if __name__ == "__main__":
    asyncio.run(main())