"""Unit tests for SDK client_base module."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from azure.connectors.sdk.client_base import ConnectorClientBase
from azure.connectors.sdk.authentication import TokenProvider, AzureIdentityTokenProvider
from azure.connectors.sdk.options import ConnectorClientOptions


class TestConnectorClientBase:
    """Tests for ConnectorClientBase."""

    def test_cannot_instantiate_abstract_class(self):
        """Test that ConnectorClientBase cannot be instantiated directly."""
        mock_token_provider = MagicMock(spec=TokenProvider)
        
        with pytest.raises(TypeError):
            ConnectorClientBase(mock_token_provider)

    def test_subclass_with_token_provider(self, mock_token_provider):
        """Test subclass initialization with TokenProvider."""
        class TestClient(ConnectorClientBase):
            @property
            def connector_name(self) -> str:
                return "test"
        
        client = TestClient(mock_token_provider)
        
        assert client._options is not None
        assert client._http_client is not None

    def test_subclass_with_azure_identity_credential(self):
        """Test subclass initialization with Azure Identity credential."""
        class TestClient(ConnectorClientBase):
            @property
            def connector_name(self) -> str:
                return "test"
        
        mock_credential = MagicMock()
        client = TestClient(mock_credential)
        
        assert client._http_client is not None

    def test_init_with_none_token_provider_raises_error(self):
        """Test that None token provider raises ValueError."""
        class TestClient(ConnectorClientBase):
            @property
            def connector_name(self) -> str:
                return "test"
        
        with pytest.raises(ValueError, match="token_provider cannot be None"):
            TestClient(None)

    def test_init_with_custom_options(self, mock_token_provider):
        """Test initialization with custom options."""
        class TestClient(ConnectorClientBase):
            @property
            def connector_name(self) -> str:
                return "test"
        
        options = ConnectorClientOptions(timeout_seconds=60.0)
        client = TestClient(mock_token_provider, options)
        
        assert client._options is options

    def test_init_without_options_creates_default(self, mock_token_provider):
        """Test initialization without options creates default options."""
        class TestClient(ConnectorClientBase):
            @property
            def connector_name(self) -> str:
                return "test"
        
        client = TestClient(mock_token_provider)
        
        assert isinstance(client._options, ConnectorClientOptions)

    def test_connector_name_property_is_abstract(self, mock_token_provider):
        """Test that connector_name property must be implemented."""
        class IncompleteClient(ConnectorClientBase):
            pass
        
        with pytest.raises(TypeError):
            IncompleteClient(mock_token_provider)

    def test_http_client_property(self, mock_token_provider):
        """Test that http_client property is accessible."""
        class TestClient(ConnectorClientBase):
            @property
            def connector_name(self) -> str:
                return "test"
        
        client = TestClient(mock_token_provider)
        http_client = client.http_client
        
        assert http_client is not None
        assert http_client is client._http_client

    @pytest.mark.asyncio
    async def test_close(self, mock_token_provider):
        """Test close method."""
        class TestClient(ConnectorClientBase):
            @property
            def connector_name(self) -> str:
                return "test"
        
        client = TestClient(mock_token_provider)
        
        with patch.object(client._http_client, 'close', new_callable=AsyncMock) as mock_close:
            await client.close()
            mock_close.assert_called_once()

    @pytest.mark.asyncio
    async def test_context_manager_enter(self, mock_token_provider):
        """Test async context manager enter."""
        class TestClient(ConnectorClientBase):
            @property
            def connector_name(self) -> str:
                return "test"
        
        client = TestClient(mock_token_provider)
        result = await client.__aenter__()
        
        assert result is client

    @pytest.mark.asyncio
    async def test_context_manager_exit(self, mock_token_provider):
        """Test async context manager exit."""
        class TestClient(ConnectorClientBase):
            @property
            def connector_name(self) -> str:
                return "test"
        
        client = TestClient(mock_token_provider)
        
        with patch.object(client, 'close', new_callable=AsyncMock) as mock_close:
            await client.__aexit__(None, None, None)
            mock_close.assert_called_once()

    @pytest.mark.asyncio
    async def test_context_manager_full_usage(self, mock_token_provider):
        """Test full async context manager usage."""
        class TestClient(ConnectorClientBase):
            @property
            def connector_name(self) -> str:
                return "test"
        
        client = TestClient(mock_token_provider)
        
        with patch.object(client._http_client, 'close', new_callable=AsyncMock) as mock_close:
            async with client as ctx_client:
                assert ctx_client is client
            
            mock_close.assert_called_once()

    def test_wraps_non_token_provider_credential(self):
        """Test that non-TokenProvider credentials are wrapped."""
        class TestClient(ConnectorClientBase):
            @property
            def connector_name(self) -> str:
                return "test"
        
        mock_credential = MagicMock()
        
        with patch('azure.connectors.sdk.client_base.AzureIdentityTokenProvider') as mock_wrapper:
            client = TestClient(mock_credential)
            mock_wrapper.assert_called_once_with(mock_credential)

    def test_does_not_wrap_token_provider(self, mock_token_provider):
        """Test that TokenProvider instances are not wrapped."""
        class TestClient(ConnectorClientBase):
            @property
            def connector_name(self) -> str:
                return "test"
        
        with patch('azure.connectors.sdk.client_base.AzureIdentityTokenProvider') as mock_wrapper:
            client = TestClient(mock_token_provider)
            mock_wrapper.assert_not_called()
