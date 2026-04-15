# Copyright (c) Microsoft Corporation. All rights reserved.

"""Authentication token providers for connector clients."""

from abc import ABC, abstractmethod
from typing import List, Optional, Union, Any
from azure.identity.aio import DefaultAzureCredential, ManagedIdentityCredential
from azure.core.credentials import AccessToken


class TokenProvider(ABC):
    """Interface for providing authentication tokens."""

    @abstractmethod
    async def get_access_token_async(self, scopes: List[str]) -> str:
        """
        Get an access token for the specified scopes.

        Args:
            scopes: The authentication scopes.

        Returns:
            The access token.
        """
        pass


class AzureIdentityTokenProvider(TokenProvider):
    """Token provider that wraps Azure Identity async credentials."""

    def __init__(self, credential: Any):
        """
        Initialize an AzureIdentityTokenProvider.

        Args:
            credential: An Azure Identity async credential (e.g., DefaultAzureCredential from azure.identity.aio).
                       Must have an async get_token() method.
        """
        if credential is None:
            raise ValueError("credential cannot be None")
        self._credential = credential

    async def get_access_token_async(self, scopes: List[str]) -> str:
        """Get an access token using the Azure Identity credential."""
        if not scopes:
            raise ValueError("At least one scope must be provided.")
        
        # NOTE(victoriahall): Azure Identity async credentials use get_token() which is async.
        token: AccessToken = await self._credential.get_token(*scopes)
        return token.token
    
    async def close(self):
        """Close the underlying credential."""
        if hasattr(self._credential, 'close'):
            result = self._credential.close()
            # NOTE(victoriahall): Only await if the close() method returns a coroutine.
            if hasattr(result, '__await__'):
                await result


class ManagedIdentityTokenProvider(TokenProvider):
    """Token provider using Azure Managed Identity."""

    def __init__(self, client_id: Optional[str] = None):
        """
        Initialize a new ManagedIdentityTokenProvider.

        Args:
            client_id: Optional client ID for user-assigned managed identity.
        """
        if client_id:
            self._credential = ManagedIdentityCredential(client_id=client_id)
        else:
            self._credential = DefaultAzureCredential()

    async def get_access_token_async(self, scopes: List[str]) -> str:
        """Get an access token using managed identity."""
        if not scopes:
            raise ValueError("At least one scope must be provided.")
        
        # NOTE(victoriahall): azure-identity async credentials use get_token() which is async.
        # Must await the call to get the AccessToken.
        token: AccessToken = await self._credential.get_token(*scopes)
        return token.token
    
    async def close(self):
        """Close the underlying credential."""
        if hasattr(self._credential, 'close'):
            result = self._credential.close()
            # NOTE(victoriahall): Only await if the close() method returns a coroutine.
            if hasattr(result, '__await__'):
                await result


class ConnectionStringTokenProvider(TokenProvider):
    """Token provider using a pre-configured connection string or API key."""

    def __init__(self, api_key: str):
        """
        Initialize a new ConnectionStringTokenProvider.

        Args:
            api_key: The API key or connection string.
        """
        if not api_key:
            raise ValueError("API key cannot be null or empty.")
        self._api_key = api_key

    async def get_access_token_async(self, scopes: List[str]) -> str:
        """Return the API key directly (no token acquisition needed)."""
        return self._api_key
