# Copyright (c) Microsoft Corporation. All rights reserved.

"""Behavioral contract tests for the complete generated connector catalog."""

from __future__ import annotations

import importlib
import inspect
from pathlib import Path
from types import ModuleType
from typing import Any, get_type_hints
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

import azure.connectors as connectors_package
from azure.connectors.sdk import ConnectorClientBase, ConnectorException
from azure.connectors.sdk.serialization import to_wire
from tests.conftest import MockResponse
from tests.generated_connector_test_utils import (
    get_generated_operations,
    invoke_generated_operation,
)


assert connectors_package.__file__ is not None
CONNECTOR_MODULE_NAMES = [
    path.stem
    for path in sorted(Path(connectors_package.__file__).parent.glob("*.py"))
    if path.name != "__init__.py"
]


def get_generated_client_type(connector_module: ModuleType) -> type[Any]:
    """Return the generated client type defined by a connector module."""
    client_types = [
        value
        for value in vars(connector_module).values()
        if inspect.isclass(value)
        and issubclass(value, ConnectorClientBase)
        and value is not ConnectorClientBase
        and value.__module__ == connector_module.__name__
    ]

    assert len(client_types) == 1, connector_module.__name__
    return client_types[0]


@pytest.mark.parametrize("module_name", CONNECTOR_MODULE_NAMES)
@pytest.mark.asyncio
async def test_all_generated_operations_succeed_with_request_controls(
    module_name: str,
    mock_credential: Any,
) -> None:
    """Exercise every generated operation's successful request contract."""
    connector_module = importlib.import_module(f"azure.connectors.{module_name}")
    client_type = get_generated_client_type(connector_module)

    for operation in sorted(get_generated_operations(client_type)):
        client = client_type(
            "https://example.azure.com/connections/test",
            credential=mock_credential,
        )
        generated_method = getattr(client, f"{operation}_async")
        is_pageable = inspect.isasyncgenfunction(generated_method)
        response_text = (
            '{"value": [{"ok": true}]}' if is_pageable else '{"ok": true}'
        )
        response_hook = MagicMock()

        with patch.object(
            client._http_client,
            "send_async",
            new_callable=AsyncMock,
            return_value=MockResponse(status=200, text=response_text),
        ) as mock_send:
            result = await invoke_generated_operation(
                client,
                operation,
                connector_module,
                include_optional_parameters=True,
                request_controls={
                    "timeout": 5.0,
                    "headers": {"x-test": "value"},
                    "client_request_id": "request-id",
                    "response_hook": response_hook,
                },
            )

        assert mock_send.call_count >= 1, operation
        for call in mock_send.call_args_list:
            method, request_url = call.args[:2]
            assert method, operation
            assert request_url.startswith(
                "https://example.azure.com/connections/test/"
            ), operation
            assert "{" not in request_url and "}" not in request_url, operation
            assert call.kwargs["timeout"] == 5.0, operation
            assert call.kwargs["headers"] == {"x-test": "value"}, operation
            assert call.kwargs["client_request_id"] == "request-id", operation
            assert call.kwargs["response_hook"] is response_hook, operation

            body = call.kwargs["body"]
            if body is not None:
                assert to_wire(body), operation

        return_type = get_type_hints(
            generated_method,
            globalns=vars(connector_module),
        )["return"]
        if return_type is type(None):
            assert result is None, operation
        elif is_pageable:
            assert result == [{"ok": True}], operation
        elif return_type is bytes:
            assert result == b'{"ok": true}', operation
        else:
            assert result == {"ok": True}, operation


@pytest.mark.parametrize("module_name", CONNECTOR_MODULE_NAMES)
@pytest.mark.asyncio
async def test_all_generated_operations_reject_error_responses(
    module_name: str,
    mock_credential: Any,
) -> None:
    """Verify every generated operation raises for a non-success response."""
    connector_module = importlib.import_module(f"azure.connectors.{module_name}")
    client_type = get_generated_client_type(connector_module)

    for operation in sorted(get_generated_operations(client_type)):
        client = client_type(
            "https://example.azure.com/connections/test",
            credential=mock_credential,
        )

        with patch.object(
            client._http_client,
            "send_async",
            new_callable=AsyncMock,
            return_value=MockResponse(status=400, text="bad request"),
        ):
            with pytest.raises(ConnectorException):
                await invoke_generated_operation(
                    client,
                    operation,
                    connector_module,
                    include_optional_parameters=True,
                )
