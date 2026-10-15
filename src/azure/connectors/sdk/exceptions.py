# Copyright (c) Microsoft Corporation. All rights reserved.

"""Exception types for connector operations."""

from http import HTTPStatus
from typing import Optional

from azure.core.exceptions import HttpResponseError
from azure.core.pipeline.transport import HttpRequest, HttpResponse

from .response import ConnectorResponseSnapshot


class _ConnectorHttpResponse(HttpResponse):
    """Adapt an immutable connector response to the Azure Core response API."""

    def __init__(
        self,
        method: str,
        path: str,
        response: ConnectorResponseSnapshot,
    ) -> None:
        """Initialize the response adapter."""
        super().__init__(HttpRequest(method, path), internal_response=None)
        self.status_code = response.status
        self.headers = dict(response.headers)
        try:
            self.reason = HTTPStatus(response.status).phrase
        except ValueError:
            self.reason = None
        self.content_type = next(
            (
                value
                for name, value in response.headers.items()
                if name.lower() == "content-type"
            ),
            None,
        )
        self._content = response.content

    def body(self) -> bytes:
        """Return the buffered response body."""
        return self._content


class ConnectorException(HttpResponseError):
    """Exception raised when connector operations fail."""

    MAX_RESPONSE_BODY_LENGTH = 2000

    def __init__(
        self,
        method: str,
        path: str,
        status_code: int,
        response_body: str,
        *,
        response: Optional[ConnectorResponseSnapshot] = None,
    ) -> None:
        """
        Initialize a ConnectorException.

        Args:
            method: The HTTP method that failed (e.g., "GET", "POST").
            path: The API path that was called (e.g., "/v2/Mail").
            status_code: The HTTP status code.
            response_body: The response body from the failed request.
            response: The completed connector response, when available.
        """
        self.method = method
        self.path = path
        self.operation = f"{method} {path}"
        self.status_code = status_code
        self.response_body = response_body
        truncated_body = self._truncate_body(response_body)
        message = f"{self.operation} failed with status {status_code}: "
        message += truncated_body
        if response is None:
            response = ConnectorResponseSnapshot(
                status=status_code,
                headers={},
                text=response_body,
                content=response_body.encode("utf-8"),
            )
        super().__init__(
            message=message,
            response=_ConnectorHttpResponse(method, path, response),
        )
        self.message = message
        self.args = (message,)
        self.status_code = status_code

    @classmethod
    def _truncate_body(cls, body: str) -> str:
        """Truncate response body if it exceeds maximum length."""
        if not body or len(body) <= cls.MAX_RESPONSE_BODY_LENGTH:
            return body
        return body[:cls.MAX_RESPONSE_BODY_LENGTH] + "...[truncated]"
