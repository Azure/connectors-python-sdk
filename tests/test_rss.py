# Copyright (c) Microsoft Corporation. All rights reserved.

"""Unit tests for RssClient."""

import inspect

import pytest
from unittest.mock import AsyncMock, patch

from azure.core.credentials import AzureKeyCredential
from azure.connectors.rss import (
    FeedItem,
    RssClient,
    TRIGGER_OPERATIONS,
    TriggerBatchResponseFeedItem,
)
from azure.connectors.sdk import (
    ConnectorException,
)
from tests.conftest import MockResponse


async def _invoke_operation(client: RssClient, operation: str):
    """Invoke an RSS operation by name for shared parameterized tests."""
    if operation == "list_feed_items":
        return await client.list_feed_items_async(
            feed_url="https://contoso.example/feed.xml",
            since="2026-01-01T00:00:00Z",
            since_property="UpdatedOn",
        )

    raise ValueError(f"Unsupported operation '{operation}'.")


class TestRssClientInitialization:
    """Tests for RssClient initialization."""

    def test_init_with_valid_url_and_defaults(self):
        """Test initialization with valid URL and default parameters."""
        client = RssClient("https://example.azure.com/connections/test",
                           AzureKeyCredential("test-key"))

        assert client._connection_runtime_url == "https://example.azure.com/connections/test"
        assert client.connector_name == "rss"
        assert isinstance(client._http_client._credential, AzureKeyCredential)

    def test_init_with_trailing_slash(self):
        """Test that trailing slash is removed from URL."""
        client = RssClient("https://example.azure.com/connections/test/",
                           AzureKeyCredential("test-key"))

        assert client._connection_runtime_url == "https://example.azure.com/connections/test"

    def test_init_with_custom_credential(self, mock_credential):
        """Test initialization with custom token provider."""
        client = RssClient(
            "https://example.azure.com/connections/test",
            credential=mock_credential,
        )

        assert client._http_client._credential is mock_credential

    def test_init_with_custom_settings(self, mock_credential):
        """Test initialization with custom pipeline settings."""
        client = RssClient(
            "https://example.azure.com/connections/test",
            credential=mock_credential,
            timeout_seconds=60.0,
            max_retry_attempts=5,
        )
        assert client._http_client._timeout_seconds == 60.0

    def test_init_with_empty_url_raises_error(self):
        """Test that empty URL raises ValueError."""
        with pytest.raises(ValueError, match="connection_runtime_url cannot be None or empty"):
            RssClient("", AzureKeyCredential("test-key"))

    def test_init_with_none_url_raises_error(self):
        """Test that None URL raises ValueError."""
        with pytest.raises(ValueError, match="connection_runtime_url cannot be None or empty"):
            RssClient(None, AzureKeyCredential("test-key"))


class TestRssClientLifecycle:
    """Tests for RssClient lifecycle methods."""

    @pytest.mark.asyncio
    async def test_close(self, mock_credential):
        """Test close method calls http_client.close."""
        client = RssClient(
            "https://example.azure.com/connections/test",
            credential=mock_credential,
        )

        with patch.object(client._http_client, "close", new_callable=AsyncMock) as mock_close:
            await client.close()
            mock_close.assert_called_once()

    @pytest.mark.asyncio
    async def test_context_manager(self, mock_credential):
        """Test async context manager functionality."""
        with patch.object(RssClient, "close", new_callable=AsyncMock) as mock_close:
            async with RssClient(
                "https://example.azure.com/connections/test",
                credential=mock_credential,
            ) as client:
                assert isinstance(client, RssClient)

            mock_close.assert_called_once()


class TestRssClientMethods:
    """Success path tests for RSS operations."""

    @pytest.mark.asyncio
    async def test_list_feed_items_success(self, mock_credential):
        """Test list_feed_items_async serializes query params and returns JSON."""
        client = RssClient(
            "https://example.azure.com/connections/test",
            credential=mock_credential,
        )
        mock_response = MockResponse(status=200, text='[{"id":"1","title":"Item"}]')

        with patch.object(
            client._http_client,
            "send_async",
            new_callable=AsyncMock,
            return_value=mock_response,
        ) as mock_send:
            result = await client.list_feed_items_async(
                feed_url="https://contoso.example/feed.xml",
                since="2026-01-01T00:00:00Z",
                since_property="UpdatedOn",
            )

            assert len(result) == 1
            call_args = mock_send.call_args
            assert call_args[0][0] == "GET"
            assert "/ListFeedItems" in call_args[0][1]
            assert "feedUrl=https%3A%2F%2Fcontoso.example%2Ffeed.xml" in call_args[0][1]
            assert "since=2026-01-01T00%3A00%3A00Z" in call_args[0][1]
            assert "sinceProperty=UpdatedOn" in call_args[0][1]


class TestRssClientErrorHandling:
    """Error handling tests for RSS operations."""

    @pytest.mark.asyncio
    @pytest.mark.parametrize("operation", ["list_feed_items"])
    async def test_error_response_raises_exception_for_all_operations(
        self,
        mock_credential,
        operation,
    ):
        """Test non-2xx responses raise ConnectorException for every operation."""
        client = RssClient(
            "https://example.azure.com/connections/test",
            credential=mock_credential,
        )
        mock_response = MockResponse(status=500, text='{"error":"server failure"}')

        with patch.object(
            client._http_client,
            "send_async",
            new_callable=AsyncMock,
            return_value=mock_response,
        ):
            with pytest.raises(ConnectorException) as exc_info:
                await _invoke_operation(client, operation)

            assert exc_info.value.status_code == 500


class TestRssApiSurface:
    """Tests for the generated callable and trigger operation surfaces."""

    def test_callable_method_signatures(self):
        """Test the client exposes exactly the generated callable methods."""
        actual_signatures = {
            name: tuple(inspect.signature(method).parameters)
            for name, method in vars(RssClient).items()
            if inspect.iscoroutinefunction(method)
        }

        assert actual_signatures == {
            "list_feed_items_async": (
                "self",
                "feed_url",
                "since",
                "since_property",
                "timeout",
                "headers",
                "client_request_id",
                "response_hook",
            ),
        }

    def test_trigger_registry_metadata(self):
        """Test the feed trigger is represented by exact registration metadata."""
        assert TRIGGER_OPERATIONS == {
            "OnNewFeed": {
                "operation_id": "OnNewFeed",
                "path": "/{connectionId}/OnNewFeed",
                "method": "get",
                "required_parameters": ["feedUrl"],
                "callback_payload_type": "TriggerBatchResponseFeedItem",
            },
        }


class TestRssTypeSerialization:
    """Tests for RSS connector dataclass defaults."""

    def test_dataclass_instances_initialize_expected_defaults(self):
        """Test generated dataclasses initialize with expected default values."""
        feed_item = FeedItem()
        trigger_response = TriggerBatchResponseFeedItem()

        assert feed_item.id is None
        assert feed_item.title is None
        assert trigger_response.value is None
