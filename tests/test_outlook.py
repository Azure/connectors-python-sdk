# Copyright (c) Microsoft Corporation. All rights reserved.

"""Unit tests for OutlookClient."""

import pytest
from unittest.mock import AsyncMock, patch
from azure.connectors.outlook import (
    OutlookClient,
    ClientReceiveMessage,
    ContactResponse,
    ClientSendAttachment,
    ClientReceiveFileAttachment,
    ClientSendHtmlMessage,
    ReplyHtmlMessage,
    CalendarEventHtmlClient,
    EmailAddress,
    PhysicalAddress,
    Table,
)
from azure.connectors.sdk import (
    ConnectorClientOptions,
    ManagedIdentityTokenProvider,
    ConnectorException,
)
from tests.conftest import MockResponse


class TestOutlookClientInitialization:
    """Tests for OutlookClient initialization."""

    def test_init_with_valid_url_and_defaults(self):
        """Test initialization with valid URL and default parameters."""
        client = OutlookClient("https://example.azure.com/connections/test")

        assert client._connection_runtime_url == "https://example.azure.com/connections/test"
        assert client.connector_name == "outlook"
        assert isinstance(client._http_client._token_provider, ManagedIdentityTokenProvider)

    def test_init_with_trailing_slash(self):
        """Test that trailing slash is removed from URL."""
        client = OutlookClient("https://example.azure.com/connections/test/")

        assert client._connection_runtime_url == "https://example.azure.com/connections/test"

    def test_init_with_custom_token_provider(self, mock_token_provider):
        """Test initialization with custom token provider."""
        client = OutlookClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        assert client._http_client._token_provider is mock_token_provider

    def test_init_with_custom_options(self, mock_token_provider):
        """Test initialization with custom options."""
        options = ConnectorClientOptions(timeout_seconds=60.0, max_retry_attempts=5)
        client = OutlookClient(
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
            OutlookClient("")

    def test_init_with_none_url_raises_error(self):
        """Test that None URL raises ValueError."""
        with pytest.raises(ValueError, match="connection_runtime_url cannot be None or empty"):
            OutlookClient(None)

    def test_connector_name_property(self, mock_token_provider):
        """Test connector_name property returns 'outlook'."""
        client = OutlookClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        assert client.connector_name == "outlook"


class TestOutlookClientLifecycle:
    """Tests for OutlookClient lifecycle methods."""

    @pytest.mark.asyncio
    async def test_close(self, mock_token_provider):
        """Test close method calls http_client.close."""
        client = OutlookClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        with patch.object(client._http_client, 'close', new_callable=AsyncMock) as mock_close:
            await client.close()
            mock_close.assert_called_once()

    @pytest.mark.asyncio
    async def test_context_manager(self, mock_token_provider):
        """Test async context manager functionality."""
        with patch.object(OutlookClient, 'close', new_callable=AsyncMock) as mock_close:
            async with OutlookClient(
                "https://example.azure.com/connections/test",
                token_provider=mock_token_provider
            ) as client:
                assert isinstance(client, OutlookClient)

            mock_close.assert_called_once()


class TestGetEmail:
    """Tests for get_email_async method."""

    @pytest.mark.asyncio
    async def test_success_with_json_response(self, mock_token_provider):
        """Test successful GET request."""
        client = OutlookClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(
            status=200,
            text='{"id": "msg123", "subject": "Hello", "from": "test@example.com"}'
        )

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ) as mock_send:
            result = await client.get_email_async(message_id="msg123")

            mock_send.assert_called_once()
            call_args = mock_send.call_args
            assert call_args[0][0] == "GET"
            assert "/Mail/msg123" in call_args[0][1]
            assert result["subject"] == "Hello"

    @pytest.mark.asyncio
    async def test_with_include_attachments(self, mock_token_provider):
        """Test GET request with includeAttachments parameter."""
        client = OutlookClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(status=200, text='{"id": "msg123"}')

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ) as mock_send:
            await client.get_email_async(message_id="msg123", include_attachments="true")

            call_args = mock_send.call_args
            url = call_args[0][1]
            assert "includeAttachments=true" in url

    @pytest.mark.asyncio
    async def test_error_response_raises_exception(self, mock_token_provider):
        """Test that error response raises ConnectorException."""
        client = OutlookClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(status=404, text='{"error": "Message not found"}')

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ):
            with pytest.raises(ConnectorException) as exc_info:
                await client.get_email_async(message_id="nonexistent")

            assert exc_info.value.status_code == 404


