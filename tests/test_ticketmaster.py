# Copyright (c) Microsoft Corporation. All rights reserved.

"""Contract tests for TicketmasterClient."""

import azure.connectors.ticketmaster as ticketmaster_module
from azure.connectors.ticketmaster import TicketmasterClient
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
