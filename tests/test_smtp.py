# Copyright (c) Microsoft Corporation. All rights reserved.

"""Unit tests for SmtpClient."""

import pytest
from unittest.mock import AsyncMock, patch
from azure.connectors.smtp import (
    SmtpClient,
    Email,
    Attachment,
)
from azure.connectors.sdk import (
    ConnectorClientOptions,
    ManagedIdentityTokenProvider,
    ConnectorException,
)
from azure.connectors.sdk.serialization import to_wire
from tests.conftest import MockResponse


class TestSmtpClientInitialization:
    """Tests for SmtpClient initialization."""

    def test_init_with_valid_url_and_defaults(self):
        """Test initialization with valid URL and default parameters."""
        client = SmtpClient("https://example.azure.com/connections/test")

        assert client._connection_runtime_url == "https://example.azure.com/connections/test"
        assert client.connector_name == "smtp"
        assert isinstance(client._http_client._token_provider, ManagedIdentityTokenProvider)

    def test_init_with_trailing_slash(self):
        """Test that trailing slash is removed from URL."""
        client = SmtpClient("https://example.azure.com/connections/test/")

        assert client._connection_runtime_url == "https://example.azure.com/connections/test"

    def test_init_with_custom_token_provider(self, mock_token_provider):
        """Test initialization with custom token provider."""
        client = SmtpClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        assert client._http_client._token_provider is mock_token_provider

    def test_init_with_custom_options(self, mock_token_provider):
        """Test initialization with custom options."""
        options = ConnectorClientOptions(timeout_seconds=60.0, max_retry_attempts=5)
        client = SmtpClient(
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
            SmtpClient("")

    def test_init_with_none_url_raises_error(self):
        """Test that None URL raises ValueError."""
        with pytest.raises(ValueError, match="connection_runtime_url cannot be None or empty"):
            SmtpClient(None)

    def test_connector_name_property(self, mock_token_provider):
        """Test connector_name property returns 'smtp'."""
        client = SmtpClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        assert client.connector_name == "smtp"


class TestSmtpClientLifecycle:
    """Tests for SmtpClient lifecycle methods."""

    @pytest.mark.asyncio
    async def test_close(self, mock_token_provider):
        """Test close method calls http_client.close."""
        client = SmtpClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        with patch.object(client._http_client, 'close', new_callable=AsyncMock) as mock_close:
            await client.close()
            mock_close.assert_called_once()

    @pytest.mark.asyncio
    async def test_context_manager(self, mock_token_provider):
        """Test async context manager functionality."""
        with patch.object(SmtpClient, 'close', new_callable=AsyncMock) as mock_close:
            async with SmtpClient(
                "https://example.azure.com/connections/test",
                token_provider=mock_token_provider
            ) as client:
                assert isinstance(client, SmtpClient)

            mock_close.assert_called_once()


class TestSendEmail:
    """Tests for send_email_async method."""

    @pytest.mark.asyncio
    async def test_success_basic_email(self, mock_token_provider):
        """Test successful POST request with basic email."""
        client = SmtpClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(status=200, text="")
        email_input = Email(
            from_="sender@contoso.com",
            to="recipient@contoso.com",
            subject="Test Email",
            body="This is a test email body."
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
            assert "/SendEmailV3" in call_args[0][1]

    @pytest.mark.asyncio
    async def test_success_with_multiple_recipients(self, mock_token_provider):
        """Test successful POST request with multiple recipients."""
        client = SmtpClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(status=200, text="")
        email_input = Email(
            from_="sender@contoso.com",
            to="recipient1@contoso.com;recipient2@contoso.com;recipient3@contoso.com",
            c_c="cc1@contoso.com;cc2@contoso.com",
            bcc="bcc@contoso.com",
            subject="Team Update",
            body="Hello team, this is an update."
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
            # Verify body argument was passed
            body = call_args.kwargs.get('body') or call_args[1].get('body')
            assert body is email_input

    @pytest.mark.asyncio
    async def test_success_with_all_fields(self, mock_token_provider):
        """Test successful POST request with all optional fields."""
        client = SmtpClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(status=200, text="")
        attachment = Attachment(
            file_name="document.pdf",
            content_data="SGVsbG8gV29ybGQ=",
            content_type="application/pdf",
            content_id="doc-123"
        )
        email_input = Email(
            from_="sender@contoso.com",
            to="recipient@contoso.com",
            c_c="cc@contoso.com",
            bcc="bcc@contoso.com",
            subject="Important Document",
            body="<h1>Please review</h1><p>See attached document.</p>",
            importance="High",
            read_receipt="sender@contoso.com",
            delivery_receipt="sender@contoso.com",
            attachments=[attachment]
        )

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ) as mock_send:
            await client.send_email_async(input=email_input)

            mock_send.assert_called_once()

    @pytest.mark.asyncio
    async def test_success_with_multiple_attachments(self, mock_token_provider):
        """Test successful POST request with multiple attachments."""
        client = SmtpClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(status=200, text="")
        attachment1 = Attachment(
            file_name="report.pdf",
            content_data="UmVwb3J0IGRhdGE=",
            content_type="application/pdf"
        )
        attachment2 = Attachment(
            file_name="image.png",
            content_data="aW1hZ2UgZGF0YQ==",
            content_type="image/png"
        )
        email_input = Email(
            from_="sender@contoso.com",
            to="recipient@contoso.com",
            subject="Files Attached",
            body="Please find the attached files.",
            attachments=[attachment1, attachment2]
        )

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ) as mock_send:
            await client.send_email_async(input=email_input)

            mock_send.assert_called_once()

    @pytest.mark.asyncio
    async def test_with_high_importance(self, mock_token_provider):
        """Test email with high importance."""
        client = SmtpClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(status=200, text="")
        email_input = Email(
            from_="sender@contoso.com",
            to="recipient@contoso.com",
            subject="Urgent Matter",
            body="This requires immediate attention.",
            importance="High"
        )

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ):
            await client.send_email_async(input=email_input)

    @pytest.mark.asyncio
    async def test_error_response_raises_exception(self, mock_token_provider):
        """Test that error response raises ConnectorException."""
        client = SmtpClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(status=400, text='{"error": "Invalid email format"}')
        email_input = Email(
            from_="invalid",
            to="recipient@contoso.com",
            subject="Test",
            body="Test body"
        )

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ):
            with pytest.raises(ConnectorException) as exc_info:
                await client.send_email_async(input=email_input)

            assert exc_info.value.status_code == 400


