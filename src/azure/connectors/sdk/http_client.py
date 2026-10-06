# Copyright (c) Microsoft Corporation. All rights reserved.

"""Asynchronous HTTP client for connector operations."""

import asyncio
import json
import random
from importlib.metadata import PackageNotFoundError, version
from typing import Any, Dict, Generic, List, Mapping, Optional, TypeVar

from azure.core.credentials import AzureKeyCredential
from azure.core.credentials_async import AsyncTokenCredential
from azure.core.exceptions import ServiceResponseTimeoutError
from azure.core.pipeline import AsyncPipeline
from azure.core.pipeline.policies import (
    AsyncBearerTokenCredentialPolicy,
    AsyncRetryPolicy,
    AzureKeyCredentialPolicy,
    ContentDecodePolicy,
    CustomHookPolicy,
    DistributedTracingPolicy,
    HeadersPolicy,
    HttpLoggingPolicy,
    NetworkTraceLoggingPolicy,
    ProxyPolicy,
    RequestIdPolicy,
    RetryMode,
    UserAgentPolicy,
)
from azure.core.pipeline.transport import AioHttpTransport, AsyncHttpTransport
from azure.core.rest import HttpRequest

from .exceptions import ConnectorException
from .response import ConnectorResponseHook, ConnectorResponseSnapshot
from .serialization import to_wire

ResponseT = TypeVar("ResponseT")
_SAFE_RETRY_METHODS = frozenset({"GET", "HEAD", "OPTIONS", "TRACE"})
_ALL_RETRY_METHODS = frozenset(
    {"DELETE", "GET", "HEAD", "OPTIONS", "PATCH", "POST", "PUT", "TRACE"}
)
_AUTHENTICATION_AND_CONTENT_HEADERS = frozenset({"authorization", "content-type"})
_PROTECTED_OPERATION_HEADERS = _AUTHENTICATION_AND_CONTENT_HEADERS | frozenset(
    {"x-ms-client-request-id"}
)

try:
    _SDK_VERSION = version("azure-connectors")
except PackageNotFoundError:
    _SDK_VERSION = "0.0.0"


class _JitterRetryPolicy(AsyncRetryPolicy):
    """Add bounded positive jitter to Azure Core retry backoff."""

    def __init__(self, *, jitter_factor: float = 0.0, **kwargs: Any):
        """Initialize the retry policy."""
        super().__init__(**kwargs)
        self._jitter_factor = max(0.0, jitter_factor)

    def get_backoff_time(self, settings: Dict[str, Any]) -> float:
        """Return Azure Core backoff with optional positive jitter."""
        backoff = super().get_backoff_time(settings)
        if backoff <= 0 or self._jitter_factor == 0:
            return backoff

        jitter = random.uniform(0, backoff * self._jitter_factor)
        return min(settings["max_backoff"], backoff + jitter)


class ConnectorResponse(Generic[ResponseT]):
    """Represent a response from a connector operation."""

    def __init__(
        self,
        status_code: int,
        headers: Dict[str, str],
        value: Optional[ResponseT],
    ):
        """Initialize the response."""
        self.status_code = status_code
        self.headers = headers
        self.value = value

    @property
    def is_success_status_code(self) -> bool:
        """Check whether the response indicates success."""
        return 200 <= self.status_code < 300


