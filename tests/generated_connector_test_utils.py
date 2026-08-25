# Copyright (c) Microsoft Corporation. All rights reserved.

"""Shared helpers for generated connector contract tests."""

from __future__ import annotations

import dataclasses
import inspect
from types import ModuleType
from typing import Any, get_origin, get_type_hints
from unittest.mock import AsyncMock, patch

import pytest

from azure.connectors.sdk import ConnectorException, ManagedIdentityTokenProvider
from tests.conftest import MockResponse


def get_generated_operations(client_type: type[Any]) -> set[str]:
    """Return generated async operation names without their async suffix."""
    return {
        name.removesuffix("_async")
        for name in dir(client_type)
        if name.endswith("_async")
        and inspect.iscoroutinefunction(getattr(client_type, name))
    }


async def invoke_generated_operation(
    client: Any,
    operation: str,
    module: ModuleType,
) -> Any:
    """Invoke a generated operation with representative required arguments."""
    method = getattr(client, f"{operation}_async")
    type_hints = get_type_hints(method, globalns=vars(module))
    arguments = {
        parameter.name: _representative_value(type_hints[parameter.name])
        for parameter in inspect.signature(method).parameters.values()
        if parameter.default is inspect.Parameter.empty
    }
    return await method(**arguments)


class GeneratedConnectorContractTests:
    """Shared contract tests for a generated connector client."""

    client_type: type[Any]
    connector_module: ModuleType
    connector_name: str
    operation_contracts: dict[str, tuple[str, bool]]

    def test_init_with_defaults(self) -> None:
        """Test initialization with default authentication."""
        client = self.client_type("https://example.azure.com/connections/test/")

        assert client._connection_runtime_url == "https://example.azure.com/connections/test"
        assert client.connector_name == self.connector_name
        assert isinstance(client._http_client._token_provider, ManagedIdentityTokenProvider)

    @pytest.mark.parametrize("connection_runtime_url", ["", None])
    def test_init_with_invalid_url_raises_error(self, connection_runtime_url: str | None) -> None:
        """Test invalid runtime URLs are rejected."""
        with pytest.raises(ValueError, match="connection_runtime_url cannot be None or empty"):
            self.client_type(connection_runtime_url)

    @pytest.mark.asyncio
    async def test_context_manager(self, mock_token_provider: Any) -> None:
        """Test async context manager cleanup."""
        with patch.object(self.client_type, "close", new_callable=AsyncMock) as mock_close:
            async with self.client_type(
                "https://example.azure.com/connections/test",
                token_provider=mock_token_provider,
            ) as client:
                assert isinstance(client, self.client_type)

        mock_close.assert_called_once()

    def test_all_generated_operations_are_covered(self) -> None:
        """Test the expected generated operation surface."""
        assert get_generated_operations(self.client_type) == set(self.operation_contracts)

    @pytest.mark.asyncio
    async def test_generated_operation_success_contracts(self, mock_token_provider: Any) -> None:
        """Test every generated operation's successful HTTP contract."""
        for operation, (expected_method, expects_body) in self.operation_contracts.items():
            client = self.client_type(
                "https://example.azure.com/connections/test",
                token_provider=mock_token_provider,
            )

            with patch.object(
                client._http_client,
                "send_async",
                new_callable=AsyncMock,
                return_value=MockResponse(status=200, text='{"ok": true}'),
            ) as mock_send:
                await invoke_generated_operation(client, operation, self.connector_module)

            method, url = mock_send.call_args.args[:2]
            assert method == expected_method, operation
            assert url.startswith("https://example.azure.com/connections/test"), operation
            assert (mock_send.call_args.kwargs["body"] is not None) is expects_body, operation

    @pytest.mark.asyncio
    async def test_non_success_responses_raise_exception(self, mock_token_provider: Any) -> None:
        """Test every generated operation raises for a non-success response."""
        for operation in self.operation_contracts:
            client = self.client_type(
                "https://example.azure.com/connections/test",
                token_provider=mock_token_provider,
            )

            with patch.object(
                client._http_client,
                "send_async",
                new_callable=AsyncMock,
                return_value=MockResponse(status=400, text="bad request"),
            ):
                with pytest.raises(ConnectorException):
                    await invoke_generated_operation(client, operation, self.connector_module)


def _representative_value(annotation: Any) -> Any:
    """Create a representative value for a required generated parameter."""
    if annotation is str:
        return "value"

    if annotation is bytes:
        return b"payload"

    if get_origin(annotation) is list:
        return []

    if inspect.isclass(annotation) and dataclasses.is_dataclass(annotation):
        return annotation()

    raise AssertionError(f"Unsupported generated parameter type '{annotation}'.")
