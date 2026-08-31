# Copyright (c) Microsoft Corporation. All rights reserved.

"""Contract tests for SeismicplannerClient."""

import azure.connectors.seismicplanner as seismicplanner_module
from azure.connectors.seismicplanner import SeismicplannerClient
from tests.generated_connector_test_utils import GeneratedConnectorContractTests


OPERATION_CONTRACTS = {
    "get_comments": ("GET", False),
    "create_comment": ("POST", True),
    "get_comment": ("GET", False),
    "delete_comment": ("DELETE", False),
    "update_comment": ("PUT", True),
    "get_projects": ("GET", False),
    "delete_projects": ("DELETE", False),
    "create_project": ("POST", True),
    "get_project": ("GET", False),
    "delete_project": ("DELETE", False),
    "update_project": ("PUT", True),
    "get_requests": ("GET", False),
    "delete_requests": ("DELETE", True),
    "create_request": ("POST", True),
    "get_request": ("GET", False),
    "delete_request": ("DELETE", False),
    "update_request": ("PUT", True),
    "get_status_schemas": ("GET", False),
    "get_status_schema": ("GET", False),
    "get_tasks": ("GET", False),
    "create_task": ("POST", True),
    "get_task": ("GET", False),
    "delete_task": ("DELETE", False),
    "update_task": ("PUT", True),
}


class TestSeismicplannerClient(GeneratedConnectorContractTests):
    """Test the generated Seismic Planner client contract."""

    client_type = SeismicplannerClient
    connector_module = seismicplanner_module
    connector_name = "seismicplanner"
    operation_contracts = OPERATION_CONTRACTS
