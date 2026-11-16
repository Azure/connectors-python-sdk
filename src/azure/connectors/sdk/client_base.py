# Copyright (c) Microsoft Corporation. All rights reserved.

"""Abstract base class for generated connector clients."""

from abc import ABC, abstractmethod
from typing import Any, AsyncIterator, Optional

from azure.core.credentials import AzureKeyCredential
from azure.core.credentials_async import AsyncTokenCredential
from azure.core.pipeline.transport import AsyncHttpTransport

from .http_client import ConnectorHttpClient
from .response import ConnectorPage, ConnectorResponseSnapshot


class ConnectorClientBase(ABC):
    """Abstract base class for generated connector clients."""

    def __init__(
        self,
        credential: AsyncTokenCredential | AzureKeyCredential,
        *,
        max_retry_attempts: int = 3,
        timeout: float = 30.0,
        use_exponential_backoff: bool = True,
        initial_retry_delay_seconds: float = 0.5,
        maximum_retry_delay_seconds: float = 120.0,
        retry_jitter_factor: float = 0.1,
        retry_unsafe_http_methods: bool = False,
        transport: Optional[AsyncHttpTransport] = None,
        **kwargs: Any,
    ):
        """
        Initialize a ConnectorClientBase.

        Args:
            credential: Caller-owned Azure Core credential.
            timeout: Total network timeout for each request, including
                retries, response loading, and body reads. Nonpositive values
                disable SDK and transport deadlines.
            transport: Optional Azure Core async HTTP transport closed by the
                client through its asynchronous lifecycle.
        """
        if credential is None:
            raise ValueError("credential cannot be None")

        self._http_client = ConnectorHttpClient(
            credential,
            max_retry_attempts=max_retry_attempts,
            timeout_seconds=timeout,
            use_exponential_backoff=use_exponential_backoff,
            initial_retry_delay_seconds=initial_retry_delay_seconds,
            maximum_retry_delay_seconds=maximum_retry_delay_seconds,
            retry_jitter_factor=retry_jitter_factor,
            retry_unsafe_http_methods=retry_unsafe_http_methods,
            transport=transport,
            **kwargs,
        )

    @property
    @abstractmethod
    def connector_name(self) -> str:
        """Get the connector name."""
        pass

    @property
    def http_client(self) -> ConnectorHttpClient:
        """Get the HTTP client for making connector requests."""
        return self._http_client

    def _wrap_page(
        self,
        items: AsyncIterator[Any],
        page_model: Any,
        raw_response: ConnectorResponseSnapshot,
        continuation_token: Optional[str] = None,
    ) -> ConnectorPage[Any]:
        """Retain parsed and raw page envelopes alongside yielded items."""
        return ConnectorPage(
            items,
            page_model=page_model,
            raw_response=raw_response,
            continuation_token=continuation_token,
        )

    async def close(self) -> None:
        """Close the HTTP client and release resources."""
        await self._http_client.close()

    async def __aenter__(self):
        """Enter async context manager."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Exit async context manager."""
        await self.close()