class TestDeleteEmail:
    """Tests for delete_email_async method."""

    @pytest.mark.asyncio
    async def test_success(self, mock_token_provider):
        """Test successful DELETE request."""
        client = OutlookClient(
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
            await client.delete_email_async(message_id="msg123")

            mock_send.assert_called_once()
            call_args = mock_send.call_args
            assert call_args[0][0] == "DELETE"
            assert "/Mail/msg123" in call_args[0][1]


class TestMoveEmail:
    """Tests for move_async method."""

    @pytest.mark.asyncio
    async def test_success_with_json_response(self, mock_token_provider):
        """Test successful POST request."""
        client = OutlookClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(
            status=200,
            text='{"id": "msg123", "parentFolderId": "archive"}'
        )

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ) as mock_send:
            _ = await client.move_async(message_id="msg123", folder_path="Archive")

            mock_send.assert_called_once()
            call_args = mock_send.call_args
            assert call_args[0][0] == "POST"
            assert "/Mail/Move/msg123" in call_args[0][1]
            assert "folderPath=Archive" in call_args[0][1]


class TestFlagEmail:
    """Tests for flag_async method."""

    @pytest.mark.asyncio
    async def test_success(self, mock_token_provider):
        """Test successful POST request."""
        client = OutlookClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(status=200, text="")

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ) as mock_send:
            await client.flag_async(message_id="msg123")

            mock_send.assert_called_once()
            call_args = mock_send.call_args
            assert call_args[0][0] == "POST"
            assert "/Mail/Flag/msg123" in call_args[0][1]


class TestMarkAsRead:
    """Tests for mark_as_read_async method."""

    @pytest.mark.asyncio
    async def test_success(self, mock_token_provider):
        """Test successful POST request."""
        client = OutlookClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(status=200, text="")

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ) as mock_send:
            await client.mark_as_read_async(message_id="msg123")

            mock_send.assert_called_once()
            call_args = mock_send.call_args
            assert call_args[0][0] == "POST"
            assert "/Mail/MarkAsRead/msg123" in call_args[0][1]


class TestGetAttachment:
    """Tests for get_attachment_async method."""

    @pytest.mark.asyncio
    async def test_success(self, mock_token_provider):
        """Test successful GET request returns bytes."""
        client = OutlookClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(status=200, text="binary content here")

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ) as mock_send:
            result = await client.get_attachment_async(
                message_id="msg123",
                attachment_id="att456"
            )

            mock_send.assert_called_once()
            call_args = mock_send.call_args
            assert call_args[0][0] == "GET"
            assert "/Mail/msg123/Attachments/att456" in call_args[0][1]
            assert isinstance(result, bytes)


class TestSendEmail:
    """Tests for send_email_async method."""

    @pytest.mark.asyncio
    async def test_success(self, mock_token_provider):
        """Test successful POST request."""
        client = OutlookClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(status=202, text="")
        email_input = ClientSendHtmlMessage(
            to="recipient@example.com",
            subject="Test Email",
            body="<p>Hello, World!</p>"
        )

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ) as mock_send:
            await client.send_email_async(input=email_input)

            mock_send.assert_called_once()
            call_args = mock_send.call_args
            assert call_args[0][0] == "POST"
            assert "/v2/Mail" in call_args[0][1]


