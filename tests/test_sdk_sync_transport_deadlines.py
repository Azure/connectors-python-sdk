# Copyright (c) Microsoft Corporation. All rights reserved.

"""Focused regressions for the real synchronous Requests transport."""

from __future__ import annotations

import gzip
import threading
import time
from collections.abc import Callable, Generator
from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from unittest.mock import MagicMock

import pytest
import requests
from azure.core.credentials import AzureKeyCredential
from azure.core.exceptions import ServiceResponseTimeoutError
from azure.core.pipeline.policies import SansIOHTTPPolicy
from azure.core.rest import HttpRequest, HttpResponse
from urllib3.exceptions import ReadTimeoutError
from urllib3.poolmanager import PoolManager, pool_classes_by_scheme

from azure.connectors.sdk.http_client import (
    ConnectorHttpClient,
    _DeadlineAdapter,
    _DeadlineHTTPResponse,
    _REQUEST_DEADLINE,
    _REQUEST_RESPONSES,
)

Responder = Callable[[BaseHTTPRequestHandler, threading.Event], None]


@contextmanager
def local_server(respond: Responder) -> Generator[str, None, None]:
    """Run a loopback server and join every server thread during cleanup."""
    stopping = threading.Event()

    class Handler(BaseHTTPRequestHandler):
        """Dispatch requests to the test's response writer."""

        protocol_version = "HTTP/1.1"

        def setup(self) -> None:
            """Bound idle keep-alive waits so server cleanup always joins."""
            self.request.settimeout(2.0)
            super().setup()

        def do_GET(self) -> None:
            """Write the configured response until the client disconnects."""
            try:
                respond(self, stopping)
            except (BrokenPipeError, ConnectionResetError, ConnectionAbortedError):
                pass

        def do_HEAD(self) -> None:
            """Allow tests to exercise bodyless responses."""
            self.do_GET()

        def log_message(self, format: str, *args: object) -> None:
            """Suppress local server request logs."""
            del format, args

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    server.daemon_threads = False
    server_thread = threading.Thread(
        target=lambda: server.serve_forever(poll_interval=0.01)
    )
    server_thread.start()
    try:
        yield f"http://127.0.0.1:{server.server_port}/"
    finally:
        stopping.set()
        server.shutdown()
        server.server_close()
        server_thread.join()


@pytest.mark.parametrize("timeout", [None, 2.0, 0.0])
@pytest.mark.parametrize("connection_close", [False, True])
def test_default_transport_reads_complete_fixed_length_body(
    timeout: float | None, connection_close: bool,
) -> None:
    """Accept nonempty successful responses with default, positive and no timeout."""
    payload = b'{"message":"completed"}'
    authorization_headers: list[str | None] = []

    def respond(handler: BaseHTTPRequestHandler, stopping: threading.Event) -> None:
        del stopping
        authorization_headers.append(handler.headers.get("Authorization"))
        handler.send_response(200)
        handler.send_header("Content-Length", str(len(payload)))
        handler.send_header("Content-Type", "application/json; charset=utf-8")
        if connection_close:
            handler.send_header("Connection", "close")
        handler.end_headers()
        handler.wfile.write(payload)
        handler.wfile.flush()

    with local_server(respond) as url:
        client = ConnectorHttpClient(AzureKeyCredential("test-key"))
        try:
            for _ in range(2):
                response = client.send("GET", url, timeout=timeout)
                assert response.status == 200
                assert response.content == payload
                assert response.text == payload.decode("utf-8")
        finally:
            client.close()

    assert authorization_headers == ["Bearer test-key", "Bearer test-key"]


@pytest.mark.parametrize("timeout", [0.0, -1.0])
def test_nonpositive_timeout_allows_slow_headers(timeout: float) -> None:
    """Disable the per-receive deadline when the operation opts out."""
    def respond(handler: BaseHTTPRequestHandler, stopping: threading.Event) -> None:
        handler.wfile.write(b"HTTP/1.1 200 OK\r\nX-Slow: ")
        handler.wfile.flush()
        for _ in range(5):
            if stopping.wait(0.04):
                return
            handler.wfile.write(b"x")
            handler.wfile.flush()
        handler.wfile.write(b"\r\nContent-Length: 2\r\n\r\nok")
        handler.wfile.flush()

    with local_server(respond) as url:
        client = ConnectorHttpClient(
            AzureKeyCredential("test-key"), timeout_seconds=0.1
        )
        try:
            response = client.send("GET", url, timeout=timeout)
            assert response.content == b"ok"
        finally:
            client.close()


