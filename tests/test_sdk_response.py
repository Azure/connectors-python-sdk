"""Unit tests for connector response contracts."""

from dataclasses import FrozenInstanceError

import pytest

from azure.connectors.sdk.response import ConnectorResponseSnapshot


def test_response_snapshot_is_immutable() -> None:
    """Test response fields and headers cannot be mutated."""
    headers = {"x-response-header": "response-value"}
    response = ConnectorResponseSnapshot(
        status=200,
        headers=headers,
        text="response",
        content=b"response",
    )

    headers["x-response-header"] = "changed"

    assert response.headers["x-response-header"] == "response-value"
    with pytest.raises(FrozenInstanceError):
        response.status = 201
    with pytest.raises(TypeError):
        response.headers["x-new-header"] = "new-value"
