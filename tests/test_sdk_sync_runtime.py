# Copyright (c) Microsoft Corporation. All rights reserved.

"""Tests for the Azure Core synchronous connector runtime."""

import json
import threading
import time
from dataclasses import dataclass
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from unittest.mock import MagicMock

import pytest
from azure.core.credentials import AccessToken, AzureKeyCredential
from azure.core.exceptions import ServiceResponseTimeoutError
from azure.core.pipeline.policies import HeadersPolicy, RetryPolicy, SansIOHTTPPolicy
from azure.core.pipeline.transport import HttpTransport

from azure.connectors.sdk import ConnectorClientBase, ConnectorHttpClient


class RecordingCredential:
    """Record token requests and lifecycle calls."""

    def __init__(self) -> None:
        """Initialize the credential."""
        self.scopes: tuple[str, ...] | None = None
        self.closed = False

    def get_token(self, *scopes: str, **kwargs: object) -> AccessToken:
        """Return a test token."""
        del kwargs
        self.scopes = scopes
        return AccessToken("test-token", 4_102_444_800)

    def close(self) -> None:
        """Record an ownership violation."""
        self.closed = True


class RecordingTransport(HttpTransport):
    """Record requests and return configured responses."""

    def __init__(self, *responses: object) -> None:
        """Initialize the transport."""
        self.responses = list(responses)
        self.requests: list[object] = []
        self.request_options: list[dict[str, object]] = []
        self.sleep_durations: list[float] = []
        self.closed = False

    def send(self, request: object, **kwargs: object) -> MagicMock:
        """Record and answer a request."""
        self.requests.append(request)
        self.request_options.append(kwargs)
        response = self.responses.pop(0)
        if isinstance(response, Exception):
            raise response
        return response

    def open(self) -> None:
        """Open the transport."""

    def close(self) -> None:
        """Close the transport."""
        self.closed = True

    def __enter__(self):
        """Enter the transport context."""
        return self

    def __exit__(self, *args: object) -> None:
        """Exit the transport context."""
        self.close()

    def sleep(self, duration: float) -> None:
        """Record a retry delay without waiting."""
        self.sleep_durations.append(duration)


class RecordingPolicy(SansIOHTTPPolicy):
    """Record policy execution and authorization state."""

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


@dataclass
class RequestBody:
    """Represent a serializable request body."""

    item_name: str
    omitted: str | None = None


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
    response.text = MagicMock(return_value=content.decode("utf-8"))
    return response


def test_token_credential_uses_fixed_scope_and_remains_open() -> None:
    """Use the API Hub scope without taking credential ownership."""
    credential = RecordingCredential()
    transport = RecordingTransport(create_response(status=204, content=b""))
    client = ConnectorHttpClient(credential, transport=transport)

    client.send("GET", "https://example.test/items")
    client.close()

    assert credential.scopes == ("https://apihub.azure.com/.default",)
    assert transport.requests[0].headers["Authorization"] == "Bearer test-token"
    assert credential.closed is False
    assert transport.closed is True


def test_request_controls_and_serialization_are_applied() -> None:
    """Protect auth headers, serialize bodies, and invoke response hooks."""
    transport = RecordingTransport(create_response(headers={"x-result": "complete"}))
    hook = MagicMock()
    client = ConnectorHttpClient(
        AzureKeyCredential("test-key"),
        transport=transport,
    )

    response = client.send(
        "POST",
        "https://example.test/items",
        RequestBody(item_name="item"),
        headers={"x-custom": "value", "Authorization": "ignored"},
        client_request_id="request-id",
        response_hook=hook,
    )

    request = transport.requests[0]
    assert request.headers["Authorization"] == "Bearer test-key"
    assert request.headers["x-custom"] == "value"
    assert request.headers["x-ms-client-request-id"] == "request-id"
    assert json.loads(request.content) == {"item_name": "item"}
    hook.assert_called_once_with(response, response.headers)


@pytest.mark.parametrize(
    ("default_timeout", "request_timeout"),
    [
        (0.1, None),
        (1.0, 0.1),
    ],
)
def test_timeout_request_runs_transport_on_calling_thread(
    default_timeout: float,
    request_timeout: float | None,
) -> None:
    """Keep timed synchronous transport work on the caller thread."""

    class ThreadRecordingTransport(RecordingTransport):
        """Record the thread that executes the transport request."""

        def __init__(self, *responses: object) -> None:
            """Initialize the transport."""
            super().__init__(*responses)
            self.send_thread_id: int | None = None

        def send(self, request: object, **kwargs: object) -> MagicMock:
            """Record the current thread before sending the request."""
            self.send_thread_id = threading.get_ident()
            return super().send(request, **kwargs)

    transport = ThreadRecordingTransport(create_response())
    client = ConnectorHttpClient(
        AzureKeyCredential("test-key"),
        max_retry_attempts=1,
        timeout_seconds=default_timeout,
        transport=transport,
    )

    client.send(
        "GET",
        "https://example.test/items",
        timeout=request_timeout,
    )
    client.close()

    assert transport.send_thread_id == threading.get_ident()
    assert transport.closed is True


