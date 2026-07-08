# Copyright (c) Microsoft Corporation. All rights reserved.

"""Sample usage for the Excelonline connector client."""

import asyncio
import os

from azure.connectors.excelonline import (
    CreateWorksheetInput,
    ExcelonlineClient,
    Item,
)


async def main() -> None:
    """Run a simple Excel Online sample flow."""
    connection_url = os.getenv("EXCELONLINE_CONNECTION_URL")
    if not connection_url:
        raise ValueError("Set EXCELONLINE_CONNECTION_URL environment variable")

    drive_id = os.getenv("EXCELONLINE_DRIVE_ID", "drive-id")
    file_id = os.getenv("EXCELONLINE_FILE_ID", "file-id")
    table_name = os.getenv("EXCELONLINE_TABLE_NAME", "Table1")

    async with ExcelonlineClient(connection_url) as client:
        worksheets = await client.get_all_worksheets_async(
            drive=drive_id,
            file=file_id,
        )
        print("worksheets", worksheets)

        tables = await client.get_tables_async(
            drive=drive_id,
            file=file_id,
        )
        print("tables", tables)

        new_sheet = await client.create_worksheet_async(
            input=CreateWorksheetInput(name="SampleSheet"),
            drive=drive_id,
            file=file_id,
        )
        print("created worksheet", new_sheet)

        row = await client.add_row_async(
            input=Item(dynamic_properties={"Name": "Sample Item", "Value": 100}),
            drive=drive_id,
            file=file_id,
            table=table_name,
        )
        print("added row", row)


if __name__ == "__main__":
    asyncio.run(main())