class ConnectorHttpClient:
    """Asynchronous HTTP client with Azure Core policies."""

    API_HUB_SCOPES = ["https://apihub.azure.com/.default"]

    def __init__(
        self,
        credential: AsyncTokenCredential | AzureKeyCredential,
        *,
        max_retry_attempts: int = 3,
        timeout_seconds: float = 30.0,
        use_exponential_backoff: bool = True,
        initial_retry_delay_seconds: float = 0.5,
        maximum_retry_delay_seconds: float = 120.0,
        retry_jitter_factor: float = 0.1,
        retry_unsafe_http_methods: bool = False,
        transport: Optional[AsyncHttpTransport] = None,
        **kwargs: Any,
    ):
        """Initialize the HTTP client."""
        if credential is None:
            raise ValueError("credential cannot be None")

        self._credential = credential
        self._timeout_seconds = timeout_seconds
        self._retry_unsafe_http_methods = retry_unsafe_http_methods
        self._transport = transport or AioHttpTransport()
        policy_options = dict(kwargs)
        policies = policy_options.pop("policies", None)
        if policies is None:
            policies = self._build_policies(
                credential,
                policy_options,
                max_retry_attempts=max_retry_attempts,
                timeout_seconds=timeout_seconds,
                use_exponential_backoff=use_exponential_backoff,
                initial_retry_delay_seconds=initial_retry_delay_seconds,
                maximum_retry_delay_seconds=maximum_retry_delay_seconds,
                retry_jitter_factor=retry_jitter_factor,
            )
        self._pipeline = AsyncPipeline(self._transport, policies=policies)

    def _build_policies(
        self,
        credential: AsyncTokenCredential | AzureKeyCredential,
        policy_options: Dict[str, Any],
        *,
        max_retry_attempts: int,
        timeout_seconds: float,
        use_exponential_backoff: bool,
        initial_retry_delay_seconds: float,
        maximum_retry_delay_seconds: float,
        retry_jitter_factor: float,
    ) -> List[Any]:
        """Build the standard Azure Core asynchronous policy chain."""
        per_call_policies = self._as_policy_list(
            policy_options.pop("per_call_policies", [])
        )
        per_retry_policies = self._as_policy_list(
            policy_options.pop("per_retry_policies", [])
        )
        default_headers = {
            name: value
            for name, value in policy_options.pop("headers", {}).items()
            if name.lower() not in _AUTHENTICATION_AND_CONTENT_HEADERS
        }
        retry_total = policy_options.pop(
            "retry_total", max(0, max_retry_attempts - 1)
        )
        retry_connect = policy_options.pop("retry_connect", retry_total)
        retry_read = policy_options.pop("retry_read", retry_total)
        retry_status = policy_options.pop("retry_status", retry_total)
        retry_backoff_factor = policy_options.pop(
            "retry_backoff_factor", initial_retry_delay_seconds
        )
        retry_backoff_max = policy_options.pop(
            "retry_backoff_max", maximum_retry_delay_seconds
        )
        retry_mode = policy_options.pop(
            "retry_mode",
            RetryMode.Exponential if use_exponential_backoff else RetryMode.Fixed,
        )
        retry_timeout = policy_options.pop("timeout", timeout_seconds)
        jitter_factor = policy_options.pop(
            "retry_jitter_factor", retry_jitter_factor
        )
        policies = [
            policy_options.pop("headers_policy", None)
            or HeadersPolicy(base_headers=default_headers, **policy_options),
            policy_options.pop("request_id_policy", None)
            or RequestIdPolicy(**policy_options),
            policy_options.pop("user_agent_policy", None)
            or UserAgentPolicy(
                sdk_moniker=f"connectors/{_SDK_VERSION}", **policy_options
            ),
            policy_options.pop("proxy_policy", None)
            or ProxyPolicy(**policy_options),
            ContentDecodePolicy(**policy_options),
        ]
        policies.extend(per_call_policies)
        policies.extend(
            [
                policy_options.pop("retry_policy", None)
                or _JitterRetryPolicy(
                    retry_total=retry_total,
                    retry_connect=retry_connect,
                    retry_read=retry_read,
                    retry_status=retry_status,
                    retry_backoff_factor=retry_backoff_factor,
                    retry_backoff_max=retry_backoff_max,
                    retry_mode=retry_mode,
                    timeout=retry_timeout,
                    jitter_factor=jitter_factor,
                    **policy_options,
                ),
                policy_options.pop("authentication_policy", None)
                or self._build_authentication_policy(
                    credential,
                    policy_options,
                ),
                policy_options.pop("custom_hook_policy", None)
                or CustomHookPolicy(**policy_options),
            ]
        )
        policies.extend(per_retry_policies)
        policies.extend(
            [
                policy_options.pop("logging_policy", None)
                or NetworkTraceLoggingPolicy(**policy_options),
                policy_options.pop("distributed_tracing_policy", None)
                or DistributedTracingPolicy(**policy_options),
                policy_options.pop("http_logging_policy", None)
                or HttpLoggingPolicy(**policy_options),
            ]
        )
        return policies

    @classmethod
    def _build_authentication_policy(
        cls,
        credential: AsyncTokenCredential | AzureKeyCredential,
        policy_options: Dict[str, Any],
    ) -> Any:
        """Build the authentication policy for the credential type."""
        if isinstance(credential, AzureKeyCredential):
            return AzureKeyCredentialPolicy(
                credential,
                "Authorization",
                prefix="Bearer",
                **policy_options,
            )

        return AsyncBearerTokenCredentialPolicy(
            credential,
            *cls.API_HUB_SCOPES,
            **policy_options,
        )

    @staticmethod
    def _as_policy_list(policies: Any) -> List[Any]:
        """Normalize one policy or an iterable of policies to a list."""
        if policies is None:
            return []
        if isinstance(policies, (list, tuple)):
            return list(policies)
        return [policies]

    async def close(self) -> None:
        """Close the HTTP transport without closing the caller credential."""
        await self._transport.close()

    async def send_async(
        self,
        method: str,
        url: str,
        body: Optional[Any] = None,
        content_type: Optional[str] = None,
        *,
        timeout: Optional[float] = None,
        headers: Optional[Mapping[str, str]] = None,
        client_request_id: Optional[str] = None,
        response_hook: Optional[ConnectorResponseHook] = None,
    ) -> ConnectorResponseSnapshot:
        """Send an HTTP request within the selected total network timeout."""
        is_binary_body = isinstance(body, (bytes, bytearray))
        if content_type is None:
            content_type = (
                "application/octet-stream" if is_binary_body else "application/json"
            )
        operation_headers = {
            name: value
            for name, value in (headers or {}).items()
            if name.lower() not in _PROTECTED_OPERATION_HEADERS
        }
        request_headers = dict(operation_headers)
        request_headers["Content-Type"] = content_type
        request_body: Optional[Any] = None
        if body is not None:
            request_body = bytes(body) if is_binary_body else json.dumps(to_wire(body))

        response = await self._send_with_retry(
            self._pipeline,
            method,
            url,
            request_headers,
            request_body,
            client_request_id=client_request_id,
            timeout=timeout,
        )
        if response_hook is not None:
            response_hook(response, response.headers)
        return response

    async def _send_with_retry(
        self,
        pipeline: AsyncPipeline,
        method: str,
        url: str,
        headers: Dict[str, str],
        body: Optional[Any],
        *,
        client_request_id: Optional[str] = None,
        timeout: Optional[float] = None,
    ) -> ConnectorResponseSnapshot:
        """Send a request within one total Azure Core pipeline timeout."""
        normalized_method = method.upper()
        request = HttpRequest(normalized_method, url, headers=headers, content=body)
        selected_timeout = (
            timeout if timeout is not None else self._timeout_seconds
        )
        request_options: Dict[str, Any] = {
            "timeout": selected_timeout,
            "headers": headers,
        }
        if selected_timeout > 0:
            request_options["read_timeout"] = selected_timeout
        if normalized_method not in _SAFE_RETRY_METHODS:
            if self._retry_unsafe_http_methods:
                request_options["retry_on_methods"] = (
                    _ALL_RETRY_METHODS | {normalized_method}
                )
            else:
                request_options["retry_total"] = 0
        if client_request_id is not None:
            request_options["request_id"] = client_request_id

        async def send_request() -> ConnectorResponseSnapshot:
            pipeline_response = await pipeline.run(request, **request_options)
            http_response = pipeline_response.http_response
            response_content = await http_response.read()
            return ConnectorResponseSnapshot(
                status=http_response.status_code,
                headers=dict(http_response.headers),
                text=http_response.text(),
                content=response_content,
            )

        if selected_timeout <= 0:
            return await send_request()

        try:
            return await asyncio.wait_for(
                send_request(),
                timeout=selected_timeout,
            )
        except asyncio.TimeoutError as ex:
            raise ServiceResponseTimeoutError(
                message=(
                    f"Request to '{url}' exceeded the total timeout of "
                    f"'{selected_timeout}' seconds."
                ),
                error=ex,
            ) from ex

    async def get_async(self, request_uri: str) -> Any:
        """Send a GET request."""
        response = await self.send_async("GET", request_uri)
        if not 200 <= response.status < 300:
            raise ConnectorException(
                "GET",
                request_uri,
                response.status,
                response.text,
            )

        return json.loads(response.text) if response.text else None

    async def post_async(self, request_uri: str, body: Any) -> Any:
        """Send a POST request with a JSON body."""
        response = await self.send_async("POST", request_uri, body)
        if not 200 <= response.status < 300:
            raise ConnectorException(
                "POST",
                request_uri,
                response.status,
                response.text,
            )

        return json.loads(response.text) if response.text else None
