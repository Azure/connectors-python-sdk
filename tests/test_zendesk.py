# Copyright (c) Microsoft Corporation. All rights reserved.

"""Unit tests for ZendeskClient."""

import inspect

import pytest
from unittest.mock import AsyncMock, patch

from azure.connectors.zendesk import (
    Item,
    ZendeskClient,
    TRIGGER_OPERATIONS,
)
from azure.connectors.sdk import (
    ConnectorClientOptions,
    ConnectorException,
    ManagedIdentityTokenProvider,
)
from tests.conftest import MockResponse


async def _invoke_operation(client: ZendeskClient, operation: str):
    """Invoke a Zendesk operation by name for shared tests."""
    if operation == "get_tables":
        return await client.get_tables_async()
    if operation == "get_items":
        return await client.get_items_async(table="tickets")
    if operation == "post_item":
        return await client.post_item_async(input=Item(), table="tickets")
    if operation == "get_item":
        return await client.get_item_async(table="tickets", id="1")
    if operation == "delete_item":
        return await client.delete_item_async(table="tickets", id="1")
    if operation == "patch_item":
        return await client.patch_item_async(input=Item(), table="tickets", id="1")
    if operation == "search_articles":
        return await client.search_articles_async(query="password")
    if operation == "get_table":
        return await client.get_table_async(table="tickets")

    raise ValueError(f"Unsupported operation '{operation}'.")


class TestZendeskClientInitialization:
    """Tests for ZendeskClient initialization."""

    def test_init_with_valid_url_and_defaults(self):
        """Test initialization with valid URL and default parameters."""
        client = ZendeskClient("https://example.azure.com/connections/test")

        assert client._connection_runtime_url == "https://example.azure.com/connections/test"
        assert client.connector_name == "zendesk"
        assert isinstance(client._http_client._token_provider, ManagedIdentityTokenProvider)

    def test_init_with_trailing_slash(self):
        """Test that trailing slash is removed from URL."""
        client = ZendeskClient("https://example.azure.com/connections/test/")

        assert client._connection_runtime_url == "https://example.azure.com/connections/test"

    def test_init_with_custom_token_provider(self, mock_token_provider):
        """Test initialization with custom token provider."""
        client = ZendeskClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider,
        )

        assert client._http_client._token_provider is mock_token_provider

    def test_init_with_custom_options(self, mock_token_provider):
        """Test initialization with custom options."""
        options = ConnectorClientOptions(timeout_seconds=60.0, max_retry_attempts=5)
        client = ZendeskClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider,
            options=options,
        )

        assert client._options is options
        assert client._options.timeout_seconds == 60.0
        assert client._options.max_retry_attempts == 5

    def test_init_with_empty_url_raises_error(self):
        """Test that empty URL raises ValueError."""
        with pytest.raises(ValueError, match="connection_runtime_url cannot be None or empty"):
            ZendeskClient("")

    def test_init_with_none_url_raises_error(self):
        """Test that None URL raises ValueError."""
        with pytest.raises(ValueError, match="connection_runtime_url cannot be None or empty"):
            ZendeskClient(None)

    def test_connector_name_property(self, mock_token_provider):
        """Test connector_name property returns 'zendesk'."""
        client = ZendeskClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider,
        )

        assert client.connector_name == "zendesk"


class TestZendeskClientLifecycle:
    """Tests for ZendeskClient lifecycle methods."""

    @pytest.mark.asyncio
    async def test_close(self, mock_token_provider):
        """Test close method calls http_client.close."""
        client = ZendeskClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider,
        )

        with patch.object(client._http_client, "close", new_callable=AsyncMock) as mock_close:
            await client.close()
            mock_close.assert_called_once()

    @pytest.mark.asyncio
    async def test_context_manager(self, mock_token_provider):
        """Test async context manager functionality."""
        with patch.object(ZendeskClient, "close", new_callable=AsyncMock) as mock_close:
            async with ZendeskClient(
                "https://example.azure.com/connections/test",
                token_provider=mock_token_provider,
            ) as client:
                assert isinstance(client, ZendeskClient)

            mock_close.assert_called_once()


