# Copyright (c) Microsoft Corporation. All rights reserved.

"""Unit tests for TextrequestClient."""

from unittest.mock import AsyncMock, patch

import pytest

from azure.connectors.textrequest import (
    CreateContactInput,
    CreateDashboardInput,
    CreateGroupInput,
    CreatePaymentInput,
    GetContactByPhoneNumberResponse,
    SendMessageByPhoneNumberInput,
    SendMessageByPhoneNumberResponse,
    TextrequestClient,
    UpdateDashboardsNameInput,
    UpdateGroupInput,
    TRIGGER_OPERATIONS,
)
from azure.connectors.sdk import (
    ConnectorClientOptions,
    ConnectorException,
    ManagedIdentityTokenProvider,
)
from tests.conftest import MockResponse


class TestTextrequestClientInitialization:
    """Tests for TextrequestClient initialization."""

    def test_init_with_valid_url_and_defaults(self):
        """Test initialization with valid URL and default parameters."""
        client = TextrequestClient("https://example.azure.com/connections/test")

        assert client._connection_runtime_url == "https://example.azure.com/connections/test"
        assert client.connector_name == "textrequest"
        assert isinstance(client._http_client._token_provider, ManagedIdentityTokenProvider)

    def test_init_with_trailing_slash(self):
        """Test that trailing slash is removed from URL."""
        client = TextrequestClient("https://example.azure.com/connections/test/")

        assert client._connection_runtime_url == "https://example.azure.com/connections/test"

    def test_init_with_custom_token_provider(self, mock_token_provider):
        """Test initialization with custom token provider."""
        client = TextrequestClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider,
        )

        assert client._http_client._token_provider is mock_token_provider

    def test_init_with_custom_options(self, mock_token_provider):
        """Test initialization with custom options."""
        options = ConnectorClientOptions(timeout_seconds=60.0, max_retry_attempts=5)
        client = TextrequestClient(
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
            TextrequestClient("")

    def test_init_with_none_url_raises_error(self):
        """Test that None URL raises ValueError."""
        with pytest.raises(ValueError, match="connection_runtime_url cannot be None or empty"):
            TextrequestClient(None)

    def test_connector_name_property(self, mock_token_provider):
        """Test connector_name property returns 'textrequest'."""
        client = TextrequestClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider,
        )

        assert client.connector_name == "textrequest"


class TestTextrequestClientLifecycle:
    """Tests for TextrequestClient lifecycle methods."""

    @pytest.mark.asyncio
    async def test_close(self, mock_token_provider):
        """Test close method calls http_client.close."""
        client = TextrequestClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider,
        )

        with patch.object(client._http_client, "close", new_callable=AsyncMock) as mock_close:
            await client.close()
            mock_close.assert_called_once()

    @pytest.mark.asyncio
    async def test_context_manager(self, mock_token_provider):
        """Test async context manager functionality."""
        with patch.object(TextrequestClient, "close", new_callable=AsyncMock) as mock_close:
            async with TextrequestClient(
                "https://example.azure.com/connections/test",
                token_provider=mock_token_provider,
            ) as client:
                assert isinstance(client, TextrequestClient)

            mock_close.assert_called_once()


