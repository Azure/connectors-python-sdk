# Copyright (c) Microsoft Corporation. All rights reserved.

"""Contract tests for EventbriteClient."""

import azure.connectors.eventbrite as eventbrite_module
from azure.connectors.eventbrite import EventbriteClient, TRIGGER_OPERATIONS
from tests.generated_connector_test_utils import GeneratedConnectorContractTests


OPERATION_CONTRACTS = {
    "create_event": ("POST", False),
    "update_event": ("POST", False),
    "get_organizations": ("GET", False),
    "get_organizers": ("GET", False),
    "get_my_venues": ("GET", False),
    "get_categories": ("GET", False),
    "get_organization_events": ("GET", False),
}


class TestEventbriteClient(GeneratedConnectorContractTests):
    """Test the generated Eventbrite client contract."""

    client_type = EventbriteClient
    connector_module = eventbrite_module
    connector_name = "eventbrite"
    operation_contracts = OPERATION_CONTRACTS


def test_trigger_operations() -> None:
    """Test Eventbrite polling triggers remain metadata-only operations."""
    assert set(TRIGGER_OPERATIONS) == {"OnNewEventV2", "OnOrderChangedV2"}
