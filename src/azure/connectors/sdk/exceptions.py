# Copyright (c) Microsoft Corporation. All rights reserved.

"""Exception types for connector operations."""

import json
from typing import Optional

from azure.core.exceptions import HttpResponseError


class ConnectorException(HttpResponseError):
    """
    Exception raised when connector operations fail.

    Attributes:
        method: The HTTP method used for the request.
        path: The connector request path.
        operation: The combined HTTP method and request path.
        status_code: The HTTP response status code.
        response_body: The unmodified response body.
        error_code: The structured connector error code, when available.
        error_message: The structured connector error message, when available.
    """

    MAX_RESPONSE_BODY_LENGTH = 2000

    def __init__(
        self,
        method: str,
        path: str,
        status_code: int,
        response_body: str,
    ):
        """
        Initialize a ConnectorException.

        Args:
            method: The HTTP method that failed (e.g., "GET", "POST").
            path: The API path that was called (e.g., "/v2/Mail").
            status_code: The HTTP status code.
            response_body: The response body from the failed request.
        """
        self.method = method
        self.path = path
        self.operation = f"{method} {path}"
        self.status_code = status_code
        self.response_body = response_body
        self.error_code, self.error_message = self._parse_service_error(
            response_body
        )
        truncated_body = self._truncate_body(response_body)
        message = f"{self.operation} failed with status {status_code}: "
        message += truncated_body
        super().__init__(message=message)
        self.status_code = status_code

    @staticmethod
    def _parse_service_error(
        response_body: str,
    ) -> tuple[Optional[str], Optional[str]]:
        """Parse common connector error fields from a JSON response body."""
        try:
            payload = json.loads(response_body)
        except (json.JSONDecodeError, TypeError):
            return None, None

        if not isinstance(payload, dict):
            return None, None

        error = payload.get("error", payload)
        if not isinstance(error, dict):
            return None, None

        error_code = error.get("code")
        error_message = error.get("message")
        return (
            error_code if isinstance(error_code, str) else None,
            error_message if isinstance(error_message, str) else None,
        )

    @classmethod
    def _truncate_body(cls, body: str) -> str:
        """Truncate response body if it exceeds maximum length."""
        if not body or len(body) <= cls.MAX_RESPONSE_BODY_LENGTH:
            return body
        return body[:cls.MAX_RESPONSE_BODY_LENGTH] + "...[truncated]"