class TestTextrequestClientOperations:
    """Tests for TextrequestClient operations against expected HTTP calls."""

    def _make_client(self, mock_token_provider):
        return TextrequestClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider,
        )

    @pytest.mark.asyncio
    async def test_get_messages_by_contact_phone_success(self, mock_token_provider):
        """Test get_messages_by_contact_phone issues a GET with paging query."""
        client = self._make_client(mock_token_provider)
        mock_response = MockResponse(status=200, text='{"items": []}')

        with patch.object(
            client._http_client, "send_async", new_callable=AsyncMock,
            return_value=mock_response,
        ) as mock_send:
            result = await client.get_messages_by_contact_phone_async(
                dashboard_id="7", phone_number="+15551112222", page="1", page_size="20"
            )

            url = mock_send.call_args[0][1]
            assert mock_send.call_args[0][0] == "GET"
            assert "/dashboards/7/contacts/%2B15551112222/messages" in url
            assert "page=1" in url
            assert "page_size=20" in url
            assert result == {"items": []}

    @pytest.mark.asyncio
    async def test_send_message_by_phone_number_success(self, mock_token_provider):
        """Test send_message_by_phone_number issues a POST with the input body."""
        client = self._make_client(mock_token_provider)
        payload = SendMessageByPhoneNumberInput(body="hello")
        mock_response = MockResponse(status=200, text='{"message_id": "m1"}')

        with patch.object(
            client._http_client, "send_async", new_callable=AsyncMock,
            return_value=mock_response,
        ) as mock_send:
            result = await client.send_message_by_phone_number_async(
                input=payload, dashboard_id="7", phone_number="+15551112222"
            )

            assert mock_send.call_args[0][0] == "POST"
            assert "/dashboards/7/contacts/%2B15551112222/messages" in mock_send.call_args[0][1]
            assert mock_send.call_args.kwargs["body"] is payload
            assert result == {"message_id": "m1"}

    @pytest.mark.asyncio
    async def test_archive_conversation_success(self, mock_token_provider):
        """Test archive_conversation issues a PUT to the archive route."""
        client = self._make_client(mock_token_provider)
        mock_response = MockResponse(status=200, text='{"ok": true}')

        with patch.object(
            client._http_client, "send_async", new_callable=AsyncMock,
            return_value=mock_response,
        ) as mock_send:
            result = await client.archive_conversation_async(
                dashboard_id="7", phone_number="+15551112222"
            )

            assert mock_send.call_args[0][0] == "PUT"
            assert "/conversations/archive" in mock_send.call_args[0][1]
            assert result == {"ok": True}

    @pytest.mark.asyncio
    async def test_unarchive_conversation_success(self, mock_token_provider):
        """Test unarchive_conversation issues a PUT to the unarchive route."""
        client = self._make_client(mock_token_provider)
        mock_response = MockResponse(status=200, text='{"ok": true}')

        with patch.object(
            client._http_client, "send_async", new_callable=AsyncMock,
            return_value=mock_response,
        ) as mock_send:
            result = await client.unarchive_conversation_async(
                dashboard_id="7", phone_number="+15551112222"
            )

            assert mock_send.call_args[0][0] == "PUT"
            assert "/conversations/unarchive" in mock_send.call_args[0][1]
            assert result == {"ok": True}

    @pytest.mark.asyncio
    async def test_get_contact_by_phone_number_success(self, mock_token_provider):
        """Test get_contact_by_phone_number issues a GET to the contact route."""
        client = self._make_client(mock_token_provider)
        mock_response = MockResponse(status=200, text='{"phone_number": "+15551112222"}')

        with patch.object(
            client._http_client, "send_async", new_callable=AsyncMock,
            return_value=mock_response,
        ) as mock_send:
            result = await client.get_contact_by_phone_number_async(
                dashboard_id="7", phone_number="+15551112222"
            )

            assert mock_send.call_args[0][0] == "GET"
            assert "/dashboards/7/contacts/%2B15551112222" in mock_send.call_args[0][1]
            assert result == {"phone_number": "+15551112222"}

    @pytest.mark.asyncio
    async def test_delete_contact_success(self, mock_token_provider):
        """Test delete_contact issues a DELETE to the contact route."""
        client = self._make_client(mock_token_provider)
        mock_response = MockResponse(status=200, text='{"ok": true}')

        with patch.object(
            client._http_client, "send_async", new_callable=AsyncMock,
            return_value=mock_response,
        ) as mock_send:
            result = await client.delete_contact_async(
                dashboard_id="7", phone_number="+15551112222"
            )

            assert mock_send.call_args[0][0] == "DELETE"
            assert "/dashboards/7/contacts/%2B15551112222" in mock_send.call_args[0][1]
            assert result == {"ok": True}

    @pytest.mark.asyncio
    async def test_create_contact_success(self, mock_token_provider):
        """Test create_contact issues a POST with the input body."""
        client = self._make_client(mock_token_provider)
        payload = CreateContactInput(first_name="Ada")
        mock_response = MockResponse(status=200, text='{"phone_number": "+15551112222"}')

        with patch.object(
            client._http_client, "send_async", new_callable=AsyncMock,
            return_value=mock_response,
        ) as mock_send:
            result = await client.create_contact_async(
                input=payload, dashboard_id="7", phone_number="+15551112222"
            )

            assert mock_send.call_args[0][0] == "POST"
            assert "/dashboards/7/contacts/%2B15551112222" in mock_send.call_args[0][1]
            assert mock_send.call_args.kwargs["body"] is payload
            assert result == {"phone_number": "+15551112222"}

    @pytest.mark.asyncio
    async def test_get_contacts_success(self, mock_token_provider):
        """Test get_contacts issues a GET with optional and paging query params."""
        client = self._make_client(mock_token_provider)
        mock_response = MockResponse(status=200, text='{"items": []}')

        with patch.object(
            client._http_client, "send_async", new_callable=AsyncMock,
            return_value=mock_response,
        ) as mock_send:
            result = await client.get_contacts_async(
                dashboard_id="7", page="1", page_size="20", is_resolved="true"
            )

            url = mock_send.call_args[0][1]
            assert mock_send.call_args[0][0] == "GET"
            assert "/dashboards/7/contacts" in url
            assert "is_resolved=true" in url
            assert "page=1" in url
            assert result == {"items": []}

    @pytest.mark.asyncio
    async def test_get_group_by_id_success(self, mock_token_provider):
        """Test get_group_by_id issues a GET to the group route."""
        client = self._make_client(mock_token_provider)
        mock_response = MockResponse(status=200, text='{"id": 3}')

        with patch.object(
            client._http_client, "send_async", new_callable=AsyncMock,
            return_value=mock_response,
        ) as mock_send:
            result = await client.get_group_by_id_async(dashboard_id="7", group_id="3")

            assert mock_send.call_args[0][0] == "GET"
            assert "/dashboards/7/groups/3" in mock_send.call_args[0][1]
            assert result == {"id": 3}

    @pytest.mark.asyncio
    async def test_update_group_success(self, mock_token_provider):
        """Test update_group issues a PUT with the input body."""
        client = self._make_client(mock_token_provider)
        payload = UpdateGroupInput()
        mock_response = MockResponse(status=200, text='{"id": 3}')

        with patch.object(
            client._http_client, "send_async", new_callable=AsyncMock,
            return_value=mock_response,
        ) as mock_send:
            result = await client.update_group_async(
                input=payload, dashboard_id="7", group_id="3"
            )

            assert mock_send.call_args[0][0] == "PUT"
            assert "/dashboards/7/groups/3" in mock_send.call_args[0][1]
            assert mock_send.call_args.kwargs["body"] is payload
            assert result == {"id": 3}

    @pytest.mark.asyncio
    async def test_create_group_success(self, mock_token_provider):
        """Test create_group issues a POST with the input body."""
        client = self._make_client(mock_token_provider)
        payload = CreateGroupInput()
        mock_response = MockResponse(status=200, text='{"id": 3}')

        with patch.object(
            client._http_client, "send_async", new_callable=AsyncMock,
            return_value=mock_response,
        ) as mock_send:
            result = await client.create_group_async(input=payload, dashboard_id="7")

            assert mock_send.call_args[0][0] == "POST"
            assert "/dashboards/7/groups" in mock_send.call_args[0][1]
            assert mock_send.call_args.kwargs["body"] is payload
            assert result == {"id": 3}

    @pytest.mark.asyncio
    async def test_get_custom_fields_success(self, mock_token_provider):
        """Test get_custom_fields issues a GET to the fields route."""
        client = self._make_client(mock_token_provider)
        mock_response = MockResponse(status=200, text='[]')

        with patch.object(
            client._http_client, "send_async", new_callable=AsyncMock,
            return_value=mock_response,
        ) as mock_send:
            result = await client.get_custom_fields_async(dashboard_id="7")

            assert mock_send.call_args[0][0] == "GET"
            assert "/dashboards/7/fields" in mock_send.call_args[0][1]
            assert result == []

    @pytest.mark.asyncio
    async def test_mark_payment_paid_success(self, mock_token_provider):
        """Test mark_payment_paid issues a POST to the mark_as_paid route."""
        client = self._make_client(mock_token_provider)
        mock_response = MockResponse(status=200, text='{"ok": true}')

        with patch.object(
            client._http_client, "send_async", new_callable=AsyncMock,
            return_value=mock_response,
        ) as mock_send:
            result = await client.mark_payment_paid_async(dashboard_id="7", payment_id="9")

            assert mock_send.call_args[0][0] == "POST"
            assert "/dashboards/7/payments/9/mark_as_paid" in mock_send.call_args[0][1]
            assert result == {"ok": True}

    @pytest.mark.asyncio
    async def test_create_payment_success(self, mock_token_provider):
        """Test create_payment issues a POST with the input body."""
        client = self._make_client(mock_token_provider)
        payload = CreatePaymentInput()
        mock_response = MockResponse(status=200, text='{"id": 9}')

        with patch.object(
            client._http_client, "send_async", new_callable=AsyncMock,
            return_value=mock_response,
        ) as mock_send:
            result = await client.create_payment_async(input=payload, dashboard_id="7")

            assert mock_send.call_args[0][0] == "POST"
            assert "/dashboards/7/payments" in mock_send.call_args[0][1]
            assert mock_send.call_args.kwargs["body"] is payload
            assert result == {"id": 9}

    @pytest.mark.asyncio
    async def test_get_dashboards_success(self, mock_token_provider):
        """Test get_dashboards issues a GET to the dashboards route."""
        client = self._make_client(mock_token_provider)
        mock_response = MockResponse(status=200, text='{"items": []}')

        with patch.object(
            client._http_client, "send_async", new_callable=AsyncMock,
            return_value=mock_response,
        ) as mock_send:
            result = await client.get_dashboards_async(page="1", page_size="20")

            url = mock_send.call_args[0][1]
            assert mock_send.call_args[0][0] == "GET"
            assert "/dashboards" in url
            assert "page=1" in url
            assert result == {"items": []}

    @pytest.mark.asyncio
    async def test_create_dashboard_success(self, mock_token_provider):
        """Test create_dashboard issues a POST with the input body."""
        client = self._make_client(mock_token_provider)
        payload = CreateDashboardInput()
        mock_response = MockResponse(status=200, text='{"id": 1}')

        with patch.object(
            client._http_client, "send_async", new_callable=AsyncMock,
            return_value=mock_response,
        ) as mock_send:
            result = await client.create_dashboard_async(input=payload)

            assert mock_send.call_args[0][0] == "POST"
            assert mock_send.call_args[0][1].endswith("/dashboards")
            assert mock_send.call_args.kwargs["body"] is payload
            assert result == {"id": 1}

    @pytest.mark.asyncio
    async def test_update_dashboards_name_success(self, mock_token_provider):
        """Test update_dashboards_name issues a PUT with the input body."""
        client = self._make_client(mock_token_provider)
        payload = UpdateDashboardsNameInput()
        mock_response = MockResponse(status=200, text='{"id": 7}')

        with patch.object(
            client._http_client, "send_async", new_callable=AsyncMock,
            return_value=mock_response,
        ) as mock_send:
            result = await client.update_dashboards_name_async(input=payload, dashboard_id="7")

            assert mock_send.call_args[0][0] == "PUT"
            assert mock_send.call_args[0][1].endswith("/dashboards/7")
            assert mock_send.call_args.kwargs["body"] is payload
            assert result == {"id": 7}

    @pytest.mark.asyncio
    async def test_empty_response_body_returns_none(self, mock_token_provider):
        """Test a 2xx response with no body returns None."""
        client = self._make_client(mock_token_provider)
        mock_response = MockResponse(status=200, text="")

        with patch.object(
            client._http_client, "send_async", new_callable=AsyncMock,
            return_value=mock_response,
        ):
            result = await client.get_dashboards_async()

            assert result is None


