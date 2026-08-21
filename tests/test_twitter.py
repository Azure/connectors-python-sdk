# Copyright (c) Microsoft Corporation. All rights reserved.

"""Unit tests for TwitterClient."""

from unittest.mock import AsyncMock, patch

import pytest

import azure.connectors.twitter as twitter_module
from azure.connectors.sdk import (
    ConnectorClientOptions,
    ConnectorException,
    ManagedIdentityTokenProvider,
)
from azure.connectors.twitter import TRIGGER_OPERATIONS, TwitterClient
from tests.conftest import MockResponse
from tests.generated_connector_test_utils import (
    get_generated_operations,
    invoke_generated_operation,
)


SUCCESS_CONTRACTS = {
    "followers": ("GET", "/followers?userName=value", False),
    "following": ("GET", "/friends?userName=value", False),
    "home_timeline": ("GET", "/hometimeline", False),
    "my_followers": ("GET", "/myfollowers", False),
    "my_following": ("GET", "/myfriends", False),
    "retweet": ("POST", "/retweet?tweetId=value", False),
    "search_tweet": ("GET", "/searchtweets?searchQuery=value", False),
    "tweet": ("POST", "/posttweet", True),
    "user": ("GET", "/user?userName=value", False),
    "user_timeline": ("GET", "/usertimeline?userName=value", False),
}
ALL_OPERATIONS = list(SUCCESS_CONTRACTS)


class TestTwitterClientInitialization:
    """Tests for TwitterClient initialization."""

    def test_init_with_valid_url_and_defaults(self):
        """Test initialization with valid URL and default parameters."""
        client = TwitterClient("https://example.azure.com/connections/test")

        assert client._connection_runtime_url == "https://example.azure.com/connections/test"
        assert client.connector_name == "twitter"
        assert isinstance(client._http_client._token_provider, ManagedIdentityTokenProvider)

    def test_init_with_trailing_slash(self):
        """Test that initialization removes a trailing slash."""
        client = TwitterClient("https://example.azure.com/connections/test/")

        assert client._connection_runtime_url == "https://example.azure.com/connections/test"

    def test_init_with_custom_token_provider(self, mock_token_provider):
        """Test initialization with a custom token provider."""
        client = TwitterClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider,
        )

        assert client._http_client._token_provider is mock_token_provider

    def test_init_with_custom_options(self, mock_token_provider):
        """Test initialization with custom client options."""
        options = ConnectorClientOptions(timeout_seconds=60.0, max_retry_attempts=5)
        client = TwitterClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider,
            options=options,
        )

        assert client._options is options

    @pytest.mark.parametrize("connection_runtime_url", ["", None])
    def test_init_with_invalid_url_raises_error(self, connection_runtime_url):
        """Test that an empty runtime URL raises ValueError."""
        with pytest.raises(ValueError, match="connection_runtime_url cannot be None or empty"):
            TwitterClient(connection_runtime_url)


class TestTwitterClientLifecycle:
    """Tests for TwitterClient lifecycle methods."""

    @pytest.mark.asyncio
    async def test_close(self, mock_token_provider):
        """Test close delegates to the HTTP client."""
        client = TwitterClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider,
        )

        with patch.object(client._http_client, "close", new_callable=AsyncMock) as mock_close:
            await client.close()

        mock_close.assert_called_once()

    @pytest.mark.asyncio
    async def test_context_manager(self, mock_token_provider):
        """Test async context manager cleanup."""
        with patch.object(TwitterClient, "close", new_callable=AsyncMock) as mock_close:
            async with TwitterClient(
                "https://example.azure.com/connections/test",
                token_provider=mock_token_provider,
            ) as client:
                assert isinstance(client, TwitterClient)

        mock_close.assert_called_once()


class TestTwitterClientOperations:
    """Tests for TwitterClient operations."""

    def test_all_generated_operations_are_covered(self):
        """Test the expected generated operation surface."""
        assert get_generated_operations(TwitterClient) == set(ALL_OPERATIONS)

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        ("operation", "expected_method", "expected_url_suffix", "expects_body"),
        [
            (operation, *contract)
            for operation, contract in SUCCESS_CONTRACTS.items()
        ],
    )
    async def test_generated_operation_success_contract(
        self,
        operation,
        expected_method,
        expected_url_suffix,
        expects_body,
        mock_token_provider,
    ):
        """Test every generated operation's successful HTTP contract."""
        client = TwitterClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider,
        )

        with patch.object(
            client._http_client,
            "send_async",
            new_callable=AsyncMock,
            return_value=MockResponse(status=200, text='{"ok": true}'),
        ) as mock_send:
            result = await invoke_generated_operation(client, operation, twitter_module)

        method, url = mock_send.call_args.args[:2]
        assert method == expected_method
        assert url.endswith(expected_url_suffix)
        assert (mock_send.call_args.kwargs["body"] is not None) is expects_body
        assert result == {"ok": True}

    @pytest.mark.asyncio
    async def test_user_timeline_success(self, mock_token_provider):
        """Test user timeline query construction."""
        client = TwitterClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider,
        )
        response = MockResponse(status=200, text='{"value": []}')

        with patch.object(
            client._http_client,
            "send_async",
            new_callable=AsyncMock,
            return_value=response,
        ) as mock_send:
            result = await client.user_timeline_async(user_name="Ada Lovelace", max_results="5")

        method, url = mock_send.call_args.args[:2]
        assert method == "GET"
        assert url.endswith("/usertimeline?userName=Ada%20Lovelace&maxResults=5")
        assert result == {"value": []}

    @pytest.mark.asyncio
    async def test_tweet_success(self, mock_token_provider):
        """Test tweet body and query construction."""
        client = TwitterClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider,
        )
        response = MockResponse(status=200, text='{"id": "tweet-1"}')

        with patch.object(
            client._http_client,
            "send_async",
            new_callable=AsyncMock,
            return_value=response,
        ) as mock_send:
            result = await client.tweet_async(input=b"payload", tweet_text="Hello")

        method, url = mock_send.call_args.args[:2]
        assert method == "POST"
        assert url.endswith("/posttweet?tweetText=Hello")
        assert mock_send.call_args.kwargs["body"] == b"payload"
        assert result == {"id": "tweet-1"}

    @pytest.mark.asyncio
    async def test_empty_response_returns_none(self, mock_token_provider):
        """Test an empty successful response returns None."""
        client = TwitterClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider,
        )

        with patch.object(
            client._http_client,
            "send_async",
            new_callable=AsyncMock,
            return_value=MockResponse(status=204, text=""),
        ):
            result = await client.home_timeline_async()

        assert result is None

    def test_trigger_metadata(self):
        """Test polling trigger metadata is registered instead of callable."""
        assert set(TRIGGER_OPERATIONS) == {"OnNewTweet"}
        assert TRIGGER_OPERATIONS["OnNewTweet"]["required_parameters"] == ["searchQuery"]
        assert not hasattr(TwitterClient, "on_new_tweet_async")

    @pytest.mark.asyncio
    @pytest.mark.parametrize("operation", ALL_OPERATIONS)
    async def test_non_success_response_raises_exception(
        self,
        operation,
        mock_token_provider,
    ):
        """Test every generated operation raises for a non-success response."""
        client = TwitterClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider,
        )

        with patch.object(
            client._http_client,
            "send_async",
            new_callable=AsyncMock,
            return_value=MockResponse(status=400, text="bad request"),
        ):
            with pytest.raises(ConnectorException):
                await invoke_generated_operation(client, operation, twitter_module)
