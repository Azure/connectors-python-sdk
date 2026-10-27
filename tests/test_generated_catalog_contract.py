# Copyright (c) Microsoft Corporation. All rights reserved.

"""Behavioral contract tests for the complete generated connector catalog."""

from __future__ import annotations

import importlib
import inspect
from pathlib import Path
from types import ModuleType
from typing import Any, get_args, get_origin, get_type_hints
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from azure.core.async_paging import AsyncItemPaged
from azure.core.credentials import AzureKeyCredential
from azure.core.credentials_async import AsyncTokenCredential
from azure.core.paging import ItemPaged
from azure.core.pipeline.transport import AsyncHttpTransport
from azure.core.polling import AsyncLROPoller, LROPoller

import azure.connectors as connectors_package
import azure.connectors.sdk as sdk_package
from azure.connectors.sdk import (
    ConnectorClientBase,
    ConnectorException,
    ConnectorHttpClient,
    ConnectorPollingMethod,
)
from azure.connectors.sdk.serialization import to_wire
from tests.conftest import MockResponse
from tests.generated_connector_test_utils import (
    generated_pager_response_text,
    get_generated_operations,
    invoke_generated_operation,
)


assert connectors_package.__file__ is not None
CONNECTOR_MODULE_NAMES = [
    path.stem
    for path in sorted(Path(connectors_package.__file__).parent.glob("*.py"))
    if not path.name.startswith("_")
]

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

PRIMITIVE_STRING_PAGER_OPERATIONS = [
    ("azuread", "list_member_groups"),
    ("eventhubs", "list_consumer_groups"),
    ("eventhubs", "list_content_types"),
    ("eventhubs", "list_event_hubs"),
    ("eventhubs", "list_partition_keys"),
    ("meetingroommap", "list_categories"),
    ("msgraphgroupsanduser", "list_member_groups"),
    ("onedrive", "list_file_tags"),
    ("servicebus", "list_queues"),
    ("servicebus", "list_session_options"),
    ("servicebus", "list_subscriptions"),
    ("servicebus", "list_system_properties"),
    ("servicebus", "list_topics"),
]

EAGER_MUTATION_OPERATIONS = [
    ("azuread", "check_member_groups"),
    ("docusign", "add_recipient_tabs"),
    ("mq", "delete_all"),
    ("mq", "read_all"),
    ("mq", "receive_all"),
    ("onedrive", "add_file_tag"),
    ("powerbi", "execute_dataset_query"),
    ("replicon", "bulk_get_project_details3"),
    ("replicon", "bulk_get_time_entered_summary"),
    ("replicon", "create_task_hierarchy_or_apply_modifications"),
    ("sendgrid", "add_global_suppression"),
    ("yammer", "post_message"),
]

