# Copyright (c) Microsoft Corporation. All rights reserved.

"""Unit tests for FreshserviceClient."""

from unittest.mock import AsyncMock, patch

import pytest

from azure.connectors.freshservice import (
    AddNoteRequest,
    AddNoteResponse,
    CreateTicketRequest,
    CreateUpdateTicketResponse,
    FreshserviceClient,
    ListTicketResponse,
    ListUsersResponse,
    TicketResponse,
    UpdateTicketRequest,
    UpdateTicketResponse,
    TRIGGER_OPERATIONS,
)
from azure.connectors.sdk import (
    ConnectorClientOptions,
    ConnectorException,
    ManagedIdentityTokenProvider,
)
from tests.conftest import MockResponse


async def _invoke_operation(client: FreshserviceClient, operation: str):
    """Invoke a Freshservice operation by name for shared tests."""
    if operation == "add_note":
        return await client.add_note_async(input=AddNoteRequest(), ticket_id="1")
    if operation == "create_ticket":
        return await client.create_ticket_async(input=CreateTicketRequest())
    if operation == "update_ticket":
        return await client.update_ticket_async(input=UpdateTicketRequest(), ticket_id="1")

    raise ValueError(f"Unsupported operation '{operation}'.")


ALL_OPERATIONS = [
    "add_note",
    "create_ticket",
    "update_ticket",
]


class TestFreshserviceClientInitialization:
    """Tests for FreshserviceClient initialization."""

    def test_init_with_valid_url_and_defaults(self):
        """Test initialization with valid URL and default parameters."""
        client = FreshserviceClient("https://example.azure.com/connections/test")

        assert client._connection_runtime_url == "https://example.azure.com/connections/test"
        assert client.connector_name == "freshservice"
        assert isinstance(client._http_client._token_provider, ManagedIdentityTokenProvider)

    def test_init_with_trailing_slash(self):
        """Test that trailing slash is removed from URL."""
        client = FreshserviceClient("https://example.azure.com/connections/test/")

        assert client._connection_runtime_url == "https://example.azure.com/connections/test"

    def test_init_with_custom_token_provider(self, mock_token_provider):
        """Test initialization with custom token provider."""
        client = FreshserviceClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider,
        )

        assert client._http_client._token_provider is mock_token_provider

    def test_init_with_custom_options(self, mock_token_provider):
        """Test initialization with custom options."""
        options = ConnectorClientOptions(timeout_seconds=60.0, max_retry_attempts=5)
        client = FreshserviceClient(
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
            FreshserviceClient("")

    def test_init_with_none_url_raises_error(self):
        """Test that None URL raises ValueError."""
        with pytest.raises(ValueError, match="connection_runtime_url cannot be None or empty"):
            FreshserviceClient(None)

    def test_connector_name_property(self, mock_token_provider):
        """Test connector_name property returns 'freshservice'."""
        client = FreshserviceClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider,
        )

        assert client.connector_name == "freshservice"


class TestFreshserviceClientLifecycle:
    """Tests for FreshserviceClient lifecycle methods."""

    @pytest.mark.asyncio
    async def test_close(self, mock_token_provider):
        """Test close method calls http_client.close."""
        client = FreshserviceClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider,
        )

        with patch.object(client._http_client, "close", new_callable=AsyncMock) as mock_close:
            await client.close()
            mock_close.assert_called_once()

    @pytest.mark.asyncio
    async def test_context_manager(self, mock_token_provider):
        """Test async context manager functionality."""
        with patch.object(FreshserviceClient, "close", new_callable=AsyncMock) as mock_close:
            async with FreshserviceClient(
                "https://example.azure.com/connections/test",
                token_provider=mock_token_provider,
            ) as client:
                assert isinstance(client, FreshserviceClient)

            mock_close.assert_called_once()


