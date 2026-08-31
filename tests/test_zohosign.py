# Copyright (c) Microsoft Corporation. All rights reserved.

"""Contract tests for ZohosignClient."""

from typing import get_type_hints

import azure.connectors.zohosign as zohosign_module
from azure.connectors.zohosign import ZohosignClient, TRIGGER_OPERATIONS
from tests.generated_connector_test_utils import GeneratedConnectorContractTests


OPERATION_CONTRACTS = {
    "delete_document": ("PUT", False),
    "download_completion_certificate": ("GET", False),
    "download_document": ("GET", False),
    "download_file": ("GET", False),
    "get_document": ("GET", False),
    "get_form_data": ("GET", False),
    "get_template_details": ("GET", False),
    "get_templates": ("GET", False),
    "invoke_api": ("POST", True),
    "recall_document": ("POST", False),
    "remind_document_recipients": ("POST", False),
    "send_sign_request": ("POST", False),
    "update_document": ("PUT", True),
}


class TestZohosignClient(GeneratedConnectorContractTests):
    """Test the generated Zoho Sign client contract."""

    client_type = ZohosignClient
    connector_module = zohosign_module
    connector_name = "zohosign"
    operation_contracts = OPERATION_CONTRACTS


def test_trigger_operations() -> None:
    """Test the Zoho Sign trigger metadata remains complete."""
    assert set(TRIGGER_OPERATIONS) == {"zoho-sign-triggers"}


def test_document_identifiers_use_integer_annotations() -> None:
    """Test Zoho Sign document identifiers preserve Swagger integer types."""
    integer_request_id_operations = [
        "delete_document",
        "download_completion_certificate",
        "download_document",
        "download_file",
        "get_document",
        "get_form_data",
        "recall_document",
        "remind_document_recipients",
    ]

    for operation in integer_request_id_operations:
        type_hints = get_type_hints(getattr(ZohosignClient, f"{operation}_async"))
        assert type_hints["request_id"] is int, operation

    download_file_hints = get_type_hints(ZohosignClient.download_file_async)
    assert download_file_hints["document_id"] is int

    for operation in ["send_sign_request", "update_document"]:
        type_hints = get_type_hints(getattr(ZohosignClient, f"{operation}_async"))
        assert type_hints["request_id"] is str, operation


def test_multipart_create_document_is_not_generated() -> None:
    """Test the unsupported multipart operation is excluded."""
    assert not hasattr(ZohosignClient, "create_document_async")
