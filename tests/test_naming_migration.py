# ------------------------------------------------------------
# Copyright (c) Microsoft Corporation.  All rights reserved.
# ------------------------------------------------------------

"""Guard canonical imports without changing managed-API or model wire names."""

from __future__ import annotations

from dataclasses import fields
from importlib import import_module

import pytest
from azure.core.credentials import AzureKeyCredential

import azure.connectors as connectors
from azure.connectors.cloudmersive_convert import RemoveWhiteSpaceFromTextRequest
from azure.connectors.sdk.serialization import to_wire


@pytest.mark.parametrize(
    ("module_name", "client_name", "api_name"),
    [
        ("azure_ad", "AzureADClient", "azuread"),
        ("azure_iot_central", "AzureIoTCentralClient", "azureiotcentral"),
        ("data_flows_sms", "DataFlowsSmsClient", "dataflowssms"),
        ("jedox_odata_hub", "JedoxODataHubClient", "jedoxodatahub"),
        ("ms_graph_groups_and_users", "MSGraphGroupsAndUsersClient", "msgraphgroupsanduser"),
        ("service_now", "ServiceNowClient", "service-now"),
    ],
)
def test_canonical_import_keeps_raw_api_identity(
    module_name: str, client_name: str, api_name: str,
) -> None:
    """Direct imports and lazy exports must agree, without rewriting connector IDs."""
    module = import_module(f"azure.connectors.{module_name}")
    client_type = getattr(module, client_name)
    assert connectors.CLIENT_REGISTRY[client_name] == module_name
    assert getattr(connectors, client_name) is client_type
    client = client_type(
        "https://example.test/connections/test", AzureKeyCredential("test-key"),
    )
    assert client.connector_name == api_name


def test_renamed_model_attribute_retains_original_wire_field() -> None:
    """Changed Python word boundaries must not alter serialized Swagger keys."""
    model = RemoveWhiteSpaceFromTextRequest(text_containing_whitespace="hello world")
    attribute = next(
        field for field in fields(model) if field.name == "text_containing_whitespace"
    )
    assert attribute.metadata["wire_name"] == "TextContainingWhitespace"
    assert to_wire(model) == {"TextContainingWhitespace": "hello world"}
