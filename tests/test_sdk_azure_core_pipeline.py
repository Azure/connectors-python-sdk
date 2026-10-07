"""Tests for the Azure Core asynchronous connector pipeline."""

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import requests
from aiohttp import web
from aiohttp.test_utils import TestServer
from azure.core.credentials import AccessToken, AzureKeyCredential
from azure.core.exceptions import ServiceRequestError, ServiceResponseTimeoutError
from azure.core.pipeline.policies import RetryMode, SansIOHTTPPolicy
from azure.core.pipeline.transport import AsyncHttpTransport, AsyncioRequestsTransport

from azure.connectors.sdk import ConnectorClientBase, ConnectorException, ConnectorHttpClient
from azure.connectors.sdk.http_client import _JitterRetryPolicy


class RecordingCredential:
    """Record token requests and lifecycle calls."""

    def __init__(self) -> None:
        """Initialize the credential."""
        self.scopes: tuple[str, ...] | None = None
        self.closed = False

    async def get_token(self, *scopes: str, **kwargs: object) -> AccessToken:
        """Return a test token."""
        del kwargs
        self.scopes = scopes
        return AccessToken("test-token", 4_102_444_800)

    async def close(self) -> None:
        """Record an ownership violation."""
        self.closed = True


class RecordingTransport(AsyncHttpTransport):
    """Record requests and return configured responses."""

    def __init__(self, *responses: object) -> None:
        """Initialize the transport."""
        self.responses = list(responses)
        self.requests: list[object] = []
        self.request_options: list[dict[str, object]] = []
        self.sleep_durations: list[float] = []
        self.closed = False
        self.connection_config = MagicMock(timeout=300.0)

    async def send(self, request: object, **kwargs: object) -> MagicMock:
        """Record and answer a request."""
        self.requests.append(request)
        self.request_options.append(kwargs)
        response = self.responses.pop(0)
        if isinstance(response, Exception):
            raise response
        return response

    async def open(self) -> None:
        """Open the transport."""

    async def close(self) -> None:
        """Close the transport."""
        self.closed = True

    async def __aenter__(self):
        """Enter the transport context."""
        return self

    async def __aexit__(self, *args: object) -> None:
        """Exit the transport context."""
        await self.close()

    async def sleep(self, duration: float) -> None:
        """Record a retry delay without waiting."""
        self.sleep_durations.append(duration)


class RecordingPolicy(SansIOHTTPPolicy):
    """Record policy execution and the current authorization header."""

    def __init__(self, name: str, events: list[tuple[str, str | None]]) -> None:
        """Initialize the recording policy."""
        self._name = name
        self._events = events

    def on_request(self, request) -> None:
        """Record request processing."""
        self._events.append(
            (self._name, request.http_request.headers.get("Authorization"))
        )


class ConcreteConnectorClient(ConnectorClientBase):
    """Provide a concrete generated-client lifecycle test double."""

    @property
    def connector_name(self) -> str:
        """Get the connector name."""
        return "test"


def create_response(
    status: int = 200,
    *,
    headers: dict[str, str] | None = None,
    content: bytes = b"{}",
) -> MagicMock:
    """Create a response accepted by the Azure Core pipeline."""
    response = MagicMock()
    response.status_code = status
    response.headers = headers or {}
    response.body = MagicMock(return_value=content)
    response.read = AsyncMock(return_value=content)
    response.text = MagicMock(return_value=content.decode("utf-8"))
    return response


@pytest.mark.asyncio
async def test_token_credential_uses_fixed_scope_and_remains_open() -> None:
    """Use the API Hub scope without taking credential ownership."""
    credential = RecordingCredential()
    transport = RecordingTransport(create_response(status=204, content=b""))
    client = ConnectorHttpClient(credential, transport=transport)

    await client.send_async("GET", "https://example.test/items")
    await client.close()

    assert credential.scopes == ("https://apihub.azure.com/.default",)
    assert transport.requests[0].headers["Authorization"] == "Bearer test-token"
    assert credential.closed is False
    assert transport.closed is True