class TestReplyTo:
    """Tests for reply_to_async method."""

    @pytest.mark.asyncio
    async def test_success(self, mock_token_provider):
        """Test successful POST request."""
        client = OutlookClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(status=202, text="")
        reply_input = ReplyHtmlMessage(
            body="<p>Thanks for your email!</p>",
            reply_all=False
        )

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ) as mock_send:
            await client.reply_to_async(input=reply_input, message_id="msg123")

            mock_send.assert_called_once()
            call_args = mock_send.call_args
            assert call_args[0][0] == "POST"
            assert "/v3/Mail/ReplyTo/msg123" in call_args[0][1]


class TestGetEmails:
    """Tests for get_emails_async method."""

    @pytest.mark.asyncio
    async def test_success_with_json_response(self, mock_token_provider):
        """Test successful GET request."""
        client = OutlookClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(
            status=200,
            text='{"value": [{"id": "msg1"}, {"id": "msg2"}]}'
        )

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ) as mock_send:
            result = await client.get_emails_async()

            mock_send.assert_called_once()
            call_args = mock_send.call_args
            assert call_args[0][0] == "GET"
            assert "/v2/Mail" in call_args[0][1]
            assert len(result["value"]) == 2

    @pytest.mark.asyncio
    async def test_with_query_parameters(self, mock_token_provider):
        """Test GET request with various query parameters."""
        client = OutlookClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(status=200, text='{"value": []}')

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ) as mock_send:
            await client.get_emails_async(
                folder_path="Inbox",
                fetch_only_unread="true",
                importance="High",
                top="10"
            )

            call_args = mock_send.call_args
            url = call_args[0][1]
            assert "folderPath=Inbox" in url
            assert "fetchOnlyUnread=true" in url
            assert "importance=High" in url
            assert "top=10" in url


class TestCalendarGetTables:
    """Tests for calendar_get_tables_async method."""

    @pytest.mark.asyncio
    async def test_success_with_json_response(self, mock_token_provider):
        """Test successful GET request."""
        client = OutlookClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(
            status=200,
            text='{"value": [{"name": "Calendar", "displayName": "Calendar"}]}'
        )

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ) as mock_send:
            result = await client.calendar_get_tables_async()

            mock_send.assert_called_once()
            call_args = mock_send.call_args
            assert call_args[0][0] == "GET"
            assert "/datasets/calendars/tables" in call_args[0][1]
            assert len(result["value"]) == 1


class TestCalendarGetItem:
    """Tests for calendar_get_item_async method."""

    @pytest.mark.asyncio
    async def test_success_with_json_response(self, mock_token_provider):
        """Test successful GET request."""
        client = OutlookClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(
            status=200,
            text='{"id": "event123", "subject": "Meeting", "start": "2024-01-15T10:00:00Z"}'
        )

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ) as mock_send:
            result = await client.calendar_get_item_async(
                table="Calendar",
                id="event123"
            )

            mock_send.assert_called_once()
            call_args = mock_send.call_args
            assert call_args[0][0] == "GET"
            assert "/datasets/calendars/v2/tables/Calendar/items/event123" in call_args[0][1]
            assert result["subject"] == "Meeting"


class TestCalendarPostItem:
    """Tests for calendar_post_item_async method."""

    @pytest.mark.asyncio
    async def test_success_with_json_response(self, mock_token_provider):
        """Test successful POST request."""
        client = OutlookClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(
            status=201,
            text='{"id": "new-event", "subject": "New Meeting"}'
        )
        event_input = CalendarEventHtmlClient(
            subject="New Meeting",
            start="2024-01-20T14:00:00Z",
            end="2024-01-20T15:00:00Z"
        )

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ) as mock_send:
            result = await client.calendar_post_item_async(
                input=event_input,
                table="Calendar"
            )

            mock_send.assert_called_once()
            call_args = mock_send.call_args
            assert call_args[0][0] == "POST"
            assert "/datasets/calendars/v3/tables/Calendar/items" in call_args[0][1]
            assert result["subject"] == "New Meeting"


