# Copyright (c) Microsoft Corporation. All rights reserved.

"""Unit tests for SalesforceClient."""

import pytest
from unittest.mock import AsyncMock, patch
from azure.connectors.salesforce import SalesforceClient
from azure.connectors.sdk import (
    ConnectorClientOptions,
    ManagedIdentityTokenProvider,
    ConnectorException,
)
from tests.conftest import MockResponse


class TestSalesforceClientInitialization:
    """Tests for SalesforceClient initialization."""

    def test_init_with_valid_url_and_defaults(self):
        """Test initialization with valid URL and default parameters."""
        client = SalesforceClient("https://example.azure.com/connections/test")

        assert client._connection_runtime_url == (
            "https://example.azure.com/connections/test"
        )
        assert client.connector_name == "salesforce"
        assert isinstance(
            client._http_client._token_provider, ManagedIdentityTokenProvider
        )

    def test_init_with_trailing_slash(self):
        """Test that trailing slash is removed from URL."""
        client = SalesforceClient("https://example.azure.com/connections/test/")

        assert client._connection_runtime_url == (
            "https://example.azure.com/connections/test"
        )

    def test_init_with_custom_token_provider(self, mock_token_provider):
        """Test initialization with custom token provider."""
        client = SalesforceClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider,
        )

        assert client._http_client._token_provider is mock_token_provider

    def test_init_with_custom_options(self, mock_token_provider):
        """Test initialization with custom options."""
        options = ConnectorClientOptions(
            timeout_seconds=60.0,
            max_retry_attempts=5,
        )
        client = SalesforceClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider,
            options=options,
        )

        assert client._options is options
        assert client._options.timeout_seconds == 60.0
        assert client._options.max_retry_attempts == 5

    def test_init_with_empty_url_raises_error(self):
        """Test that empty URL raises ValueError."""
        with pytest.raises(
            ValueError, match="connection_runtime_url cannot be None or empty"
        ):
            SalesforceClient("")

    def test_init_with_none_url_raises_error(self):
        """Test that None URL raises ValueError."""
        with pytest.raises(
            ValueError, match="connection_runtime_url cannot be None or empty"
        ):
            SalesforceClient(None)

    def test_connector_name_property(self, mock_token_provider):
        """Test connector_name property returns 'salesforce'."""
        client = SalesforceClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider,
        )

        assert client.connector_name == "salesforce"


class TestSalesforceClientLifecycle:
    """Tests for SalesforceClient lifecycle methods."""

    @pytest.mark.asyncio
    async def test_close(self, mock_token_provider):
        """Test close method calls http_client.close."""
        client = SalesforceClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider,
        )

        with patch.object(
            client._http_client,
            "close",
            new_callable=AsyncMock,
        ) as mock_close:
            await client.close()
            mock_close.assert_called_once()

    @pytest.mark.asyncio
    async def test_context_manager(self, mock_token_provider):
        """Test async context manager functionality."""
        with patch.object(
            SalesforceClient,
            "close",
            new_callable=AsyncMock,
        ) as mock_close:
            async with SalesforceClient(
                "https://example.azure.com/connections/test",
                token_provider=mock_token_provider,
            ) as client:
                assert isinstance(client, SalesforceClient)

            mock_close.assert_called_once()


class TestGetTables:
    """Tests for get_tables_async method."""

    @pytest.mark.asyncio
    async def test_success(self, mock_token_provider):
        """Test successful GET request."""
        client = SalesforceClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider,
        )

        mock_response = MockResponse(
            status=200,
            text='{"value": [{"name": "account", "displayName": "Account"}]}'
        )

        with patch.object(
            client._http_client,
            "send_async",
            new_callable=AsyncMock,
            return_value=mock_response,
        ) as mock_send:
            result = await client.get_tables_async()

            mock_send.assert_called_once()
            call_args = mock_send.call_args
            assert call_args[0][0] == "GET"
            assert "/datasets/default/tables" in call_args[0][1]
            assert result["value"][0]["name"] == "account"

    @pytest.mark.asyncio
    async def test_error_response_raises_exception(self, mock_token_provider):
        """Test that error response raises ConnectorException."""
        client = SalesforceClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider,
        )

        mock_response = MockResponse(status=401, text='{"error": "Unauthorized"}')

        with patch.object(
            client._http_client,
            "send_async",
            new_callable=AsyncMock,
            return_value=mock_response,
        ):
            with pytest.raises(ConnectorException) as exc_info:
                await client.get_tables_async()

            assert exc_info.value.status_code == 401


class TestGetItems:
    """Tests for get_items_async method."""

    @pytest.mark.asyncio
    async def test_with_query_parameters(self, mock_token_provider):
        """Test GET request includes expected query parameters."""
        client = SalesforceClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider,
        )

        mock_response = MockResponse(status=200, text='{"value": []}')

        with patch.object(
            client._http_client,
            "send_async",
            new_callable=AsyncMock,
            return_value=mock_response,
        ) as mock_send:
            await client.get_items_async(
                table="account",
                filter="Name eq 'Contoso'",
                top="5",
                select="Id,Name",
            )

            call_args = mock_send.call_args
            url = call_args[0][1]
            assert "/datasets/default/tables/account/items" in url
            assert "$filter=" in url
            assert "$top=5" in url
            assert "$select=Id%2CName" in url


class TestCreateJob:
    """Tests for create_job_async method."""

    @pytest.mark.asyncio
    async def test_sends_request_body(self, mock_token_provider):
        """Test create_job_async sends the input payload in request body."""
        client = SalesforceClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider,
        )

        payload = {
            "object": "Account",
            "operation": "insert",
            "contentType": "CSV",
        }
        mock_response = MockResponse(status=200, text='{"id": "750xx0000000001"}')

        with patch.object(
            client._http_client,
            "send_async",
            new_callable=AsyncMock,
            return_value=mock_response,
        ) as mock_send:
            result = await client.create_job_async(input=payload)

            call_args = mock_send.call_args
            assert call_args[0][0] == "POST"
            assert "/bulk/createjob" in call_args[0][1]
            assert call_args.kwargs["body"] == payload
            assert result["id"] == "750xx0000000001"


class TestPostItem:
    """Tests for post_item_async method."""

    @pytest.mark.asyncio
    async def test_sends_request_body(self, mock_token_provider):
        """Test post_item_async sends the input payload in request body."""
        client = SalesforceClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider,
        )

        payload = {
            "Name": "Contoso",
            "Phone": "425-555-0100",
        }
        mock_response = MockResponse(status=200, text='{"id": "001xx0000000001"}')

        with patch.object(
            client._http_client,
            "send_async",
            new_callable=AsyncMock,
            return_value=mock_response,
        ) as mock_send:
            result = await client.post_item_async(input=payload, table="account")

            call_args = mock_send.call_args
            assert call_args[0][0] == "POST"
            assert "/v2/datasets/default/tables/account/items" in call_args[0][1]
            assert call_args.kwargs["body"] == payload
            assert result["id"] == "001xx0000000001"
