# Copyright (c) Microsoft Corporation. All rights reserved.

"""Contract tests for Starrezrestv1Client."""

from unittest.mock import AsyncMock, patch

import pytest

import azure.connectors.starrezrestv1 as starrezrestv1_module
from azure.connectors.sdk.serialization import to_wire
from azure.connectors.aio.starrezrestv1 import Starrezrestv1Client
from azure.connectors.starrezrestv1 import SelectBookingInput
from tests.conftest import MockResponse
from tests.generated_connector_test_utils import (
    GeneratedConnectorContractTests,
    model_instance,
    resolve_generated_result,
)


OPERATION_CONTRACTS = {
    "list_select_entry": ("POST", True),
    "create_entry": ("POST", True),
    "update_entry": ("POST", True),
    "delete": ("POST", False),
    "list_select_entry_custom_field": ("POST", True),
    "update_entry_custom_field": ("POST", True),
    "list_select_term": ("POST", True),
    "list_select_entry_address": ("POST", True),
    "update_entry_address": ("POST", True),
    "list_select_entry_application": ("POST", True),
    "create_entry_application": ("POST", True),
    "update_entry_application": ("POST", True),
    "list_select_term_session": ("POST", True),
    "list_select_entry_detail": ("POST", True),
    "update_entry_detail": ("POST", True),
    "list_select_entry_enrollment": ("POST", True),
    "create_entry_enrollment": ("POST", True),
    "update_entry_enrollment": ("POST", True),
    "list_select_booking": ("POST", True),
    "create_booking": ("POST", True),
    "update_booking": ("POST", True),
    "list_select_room_space": ("POST", True),
    "create_room_space": ("POST", True),
    "list_select_room_location": ("POST", True),
    "list_select_transaction": ("POST", True),
    "create_transaction": ("POST", True),
    "list_select_room_space_maintenance": ("POST", True),
    "create_room_space_maintenance": ("POST", True),
    "update_room_space_maintenance": ("POST", True),
}


class TestStarrezrestv1Client(GeneratedConnectorContractTests):
    """Test the generated StarRez REST V1 client contract."""

    client_type = Starrezrestv1Client
    connector_module = starrezrestv1_module
    connector_name = "starrezrestv1"
    operation_contracts = OPERATION_CONTRACTS


@pytest.mark.asyncio
async def test_select_booking_sends_filter_and_deserializes_response(
    mock_credential,
) -> None:
    """Test a bounded booking query sends a meaningful request body."""
    client = Starrezrestv1Client(
        "https://example.azure.com/connections/test",
        credential=mock_credential,
    )
    request = model_instance(
        SelectBookingInput,
        return_empty_array_on_no_result=True,
        page_size=10,
    )

    with patch.object(
        client._http_client,
        "send",
        new_callable=AsyncMock,
        return_value=MockResponse(status=200, text='[{"BookingID": 123}]'),
    ) as mock_send:
        result = await resolve_generated_result(
            client.list_select_booking(input=request)
        )

    mock_send.assert_awaited_once_with(
        "POST",
        "https://example.azure.com/connections/test/select/Booking.json",
        body=request,
        timeout=None,
        headers=None,
        client_request_id=None,
        response_hook=None,
    )
    assert to_wire(request) == {
        "_returnEmptyArrayOnNoResult": True,
        "_pageSize": 10,
        "_pageIndex": 1,
    }
    assert result == [{"BookingID": 123}]
