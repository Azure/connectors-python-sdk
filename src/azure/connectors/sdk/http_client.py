# Copyright (c) Microsoft Corporation. All rights reserved.

"""Synchronous HTTP client for connector operations."""

from __future__ import annotations

import io
import json
import random
import time
from contextvars import ContextVar
from http.client import HTTPResponse
from importlib.metadata import PackageNotFoundError, version
from threading import Lock
from typing import Any, Dict, Generic, List, Mapping, Optional, TypeVar

import requests
from azure.core.credentials import AzureKeyCredential, TokenCredential
from azure.core.exceptions import ServiceResponseError, ServiceResponseTimeoutError
from azure.core.pipeline import Pipeline
from azure.core.pipeline.policies import (
    AzureKeyCredentialPolicy,
    BearerTokenCredentialPolicy,
    ContentDecodePolicy,
    CustomHookPolicy,
    DistributedTracingPolicy,
    HeadersPolicy,
    HttpLoggingPolicy,
    NetworkTraceLoggingPolicy,
    ProxyPolicy,
    RequestIdPolicy,
    RetryMode,
    RetryPolicy,
    UserAgentPolicy,
)
from azure.core.pipeline.transport import HttpTransport, RequestsTransport
from azure.core.rest import HttpRequest
from requests.adapters import HTTPAdapter
from urllib3.exceptions import ReadTimeoutError
from urllib3.util.retry import Retry

from .exceptions import ConnectorException
from .response import ConnectorResponseHook, ConnectorResponseSnapshot
from .serialization import to_wire

ResponseT = TypeVar("ResponseT")
_REQUEST_DEADLINE: ContextVar[Optional[float]] = ContextVar(
    "connector_request_deadline", default=None
)
_REQUEST_RESPONSES: ContextVar[Optional[List[Any]]] = ContextVar(
    "connector_request_responses", default=None
)
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


class _DeadlineReader(io.RawIOBase):
    """Apply an absolute deadline before each underlying socket receive."""

    def __init__(self, response_socket: Any, deadline: float) -> None:
        """Own a socket file, but not the connection's socket itself."""
        super().__init__()
        self._raw: Any = None
        self._socket = response_socket
        self._deadline = deadline
        self._idle_timeout = response_socket.gettimeout()
        self._raw = response_socket.makefile("rb", buffering=0)

    def readable(self) -> bool:
        """Allow BufferedReader to consume this socket file."""
        return True

    def readinto(self, buffer: Any) -> Optional[int]:
        """Bound each receive, including receives inside header parsing."""
        remaining = self._deadline - time.monotonic()
        if remaining <= 0:
            raise TimeoutError("The connector response deadline expired.")
        self._socket.settimeout(
            remaining
            if self._idle_timeout is None
            else min(remaining, self._idle_timeout)
        )
        return self._raw.readinto(buffer)

    def close(self) -> None:
        """Release the socket file using normal socket makefile ownership."""
        try:
            if self._raw is not None:
                self._raw.close()
        finally:
            super().close()


class _DeadlineHTTPResponse(HTTPResponse):
    """Include status lines, headers and body framing in the read deadline."""

    def __init__(self, response_socket: Any, *args: Any, **kwargs: Any) -> None:
        """Replace only the unread socket file, preserving HTTP parsing."""
        super().__init__(response_socket, *args, **kwargs)
        deadline = _REQUEST_DEADLINE.get()
        if deadline is not None:
            original_file = self.fp
            try:
                self.fp = io.BufferedReader(_DeadlineReader(response_socket, deadline))
            finally:
                if original_file is not None:
                    original_file.close()


class _DeadlineAdapter(HTTPAdapter):
    """Use deadline-aware response parsing without changing global pools."""

    def __init__(self) -> None:
        """Leave retries to Azure Core and serialize proxy pool creation."""
        self._proxy_lock = Lock()
        super().__init__(
            max_retries=Retry(total=False, redirect=False, raise_on_status=False)
        )

    @staticmethod
    def _configure_pools(manager: Any) -> None:
        """Preserve TLS and proxy connection behavior in instance-local subclasses."""
        pool_classes = {}
        for scheme, pool_class in manager.pool_classes_by_scheme.items():
            connection_class = type(
                f"_Deadline{pool_class.ConnectionCls.__name__}",
                (pool_class.ConnectionCls,),
                {"response_class": _DeadlineHTTPResponse},
            )
            pool_classes[scheme] = type(
                f"_Deadline{pool_class.__name__}",
                (pool_class,),
                {"ConnectionCls": connection_class},
            )
        manager.pool_classes_by_scheme = pool_classes

    def init_poolmanager(
        self, connections: int, maxsize: int, block: bool = False, **kwargs: Any
    ) -> None:
        """Customize the adapter's own pools, not urllib3's shared registry."""
        super().init_poolmanager(connections, maxsize, block=block, **kwargs)
        self._configure_pools(self.poolmanager)

    def proxy_manager_for(self, proxy: str, **kwargs: Any) -> Any:
        """Apply the same parser to proxy pools without replacing proxy support."""
        with self._proxy_lock:
            if proxy in self.proxy_manager:
                return self.proxy_manager[proxy]
            manager = super().proxy_manager_for(proxy, **kwargs)
            self._configure_pools(manager)
            return manager


