# Copyright (c) Microsoft Corporation. All rights reserved.

"""Unit tests for connector long-running operation polling."""

from datetime import datetime, timedelta, timezone
from email.utils import format_datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from azure.core.polling import AsyncLROPoller, LROPoller

from azure.connectors.sdk.aio.polling import (
    ConnectorPollingMethod as AsyncConnectorPollingMethod,
)
from azure.connectors.sdk._polling import (
    get_retry_after_seconds,
    resolve_polling_url,
)
from azure.connectors.sdk.exceptions import ConnectorException
from azure.connectors.sdk.polling import ConnectorPollingMethod
from azure.connectors.sdk.response import ConnectorResponseSnapshot


def create_response(
    status: int,
    headers: dict[str, str] | None = None,
    text: str = "",
) -> ConnectorResponseSnapshot:
    """Create an immutable connector response for polling tests."""
    return ConnectorResponseSnapshot(
        status=status,
        headers=headers or {},
        text=text,
        content=text.encode("utf-8"),
    )


def test_sync_poller_follows_location_and_forwards_request_controls() -> None:
    """Poll synchronously through the runtime URL with all request controls."""
    initial_response = create_response(
        202,
        {"location": "https://backend.example/jobs/42", "Retry-After": "2"},
    )
    http_client = MagicMock()
    http_client.send.return_value = create_response(200, text='{"status": "done"}')
    client = MagicMock()
    client._connection_runtime_url = "https://runtime.example/connections/1"
    response_hook = MagicMock()
    polling_method = ConnectorPollingMethod(
        http_client=http_client,
        polling_header_name="location",
        timeout=5.0,
        headers={"x-test": "value"},
        client_request_id="request-id",
        response_hook=response_hook,
    )

    with patch("azure.connectors.sdk.polling.time.sleep") as sleep:
        poller = LROPoller(
            client,
            initial_response,
            lambda response: response.text,
            polling_method,
        )
        result = poller.result()

    assert result == '{"status": "done"}'
    sleep.assert_called_once_with(2.0)
    http_client.send.assert_called_once_with(
        "GET",
        "https://runtime.example/connections/1/jobs/42",
        body=None,
        timeout=5.0,
        headers={"x-test": "value"},
        client_request_id="request-id",
        response_hook=response_hook,
    )
    assert poller.done() is True
    assert poller.status() == "Succeeded"


@pytest.mark.parametrize(
    ("updated_location", "expected_url"),
    [
        ("43", "https://runtime.example/connections/1/jobs/pending/43"),
        ("../43", "https://runtime.example/connections/1/jobs/43"),
    ],
)
def test_sync_poller_resolves_relative_location_against_current_url(
    updated_location: str,
    expected_url: str,
) -> None:
    """Resolve sync Location updates relative to the current polling request."""
    http_client = MagicMock()
    http_client.send.side_effect = [
        create_response(202, {"Location": updated_location, "Retry-After": "0"}),
        create_response(200),
    ]
    client = MagicMock()
    client._connection_runtime_url = "https://runtime.example/connections/1"

    with patch("azure.connectors.sdk.polling.time.sleep"):
        poller = LROPoller(
            client,
            create_response(
                202,
                {"Location": "/jobs/pending/42", "Retry-After": "0"},
            ),
            lambda response: response.text,
            ConnectorPollingMethod(http_client, "Location"),
        )
        poller.result()

    assert [call.args[1] for call in http_client.send.call_args_list] == [
        "https://runtime.example/connections/1/jobs/pending/42",
        expected_url,
    ]


@pytest.mark.asyncio
async def test_async_poller_updates_location_until_terminal_response() -> None:
    """Poll asynchronously and honor a changed Location header."""
    initial_response = create_response(
        202,
        {"Location": "/jobs/42", "Retry-After": "0"},
    )
    http_client = MagicMock()
    http_client.send = AsyncMock(
        side_effect=[
            create_response(202, {"Location": "?step=2", "Retry-After": "0"}),
            create_response(204),
        ]
    )
    client = MagicMock()
    client._connection_runtime_url = "https://runtime.example/connections/1"
    polling_method = AsyncConnectorPollingMethod(http_client, "Location")
    poller = AsyncLROPoller(
        client,
        initial_response,
        lambda response: response.text or None,
        polling_method,
    )

    with patch(
        "azure.connectors.sdk.aio.polling.asyncio.sleep",
        new_callable=AsyncMock,
    ) as sleep:
        result = await poller.result()

    assert result is None
    assert sleep.await_count == 2
    assert [call.args[1] for call in http_client.send.await_args_list] == [
        "https://runtime.example/connections/1/jobs/42",
        "https://runtime.example/connections/1/jobs/42?step=2",
    ]
    assert poller.done() is True
    assert poller.status() == "Succeeded"


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("updated_location", "expected_url"),
    [
        ("43", "https://runtime.example/connections/1/jobs/pending/43"),
        ("../43", "https://runtime.example/connections/1/jobs/43"),
    ],
)
async def test_async_poller_resolves_relative_location_against_current_url(
    updated_location: str,
    expected_url: str,
) -> None:
    """Resolve async Location updates relative to the current polling request."""
    http_client = MagicMock()
    http_client.send = AsyncMock(
        side_effect=[
            create_response(
                202,
                {"Location": updated_location, "Retry-After": "0"},
            ),
            create_response(200),
        ]
    )
    client = MagicMock()
    client._connection_runtime_url = "https://runtime.example/connections/1"
    poller = AsyncLROPoller(
        client,
        create_response(
            202,
            {"Location": "/jobs/pending/42", "Retry-After": "0"},
        ),
        lambda response: response.text,
        AsyncConnectorPollingMethod(http_client, "Location"),
    )

    with patch(
        "azure.connectors.sdk.aio.polling.asyncio.sleep",
        new_callable=AsyncMock,
    ):
        await poller.result()

    assert [call.args[1] for call in http_client.send.await_args_list] == [
        "https://runtime.example/connections/1/jobs/pending/42",
        expected_url,
    ]


