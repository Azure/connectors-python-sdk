# ------------------------------------------------------------
# Copyright (c) Microsoft Corporation.  All rights reserved.
# ------------------------------------------------------------

"""Behavioral tests for generated conditional request controls."""

from __future__ import annotations

from typing import Any
from unittest.mock import AsyncMock, patch

import pytest
from azure.core import MatchConditions
from azure.core.credentials import AzureKeyCredential
from azure.connectors.azuretables import AzuretablesClient

from tests.conftest import MockResponse


OPERATIONS = ("delete_entity", "merge_entity", "replace_entity")


def create_client() -> AzuretablesClient:
    """Create the generated async root client."""
    return AzuretablesClient(
        "https://example.azure.com/connections/test",
        credential=AzureKeyCredential("test-key"),
    )


async def invoke_operation(
    client: AzuretablesClient,
    operation_name: str,
    **controls: Any,
) -> None:
    """Invoke one generated entity operation with shared path arguments."""
    arguments: dict[str, Any] = {
        "storage_account_name": "sample-account",
        "table_name": "sample-table",
        "partition_key": "sample-partition",
        "row_key": "sample-row",
        **controls,
    }
    if operation_name in {"merge_entity", "replace_entity"}:
        arguments["input"] = {"Name": "sample"}
    await getattr(client, operation_name)(**arguments)


@pytest.mark.parametrize("operation_name", OPERATIONS)
@pytest.mark.asyncio
async def test_header_only_etag_preserves_value_and_casing(
    operation_name: str,
) -> None:
    """Preserve caller If-Match headers case-insensitively when controls are omitted."""
    client = create_client()
    send = AsyncMock(return_value=MockResponse(status=204, text=""))

    with patch.object(client._http_client, "send", new=send):
        await invoke_operation(
            client,
            operation_name,
            headers={"if-MATCH": "caller-etag", "x-sample": "value"},
        )

    assert send.call_args.kwargs["headers"] == {
        "if-MATCH": "caller-etag",
        "x-sample": "value",
    }
    send.assert_awaited_once()


@pytest.mark.parametrize(
    "operation_name,expected_headers",
    [
        ("delete_entity", None),
        ("merge_entity", {"If-Match": "*"}),
        ("replace_entity", {"If-Match": "*"}),
    ],
)
@pytest.mark.asyncio
async def test_omitted_controls_apply_required_or_authored_default(
    operation_name: str,
    expected_headers: dict[str, str] | None,
) -> None:
    """Apply wildcard fallback or the authored default only when no header exists."""
    client = create_client()
    send = AsyncMock(return_value=MockResponse(status=204, text=""))

    with patch.object(client._http_client, "send", new=send):
        await invoke_operation(client, operation_name)

    assert send.call_args.kwargs["headers"] == expected_headers
    send.assert_awaited_once()


@pytest.mark.parametrize("operation_name", OPERATIONS)
@pytest.mark.asyncio
async def test_explicit_etag_overrides_caller_header(
    operation_name: str,
) -> None:
    """Give an explicit typed ETag precedence over an existing caller header."""
    client = create_client()
    send = AsyncMock(return_value=MockResponse(status=204, text=""))

    with patch.object(client._http_client, "send", new=send):
        await invoke_operation(
            client,
            operation_name,
            etag="explicit-etag",
            headers={"if-match": "caller-etag", "x-sample": "value"},
        )

    assert send.call_args.kwargs["headers"] == {
        "x-sample": "value",
        "If-Match": "explicit-etag",
    }
    send.assert_awaited_once()


@pytest.mark.parametrize("operation_name", OPERATIONS)
@pytest.mark.asyncio
async def test_if_not_modified_requires_explicit_etag(
    operation_name: str,
) -> None:
    """Reject IfNotModified without an explicit ETag before dispatch."""
    client = create_client()
    send = AsyncMock()

    with patch.object(client._http_client, "send", new=send):
        with pytest.raises(
            ValueError,
            match=r"etag is required for MatchConditions\.IfNotModified\.",
        ):
            await invoke_operation(
                client,
                operation_name,
                match_condition=MatchConditions.IfNotModified,
            )

    send.assert_not_called()
    send.assert_not_awaited()


@pytest.mark.parametrize("operation_name", OPERATIONS)
@pytest.mark.asyncio
async def test_unconditionally_with_explicit_etag_emits_wildcard(
    operation_name: str,
) -> None:
    """Preserve Unconditionally semantics when an explicit ETag is also supplied."""
    client = create_client()
    send = AsyncMock(return_value=MockResponse(status=204, text=""))

    with patch.object(client._http_client, "send", new=send):
        await invoke_operation(
            client,
            operation_name,
            etag="explicit-etag",
            match_condition=MatchConditions.Unconditionally,
            headers={"if-match": "caller-etag"},
        )

    assert send.call_args.kwargs["headers"] == {"If-Match": "*"}
    send.assert_awaited_once()
