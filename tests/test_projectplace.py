# Copyright (c) Microsoft Corporation. All rights reserved.

"""Unit tests for ProjectplaceClient."""

from unittest.mock import AsyncMock, patch

import pytest

from azure.connectors.projectplace import (
    CreateCardInput,
    MoveCardInput,
    ProjectplaceClient,
    TRIGGER_OPERATIONS,
)
from azure.connectors.sdk import (
    ConnectorClientOptions,
    ConnectorException,
    ManagedIdentityTokenProvider,
)
from tests.conftest import MockResponse


class TestProjectplaceClientInitialization:
    """Tests for ProjectplaceClient initialization."""

    def test_init_with_valid_url_and_defaults(self):
        """Test initialization with valid URL and default parameters."""
        client = ProjectplaceClient("https://example.azure.com/connections/test")

        assert client._connection_runtime_url == "https://example.azure.com/connections/test"
        assert client.connector_name == "projectplace"
        assert isinstance(client._http_client._token_provider, ManagedIdentityTokenProvider)

    def test_init_with_trailing_slash(self):
        """Test that trailing slash is removed from URL."""
        client = ProjectplaceClient("https://example.azure.com/connections/test/")

        assert client._connection_runtime_url == "https://example.azure.com/connections/test"

    def test_init_with_custom_token_provider(self, mock_token_provider):
        """Test initialization with custom token provider."""
        client = ProjectplaceClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider,
        )

        assert client._http_client._token_provider is mock_token_provider

    def test_init_with_custom_options(self, mock_token_provider):
        """Test initialization with custom options."""
        options = ConnectorClientOptions(timeout_seconds=60.0, max_retry_attempts=5)
        client = ProjectplaceClient(
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
            ProjectplaceClient("")

    def test_init_with_none_url_raises_error(self):
        """Test that None URL raises ValueError."""
        with pytest.raises(ValueError, match="connection_runtime_url cannot be None or empty"):
            ProjectplaceClient(None)

    def test_connector_name_property(self, mock_token_provider):
        """Test connector_name property returns 'projectplace'."""
        client = ProjectplaceClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider,
        )

        assert client.connector_name == "projectplace"


class TestProjectplaceClientLifecycle:
    """Tests for ProjectplaceClient lifecycle methods."""

    @pytest.mark.asyncio
    async def test_close(self, mock_token_provider):
        """Test close method calls http_client.close."""
        client = ProjectplaceClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider,
        )

        with patch.object(client._http_client, "close", new_callable=AsyncMock) as mock_close:
            await client.close()
            mock_close.assert_called_once()

    @pytest.mark.asyncio
    async def test_context_manager(self, mock_token_provider):
        """Test async context manager functionality."""
        with patch.object(ProjectplaceClient, "close", new_callable=AsyncMock) as mock_close:
            async with ProjectplaceClient(
                "https://example.azure.com/connections/test",
                token_provider=mock_token_provider,
            ) as client:
                assert isinstance(client, ProjectplaceClient)

            mock_close.assert_called_once()