class TestZendeskClientMethods:
    """Success path tests for Zendesk methods."""

    @pytest.mark.asyncio
    async def test_get_tables_success(self, mock_token_provider):
        """Test get_tables_async returns parsed JSON from the datasets endpoint."""
        client = ZendeskClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider,
        )
        mock_response = MockResponse(status=200, text='{"value":[{"name":"tickets"}]}')

        with patch.object(
            client._http_client,
            "send_async",
            new_callable=AsyncMock,
            return_value=mock_response,
        ) as mock_send:
            result = await client.get_tables_async()

            assert result["value"][0]["name"] == "tickets"
            assert mock_send.call_args[0][0] == "GET"
            assert "/datasets/default/tables" in mock_send.call_args[0][1]

    @pytest.mark.asyncio
    async def test_get_items_includes_query_params(self, mock_token_provider):
        """Test get_items_async serializes OData query parameters."""
        client = ZendeskClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider,
        )
        mock_response = MockResponse(status=200, text='{"value":[]}')

        with patch.object(
            client._http_client,
            "send_async",
            new_callable=AsyncMock,
            return_value=mock_response,
        ) as mock_send:
            await client.get_items_async(
                table="tickets",
                filter="status eq 'open'",
                top="10",
            )

            request_url = mock_send.call_args[0][1]
            assert mock_send.call_args[0][0] == "GET"
            assert "/datasets/default/tables/tickets/items" in request_url
            assert "$filter=" in request_url
            assert "$top=10" in request_url

    @pytest.mark.asyncio
    async def test_post_item_success(self, mock_token_provider):
        """Test post_item_async posts the body to the items endpoint."""
        client = ZendeskClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider,
        )
        mock_response = MockResponse(status=201, text='{"dynamic_properties":{"id":1}}')
        body = Item()

        with patch.object(
            client._http_client,
            "send_async",
            new_callable=AsyncMock,
            return_value=mock_response,
        ) as mock_send:
            result = await client.post_item_async(input=body, table="tickets")

            assert result["dynamic_properties"]["id"] == 1
            assert mock_send.call_args[0][0] == "POST"
            assert "/datasets/default/tables/tickets/items" in mock_send.call_args[0][1]
            assert mock_send.call_args.kwargs["body"] is body

    @pytest.mark.asyncio
    async def test_get_item_success(self, mock_token_provider):
        """Test get_item_async targets the single-item endpoint."""
        client = ZendeskClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider,
        )
        mock_response = MockResponse(status=200, text='{"dynamic_properties":{"id":42}}')

        with patch.object(
            client._http_client,
            "send_async",
            new_callable=AsyncMock,
            return_value=mock_response,
        ) as mock_send:
            result = await client.get_item_async(table="tickets", id="42")

            assert result["dynamic_properties"]["id"] == 42
            assert mock_send.call_args[0][0] == "GET"
            assert "/datasets/default/tables/tickets/items/42" in mock_send.call_args[0][1]

    @pytest.mark.asyncio
    async def test_delete_item_returns_none(self, mock_token_provider):
        """Test delete_item_async issues a DELETE and returns None."""
        client = ZendeskClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider,
        )
        mock_response = MockResponse(status=200, text="")

        with patch.object(
            client._http_client,
            "send_async",
            new_callable=AsyncMock,
            return_value=mock_response,
        ) as mock_send:
            result = await client.delete_item_async(table="tickets", id="42")

            assert result is None
            assert mock_send.call_args[0][0] == "DELETE"
            assert "/datasets/default/tables/tickets/items/42" in mock_send.call_args[0][1]

    @pytest.mark.asyncio
    async def test_patch_item_success(self, mock_token_provider):
        """Test patch_item_async sends the body via PATCH."""
        client = ZendeskClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider,
        )
        mock_response = MockResponse(status=200, text='{"dynamic_properties":{"id":42}}')
        body = Item()

        with patch.object(
            client._http_client,
            "send_async",
            new_callable=AsyncMock,
            return_value=mock_response,
        ) as mock_send:
            result = await client.patch_item_async(input=body, table="tickets", id="42")

            assert result["dynamic_properties"]["id"] == 42
            assert mock_send.call_args[0][0] == "PATCH"
            assert "/datasets/default/tables/tickets/items/42" in mock_send.call_args[0][1]
            assert mock_send.call_args.kwargs["body"] is body

    @pytest.mark.asyncio
    async def test_search_articles_includes_query_params(self, mock_token_provider):
        """Test search_articles_async serializes the help center query parameters."""
        client = ZendeskClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider,
        )
        mock_response = MockResponse(status=200, text='{"results":[]}')

        with patch.object(
            client._http_client,
            "send_async",
            new_callable=AsyncMock,
            return_value=mock_response,
        ) as mock_send:
            await client.search_articles_async(query="password reset", locale="en-us")

            request_url = mock_send.call_args[0][1]
            assert mock_send.call_args[0][0] == "GET"
            assert "/api/v2/help_center/articles/search" in request_url
            assert "query=password%20reset" in request_url
            assert "locale=en-us" in request_url

    @pytest.mark.asyncio
    async def test_get_table_success(self, mock_token_provider):
        """Test get_table_async targets the metadata endpoint."""
        client = ZendeskClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider,
        )
        mock_response = MockResponse(status=200, text='{"name":"tickets"}')

        with patch.object(
            client._http_client,
            "send_async",
            new_callable=AsyncMock,
            return_value=mock_response,
        ) as mock_send:
            result = await client.get_table_async(table="tickets")

            assert result["name"] == "tickets"
            assert mock_send.call_args[0][0] == "GET"
            assert "/$metadata.json/datasets/default/tables/tickets" in mock_send.call_args[0][1]

    @pytest.mark.asyncio
    async def test_get_tables_empty_returns_none(self, mock_token_provider):
        """Test get_tables_async returns None for an empty body."""
        client = ZendeskClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider,
        )
        mock_response = MockResponse(status=200, text="")

        with patch.object(
            client._http_client,
            "send_async",
            new_callable=AsyncMock,
            return_value=mock_response,
        ):
            result = await client.get_tables_async()

            assert result is None


