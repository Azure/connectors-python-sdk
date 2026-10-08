# Copyright (c) Microsoft Corporation. All rights reserved.

"""Contract tests for SeismicplannerClient."""

from typing import Any, Dict, Optional, get_type_hints
from unittest.mock import AsyncMock, patch

import pytest

import azure.connectors.seismicplanner as seismicplanner_module
from azure.connectors.seismicplanner import (
    CustomPropertyDataDisplay,
    CustomPropertyValues,
    SeismicplannerClient,
)
from tests.conftest import MockResponse
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

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "identifiers,expected_query",
        [
            (["folder/a", "folder/b"], "ids=folder%2Fa%2Cfolder%2Fb"),
            ("folder/a,folder/b", "ids=folder%2Fa%2Cfolder%2Fb"),
            ([], "ids="),
            (None, None),
        ],
    )
    async def test_get_requests_encodes_csv_and_compatibility_values(
        self, mock_token_provider: Any, identifiers: Any, expected_query: str | None,
    ) -> None:
        """Test generated CSV and legacy scalar-fallback paths encode complete query values."""
        async with SeismicplannerClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider,
        ) as client:
            with patch.object(
                client._http_client,
                "send_async",
                new_callable=AsyncMock,
                return_value=MockResponse(status=200, text='{"value": []}'),
            ) as transport:
                await client.get_requests_async(space_id="space-id", ids=identifiers)

            transport.assert_awaited_once()
            method, request_url = transport.await_args.args
            assert method == "GET"
            if expected_query is None:
                assert "ids=" not in request_url
            else:
                assert request_url.endswith("?" + expected_query)
                assert "folder/" not in request_url

    def test_localizations_use_typed_map_values(self) -> None:
        """Test that localization dictionary values retain their Swagger model type."""
        type_hints = get_type_hints(CustomPropertyValues)
        model = CustomPropertyValues(
            localizations={"en-US": CustomPropertyDataDisplay(name="English")}
        )

        assert type_hints["localizations"] == Optional[
            Dict[str, CustomPropertyDataDisplay]
        ]
        assert model.localizations is not None
        assert model.localizations["en-US"].name == "English"
