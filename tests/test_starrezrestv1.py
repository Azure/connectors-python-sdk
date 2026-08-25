# Copyright (c) Microsoft Corporation. All rights reserved.

"""Contract tests for Starrezrestv1Client."""

import azure.connectors.starrezrestv1 as starrezrestv1_module
from azure.connectors.starrezrestv1 import Starrezrestv1Client
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
