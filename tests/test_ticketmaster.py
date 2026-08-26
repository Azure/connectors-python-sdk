# Copyright (c) Microsoft Corporation. All rights reserved.

"""Contract tests for TicketmasterClient."""

from unittest.mock import AsyncMock, patch

import pytest

import azure.connectors.ticketmaster as ticketmaster_module
from azure.connectors.ticketmaster import TicketmasterClient
from tests.conftest import MockResponse
from tests.generated_connector_test_utils import GeneratedConnectorContractTests


OPERATION_CONTRACTS = {
    "events_get": ("GET", False),
    "event_get": ("GET", False),
    "event_images_get": ("GET", False),
    "attractions_get": ("GET", False),
    "attraction_get": ("GET", False),
    "classifications_get": ("GET", False),
    "classification_get": ("GET", False),
    "genre_get": ("GET", False),
    "segment_get": ("GET", False),
    "sub_genre_get": ("GET", False),
    "venues_get": ("GET", False),
    "venue_get": ("GET", False),
    "suggestions_get": ("GET", False),
}


class TestTicketmasterClient(GeneratedConnectorContractTests):
    """Test the generated Ticketmaster client contract."""

    client_type = TicketmasterClient
    connector_module = ticketmaster_module
    connector_name = "ticketmaster"
    operation_contracts = OPERATION_CONTRACTS


@pytest.mark.asyncio
async def test_attractions_get_serializes_query_and_response(
    mock_token_provider,
) -> None:
    """Test array query serialization and response deserialization."""
    client = TicketmasterClient(
        "https://example.azure.com/connections/test",
        token_provider=mock_token_provider,
    )

    with patch.object(
        client._http_client,
        "send_async",
        new_callable=AsyncMock,
        return_value=MockResponse(status=200, text='{"items": []}'),
    ) as mock_send:
        result = await client.attractions_get_async(
            keyword="rock & roll",
            classification_name=["music", "comedy"],
        )

    mock_send.assert_awaited_once_with(
        "GET",
        "https://example.azure.com/connections/test/discovery/v2/attractions"
        "?keyword=rock%20%26%20roll&classificationName=music%2Ccomedy",
        body=None,
    )
    assert result == {"items": []}