def test_immediate_success_requires_no_polling() -> None:
    """Return an immediate successful response without issuing a poll request."""
    http_client = MagicMock()
    client = MagicMock()
    client._connection_runtime_url = "https://runtime.example/connections/1"
    poller = LROPoller(
        client,
        create_response(200, text='{"status": "done"}'),
        lambda response: response.text,
        ConnectorPollingMethod(http_client, "Location"),
    )

    assert poller.result() == '{"status": "done"}'
    http_client.send.assert_not_called()


def test_missing_location_rejects_accepted_response() -> None:
    """Reject an accepted response that cannot identify a polling URL."""
    client = MagicMock()
    client._connection_runtime_url = "https://runtime.example/connections/1"

    with pytest.raises(ValueError, match="Location"):
        LROPoller(
            client,
            create_response(202),
            lambda response: response.text,
            ConnectorPollingMethod(MagicMock(), "Location"),
        )


def test_terminal_error_raises_connector_exception() -> None:
    """Raise a connector exception for a failed terminal polling response."""
    http_client = MagicMock()
    http_client.send.return_value = create_response(500, text="failed")
    client = MagicMock()
    client._connection_runtime_url = "https://runtime.example/connections/1"

    with patch("azure.connectors.sdk.polling.time.sleep"):
        poller = LROPoller(
            client,
            create_response(202, {"Location": "/jobs/42", "Retry-After": "0"}),
            lambda response: response.text,
            ConnectorPollingMethod(http_client, "Location"),
        )
        with pytest.raises(ConnectorException):
            poller.result()

    assert poller.status() == "Failed"


def test_resource_rejects_access_before_completion() -> None:
    """Reject terminal resource access while polling remains in progress."""
    client = MagicMock()
    client._connection_runtime_url = "https://runtime.example/connections/1"
    polling_method = ConnectorPollingMethod(MagicMock(), "Location")
    polling_method.initialize(
        client,
        create_response(202, {"Location": "/jobs/42"}),
        lambda response: response.text,
    )

    with pytest.raises(RuntimeError, match="has not completed"):
        polling_method.resource()


def test_continuation_tokens_are_explicitly_unsupported() -> None:
    """Defer poller serialization to a later protocol phase."""
    polling_method = ConnectorPollingMethod(MagicMock(), "Location")

    with pytest.raises(TypeError, match="doesn't support"):
        polling_method.get_continuation_token()


def test_retry_after_supports_http_dates_and_defaults() -> None:
    """Parse HTTP-date delays and use the bounded default for malformed values."""
    retry_at = datetime.now(timezone.utc) + timedelta(seconds=60)

    delay = get_retry_after_seconds(
        create_response(202, {"Retry-After": format_datetime(retry_at)})
    )

    assert 55.0 <= delay <= 60.0
    assert get_retry_after_seconds(create_response(202)) == 1.0
    assert get_retry_after_seconds(
        create_response(202, {"Retry-After": "invalid"})
    ) == 1.0


@pytest.mark.parametrize("retry_after", ["Infinity", "-Infinity", "NaN", "1e309"])
def test_retry_after_defaults_for_non_finite_numbers(retry_after: str) -> None:
    """Use the finite default when Retry-After cannot represent a sleep delay."""
    assert get_retry_after_seconds(
        create_response(202, {"Retry-After": retry_after})
    ) == 1.0


def test_foreign_polling_url_is_rebased_without_forwarding_its_origin() -> None:
    """Preserve backend path and query while using the authenticated runtime."""
    resolved = resolve_polling_url(
        "https://backend.example/jobs/42?state=running",
        "https://runtime.example/connections/1",
    )

    assert resolved == (
        "https://runtime.example/connections/1/jobs/42?state=running"
    )


def test_same_host_polling_url_rejects_scheme_or_port_changes() -> None:
    """Reject an origin that resembles the runtime but changes its security boundary."""
    with pytest.raises(ValueError, match="scheme and port"):
        resolve_polling_url(
            "http://runtime.example/jobs/42",
            "https://runtime.example/connections/1",
        )


def test_polling_method_rejects_unsupported_header_protocol() -> None:
    """Reject status-document protocols outside the current Location contract."""
    with pytest.raises(ValueError, match="Only the 'Location'"):
        ConnectorPollingMethod(MagicMock(), "Azure-AsyncOperation")