class _DeadlineRequestsTransport(RequestsTransport):
    """Install deadline-aware adapters only on transport-created sessions."""

    def _init_session(self, session: requests.Session) -> None:
        """Keep Azure Core environment settings and caller session ownership."""
        super()._init_session(session)
        for adapter in set(session.adapters.values()):
            adapter.close()
        adapter = _DeadlineAdapter()
        session.mount("http://", adapter)
        session.mount("https://", adapter)

    def send(self, request: Any, **kwargs: Any) -> Any:
        """Account for policy time and release abandoned retry responses."""
        responses = _REQUEST_RESPONSES.get()
        if responses:
            responses.pop().close()
        deadline = _REQUEST_DEADLINE.get()
        if deadline is not None:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise ServiceResponseTimeoutError("The connector deadline expired.")
            for option in ("connection_timeout", "read_timeout"):
                configured = kwargs.get(option)
                if configured is None or isinstance(configured, (int, float)):
                    kwargs[option] = (
                        remaining if configured is None else min(configured, remaining)
                    )
        response = super().send(request, **kwargs)
        if responses is not None:
            responses.append(response)
        return response

    def sleep(self, duration: float) -> None:
        """Release retry responses and keep retry delays inside the deadline."""
        responses = _REQUEST_RESPONSES.get()
        if responses:
            responses.pop().close()
        deadline = _REQUEST_DEADLINE.get()
        if deadline is not None:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise ServiceResponseTimeoutError("The connector deadline expired.")
            if duration >= remaining:
                super().sleep(remaining)
                raise ServiceResponseTimeoutError("The connector deadline expired.")
        super().sleep(duration)


