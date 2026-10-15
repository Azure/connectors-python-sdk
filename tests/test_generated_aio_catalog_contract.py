# Copyright (c) Microsoft Corporation. All rights reserved.

"""Behavioral contract tests for the asynchronous generated catalog."""

from __future__ import annotations

import importlib
import inspect
from pathlib import Path
from types import ModuleType
from typing import Any, get_args, get_origin, get_type_hints
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from azure.core.async_paging import AsyncItemPaged
from azure.core.paging import ItemPaged
from azure.core.polling import AsyncLROPoller, LROPoller

import azure.connectors as connectors_package
import azure.connectors.aio as aio_package
from azure.connectors.sdk import ConnectorClientBase as SyncConnectorClientBase
from azure.connectors.sdk.aio import ConnectorClientBase
from azure.connectors.sdk.exceptions import ConnectorException
from azure.connectors.sdk.serialization import to_wire
from tests.conftest import MockResponse
from tests.generated_connector_test_utils import (
    _representative_value,
    generated_pager_response_text,
    get_generated_operations,
)


assert connectors_package.__file__ is not None
AIO_MODULE_DIRECTORY = Path(connectors_package.__file__).parent / "aio"
CONNECTOR_MODULE_NAMES = [
    path.stem
    for path in sorted(AIO_MODULE_DIRECTORY.glob("*.py"))
    if path.name != "__init__.py"
]
REQUEST_CONTROL_PARAMETER_NAMES = {
    "client_request_id",
    "headers",
    "response_hook",
    "timeout",
}
SHARED_PACKAGE_EXPORT_NAMES = {
    "ConnectorClientBase",
    "ConnectorException",
    "ConnectorHttpClient",
    "ConnectorResponse",
    "ConnectorResponseHook",
    "ConnectorResponseSnapshot",
    "TriggerCallbackBody",
    "TriggerCallbackPayload",
}


def test_package_roots_export_generated_clients_lazily() -> None:
    """Expose generated clients without importing their modules eagerly."""
    client_names = set(connectors_package.CLIENT_REGISTRY)

    assert SHARED_PACKAGE_EXPORT_NAMES <= set(connectors_package.__all__)
    assert client_names <= set(connectors_package.__all__)
    assert client_names <= set(aio_package.__all__)
    assert client_names <= set(dir(connectors_package))
    assert client_names <= set(dir(aio_package))
    assert not (client_names & vars(connectors_package).keys())
    assert not (client_names & vars(aio_package).keys())


def get_generated_client_type(connector_module: ModuleType) -> type[Any]:
    """Return the asynchronous client type defined by a connector module."""
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


async def invoke_generated_operation(
    client: Any,
    operation: str,
    module: ModuleType,
    *,
    include_optional_parameters: bool = False,
    request_controls: dict[str, Any] | None = None,
) -> Any:
    """Invoke an asynchronous generated operation with representative values."""
    method = getattr(client, operation)
    type_hints = get_type_hints(method, globalns=vars(module))
    arguments = {
        parameter.name: _representative_value(type_hints[parameter.name])
        for parameter in inspect.signature(method).parameters.values()
        if parameter.name not in REQUEST_CONTROL_PARAMETER_NAMES
        and (
            include_optional_parameters
            or parameter.default is inspect.Parameter.empty
        )
    }
    arguments.update(request_controls or {})
    result = method(**arguments)
    if isinstance(result, AsyncItemPaged):
        return [item async for item in result]

    awaited_result = await result
    if isinstance(awaited_result, AsyncLROPoller):
        return await awaited_result.result()

    return awaited_result


