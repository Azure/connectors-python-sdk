"""Unit tests for SDK authentication module."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from azure.core.credentials import AccessToken

from azure.connectors.sdk.authentication import (
    TokenProvider,
    AzureIdentityTokenProvider,
    ManagedIdentityTokenProvider,
    ConnectionStringTokenProvider,
)


class TestAzureIdentityTokenProvider:
    """Tests for AzureIdentityTokenProvider."""

    @pytest.mark.asyncio
    async def test_init_with_valid_credential(self):
        """Test initialization with valid credential."""
        mock_credential = MagicMock()
        provider = AzureIdentityTokenProvider(mock_credential)
        
        assert provider._credential is mock_credential

    def test_init_with_none_raises_error(self):
        """Test that None credential raises ValueError."""
        with pytest.raises(ValueError, match="credential cannot be None"):
            AzureIdentityTokenProvider(None)

    @pytest.mark.asyncio
    async def test_get_access_token_success(self):
        """Test successful token acquisition."""
        mock_credential = MagicMock()
        mock_token = AccessToken(token="test_token_123", expires_on=9999999999)
        mock_credential.get_token = AsyncMock(return_value=mock_token)
        
        provider = AzureIdentityTokenProvider(mock_credential)
        token = await provider.get_access_token_async(["https://api.example.com/.default"])
        
        assert token == "test_token_123"
        mock_credential.get_token.assert_called_once_with("https://api.example.com/.default")

    @pytest.mark.asyncio
    async def test_get_access_token_with_multiple_scopes(self):
        """Test token acquisition with multiple scopes."""
        mock_credential = MagicMock()
        mock_token = AccessToken(token="multi_scope_token", expires_on=9999999999)
        mock_credential.get_token = AsyncMock(return_value=mock_token)
        
        provider = AzureIdentityTokenProvider(mock_credential)
        scopes = ["scope1", "scope2", "scope3"]
        token = await provider.get_access_token_async(scopes)
        
        assert token == "multi_scope_token"
        mock_credential.get_token.assert_called_once_with("scope1", "scope2", "scope3")

    @pytest.mark.asyncio
    async def test_get_access_token_empty_scopes_raises_error(self):
        """Test that empty scopes list raises ValueError."""
        mock_credential = MagicMock()
        provider = AzureIdentityTokenProvider(mock_credential)
        
        with pytest.raises(ValueError, match="At least one scope must be provided"):
            await provider.get_access_token_async([])

    @pytest.mark.asyncio
    async def test_close_with_async_close(self):
        """Test closing credential with async close method."""
        mock_credential = MagicMock()
        mock_credential.close = AsyncMock()
        
        provider = AzureIdentityTokenProvider(mock_credential)
        await provider.close()
        
        mock_credential.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_close_with_sync_close(self):
        """Test closing credential with sync close method."""
        mock_credential = MagicMock()
        mock_credential.close = MagicMock(return_value=None)
        
        provider = AzureIdentityTokenProvider(mock_credential)
        await provider.close()
        
        mock_credential.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_close_without_close_method(self):
        """Test closing credential without close method."""
        mock_credential = MagicMock(spec=[])  # No close method
        
        provider = AzureIdentityTokenProvider(mock_credential)
        await provider.close()  # Should not raise


class TestManagedIdentityTokenProvider:
    """Tests for ManagedIdentityTokenProvider."""

    @pytest.mark.asyncio
    async def test_init_with_client_id(self):
        """Test initialization with client ID."""
        with patch('azure.connectors.sdk.authentication.ManagedIdentityCredential') as mock_cred:
            provider = ManagedIdentityTokenProvider(client_id="test-client-id")
            
            mock_cred.assert_called_once_with(client_id="test-client-id")

    @pytest.mark.asyncio
    async def test_init_without_client_id(self):
        """Test initialization without client ID uses DefaultAzureCredential."""
        with patch('azure.connectors.sdk.authentication.DefaultAzureCredential') as mock_cred:
            provider = ManagedIdentityTokenProvider()
            
            mock_cred.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_access_token_success(self):
        """Test successful token acquisition."""
        with patch('azure.connectors.sdk.authentication.DefaultAzureCredential') as mock_cred_class:
            mock_credential = MagicMock()
            mock_token = AccessToken(token="managed_identity_token", expires_on=9999999999)
            mock_credential.get_token = AsyncMock(return_value=mock_token)
            mock_cred_class.return_value = mock_credential
            
            provider = ManagedIdentityTokenProvider()
            token = await provider.get_access_token_async(["https://api.example.com/.default"])
            
            assert token == "managed_identity_token"

    @pytest.mark.asyncio
    async def test_get_access_token_empty_scopes_raises_error(self):
        """Test that empty scopes list raises ValueError."""
        with patch('azure.connectors.sdk.authentication.DefaultAzureCredential'):
            provider = ManagedIdentityTokenProvider()
            
            with pytest.raises(ValueError, match="At least one scope must be provided"):
                await provider.get_access_token_async([])

    @pytest.mark.asyncio
    async def test_close(self):
        """Test closing managed identity credential."""
        with patch('azure.connectors.sdk.authentication.DefaultAzureCredential') as mock_cred_class:
            mock_credential = MagicMock()
            mock_credential.close = AsyncMock()
            mock_cred_class.return_value = mock_credential
            
            provider = ManagedIdentityTokenProvider()
            await provider.close()
            
            mock_credential.close.assert_called_once()


class TestConnectionStringTokenProvider:
    """Tests for ConnectionStringTokenProvider."""

    def test_init_with_valid_api_key(self):
        """Test initialization with valid API key."""
        provider = ConnectionStringTokenProvider("my-api-key-123")
        
        assert provider._api_key == "my-api-key-123"

    def test_init_with_empty_string_raises_error(self):
        """Test that empty API key raises ValueError."""
        with pytest.raises(ValueError, match="API key cannot be null or empty"):
            ConnectionStringTokenProvider("")

    def test_init_with_none_raises_error(self):
        """Test that None API key raises ValueError."""
        with pytest.raises(ValueError, match="API key cannot be null or empty"):
            ConnectionStringTokenProvider(None)

    @pytest.mark.asyncio
    async def test_get_access_token_returns_api_key(self):
        """Test that get_access_token returns the API key directly."""
        provider = ConnectionStringTokenProvider("my-secret-key")
        token = await provider.get_access_token_async(["any", "scopes"])
        
        assert token == "my-secret-key"

    @pytest.mark.asyncio
    async def test_get_access_token_ignores_scopes(self):
        """Test that scopes are ignored for connection string provider."""
        provider = ConnectionStringTokenProvider("api-key-456")
        
        token1 = await provider.get_access_token_async(["scope1"])
        token2 = await provider.get_access_token_async(["scope2", "scope3"])
        token3 = await provider.get_access_token_async([])
        
        assert token1 == "api-key-456"
        assert token2 == "api-key-456"
        assert token3 == "api-key-456"


class TestTokenProviderInterface:
    """Tests for TokenProvider abstract interface."""

    def test_cannot_instantiate_abstract_class(self):
        """Test that TokenProvider cannot be instantiated directly."""
        with pytest.raises(TypeError):
            TokenProvider()

    def test_subclass_must_implement_abstract_method(self):
        """Test that subclass must implement get_access_token_async."""
        class IncompleteProvider(TokenProvider):
            pass
        
        with pytest.raises(TypeError):
            IncompleteProvider()

    @pytest.mark.asyncio
    async def test_subclass_with_implementation_works(self):
        """Test that properly implemented subclass works."""
        class CustomProvider(TokenProvider):
            async def get_access_token_async(self, scopes):
                return "custom_token"
        
        provider = CustomProvider()
        token = await provider.get_access_token_async(["scope"])
        
        assert token == "custom_token"
