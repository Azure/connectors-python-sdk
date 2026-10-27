# Copyright (c) Microsoft Corporation. All rights reserved.

"""Contract tests for JedoxodatahubClient."""

import azure.connectors.jedoxodatahub as jedoxodatahub_module
from azure.connectors.jedoxodatahub import JedoxodatahubClient
from tests.generated_connector_test_utils import GeneratedConnectorContractTests


OPERATION_CONTRACTS = dict.fromkeys(
    [
        "cube_by_id",
        "database_by_id",
        "dimension_by_id",
        "element_by_id",
        "extract_by_name",
        "get_cube_cell_result_schema",
        "get_extract_rows_result_schema",
        "get_transform_rows_result_schema",
        "get_view_cell_result_schema",
        "integrator_projects_by_id",
        "integrator_projects_by_name",
        "job_by_name",
        "list_cube_cells",
        "list_cubes",
        "list_databases",
        "list_dimensions",
        "list_elements",
        "list_extract_rows",
        "list_extracts",
        "list_integrator_project_groups",
        "list_integrator_projects",
        "list_jobs",
        "list_loads",
        "list_transform_rows",
        "list_transforms",
        "list_view_cells",
        "list_views",
        "load_by_name",
        "run_job",
        "run_job_with_variables",
        "run_load",
        "run_load_with_variables",
        "transform_by_name",
        "view_by_id",
    ],
    ("GET", False),
)


class TestJedoxodatahubClient(GeneratedConnectorContractTests):
    """Test the generated Jedox OData Hub client contract."""

    client_type = JedoxodatahubClient
    connector_module = jedoxodatahub_module
    connector_name = "jedoxodatahub"
    operation_contracts = OPERATION_CONTRACTS