class TestCalendarDeleteItem:
    """Tests for calendar_delete_item_async method."""

    @pytest.mark.asyncio
    async def test_success(self, mock_token_provider):
        """Test successful DELETE request."""
        client = OutlookClient(
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
            await client.calendar_delete_item_async(table="Calendar", id="event123")

            mock_send.assert_called_once()
            call_args = mock_send.call_args
            assert call_args[0][0] == "DELETE"
            assert "/datasets/calendars/tables/Calendar/items/event123" in call_args[0][1]


class TestContactGetTables:
    """Tests for contact_get_tables_async method."""

    @pytest.mark.asyncio
    async def test_success_with_json_response(self, mock_token_provider):
        """Test successful GET request."""
        client = OutlookClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(
            status=200,
            text='{"value": [{"name": "Contacts", "displayName": "Contacts"}]}'
        )

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ) as mock_send:
            _ = await client.contact_get_tables_async()

            mock_send.assert_called_once()
            call_args = mock_send.call_args
            assert call_args[0][0] == "GET"
            assert "/datasets/contacts/tables" in call_args[0][1]


class TestContactGetItems:
    """Tests for contact_get_items_async method."""

    @pytest.mark.asyncio
    async def test_success_with_json_response(self, mock_token_provider):
        """Test successful GET request."""
        client = OutlookClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(
            status=200,
            text='{"value": [{"id": "contact1", "displayName": "John Doe"}]}'
        )

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ) as mock_send:
            _ = await client.contact_get_items_async(table="Contacts")

            mock_send.assert_called_once()
            call_args = mock_send.call_args
            assert call_args[0][0] == "GET"
            assert "/datasets/contacts/tables/Contacts/items" in call_args[0][1]


class TestOnNewEmail:
    """Tests for on_new_email_async method (trigger)."""

    @pytest.mark.asyncio
    async def test_success_with_json_response(self, mock_token_provider):
        """Test successful GET trigger request."""
        client = OutlookClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(
            status=200,
            text='{"value": [{"id": "new-msg", "subject": "New Email!"}]}'
        )

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ) as mock_send:
            _ = await client.on_new_email_async()

            mock_send.assert_called_once()
            call_args = mock_send.call_args
            assert call_args[0][0] == "GET"
            assert "/v2/Mail/OnNewEmail" in call_args[0][1]

    @pytest.mark.asyncio
    async def test_with_filters(self, mock_token_provider):
        """Test GET trigger with filter parameters."""
        client = OutlookClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(status=200, text='{"value": []}')

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ) as mock_send:
            await client.on_new_email_async(
                folder_path="Inbox",
                from_="important@example.com",
                importance="High"
            )

            call_args = mock_send.call_args
            url = call_args[0][1]
            assert "folderPath=Inbox" in url
            assert "from=" in url
            assert "importance=High" in url


