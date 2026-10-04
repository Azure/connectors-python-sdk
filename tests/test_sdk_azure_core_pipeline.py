"""Tests for the Azure Core asynchronous connector pipeline."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from azure.core.credentials import AccessToken, AzureKeyCredential
from azure.core.pipeline.policies import RetryMode, SansIOHTTPPolicy
from azure.core.pipeline.transport import AsyncHttpTransport

from azure.connectors.sdk import ConnectorHttpClient
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
    assert transport.requests[0].headers["x-ms-client-request-id"] == "request-id"
    hook.assert_called_once_with(response, response.headers)
    with pytest.raises(TypeError):
        response.headers["x-new"] = "value"


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
