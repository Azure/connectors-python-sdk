# Copyright (c) Microsoft Corporation. All rights reserved.

"""Contract tests for ElfsquaddataClient."""

from unittest.mock import AsyncMock, patch

import pytest

import azure.connectors.elfsquaddata as elfsquaddata_module
from azure.connectors.elfsquaddata import ElfsquaddataClient, TRIGGER_OPERATIONS
from tests.conftest import MockResponse
from tests.generated_connector_test_utils import GeneratedConnectorContractTests


OPERATION_CONTRACTS = {
    "delete_entity_by_id": ("DELETE", False),
    **dict.fromkeys(
        [
            "get_entities",
            "get_entity_by_id",
            "get_function_definition",
            "get_functions",
            "get_schema",
            "get_schemas",
            "get_trigger_schema",
            "get_triggers",
        ],
        ("GET", False),
    ),
    "post_entity_by_id": ("POST", True),
    **dict.fromkeys(
        [
            "invoke_function",
            "put_entity_by_id",
        ],
        ("PUT", True),
    ),
}


class TestElfsquaddataClient(GeneratedConnectorContractTests):
    """Test the generated Elfsquad Data client contract."""

    client_type = ElfsquaddataClient
    connector_module = elfsquaddata_module
    connector_name = "elfsquaddata"
    operation_contracts = OPERATION_CONTRACTS


def test_trigger_operations() -> None:
    """Test Elfsquad Data trigger metadata remains complete."""
    assert set(TRIGGER_OPERATIONS) == {"create_trigger"}


@pytest.mark.asyncio
async def test_get_entities_serializes_query_and_response(
    mock_token_provider,
) -> None:
    """Test entity query serialization and response deserialization."""
    client = ElfsquaddataClient(
        "https://example.azure.com/connections/test",
        token_provider=mock_token_provider,
    )

    with patch.object(
        client._http_client,
        "send_async",
        new_callable=AsyncMock,
        return_value=MockResponse(status=200, text='{"value": []}'),
    ) as mock_send:
        result = await client.get_entities_async(
            entity_name="products",
            top=10,
            select="id,name",
            count=True,
        )

    mock_send.assert_awaited_once_with(
        "GET",
        "https://example.azure.com/connections/test/data/1/products"
        "?$top=10&$select=id%2Cname&$count=true",
        body=None,
    )
    assert result == {"value": []}
