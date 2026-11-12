# ------------------------------------------------------------
# Copyright (c) Microsoft Corporation.  All rights reserved.
# ------------------------------------------------------------

"""Read sms balance through the generated async connector client."""

import asyncio
import os

from azure.identity.aio import DefaultAzureCredential

from azure.connectors.data_flows_sms import DataFlowsSmsClient


CONNECTION_RUNTIME_URL = os.environ.get("DATAFLOWSSMS_CONNECTION_URL", "")


async def main() -> None:
    """Use a read-only operation; no connector mutation is performed."""
    if not CONNECTION_RUNTIME_URL:
        print("Set DATAFLOWSSMS_CONNECTION_URL to run this sample.")
        return

    async with DefaultAzureCredential() as credential:
        async with DataFlowsSmsClient(CONNECTION_RUNTIME_URL, credential) as client:
            value = await client.get_balance()
            print(f"SMS balance: {value}")


if __name__ == "__main__":
    asyncio.run(main())
