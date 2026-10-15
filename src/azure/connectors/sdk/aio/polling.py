# Copyright (c) Microsoft Corporation. All rights reserved.

"""Asynchronous Azure Core polling for connector operations."""

import asyncio
from typing import Any, Callable, Generic, Mapping, Optional, TypeVar

from azure.core.polling import AsyncPollingMethod

from .._polling import (
    get_location,
    get_polling_status,
    get_retry_after_seconds,
    resolve_polling_url,
)
from ..exceptions import ConnectorException
from ..response import ConnectorResponseHook, ConnectorResponseSnapshot

PollingResultT = TypeVar("PollingResultT")


class ConnectorPollingMethod(
    AsyncPollingMethod[PollingResultT], Generic[PollingResultT]
):
    """Poll a connector operation until it returns a terminal HTTP response."""

    def __init__(
        self,
        http_client: Any,
        polling_header_name: str,
        *,
        timeout: Optional[float] = None,
        headers: Optional[Mapping[str, str]] = None,
        client_request_id: Optional[str] = None,
        response_hook: Optional[ConnectorResponseHook] = None,
    ) -> None:
        """Initialize connector polling request options."""
        if polling_header_name.casefold() != "location":
            raise ValueError("Only the 'Location' polling header is supported.")

        self._http_client = http_client
        self._timeout = timeout
        self._headers = headers
        self._client_request_id = client_request_id
        self._response_hook = response_hook
        self._response: Optional[ConnectorResponseSnapshot] = None
        self._polling_url: Optional[str] = None
        self._connection_runtime_url: Optional[str] = None
        self._deserialization_callback: Optional[
            Callable[[ConnectorResponseSnapshot], PollingResultT]
        ] = None

    def initialize(
        self,
        client: Any,
        initial_response: ConnectorResponseSnapshot,
        deserialization_callback: Callable[
            [ConnectorResponseSnapshot], PollingResultT
        ],
    ) -> None:
        """Initialize polling from the operation's first response."""
        self._response = initial_response
        self._connection_runtime_url = client._connection_runtime_url
        self._deserialization_callback = deserialization_callback
        if initial_response.status == 202:
            self._update_polling_url(require_url=True)

    async def run(self) -> None:
        """Poll until the connector returns a terminal response."""
        while not self.finished():
            if self._response is None or self._polling_url is None:
                raise RuntimeError("Connector polling was not initialized.")
            await asyncio.sleep(get_retry_after_seconds(self._response))
            request_url = self._polling_url
            self._response = await self._http_client.send(
                "GET",
                request_url,
                body=None,
                timeout=self._timeout,
                headers=self._headers,
                client_request_id=self._client_request_id,
                response_hook=self._response_hook,
            )
            if self._response.status == 202:
                self._update_polling_url(require_url=False)
            elif not 200 <= self._response.status < 300:
                raise ConnectorException(
                    "GET",
                    request_url,
                    self._response.status,
                    self._response.text,
                    response=self._response,
                )

    def status(self) -> str:
        """Return the current Azure Core polling status."""
        return get_polling_status(self._response)

    def finished(self) -> bool:
        """Return whether the connector has produced a terminal response."""
        return self._response is not None and self._response.status != 202

    def resource(self) -> PollingResultT:
        """Deserialize the terminal connector response."""
        if self._response is None or self._deserialization_callback is None:
            raise RuntimeError("Connector polling was not initialized.")
        if not self.finished():
            raise RuntimeError("Connector polling has not completed.")
        return self._deserialization_callback(self._response)

    def _update_polling_url(self, *, require_url: bool) -> None:
        """Update and validate the polling URL from the current response."""
        if self._response is None or self._connection_runtime_url is None:
            raise RuntimeError("Connector polling was not initialized.")
        location = get_location(self._response)
        if location is None:
            if require_url:
                raise ValueError(
                    "An HTTP 202 response must include a 'Location' polling URL."
                )
            return
        self._polling_url = resolve_polling_url(
            location,
            self._connection_runtime_url,
            self._polling_url,
        )


__all__ = ["ConnectorPollingMethod"]
