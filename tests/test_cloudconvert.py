# Copyright (c) Microsoft Corporation. All rights reserved.

"""Contract tests for CloudconvertClient."""

import azure.connectors.cloudconvert as cloudconvert_module
from azure.connectors.cloudconvert import CloudconvertClient
from tests.generated_connector_test_utils import GeneratedConnectorContractTests


OPERATION_CONTRACTS = {
    **dict.fromkeys(
        [
            "capture_website",
            "convert_file",
            "merge_files",
            "optimize_file",
        ],
        ("POST", True),
    ),
    **dict.fromkeys(
        [
            "get_capture_website_options",
            "get_convert_options",
            "get_merge_inputs",
            "get_merge_options",
            "get_optimize_options",
        ],
        ("GET", False),
    ),
}


class TestCloudconvertClient(GeneratedConnectorContractTests):
    """Test the generated CloudConvert client contract."""

    client_type = CloudconvertClient
    connector_module = cloudconvert_module
    connector_name = "cloudconvert"
    operation_contracts = OPERATION_CONTRACTS
