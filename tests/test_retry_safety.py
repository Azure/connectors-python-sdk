# Copyright (c) Microsoft Corporation. All rights reserved.

"""HTTP method retry-safety tests for the shared connector client."""

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import aiohttp
import pytest

from azure.connectors.sdk.http_client import ConnectorHttpClient
from azure.connectors.sdk.options import ConnectorClientOptions


def response_context(status: int):
    """Return an asynchronous response context for a test status code."""
    response = MagicMock(status=status, headers={})
    response.text = AsyncMock(return_value="transient")
    response.read = AsyncMock(return_value=b"transient")
    context = MagicMock()
    context.__aenter__.return_value = response
    return context


async def send_with_session(method, options, session, mock_token_provider, body=None):
    """Send a request through the real retry loop and a deterministic session."""
    client = ConnectorHttpClient(mock_token_provider, options)
    with patch.object(client, "_ensure_session", AsyncMock(return_value=session)):
        with patch.object(client, "_delay_retry", AsyncMock()):
            return await client.send_async(
                method, "https://example.com/action", body=body
            )


def test_retry_unsafe_http_methods_defaults_to_false():
    """Keep retries of methods outside the safe allowlist opt-in only."""
    assert ConnectorClientOptions().retry_unsafe_http_methods is False


@pytest.mark.asyncio
async def test_post_transient_response_is_sent_once_by_default(mock_token_provider):
    """Do not replay a POST whose first outcome is ambiguous."""
    options = ConnectorClientOptions(max_retry_attempts=2)
    session = MagicMock()
    session.request.side_effect = [response_context(500), response_context(200)]
    result = await send_with_session("POST", options, session, mock_token_provider)

    assert result.status == 500
    assert session.request.call_count == 1


@pytest.mark.asyncio
@pytest.mark.parametrize("method", ["GET", "HEAD", "OPTIONS", "TRACE"])
@pytest.mark.parametrize("status", [429, 500, 503])
async def test_safe_methods_retry_transient_responses(
    method, status, mock_token_provider
):
    """Retain configured retries for every safe method and transient status."""
    options = ConnectorClientOptions(max_retry_attempts=2)
    session = MagicMock()
    session.request.side_effect = [response_context(status), response_context(200)]

    result = await send_with_session(method, options, session, mock_token_provider)

    assert result.status == 200
    assert session.request.call_count == 2


@pytest.mark.asyncio
@pytest.mark.parametrize("method", ["PUT", "PATCH", "DELETE", "CUSTOM"])
@pytest.mark.parametrize("status", [429, 503])
async def test_other_unsafe_methods_are_sent_once(
    method, status, mock_token_provider
):
    """Include unknown extension methods in the unsafe-by-default fallback."""
    options = ConnectorClientOptions(max_retry_attempts=2)
    session = MagicMock()
    session.request.side_effect = [response_context(status), response_context(200)]

    result = await send_with_session(method, options, session, mock_token_provider)

    assert result.status == status
    assert session.request.call_count == 1


@pytest.mark.asyncio
async def test_safe_method_uses_exact_configured_attempts(mock_token_provider):
    """Keep the existing total-attempt semantics for safe requests."""
    options = ConnectorClientOptions(max_retry_attempts=3)
    session = MagicMock()
    session.request.side_effect = [
        response_context(500), response_context(503), response_context(200)
    ]

    result = await send_with_session("GET", options, session, mock_token_provider)

    assert result.status == 200
    assert session.request.call_count == 3


@pytest.mark.asyncio
async def test_post_transient_response_retries_when_enabled(mock_token_provider):
    """Apply the configured retry budget when explicitly opted in."""
    options = ConnectorClientOptions(
        max_retry_attempts=2, retry_unsafe_http_methods=True
    )
    session = MagicMock()
    session.request.side_effect = [response_context(429), response_context(200)]

    result = await send_with_session("POST", options, session, mock_token_provider)

    assert result.status == 200
    assert session.request.call_count == 2


@pytest.mark.asyncio
@pytest.mark.parametrize("method", ["GET", "POST", "PUT", "PATCH", "DELETE", "CUSTOM"])
async def test_transport_error_obeys_method_safety(method, mock_token_provider):
    """An ambiguous transport error must not replay unsafe methods."""
    options = ConnectorClientOptions(max_retry_attempts=2)
    session = MagicMock()
    session.request.side_effect = [
        aiohttp.ClientConnectionError("Unknown outcome."), response_context(200)
    ]

    if method == "GET":
        result = await send_with_session(method, options, session, mock_token_provider)
        assert result.status == 200
        assert session.request.call_count == 2
    else:
        with pytest.raises(aiohttp.ClientConnectionError):
            await send_with_session(method, options, session, mock_token_provider)
        assert session.request.call_count == 1


@pytest.mark.asyncio
async def test_post_transport_error_retries_when_enabled(mock_token_provider):
    """Opt-in permits replay after a retriable transport failure."""
    options = ConnectorClientOptions(
        max_retry_attempts=2, retry_unsafe_http_methods=True
    )
    session = MagicMock()
    session.request.side_effect = [
        aiohttp.ClientConnectionError("Unknown outcome."), response_context(200)
    ]

    result = await send_with_session("POST", options, session, mock_token_provider)

    assert result.status == 200
    assert session.request.call_count == 2


@pytest.mark.asyncio
async def test_cancellation_does_not_retry(mock_token_provider):
    """Cancellation must propagate without another attempt."""
    options = ConnectorClientOptions(max_retry_attempts=2)
    session = MagicMock()
    session.request.side_effect = asyncio.CancelledError()

    with pytest.raises(asyncio.CancelledError):
        await send_with_session("GET", options, session, mock_token_provider)

    assert session.request.call_count == 1


@pytest.mark.asyncio
@pytest.mark.parametrize("body", [{"message": "hello"}, b"\x00\xffbinary"])
async def test_opted_in_post_replays_identical_body(body, mock_token_provider):
    """JSON and binary bodies remain byte-identical on explicit replay."""
    options = ConnectorClientOptions(
        max_retry_attempts=2, retry_unsafe_http_methods=True
    )
    session = MagicMock()
    session.request.side_effect = [response_context(500), response_context(200)]

    result = await send_with_session(
        "POST", options, session, mock_token_provider, body=body
    )

    assert result.status == 200
    assert session.request.call_count == 2
    first_body = session.request.call_args_list[0].kwargs["data"]
    second_body = session.request.call_args_list[1].kwargs["data"]
    assert first_body == second_body