class _JitterRetryPolicy(RetryPolicy):
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
    """Synchronous HTTP client with Azure Core policies."""

    API_HUB_SCOPES = ["https://apihub.azure.com/.default"]

    def __init__(
        self,
        credential: TokenCredential | AzureKeyCredential,
        *,
        max_retry_attempts: int = 3,
        timeout_seconds: float = 30.0,
        use_exponential_backoff: bool = True,
        initial_retry_delay_seconds: float = 0.5,
        maximum_retry_delay_seconds: float = 120.0,
        retry_jitter_factor: float = 0.1,
        retry_unsafe_http_methods: bool = False,
        transport: Optional[HttpTransport] = None,
        **kwargs: Any,
    ):
        """Initialize the HTTP client."""
        if credential is None:
            raise ValueError("credential cannot be None")

        self._credential = credential
        self._timeout_seconds = timeout_seconds
        self._retry_unsafe_http_methods = retry_unsafe_http_methods
        self._transport = transport or _DeadlineRequestsTransport(**kwargs)
        policy_options = dict(kwargs)
        per_call_policies = self._as_policy_list(
            policy_options.pop("per_call_policies", [])
        )
        per_retry_policies = self._as_policy_list(
            policy_options.pop("per_retry_policies", [])
        )
        policies = policy_options.pop("policies", None)
        if policies is None:
            policies = self._build_policies(
                credential,
                policy_options,
                per_call_policies=per_call_policies,
                per_retry_policies=per_retry_policies,
                max_retry_attempts=max_retry_attempts,
                timeout_seconds=timeout_seconds,
                use_exponential_backoff=use_exponential_backoff,
                initial_retry_delay_seconds=initial_retry_delay_seconds,
                maximum_retry_delay_seconds=maximum_retry_delay_seconds,
                retry_jitter_factor=retry_jitter_factor,
            )
        else:
            policies = self._compose_policies(
                policies,
                per_call_policies=per_call_policies,
                per_retry_policies=per_retry_policies,
            )
        self._has_retry_policy = any(
            isinstance(policy, RetryPolicy) for policy in policies
        )
        self._pipeline = Pipeline(self._transport, policies=policies)

    def _build_policies(
        self,
        credential: TokenCredential | AzureKeyCredential,
        policy_options: Dict[str, Any],
        *,
        per_call_policies: List[Any],
        per_retry_policies: List[Any],
        max_retry_attempts: int,
        timeout_seconds: float,
        use_exponential_backoff: bool,
        initial_retry_delay_seconds: float,
        maximum_retry_delay_seconds: float,
        retry_jitter_factor: float,
    ) -> List[Any]:
        """Build the standard Azure Core synchronous policy chain."""
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
    def _compose_policies(
        cls,
        policies: Any,
        *,
        per_call_policies: List[Any],
        per_retry_policies: List[Any],
    ) -> List[Any]:
        """Compose extension policies with an explicit Azure Core chain."""
        composed_policies = per_call_policies + cls._as_policy_list(policies)
        if not per_retry_policies:
            return composed_policies

        retry_policy_index = next(
            (
                index
                for index in range(len(composed_policies) - 1, -1, -1)
                if isinstance(composed_policies[index], RetryPolicy)
            ),
            None,
        )
        if retry_policy_index is None:
            raise ValueError(
                "Cannot add per_retry_policies because the explicit policy "
                "chain has no RetryPolicy."
            )

        insertion_index = retry_policy_index + 1
        return (
            composed_policies[:insertion_index]
            + per_retry_policies
            + composed_policies[insertion_index:]
        )

    @classmethod
    def _build_authentication_policy(
        cls,
        credential: TokenCredential | AzureKeyCredential,
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

        return BearerTokenCredentialPolicy(
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

    def close(self) -> None:
        """Close the HTTP transport without closing the caller credential."""
        self._pipeline.__exit__(None, None, None)

    def send(
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
        """Send a request with the selected elapsed network timeout.

        The owned default session bounds header and body receives. Custom
        transports/sessions must provide their own interruptible I/O. Credential
        and policy callbacks execute synchronously and cannot be preempted.
        """
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

        response = self._send_with_retry(
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

    def _send_with_retry(
        self,
        pipeline: Pipeline,
        method: str,
        url: str,
        headers: Dict[str, str],
        body: Optional[Any],
        *,
        client_request_id: Optional[str] = None,
        timeout: Optional[float] = None,
    ) -> ConnectorResponseSnapshot:
        """Send a request with Azure Core retry and transport timeouts."""
        normalized_method = method.upper()
        request = HttpRequest(normalized_method, url, headers=headers, content=body)
        selected_timeout = (
            timeout if timeout is not None else self._timeout_seconds
        )
        request_options: Dict[str, Any] = {"headers": headers}
        if selected_timeout > 0:
            if self._has_retry_policy:
                request_options["timeout"] = selected_timeout
            else:
                request_options["connection_timeout"] = selected_timeout
            if isinstance(self._transport, RequestsTransport):
                request_options["read_timeout"] = selected_timeout
        else:
            if self._has_retry_policy:
                request_options["timeout"] = float("inf")
            request_options["connection_timeout"] = None
            if isinstance(self._transport, RequestsTransport):
                request_options["read_timeout"] = None
        if self._has_retry_policy and normalized_method not in _SAFE_RETRY_METHODS:
            if self._retry_unsafe_http_methods:
                request_options["retry_on_methods"] = (
                    _ALL_RETRY_METHODS | {normalized_method}
                )
            else:
                request_options["retry_total"] = 0
        if client_request_id is not None:
            request_options["request_id"] = client_request_id

        enforce_total_timeout = (
            selected_timeout > 0 and isinstance(self._transport, RequestsTransport)
        )
        if enforce_total_timeout:
            request_options["stream"] = True

        return self._run_pipeline(
            pipeline,
            request,
            request_options,
            total_timeout=selected_timeout if enforce_total_timeout else None,
            url=url,
        )

    @staticmethod
    def _run_pipeline(
        pipeline: Pipeline,
        request: HttpRequest,
        request_options: Dict[str, Any],
        *,
        total_timeout: Optional[float] = None,
        url: Optional[str] = None,
    ) -> ConnectorResponseSnapshot:
        """Run the pipeline and buffer its response within an optional deadline."""
        deadline = (
            time.monotonic() + total_timeout if total_timeout is not None else None
        )
        deadline_token = _REQUEST_DEADLINE.set(deadline)
        responses: List[Any] = []
        responses_token = _REQUEST_RESPONSES.set(responses)
        http_response = None
        try:
            pipeline_response = pipeline.run(request, **request_options)
            http_response = pipeline_response.http_response
            if deadline is None:
                return ConnectorHttpClient._snapshot_response(http_response)

            assert total_timeout is not None
            response_chunks = []
            for response_chunk in http_response.iter_bytes():
                if time.monotonic() >= deadline:
                    raise ConnectorHttpClient._create_timeout_error(
                        url=url,
                        total_timeout=total_timeout,
                    )
                response_chunks.append(response_chunk)

            if time.monotonic() >= deadline:
                raise ConnectorHttpClient._create_timeout_error(
                    url=url,
                    total_timeout=total_timeout,
                )

            response_content = b"".join(response_chunks)
            return ConnectorHttpClient._snapshot_response(
                http_response,
                response_content=response_content,
                response_text=ConnectorHttpClient._decode_response_content(
                    response_content,
                    encoding=http_response.encoding,
                ),
            )
        except (ReadTimeoutError, requests.exceptions.Timeout) as ex:
            raise ServiceResponseTimeoutError(
                message="The connector response read timed out.", error=ex
            ) from ex
        except requests.exceptions.ConnectionError as ex:
            if any(isinstance(argument, ReadTimeoutError) for argument in ex.args):
                raise ServiceResponseTimeoutError(
                    message="The connector response read timed out.", error=ex
                ) from ex
            raise
        except ServiceResponseError as ex:
            if not isinstance(ex, ServiceResponseTimeoutError) and isinstance(
                ex.inner_exception, (ReadTimeoutError, requests.exceptions.ReadTimeout)
            ):
                raise ServiceResponseTimeoutError(
                    message="The connector response read timed out.", error=ex
                ) from ex
            raise
        except Exception as ex:
            if (
                deadline is not None
                and total_timeout is not None
                and time.monotonic() >= deadline
                and not isinstance(ex, ServiceResponseTimeoutError)
            ):
                raise ConnectorHttpClient._create_timeout_error(
                    url=url,
                    total_timeout=total_timeout,
                    error=ex,
                ) from ex
            raise
        finally:
            try:
                if http_response is not None and not any(
                    response is http_response for response in responses
                ):
                    http_response.close()
                for response in responses:
                    response.close()
            finally:
                _REQUEST_RESPONSES.reset(responses_token)
                _REQUEST_DEADLINE.reset(deadline_token)

    @staticmethod
    def _create_timeout_error(
        *,
        url: Optional[str],
        total_timeout: float,
        error: Optional[Exception] = None,
    ) -> ServiceResponseTimeoutError:
        """Create the standard Azure Core total-timeout exception."""
        return ServiceResponseTimeoutError(
            message=(
                f"Request to '{url}' exceeded the total timeout of "
                f"'{total_timeout}' seconds."
            ),
            error=error,
        )

    @staticmethod
    def _decode_response_content(
        response_content: bytes,
        *,
        encoding: Optional[str],
    ) -> str:
        """Decode buffered response content using Azure Core encoding metadata."""
        try:
            return response_content.decode(encoding or "utf-8", errors="replace")
        except LookupError:
            return response_content.decode("utf-8", errors="replace")

    @staticmethod
    def _snapshot_response(
        http_response: Any,
        *,
        response_content: Optional[bytes] = None,
        response_text: Optional[str] = None,
    ) -> ConnectorResponseSnapshot:
        """Buffer an Azure Core response into an immutable snapshot."""
        if response_content is None:
            response_content = http_response.body()
        if response_text is None:
            response_text = http_response.text()
        return ConnectorResponseSnapshot(
            status=http_response.status_code,
            headers=dict(http_response.headers),
            text=response_text,
            content=response_content,
        )

    def get(self, request_uri: str) -> Any:
        """Send a GET request."""
        response = self.send("GET", request_uri)
        if not 200 <= response.status < 300:
            raise ConnectorException(
                "GET",
                request_uri,
                response.status,
                response.text,
                response=response,
            )

        return json.loads(response.text) if response.text else None

    def post(self, request_uri: str, body: Any) -> Any:
        """Send a POST request with a JSON body."""
        response = self.send("POST", request_uri, body)
        if not 200 <= response.status < 300:
            raise ConnectorException(
                "POST",
                request_uri,
                response.status,
                response.text,
                response=response,
            )

        return json.loads(response.text) if response.text else None
