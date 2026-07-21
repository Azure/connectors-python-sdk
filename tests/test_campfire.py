# Copyright (c) Microsoft Corporation. All rights reserved.

"""Unit tests for CampfireClient."""

from unittest.mock import AsyncMock, patch

import pytest

from azure.connectors.campfire import (
    Account,
    CampfireClient,
    Room,
    TRIGGER_OPERATIONS,
    Upload,
    UploadResponse,
)
from azure.connectors.sdk import (
    ConnectorClientOptions,
    ConnectorException,
    ManagedIdentityTokenProvider,
)
from tests.conftest import MockResponse


class TestCampfireClientInitialization:
    """Tests for CampfireClient initialization."""

    def test_init_with_valid_url_and_defaults(self):
        """Test initialization with valid URL and default parameters."""
        client = CampfireClient("https://example.azure.com/connections/test")

        assert client._connection_runtime_url == "https://example.azure.com/connections/test"
        assert client.connector_name == "campfire"
        assert isinstance(client._http_client._token_provider, ManagedIdentityTokenProvider)

    def test_init_with_trailing_slash(self):
        """Test that trailing slash is removed from URL."""
        client = CampfireClient("https://example.azure.com/connections/test/")

        assert client._connection_runtime_url == "https://example.azure.com/connections/test"

    def test_init_with_custom_token_provider(self, mock_token_provider):
        """Test initialization with custom token provider."""
        client = CampfireClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider,
        )

        assert client._http_client._token_provider is mock_token_provider

    def test_init_with_custom_options(self, mock_token_provider):
        """Test initialization with custom options."""
        options = ConnectorClientOptions(timeout_seconds=60.0, max_retry_attempts=5)
        client = CampfireClient(
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
            CampfireClient("")

    def test_init_with_none_url_raises_error(self):
        """Test that None URL raises ValueError."""
        with pytest.raises(ValueError, match="connection_runtime_url cannot be None or empty"):
            CampfireClient(None)

    def test_connector_name_property(self, mock_token_provider):
        """Test connector_name property returns 'campfire'."""
        client = CampfireClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider,
        )

        assert client.connector_name == "campfire"


class TestCampfireClientLifecycle:
    """Tests for CampfireClient lifecycle methods."""

    @pytest.mark.asyncio
    async def test_close(self, mock_token_provider):
        """Test close method calls http_client.close."""
        client = CampfireClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider,
        )

        with patch.object(client._http_client, "close", new_callable=AsyncMock) as mock_close:
            await client.close()
            mock_close.assert_called_once()

    @pytest.mark.asyncio
    async def test_context_manager(self, mock_token_provider):
        """Test async context manager functionality."""
        with patch.object(CampfireClient, "close", new_callable=AsyncMock) as mock_close:
            async with CampfireClient(
                "https://example.azure.com/connections/test",
                token_provider=mock_token_provider,
            ) as client:
                assert isinstance(client, CampfireClient)

            mock_close.assert_called_once()


