# Copyright (c) Microsoft Corporation. All rights reserved.

"""Contract tests for FormstackFormsClient."""

import azure.connectors.formstack_forms as formstackforms_module
from azure.connectors.formstack_forms import FormstackFormsClient
from azure.connectors.formstack_forms import TRIGGER_OPERATIONS
from tests.generated_connector_test_utils import GeneratedConnectorContractTests


OPERATION_CONTRACTS = {
    "get_available_forms": ("GET", False),
    "get_form_schema": ("GET", False),
}


class TestFormstackFormsClient(GeneratedConnectorContractTests):
    """Test the generated Formstack Forms client contract."""

    client_type = FormstackFormsClient
    connector_module = formstackforms_module
    connector_name = "formstackforms"
    operation_contracts = OPERATION_CONTRACTS


def test_trigger_operations() -> None:
    """Test the Formstack Forms trigger remains a metadata-only operation."""
    assert set(TRIGGER_OPERATIONS) == {"FormstackFormSubmitted"}
