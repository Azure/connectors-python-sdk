# Copyright (c) Microsoft Corporation. All rights reserved.

"""Exception types for connector operations."""


class ConnectorException(Exception):
    """Exception raised when connector operations fail."""

    MAX_RESPONSE_BODY_LENGTH = 2000

    def __init__(self, operation: str, status_code: int, response_body: str):
        """
        Initialize a ConnectorException.

        Args:
            operation: The operation that failed (e.g., "GET /v2/Mail").
            status_code: The HTTP status code.
            response_body: The response body from the failed request.
        """
        self.operation = operation
        self.status_code = status_code
        self.response_body = response_body
        truncated_body = self._truncate_body(response_body)
        super().__init__(f"{operation} failed with status {status_code}: {truncated_body}")

    @classmethod
    def _truncate_body(cls, body: str) -> str:
        """Truncate response body if it exceeds maximum length."""
        if not body or len(body) <= cls.MAX_RESPONSE_BODY_LENGTH:
            return body
        return body[:cls.MAX_RESPONSE_BODY_LENGTH] + "...[truncated]"
