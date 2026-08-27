# Copyright (c) Microsoft Corporation. All rights reserved.

"""Contract tests for MeetingroommapClient."""

import azure.connectors.meetingroommap as meetingroommap_module
from azure.connectors.meetingroommap import MeetingroommapClient
from tests.generated_connector_test_utils import GeneratedConnectorContractTests


OPERATION_CONTRACTS = {
    "get_custom_locations": ("POST", True),
    "get_custom_locations_by_image_name": ("POST", True),
    "get_categories": ("GET", False),
    "location_details": ("GET", False),
    "search_locations": ("GET", False),
    "get_custom_location_image": ("GET", False),
    "images": ("GET", False),
    "get_meeting_room_image": ("GET", False),
    "next_meetings": ("GET", False),
    "get_meeting_room_details": ("GET", False),
    "get_office_locations": ("GET", False),
    "search_coworkers": ("GET", False),
    "get_office_locations_by_image": ("GET", False),
    "get_room_with_persons_details": ("GET", False),
    "get_office_location_image": ("GET", False),
    "get_rooms": ("GET", False),
    "search_meeting_rooms": ("GET", False),
    "room_lists": ("GET", False),
    "rooms_by_list_address": ("GET", False),
    "get_rooms_by_image_name": ("GET", False),
}


class TestMeetingroommapClient(GeneratedConnectorContractTests):
    """Test the generated Meeting Room Map client contract."""

    client_type = MeetingroommapClient
    connector_module = meetingroommap_module
    connector_name = "meetingroommap"
    operation_contracts = OPERATION_CONTRACTS
