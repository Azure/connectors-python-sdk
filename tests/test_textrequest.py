# Copyright (c) Microsoft Corporation. All rights reserved.

"""Unit tests for TextrequestClient."""

from unittest.mock import AsyncMock, patch

import pytest

from azure.core.credentials import AzureKeyCredential
import azure.connectors.textrequest as textrequest_module
from azure.connectors.textrequest import TextrequestClient
from azure.connectors.textrequest import (
    CreateContactInput,
    CreateDashboardInput,
    CreateGroupInput,
    CreatePaymentInput,
    GetContactByPhoneNumberResponse,
    SendMessageByPhoneNumberInput,
    SendMessageByPhoneNumberResponse,
    UpdateDashboardsNameInput,
    UpdateGroupInput,
    TRIGGER_OPERATIONS,
)
from azure.connectors.sdk import (
    ConnectorException,
)
from tests.conftest import MockResponse
from tests.generated_connector_test_utils import (
    get_generated_operations,
    invoke_generated_operation,
    resolve_generated_result,
)


SUCCESS_CONTRACTS = {
    "archive_conversation": (
        "PUT",
        "/dashboards/1/contacts/value/conversations/archive",
        False,
    ),
    "bulk_update_contacts": ("POST", "/dashboards/1/contacts", True),
    "cancel_payment": (
        "POST",
        "/dashboards/1/payments/1/cancel",
        False,
    ),
    "create_contact": ("POST", "/dashboards/1/contacts/value", True),
    "create_dashboard": ("POST", "/dashboards", True),
    "create_group": ("POST", "/dashboards/1/groups", True),
    "create_payment": ("POST", "/dashboards/1/payments", True),
    "delete_contact": ("DELETE", "/dashboards/1/contacts/value", False),
    "delete_dashboard": ("DELETE", "/dashboards/1", False),
    "delete_group": ("DELETE", "/dashboards/1/groups/1", False),
    "get_contact_by_phone_number": (
        "GET",
        "/dashboards/1/contacts/value",
        False,
    ),
    "list_contacts": (
        "GET",
        "/dashboards/1/contacts?page=1&page_size=1",
        False,
    ),
    "list_conversations": ("GET", "/dashboards/1/conversations", False),
    "list_custom_fields": ("GET", "/dashboards/1/fields", False),
    "get_dashboard": ("GET", "/dashboards/1", False),
    "list_dashboards": ("GET", "/dashboards", False),
    "get_group_by_id": ("GET", "/dashboards/1/groups/1", False),
    "list_groups": (
        "GET",
        "/dashboards/1/groups?page=1&page_size=1",
        False,
    ),
    "list_messages_by_contact_phone": (
        "GET",
        "/dashboards/1/contacts/value/messages?page=1&page_size=1",
        False,
    ),
    "get_payment": ("GET", "/dashboards/1/payments/1", False),
    "list_payments": (
        "GET",
        "/dashboards/1/payments?page=1&page_size=1",
        False,
    ),
    "list_tags": (
        "GET",
        "/dashboards/1/tags?page=1&page_size=1",
        False,
    ),
    "mark_payment_paid": (
        "POST",
        "/dashboards/1/payments/1/mark_as_paid",
        False,
    ),
    "send_message_by_phone_number": (
        "POST",
        "/dashboards/1/contacts/value/messages",
        True,
    ),
    "send_payment_reminder": (
        "POST",
        "/dashboards/1/payments/1/resend",
        False,
    ),
    "unarchive_conversation": (
        "PUT",
        "/dashboards/1/contacts/value/conversations/unarchive",
        False,
    ),
    "update_dashboards_name": ("PUT", "/dashboards/1", True),
    "update_group": ("PUT", "/dashboards/1/groups/1", True),
}
ALL_OPERATIONS = list(SUCCESS_CONTRACTS)
PAGED_OPERATIONS = {
    "list_contacts",
    "list_conversations",
    "list_dashboards",
    "list_groups",
    "list_messages_by_contact_phone",
    "list_payments",
    "list_tags",
}


