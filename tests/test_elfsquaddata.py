# Copyright (c) Microsoft Corporation. All rights reserved.

"""Contract tests for ElfsquaddataClient."""

import json
from unittest.mock import AsyncMock, patch

import pytest

import azure.connectors.elfsquaddata as elfsquaddata_module
from azure.connectors.elfsquaddata import ElfsquaddataClient, TRIGGER_OPERATIONS
from tests.conftest import MockResponse
from tests.generated_connector_test_utils import GeneratedConnectorContractTests
from tests.generated_connector_test_utils import collect_operation_result


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
    pageable_item_fields = {"get_entities": "value"}


def test_trigger_operations() -> None:
    """Test Elfsquad Data trigger metadata remains complete."""
    assert set(TRIGGER_OPERATIONS) == {"create_trigger"}


@pytest.mark.asyncio
@pytest.mark.parametrize("entities", [[], [{"id": "product-1", "name": "Widget"}]])
async def test_get_entities_serializes_query_and_response(
    mock_token_provider,
    entities,
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
        return_value=MockResponse(status=200, text=json.dumps({"value": entities})),
    ) as mock_send:
        result = await collect_operation_result(client.get_entities_async(
            entity_name="products",
            top=10,
            select="id,name",
            count=True,
        ))

    mock_send.assert_awaited_once_with(
        "GET",
        "https://example.azure.com/connections/test/data/1/products"
        "?$top=10&$select=id%2Cname&$count=true",
        body=None,
    )
    assert result == entities


@pytest.mark.asyncio
@pytest.mark.parametrize("empty_first_page", [False, True])
async def test_get_entities_follows_odata_pages_and_terminates(
    mock_token_provider, empty_first_page,
) -> None:
    """Test actual Elfsquad item and OData continuation fields, including an empty page."""
    first_items = [] if empty_first_page else [{"id": "product-1", "name": "First"}]
    last_items = [{"id": "product-2", "details": {"name": "Second"}}]
    async with ElfsquaddataClient(
        "https://example.azure.com/connections/test",
        token_provider=mock_token_provider,
    ) as client:
        with patch.object(
            client._http_client,
            "send_async",
            new_callable=AsyncMock,
            side_effect=[
                MockResponse(status=200, text=json.dumps({
                    "value": first_items, "@odata.nextLink": "?$skiptoken=page-2",
                })),
                MockResponse(status=200, text=json.dumps({
                    "value": last_items, "@odata.nextLink": None,
                })),
            ],
        ) as transport:
            entities = [entity async for entity in client.get_entities_async(
                entity_name="products", top=10,
            )]

        assert entities == first_items + last_items
        assert transport.await_count == 2
        assert transport.await_args_list[0].args == (
            "GET", "https://example.azure.com/connections/test/data/1/products?$top=10",
        )
        assert transport.await_args_list[1].args == (
            "GET", "https://example.azure.com/connections/test/data/1/products?$skiptoken=page-2",
        )
        assert all(request.kwargs == {"body": None} for request in transport.await_args_list)


@pytest.mark.asyncio
@pytest.mark.parametrize("status,body", [(200, ""), (200, '{"value": []}'), (204, "")])
async def test_get_entities_empty_response_is_a_single_request(
    mock_token_provider, status, body,
) -> None:
    """Test empty body and empty collection contracts separately from continuation cases."""
    async with ElfsquaddataClient(
        "https://example.azure.com/connections/test",
        token_provider=mock_token_provider,
    ) as client:
        with patch.object(
            client._http_client,
            "send_async",
            new_callable=AsyncMock,
            return_value=MockResponse(status=status, text=body),
        ) as transport:
            entities = [
                entity async for entity in client.get_entities_async(entity_name="products")
            ]

        assert entities == []
        transport.assert_awaited_once_with(
            "GET", "https://example.azure.com/connections/test/data/1/products", body=None,
        )
