# ------------------------------------------------------------
# Copyright (c) Microsoft Corporation.  All rights reserved.
# ------------------------------------------------------------

"""Regression coverage for initiating and subsequent relative LRO Locations."""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch
from urllib.parse import urljoin, urlsplit

import pytest
from azure.core.credentials import AzureKeyCredential
from azure.core.polling import AsyncLROPoller, LROPoller
from requests import Request

from azure.connectors.aio.kusto import KustoClient as AsyncKustoClient
from azure.connectors.kusto import KustoClient
from azure.connectors.sdk._polling import resolve_polling_url
from azure.connectors.sdk.aio.polling import (
    ConnectorPollingMethod as AsyncConnectorPollingMethod,
)
from azure.connectors.sdk.polling import ConnectorPollingMethod
from azure.connectors.sdk.response import ConnectorResponseSnapshot

RUNTIME_URL = "https://runtime.example/connections/1"
REQUEST_URL = f"{RUNTIME_URL}/ListKustoResults/false"
LOCATION_CASES = [
    ("43", f"{RUNTIME_URL}/ListKustoResults/43"),
    ("../43", f"{RUNTIME_URL}/43"),
    ("?step=1", f"{REQUEST_URL}?step=1"),
    ("/jobs/43", f"{RUNTIME_URL}/jobs/43"),
    ("https://backend.example/jobs/43", f"{RUNTIME_URL}/jobs/43"),
    (
        "https://runtime.example/jobs/43",
        "https://runtime.example/jobs/43",
    ),
]
UNSAFE_LOCATIONS = [
    "https://evil.invalid\\@runtime.example/jobs",
    "https://runtime.example\\@evil.invalid/jobs",
    "https://user@runtime.example/jobs",
    "https://user:password@backend.example/jobs",
    "https://runtime.example%2f.evil.invalid/jobs",
    "https://runtime.example:/jobs",
    "https://[::1]runtime.example/jobs",
    "https:/runtime.example/jobs",
    "//evil.invalid/jobs",
    "///evil.invalid/jobs",
    "\\\\evil.invalid/jobs",
    "https://runtime.example\t.evil.invalid/jobs",
    "\nhttps://runtime.example/jobs",
    "https://runtime.example/jobs\r\nignored",
    "https://runtime.example/jobs\x00",
    "https://runtime.example/jobs\x7f",
    " https://runtime.example/jobs",
    "../jobs\\@evil.invalid",
    "?state=running\n",
]


def assert_prepared_runtime_origin(url: str) -> None:
    """Check the credential-bearing URL after Requests transport normalization."""
    prepared = Request(
        "GET", url, headers={"Authorization": "Bearer test-token"},
    ).prepare()
    parsed = urlsplit(prepared.url)
    assert (parsed.scheme, parsed.hostname, parsed.port or 443) == (
        "https", "runtime.example", 443,
    )
    assert prepared.headers["Authorization"] == "Bearer test-token"


def response(
    status: int, location: str | None = None,
) -> ConnectorResponseSnapshot:
    """Create a zero-delay response for a polling sequence."""
    headers = {"Retry-After": "0"}
    if location is not None:
        headers["Location"] = location
    return ConnectorResponseSnapshot(status, headers, '{}', b'{}')


@pytest.mark.parametrize("initial_location,expected_url", LOCATION_CASES)
@pytest.mark.parametrize("subsequent_location", ["44", "../44", "?step=2"])
def test_sync_initial_and_subsequent_relative_locations(
    initial_location: str,
    expected_url: str,
    subsequent_location: str,
) -> None:
    """Use the initiating URI first and the actual polling URI thereafter."""
    http_client = MagicMock()
    http_client.send.side_effect = [
        response(202, subsequent_location), response(200),
    ]
    method = ConnectorPollingMethod(
        http_client, "Location", request_url=REQUEST_URL,
    )
    with patch("azure.connectors.sdk.polling.time.sleep"):
        poller = LROPoller(
            SimpleNamespace(_connection_runtime_url=RUNTIME_URL),
            response(202, initial_location),
            lambda terminal: terminal.text,
            method,
        )
        assert poller.result() == '{}'

    assert [call.args[1] for call in http_client.send.call_args_list] == [
        expected_url, urljoin(expected_url, subsequent_location),
    ]
    for call in http_client.send.call_args_list:
        assert_prepared_runtime_origin(call.args[1])


