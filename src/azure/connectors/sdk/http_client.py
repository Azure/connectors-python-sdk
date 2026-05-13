# Copyright (c) Microsoft Corporation. All rights reserved.

"""HTTP client for connector operations with retry and authentication."""

import asyncio
import json
from dataclasses import asdict, is_dataclass
from typing import Any, Dict, List, NamedTuple, Optional, TypeVar, Generic, cast
import aiohttp
from aiohttp import ClientTimeout

from .authentication import TokenProvider
from .options import ConnectorClientOptions
from .exceptions import ConnectorException

T = TypeVar("T")


class _ResponseSnapshot(NamedTuple):
    """Immutable snapshot of an HTTP response for use after context exits."""

    status: int
    headers: Dict[str, str]
    text: str
    content: bytes


class ConnectorResponse(Generic[T]):
    """Represents a response from a connector operation."""

    def __init__(
        self, status_code: int, headers: Dict[str, str], value: Optional[T]
    ):
        """
        Initialize a ConnectorResponse.

        Args:
            status_code: The HTTP status code.
            headers: The response headers.
            value: The response value.
        """
        self.status_code = status_code
        self.headers = headers
        self.value = value

    @property
    def is_success_status_code(self) -> bool:
        """Check if the response indicates success."""
        return 200 <= self.status_code < 300


class ConnectorHttpClient:
    """HTTP client for connector operations with retry and authentication."""

    API_HUB_SCOPES = ["https://apihub.azure.com/.default"]

    def __init__(
        self,
        token_provider: TokenProvider,
        options: ConnectorClientOptions,
    ):
        """
        Initialize a ConnectorHttpClient.

        Args:
            token_provider: The token provider for authentication.
            options: The client options.
        """
        self._token_provider = token_provider
        self._options = options
        self._session: Optional[aiohttp.ClientSession] = None

    async def _ensure_session(self) -> aiohttp.ClientSession:
        """Ensure the HTTP session is initialized."""
        if self._session is None or self._session.closed:
            timeout = ClientTimeout(total=self._options.timeout_seconds)
            self._session = aiohttp.ClientSession(timeout=timeout)
        return self._session

    async def close(self):
        """Close the HTTP session and token provider."""
        if self._session and not self._session.closed:
            await self._session.close()
            self._session = None

        # Close the token provider if it has a close method
        if hasattr(self._token_provider, 'close'):
            await self._token_provider.close()

    async def send_async(
        self,
        method: str,
        url: str,
        scopes: Optional[List[str]] = None,
        body: Optional[Any] = None,
    ) -> _ResponseSnapshot:
        """
        Send an HTTP request with authentication and retry.

        Args:
            method: The HTTP method.
            url: The request URL.
            scopes: The authentication scopes. Defaults to API Hub scopes.
            body: Optional request body (will be JSON-serialized).

        Returns:
            The HTTP response.
        """
        if scopes is None:
            scopes = self.API_HUB_SCOPES

        token = await self._token_provider.get_access_token_async(scopes)
        session = await self._ensure_session()

        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }

        # NOTE(victoriahall): Convert dataclass objects to dictionaries
        # for JSON serialization. Generated connector clients pass
        # dataclass instances as body parameters.
        json_body = None
        if body is not None:
            if is_dataclass(body) and not isinstance(body, type):
                # Convert dataclass to dict, excluding None values
                body_dict = asdict(cast(Any, body))

                # NOTE(victoriahall): Handle dynamic schemas with
                # additional_properties. Extract additional_properties and
                # merge into main dict (like .NET [JsonExtensionData]).
                if 'additional_properties' in body_dict:
                    additional_props = body_dict.pop(
                        'additional_properties'
                    )
                    if additional_props:
                        # Merge additional properties into the main dict
                        body_dict.update(additional_props)

                # Filter out None values to avoid sending null fields
                body_dict = {
                    k: v for k, v in body_dict.items() if v is not None
                }
                json_body = json.dumps(body_dict)
            else:
                json_body = json.dumps(body)

        return await self._send_with_retry(
            session, method, url, headers, json_body
        )

    async def _send_with_retry(
        self,
        session: aiohttp.ClientSession,
        method: str,
        url: str,
        headers: Dict[str, str],
        body: Optional[str],
    ) -> _ResponseSnapshot:
        """Send request with retry logic."""
        last_exception = None

        for attempt in range(self._options.max_retry_attempts):
            try:
                async with session.request(
                    method, url, headers=headers, data=body
                ) as response:
                    # For transient errors, retry
                    if response.status >= 500 or response.status == 429:
                        if (
                            attempt < self._options.max_retry_attempts - 1
                        ):
                            await self._delay_retry(attempt)
                            continue

                    # Return response for caller to handle
                    response_text = await response.text()
                    response_content = await response.read()
                    return _ResponseSnapshot(
                        status=response.status,
                        headers=dict(response.headers),
                        text=response_text,
                        content=response_content,
                    )

            except aiohttp.ClientError as ex:
                last_exception = ex
                if attempt < self._options.max_retry_attempts - 1:
                    await self._delay_retry(attempt)
                    continue
                raise

        # NOTE(victoriahall): If all retries exhausted without returning,
        # raise the last exception or a generic error.
        if last_exception:
            raise last_exception
        raise ConnectorException(
            "RETRY",
            "Request failed after all retry attempts.",
            0,
            "",
        )

    async def _delay_retry(self, attempt: int):
        """Calculate and apply retry delay."""
        if self._options.use_exponential_backoff:
            delay = (
                self._options.initial_retry_delay_seconds * (2 ** attempt)
            )
        else:
            delay = self._options.initial_retry_delay_seconds

        await asyncio.sleep(delay)

    async def get_async(
        self, request_uri: str, scopes: Optional[List[str]] = None
    ) -> Any:
        """
        Send a GET request.

        Args:
            request_uri: The request URI.
            scopes: Optional authentication scopes.

        Returns:
            The deserialized response.
        """
        response = await self.send_async("GET", request_uri, scopes)

        if not (200 <= response.status < 300):
            raise ConnectorException(
                "GET",
                request_uri,
                response.status,
                response.text,
            )

        if not response.text:
            return None

        return json.loads(response.text)

    async def post_async(
        self,
        request_uri: str,
        body: Any,
        scopes: Optional[List[str]] = None,
    ) -> Any:
        """
        Send a POST request with JSON body.

        Args:
            request_uri: The request URI.
            body: The request body.
            scopes: Optional authentication scopes.

        Returns:
            The deserialized response.
        """
        response = await self.send_async("POST", request_uri, scopes, body)

        if not (200 <= response.status < 300):
            raise ConnectorException(
                "POST",
                request_uri,
                response.status,
                response.text,
            )

        if not response.text:
            return None

        return json.loads(response.text)