class TestProjectplaceClientOperations:
    """Tests for ProjectplaceClient operations against expected HTTP calls."""

    @pytest.mark.asyncio
    async def test_create_card_success(self, mock_token_provider):
        """Test create card issues a POST to the create_card route with a body."""
        client = ProjectplaceClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider,
        )
        mock_response = MockResponse(status=200, text='{"id": 9}')

        with patch.object(
            client._http_client,
            "send_async",
            new_callable=AsyncMock,
            return_value=mock_response,
        ) as mock_send:
            result = await client.create_card_async(input=CreateCardInput(), board_id="42")

            method, url = mock_send.call_args[0][0], mock_send.call_args[0][1]
            assert method == "POST"
            assert url.endswith("/v1/external_notifications/42/create_card")
            assert mock_send.call_args.kwargs["body"] is not None
            assert result == {"id": 9}

    @pytest.mark.asyncio
    async def test_move_card_success(self, mock_token_provider):
        """Test move card issues a POST to the move_card route with a body."""
        client = ProjectplaceClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider,
        )
        mock_response = MockResponse(status=200, text='{"id": 5}')

        with patch.object(
            client._http_client,
            "send_async",
            new_callable=AsyncMock,
            return_value=mock_response,
        ) as mock_send:
            result = await client.move_card_async(input=MoveCardInput(), board_id="7")

            method, url = mock_send.call_args[0][0], mock_send.call_args[0][1]
            assert method == "POST"
            assert url.endswith("/v1/external_notifications/7/move_card")
            assert mock_send.call_args.kwargs["body"] is not None
            assert result == {"id": 5}

    @pytest.mark.asyncio
    async def test_list_boards_success(self, mock_token_provider):
        """Test list boards issues a GET to the list_boards route."""
        client = ProjectplaceClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider,
        )
        mock_response = MockResponse(status=200, text='[]')

        with patch.object(
            client._http_client,
            "send_async",
            new_callable=AsyncMock,
            return_value=mock_response,
        ) as mock_send:
            result = await client.list_boards_async()

            method, url = mock_send.call_args[0][0], mock_send.call_args[0][1]
            assert method == "GET"
            assert url.endswith("/v1/external_notifications/lists/list_boards")
            assert result == []

    @pytest.mark.asyncio
    async def test_empty_response_body_returns_none(self, mock_token_provider):
        """Test a 2xx response with no body returns None."""
        client = ProjectplaceClient(
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
            result = await client.create_card_async(input=CreateCardInput(), board_id="1")

            assert result is None


class TestProjectplaceClientErrorHandling:
    """Error handling tests for ProjectplaceClient operations."""

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "operation",
        ["create_card", "move_card", "list_boards"],
    )
    async def test_error_response_raises_exception(self, mock_token_provider, operation):
        """Test non-2xx responses raise ConnectorException for every operation."""
        client = ProjectplaceClient(
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
                if operation == "create_card":
                    await client.create_card_async(input=CreateCardInput(), board_id="1")
                elif operation == "move_card":
                    await client.move_card_async(input=MoveCardInput(), board_id="1")
                else:
                    await client.list_boards_async()

            assert exc_info.value.status_code == 500


class TestProjectplaceTriggerOperations:
    """Tests for the module-level TRIGGER_OPERATIONS registry."""

    def test_all_expected_triggers_registered(self):
        """Test the registry exposes every Projectplace trigger operation."""
        assert set(TRIGGER_OPERATIONS) == {
            "set_webhook_card_create",
            "set_webhook_properties_change",
            "set_webhook_card_due_date",
        }

    @pytest.mark.parametrize("operation_id", list(TRIGGER_OPERATIONS))
    def test_trigger_metadata_shape(self, operation_id):
        """Test each trigger entry carries the expected metadata fields."""
        trigger = TRIGGER_OPERATIONS[operation_id]

        assert trigger["operation_id"] == operation_id
        assert trigger["method"] == "post"
        assert trigger["path"].startswith("/{connectionId}/")
        assert "callback_payload_type" in trigger
        assert isinstance(trigger["required_parameters"], list)

    def test_triggers_are_not_client_methods(self):
        """Test trigger operations are not emitted as callable client methods."""
        assert not hasattr(ProjectplaceClient, "set_webhook_card_create_async")
        assert not hasattr(ProjectplaceClient, "set_webhook_properties_change_async")
        assert not hasattr(ProjectplaceClient, "set_webhook_card_due_date_async")


class TestProjectplaceTypeSerialization:
    """Tests for Projectplace connector dataclass defaults."""

    def test_request_dataclasses_instantiate(self):
        """Test generated request dataclasses instantiate without arguments."""
        assert CreateCardInput().title is None
        assert CreateCardInput().column_id is None
        assert MoveCardInput().card_id is None
        assert MoveCardInput().column_id is None