@pytest.mark.asyncio
async def test_key_credential_uses_bearer_authorization() -> None:
    """Use an Azure key credential with the connector bearer format."""
    transport = RecordingTransport(create_response(status=204, content=b""))
    client = ConnectorHttpClient(
        AzureKeyCredential("test-key"),
        transport=transport,
    )

    await client.send_async("GET", "https://example.test/items")

    assert transport.requests[0].headers["Authorization"] == "Bearer test-key"


@pytest.mark.asyncio
async def test_request_controls_and_response_hook_are_applied() -> None:
    """Apply direct controls and invoke the hook with an immutable snapshot."""
    transport = RecordingTransport(
        create_response(headers={"x-result": "complete"})
    )
    hook = MagicMock()
    client = ConnectorHttpClient(
        AzureKeyCredential("test-key"),
        timeout_seconds=30.0,
        transport=transport,
    )

    response = await client.send_async(
        "GET",
        "https://example.test/items",
        timeout=5.0,
        headers={"x-custom": "value", "Authorization": "ignored"},
        client_request_id="request-id",
        response_hook=hook,
    )

    assert transport.requests[0].headers["x-custom"] == "value"
    assert transport.requests[0].headers["Authorization"] == "Bearer test-key"
    assert transport.request_options[0]["connection_timeout"] == 5.0
    assert "read_timeout" not in transport.request_options[0]
    assert transport.requests[0].headers["x-ms-client-request-id"] == "request-id"
    hook.assert_called_once_with(response, response.headers)
    with pytest.raises(TypeError):
        response.headers["x-new"] = "value"


@pytest.mark.asyncio
async def test_request_controls_override_client_default_headers() -> None:
    """Apply operation headers and request IDs after client defaults."""
    transport = RecordingTransport(create_response())
    client = ConnectorHttpClient(
        AzureKeyCredential("test-key"),
        headers={
            "Authorization": "ignored",
            "Content-Type": "ignored",
            "x-custom": "client",
            "x-ms-client-request-id": "fixed",
        },
        transport=transport,
    )

    await client.send_async(
        "GET",
        "https://example.test/items",
        headers={"x-custom": "operation"},
        client_request_id="per-call",
    )

    request_headers = transport.requests[0].headers
    assert request_headers["Authorization"] == "Bearer test-key"
    assert request_headers["Content-Type"] == "application/json"
    assert request_headers["x-custom"] == "operation"
    assert request_headers["x-ms-client-request-id"] == "per-call"


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("default_timeout", "request_timeout"),
    [
        (0.05, None),
        (1.0, 0.05),
    ],
)
async def test_timeout_bounds_slow_response_body(
    default_timeout: float,
    request_timeout: float | None,
) -> None:
    """Bound response body I/O by the default or per-call total timeout."""

    async def delayed_body(request: web.Request) -> web.StreamResponse:
        response = web.StreamResponse(status=200)
        await response.prepare(request)
        await asyncio.sleep(0.2)
        await response.write(b"ok")
        await response.write_eof()
        return response

    application = web.Application()
    application.router.add_get("/", delayed_body)
    server = TestServer(application)
    await server.start_server()
    client = ConnectorHttpClient(
        AzureKeyCredential("test-key"),
        max_retry_attempts=1,
        timeout_seconds=default_timeout,
    )

    try:
        with pytest.raises(ServiceResponseTimeoutError):
            await client.send_async(
                "GET",
                str(server.make_url("/")),
                timeout=request_timeout,
            )
    finally:
        await client.close()
        await server.close()


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("default_timeout", "request_timeout"),
    [
        (0.0, None),
        (30.0, 0.0),
        (-1.0, None),
        (30.0, -1.0),
    ],
)
async def test_nonpositive_timeout_disables_request_deadlines(
    default_timeout: float,
    request_timeout: float | None,
) -> None:
    """Dispatch without SDK or transport deadlines for nonpositive timeouts."""
    transport = RecordingTransport(create_response())
    client = ConnectorHttpClient(
        AzureKeyCredential("test-key"),
        timeout_seconds=default_timeout,
        transport=transport,
    )

    response = await client.send_async(
        "GET",
        "https://example.test/items",
        timeout=request_timeout,
    )

    assert response.status == 200
    assert len(transport.requests) == 1
    assert transport.request_options[0]["connection_timeout"] is None
    assert "read_timeout" not in transport.request_options[0]


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("default_timeout", "request_timeout"),
    [
        (0.0, None),
        (30.0, 0.0),
    ],
)
async def test_nonpositive_timeout_allows_slow_response_body(
    default_timeout: float,
    request_timeout: float | None,
) -> None:
    """Load a slow response body without SDK or transport deadlines."""

    async def delayed_body(request: web.Request) -> web.StreamResponse:
        response = web.StreamResponse(status=200)
        await response.prepare(request)
        await asyncio.sleep(0.05)
        await response.write(b"ok")
        await response.write_eof()
        return response

    application = web.Application()
    application.router.add_get("/", delayed_body)
    server = TestServer(application)
    await server.start_server()
    client = ConnectorHttpClient(
        AzureKeyCredential("test-key"),
        max_retry_attempts=1,
        timeout_seconds=default_timeout,
    )

    try:
        response = await client.send_async(
            "GET",
            str(server.make_url("/")),
            timeout=request_timeout,
        )
    finally:
        await client.close()
        await server.close()

    assert response.status == 200
    assert response.content == b"ok"


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("method", "status"),
    [
        ("GET", 204),
        ("HEAD", 200),
        ("GET", 200),
    ],
)
async def test_empty_buffered_response_creates_snapshot_and_invokes_hook(
    method: str,
    status: int,
) -> None:
    """Use already-buffered empty content without reading the stream again."""

    async def empty_response(request: web.Request) -> web.Response:
        del request
        return web.Response(status=status, body=b"")

    application = web.Application()
    application.router.add_route("*", "/", empty_response)
    server = TestServer(application)
    await server.start_server()
    hook = MagicMock()
    client = ConnectorHttpClient(
        AzureKeyCredential("test-key"),
        max_retry_attempts=1,
    )

    try:
        response = await client.send_async(
            method,
            str(server.make_url("/")),
            response_hook=hook,
        )
    finally:
        await client.close()
        await server.close()

    assert response.status == status
    assert response.content == b""
    assert response.text == ""
    hook.assert_called_once_with(response, response.headers)


