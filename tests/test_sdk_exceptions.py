"""Unit tests for SDK exceptions module."""

import pytest

from azure.connectors.sdk.exceptions import ConnectorException


class TestConnectorException:
    """Tests for ConnectorException."""

    def test_init_with_all_parameters(self):
        """Test initialization with all parameters."""
        ex = ConnectorException(
            operation="GET /api/data",
            status_code=404,
            response_body='{"error": "Not Found"}'
        )

        assert ex.operation == "GET /api/data"
        assert ex.status_code == 404
        assert ex.response_body == '{"error": "Not Found"}'

    def test_exception_message_format(self):
        """Test that exception message includes operation, status, and body."""
        ex = ConnectorException(
            operation="POST /api/items",
            status_code=500,
            response_body='{"error": "Internal Server Error"}'
        )

        message = str(ex)
        assert "POST /api/items" in message
        assert "500" in message
        assert '{"error": "Internal Server Error"}' in message

    def test_exception_with_empty_body(self):
        """Test exception with empty response body."""
        ex = ConnectorException(
            operation="DELETE /api/resource",
            status_code=204,
            response_body=""
        )

        assert ex.response_body == ""
        assert "204" in str(ex)

    def test_exception_inherits_from_exception(self):
        """Test that ConnectorException inherits from Exception."""
        ex = ConnectorException("GET /", 500, "error")

        assert isinstance(ex, Exception)

    def test_exception_can_be_raised_and_caught(self):
        """Test that exception can be raised and caught."""
        with pytest.raises(ConnectorException) as exc_info:
            raise ConnectorException("GET /test", 400, "Bad Request")

        assert exc_info.value.status_code == 400

    def test_truncate_body_short_body(self):
        """Test that short bodies are not truncated."""
        short_body = "error" * 100  # 500 chars
        ex = ConnectorException("GET /", 500, short_body)

        assert ex.response_body == short_body
        assert "[truncated]" not in str(ex)

    def test_truncate_body_long_body(self):
        """Test that long bodies are truncated."""
        long_body = "x" * 5000  # Much longer than MAX_RESPONSE_BODY_LENGTH
        ex = ConnectorException("GET /", 500, long_body)

        message = str(ex)
        assert "[truncated]" in message
        assert len(message) < len(long_body)

    def test_truncate_body_exactly_max_length(self):
        """Test body exactly at max length is not truncated."""
        exact_body = "x" * ConnectorException.MAX_RESPONSE_BODY_LENGTH
        ex = ConnectorException("GET /", 500, exact_body)

        assert "[truncated]" not in str(ex)

    def test_truncate_body_one_over_max_length(self):
        """Test body one char over max length is truncated."""
        over_body = "x" * (ConnectorException.MAX_RESPONSE_BODY_LENGTH + 1)
        ex = ConnectorException("GET /", 500, over_body)

        assert "[truncated]" in str(ex)

    def test_exception_with_various_status_codes(self):
        """Test exception with different HTTP status codes."""
        for status_code in [400, 401, 403, 404, 429, 500, 502, 503]:
            ex = ConnectorException(f"GET /test/{status_code}", status_code, "error")

            assert ex.status_code == status_code
            assert str(status_code) in str(ex)

    def test_exception_message_includes_operation_details(self):
        """Test that detailed operation info is in the message."""
        ex = ConnectorException(
            operation="POST /v2/Mail with headers={'Content-Type': 'application/json'}",
            status_code=403,
            response_body="Forbidden"
        )

        message = str(ex)
        assert "POST /v2/Mail" in message
        assert "403" in message
        assert "Forbidden" in message

    def test_exception_attributes_accessible(self):
        """Test that all exception attributes are accessible."""
        ex = ConnectorException("PATCH /api", 422, "Validation Error")

        assert hasattr(ex, 'operation')
        assert hasattr(ex, 'status_code')
        assert hasattr(ex, 'response_body')
        assert ex.operation == "PATCH /api"
        assert ex.status_code == 422
        assert ex.response_body == "Validation Error"

    def test_exception_with_json_response_body(self):
        """Test exception with JSON response body."""
        json_body = '{"error": {"code": "InvalidRequest", "message": "The request is invalid"}}'
        ex = ConnectorException("PUT /resource", 400, json_body)

        assert json_body in str(ex)
        assert ex.response_body == json_body

    def test_max_response_body_length_constant(self):
        """Test that MAX_RESPONSE_BODY_LENGTH constant is accessible."""
        assert hasattr(ConnectorException, 'MAX_RESPONSE_BODY_LENGTH')
        assert isinstance(ConnectorException.MAX_RESPONSE_BODY_LENGTH, int)
        assert ConnectorException.MAX_RESPONSE_BODY_LENGTH == 2000