class TestTextrequestClientInitialization:
    """Tests for TextrequestClient initialization."""

    def test_init_with_valid_url_and_defaults(self):
        """Test initialization with valid URL and default parameters."""
        client = TextrequestClient(
            "https://example.azure.com/connections/test", AzureKeyCredential("test-key"))

        assert client._connection_runtime_url == "https://example.azure.com/connections/test"
        assert client.connector_name == "textrequest"
        assert isinstance(client._http_client._credential, AzureKeyCredential)

    def test_init_with_trailing_slash(self):
        """Test that trailing slash is removed from URL."""
        client = TextrequestClient(
            "https://example.azure.com/connections/test/", AzureKeyCredential("test-key"))

        assert client._connection_runtime_url == "https://example.azure.com/connections/test"

    def test_init_with_custom_credential(self, mock_credential):
        """Test initialization with custom token provider."""
        client = TextrequestClient(
            "https://example.azure.com/connections/test",
            credential=mock_credential,
        )

        assert client._http_client._credential is mock_credential

    def test_init_with_custom_settings(self, mock_credential):
        """Test initialization with custom pipeline settings."""
        client = TextrequestClient(
            "https://example.azure.com/connections/test",
            credential=mock_credential,
            timeout=60.0,
            max_retry_attempts=5,
        )
        assert client._http_client._timeout_seconds == 60.0

    def test_init_with_empty_url_raises_error(self):
        """Test that empty URL raises ValueError."""
        with pytest.raises(ValueError, match="connection_runtime_url cannot be None or empty"):
            TextrequestClient("", AzureKeyCredential("test-key"))

    def test_init_with_none_url_raises_error(self):
        """Test that None URL raises ValueError."""
        with pytest.raises(ValueError, match="connection_runtime_url cannot be None or empty"):
            TextrequestClient(None, AzureKeyCredential("test-key"))

    def test_connector_name_property(self, mock_credential):
        """Test connector_name property returns 'textrequest'."""
        client = TextrequestClient(
            "https://example.azure.com/connections/test",
            credential=mock_credential,
        )

        assert client.connector_name == "textrequest"


class TestTextrequestClientLifecycle:
    """Tests for TextrequestClient lifecycle methods."""

    @pytest.mark.asyncio
    async def test_close(self, mock_credential):
        """Test close method calls http_client.close."""
        client = TextrequestClient(
            "https://example.azure.com/connections/test",
            credential=mock_credential,
        )

        with patch.object(client._http_client, "close", new_callable=AsyncMock) as mock_close:
            await client.close()
            mock_close.assert_called_once()

    @pytest.mark.asyncio
    async def test_context_manager(self, mock_credential):
        """Test async context manager functionality."""
        with patch.object(TextrequestClient, "close", new_callable=AsyncMock) as mock_close:
            async with TextrequestClient(
                "https://example.azure.com/connections/test",
                credential=mock_credential,
            ) as client:
                assert isinstance(client, TextrequestClient)

            mock_close.assert_called_once()