class TestTextrequestClientErrorHandling:
    """Error handling tests for TextrequestClient operations."""

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "operation",
        [
            "get_messages_by_contact_phone",
            "send_message_by_phone_number",
            "archive_conversation",
            "unarchive_conversation",
            "get_contact_by_phone_number",
            "delete_contact",
            "create_contact",
            "get_contacts",
            "bulk_update_contacts",
            "get_group_by_id",
            "delete_group",
            "update_group",
            "get_groups",
            "create_group",
            "get_tags",
            "get_custom_fields",
            "get_payment",
            "mark_payment_paid",
            "send_payment_reminder",
            "cancel_payment",
            "get_payments",
            "create_payment",
            "get_dashboard",
            "delete_dashboard",
            "update_dashboards_name",
            "get_conversations",
            "get_dashboards",
            "create_dashboard",
        ],
    )
    async def test_error_response_raises_exception(self, mock_token_provider, operation):
        """Test non-2xx responses raise ConnectorException for every operation."""
        client = TextrequestClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider,
        )
        mock_response = MockResponse(status=500, text='{"error":"server failure"}')

        with patch.object(
            client._http_client, "send_async", new_callable=AsyncMock,
            return_value=mock_response,
        ):
            with pytest.raises(ConnectorException) as exc_info:
                if operation == "get_messages_by_contact_phone":
                    await client.get_messages_by_contact_phone_async(
                        dashboard_id="7", phone_number="p", page="1", page_size="20"
                    )
                elif operation == "send_message_by_phone_number":
                    await client.send_message_by_phone_number_async(
                        input=SendMessageByPhoneNumberInput(), dashboard_id="7", phone_number="p"
                    )
                elif operation == "archive_conversation":
                    await client.archive_conversation_async(dashboard_id="7", phone_number="p")
                elif operation == "unarchive_conversation":
                    await client.unarchive_conversation_async(dashboard_id="7", phone_number="p")
                elif operation == "get_contact_by_phone_number":
                    await client.get_contact_by_phone_number_async(
                        dashboard_id="7", phone_number="p"
                    )
                elif operation == "delete_contact":
                    await client.delete_contact_async(dashboard_id="7", phone_number="p")
                elif operation == "create_contact":
                    await client.create_contact_async(
                        input=CreateContactInput(), dashboard_id="7", phone_number="p"
                    )
                elif operation == "get_contacts":
                    await client.get_contacts_async(
                        dashboard_id="7", page="1", page_size="20"
                    )
                elif operation == "bulk_update_contacts":
                    await client.bulk_update_contacts_async(input=[], dashboard_id="7")
                elif operation == "get_group_by_id":
                    await client.get_group_by_id_async(dashboard_id="7", group_id="3")
                elif operation == "delete_group":
                    await client.delete_group_async(dashboard_id="7", group_id="3")
                elif operation == "update_group":
                    await client.update_group_async(
                        input=UpdateGroupInput(), dashboard_id="7", group_id="3"
                    )
                elif operation == "get_groups":
                    await client.get_groups_async(dashboard_id="7", page="1", page_size="20")
                elif operation == "create_group":
                    await client.create_group_async(input=CreateGroupInput(), dashboard_id="7")
                elif operation == "get_tags":
                    await client.get_tags_async(dashboard_id="7", page="1", page_size="20")
                elif operation == "get_custom_fields":
                    await client.get_custom_fields_async(dashboard_id="7")
                elif operation == "get_payment":
                    await client.get_payment_async(dashboard_id="7", payment_id="9")
                elif operation == "mark_payment_paid":
                    await client.mark_payment_paid_async(dashboard_id="7", payment_id="9")
                elif operation == "send_payment_reminder":
                    await client.send_payment_reminder_async(dashboard_id="7", payment_id="9")
                elif operation == "cancel_payment":
                    await client.cancel_payment_async(dashboard_id="7", payment_id="9")
                elif operation == "get_payments":
                    await client.get_payments_async(dashboard_id="7", page="1", page_size="20")
                elif operation == "create_payment":
                    await client.create_payment_async(input=CreatePaymentInput(), dashboard_id="7")
                elif operation == "get_dashboard":
                    await client.get_dashboard_async(dashboard_id="7")
                elif operation == "delete_dashboard":
                    await client.delete_dashboard_async(dashboard_id="7")
                elif operation == "update_dashboards_name":
                    await client.update_dashboards_name_async(
                        input=UpdateDashboardsNameInput(), dashboard_id="7"
                    )
                elif operation == "get_conversations":
                    await client.get_conversations_async(dashboard_id="7")
                elif operation == "get_dashboards":
                    await client.get_dashboards_async()
                else:
                    await client.create_dashboard_async(input=CreateDashboardInput())

            assert exc_info.value.status_code == 500