class TestDataClasses:
    """Tests for data class creation and attributes."""

    def test_attachment_creation(self):
        """Test Attachment dataclass creation."""
        attachment = Attachment(
            content_data="filedata",
            content_type="application/octet-stream",
            file_name="data.bin",
            content_id="bin-123"
        )

        assert attachment.content_data == "filedata"
        assert attachment.content_type == "application/octet-stream"
        assert attachment.file_name == "data.bin"
        assert attachment.content_id == "bin-123"

    def test_email_creation(self):
        """Test Email dataclass creation."""
        attachment = Attachment(
            file_name="spreadsheet.xlsx",
            content_data="exceldata",
            content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
        email = Email(
            from_="sender@contoso.com",
            to="recipient1@contoso.com;recipient2@contoso.com",
            c_c="cc@contoso.com",
            subject="Q4 Report",
            body="Please review the attached quarterly report.",
            bcc="manager@contoso.com",
            importance="High",
            read_receipt="sender@contoso.com",
            delivery_receipt="sender@contoso.com",
            attachments=[attachment]
        )

        assert email.from_ == "sender@contoso.com"
        assert "recipient1@contoso.com" in email.to
        assert email.importance == "High"
        assert email.read_receipt == "sender@contoso.com"

    def test_current_email_model_uses_swagger_wire_names(self):
        """Test the current email and attachment models preserve Swagger keys."""
        email = Email(
            from_="sender@contoso.com",
            to="recipient@contoso.com",
            c_c="copy@contoso.com",
            attachments=[Attachment(content_data="filedata")],
        )

        assert to_wire(email) == {
            "From": "sender@contoso.com",
            "To": "recipient@contoso.com",
            "CC": "copy@contoso.com",
            "Attachments": [{"ContentData": "filedata"}],
        }

    def test_email_with_defaults(self):
        """Test Email dataclass with default values."""
        email = Email()

        assert email.from_ is None
        assert email.to is None
        assert email.subject is None
        assert email.body is None
        assert email.importance is None
        assert email.attachments is None


class TestEdgeCases:
    """Tests for edge cases and special scenarios."""

    @pytest.mark.asyncio
    async def test_http_client_property_access(self, mock_token_provider):
        """Test accessing http_client property."""
        client = SmtpClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        assert client.http_client is not None
        assert client._http_client is client.http_client

    @pytest.mark.asyncio
    async def test_empty_body_email(self, mock_token_provider):
        """Test sending email with empty body."""
        client = SmtpClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(status=200, text="")
        email_input = Email(
            from_="sender@contoso.com",
            to="recipient@contoso.com",
            subject="Empty Body Test",
            body=""
        )

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ):
            await client.send_email_async(input=email_input)

    @pytest.mark.asyncio
    async def test_html_body_email(self, mock_token_provider):
        """Test sending email with HTML body."""
        client = SmtpClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(status=200, text="")
        email_input = Email(
            from_="sender@contoso.com",
            to="recipient@contoso.com",
            subject="HTML Email",
            body="<html><body><h1>Welcome</h1><p>This is an HTML email.</p></body></html>"
        )

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ):
            await client.send_email_async(input=email_input)

    @pytest.mark.asyncio
    async def test_multiple_consecutive_sends(self, mock_token_provider):
        """Test multiple consecutive send operations."""
        client = SmtpClient(
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
            email1 = Email(
                from_="sender@contoso.com",
                to="recipient1@contoso.com",
                subject="First Email",
                body="First message"
            )
            await client.send_email_async(input=email1)

            email2 = Email(
                from_="sender@contoso.com",
                to="recipient2@contoso.com",
                subject="Second Email",
                body="Second message"
            )
            await client.send_email_async(input=email2)

            assert mock_send.call_count == 2

    @pytest.mark.asyncio
    async def test_special_characters_in_subject(self, mock_token_provider):
        """Test email with special characters in subject."""
        client = SmtpClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(status=200, text="")
        email_input = Email(
            from_="sender@contoso.com",
            to="recipient@contoso.com",
            subject="Special chars: äöü ñ 日本語 emoji 🎉",
            body="Testing special character handling"
        )

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ):
            await client.send_email_async(input=email_input)

    @pytest.mark.asyncio
    async def test_long_recipient_list(self, mock_token_provider):
        """Test email with many recipients."""
        client = SmtpClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(status=200, text="")
        recipients = ";".join([f"user{i}@contoso.com" for i in range(50)])
        email_input = Email(
            from_="sender@contoso.com",
            to=recipients,
            subject="Mass Email",
            body="This email goes to many recipients."
        )

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ):
            await client.send_email_async(input=email_input)