def test_timeout_bounds_slow_drip_response_body() -> None:
    """Enforce one elapsed deadline while a response body keeps producing data."""

    class SlowDripHandler(BaseHTTPRequestHandler):
        """Write response bytes frequently enough to evade a socket idle timeout."""

        def do_GET(self) -> None:
            """Write one byte per interval until the client closes the response."""
            self.send_response(200)
            self.send_header("Content-Length", "10")
            self.end_headers()
            try:
                for _ in range(10):
                    self.wfile.write(b"x")
                    self.wfile.flush()
                    time.sleep(0.04)
            except (BrokenPipeError, ConnectionResetError):
                pass

        def log_message(self, format: str, *args: object) -> None:
            """Suppress local server request logs."""
            del format, args

    server = ThreadingHTTPServer(("127.0.0.1", 0), SlowDripHandler)
    server_thread = threading.Thread(target=server.serve_forever, daemon=True)
    server_thread.start()
    client = ConnectorHttpClient(
        AzureKeyCredential("test-key"),
        max_retry_attempts=1,
        timeout_seconds=0.1,
    )

    try:
        started_at = time.monotonic()
        with pytest.raises(ServiceResponseTimeoutError):
            client.send("GET", f"http://127.0.0.1:{server.server_port}/")
        elapsed = time.monotonic() - started_at
    finally:
        client.close()
        server.shutdown()
        server.server_close()
        server_thread.join()

    assert elapsed < 0.3


def test_default_transport_uses_standard_tls_options() -> None:
    """Apply standard Azure Core TLS options to the owned Requests transport."""
    client = ConnectorHttpClient(
        AzureKeyCredential("test-key"),
        connection_verify=False,
        connection_cert="client.pem",
    )

    try:
        assert client._transport.connection_config.verify is False
        assert client._transport.connection_config.cert == "client.pem"
    finally:
        client.close()


def test_unsafe_method_does_not_retry_by_default() -> None:
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

    response = client.send("POST", "https://example.test/items")

    assert response.status == 500
    assert len(transport.requests) == 1


def test_unsafe_method_retries_when_enabled() -> None:
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

    response = client.send("POST", "https://example.test/items")

    assert response.status == 200
    assert len(transport.requests) == 2


def test_explicit_chain_composes_injected_policy_scopes() -> None:
    """Compose per-call and per-retry extensions with an explicit chain."""
    events: list[tuple[str, str | None]] = []
    transport = RecordingTransport(
        create_response(status=500),
        create_response(status=200),
    )
    client = ConnectorHttpClient(
        AzureKeyCredential("test-key"),
        policies=[HeadersPolicy(), RetryPolicy(retry_total=1, retry_backoff_factor=0)],
        per_call_policies=RecordingPolicy("per-call", events),
        per_retry_policies=[RecordingPolicy("per-retry", events)],
        transport=transport,
    )

    response = client.send("GET", "https://example.test/items")

    assert response.status == 200
    assert events == [
        ("per-call", None),
        ("per-retry", None),
        ("per-retry", None),
    ]


def test_explicit_chain_rejects_per_retry_policy_without_retry() -> None:
    """Reject per-retry extensions when an explicit chain cannot run them."""
    with pytest.raises(ValueError, match="no RetryPolicy"):
        ConnectorHttpClient(
            AzureKeyCredential("test-key"),
            policies=[HeadersPolicy()],
            per_retry_policies=RecordingPolicy("per-retry", []),
        )


def test_explicit_no_retry_chain_preserves_transport_timeout() -> None:
    """Forward positive timeouts when an explicit chain omits retry policy."""
    transport = RecordingTransport(create_response())
    client = ConnectorHttpClient(
        AzureKeyCredential("test-key"),
        policies=[HeadersPolicy()],
        transport=transport,
    )

    response = client.send(
        "GET",
        "https://example.test/items",
        timeout=5.0,
    )

    assert response.status == 200
    assert transport.request_options[0]["connection_timeout"] == 5.0


def test_generated_client_uses_synchronous_context_lifecycle() -> None:
    """Close the owned transport through the generated client lifecycle."""
    transport = RecordingTransport(create_response())

    with ConcreteConnectorClient(
        AzureKeyCredential("test-key"),
        timeout=60.0,
        transport=transport,
    ) as client:
        assert client.connector_name == "test"
        assert client.http_client._timeout_seconds == 60.0

    assert transport.closed is True
