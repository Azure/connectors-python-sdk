# Copyright (c) Microsoft Corporation. All rights reserved.

"""Contract tests for JedoxodatahubClient."""

import azure.connectors.jedoxodatahub as jedoxodatahub_module
from azure.connectors.jedoxodatahub import JedoxodatahubClient
from tests.generated_connector_test_utils import GeneratedConnectorContractTests


OPERATION_CONTRACTS = dict.fromkeys(
    [
        "cube_by_id",
        "cube_cells",
        "cubes",
        "database_by_id",
        "databases",
        "dimension_by_id",
        "dimensions",
        "element_by_id",
        "elements",
        "extract_by_name",
        "extract_rows",
        "extracts",
        "get_cube_cell_result_schema",
        "get_extract_rows_result_schema",
        "get_transform_rows_result_schema",
        "get_view_cell_result_schema",
        "integrator_project_groups",
        "integrator_projects",
        "integrator_projects_by_id",
        "integrator_projects_by_name",
        "job_by_name",
        "jobs",
        "load_by_name",
        "loads",
        "run_job",
        "run_job_with_variables",
        "run_load",
        "run_load_with_variables",
        "transform_by_name",
        "transform_rows",
        "transforms",
        "view_by_id",
        "view_cells",
        "views",
    ],
    ("GET", False),
)


class TestJedoxodatahubClient(GeneratedConnectorContractTests):
    """Test the generated Jedox OData Hub client contract."""

    client_type = JedoxodatahubClient
    connector_module = jedoxodatahub_module
    connector_name = "jedoxodatahub"
    operation_contracts = OPERATION_CONTRACTS