class TestCampfireClientOperations:
    """Tests for CampfireClient operations against expected HTTP calls."""

    @pytest.mark.asyncio
    async def test_create_message_success(self, mock_token_provider):
        """Test create message issues a POST to the speak route with query params."""
        client = CampfireClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider,
        )
        mock_response = MockResponse(status=200, text='{"message": {"id": 1}}')

        with patch.object(
            client._http_client,
            "send_async",
            new_callable=AsyncMock,
            return_value=mock_response,
        ) as mock_send:
            result = await client.create_message_async(
                room_id="R1", account="acct1", message="hello"
            )

            method, url = mock_send.call_args[0][0], mock_send.call_args[0][1]
            assert method == "POST"
            assert "/room/R1/speak.json" in url
            assert "account=acct1" in url
            assert "message=hello" in url
            assert result == {"message": {"id": 1}}

    @pytest.mark.asyncio
    async def test_get_user_success(self, mock_token_provider):
        """Test get user issues a GET to the users route with account query param."""
        client = CampfireClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider,
        )
        mock_response = MockResponse(status=200, text='{"user": {"id": 5}}')

        with patch.object(
            client._http_client,
            "send_async",
            new_callable=AsyncMock,
            return_value=mock_response,
        ) as mock_send:
            result = await client.get_user_async(user_id="5", account="acct1")

            method, url = mock_send.call_args[0][0], mock_send.call_args[0][1]
            assert method == "GET"
            assert "/users/5.json" in url
            assert "account=acct1" in url
            assert result == {"user": {"id": 5}}

    @pytest.mark.asyncio
    async def test_list_accounts_success(self, mock_token_provider):
        """Test list accounts issues a GET to the authorization route."""
        client = CampfireClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider,
        )
        mock_response = MockResponse(status=200, text='{"accounts": []}')

        with patch.object(
            client._http_client,
            "send_async",
            new_callable=AsyncMock,
            return_value=mock_response,
        ) as mock_send:
            result = await client.list_accounts_async(parent_operation="op1")

            method, url = mock_send.call_args[0][0], mock_send.call_args[0][1]
            assert method == "GET"
            assert "/authorization.json" in url
            assert "parentOperation=op1" in url
            assert result == {"accounts": []}

    @pytest.mark.asyncio
    async def test_list_rooms_success(self, mock_token_provider):
        """Test list rooms issues a GET to the rooms route with account query param."""
        client = CampfireClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider,
        )
        mock_response = MockResponse(status=200, text='{"rooms": []}')

        with patch.object(
            client._http_client,
            "send_async",
            new_callable=AsyncMock,
            return_value=mock_response,
        ) as mock_send:
            result = await client.list_rooms_async(account="acct1")

            method, url = mock_send.call_args[0][0], mock_send.call_args[0][1]
            assert method == "GET"
            assert "/rooms.json" in url
            assert "account=acct1" in url
            assert result == {"rooms": []}

    @pytest.mark.asyncio
    async def test_empty_response_body_returns_none(self, mock_token_provider):
        """Test a 2xx response with no body returns None."""
        client = CampfireClient(
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
            result = await client.list_rooms_async(account="acct1")

            assert result is None


class TestCampfireClientErrorHandling:
    """Error handling tests for CampfireClient operations."""

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "operation",
        [
            "create_message",
            "get_user",
            "list_accounts",
            "list_rooms",
        ],
    )
    async def test_error_response_raises_exception(self, mock_token_provider, operation):
        """Test non-2xx responses raise ConnectorException for every operation."""
        client = CampfireClient(
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
            with pytest.raises(ConnectorException) as exc_info:
                if operation == "create_message":
                    await client.create_message_async(
                        room_id="R1", account="acct1", message="hello"
                    )
                elif operation == "get_user":
                    await client.get_user_async(user_id="5", account="acct1")
                elif operation == "list_accounts":
                    await client.list_accounts_async()
                else:
                    await client.list_rooms_async(account="acct1")

            assert exc_info.value.status_code == 500


class TestCampfireTriggerOperations:
    """Tests for the module-level TRIGGER_OPERATIONS registry."""

    def test_all_expected_triggers_registered(self):
        """Test the registry exposes every Campfire trigger operation."""
        assert set(TRIGGER_OPERATIONS) == {
            "OnNewRoom",
            "OnNewMessage",
            "OnNewUpload",
        }

    @pytest.mark.parametrize("operation_id", list(TRIGGER_OPERATIONS))
    def test_trigger_metadata_shape(self, operation_id):
        """Test each trigger entry carries the expected metadata fields."""
        trigger = TRIGGER_OPERATIONS[operation_id]

        assert trigger["operation_id"] == operation_id
        assert trigger["method"] == "get"
        assert trigger["path"].startswith("/{connectionId}/")
        assert "account" in trigger["required_parameters"]
        assert "callback_payload_type" in trigger

    def test_triggers_are_not_client_methods(self):
        """Test trigger operations are not emitted as callable client methods."""
        assert not hasattr(CampfireClient, "on_new_room_async")
        assert not hasattr(CampfireClient, "on_new_message_async")
        assert not hasattr(CampfireClient, "on_new_upload_async")


class TestCampfireTypeSerialization:
    """Tests for Campfire dataclass defaults."""

    def test_dataclass_defaults(self):
        """Test dataclasses default their fields to None."""
        assert Account().id is None
        assert Account().name is None
        assert Room().name is None
        assert Room().topic is None
        assert Upload().content_type is None
        assert UploadResponse().uploads is None