class TestZendeskClientErrorHandling:
    """Error handling tests that ensure all methods raise ConnectorException."""

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "operation",
        [
            "get_tables",
            "get_items",
            "post_item",
            "get_item",
            "delete_item",
            "patch_item",
            "search_articles",
            "get_table",
        ],
    )
    async def test_error_response_raises_exception_for_all_operations(
        self,
        mock_token_provider,
        operation,
    ):
        """Test non-2xx responses raise ConnectorException for every operation."""
        client = ZendeskClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider,
        )
        mock_response = MockResponse(status=500, text='{"error":"server failure"}')

        with patch.object(
            client._http_client,
            "send_async",
            new_callable=AsyncMock,
            return_value=mock_response,
        ):
            with pytest.raises(ConnectorException):
                await _invoke_operation(client, operation)


class TestZendeskClientSignatures:
    """Tests that verify parameter and return annotations on public methods."""

    def test_search_articles_query_required_and_annotated_str(self):
        """Test the query parameter is required and annotated as str, not Optional."""
        signature = inspect.signature(ZendeskClient.search_articles_async)

        assert signature.parameters["query"].default is inspect.Parameter.empty
        assert signature.parameters["query"].annotation == "str"

    def test_search_articles_optional_params_default_to_none(self):
        """Test optional search params default to None."""
        signature = inspect.signature(ZendeskClient.search_articles_async)

        assert signature.parameters["locale"].default is None

    @pytest.mark.asyncio
    async def test_search_articles_missing_query_raises_type_error(self, mock_token_provider):
        """Test omitting the required query param raises TypeError."""
        client = ZendeskClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider,
        )

        with pytest.raises(TypeError):
            await client.search_articles_async()

    @pytest.mark.parametrize(
        "method_name",
        [
            "get_tables_async",
            "get_items_async",
            "post_item_async",
            "get_item_async",
            "delete_item_async",
            "patch_item_async",
            "search_articles_async",
            "get_table_async",
        ],
    )
    def test_public_methods_have_return_annotation(self, method_name):
        """Test every public async method declares a non-empty return annotation."""
        signature = inspect.signature(getattr(ZendeskClient, method_name))

        assert signature.return_annotation is not inspect.Signature.empty
        assert signature.return_annotation in ("dict[str, Any] | None", "None")


class TestZendeskTriggerOperations:
    """Tests for the module-level trigger registration metadata."""

    def test_on_new_items_registered_as_trigger(self):
        """Test the on-new-items route is registered as a trigger operation."""
        assert "GetOnNewItems" in TRIGGER_OPERATIONS
        trigger = TRIGGER_OPERATIONS["GetOnNewItems"]

        assert trigger["operation_id"] == "GetOnNewItems"
        assert trigger["path"].endswith("/onnewitems")

    def test_on_updated_items_registered_as_trigger(self):
        """Test the on-updated-items route is registered as a trigger operation."""
        assert "GetOnUpdatedItemsV2" in TRIGGER_OPERATIONS
        trigger = TRIGGER_OPERATIONS["GetOnUpdatedItemsV2"]

        assert trigger["operation_id"] == "GetOnUpdatedItemsV2"
        assert trigger["path"].endswith("/onupdateditems")

    def test_trigger_routes_not_client_methods(self):
        """Test the trigger routes are no longer exposed as callable client methods."""
        assert not hasattr(ZendeskClient, "get_on_new_items_async")
        assert not hasattr(ZendeskClient, "get_on_updated_items_async")
