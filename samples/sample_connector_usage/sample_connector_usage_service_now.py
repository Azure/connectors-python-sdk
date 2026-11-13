# ------------------------------------------------------------
# Copyright (c) Microsoft Corporation.  All rights reserved.
# ------------------------------------------------------------

"""Read incident record through the generated async connector client."""

import asyncio
import os

from azure.identity.aio import DefaultAzureCredential

from azure.connectors.service_now import ServiceNowClient


CONNECTION_RUNTIME_URL = os.environ.get("SERVICENOW_CONNECTION_URL", "")
RECORD_ID = os.environ.get("SERVICENOW_RECORD_ID", "")


async def main() -> None:
    """Use a read-only operation; no connector mutation is performed."""
    if not CONNECTION_RUNTIME_URL or not RECORD_ID:
        print("Set SERVICENOW_CONNECTION_URL and SERVICENOW_RECORD_ID to run this sample.")
        return

    async with DefaultAzureCredential() as credential:
        async with ServiceNowClient(CONNECTION_RUNTIME_URL, credential) as client:
            value = await client.get_record(table_type="incident", sysid=RECORD_ID)
            print(f"Incident record: {value}")


if __name__ == "__main__":
    asyncio.run(main())
