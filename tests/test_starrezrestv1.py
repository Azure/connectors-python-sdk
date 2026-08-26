# Copyright (c) Microsoft Corporation. All rights reserved.

"""Contract tests for Starrezrestv1Client."""

from unittest.mock import AsyncMock, patch

import pytest

import azure.connectors.starrezrestv1 as starrezrestv1_module
from azure.connectors.sdk.serialization import to_wire
from azure.connectors.starrezrestv1 import SelectBookingInput, Starrezrestv1Client
from tests.conftest import MockResponse
from tests.generated_connector_test_utils import GeneratedConnectorContractTests


OPERATION_CONTRACTS = {
    "select_entry": ("POST", True),
    "create_entry": ("POST", True),
    "update_entry": ("POST", True),
    "delete": ("POST", False),
    "select_entry_custom_field": ("POST", True),
    "update_entry_custom_field": ("POST", True),
    "select_term": ("POST", True),
    "select_entry_address": ("POST", True),
    "update_entry_address": ("POST", True),
    "select_entry_application": ("POST", True),
    "create_entry_application": ("POST", True),
    "update_entry_application": ("POST", True),
    "select_term_session": ("POST", True),
    "select_entry_detail": ("POST", True),
    "update_entry_detail": ("POST", True),
    "select_entry_enrollment": ("POST", True),
    "create_entry_enrollment": ("POST", True),
    "update_entry_enrollment": ("POST", True),
    "select_booking": ("POST", True),
    "create_booking": ("POST", True),
    "update_booking": ("POST", True),
    "select_room_space": ("POST", True),
    "create_room_space": ("POST", True),
    "select_room_location": ("POST", True),
    "select_transaction": ("POST", True),
    "create_transaction": ("POST", True),
    "select_room_space_maintenance": ("POST", True),
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
    mock_token_provider,
) -> None:
    """Test a bounded booking query sends a meaningful request body."""
    client = Starrezrestv1Client(
        "https://example.azure.com/connections/test",
        token_provider=mock_token_provider,
    )
    request = SelectBookingInput(
        return_empty_array_on_no_result=True,
        page_size=10,
    )

    with patch.object(
        client._http_client,
        "send_async",
        new_callable=AsyncMock,
        return_value=MockResponse(status=200, text='{"bookings": []}'),
    ) as mock_send:
        result = await client.select_booking_async(input=request)

    mock_send.assert_awaited_once_with(
        "POST",
        "https://example.azure.com/connections/test/select/Booking.json",
        body=request,
    )
    assert to_wire(request) == {
        "_returnEmptyArrayOnNoResult": True,
        "_pageSize": 10,
    }
    assert result == {"bookings": []}