@pytest.mark.asyncio
async def test_empty_buffered_error_raises_connector_exception() -> None:
    """Preserve normal connector error handling for an empty response body."""

    async def empty_error(request: web.Request) -> web.Response:
        del request
        return web.Response(status=400, body=b"")

    application = web.Application()
    application.router.add_get("/", empty_error)
    server = TestServer(application)
    await server.start_server()
    client = ConnectorHttpClient(
        AzureKeyCredential("test-key"),
        max_retry_attempts=1,
    )

    try:
        with pytest.raises(ConnectorException) as error:
            await client.get_async(str(server.make_url("/")))
    finally:
        await client.close()
        await server.close()

    assert error.value.status_code == 400
    assert error.value.response_body == ""


@pytest.mark.asyncio
@pytest.mark.parametrize("request_timeout", [None, 5.0, 0.0, -1.0])
async def test_requests_transport_accepts_timeout_controls(
    request_timeout: float | None,
) -> None:
    """Keep timeout options compatible with the requests-backed transport."""
    transport = AsyncioRequestsTransport()
    client = ConnectorHttpClient(
        AzureKeyCredential("test-key"),
        max_retry_attempts=1,
        transport=transport,
    )
    request_options = (
        {} if request_timeout is None else {"timeout": request_timeout}
    )

    try:
        with patch.object(
            requests.Session,
            "request",
            autospec=True,
            side_effect=requests.ConnectionError("synthetic connection error"),
        ) as request:
            with pytest.raises(ServiceRequestError):
                await client.send_async(
                    "GET",
                    "https://example.test/items",
                    **request_options,
                )
    finally:
        await client.close()

    request.assert_called_once()
    assert "read_timeout" not in request.call_args.kwargs