NOT_FOUND_CONTRACT_OPERATIONS = [
    ("arm", "deployments_delete", "DELETE", True),
    ("zohosign", "delete_document", "PUT", False),
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


def test_package_exports_use_only_the_async_root_runtime() -> None:
    """Expose one async runtime without sync or aio namespace duplicates."""
    connector_directory = Path(connectors_package.__file__).parent
    assert len(CONNECTOR_MODULE_NAMES) == 101
    for directory in (
        connector_directory,
        connector_directory / "sdk",
    ):
        for namespace in ("aio", "sync"):
            assert not (directory / namespace).exists()
            assert not (directory / f"{namespace}.py").exists()

    assert SHARED_PACKAGE_EXPORT_NAMES <= set(connectors_package.__all__)
    assert SHARED_PACKAGE_EXPORT_NAMES <= set(sdk_package.__all__)
    for name in SHARED_PACKAGE_EXPORT_NAMES:
        assert getattr(connectors_package, name) is getattr(sdk_package, name)

    client_names = set(connectors_package.CLIENT_REGISTRY)
    assert len(client_names) == len(CONNECTOR_MODULE_NAMES)
    assert client_names <= set(connectors_package.__all__)
    assert client_names <= set(dir(connectors_package))
    for client_name, module_name in connectors_package.CLIENT_REGISTRY.items():
        connector_module = importlib.import_module(f"azure.connectors.{module_name}")
        assert getattr(connectors_package, client_name) is get_generated_client_type(
            connector_module
        )

    for runtime_type in (ConnectorClientBase, ConnectorHttpClient):
        hints = get_type_hints(runtime_type.__init__)
        assert set(get_args(hints["credential"])) == {
            AsyncTokenCredential, AzureKeyCredential,
        }
        assert set(get_args(hints["transport"])) == {
            AsyncHttpTransport, type(None),
        }
        assert inspect.iscoroutinefunction(runtime_type.close)
        assert not hasattr(runtime_type, "__enter__")
        assert not hasattr(runtime_type, "__exit__")

    assert inspect.iscoroutinefunction(ConnectorClientBase.__aenter__)
    assert inspect.iscoroutinefunction(ConnectorClientBase.__aexit__)
    assert inspect.iscoroutinefunction(ConnectorHttpClient.send)
    assert inspect.iscoroutinefunction(ConnectorPollingMethod.run)
    assert "ConnectorPollingMethod" in sdk_package.__all__


def test_root_client_exports_load_lazily_and_cache_identity(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Resolve a root export once without relying on global test import order."""
    client_name, module_name = next(iter(connectors_package.CLIENT_REGISTRY.items()))
    monkeypatch.delattr(connectors_package, client_name, raising=False)
    assert client_name not in vars(connectors_package)

    with patch.object(
        connectors_package, "import_module", wraps=connectors_package.import_module,
    ) as import_module:
        client_type = getattr(connectors_package, client_name)
        assert getattr(connectors_package, client_name) is client_type

    import_module.assert_called_once_with(f".{module_name}", "azure.connectors")


@pytest.mark.parametrize("module_name", CONNECTOR_MODULE_NAMES)
def test_generated_root_operations_are_async_only(module_name: str) -> None:
    """Keep only lazy async pagers and awaited operations on root clients."""
    connector_module = importlib.import_module(f"azure.connectors.{module_name}")
    client_type = get_generated_client_type(connector_module)
    hints = get_type_hints(client_type.__init__, globalns=vars(connector_module))
    assert set(get_args(hints["credential"])) == {
        AsyncTokenCredential, AzureKeyCredential,
    }
    assert set(get_args(hints["transport"])) == {
        AsyncHttpTransport, type(None),
    }
    operations = get_generated_operations(client_type)
    assert operations, module_name
    assert not any(name.endswith("_async") for name in operations), module_name
    for operation in operations:
        method = getattr(client_type, operation)
        return_type = get_type_hints(method, globalns=vars(connector_module))["return"]
        origin = get_origin(return_type)
        assert origin not in {ItemPaged, LROPoller}, operation
        assert inspect.iscoroutinefunction(method) is (origin is not AsyncItemPaged), operation
        if operation.startswith("begin_"):
            assert origin is AsyncLROPoller, operation
            assert operation.removeprefix("begin_") not in operations, operation
        else:
            assert origin is not AsyncLROPoller, operation


@pytest.mark.parametrize(
    ("module_name", "operation_name"),
    PRIMITIVE_STRING_PAGER_OPERATIONS,
)
def test_primitive_string_collections_use_typed_pagers(
    module_name: str,
    operation_name: str,
) -> None:
    """Preserve primitive item types in generated pager annotations."""
    connector_module = importlib.import_module(f"azure.connectors.{module_name}")
    client_type = get_generated_client_type(connector_module)
    return_type = get_type_hints(
        getattr(client_type, operation_name),
        globalns=vars(connector_module),
    )["return"]

    assert get_origin(return_type) is AsyncItemPaged
    assert get_args(return_type) == (str,)


@pytest.mark.parametrize(
    ("module_name", "operation_name"),
    EAGER_MUTATION_OPERATIONS,
)
def test_mutation_collection_responses_remain_eager(
    module_name: str,
    operation_name: str,
) -> None:
    """Keep bounded mutation responses out of the lazy paging contract."""
    connector_module = importlib.import_module(f"azure.connectors.{module_name}")
    client_type = get_generated_client_type(connector_module)
    return_type = get_type_hints(
        getattr(client_type, operation_name),
        globalns=vars(connector_module),
    )["return"]

    assert get_origin(return_type) not in {ItemPaged, AsyncItemPaged}
    assert inspect.iscoroutinefunction(getattr(client_type, operation_name))


@pytest.mark.parametrize(
    (
        "module_name",
        "operation_name",
        "expected_method",
        "accepts_not_found",
    ),
    NOT_FOUND_CONTRACT_OPERATIONS,
)
@pytest.mark.asyncio
async def test_not_found_contract_follows_http_method(
    module_name: str,
    operation_name: str,
    expected_method: str,
    accepts_not_found: bool,
) -> None:
    """Apply idempotent HTTP 404 handling only to DELETE requests."""
    connector_module = importlib.import_module(f"azure.connectors.{module_name}")
    client_type = get_generated_client_type(connector_module)
    client = client_type(
        "https://example.azure.com/connections/test",
        credential=AzureKeyCredential("test-key"),
    )

    with patch.object(
        client._http_client,
        "send",
        new_callable=AsyncMock,
        return_value=MockResponse(status=404, text="not found"),
    ) as mock_send:
        if accepts_not_found:
            result = await invoke_generated_operation(
                client,
                operation_name,
                connector_module,
            )
            assert result is None
        else:
            with pytest.raises(ConnectorException):
                await invoke_generated_operation(
                    client,
                    operation_name,
                    connector_module,
                )

    assert mock_send.call_args.args[0] == expected_method
    mock_send.assert_awaited_once()


@pytest.mark.parametrize("module_name", CONNECTOR_MODULE_NAMES)
@pytest.mark.asyncio
async def test_all_generated_operations_succeed_with_request_controls(
    module_name: str,
) -> None:
    """Exercise every generated operation's successful request contract."""
    connector_module = importlib.import_module(f"azure.connectors.{module_name}")
    client_type = get_generated_client_type(connector_module)

    for operation in sorted(get_generated_operations(client_type)):
        client = client_type(
            "https://example.azure.com/connections/test",
            credential=AzureKeyCredential("test-key"),
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

        assert mock_send.await_count == mock_send.call_count == 1, operation
        for call in mock_send.await_args_list:
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
async def test_all_generated_operations_reject_error_responses(
    module_name: str,
) -> None:
    """Verify every generated operation raises for a non-success response."""
    connector_module = importlib.import_module(f"azure.connectors.{module_name}")
    client_type = get_generated_client_type(connector_module)

    for operation in sorted(get_generated_operations(client_type)):
        client = client_type(
            "https://example.azure.com/connections/test",
            credential=AzureKeyCredential("test-key"),
        )

        with patch.object(
            client._http_client,
            "send",
            new_callable=AsyncMock,
            return_value=MockResponse(status=400, text="bad request"),
        ) as mock_send, pytest.raises(ConnectorException):
            await invoke_generated_operation(
                client,
                operation,
                connector_module,
                include_optional_parameters=True,
            )

        mock_send.assert_awaited_once()