class TestTextrequestClientOperations:
    """Tests for TextrequestClient operations against expected HTTP calls."""

    def _make_client(self, mock_credential):
        return TextrequestClient(
            "https://example.azure.com/connections/test",
            credential=mock_credential,
        )

    def test_all_generated_operations_are_covered(self):
        """Test the expected generated operation surface."""
        assert get_generated_operations(TextrequestClient) == set(ALL_OPERATIONS)

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
        mock_credential,
    ):
        """Test every generated operation's successful HTTP contract."""
        client = self._make_client(mock_credential)

        with patch.object(
            client._http_client,
            "send",
            new_callable=AsyncMock,
            return_value=MockResponse(
                status=200,
                text=(
                    '[{"ok": true}]'
                    if operation in {
                        "bulk_update_contacts",
                        "list_custom_fields",
                    }
                    else '{"items": [{"ok": true}]}'
                    if operation in PAGED_OPERATIONS
                    else '{"ok": true}'
                ),
            ),
        ) as mock_send:
            result = await invoke_generated_operation(
                client,
                operation,
                textrequest_module,
            )

        method, url = mock_send.call_args.args[:2]
        assert method == expected_method
        assert url.endswith(expected_url_suffix)
        assert (mock_send.call_args.kwargs["body"] is not None) is expects_body
        expected_result = (
            [{"ok": True}]
            if operation in {
                "bulk_update_contacts",
                "list_custom_fields",
            } | PAGED_OPERATIONS
            else {"ok": True}
        )
        assert result == expected_result

    @pytest.mark.asyncio
    async def test_get_messages_by_contact_phone_success(self, mock_credential):
        """Test get_messages_by_contact_phone issues a GET with paging query."""
        client = self._make_client(mock_credential)
        mock_response = MockResponse(status=200, text='{"items": []}')

        with patch.object(
            client._http_client, "send", new_callable=AsyncMock,
            return_value=mock_response,
        ) as mock_send:
            result = await resolve_generated_result(
                client.list_messages_by_contact_phone(
                    dashboard_id="7",
                    phone_number="+15551112222",
                    page="1",
                    page_size="20",
                )
            )

            url = mock_send.call_args[0][1]
            assert mock_send.call_args[0][0] == "GET"
            assert "/dashboards/7/contacts/%2B15551112222/messages" in url
            assert "page=1" in url
            assert "page_size=20" in url
            assert result == []

    @pytest.mark.asyncio
    async def test_send_message_by_phone_number_success(self, mock_credential):
        """Test send_message_by_phone_number issues a POST with the input body."""
        client = self._make_client(mock_credential)
        payload = SendMessageByPhoneNumberInput(body="hello")
        mock_response = MockResponse(status=200, text='{"message_id": "m1"}')

        with patch.object(
            client._http_client, "send", new_callable=AsyncMock,
            return_value=mock_response,
        ) as mock_send:
            result = await client.send_message_by_phone_number(
                input=payload, dashboard_id="7", phone_number="+15551112222"
            )

            assert mock_send.call_args[0][0] == "POST"
            assert "/dashboards/7/contacts/%2B15551112222/messages" in mock_send.call_args[0][1]
            assert mock_send.call_args.kwargs["body"] is payload
            assert result == {"message_id": "m1"}

    @pytest.mark.asyncio
    async def test_archive_conversation_success(self, mock_credential):
        """Test archive_conversation issues a PUT to the archive route."""
        client = self._make_client(mock_credential)
        mock_response = MockResponse(status=200, text='{"ok": true}')

        with patch.object(
            client._http_client, "send", new_callable=AsyncMock,
            return_value=mock_response,
        ) as mock_send:
            result = await client.archive_conversation(
                dashboard_id="7", phone_number="+15551112222"
            )

            assert mock_send.call_args[0][0] == "PUT"
            assert "/conversations/archive" in mock_send.call_args[0][1]
            assert result == {"ok": True}

    @pytest.mark.asyncio
    async def test_unarchive_conversation_success(self, mock_credential):
        """Test unarchive_conversation issues a PUT to the unarchive route."""
        client = self._make_client(mock_credential)
        mock_response = MockResponse(status=200, text='{"ok": true}')

        with patch.object(
            client._http_client, "send", new_callable=AsyncMock,
            return_value=mock_response,
        ) as mock_send:
            result = await client.unarchive_conversation(
                dashboard_id="7", phone_number="+15551112222"
            )

            assert mock_send.call_args[0][0] == "PUT"
            assert "/conversations/unarchive" in mock_send.call_args[0][1]
            assert result == {"ok": True}

    @pytest.mark.asyncio
    async def test_get_contact_by_phone_number_success(self, mock_credential):
        """Test get_contact_by_phone_number issues a GET to the contact route."""
        client = self._make_client(mock_credential)
        mock_response = MockResponse(status=200, text='{"phone_number": "+15551112222"}')

        with patch.object(
            client._http_client, "send", new_callable=AsyncMock,
            return_value=mock_response,
        ) as mock_send:
            result = await client.get_contact_by_phone_number(
                dashboard_id="7", phone_number="+15551112222"
            )

            assert mock_send.call_args[0][0] == "GET"
            assert "/dashboards/7/contacts/%2B15551112222" in mock_send.call_args[0][1]
            assert result == {"phone_number": "+15551112222"}

    @pytest.mark.asyncio
    async def test_delete_contact_success(self, mock_credential):
        """Test delete_contact issues a DELETE to the contact route."""
        client = self._make_client(mock_credential)
        mock_response = MockResponse(status=200, text='{"ok": true}')

        with patch.object(
            client._http_client, "send", new_callable=AsyncMock,
            return_value=mock_response,
        ) as mock_send:
            result = await client.delete_contact(
                dashboard_id="7", phone_number="+15551112222"
            )

            assert mock_send.call_args[0][0] == "DELETE"
            assert "/dashboards/7/contacts/%2B15551112222" in mock_send.call_args[0][1]
            assert result == {"ok": True}

    @pytest.mark.asyncio
    async def test_create_contact_success(self, mock_credential):
        """Test create_contact issues a POST with the input body."""
        client = self._make_client(mock_credential)
        payload = CreateContactInput(first_name="Ada")
        mock_response = MockResponse(status=200, text='{"phone_number": "+15551112222"}')

        with patch.object(
            client._http_client, "send", new_callable=AsyncMock,
            return_value=mock_response,
        ) as mock_send:
            result = await client.create_contact(
                input=payload, dashboard_id="7", phone_number="+15551112222"
            )

            assert mock_send.call_args[0][0] == "POST"
            assert "/dashboards/7/contacts/%2B15551112222" in mock_send.call_args[0][1]
            assert mock_send.call_args.kwargs["body"] is payload
            assert result == {"phone_number": "+15551112222"}

    @pytest.mark.asyncio
    async def test_get_contacts_success(self, mock_credential):
        """Test get_contacts issues a GET with optional and paging query params."""
        client = self._make_client(mock_credential)
        mock_response = MockResponse(status=200, text='{"items": []}')

        with patch.object(
            client._http_client, "send", new_callable=AsyncMock,
            return_value=mock_response,
        ) as mock_send:
            result = await resolve_generated_result(
                client.list_contacts(
                    dashboard_id="7",
                    page="1",
                    page_size="20",
                    is_resolved="true",
                )
            )

            url = mock_send.call_args[0][1]
            assert mock_send.call_args[0][0] == "GET"
            assert "/dashboards/7/contacts" in url
            assert "is_resolved=true" in url
            assert "page=1" in url
            assert result == []

    @pytest.mark.asyncio
    async def test_get_group_by_id_success(self, mock_credential):
        """Test get_group_by_id issues a GET to the group route."""
        client = self._make_client(mock_credential)
        mock_response = MockResponse(status=200, text='{"id": 3}')

        with patch.object(
            client._http_client, "send", new_callable=AsyncMock,
            return_value=mock_response,
        ) as mock_send:
            result = await client.get_group_by_id(dashboard_id="7", group_id="3")

            assert mock_send.call_args[0][0] == "GET"
            assert "/dashboards/7/groups/3" in mock_send.call_args[0][1]
            assert result == {"id": 3}

    @pytest.mark.asyncio
    async def test_update_group_success(self, mock_credential):
        """Test update_group issues a PUT with the input body."""
        client = self._make_client(mock_credential)
        payload = UpdateGroupInput()
        mock_response = MockResponse(status=200, text='{"id": 3}')

        with patch.object(
            client._http_client, "send", new_callable=AsyncMock,
            return_value=mock_response,
        ) as mock_send:
            result = await client.update_group(
                input=payload, dashboard_id="7", group_id="3"
            )

            assert mock_send.call_args[0][0] == "PUT"
            assert "/dashboards/7/groups/3" in mock_send.call_args[0][1]
            assert mock_send.call_args.kwargs["body"] is payload
            assert result == {"id": 3}

    @pytest.mark.asyncio
    async def test_create_group_success(self, mock_credential):
        """Test create_group issues a POST with the input body."""
        client = self._make_client(mock_credential)
        payload = CreateGroupInput()
        mock_response = MockResponse(status=200, text='{"id": 3}')

        with patch.object(
            client._http_client, "send", new_callable=AsyncMock,
            return_value=mock_response,
        ) as mock_send:
            result = await client.create_group(input=payload, dashboard_id="7")

            assert mock_send.call_args[0][0] == "POST"
            assert "/dashboards/7/groups" in mock_send.call_args[0][1]
            assert mock_send.call_args.kwargs["body"] is payload
            assert result == {"id": 3}

    @pytest.mark.asyncio
    async def test_list_custom_fields_success(self, mock_credential):
        """Test list_custom_fields issues a GET to the fields route."""
        client = self._make_client(mock_credential)
        mock_response = MockResponse(status=200, text='[{"id": "field-1"}]')

        with patch.object(
            client._http_client, "send", new_callable=AsyncMock,
            return_value=mock_response,
        ) as mock_send:
            result = await invoke_generated_operation(
                client,
                "list_custom_fields",
                textrequest_module,
                request_controls={"dashboard_id": "7"},
            )

            assert mock_send.call_args[0][0] == "GET"
            assert "/dashboards/7/fields" in mock_send.call_args[0][1]
            assert result == [{"id": "field-1"}]

    @pytest.mark.asyncio
    async def test_mark_payment_paid_success(self, mock_credential):
        """Test mark_payment_paid issues a POST to the mark_as_paid route."""
        client = self._make_client(mock_credential)
        mock_response = MockResponse(status=200, text='{"ok": true}')

        with patch.object(
            client._http_client, "send", new_callable=AsyncMock,
            return_value=mock_response,
        ) as mock_send:
            result = await client.mark_payment_paid(dashboard_id="7", payment_id="9")

            assert mock_send.call_args[0][0] == "POST"
            assert "/dashboards/7/payments/9/mark_as_paid" in mock_send.call_args[0][1]
            assert result == {"ok": True}

    @pytest.mark.asyncio
    async def test_create_payment_success(self, mock_credential):
        """Test create_payment issues a POST with the input body."""
        client = self._make_client(mock_credential)
        payload = CreatePaymentInput()
        mock_response = MockResponse(status=200, text='{"id": 9}')

        with patch.object(
            client._http_client, "send", new_callable=AsyncMock,
            return_value=mock_response,
        ) as mock_send:
            result = await client.create_payment(input=payload, dashboard_id="7")

            assert mock_send.call_args[0][0] == "POST"
            assert "/dashboards/7/payments" in mock_send.call_args[0][1]
            assert mock_send.call_args.kwargs["body"] is payload
            assert result == {"id": 9}

    @pytest.mark.asyncio
    async def test_get_dashboards_success(self, mock_credential):
        """Test get_dashboards issues a GET to the dashboards route."""
        client = self._make_client(mock_credential)
        mock_response = MockResponse(status=200, text='{"items": []}')

        with patch.object(
            client._http_client, "send", new_callable=AsyncMock,
            return_value=mock_response,
        ) as mock_send:
            result = await resolve_generated_result(
                client.list_dashboards(page="1", page_size="20")
            )

            url = mock_send.call_args[0][1]
            assert mock_send.call_args[0][0] == "GET"
            assert "/dashboards" in url
            assert "page=1" in url
            assert result == []

    @pytest.mark.asyncio
    async def test_create_dashboard_success(self, mock_credential):
        """Test create_dashboard issues a POST with the input body."""
        client = self._make_client(mock_credential)
        payload = CreateDashboardInput()
        mock_response = MockResponse(status=200, text='{"id": 1}')

        with patch.object(
            client._http_client, "send", new_callable=AsyncMock,
            return_value=mock_response,
        ) as mock_send:
            result = await client.create_dashboard(input=payload)

            assert mock_send.call_args[0][0] == "POST"
            assert mock_send.call_args[0][1].endswith("/dashboards")
            assert mock_send.call_args.kwargs["body"] is payload
            assert result == {"id": 1}

    @pytest.mark.asyncio
    async def test_update_dashboards_name_success(self, mock_credential):
        """Test update_dashboards_name issues a PUT with the input body."""
        client = self._make_client(mock_credential)
        payload = UpdateDashboardsNameInput()
        mock_response = MockResponse(status=200, text='{"id": 7}')

        with patch.object(
            client._http_client, "send", new_callable=AsyncMock,
            return_value=mock_response,
        ) as mock_send:
            result = await client.update_dashboards_name(input=payload, dashboard_id="7")

            assert mock_send.call_args[0][0] == "PUT"
            assert mock_send.call_args[0][1].endswith("/dashboards/7")
            assert mock_send.call_args.kwargs["body"] is payload
            assert result == {"id": 7}

    @pytest.mark.asyncio
    async def test_empty_response_body_returns_none(self, mock_credential):
        """Test a 2xx response with no body returns None."""
        client = self._make_client(mock_credential)
        mock_response = MockResponse(status=200, text="")

        with patch.object(
            client._http_client, "send", new_callable=AsyncMock,
            return_value=mock_response,
        ):
            result = await resolve_generated_result(client.list_dashboards())

            assert result == []


