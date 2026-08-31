# Copyright (c) Microsoft Corporation. All rights reserved.

"""Contract tests for RepliconClient."""

import azure.connectors.replicon as replicon_module
from azure.connectors.replicon import RepliconClient, TRIGGER_OPERATIONS
from tests.generated_connector_test_utils import GeneratedConnectorContractTests


OPERATION_CONTRACTS = {
    "bulk_get_project_details3": ("POST", True),
    "create_project_or_apply_modifications": ("POST", True),
    "user_list_service_get_data": ("POST", True),
    "get_descendant_task_details": ("POST", True),
    "create_task_hierarchy_or_apply_modifications": ("POST", True),
    "move_task": ("POST", True),
    "task_list_service_get_data": ("POST", True),
    "get_timesheet_summary": ("POST", True),
    "bulk_get_time_entered_summary": ("POST", True),
    "put_project_team_member_assignments": ("POST", True),
    "put_resource_assignments": ("POST", True),
    "get_my_tenant_endpoint_details": ("POST", False),
}


class TestRepliconClient(GeneratedConnectorContractTests):
    """Test the generated Replicon client contract."""

    client_type = RepliconClient
    connector_module = replicon_module
    connector_name = "replicon"
    operation_contracts = OPERATION_CONTRACTS


def test_trigger_operations() -> None:
    """Test the Replicon webhook trigger remains a metadata-only operation."""
    assert set(TRIGGER_OPERATIONS) == {"WebhookSubscriptionsRestAPI"}
