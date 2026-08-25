# Copyright (c) Microsoft Corporation. All rights reserved.

"""Contract tests for TypeformClient."""

import azure.connectors.typeform as typeform_module
from azure.connectors.typeform import TRIGGER_OPERATIONS, TypeformClient
from tests.generated_connector_test_utils import GeneratedConnectorContractTests


OPERATION_CONTRACTS = {
    "list_forms": ("GET", False),
    "get_schema": ("GET", False),
}


class TestTypeformClient(GeneratedConnectorContractTests):
    """Test the generated Typeform client contract."""

    client_type = TypeformClient
    connector_module = typeform_module
    connector_name = "typeform"
    operation_contracts = OPERATION_CONTRACTS


def test_trigger_operations() -> None:
    """Test the Typeform trigger remains a metadata-only operation."""
    assert set(TRIGGER_OPERATIONS) == {"NewResponseWebhook_V2"}