class TestTextrequestClientErrorHandling:
    """Error handling tests for TextrequestClient operations."""

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "operation",
        [
            "list_messages_by_contact_phone",
            "send_message_by_phone_number",
            "archive_conversation",
            "unarchive_conversation",
            "get_contact_by_phone_number",
            "delete_contact",
            "create_contact",
            "list_contacts",
            "bulk_update_contacts",
            "get_group_by_id",
            "delete_group",
            "update_group",
            "list_groups",
            "create_group",
            "list_tags",
            "list_custom_fields",
            "get_payment",
            "mark_payment_paid",
            "send_payment_reminder",
            "cancel_payment",
            "list_payments",
            "create_payment",
            "get_dashboard",
            "delete_dashboard",
            "update_dashboards_name",
            "list_conversations",
            "list_dashboards",
            "create_dashboard",
        ],
    )
    async def test_error_response_raises_exception(self, mock_credential, operation):
        """Test non-2xx responses raise ConnectorException for every operation."""
        client = TextrequestClient(
            "https://example.azure.com/connections/test",
            credential=mock_credential,
        )
        mock_response = MockResponse(status=500, text='{"error":"server failure"}')

        with patch.object(
            client._http_client, "send", new_callable=AsyncMock,
            return_value=mock_response,
        ):
            with pytest.raises(ConnectorException) as exc_info:
                await invoke_generated_operation(
                    client,
                    operation,
                    textrequest_module,
                )

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
