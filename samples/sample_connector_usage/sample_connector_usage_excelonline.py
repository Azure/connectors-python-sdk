# Copyright (c) Microsoft Corporation. All rights reserved.

"""Sample usage for the Excelonline connector client."""
import os

from azure.identity import DefaultAzureCredential

from azure.connectors.excelonline import (
    CreateWorksheetInput,
    ExcelonlineClient,
    Item,
)


def main() -> None:
    """Run a simple Excel Online sample flow."""
    connection_url = os.getenv("EXCELONLINE_CONNECTION_URL")
    if not connection_url:
        raise ValueError("Set EXCELONLINE_CONNECTION_URL environment variable")

    drive_id = os.getenv("EXCELONLINE_DRIVE_ID", "drive-id")
    file_id = os.getenv("EXCELONLINE_FILE_ID", "file-id")
    table_name = os.getenv("EXCELONLINE_TABLE_NAME", "Table1")

    with DefaultAzureCredential() as credential:
        with ExcelonlineClient(connection_url, credential) as client:
            worksheets = list(client.list_all_worksheets(
                drive=drive_id,
                file=file_id,
            ))
            print("worksheets", worksheets)

            tables = list(client.list_tables(
                drive=drive_id,
                file=file_id,
            ))
            print("tables", tables)

            new_sheet = client.create_worksheet(
                input=CreateWorksheetInput(name="SampleSheet"),
                drive=drive_id,
                file=file_id,
            )
            print("created worksheet", new_sheet)

            row = client.add_row(
                input=Item(dynamic_properties={"Name": "Sample Item", "Value": 100}),
                drive=drive_id,
                file=file_id,
                table=table_name,
            )
            print("added row", row)


if __name__ == "__main__":
    main()