class TestTextrequestTriggerOperations:
    """Tests for the module-level TRIGGER_OPERATIONS registry."""

    def test_all_expected_triggers_registered(self):
        """Test the registry exposes every TextRequest trigger operation."""
        assert set(TRIGGER_OPERATIONS) == {"TextingWebhook"}

    @pytest.mark.parametrize("operation_id", list(TRIGGER_OPERATIONS))
    def test_trigger_metadata_shape(self, operation_id):
        """Test each trigger entry carries the expected metadata fields."""
        trigger = TRIGGER_OPERATIONS[operation_id]

        assert trigger["operation_id"] == operation_id
        assert trigger["method"] == "post"
        assert trigger["path"].startswith("/{connectionId}/")
        assert "body" in trigger["required_parameters"]
        assert "callback_payload_type" in trigger

    def test_triggers_are_not_client_methods(self):
        """Test trigger operations are not emitted as callable client methods."""
        assert not hasattr(TextrequestClient, "texting_webhook_async")


class TestTextrequestTypeSerialization:
    """Tests for TextRequest dataclass defaults."""

    def test_dataclass_defaults(self):
        """Test dataclasses default their fields to None."""
        assert SendMessageByPhoneNumberInput().body is None
        assert SendMessageByPhoneNumberResponse().message_id is None
        assert SendMessageByPhoneNumberResponse().delivery_status is None
        assert GetContactByPhoneNumberResponse().phone_number is None
        assert CreateContactInput().first_name is None
        assert CreateContactInput().is_resolved is None