class TestDataClasses:
    """Tests for data class creation and attributes."""

    def test_client_receive_message(self):
        """Test ClientReceiveMessage dataclass creation."""
        attachment = ClientReceiveFileAttachment(
            id="att1",
            name="document.pdf",
            content_type="application/pdf",
            size=1024
        )
        message = ClientReceiveMessage(
            id="msg123",
            from_="sender@example.com",
            to="recipient@example.com",
            subject="Test Subject",
            body="<p>Hello!</p>",
            importance=1,
            has_attachment=True,
            attachments=[attachment],
            is_read=False,
            is_html=True
        )

        assert message.id == "msg123"
        assert message.subject == "Test Subject"
        assert message.has_attachment is True
        assert len(message.attachments) == 1

    def test_client_send_html_message(self):
        """Test ClientSendHtmlMessage dataclass creation."""
        attachment = ClientSendAttachment(
            name="report.pdf",
            content_bytes="base64encodedcontent"
        )
        message = ClientSendHtmlMessage(
            to="recipient@example.com",
            cc="cc@example.com",
            bcc="bcc@example.com",
            subject="Important Update",
            body="<h1>Hello</h1><p>Content here</p>",
            attachments=[attachment],
            importance="High"
        )

        assert message.to == "recipient@example.com"
        assert message.importance == "High"
        assert len(message.attachments) == 1

    def test_contact_response(self):
        """Test ContactResponse dataclass creation."""
        email = EmailAddress(name="John Doe", address="john@example.com")
        address = PhysicalAddress(
            street="123 Main St",
            city="Seattle",
            state="WA",
            postal_code="98101",
            country_or_region="USA"
        )
        contact = ContactResponse(
            id="contact123",
            given_name="John",
            surname="Doe",
            display_name="John Doe",
            email_addresses=[email],
            company_name="Contoso",
            job_title="Engineer",
            business_address=address
        )

        assert contact.given_name == "John"
        assert contact.surname == "Doe"
        assert len(contact.email_addresses) == 1

    def test_calendar_event_html_client(self):
        """Test CalendarEventHtmlClient dataclass creation."""
        event = CalendarEventHtmlClient(
            subject="Team Meeting",
            start="2024-01-20T10:00:00Z",
            end="2024-01-20T11:00:00Z",
            time_zone="Pacific Standard Time",
            location="Conference Room A",
            body="<p>Agenda: Review Q1 goals</p>",
            required_attendees="alice@example.com;bob@example.com",
            importance="Normal",
            is_all_day=False,
            reminder=15
        )

        assert event.subject == "Team Meeting"
        assert event.location == "Conference Room A"
        assert event.reminder == 15

    def test_reply_html_message(self):
        """Test ReplyHtmlMessage dataclass creation."""
        reply = ReplyHtmlMessage(
            body="<p>Thanks for the update!</p>",
            reply_all=True,
            importance="Normal"
        )

        assert reply.body is not None
        assert reply.reply_all is True

    def test_email_address(self):
        """Test EmailAddress dataclass creation."""
        email = EmailAddress(
            name="Jane Smith",
            address="jane.smith@example.com"
        )

        assert email.name == "Jane Smith"
        assert email.address == "jane.smith@example.com"

    def test_physical_address(self):
        """Test PhysicalAddress dataclass creation."""
        address = PhysicalAddress(
            street="456 Oak Ave",
            city="Portland",
            state="OR",
            postal_code="97201",
            country_or_region="United States"
        )

        assert address.city == "Portland"
        assert address.state == "OR"

    def test_client_receive_file_attachment(self):
        """Test ClientReceiveFileAttachment dataclass creation."""
        attachment = ClientReceiveFileAttachment(
            id="att123",
            name="photo.jpg",
            content_bytes="base64content",
            content_type="image/jpeg",
            size=2048,
            is_inline=False,
            content_id="cid123"
        )

        assert attachment.name == "photo.jpg"
        assert attachment.size == 2048
        assert attachment.is_inline is False

    def test_table(self):
        """Test Table dataclass creation."""
        table = Table(
            name="Calendar",
            display_name="My Calendar",
            dynamic_properties={"color": "blue"}
        )

        assert table.name == "Calendar"
        assert table.display_name == "My Calendar"


class TestEdgeCases:
    """Tests for edge cases and special scenarios."""

    @pytest.mark.asyncio
    async def test_http_client_property_access(self, mock_token_provider):
        """Test accessing http_client property."""
        client = OutlookClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        assert client.http_client is not None
        assert client._http_client is client.http_client

    @pytest.mark.asyncio
    async def test_multiple_consecutive_calls(self, mock_token_provider):
        """Test multiple consecutive API calls."""
        client = OutlookClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(status=200, text='{"value": []}')

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ) as mock_send:
            await client.get_emails_async()
            await client.calendar_get_tables_async()

            assert mock_send.call_count == 2

    @pytest.mark.asyncio
    async def test_empty_response_returns_none(self, mock_token_provider):
        """Test that empty response returns None."""
        client = OutlookClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(status=200, text="")

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ):
            result = await client.get_emails_async()
            assert result is None

    @pytest.mark.asyncio
    async def test_unauthorized_raises_exception(self, mock_token_provider):
        """Test that 401 unauthorized raises ConnectorException."""
        client = OutlookClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(status=401, text='{"error": "Unauthorized"}')

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ):
            with pytest.raises(ConnectorException) as exc_info:
                await client.get_email_async(message_id="msg123")

            assert exc_info.value.status_code == 401