@pytest.mark.asyncio
async def test_requests_transport_closes_through_generated_client_lifecycle() -> None:
    """Close a synchronous-close transport through its async context lifecycle."""
    direct_client = ConnectorHttpClient(
        AzureKeyCredential("test-key"),
        transport=AsyncioRequestsTransport(),
    )
    await direct_client.close()

    async with ConcreteConnectorClient(
        AzureKeyCredential("test-key"),
        transport=AsyncioRequestsTransport(),
    ) as generated_client:
        assert generated_client.connector_name == "test"


@pytest.mark.asyncio
async def test_unsafe_method_does_not_retry_by_default() -> None:
    """Keep unsafe connector operations to one attempt by default."""
    transport = RecordingTransport(
        create_response(status=500),
        create_response(status=200),
    )
    client = ConnectorHttpClient(
        AzureKeyCredential("test-key"),
        max_retry_attempts=2,
        initial_retry_delay_seconds=0,
        transport=transport,
    )

    response = await client.send_async("POST", "https://example.test/items")

    assert response.status == 500
    assert len(transport.requests) == 1


@pytest.mark.asyncio
async def test_unsafe_method_retries_when_enabled() -> None:
    """Retry an unsafe method only after explicit client opt-in."""
    transport = RecordingTransport(
        create_response(status=500),
        create_response(status=200),
    )
    client = ConnectorHttpClient(
        AzureKeyCredential("test-key"),
        max_retry_attempts=2,
        initial_retry_delay_seconds=0,
        retry_unsafe_http_methods=True,
        transport=transport,
    )

    response = await client.send_async("POST", "https://example.test/items")

    assert response.status == 200
    assert len(transport.requests) == 2


@pytest.mark.parametrize(
    ("retry_mode", "jitter", "expected_backoff", "expected_jitter_limit"),
    [
        (RetryMode.Fixed, 0.25, 1.25, 0.5),
        (RetryMode.Exponential, 0.5, 2.5, 1.0),
    ],
)
def test_jitter_retry_policy_adds_bounded_positive_jitter(
    retry_mode: RetryMode,
    jitter: float,
    expected_backoff: float,
    expected_jitter_limit: float,
) -> None:
    """Add bounded jitter to fixed and exponential Azure Core backoff."""
    policy = _JitterRetryPolicy(
        retry_mode=retry_mode,
        jitter_factor=0.5,
    )
    settings = {
        "history": [object(), object()],
        "backoff": 1.0,
        "max_backoff": 10.0,
    }

    with patch(
        "azure.connectors.sdk.http_client.random.uniform",
        return_value=jitter,
    ) as mock_uniform:
        backoff = policy.get_backoff_time(settings)

    assert backoff == expected_backoff
    mock_uniform.assert_called_once_with(0, expected_jitter_limit)


def test_jitter_retry_policy_caps_backoff_after_jitter() -> None:
    """Keep jittered backoff within the configured Azure Core maximum."""
    policy = _JitterRetryPolicy(
        retry_mode=RetryMode.Exponential,
        jitter_factor=0.5,
    )
    settings = {
        "history": [object(), object()],
        "backoff": 1.0,
        "max_backoff": 2.25,
    }

    with patch(
        "azure.connectors.sdk.http_client.random.uniform",
        return_value=0.5,
    ):
        backoff = policy.get_backoff_time(settings)

    assert backoff == 2.25


@pytest.mark.asyncio
async def test_injected_policies_run_at_their_configured_retry_scope() -> None:
    """Run per-call policies once and authenticated per-retry policies each attempt."""
    events: list[tuple[str, str | None]] = []
    transport = RecordingTransport(
        create_response(status=500),
        create_response(status=200),
    )
    client = ConnectorHttpClient(
        AzureKeyCredential("test-key"),
        max_retry_attempts=2,
        initial_retry_delay_seconds=0,
        retry_jitter_factor=0,
        per_call_policies=RecordingPolicy("per-call", events),
        per_retry_policies=[RecordingPolicy("per-retry", events)],
        transport=transport,
    )

    response = await client.send_async("GET", "https://example.test/items")

    assert response.status == 200
    assert events == [
        ("per-call", None),
        ("per-retry", "Bearer test-key"),
        ("per-retry", "Bearer test-key"),
    ]