@pytest.mark.parametrize("kind", ["gzip", "chunked", "head", "empty"])
def test_default_transport_preserves_body_framing_and_decoding(kind: str) -> None:
    """Let the supported response iterator handle decoding and completed bodies."""
    payload = b"nonempty response" * 100

    def respond(handler: BaseHTTPRequestHandler, stopping: threading.Event) -> None:
        del stopping
        handler.send_response(200)
        if kind == "chunked":
            handler.send_header("Transfer-Encoding", "chunked")
            handler.end_headers()
            handler.wfile.write(b"3\r\none\r\n3\r\ntwo\r\n0\r\n\r\n")
        else:
            content = gzip.compress(payload) if kind == "gzip" else b""
            handler.send_header(
                "Content-Length", str(len(payload) if kind == "head" else len(content))
            )
            if kind == "gzip":
                handler.send_header("Content-Encoding", "gzip")
            handler.end_headers()
            handler.wfile.write(content)
        handler.wfile.flush()

    with local_server(respond) as url:
        client = ConnectorHttpClient(AzureKeyCredential("test-key"))
        try:
            response = client.send("HEAD" if kind == "head" else "GET", url)
        finally:
            client.close()

    expected = payload if kind == "gzip" else b"onetwo" if kind == "chunked" else b""
    assert response.status == 200
    assert response.content == expected


@pytest.mark.parametrize("phase", ["status", "headers", "chunk_headers", "body"])
@pytest.mark.parametrize("request_timeout", [None, 0.1])
def test_total_deadline_bounds_slow_drip_network_reads(
    phase: str, request_timeout: float | None,
) -> None:
    """Interrupt slow-drip parsing before the server's roughly 0.6-second finish."""
    disconnected = threading.Event()

    def respond(handler: BaseHTTPRequestHandler, stopping: threading.Event) -> None:
        try:
            if phase == "status":
                handler.wfile.write(b"HTTP/1.1 200 ")
                fragments = [b"O"] * 15 + [b"K\r\nContent-Length: 2\r\n\r\nok"]
            elif phase == "headers":
                handler.wfile.write(b"HTTP/1.1 200 OK\r\nX-Slow: ")
                fragments = [b"x"] * 15 + [b"\r\nContent-Length: 2\r\n\r\nok"]
            elif phase == "chunk_headers":
                handler.wfile.write(
                    b"HTTP/1.1 200 OK\r\nTransfer-Encoding: chunked\r\n\r\n1;"
                )
                fragments = [b"x"] * 15 + [b"\r\nx\r\n0\r\n\r\n"]
            else:
                handler.wfile.write(b"HTTP/1.1 200 OK\r\nContent-Length: 16\r\n\r\n")
                fragments = [b"x"] * 16
            handler.wfile.flush()
            for fragment in fragments:
                if stopping.wait(0.04):
                    return
                handler.wfile.write(fragment)
                handler.wfile.flush()
        except (BrokenPipeError, ConnectionResetError, ConnectionAbortedError):
            disconnected.set()

    with local_server(respond) as url:
        client = ConnectorHttpClient(
            AzureKeyCredential("test-key"),
            max_retry_attempts=1,
            timeout_seconds=0.1 if request_timeout is None else 2.0,
        )
        try:
            started_at = time.monotonic()
            with pytest.raises(ServiceResponseTimeoutError):
                client.send("GET", url, timeout=request_timeout)
            elapsed = time.monotonic() - started_at
            assert elapsed < 0.3
            assert disconnected.wait(1.0)
            assert _REQUEST_DEADLINE.get() is None
            assert _REQUEST_RESPONSES.get() is None
        finally:
            client.close()


@pytest.mark.parametrize("phase", ["pipeline", "body"])
def test_raw_urllib3_read_timeout_is_normalized_before_deadline(phase: str) -> None:
    """Never expose raw urllib3 timeout exceptions, even before total expiry."""
    error = ReadTimeoutError(None, "/", "injected idle timeout")
    response = MagicMock()
    pipeline = MagicMock()
    if phase == "pipeline":
        pipeline.run.side_effect = error
    else:
        pipeline.run.return_value.http_response = response
        response.iter_bytes.side_effect = error

    with pytest.raises(ServiceResponseTimeoutError) as raised:
        ConnectorHttpClient._run_pipeline(
            pipeline,
            HttpRequest("GET", "https://example.test/"),
            {},
            total_timeout=10.0,
        )

    assert raised.value.__cause__ is error
    if phase == "body":
        response.close.assert_called_once_with()
    assert _REQUEST_DEADLINE.get() is None
    assert _REQUEST_RESPONSES.get() is None


def test_retry_after_wait_obeys_deadline_and_closes_response() -> None:
    """Do not retain a streamed retry response or sleep past the call budget."""
    disconnected = threading.Event()

    def respond(handler: BaseHTTPRequestHandler, stopping: threading.Event) -> None:
        handler.send_response(503)
        handler.send_header("Content-Length", "100")
        handler.send_header("Retry-After", "2")
        handler.end_headers()
        try:
            while not stopping.wait(0.02):
                handler.wfile.write(b"x")
                handler.wfile.flush()
        except (BrokenPipeError, ConnectionResetError, ConnectionAbortedError):
            disconnected.set()

    with local_server(respond) as url:
        client = ConnectorHttpClient(
            AzureKeyCredential("test-key"), timeout_seconds=0.1
        )
        try:
            started_at = time.monotonic()
            with pytest.raises(ServiceResponseTimeoutError):
                client.send("GET", url)
            assert time.monotonic() - started_at < 0.3
            assert disconnected.wait(1.0)
        finally:
            client.close()


