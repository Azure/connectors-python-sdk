# Copyright (c) Microsoft Corporation. All rights reserved.

"""Unit tests for the connector client base."""

from unittest.mock import AsyncMock, patch

import pytest
from azure.core.credentials import AzureKeyCredential

from azure.connectors.sdk.client_base import ConnectorClientBase


class TestClient(ConnectorClientBase):
    """Concrete connector client used by base-class tests."""

    @property
    def connector_name(self) -> str:
        """Return the test connector name."""
        return "test"


class TestConnectorClientBase:
    """Tests for ConnectorClientBase."""

    def test_cannot_instantiate_abstract_class(self) -> None:
        """Test that the abstract base class cannot be instantiated."""
        with pytest.raises(TypeError):
            ConnectorClientBase(AzureKeyCredential("test-key"))

    def test_init_with_credential(self, mock_credential) -> None:
        """Test initialization with an asynchronous Azure Core credential."""
        client = TestClient(mock_credential)

        assert client._http_client._credential is mock_credential

    def test_init_with_key_credential(self) -> None:
        """Test initialization with an Azure key credential."""
        credential = AzureKeyCredential("test-key")
        client = TestClient(credential)

        assert client._http_client._credential is credential

    def test_init_with_none_credential_raises_error(self) -> None:
        """Test that a missing credential is rejected."""
        with pytest.raises(ValueError, match="credential cannot be None"):
            TestClient(None)

    def test_init_forwards_pipeline_settings(self, mock_credential) -> None:
        """Test that direct settings are forwarded to the HTTP client."""
        with patch(
            "azure.connectors.sdk.client_base.ConnectorHttpClient"
        ) as mock_http_client:
            TestClient(
                mock_credential,
                max_retry_attempts=5,
                timeout_seconds=60.0,
                retry_unsafe_http_methods=True,
                retry_status=2,
            )

        call = mock_http_client.call_args
        assert call.args == (mock_credential,)
        assert call.kwargs["max_retry_attempts"] == 5
        assert call.kwargs["timeout_seconds"] == 60.0
        assert call.kwargs["retry_unsafe_http_methods"] is True
        assert call.kwargs["retry_status"] == 2

    def test_connector_name_property_is_abstract(self, mock_credential) -> None:
        """Test that subclasses must implement the connector name."""

        class IncompleteClient(ConnectorClientBase):
            pass

        with pytest.raises(TypeError):
            IncompleteClient(mock_credential)

    def test_http_client_property(self, mock_credential) -> None:
        """Test that the HTTP client property exposes the owned client."""
        client = TestClient(mock_credential)

        assert client.http_client is client._http_client

    @pytest.mark.asyncio
    async def test_close(self, mock_credential) -> None:
        """Test that close releases the HTTP client."""
        client = TestClient(mock_credential)

        with patch.object(
            client._http_client,
            "close",
            new_callable=AsyncMock,
        ) as mock_close:
            await client.close()

        mock_close.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_context_manager(self, mock_credential) -> None:
        """Test asynchronous context manager cleanup."""
        client = TestClient(mock_credential)

        with patch.object(
            client,
            "close",
            new_callable=AsyncMock,
        ) as mock_close:
            async with client as entered_client:
                assert entered_client is client

        mock_close.assert_awaited_once()
