# Copyright (c) Microsoft Corporation. All rights reserved.

"""Abstract base class for generated connector clients."""

from abc import ABC, abstractmethod
from typing import Optional, Union

from .authentication import TokenProvider, AzureIdentityTokenProvider
from .http_client import ConnectorHttpClient
from .options import ConnectorClientOptions


class ConnectorClientBase(ABC):
    """Abstract base class for generated connector clients."""

    def __init__(
        self,
        token_provider: Union[TokenProvider, object],
        options: Optional[ConnectorClientOptions] = None,
    ):
        """
        Initialize a ConnectorClientBase.

        Args:
            token_provider: The token provider for authentication. Can be a TokenProvider instance
                          or an Azure Identity credential (e.g., DefaultAzureCredential from azure.identity.aio).
            options: Optional connector client options.
        """
        if token_provider is None:
            raise ValueError("token_provider cannot be None")
        
        # NOTE(victoriahall): If the user passes an Azure Identity credential directly,
        # wrap it in an AzureIdentityTokenProvider for compatibility.
        if not isinstance(token_provider, TokenProvider):
            # Assume it's an Azure Identity credential
            token_provider = AzureIdentityTokenProvider(token_provider)
        
        self._options = options or ConnectorClientOptions()
        self._http_client = ConnectorHttpClient(token_provider, self._options)

    @property
    @abstractmethod
    def connector_name(self) -> str:
        """Get the connector name."""
        pass

    @property
    def http_client(self) -> ConnectorHttpClient:
        """Get the HTTP client for making connector requests."""
        return self._http_client

    async def close(self):
        """Close the HTTP client and release resources."""
        await self._http_client.close()

    async def __aenter__(self):
        """Enter async context manager."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Exit async context manager."""
        await self.close()
