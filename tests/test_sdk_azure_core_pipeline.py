"""Tests for the Azure Core asynchronous connector pipeline."""

from unittest.mock import AsyncMock, MagicMock

import pytest
from azure.core.credentials import AccessToken, AzureKeyCredential
from azure.core.pipeline.transport import AsyncHttpTransport

from azure.connectors.sdk import ConnectorHttpClient


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
