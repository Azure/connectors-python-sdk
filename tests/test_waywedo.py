# Copyright (c) Microsoft Corporation. All rights reserved.

"""Contract tests for WaywedoClient."""

import azure.connectors.waywedo as waywedo_module
from azure.connectors.waywedo import TRIGGER_OPERATIONS, WaywedoClient
from tests.generated_connector_test_utils import GeneratedConnectorContractTests


OPERATION_CONTRACTS = {
    "comment_add": ("POST", True),
    "checklist_instances": ("POST", True),
    "checklist_instances_get": ("GET", False),
    "checklist_instances_activity": ("GET", False),
    "find_steps": ("GET", False),
    "checklist_steps_get": ("GET", False),
    "checklist_steps_complete": ("POST", True),
    "collaborators_add": ("POST", True),
    "find_checklist": ("GET", False),
    "procedures_get": ("GET", False),
    "find_checklist_instances": ("GET", False),
    "find_user": ("GET", False),
    "users": ("POST", True),
    "get_all_checklist_instances": ("GET", False),
}


class TestWaywedoClient(GeneratedConnectorContractTests):
    """Test the generated Way We Do client contract."""

    client_type = WaywedoClient
    connector_module = waywedo_module
    connector_name = "waywedo"
    operation_contracts = OPERATION_CONTRACTS


def test_trigger_operations() -> None:
    """Test Way We Do webhook triggers remain metadata-only operations."""
    assert set(TRIGGER_OPERATIONS) == {
        "Checklist_Create_WebHook",
        "Checklist_Step_Completed_WebHook",
        "Finish_Checklist_WebHook",
        "Generate_Acceptance_PDF_WebHook",
        "Invite_Supervisor_WebHook",
        "New_Comment_WebHook",
    }
