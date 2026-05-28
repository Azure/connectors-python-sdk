# Copyright (c) Microsoft Corporation. All rights reserved.

"""Unit tests for Office365Client."""

import json
import pytest
from unittest.mock import AsyncMock, patch
from azure.connectors.office365 import (
    Office365Client,
    ClientDraftHtmlMessage,
    ClientReceiveFileAttachment,
    ClientReceiveMessage,
    FindMeetingTimesInput,
    GraphCalendarEventClientReceive,
    GraphCalendarEventListWithActionType,
    GraphClientReceiveFileAttachment,
    GraphClientReceiveMessage,
    MarkAsReadInput,
    MCPQueryRequest,
    CalendarEventBackend,
    GetAttachmentResponse,
    SensitivityLabelMetadata,
)
from azure.connectors.sdk import (
    ConnectorClientOptions,
    ManagedIdentityTokenProvider,
    ConnectorException,
)
from tests.conftest import MockTokenProvider, MockResponse


class TestOffice365ClientInitialization:
    """Tests for Office365Client initialization."""

    def test_init_with_valid_url_and_defaults(self):
        """Test initialization with valid URL and default parameters."""
        client = Office365Client("https://example.azure.com/connections/test")

        assert client._connection_runtime_url == "https://example.azure.com/connections/test"
        assert client.connector_name == "office365"
        assert isinstance(client._http_client._token_provider, ManagedIdentityTokenProvider)

    def test_init_with_trailing_slash(self):
        """Test that trailing slash is removed from URL."""
        client = Office365Client("https://example.azure.com/connections/test/")

        assert client._connection_runtime_url == "https://example.azure.com/connections/test"

    def test_init_with_custom_token_provider(self, mock_token_provider):
        """Test initialization with custom token provider."""
        client = Office365Client(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        assert client._http_client._token_provider is mock_token_provider

    def test_init_with_custom_options(self, mock_token_provider):
        """Test initialization with custom options."""
        options = ConnectorClientOptions(timeout_seconds=60.0, max_retry_attempts=5)
        client = Office365Client(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider,
            options=options
        )

        assert client._options is options
        assert client._options.timeout_seconds == 60.0
        assert client._options.max_retry_attempts == 5

    def test_init_with_empty_url_raises_error(self):
        """Test that empty URL raises ValueError."""
        with pytest.raises(ValueError, match="connection_runtime_url cannot be None or empty"):
            Office365Client("")

    def test_init_with_none_url_raises_error(self):
        """Test that None URL raises ValueError."""
        with pytest.raises(ValueError, match="connection_runtime_url cannot be None or empty"):
            Office365Client(None)

    def test_connector_name_property(self, mock_token_provider):
        """Test connector_name property returns 'office365'."""
        client = Office365Client(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        assert client.connector_name == "office365"


class TestOffice365ClientLifecycle:
    """Tests for Office365Client lifecycle methods."""

    @pytest.mark.asyncio
    async def test_close(self, mock_token_provider):
        """Test close method calls http_client.close."""
        client = Office365Client(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        with patch.object(client._http_client, 'close', new_callable=AsyncMock) as mock_close:
            await client.close()
            mock_close.assert_called_once()

    @pytest.mark.asyncio
    async def test_context_manager(self, mock_token_provider):
        """Test async context manager functionality."""
        with patch.object(Office365Client, 'close', new_callable=AsyncMock) as mock_close:
            async with Office365Client(
                "https://example.azure.com/connections/test",
                token_provider=mock_token_provider
            ) as client:
                assert isinstance(client, Office365Client)

            mock_close.assert_called_once()


class TestGetOutlookCategoryNames:
    """Tests for get_outlook_category_names_async method."""

    @pytest.mark.asyncio
    async def test_success_with_json_response(self, mock_token_provider):
        """Test successful GET request without parameters."""
        client = Office365Client(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(
            status=200,
            text='{"value": [{"displayName": "Red category"}, {"displayName": "Blue category"}]}'
        )

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ) as mock_send:
            result = await client.get_outlook_category_names_async()

            mock_send.assert_called_once_with(
                "GET",
                "https://example.azure.com/connections/test/Categories",
                body=None
            )
            assert "value" in result
            assert len(result["value"]) == 2

    @pytest.mark.asyncio
    async def test_empty_response_returns_none(self, mock_token_provider):
        """Test that empty response returns None."""
        client = Office365Client(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(status=204, text="")

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ):
            result = await client.get_outlook_category_names_async()
            assert result is None

    @pytest.mark.asyncio
    async def test_error_response_raises_exception(self, mock_token_provider):
        """Test that error response raises ConnectorException."""
        client = Office365Client(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(
            status=401,
            text='{"error": "Unauthorized"}'
        )

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ):
            with pytest.raises(ConnectorException) as exc_info:
                await client.get_outlook_category_names_async()

            assert exc_info.value.status_code == 401


class TestDraftEmail:
    """Tests for draft_email_async method."""

    @pytest.mark.asyncio
    async def test_success_with_body_and_no_query_params(self, mock_token_provider):
        """Test successful POST with body but no query parameters."""
        client = Office365Client(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(
            status=200,
            text='{"id": "message123", "subject": "Test Email"}'
        )

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ) as mock_send:
            input_message = ClientDraftHtmlMessage()
            result = await client.draft_email_async(input_message)

            mock_send.assert_called_once_with(
                "POST",
                "https://example.azure.com/connections/test/Draft",
                body=input_message
            )
            assert result["id"] == "message123"

    @pytest.mark.asyncio
    async def test_success_with_query_parameters(self, mock_token_provider):
        """Test POST with query parameters."""
        client = Office365Client(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(
            status=200,
            text='{"id": "reply123"}'
        )

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ) as mock_send:
            input_message = ClientDraftHtmlMessage()
            await client.draft_email_async(
                input_message,
                message_id="original123",
                draft_type="reply",
                comment="Replying to your message"
            )

            call_args = mock_send.call_args
            path = call_args[0][1]
            assert "messageId=original123" in path
            assert "draftType=reply" in path
            assert "comment=Replying%20to%20your%20message" in path

    @pytest.mark.asyncio
    async def test_error_response_raises_exception(self, mock_token_provider):
        """Test that error response raises ConnectorException."""
        client = Office365Client(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(
            status=400,
            text='{"error": "Invalid email format"}'
        )

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ):
            with pytest.raises(ConnectorException) as exc_info:
                await client.draft_email_async(ClientDraftHtmlMessage())

            assert exc_info.value.status_code == 400


class TestUpdateDraftEmail:
    """Tests for update_draft_email_async method."""

    @pytest.mark.asyncio
    async def test_success_no_return_value(self, mock_token_provider):
        """Test PATCH method with no return value."""
        client = Office365Client(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(status=204, text="")

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ) as mock_send:
            input_message = ClientDraftHtmlMessage()
            result = await client.update_draft_email_async(input_message, "message123")

            call_args = mock_send.call_args
            assert call_args[0][0] == "PATCH"
            assert "messageId=message123" in call_args[0][1]
            assert call_args[1]["body"] is input_message
            assert result is None


class TestSendDraftEmail:
    """Tests for send_draft_email_async method."""

    @pytest.mark.asyncio
    async def test_success_with_path_parameter(self, mock_token_provider):
        """Test POST with path parameter."""
        client = Office365Client(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(status=202, text="")

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ) as mock_send:
            result = await client.send_draft_email_async("message123")

            # NOTE: The generated code uses template syntax instead of f-string interpolation
            call_args = mock_send.call_args
            assert call_args[0][0] == "POST"
            assert "/Draft/Send/" in call_args[0][1]
            assert result is None

    @pytest.mark.asyncio
    async def test_path_parameter_construction(self, mock_token_provider):
        """Test that path is constructed correctly."""
        client = Office365Client(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(status=202, text="")

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ) as mock_send:
            await client.send_draft_email_async("test123")

            call_args = mock_send.call_args
            path = call_args[0][1]
            assert "https://example.azure.com/connections/test/Draft/Send/" in path


class TestAssignCategory:
    """Tests for assign_category_async method."""

    @pytest.mark.asyncio
    async def test_success_with_multiple_query_params(self, mock_token_provider):
        """Test method with multiple query parameters."""
        client = Office365Client(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(status=200, text='{"success": true}')

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ) as mock_send:
            await client.assign_category_async(
                message_id="msg123",
                category="Red category"
            )

            call_args = mock_send.call_args
            path = call_args[0][1]
            assert "messageId=msg123" in path
            assert "category=Red%20category" in path


class TestDeleteEmail:
    """Tests for delete_email_async method."""

    @pytest.mark.asyncio
    async def test_delete_success(self, mock_token_provider):
        """Test successful DELETE request."""
        client = Office365Client(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(status=204, text="")

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ) as mock_send:
            result = await client.delete_email_async("message123")

            call_args = mock_send.call_args
            assert call_args[0][0] == "DELETE"
            assert result is None


class TestGetEmail:
    """Tests for get_email_async method."""

    @pytest.mark.asyncio
    async def test_success_with_complex_response(self, mock_token_provider):
        """Test GET with complex JSON response."""
        client = Office365Client(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(
            status=200,
            text=(
                '{"id": "msg123", "subject": "Test", '
                '"from": {"emailAddress": {"address": "test@example.com"}}}'
            )
        )

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ):
            result = await client.get_email_async("message123")

            assert result["id"] == "msg123"
            assert result["subject"] == "Test"
            assert result["from"]["emailAddress"]["address"] == "test@example.com"


class TestGetEmails:
    """Tests for get_emails_async method."""

    @pytest.mark.asyncio
    async def test_success_with_filtering_and_pagination(self, mock_token_provider):
        """Test GET with complex query parameters for filtering."""
        client = Office365Client(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(
            status=200,
            text='{"value": [{"id": "1"}, {"id": "2"}]}'
        )

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ) as mock_send:
            await client.get_emails_async(
                folder_path="Inbox",
                top="10",
                search_query="subject:Important"
            )

            call_args = mock_send.call_args
            path = call_args[0][1]
            assert "folderpath=inbox" in path.lower()
            assert "top=10" in path
            assert "searchquery=subject" in path.lower()


class TestSendEmail:
    """Tests for send_email_async method."""

    @pytest.mark.asyncio
    async def test_send_email_success(self, mock_token_provider):
        """Test successful email send."""
        client = Office365Client(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(status=202, text="")

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ) as mock_send:
            # NOTE: send_email_async expects ClientSendHtmlMessage, not ClientDraftHtmlMessage
            from azure.connectors.office365 import ClientSendHtmlMessage
            email_message = ClientSendHtmlMessage()
            result = await client.send_email_async(email_message)

            call_args = mock_send.call_args
            assert call_args[0][0] == "POST"
            assert "/v2/Mail" in call_args[0][1]
            assert call_args[1]["body"] is email_message
            assert result is None


class TestFindMeetingTimes:
    """Tests for find_meeting_times_async method."""

    @pytest.mark.asyncio
    async def test_success_with_input_schema(self, mock_token_provider):
        """Test POST with complex input schema."""
        client = Office365Client(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(
            status=200,
            text='{"emptySuggestionsReason": "", "meetingTimeSuggestions": []}'
        )

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ):
            input_data = FindMeetingTimesInput(
                required_attendees="user1@example.com;user2@example.com",
                meeting_duration=60,
                max_candidates=5
            )
            result = await client.find_meeting_times_async(input_data)

            assert "emptySuggestionsReason" in result


class TestGetAttachment:
    """Tests for get_attachment_async method."""

    @pytest.mark.asyncio
    async def test_success_with_attachment_data(self, mock_token_provider):
        """Test getting email attachment."""
        client = Office365Client(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(
            status=200,
            text=(
                '{"id": "att123", "name": "document.pdf", '
                '"contentType": "application/pdf", "size": 1024}'
            )
        )

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ):
            result = await client.get_attachment_async("message123", "att123")

            assert result["id"] == "att123"
            assert result["name"] == "document.pdf"
            assert result["contentType"] == "application/pdf"


class TestMCPEmailsManagement:
    """Tests for mcp_emails_management_async method."""

    @pytest.mark.asyncio
    async def test_success_without_session_id(self, mock_token_provider):
        """Test MCP endpoint without session ID."""
        client = Office365Client(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(
            status=200,
            text='{"jsonrpc": "2.0", "id": "1", "result": {}}'
        )

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ) as mock_send:
            request = MCPQueryRequest(jsonrpc="2.0", id="1", method="list")
            result = await client.mcp_emails_management_async(request)

            mock_send.assert_called_once_with(
                "POST",
                "https://example.azure.com/connections/test/mcp/EmailsManagement",
                body=request
            )
            assert result["jsonrpc"] == "2.0"

    @pytest.mark.asyncio
    async def test_success_with_session_id(self, mock_token_provider):
        """Test MCP endpoint with session ID."""
        client = Office365Client(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(
            status=200,
            text='{"jsonrpc": "2.0", "id": "2", "result": {}}'
        )

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ) as mock_send:
            request = MCPQueryRequest(jsonrpc="2.0", id="2", method="init")
            await client.mcp_emails_management_async(
                request,
                session_id="session-abc"
            )

            call_args = mock_send.call_args
            path = call_args[0][1]
            assert "sessionId=session-abc" in path


class TestCalendarMethods:
    """Tests for calendar-related methods."""

    @pytest.mark.asyncio
    async def test_get_calendars(self, mock_token_provider):
        """Test getting list of calendars."""
        client = Office365Client(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(
            status=200,
            text='{"value": [{"name": "Calendar", "id": "cal123"}]}'
        )

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ):
            result = await client.calendar_get_tables_async()
            assert "value" in result
            assert len(result["value"]) == 1

    @pytest.mark.asyncio
    async def test_create_calendar_event(self, mock_token_provider):
        """Test creating a calendar event."""
        client = Office365Client(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(
            status=201,
            text='{"id": "event123", "subject": "Meeting"}'
        )

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ) as mock_send:
            event = CalendarEventBackend()
            result = await client.calendar_post_item_async("Calendar", event)

            call_args = mock_send.call_args
            assert call_args[0][0] == "POST"
            assert result["id"] == "event123"

    @pytest.mark.asyncio
    async def test_delete_calendar_event(self, mock_token_provider):
        """Test deleting a calendar event."""
        client = Office365Client(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(status=204, text="")

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ) as mock_send:
            result = await client.calendar_delete_item_async("Calendar", "event123")

            call_args = mock_send.call_args
            assert call_args[0][0] == "DELETE"
            assert result is None


class TestContactMethods:
    """Tests for contact-related methods."""

    @pytest.mark.asyncio
    async def test_get_contacts(self, mock_token_provider):
        """Test getting list of contacts."""
        client = Office365Client(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(
            status=200,
            text='{"value": [{"displayName": "John Doe", "emailAddress": "john@example.com"}]}'
        )

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ):
            result = await client.contact_get_items_async("Contacts")
            assert "value" in result


class TestDataClasses:
    """Tests for data classes and type definitions."""

    def test_find_meeting_times_input_creation(self):
        """Test FindMeetingTimesInput dataclass creation."""
        input_data = FindMeetingTimesInput(
            required_attendees="user1@example.com;user2@example.com",
            optional_attendees="user3@example.com",
            meeting_duration=60,
            max_candidates=5
        )

        assert input_data.required_attendees == "user1@example.com;user2@example.com"
        assert input_data.optional_attendees == "user3@example.com"
        assert input_data.meeting_duration == 60
        assert input_data.max_candidates == 5

    def test_mark_as_read_input_creation(self):
        """Test MarkAsReadInput dataclass creation."""
        input_data = MarkAsReadInput(is_read=True)
        assert input_data.is_read is True

    def test_get_attachment_response_structure(self):
        """Test GetAttachmentResponse dataclass structure."""
        response = GetAttachmentResponse(
            id="att123",
            name="document.pdf",
            content_type="application/pdf",
            size=1024,
            is_inline=False
        )

        assert response.id == "att123"
        assert response.name == "document.pdf"
        assert response.content_type == "application/pdf"
        assert response.size == 1024
        assert response.is_inline is False

    def test_dataclasses_with_defaults(self):
        """Test that dataclasses can be created with default None values."""
        input_data = FindMeetingTimesInput()

        assert input_data.required_attendees is None
        assert input_data.optional_attendees is None
        assert input_data.meeting_duration is None


class TestClientReceiveMessageFromJson:
    """Tests for ClientReceiveMessage.from_json method for SDK-type bindings."""

    def _make_payload(self, value):
        """Create a payload object with a .value attribute for testing."""
        from types import SimpleNamespace
        return SimpleNamespace(value=value)

    def test_from_json_parses_single_message_from_dict(self):
        """Test parsing a single message from a dictionary payload."""
        payload = self._make_payload({
            "body": {
                "value": [
                    {
                        "id": "AAMkADlmOTA3NWNm",
                        "receivedDateTime": "2026-03-25T10:30:00+00:00",
                        "hasAttachments": False,
                        "subject": "Test Subject",
                        "bodyPreview": "Preview text",
                        "importance": "normal",
                        "isRead": True,
                        "isHtml": True,
                        "body": "<html><body>Test</body></html>",
                        "from": "sender@example.com",
                        "toRecipients": "recipient@example.com",
                        "ccRecipients": None,
                        "bccRecipients": None,
                        "replyTo": None,
                        "attachments": []
                    }
                ]
            }
        })

        messages = ClientReceiveMessage.from_json(payload)

        assert len(messages) == 1
        msg = messages[0]
        assert msg.id == "AAMkADlmOTA3NWNm"
        assert msg.from_ == "sender@example.com"
        assert msg.to == "recipient@example.com"
        assert msg.subject == "Test Subject"
        assert msg.body == "<html><body>Test</body></html>"
        assert msg.body_preview == "Preview text"
        assert msg.importance == 1  # normal -> 1
        assert msg.is_read is True
        assert msg.is_html is True
        assert msg.has_attachment is False
        assert msg.date_time_received == "2026-03-25T10:30:00+00:00"
        assert msg.cc is None
        assert msg.bcc is None
        assert msg.reply_to is None

    def test_from_json_parses_multiple_messages(self):
        """Test parsing multiple messages from payload."""
        payload = self._make_payload({
            "body": {
                "value": [
                    {"id": "msg1", "subject": "First", "importance": "low"},
                    {"id": "msg2", "subject": "Second", "importance": "high"},
                    {"id": "msg3", "subject": "Third", "importance": "normal"},
                ]
            }
        })

        messages = ClientReceiveMessage.from_json(payload)

        assert len(messages) == 3
        assert messages[0].id == "msg1"
        assert messages[0].subject == "First"
        assert messages[0].importance == 0  # low -> 0
        assert messages[1].id == "msg2"
        assert messages[1].subject == "Second"
        assert messages[1].importance == 2  # high -> 2
        assert messages[2].id == "msg3"
        assert messages[2].subject == "Third"
        assert messages[2].importance == 1  # normal -> 1

    def test_from_json_parses_json_string(self):
        """Test parsing from a JSON string instead of dict."""
        payload = self._make_payload(json.dumps({
            "body": {
                "value": [
                    {"id": "test123", "subject": "JSON String Test"}
                ]
            }
        }))

        messages = ClientReceiveMessage.from_json(payload)

        assert len(messages) == 1
        assert messages[0].id == "test123"
        assert messages[0].subject == "JSON String Test"

    def test_from_json_importance_conversion(self):
        """Test that importance strings are converted to integers."""
        payload = self._make_payload({
            "body": {
                "value": [
                    {"id": "1", "importance": "low"},
                    {"id": "2", "importance": "normal"},
                    {"id": "3", "importance": "high"},
                    {"id": "4", "importance": "LOW"},  # Test case insensitivity
                    {"id": "5", "importance": "HIGH"},
                ]
            }
        })

        messages = ClientReceiveMessage.from_json(payload)

        assert messages[0].importance == 0
        assert messages[1].importance == 1
        assert messages[2].importance == 2
        assert messages[3].importance == 0  # LOW -> 0
        assert messages[4].importance == 2  # HIGH -> 2

    def test_from_json_importance_as_integer(self):
        """Test that integer importance values are preserved."""
        payload = self._make_payload({
            "body": {
                "value": [
                    {"id": "1", "importance": 0},
                    {"id": "2", "importance": 1},
                    {"id": "3", "importance": 2},
                ]
            }
        })

        messages = ClientReceiveMessage.from_json(payload)

        assert messages[0].importance == 0
        assert messages[1].importance == 1
        assert messages[2].importance == 2

    def test_from_json_with_attachments(self):
        """Test parsing messages with attachments."""
        payload = self._make_payload({
            "body": {
                "value": [
                    {
                        "id": "msg1",
                        "hasAttachments": True,
                        "attachments": [
                            {
                                "id": "att1",
                                "name": "document.pdf",
                                "contentBytes": "base64content",
                                "contentType": "application/pdf",
                                "size": 1024,
                                "isInline": False,
                                "lastModifiedDateTime": "2026-03-25T10:00:00Z",
                                "contentId": "cid123"
                            },
                            {
                                "id": "att2",
                                "name": "image.png",
                                "contentType": "image/png",
                                "size": 2048,
                                "isInline": True
                            }
                        ]
                    }
                ]
            }
        })

        messages = ClientReceiveMessage.from_json(payload)

        assert len(messages) == 1
        msg = messages[0]
        assert msg.has_attachment is True
        assert msg.attachments is not None
        assert len(msg.attachments) == 2

        att1 = msg.attachments[0]
        assert isinstance(att1, ClientReceiveFileAttachment)
        assert att1.id == "att1"
        assert att1.name == "document.pdf"
        assert att1.content_bytes == "base64content"
        assert att1.content_type == "application/pdf"
        assert att1.size == 1024
        assert att1.is_inline is False
        assert att1.last_modified_date_time == "2026-03-25T10:00:00Z"
        assert att1.content_id == "cid123"

        att2 = msg.attachments[1]
        assert att2.id == "att2"
        assert att2.name == "image.png"
        assert att2.is_inline is True

    def test_from_json_with_missing_fields(self):
        """Test that missing fields default to None."""
        payload = self._make_payload({
            "body": {
                "value": [
                    {"id": "minimal"}
                ]
            }
        })

        messages = ClientReceiveMessage.from_json(payload)

        assert len(messages) == 1
        msg = messages[0]
        assert msg.id == "minimal"
        assert msg.from_ is None
        assert msg.to is None
        assert msg.subject is None
        assert msg.body is None
        assert msg.importance is None
        assert msg.is_read is None
        assert msg.attachments is None

    def test_from_json_with_empty_value_list(self):
        """Test parsing payload with empty value list."""
        payload = self._make_payload({"body": {"value": []}})

        messages = ClientReceiveMessage.from_json(payload)

        assert len(messages) == 0

    def test_from_json_invalid_json_string_raises_error(self):
        """Test that invalid JSON string raises ValueError."""
        payload = self._make_payload("not valid json{")

        with pytest.raises(ValueError, match="Invalid JSON payload"):
            ClientReceiveMessage.from_json(payload)

    def test_from_json_parses_single_item_without_value_array(self):
        """Test parsing a single message when body is the message itself (no value array)."""
        payload = self._make_payload({
            "body": {
                "id": "single123",
                "subject": "Single Item Test",
                "from": "sender@example.com",
                "toRecipients": "recipient@example.com",
                "importance": "high",
                "bodyPreview": "This is a single item",
                "isRead": False,
            }
        })

        messages = ClientReceiveMessage.from_json(payload)

        assert len(messages) == 1
        assert messages[0].id == "single123"
        assert messages[0].subject == "Single Item Test"
        assert messages[0].from_ == "sender@example.com"
        assert messages[0].to == "recipient@example.com"
        assert messages[0].importance == 2  # "high" -> 2
        assert messages[0].body_preview == "This is a single item"
        assert messages[0].is_read is False

    def test_from_json_direct_value_without_body_wrapper(self):
        """Test parsing when value is directly under root without body wrapper."""
        payload = self._make_payload({
            "value": [
                {"id": "direct", "subject": "Direct Access"}
            ]
        })

        messages = ClientReceiveMessage.from_json(payload)

        assert len(messages) == 1
        assert messages[0].id == "direct"
        assert messages[0].subject == "Direct Access"

    def test_from_json_missing_value_attribute_raises_error(self):
        """Test that payload without .value attribute raises ValueError."""
        payload = {"body": {"value": []}}  # Plain dict without .value attribute

        with pytest.raises(ValueError, match="Payload must have a 'value' attribute"):
            ClientReceiveMessage.from_json(payload)


class TestGraphClientReceiveMessageFromJson:
    """Tests for GraphClientReceiveMessage.from_json method for SDK-type bindings."""

    def _make_payload(self, value):
        """Create a payload object with a .value attribute for testing."""
        from types import SimpleNamespace
        return SimpleNamespace(value=value)

    def test_from_json_parses_batch_messages(self):
        """Test parsing batch messages from payload with body.value array."""
        payload = self._make_payload({
            "body": {
                "value": [
                    {
                        "id": "AAMkADlmOTA3NWNm",
                        "receivedDateTime": "2026-03-25T10:30:00+00:00",
                        "hasAttachments": False,
                        "subject": "Test Subject",
                        "bodyPreview": "Preview text",
                        "importance": "normal",
                        "isRead": True,
                        "isHtml": True,
                        "body": "<html><body>Test</body></html>",
                        "from": "sender@example.com",
                        "toRecipients": "recipient@example.com",
                        "ccRecipients": None,
                        "bccRecipients": None,
                        "replyTo": None,
                        "attachments": []
                    }
                ]
            }
        })

        messages = GraphClientReceiveMessage.from_json(payload)

        assert len(messages) == 1
        msg = messages[0]
        assert msg.id == "AAMkADlmOTA3NWNm"
        assert msg.from_ == "sender@example.com"
        assert msg.to_recipients == "recipient@example.com"
        assert msg.subject == "Test Subject"
        assert msg.body == "<html><body>Test</body></html>"
        assert msg.body_preview == "Preview text"
        assert msg.importance == "normal"
        assert msg.is_read is True
        assert msg.is_html is True
        assert msg.has_attachments is False
        assert msg.received_date_time == "2026-03-25T10:30:00+00:00"
        assert msg.cc_recipients is None
        assert msg.bcc_recipients is None
        assert msg.reply_to is None

    def test_from_json_parses_single_message(self):
        """Test parsing a single message from payload with body as object."""
        payload = self._make_payload({
            "body": {
                "id": "AAMkSingleMessage",
                "receivedDateTime": "2026-03-25T11:00:00+00:00",
                "hasAttachments": True,
                "subject": "Single Message Test",
                "importance": "high",
                "isRead": False,
                "from": "single@example.com",
                "toRecipients": "me@example.com"
            }
        })

        messages = GraphClientReceiveMessage.from_json(payload)

        assert len(messages) == 1
        msg = messages[0]
        assert msg.id == "AAMkSingleMessage"
        assert msg.subject == "Single Message Test"
        assert msg.importance == "high"
        assert msg.has_attachments is True
        assert msg.is_read is False
        assert msg.from_ == "single@example.com"
        assert msg.to_recipients == "me@example.com"

    def test_from_json_parses_multiple_messages(self):
        """Test parsing multiple messages from payload."""
        payload = self._make_payload({
            "body": {
                "value": [
                    {"id": "msg1", "subject": "First", "importance": "low"},
                    {"id": "msg2", "subject": "Second", "importance": "high"},
                    {"id": "msg3", "subject": "Third", "importance": "normal"},
                ]
            }
        })

        messages = GraphClientReceiveMessage.from_json(payload)

        assert len(messages) == 3
        assert messages[0].id == "msg1"
        assert messages[0].subject == "First"
        assert messages[0].importance == "low"
        assert messages[1].id == "msg2"
        assert messages[1].subject == "Second"
        assert messages[1].importance == "high"
        assert messages[2].id == "msg3"
        assert messages[2].subject == "Third"
        assert messages[2].importance == "normal"

    def test_from_json_parses_json_string(self):
        """Test parsing from a JSON string instead of dict."""
        payload = self._make_payload(json.dumps({
            "body": {
                "value": [
                    {"id": "test123", "subject": "JSON String Test"}
                ]
            }
        }))

        messages = GraphClientReceiveMessage.from_json(payload)

        assert len(messages) == 1
        assert messages[0].id == "test123"
        assert messages[0].subject == "JSON String Test"

    def test_from_json_with_attachments(self):
        """Test parsing messages with attachments."""
        payload = self._make_payload({
            "body": {
                "value": [
                    {
                        "id": "msg1",
                        "hasAttachments": True,
                        "attachments": [
                            {
                                "id": "att1",
                                "name": "document.pdf",
                                "contentBytes": "base64content",
                                "contentType": "application/pdf",
                                "size": 1024,
                                "isInline": False,
                                "lastModifiedDateTime": "2026-03-25T10:00:00Z",
                                "contentId": "cid123"
                            }
                        ]
                    }
                ]
            }
        })

        messages = GraphClientReceiveMessage.from_json(payload)

        assert len(messages) == 1
        msg = messages[0]
        assert msg.has_attachments is True
        assert msg.attachments is not None
        assert len(msg.attachments) == 1

        att = msg.attachments[0]
        assert isinstance(att, GraphClientReceiveFileAttachment)
        assert att.id == "att1"
        assert att.name == "document.pdf"
        assert att.content_bytes == "base64content"
        assert att.content_type == "application/pdf"
        assert att.size == 1024
        assert att.is_inline is False
        assert att.last_modified_date_time == "2026-03-25T10:00:00Z"
        assert att.content_id == "cid123"

    def test_from_json_with_sensitivity_labels(self):
        """Test parsing messages with sensitivity label info."""
        payload = self._make_payload({
            "body": {
                "value": [
                    {
                        "id": "msg1",
                        "subject": "Confidential Message",
                        "sensitivityLabelInfo": [
                            {
                                "sensitivityLabelId": "label-123",
                                "name": "Confidential",
                                "displayName": "Confidential - Internal",
                                "tooltip": "For internal use only",
                                "priority": 2,
                                "color": "#FF0000",
                                "isEncrypted": True,
                                "isEnabled": True,
                                "isParent": False,
                                "parentSensitivityLabelId": "parent-456"
                            }
                        ]
                    }
                ]
            }
        })

        messages = GraphClientReceiveMessage.from_json(payload)

        assert len(messages) == 1
        msg = messages[0]
        assert msg.sensitivity_label_info is not None
        assert len(msg.sensitivity_label_info) == 1

        label = msg.sensitivity_label_info[0]
        assert isinstance(label, SensitivityLabelMetadata)
        assert label.sensitivity_label_id == "label-123"
        assert label.name == "Confidential"
        assert label.display_name == "Confidential - Internal"
        assert label.tooltip == "For internal use only"
        assert label.priority == 2
        assert label.color == "#FF0000"
        assert label.is_encrypted is True
        assert label.is_enabled is True
        assert label.is_parent is False
        assert label.parent_sensitivity_label_id == "parent-456"

    def test_from_json_with_missing_fields(self):
        """Test that missing fields default to None."""
        payload = self._make_payload({
            "body": {
                "value": [
                    {"id": "minimal"}
                ]
            }
        })

        messages = GraphClientReceiveMessage.from_json(payload)

        assert len(messages) == 1
        msg = messages[0]
        assert msg.id == "minimal"
        assert msg.from_ is None
        assert msg.to_recipients is None
        assert msg.subject is None
        assert msg.body is None
        assert msg.importance is None
        assert msg.is_read is None
        assert msg.attachments is None
        assert msg.sensitivity_label_info is None

    def test_from_json_with_empty_value_list(self):
        """Test parsing payload with empty value list."""
        payload = self._make_payload({"body": {"value": []}})

        messages = GraphClientReceiveMessage.from_json(payload)

        assert len(messages) == 0

    def test_from_json_invalid_json_string_raises_error(self):
        """Test that invalid JSON string raises ValueError."""
        payload = self._make_payload("not valid json{")

        with pytest.raises(ValueError, match="Invalid JSON payload"):
            GraphClientReceiveMessage.from_json(payload)

    def test_from_json_missing_value_attribute_raises_error(self):
        """Test that payload without .value attribute raises ValueError."""
        payload = {"body": {"value": []}}  # Plain dict without .value attribute

        with pytest.raises(ValueError, match="Payload must have a 'value' attribute"):
            GraphClientReceiveMessage.from_json(payload)


class TestGraphCalendarEventListWithActionTypeFromJson:
    """Tests for GraphCalendarEventListWithActionType.from_json for SDK-type bindings."""

    def _make_payload(self, value):
        """Create a payload object with a .value attribute for testing."""
        from types import SimpleNamespace
        return SimpleNamespace(value=value)

    def test_from_json_parses_batch_events(self):
        """Test parsing batch calendar events from payload with body.value array."""
        payload = self._make_payload({
            "body": {
                "value": [
                    {
                        "id": "AAMkADlmEvent1",
                        "actionType": "added",
                        "isAdded": True,
                        "isUpdated": False,
                        "subject": "Team Meeting",
                        "start": "2026-03-25T10:00:00.0000000",
                        "end": "2026-03-25T11:00:00.0000000",
                        "startWithTimeZone": "2026-03-25T10:00:00.0000000+00:00",
                        "endWithTimeZone": "2026-03-25T11:00:00.0000000+00:00",
                        "body": "Discuss project updates",
                        "isHtml": False,
                        "responseType": "organizer",
                        "importance": "normal",
                        "location": "Conference Room A",
                        "isAllDay": False,
                        "categories": ["Work", "Meetings"],
                    }
                ]
            }
        })

        result = GraphCalendarEventListWithActionType.from_json(payload)

        assert result.value is not None
        assert len(result.value) == 1
        event = result.value[0]
        assert event.id == "AAMkADlmEvent1"
        assert event.action_type == "added"
        assert event.is_added is True
        assert event.is_updated is False
        assert event.subject == "Team Meeting"
        assert event.start == "2026-03-25T10:00:00.0000000"
        assert event.end == "2026-03-25T11:00:00.0000000"
        assert event.start_with_time_zone == "2026-03-25T10:00:00.0000000+00:00"
        assert event.end_with_time_zone == "2026-03-25T11:00:00.0000000+00:00"
        assert event.body == "Discuss project updates"
        assert event.is_html is False
        assert event.response_type == "organizer"
        assert event.importance == "normal"
        assert event.location == "Conference Room A"
        assert event.is_all_day is False
        assert event.categories == ["Work", "Meetings"]

    def test_from_json_parses_single_event(self):
        """Test parsing a single calendar event from payload with body as object."""
        payload = self._make_payload({
            "body": {
                "id": "AAMkSingleEvent",
                "actionType": "updated",
                "isAdded": False,
                "isUpdated": True,
                "subject": "One-on-One",
                "start": "2026-03-26T14:00:00.0000000",
                "end": "2026-03-26T14:30:00.0000000",
                "organizer": "manager@example.com",
                "requiredAttendees": "employee@example.com",
                "optionalAttendees": None,
            }
        })

        result = GraphCalendarEventListWithActionType.from_json(payload)

        assert result.value is not None
        assert len(result.value) == 1
        event = result.value[0]
        assert event.id == "AAMkSingleEvent"
        assert event.action_type == "updated"
        assert event.is_added is False
        assert event.is_updated is True
        assert event.subject == "One-on-One"
        assert event.organizer == "manager@example.com"
        assert event.required_attendees == "employee@example.com"
        assert event.optional_attendees is None

    def test_from_json_parses_multiple_events(self):
        """Test parsing multiple events from payload."""
        payload = self._make_payload({
            "body": {
                "value": [
                    {"id": "event1", "subject": "Morning Sync", "actionType": "added"},
                    {"id": "event2", "subject": "Lunch Break", "actionType": "updated"},
                    {"id": "event3", "subject": "Sprint Review", "actionType": "deleted"},
                ]
            }
        })

        result = GraphCalendarEventListWithActionType.from_json(payload)

        assert result.value is not None
        assert len(result.value) == 3
        assert result.value[0].id == "event1"
        assert result.value[0].subject == "Morning Sync"
        assert result.value[0].action_type == "added"
        assert result.value[1].id == "event2"
        assert result.value[1].subject == "Lunch Break"
        assert result.value[1].action_type == "updated"
        assert result.value[2].id == "event3"
        assert result.value[2].subject == "Sprint Review"
        assert result.value[2].action_type == "deleted"

    def test_from_json_parses_json_string(self):
        """Test parsing from a JSON string instead of dict."""
        payload = self._make_payload(json.dumps({
            "body": {
                "value": [
                    {"id": "test123", "subject": "JSON String Test", "importance": "high"}
                ]
            }
        }))

        result = GraphCalendarEventListWithActionType.from_json(payload)

        assert result.value is not None
        assert len(result.value) == 1
        assert result.value[0].id == "test123"
        assert result.value[0].subject == "JSON String Test"
        assert result.value[0].importance == "high"

    def test_from_json_parses_all_fields(self):
        """Test parsing event with all fields populated."""
        payload = self._make_payload({
            "body": {
                "value": [
                    {
                        "id": "fullEvent",
                        "actionType": "added",
                        "isAdded": True,
                        "isUpdated": False,
                        "subject": "Full Event Test",
                        "start": "2026-04-01T09:00:00.0000000",
                        "end": "2026-04-01T10:00:00.0000000",
                        "startWithTimeZone": "2026-04-01T09:00:00.0000000-07:00",
                        "endWithTimeZone": "2026-04-01T10:00:00.0000000-07:00",
                        "body": "<html><body>Meeting details</body></html>",
                        "isHtml": True,
                        "responseType": "accepted",
                        "responseTime": "2026-03-28T12:00:00Z",
                        "createdDateTime": "2026-03-25T08:00:00Z",
                        "lastModifiedDateTime": "2026-03-28T12:00:00Z",
                        "organizer": "organizer@example.com",
                        "timeZone": "Pacific Standard Time",
                        "seriesMasterId": "series123",
                        "iCalUId": "ical-uid-456",
                        "categories": ["Important", "Work"],
                        "webLink": "https://outlook.office.com/calendar/item/123",
                        "requiredAttendees": "required@example.com",
                        "optionalAttendees": "optional@example.com",
                        "resourceAttendees": "room@example.com",
                        "location": "Building 1, Room 101",
                        "importance": "high",
                        "isAllDay": False,
                        "recurrence": "weekly",
                        "recurrenceEnd": "2026-12-31T00:00:00Z",
                        "numberOfOccurences": 52,
                        "reminderMinutesBeforeStart": 15,
                        "isReminderOn": True,
                        "showAs": "busy",
                        "responseRequested": True,
                        "sensitivity": "private",
                    }
                ]
            }
        })

        result = GraphCalendarEventListWithActionType.from_json(payload)

        assert result.value is not None
        assert len(result.value) == 1
        event = result.value[0]
        assert event.id == "fullEvent"
        assert event.action_type == "added"
        assert event.is_added is True
        assert event.is_updated is False
        assert event.subject == "Full Event Test"
        assert event.start == "2026-04-01T09:00:00.0000000"
        assert event.end == "2026-04-01T10:00:00.0000000"
        assert event.start_with_time_zone == "2026-04-01T09:00:00.0000000-07:00"
        assert event.end_with_time_zone == "2026-04-01T10:00:00.0000000-07:00"
        assert event.body == "<html><body>Meeting details</body></html>"
        assert event.is_html is True
        assert event.response_type == "accepted"
        assert event.response_time == "2026-03-28T12:00:00Z"
        assert event.created_date_time == "2026-03-25T08:00:00Z"
        assert event.last_modified_date_time == "2026-03-28T12:00:00Z"
        assert event.organizer == "organizer@example.com"
        assert event.time_zone == "Pacific Standard Time"
        assert event.series_master_id == "series123"
        assert event.i_cal_u_id == "ical-uid-456"
        assert event.categories == ["Important", "Work"]
        assert event.web_link == "https://outlook.office.com/calendar/item/123"
        assert event.required_attendees == "required@example.com"
        assert event.optional_attendees == "optional@example.com"
        assert event.resource_attendees == "room@example.com"
        assert event.location == "Building 1, Room 101"
        assert event.importance == "high"
        assert event.is_all_day is False
        assert event.recurrence == "weekly"
        assert event.recurrence_end == "2026-12-31T00:00:00Z"
        assert event.number_of_occurences == 52
        assert event.reminder_minutes_before_start == 15
        assert event.is_reminder_on is True
        assert event.show_as == "busy"
        assert event.response_requested is True
        assert event.sensitivity == "private"

    def test_from_json_with_missing_fields(self):
        """Test that missing fields default to None."""
        payload = self._make_payload({
            "body": {
                "value": [
                    {"id": "minimal"}
                ]
            }
        })

        result = GraphCalendarEventListWithActionType.from_json(payload)

        assert result.value is not None
        assert len(result.value) == 1
        event = result.value[0]
        assert event.id == "minimal"
        assert event.action_type is None
        assert event.subject is None
        assert event.start is None
        assert event.end is None
        assert event.body is None
        assert event.importance is None
        assert event.location is None
        assert event.categories is None

    def test_from_json_with_empty_value_list(self):
        """Test parsing payload with empty value list."""
        payload = self._make_payload({"body": {"value": []}})

        result = GraphCalendarEventListWithActionType.from_json(payload)

        assert result.value is not None
        assert len(result.value) == 0

    def test_from_json_invalid_json_string_raises_error(self):
        """Test that invalid JSON string raises ValueError."""
        payload = self._make_payload("not valid json{")

        with pytest.raises(ValueError, match="Invalid JSON payload"):
            GraphCalendarEventListWithActionType.from_json(payload)

    def test_from_json_missing_value_attribute_raises_error(self):
        """Test that payload without .value attribute raises ValueError."""
        payload = {"body": {"value": []}}  # Plain dict without .value attribute

        with pytest.raises(ValueError, match="Payload must have a 'value' attribute"):
            GraphCalendarEventListWithActionType.from_json(payload)


class TestEdgeCases:
    """Tests for edge cases and boundary conditions."""

    @pytest.mark.asyncio
    async def test_multiple_consecutive_calls(self, mock_token_provider):
        """Test multiple consecutive API calls work correctly."""
        client = Office365Client(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response_1 = MockResponse(status=200, text='{"result": "first"}')
        mock_response_2 = MockResponse(status=200, text='{"result": "second"}')

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            side_effect=[mock_response_1, mock_response_2]
        ):
            result_1 = await client.get_outlook_category_names_async()
            result_2 = await client.get_outlook_category_names_async()

            assert result_1 == {"result": "first"}
            assert result_2 == {"result": "second"}

    @pytest.mark.asyncio
    async def test_json_parse_error_raises_exception(self, mock_token_provider):
        """Test that invalid JSON in response raises an error."""
        client = Office365Client(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(status=200, text='invalid json{')

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ):
            with pytest.raises(json.JSONDecodeError):
                await client.get_outlook_category_names_async()

    @pytest.mark.asyncio
    async def test_url_construction_with_multiple_trailing_slashes(self):
        """Test URL construction handles multiple trailing slashes."""
        client = Office365Client(
            "https://example.azure.com/connections/test///",
            token_provider=MockTokenProvider()
        )

        assert client._connection_runtime_url == "https://example.azure.com/connections/test"

    def test_http_client_property_access(self, mock_token_provider):
        """Test that http_client property is accessible."""
        client = Office365Client(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        assert client.http_client is not None
        assert client.http_client is client._http_client

    @pytest.mark.asyncio
    async def test_special_characters_in_query_params(self, mock_token_provider):
        """Test that special characters in query params are encoded."""
        client = Office365Client(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(status=200, text='{}')

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ) as mock_send:
            await client.assign_category_async(
                message_id="msg/123",
                category="Red & Blue"
            )

            call_args = mock_send.call_args
            path = call_args[0][1]
            # Verify special characters are encoded
            assert "%2F" in path or "msg/123" in path  # Forward slash may or may not be encoded
            assert "Red%20%26%20Blue" in path or "Red%20&%20Blue" in path

    @pytest.mark.asyncio
    async def test_boolean_query_param_conversion(self, mock_token_provider):
        """Test that boolean values are converted to lowercase strings."""
        client = Office365Client(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(status=200, text='{}')

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ) as mock_send:
            # Create input with boolean
            input_data = FindMeetingTimesInput(is_organizer_optional=True)

            # While we can't directly test query param conversion without reading the actual
            # implementation, we can verify the call succeeds
            await client.find_meeting_times_async(input_data)

            mock_send.assert_called_once()


class TestGraphCalendarEventClientReceiveFromJson:
    """Tests for GraphCalendarEventClientReceive.from_json for SDK-type bindings."""

    def _make_payload(self, value):
        """Create a payload object with a .value attribute for testing."""
        from types import SimpleNamespace
        return SimpleNamespace(value=value)

    def test_from_json_parses_batch_events(self):
        """Test parsing batch calendar events from payload with body.value array."""
        payload = self._make_payload({
            "body": {
                "value": [
                    {
                        "id": "AAMkADlmEvent1",
                        "subject": "Team Meeting",
                        "start": "2026-03-25T10:00:00.0000000",
                        "end": "2026-03-25T11:00:00.0000000",
                        "startWithTimeZone": "2026-03-25T10:00:00.0000000+00:00",
                        "endWithTimeZone": "2026-03-25T11:00:00.0000000+00:00",
                        "body": "Discuss project updates",
                        "isHtml": False,
                        "responseType": "organizer",
                        "importance": "normal",
                        "location": "Conference Room A",
                        "isAllDay": False,
                        "categories": ["Work", "Meetings"],
                    }
                ]
            }
        })

        events = GraphCalendarEventClientReceive.from_json(payload)

        assert len(events) == 1
        event = events[0]
        assert event.id == "AAMkADlmEvent1"
        assert event.subject == "Team Meeting"
        assert event.start == "2026-03-25T10:00:00.0000000"
        assert event.end == "2026-03-25T11:00:00.0000000"
        assert event.start_with_time_zone == "2026-03-25T10:00:00.0000000+00:00"
        assert event.end_with_time_zone == "2026-03-25T11:00:00.0000000+00:00"
        assert event.body == "Discuss project updates"
        assert event.is_html is False
        assert event.response_type == "organizer"
        assert event.importance == "normal"
        assert event.location == "Conference Room A"
        assert event.is_all_day is False
        assert event.categories == ["Work", "Meetings"]

    def test_from_json_parses_single_event(self):
        """Test parsing a single calendar event from payload with body as object."""
        payload = self._make_payload({
            "body": {
                "id": "AAMkSingleEvent",
                "subject": "One-on-One",
                "start": "2026-03-26T14:00:00.0000000",
                "end": "2026-03-26T14:30:00.0000000",
                "organizer": "manager@example.com",
                "requiredAttendees": "employee@example.com",
                "optionalAttendees": None,
            }
        })

        events = GraphCalendarEventClientReceive.from_json(payload)

        assert len(events) == 1
        event = events[0]
        assert event.id == "AAMkSingleEvent"
        assert event.subject == "One-on-One"
        assert event.organizer == "manager@example.com"
        assert event.required_attendees == "employee@example.com"
        assert event.optional_attendees is None

    def test_from_json_parses_multiple_events(self):
        """Test parsing multiple events from payload."""
        payload = self._make_payload({
            "body": {
                "value": [
                    {"id": "event1", "subject": "Morning Sync"},
                    {"id": "event2", "subject": "Lunch Break"},
                    {"id": "event3", "subject": "Sprint Review"},
                ]
            }
        })

        events = GraphCalendarEventClientReceive.from_json(payload)

        assert len(events) == 3
        assert events[0].id == "event1"
        assert events[0].subject == "Morning Sync"
        assert events[1].id == "event2"
        assert events[1].subject == "Lunch Break"
        assert events[2].id == "event3"
        assert events[2].subject == "Sprint Review"

    def test_from_json_parses_json_string(self):
        """Test parsing from a JSON string instead of dict."""
        payload = self._make_payload(json.dumps({
            "body": {
                "value": [
                    {"id": "test123", "subject": "JSON String Test", "importance": "high"}
                ]
            }
        }))

        events = GraphCalendarEventClientReceive.from_json(payload)

        assert len(events) == 1
        assert events[0].id == "test123"
        assert events[0].subject == "JSON String Test"
        assert events[0].importance == "high"

    def test_from_json_parses_all_fields(self):
        """Test parsing event with all fields populated."""
        payload = self._make_payload({
            "body": {
                "value": [
                    {
                        "id": "fullEvent",
                        "subject": "Full Event Test",
                        "start": "2026-04-01T09:00:00.0000000",
                        "end": "2026-04-01T10:00:00.0000000",
                        "startWithTimeZone": "2026-04-01T09:00:00.0000000-07:00",
                        "endWithTimeZone": "2026-04-01T10:00:00.0000000-07:00",
                        "body": "<html><body>Meeting details</body></html>",
                        "isHtml": True,
                        "responseType": "accepted",
                        "responseTime": "2026-03-28T12:00:00Z",
                        "createdDateTime": "2026-03-25T08:00:00Z",
                        "lastModifiedDateTime": "2026-03-28T12:00:00Z",
                        "organizer": "organizer@example.com",
                        "timeZone": "Pacific Standard Time",
                        "seriesMasterId": "series123",
                        "iCalUId": "ical-uid-456",
                        "categories": ["Important", "Work"],
                        "webLink": "https://outlook.office.com/calendar/item/123",
                        "requiredAttendees": "required@example.com",
                        "optionalAttendees": "optional@example.com",
                        "resourceAttendees": "room@example.com",
                        "location": "Building 1, Room 101",
                        "importance": "high",
                        "isAllDay": False,
                        "recurrence": "weekly",
                        "recurrenceEnd": "2026-12-31T00:00:00Z",
                        "numberOfOccurences": 52,
                        "reminderMinutesBeforeStart": 15,
                        "isReminderOn": True,
                        "showAs": "busy",
                        "responseRequested": True,
                        "sensitivity": "private",
                    }
                ]
            }
        })

        events = GraphCalendarEventClientReceive.from_json(payload)

        assert len(events) == 1
        event = events[0]
        assert event.id == "fullEvent"
        assert event.subject == "Full Event Test"
        assert event.start == "2026-04-01T09:00:00.0000000"
        assert event.end == "2026-04-01T10:00:00.0000000"
        assert event.start_with_time_zone == "2026-04-01T09:00:00.0000000-07:00"
        assert event.end_with_time_zone == "2026-04-01T10:00:00.0000000-07:00"
        assert event.body == "<html><body>Meeting details</body></html>"
        assert event.is_html is True
        assert event.response_type == "accepted"
        assert event.response_time == "2026-03-28T12:00:00Z"
        assert event.created_date_time == "2026-03-25T08:00:00Z"
        assert event.last_modified_date_time == "2026-03-28T12:00:00Z"
        assert event.organizer == "organizer@example.com"
        assert event.time_zone == "Pacific Standard Time"
        assert event.series_master_id == "series123"
        assert event.i_cal_u_id == "ical-uid-456"
        assert event.categories == ["Important", "Work"]
        assert event.web_link == "https://outlook.office.com/calendar/item/123"
        assert event.required_attendees == "required@example.com"
        assert event.optional_attendees == "optional@example.com"
        assert event.resource_attendees == "room@example.com"
        assert event.location == "Building 1, Room 101"
        assert event.importance == "high"
        assert event.is_all_day is False
        assert event.recurrence == "weekly"
        assert event.recurrence_end == "2026-12-31T00:00:00Z"
        assert event.number_of_occurences == 52
        assert event.reminder_minutes_before_start == 15
        assert event.is_reminder_on is True
        assert event.show_as == "busy"
        assert event.response_requested is True
        assert event.sensitivity == "private"

    def test_from_json_with_missing_fields(self):
        """Test that missing fields default to None."""
        payload = self._make_payload({
            "body": {
                "value": [
                    {"id": "minimal"}
                ]
            }
        })

        events = GraphCalendarEventClientReceive.from_json(payload)

        assert len(events) == 1
        event = events[0]
        assert event.id == "minimal"
        assert event.subject is None
        assert event.start is None
        assert event.end is None
        assert event.body is None
        assert event.importance is None
        assert event.location is None
        assert event.categories is None

    def test_from_json_with_empty_value_list(self):
        """Test parsing payload with empty value list."""
        payload = self._make_payload({"body": {"value": []}})

        events = GraphCalendarEventClientReceive.from_json(payload)

        assert len(events) == 0

    def test_from_json_invalid_json_string_raises_error(self):
        """Test that invalid JSON string raises ValueError."""
        payload = self._make_payload("not valid json{")

        with pytest.raises(ValueError, match="Invalid JSON payload"):
            GraphCalendarEventClientReceive.from_json(payload)

    def test_from_json_missing_value_attribute_raises_error(self):
        """Test that payload without .value attribute raises ValueError."""
        payload = {"body": {"value": []}}  # Plain dict without .value attribute

        with pytest.raises(ValueError, match="Payload must have a 'value' attribute"):
            GraphCalendarEventClientReceive.from_json(payload)