@pytest.mark.asyncio
@pytest.mark.parametrize("initial_location,expected_url", LOCATION_CASES)
@pytest.mark.parametrize("subsequent_location", ["44", "../44", "?step=2"])
async def test_aio_initial_and_subsequent_relative_locations(
    initial_location: str,
    expected_url: str,
    subsequent_location: str,
) -> None:
    """Apply identical initial and later Location semantics asynchronously."""
    http_client = SimpleNamespace(send=AsyncMock(side_effect=[
        response(202, subsequent_location), response(200),
    ]))
    poller = AsyncLROPoller(
        SimpleNamespace(_connection_runtime_url=RUNTIME_URL),
        response(202, initial_location),
        lambda terminal: terminal.text,
        AsyncConnectorPollingMethod(
            http_client, "Location", request_url=REQUEST_URL,
        ),
    )
    with patch(
        "azure.connectors.sdk.aio.polling.asyncio.sleep", new_callable=AsyncMock,
    ):
        assert await poller.result() == '{}'

    assert [call.args[1] for call in http_client.send.await_args_list] == [
        expected_url, urljoin(expected_url, subsequent_location),
    ]
    for call in http_client.send.await_args_list:
        assert_prepared_runtime_origin(call.args[1])


@pytest.mark.parametrize("location", UNSAFE_LOCATIONS)
@pytest.mark.parametrize(
    "method_type", [ConnectorPollingMethod, AsyncConnectorPollingMethod],
)
def test_polling_rejects_ambiguous_initial_authority_before_sending(
    location: str, method_type: type,
) -> None:
    """Reject malformed initial Locations on both surfaces before authentication."""
    http_client = MagicMock()
    method = method_type(http_client, "Location", request_url=REQUEST_URL)
    with pytest.raises(ValueError):
        method.initialize(
            SimpleNamespace(_connection_runtime_url=RUNTIME_URL),
            response(202, location),
            lambda terminal: terminal.text,
        )
    http_client.send.assert_not_called()


@pytest.mark.parametrize("location", UNSAFE_LOCATIONS)
def test_sync_polling_rejects_ambiguous_subsequent_location(
    location: str,
) -> None:
    """Never issue a follow-up sync request to an ambiguous Location."""
    http_client = MagicMock()
    http_client.send.return_value = response(202, location)
    method = ConnectorPollingMethod(
        http_client, "Location", request_url=REQUEST_URL,
    )
    method.initialize(
        SimpleNamespace(_connection_runtime_url=RUNTIME_URL),
        response(202, "43"),
        lambda terminal: terminal.text,
    )
    with patch("azure.connectors.sdk.polling.time.sleep"):
        with pytest.raises(ValueError):
            method.run()
    http_client.send.assert_called_once()
    assert_prepared_runtime_origin(http_client.send.call_args.args[1])


@pytest.mark.asyncio
@pytest.mark.parametrize("location", UNSAFE_LOCATIONS)
async def test_aio_polling_rejects_ambiguous_subsequent_location(
    location: str,
) -> None:
    """Never issue a follow-up async request to an ambiguous Location."""
    http_client = SimpleNamespace(send=AsyncMock(return_value=response(202, location)))
    method = AsyncConnectorPollingMethod(
        http_client, "Location", request_url=REQUEST_URL,
    )
    method.initialize(
        SimpleNamespace(_connection_runtime_url=RUNTIME_URL),
        response(202, "43"),
        lambda terminal: terminal.text,
    )
    with patch(
        "azure.connectors.sdk.aio.polling.asyncio.sleep", new_callable=AsyncMock,
    ):
        with pytest.raises(ValueError):
            await method.run()
    http_client.send.assert_awaited_once()
    assert_prepared_runtime_origin(http_client.send.await_args.args[1])