def test_failed_request_does_not_poison_reused_client_or_other_thread() -> None:
    """Keep request deadlines isolated and permit success after a timeout."""
    def respond(handler: BaseHTTPRequestHandler, stopping: threading.Event) -> None:
        if handler.path == "/slow":
            handler.wfile.write(b"HTTP/1.1 200 OK\r\nX-Slow: ")
            handler.wfile.flush()
            for _ in range(10):
                if stopping.wait(0.04):
                    return
                handler.wfile.write(b"x")
                handler.wfile.flush()
            handler.wfile.write(b"\r\nContent-Length: 2\r\n\r\nok")
        else:
            if stopping.wait(0.2):
                return
            handler.send_response(200)
            handler.send_header("Content-Length", "2")
            handler.end_headers()
            handler.wfile.write(b"ok")
        handler.wfile.flush()

    with local_server(respond) as url:
        short_client = ConnectorHttpClient(
            AzureKeyCredential("short-key"), max_retry_attempts=1
        )
        long_client = ConnectorHttpClient(AzureKeyCredential("long-key"))

        def send_short_request() -> None:
            with pytest.raises(ServiceResponseTimeoutError):
                short_client.send("GET", url + "slow", timeout=0.1)
            assert _REQUEST_DEADLINE.get() is None

        try:
            with ThreadPoolExecutor(max_workers=2) as executor:
                short_result = executor.submit(send_short_request)
                long_result = executor.submit(long_client.send, "GET", url, timeout=1.0)
                short_result.result(timeout=2.0)
                assert long_result.result(timeout=2.0).content == b"ok"
            assert short_client.send("GET", url, timeout=1.0).content == b"ok"
        finally:
            short_client.close()
            long_client.close()


def test_deadline_pools_preserve_tls_proxy_types_and_global_registry() -> None:
    """Customize instance-local subclasses, retaining HTTPS and proxy behavior."""
    original_pools = dict(pool_classes_by_scheme)
    adapter = _DeadlineAdapter()
    try:
        managers = [
            adapter.poolmanager,
            adapter.proxy_manager_for("http://localhost:8080"),
            adapter.proxy_manager_for("https://localhost:8443"),
        ]
        for manager in managers:
            for scheme, pool_class in manager.pool_classes_by_scheme.items():
                original_pool = original_pools[scheme]
                assert issubclass(pool_class, original_pool)
                assert issubclass(pool_class.ConnectionCls, original_pool.ConnectionCls)
                assert pool_class.ConnectionCls.response_class is _DeadlineHTTPResponse
        assert pool_classes_by_scheme == original_pools
        assert PoolManager().pool_classes_by_scheme == original_pools
    finally:
        adapter.close()


def test_caller_session_is_not_remounted_or_closed() -> None:
    """Leave caller-provided session configuration and ownership unchanged."""
    session = requests.Session()
    adapters = dict(session.adapters)
    client = ConnectorHttpClient(
        AzureKeyCredential("test-key"), session=session, session_owner=False
    )
    try:
        client._transport.open()
        assert session.adapters == adapters
        client.close()
        assert client._transport.session is session
        assert session.adapters == adapters
    finally:
        session.close()


def test_response_policy_failure_closes_response_without_background_work() -> None:
    """Close a response even when a pipeline callback fails before run returns."""
    disconnected = threading.Event()
    callback_threads: list[int] = []
    responses: list[HttpResponse] = []

    class RejectingPolicy(SansIOHTTPPolicy):
        """Fail after the transport has returned response headers."""

        def on_request(self, request) -> None:
            """Record synchronous policy execution."""
            del request
            callback_threads.append(threading.get_ident())

        def on_response(self, request, response) -> None:
            """Record the response and raise a caller-defined failure."""
            del request
            callback_threads.append(threading.get_ident())
            responses.append(response.http_response)
            raise ValueError("Rejected by the caller's response policy.")

    class CallerCredential(AzureKeyCredential):
        """Record whether client cleanup incorrectly closes its credential."""

        closed = False

        def close(self) -> None:
            """Record a credential ownership violation."""
            self.closed = True

    def respond(handler: BaseHTTPRequestHandler, stopping: threading.Event) -> None:
        handler.send_response(200)
        handler.send_header("Content-Length", "100")
        handler.end_headers()
        try:
            while not stopping.wait(0.02):
                handler.wfile.write(b"x")
                handler.wfile.flush()
        except (BrokenPipeError, ConnectionResetError, ConnectionAbortedError):
            disconnected.set()

    credential = CallerCredential("test-key")
    with local_server(respond) as url:
        client = ConnectorHttpClient(credential, per_call_policies=[RejectingPolicy()])
        try:
            with pytest.raises(ValueError, match="Rejected by the caller"):
                client.send("GET", url)
            assert disconnected.wait(1.0)
            assert len(responses) == 1
            assert responses[0].is_closed
            assert callback_threads == [threading.get_ident()] * 2
        finally:
            client.close()

    assert credential.closed is False
    assert _REQUEST_DEADLINE.get() is None
    assert _REQUEST_RESPONSES.get() is None