class TestFreshserviceClientOperations:
    """Tests for FreshserviceClient operations against expected HTTP calls."""

    @pytest.mark.asyncio
    async def test_create_ticket_success(self, mock_token_provider):
        """Test ticket creation issues a POST to /api/v2/tickets with body."""
        client = FreshserviceClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider,
        )
        mock_response = MockResponse(status=201, text='{"ticket": {"id": 9}}')

        with patch.object(
            client._http_client,
            "send_async",
            new_callable=AsyncMock,
            return_value=mock_response,
        ) as mock_send:
            result = await client.create_ticket_async(input=CreateTicketRequest())

            method, path = mock_send.call_args[0][0], mock_send.call_args[0][1]
            assert method == "POST"
            assert path.endswith("/api/v2/tickets")
            assert mock_send.call_args.kwargs["body"] is not None
            assert result == {"ticket": {"id": 9}}

    @pytest.mark.asyncio
    async def test_update_ticket_success_targets_resource(self, mock_token_provider):
        """Test ticket update issues a PUT to /api/v2/tickets/{id}."""
        client = FreshserviceClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider,
        )
        mock_response = MockResponse(status=200, text='{"ticket": {"id": 5}}')

        with patch.object(
            client._http_client,
            "send_async",
            new_callable=AsyncMock,
            return_value=mock_response,
        ) as mock_send:
            result = await client.update_ticket_async(input=UpdateTicketRequest(), ticket_id="5")

            method, path = mock_send.call_args[0][0], mock_send.call_args[0][1]
            assert method == "PUT"
            assert path.endswith("/api/v2/tickets/5")
            assert mock_send.call_args.kwargs["body"] is not None
            assert result == {"ticket": {"id": 5}}

    @pytest.mark.asyncio
    async def test_add_note_success_targets_notes(self, mock_token_provider):
        """Test adding a note issues a POST to /api/v2/tickets/{id}/notes."""
        client = FreshserviceClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider,
        )
        mock_response = MockResponse(status=201, text='{"conversation": {"id": 3}}')

        with patch.object(
            client._http_client,
            "send_async",
            new_callable=AsyncMock,
            return_value=mock_response,
        ) as mock_send:
            result = await client.add_note_async(input=AddNoteRequest(), ticket_id="7")

            method, path = mock_send.call_args[0][0], mock_send.call_args[0][1]
            assert method == "POST"
            assert path.endswith("/api/v2/tickets/7/notes")
            assert mock_send.call_args.kwargs["body"] is not None
            assert result == {"conversation": {"id": 3}}

    @pytest.mark.asyncio
    async def test_empty_response_body_returns_none(self, mock_token_provider):
        """Test a 2xx response with no body returns None."""
        client = FreshserviceClient(
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
            result = await client.create_ticket_async(input=CreateTicketRequest())

            assert result is None


class TestFreshserviceClientErrorHandling:
    """Error handling tests that ensure all methods raise ConnectorException."""

    @pytest.mark.asyncio
    @pytest.mark.parametrize("operation", ALL_OPERATIONS)
    async def test_error_response_raises_exception_for_all_operations(
        self,
        mock_token_provider,
        operation,
    ):
        """Test non-2xx responses raise ConnectorException for every operation."""
        client = FreshserviceClient(
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
                await _invoke_operation(client, operation)

            assert exc_info.value.status_code == 500


class TestFreshserviceTriggerOperations:
    """Tests for the module-level TRIGGER_OPERATIONS registry."""

    def test_all_expected_triggers_registered(self):
        """Test the registry exposes every Freshservice trigger operation."""
        assert set(TRIGGER_OPERATIONS) == {
            "OnTicketCreatedV2",
        }

    @pytest.mark.parametrize("operation_id", list(TRIGGER_OPERATIONS))
    def test_trigger_metadata_shape(self, operation_id):
        """Test each trigger entry carries the expected metadata fields."""
        trigger = TRIGGER_OPERATIONS[operation_id]

        assert trigger["operation_id"] == operation_id
        assert trigger["method"] == "get"
        assert trigger["path"].startswith("/{connectionId}/")
        assert "callback_payload_type" in trigger
        assert isinstance(trigger["required_parameters"], list)

    def test_triggers_are_not_client_methods(self):
        """Test trigger operations are not emitted as callable client methods."""
        assert not hasattr(FreshserviceClient, "on_ticket_created_v2_async")


class TestFreshserviceTypeSerialization:
    """Tests for Freshservice connector dataclass defaults."""

    def test_response_dataclasses_initialize_expected_defaults(self):
        """Test generated response dataclasses initialize with None defaults."""
        assert ListTicketResponse().id is None
        assert ListTicketResponse().type_ is None
        assert AddNoteResponse().conversation is None
        assert CreateUpdateTicketResponse().ticket is None
        assert UpdateTicketResponse().ticket is None
        assert TicketResponse().id is None
        assert ListUsersResponse().additional_properties == {}

    def test_request_dataclasses_instantiate(self):
        """Test generated request dataclasses instantiate without arguments."""
        assert CreateTicketRequest().helpdesk_ticket is None
        assert UpdateTicketRequest().helpdesk_ticket is None
        assert AddNoteRequest().helpdesk_note is None