@pytest.mark.parametrize("location", ["43", "../43", "?step=1"])
@pytest.mark.parametrize("unsafe_base", UNSAFE_LOCATIONS)
def test_relative_polling_rejects_ambiguous_request_base(
    location: str, unsafe_base: str,
) -> None:
    """Validate a relative initiating URI before urljoin can strip unsafe input."""
    with pytest.raises(ValueError):
        resolve_polling_url(location, RUNTIME_URL, unsafe_base)


@pytest.mark.parametrize("unsafe_runtime", UNSAFE_LOCATIONS)
def test_polling_validates_runtime_before_rebasing(unsafe_runtime: str) -> None:
    """Reject ambiguous configured authorities even for runtime-relative paths."""
    with pytest.raises(ValueError):
        resolve_polling_url("/jobs/43", unsafe_runtime)


def test_same_origin_polling_reconstructs_trusted_runtime_authority() -> None:
    """Do not forward the connector-provided authority spelling to Requests."""
    resolved = resolve_polling_url(
        "https://RUNTIME.EXAMPLE:443/jobs/43?state=running", RUNTIME_URL,
    )
    assert resolved == "https://runtime.example/jobs/43?state=running"
    assert_prepared_runtime_origin(resolved)


@pytest.mark.parametrize("location", ["43", "../43", "?step=1"])
@pytest.mark.parametrize(
    "request_url", [
        "http://runtime.example/operation/false",
        "https://runtime.example:444/operation/false",
    ],
)
def test_relative_location_cannot_inherit_an_unsafe_origin(
    location: str, request_url: str,
) -> None:
    """Validate joined relative URLs through the existing origin checks."""
    with pytest.raises(ValueError, match="scheme and port"):
        resolve_polling_url(location, RUNTIME_URL, request_url)


@pytest.mark.parametrize("initial_location,expected_url", LOCATION_CASES[:2])
def test_kusto_begin_carries_initiating_request_uri(
    initial_location: str, expected_url: str,
) -> None:
    """Catch missing request_url propagation in the generated synchronous API."""
    client = KustoClient(RUNTIME_URL, AzureKeyCredential("test-key"))
    client._http_client = MagicMock()
    client.http_client.send.side_effect = [
        response(202, initial_location), response(200),
    ]
    with client, patch("azure.connectors.sdk.polling.time.sleep"):
        assert client.begin_list_kusto_results(input={}).result() == {}

    assert [call.args[:2] for call in client.http_client.send.call_args_list] == [
        ("POST", REQUEST_URL), ("GET", expected_url),
    ]


@pytest.mark.asyncio
@pytest.mark.parametrize("initial_location,expected_url", LOCATION_CASES[:2])
async def test_aio_kusto_begin_carries_initiating_request_uri(
    initial_location: str, expected_url: str,
) -> None:
    """Catch missing request_url propagation in the generated asynchronous API."""
    client = AsyncKustoClient(RUNTIME_URL, AzureKeyCredential("test-key"))
    client._http_client = MagicMock()
    client.http_client.send = AsyncMock(side_effect=[
        response(202, initial_location), response(200),
    ])
    client.http_client.close = AsyncMock()
    async with client:
        with patch(
            "azure.connectors.sdk.aio.polling.asyncio.sleep",
            new_callable=AsyncMock,
        ):
            poller = await client.begin_list_kusto_results(input={})
            assert await poller.result() == {}

    assert [call.args[:2] for call in client.http_client.send.await_args_list] == [
        ("POST", REQUEST_URL), ("GET", expected_url),
    ]
