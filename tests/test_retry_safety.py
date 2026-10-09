# Copyright (c) Microsoft Corporation. All rights reserved.

"""HTTP method retry-safety tests for the Azure Core connector pipeline."""

import asyncio
from unittest.mock import AsyncMock, MagicMock

import pytest
from azure.core.credentials import AzureKeyCredential
from azure.core.exceptions import ServiceRequestError
from azure.core.pipeline.transport import AsyncHttpTransport

from azure.connectors.sdk.http_client import ConnectorHttpClient


class RecordingTransport(AsyncHttpTransport):
    """Record transport attempts and return deterministic outcomes."""

    def __init__(self, *outcomes: object) -> None:
        """Initialize the transport outcomes."""
        self.outcomes = list(outcomes)
        self.requests: list[object] = []
        self.sleep_durations: list[float] = []
        self.connection_config = MagicMock(timeout=300.0)

    async def send(self, request: object, **kwargs: object) -> MagicMock:
        """Record a request and return or raise the next outcome."""
        del kwargs
        self.requests.append(request)
        outcome = self.outcomes.pop(0)
        if isinstance(outcome, BaseException):
            raise outcome
        return outcome

    async def open(self) -> None:
        """Open the transport."""

    async def close(self) -> None:
        """Close the transport."""

    async def __aenter__(self):
        """Enter the transport context."""
        return self

    async def __aexit__(self, *args: object) -> None:
        """Exit the transport context."""
        del args

    async def sleep(self, duration: float) -> None:
        """Record a retry delay without waiting."""
        self.sleep_durations.append(duration)


def create_response(status: int) -> MagicMock:
    """Create a response accepted by the Azure Core pipeline."""
    response = MagicMock()
    response.status_code = status
    response.headers = {}
    response.read = AsyncMock(return_value=b"transient")
    response.text = MagicMock(return_value="transient")
    return response


async def send_with_transport(
    method: str,
    *outcomes: object,
    max_retry_attempts: int = 2,
    retry_unsafe_http_methods: bool = False,
    body: object = None,
) -> tuple[object, RecordingTransport]:
    """Send through the real Azure Core retry policy and recording transport."""
    transport = RecordingTransport(*outcomes)
    client = ConnectorHttpClient(
        AzureKeyCredential("test-key"),
        max_retry_attempts=max_retry_attempts,
        initial_retry_delay_seconds=0,
        retry_jitter_factor=0,
        retry_unsafe_http_methods=retry_unsafe_http_methods,
        transport=transport,
    )
    response = await client.send_async(
        method,
        "https://example.com/action",
        body=body,
    )
    return response, transport


def test_retry_unsafe_http_methods_defaults_to_false() -> None:
    """Keep retries of methods outside the safe allowlist opt-in only."""
    client = ConnectorHttpClient(AzureKeyCredential("test-key"))

    assert client._retry_unsafe_http_methods is False


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "method, expected_attempts",
    [
        ("get", 2),
        ("GeT", 2),
        ("head", 2),
        ("HeAd", 2),
        ("options", 2),
        ("OpTiOnS", 2),
        ("trace", 2),
        ("TrAcE", 2),
        ("post", 1),
        ("PuT", 1),
        ("pAtCh", 1),
        ("delete", 1),
        ("CuStOm", 1),
    ],
)
@pytest.mark.parametrize("failure", ["response", "transport"])
async def test_method_case_is_normalized_before_retry_and_dispatch(
    method: str,
    expected_attempts: int,
    failure: str,
) -> None:
    """Classify and dispatch every method using the same uppercase value."""
    first_outcome = (
        create_response(500)
        if failure == "response"
        else ServiceRequestError("Unknown outcome.")
    )
    outcomes = (first_outcome, create_response(200))

    if failure == "transport" and expected_attempts == 1:
        transport = RecordingTransport(*outcomes)
        client = ConnectorHttpClient(
            AzureKeyCredential("test-key"),
            max_retry_attempts=2,
            initial_retry_delay_seconds=0,
            retry_jitter_factor=0,
            transport=transport,
        )
        with pytest.raises(ServiceRequestError):
            await client.send_async(method, "https://example.com/action")
    else:
        response, transport = await send_with_transport(method, *outcomes)
        assert response.status == (200 if expected_attempts == 2 else 500)

    assert len(transport.requests) == expected_attempts
    assert all(request.method == method.upper() for request in transport.requests)


@pytest.mark.asyncio
@pytest.mark.parametrize("method", ["GET", "HEAD", "OPTIONS", "TRACE"])
@pytest.mark.parametrize("status", [429, 500, 503])
async def test_safe_methods_retry_transient_responses(
    method: str,
    status: int,
) -> None:
    """Retain configured retries for each safe method and transient status."""
    response, transport = await send_with_transport(
        method,
        create_response(status),
        create_response(200),
    )

    assert response.status == 200
    assert len(transport.requests) == 2


@pytest.mark.asyncio
@pytest.mark.parametrize("method", ["POST", "PUT", "PATCH", "DELETE", "CUSTOM"])
@pytest.mark.parametrize("status", [429, 503])
async def test_unsafe_methods_are_sent_once_by_default(
    method: str,
    status: int,
) -> None:
    """Do not replay unsafe or extension methods after transient responses."""
    response, transport = await send_with_transport(
        method,
        create_response(status),
        create_response(200),
    )

    assert response.status == status
    assert len(transport.requests) == 1


@pytest.mark.asyncio
async def test_safe_method_uses_exact_configured_attempts() -> None:
    """Keep max_retry_attempts as the total-attempt count."""
    response, transport = await send_with_transport(
        "GET",
        create_response(500),
        create_response(503),
        create_response(200),
        max_retry_attempts=3,
    )

    assert response.status == 200
    assert len(transport.requests) == 3


@pytest.mark.asyncio
@pytest.mark.parametrize("method", ["POST", "post", "PoSt", "CUSTOM", "custom", "CuStOm"])
@pytest.mark.parametrize("failure", ["response", "transport"])
async def test_unsafe_method_retries_when_enabled(
    method: str,
    failure: str,
) -> None:
    """Apply the configured retry budget after explicit unsafe-method opt-in."""
    first_outcome = (
        create_response(429)
        if failure == "response"
        else ServiceRequestError("Unknown outcome.")
    )
    response, transport = await send_with_transport(
        method,
        first_outcome,
        create_response(200),
        retry_unsafe_http_methods=True,
    )

    assert response.status == 200
    assert len(transport.requests) == 2
    assert all(request.method == method.upper() for request in transport.requests)


@pytest.mark.asyncio
async def test_cancellation_does_not_retry() -> None:
    """Propagate cancellation without issuing another attempt."""
    transport = RecordingTransport(asyncio.CancelledError(), create_response(200))
    client = ConnectorHttpClient(
        AzureKeyCredential("test-key"),
        max_retry_attempts=2,
        initial_retry_delay_seconds=0,
        retry_jitter_factor=0,
        transport=transport,
    )

    with pytest.raises(asyncio.CancelledError):
        await client.send_async("GET", "https://example.com/action")

    assert len(transport.requests) == 1


@pytest.mark.asyncio
@pytest.mark.parametrize("body", [{"message": "hello"}, b"\x00\xffbinary"])
async def test_opted_in_post_replays_identical_body(body: object) -> None:
    """Keep JSON and binary request bodies identical during explicit replay."""
    response, transport = await send_with_transport(
        "POST",
        create_response(500),
        create_response(200),
        retry_unsafe_http_methods=True,
        body=body,
    )

    assert response.status == 200
    assert len(transport.requests) == 2
    assert transport.requests[0].content == transport.requests[1].content
