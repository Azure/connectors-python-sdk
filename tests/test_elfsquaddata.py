# Copyright (c) Microsoft Corporation. All rights reserved.

"""Contract tests for ElfsquaddataClient."""

import azure.connectors.elfsquaddata as elfsquaddata_module
from azure.connectors.elfsquaddata import ElfsquaddataClient, TRIGGER_OPERATIONS
from tests.generated_connector_test_utils import GeneratedConnectorContractTests


OPERATION_CONTRACTS = {
    "delete_entity_by_id": ("DELETE", False),
    **dict.fromkeys(
        [
            "get_entities",
            "get_entity_by_id",
            "get_function_definition",
            "get_functions",
            "get_schema",
            "get_schemas",
            "get_trigger_schema",
            "get_triggers",
        ],
        ("GET", False),
    ),
    "post_entity_by_id": ("POST", True),
    **dict.fromkeys(
        [
            "invoke_function",
            "put_entity_by_id",
        ],
        ("PUT", True),
    ),
}


class TestElfsquaddataClient(GeneratedConnectorContractTests):
    """Test the generated Elfsquad Data client contract."""

    client_type = ElfsquaddataClient
    connector_module = elfsquaddata_module
    connector_name = "elfsquaddata"
    operation_contracts = OPERATION_CONTRACTS


def test_trigger_operations() -> None:
    """Test Elfsquad Data trigger metadata remains complete."""
    assert set(TRIGGER_OPERATIONS) == {"create_trigger"}