@pytest.mark.parametrize("module_name", CONNECTOR_MODULE_NAMES)
def test_root_and_aio_operation_surfaces_match(module_name: str) -> None:
    """Keep root and aio class, operation, and signature identities aligned."""
    root_module = importlib.import_module(f"azure.connectors.{module_name}")
    aio_module = importlib.import_module(f"azure.connectors.aio.{module_name}")
    root_client = next(
        value
        for value in vars(root_module).values()
        if inspect.isclass(value)
        and issubclass(value, SyncConnectorClientBase)
        and value is not SyncConnectorClientBase
        and value.__module__ == root_module.__name__
    )
    aio_client = get_generated_client_type(aio_module)

    assert aio_client.__name__ == root_client.__name__
    operation_names = get_generated_operations(root_client)
    assert get_generated_operations(aio_client) == operation_names
    assert not any(name.endswith("_async") for name in operation_names)

    for operation_name in operation_names:
        root_method = getattr(root_client, operation_name)
        aio_method = getattr(aio_client, operation_name)
        root_signature = inspect.signature(root_method)
        aio_signature = inspect.signature(aio_method)
        assert list(root_signature.parameters.values()) == list(
            aio_signature.parameters.values()
        ), operation_name

        root_return_type = get_type_hints(
            root_method,
            globalns=vars(root_module),
        )["return"]
        aio_return_type = get_type_hints(
            aio_method,
            globalns=vars(aio_module),
        )["return"]
        is_pageable = get_origin(root_return_type) is ItemPaged
        is_long_running = get_origin(root_return_type) is LROPoller
        if is_pageable:
            assert get_origin(aio_return_type) is AsyncItemPaged, operation_name
            assert get_args(aio_return_type) == get_args(
                root_return_type
            ), operation_name
        elif is_long_running:
            assert get_origin(aio_return_type) is AsyncLROPoller, operation_name
            assert get_args(aio_return_type) == get_args(
                root_return_type
            ), operation_name
        else:
            assert aio_return_type == root_return_type, operation_name

        assert not inspect.iscoroutinefunction(root_method), operation_name
        assert inspect.iscoroutinefunction(aio_method) == (
            not is_pageable
        ), operation_name


@pytest.mark.parametrize("module_name", CONNECTOR_MODULE_NAMES)
@pytest.mark.asyncio
async def test_all_aio_operations_succeed_with_request_controls(
    module_name: str,
    mock_credential: Any,
) -> None:
    """Exercise every asynchronous operation's successful request contract."""
    connector_module = importlib.import_module(
        f"azure.connectors.aio.{module_name}"
    )
    client_type = get_generated_client_type(connector_module)

    for operation in sorted(get_generated_operations(client_type)):
        client = client_type(
            "https://example.azure.com/connections/test",
            credential=mock_credential,
        )
        generated_method = getattr(client, operation)
        return_type = get_type_hints(
            generated_method,
            globalns=vars(connector_module),
        )["return"]
        is_pageable = get_origin(return_type) is AsyncItemPaged
        result_type = (
            get_args(return_type)[0]
            if get_origin(return_type) is AsyncLROPoller
            else return_type
        )
        response_text = '{"ok": true}'
        if is_pageable:
            response_text = generated_pager_response_text(generated_method)
        response_hook = MagicMock()

        with patch.object(
            client._http_client,
            "send",
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
            expected_headers = {"x-test": "value"}
            if "match_condition" in inspect.signature(generated_method).parameters:
                expected_headers["If-Match"] = "*"
            assert call.kwargs["headers"] == expected_headers, operation
            assert call.kwargs["client_request_id"] == "request-id", operation
            assert call.kwargs["response_hook"] is response_hook, operation
            body = call.kwargs["body"]
            if body is not None:
                assert to_wire(body) is not None, operation

        if result_type is type(None):
            assert result is None, operation
        elif is_pageable:
            assert result == [{"ok": True}], operation
        elif result_type is bytes:
            assert result == b'{"ok": true}', operation
        else:
            assert result == {"ok": True}, operation


@pytest.mark.parametrize("module_name", CONNECTOR_MODULE_NAMES)
@pytest.mark.asyncio
async def test_all_aio_operations_reject_error_responses(
    module_name: str,
    mock_credential: Any,
) -> None:
    """Verify every asynchronous operation raises for an error response."""
    connector_module = importlib.import_module(
        f"azure.connectors.aio.{module_name}"
    )
    client_type = get_generated_client_type(connector_module)

    for operation in sorted(get_generated_operations(client_type)):
        client = client_type(
            "https://example.azure.com/connections/test",
            credential=mock_credential,
        )

        with patch.object(
            client._http_client,
            "send",
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
