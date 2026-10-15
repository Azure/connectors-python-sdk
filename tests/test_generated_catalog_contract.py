# Copyright (c) Microsoft Corporation. All rights reserved.

"""Behavioral contract tests for the complete generated connector catalog."""

from __future__ import annotations

import importlib
import inspect
from pathlib import Path
from types import ModuleType
from typing import Any, get_args, get_origin, get_type_hints
from unittest.mock import MagicMock, patch

import pytest
from azure.core.credentials import AzureKeyCredential
from azure.core.paging import ItemPaged
from azure.core.polling import LROPoller

import azure.connectors as connectors_package
from azure.connectors.sdk import ConnectorClientBase, ConnectorException
from azure.connectors.sdk.serialization import to_wire
from tests.conftest import MockResponse
from tests.generated_connector_test_utils import (
    generated_pager_response_text,
    get_generated_operations,
    invoke_sync_generated_operation,
)


assert connectors_package.__file__ is not None
CONNECTOR_MODULE_NAMES = [
    path.stem
    for path in sorted(Path(connectors_package.__file__).parent.glob("*.py"))
    if not path.name.startswith("_")
]

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

    assert get_origin(return_type) is ItemPaged
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

    assert get_origin(return_type) is not ItemPaged


@pytest.mark.parametrize("module_name", CONNECTOR_MODULE_NAMES)
def test_all_generated_operations_succeed_with_request_controls(
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
        is_pageable = get_origin(return_type) is ItemPaged
        result_type = (
            get_args(return_type)[0]
            if get_origin(return_type) is LROPoller
            else return_type
        )
        response_text = '{"ok": true}'
        if is_pageable:
            response_text = generated_pager_response_text(generated_method)
        response_hook = MagicMock()

        with patch.object(
            client._http_client,
            "send",
            new_callable=MagicMock,
            return_value=MockResponse(status=200, text=response_text),
        ) as mock_send:
            result = invoke_sync_generated_operation(
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
def test_all_generated_operations_reject_error_responses(
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
            new_callable=MagicMock,
            return_value=MockResponse(status=400, text="bad request"),
        ):
            with pytest.raises(ConnectorException):
                invoke_sync_generated_operation(
                    client,
                    operation,
                    connector_module,
                    include_optional_parameters=True,
                )
