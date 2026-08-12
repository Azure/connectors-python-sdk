# Copyright (c) Microsoft Corporation. All rights reserved.

"""Unit tests for MicrosoftbookingsClient."""

import pytest
from unittest.mock import AsyncMock, patch
from azure.connectors.microsoftbookings import (
    MicrosoftbookingsClient,
    CreateAppointmentInput,
    UpdateAppointmentInput,
    CancelAppointmentInput,
    WebhookResponse,
    ListMailboxResponse,
    DeleteWebhookResponse,
    MailboxEntity,
    AppointmentData,
    CustomerData,
    StaffMemberData,
    CustomQuestion,
    TRIGGER_OPERATIONS,
)
from azure.connectors.sdk import (
    ConnectorClientOptions,
    ManagedIdentityTokenProvider,
    ConnectorException,
)
from tests.conftest import MockResponse


class TestMicrosoftbookingsClientInitialization:
    """Tests for MicrosoftbookingsClient initialization."""

    def test_init_with_valid_url_and_defaults(self):
        """Test initialization with valid URL and default parameters."""
        client = MicrosoftbookingsClient(
            "https://example.azure.com/connections/test"
        )

        assert client._connection_runtime_url == (
            "https://example.azure.com/connections/test"
        )
        assert client.connector_name == "microsoftbookings"
        assert isinstance(
            client._http_client._token_provider, ManagedIdentityTokenProvider
        )

    def test_init_with_trailing_slash(self):
        """Test that trailing slash is removed from URL."""
        client = MicrosoftbookingsClient(
            "https://example.azure.com/connections/test/"
        )

        assert client._connection_runtime_url == (
            "https://example.azure.com/connections/test"
        )

    def test_init_with_custom_token_provider(self, mock_token_provider):
        """Test initialization with custom token provider."""
        client = MicrosoftbookingsClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        assert client._http_client._token_provider is mock_token_provider

    def test_init_with_custom_options(self, mock_token_provider):
        """Test initialization with custom options."""
        options = ConnectorClientOptions(
            timeout_seconds=60.0, max_retry_attempts=5
        )
        client = MicrosoftbookingsClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider,
            options=options
        )

        assert client._options is options
        assert client._options.timeout_seconds == 60.0
        assert client._options.max_retry_attempts == 5

    def test_init_with_empty_url_raises_error(self):
        """Test that empty URL raises ValueError."""
        with pytest.raises(
            ValueError, match="connection_runtime_url cannot be None or empty"
        ):
            MicrosoftbookingsClient("")

    def test_init_with_none_url_raises_error(self):
        """Test that None URL raises ValueError."""
        with pytest.raises(
            ValueError, match="connection_runtime_url cannot be None or empty"
        ):
            MicrosoftbookingsClient(None)

    def test_connector_name_property(self, mock_token_provider):
        """Test connector_name property returns 'microsoftbookings'."""
        client = MicrosoftbookingsClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        assert client.connector_name == "microsoftbookings"


class TestMicrosoftbookingsClientLifecycle:
    """Tests for MicrosoftbookingsClient lifecycle methods."""

    @pytest.mark.asyncio
    async def test_close(self, mock_token_provider):
        """Test close method calls http_client.close."""
        client = MicrosoftbookingsClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        with patch.object(
            client._http_client, 'close', new_callable=AsyncMock
        ) as mock_close:
            await client.close()
            mock_close.assert_called_once()

    @pytest.mark.asyncio
    async def test_context_manager(self, mock_token_provider):
        """Test async context manager functionality."""
        with patch.object(
            MicrosoftbookingsClient, 'close', new_callable=AsyncMock
        ) as mock_close:
            async with MicrosoftbookingsClient(
                "https://example.azure.com/connections/test",
                token_provider=mock_token_provider
            ) as client:
                assert isinstance(client, MicrosoftbookingsClient)

            mock_close.assert_called_once()


class TestTriggerOperations:
    """Tests for appointment trigger registration metadata."""

    @pytest.mark.parametrize(
        ("operation_id", "payload_type"),
        [
            ("CreateAppointment", "WebhookResponse"),
            ("UpdateAppointment", None),
            ("CancelAppointment", None),
        ],
    )
    def test_registration_metadata(self, operation_id, payload_type):
        """Test metadata needed to register each appointment trigger."""
        metadata = TRIGGER_OPERATIONS[operation_id]

        assert metadata["method"] == "post"
        assert metadata["required_parameters"] == ["SMTPAddress", "body"]
        assert metadata["callback_payload_type"] == payload_type


class TestListBookingsBusinessUserAsAdminAsync:
    """Tests for list_bookings_business_user_as_admin_async method."""

    @pytest.mark.asyncio
    async def test_success(self, mock_token_provider):
        """Test successful request returns mailbox list."""
        response_json = (
            '{"mailboxes": ['
            '{"display_name": "Contoso Bookings", "email": "bookings@contoso.com"}'
            ']}'
        )
        mock_response = MockResponse(status=200, text=response_json)

        client = MicrosoftbookingsClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ) as mock_send:
            result = await client.list_bookings_business_user_as_admin_async()

            mock_send.assert_called_once()
            call_args = mock_send.call_args
            assert call_args[0][0] == "GET"
            assert "/bookingBusinessesUserAsAdmin" in call_args[0][1]
            assert result is not None
            assert "mailboxes" in result

    @pytest.mark.asyncio
    async def test_empty_response_returns_none(self, mock_token_provider):
        """Test empty response returns None."""
        mock_response = MockResponse(status=200, text='')

        client = MicrosoftbookingsClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ):
            result = await client.list_bookings_business_user_as_admin_async()
            assert result is None

    @pytest.mark.asyncio
    async def test_error_response_raises_exception(self, mock_token_provider):
        """Test that error response raises ConnectorException."""
        mock_response = MockResponse(
            status=401,
            text='{"error": {"code": "Unauthorized", "message": "Token expired"}}'
        )

        client = MicrosoftbookingsClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ):
            with pytest.raises(ConnectorException) as exc_info:
                await client.list_bookings_business_user_as_admin_async()

            assert exc_info.value.status_code == 401


class TestDataClasses:
    """Tests for dataclass definitions."""

    def test_create_appointment_input_defaults(self):
        """Test CreateAppointmentInput dataclass with defaults."""
        input_obj = CreateAppointmentInput()
        assert input_obj.webhook is None

    def test_create_appointment_input_with_values(self):
        """Test CreateAppointmentInput dataclass with values."""
        input_obj = CreateAppointmentInput(
            webhook={"callbackUrl": "https://example.com/callback"}
        )
        assert input_obj.webhook["callbackUrl"] == "https://example.com/callback"

    def test_update_appointment_input_defaults(self):
        """Test UpdateAppointmentInput dataclass with defaults."""
        input_obj = UpdateAppointmentInput()
        assert input_obj.webhook is None

    def test_cancel_appointment_input_defaults(self):
        """Test CancelAppointmentInput dataclass with defaults."""
        input_obj = CancelAppointmentInput()
        assert input_obj.webhook is None

    def test_webhook_response_defaults(self):
        """Test WebhookResponse dataclass with defaults."""
        response = WebhookResponse()
        assert response.webhook_id is None

    def test_webhook_response_with_values(self):
        """Test WebhookResponse dataclass with values."""
        response = WebhookResponse(webhook_id="wh-12345")
        assert response.webhook_id == "wh-12345"

    def test_list_mailbox_response_defaults(self):
        """Test ListMailboxResponse dataclass with defaults."""
        response = ListMailboxResponse()
        assert response.mailboxes is None

    def test_list_mailbox_response_with_values(self):
        """Test ListMailboxResponse dataclass with values."""
        mailbox = MailboxEntity(
            display_name="Contoso Bookings",
            email="bookings@contoso.com"
        )
        response = ListMailboxResponse(mailboxes=[mailbox])
        assert len(response.mailboxes) == 1
        assert response.mailboxes[0].email == "bookings@contoso.com"

    def test_delete_webhook_response_defaults(self):
        """Test DeleteWebhookResponse string alias."""
        response = DeleteWebhookResponse()
        assert response == ""

    def test_mailbox_entity_defaults(self):
        """Test MailboxEntity dataclass with defaults."""
        entity = MailboxEntity()
        assert entity.display_name is None
        assert entity.email is None

    def test_mailbox_entity_with_values(self):
        """Test MailboxEntity dataclass with values."""
        entity = MailboxEntity(
            display_name="Contoso Bookings",
            email="bookings@contoso.com"
        )
        assert entity.display_name == "Contoso Bookings"
        assert entity.email == "bookings@contoso.com"

    def test_appointment_data_defaults(self):
        """Test AppointmentData dataclass with defaults."""
        data = AppointmentData()
        assert data.id is None
        assert data.service_name is None
        assert data.customer_email is None
        assert data.start_time is None
        assert data.end_time is None
        assert data.duration is None

    def test_appointment_data_with_values(self):
        """Test AppointmentData dataclass with values."""
        data = AppointmentData(
            id="apt-123",
            service_name="Consultation",
            customer_email="customer@example.com",
            start_time="2026-06-10T10:00:00Z",
            end_time="2026-06-10T11:00:00Z",
            duration=60,
            is_s_m_s_notifications_enabled=True
        )
        assert data.id == "apt-123"
        assert data.service_name == "Consultation"
        assert data.duration == 60
        assert data.is_s_m_s_notifications_enabled is True

    def test_customer_data_defaults(self):
        """Test CustomerData dataclass with defaults."""
        data = CustomerData()
        assert data.id is None
        assert data.name is None
        assert data.email is None

    def test_customer_data_with_values(self):
        """Test CustomerData dataclass with values."""
        data = CustomerData(
            id="cust-123",
            name="John Doe",
            email="john@example.com",
            time_zone="America/New_York"
        )
        assert data.id == "cust-123"
        assert data.name == "John Doe"
        assert data.email == "john@example.com"

    def test_staff_member_data_defaults(self):
        """Test StaffMemberData dataclass with defaults."""
        data = StaffMemberData()
        assert data.id is None
        assert data.display_name is None
        assert data.email_address is None

    def test_staff_member_data_with_values(self):
        """Test StaffMemberData dataclass with values."""
        data = StaffMemberData(
            id="staff-123",
            display_name="Jane Smith",
            email_address="jane@contoso.com"
        )
        assert data.id == "staff-123"
        assert data.display_name == "Jane Smith"
        assert data.email_address == "jane@contoso.com"

    def test_custom_question_defaults(self):
        """Test CustomQuestion dataclass with defaults."""
        question = CustomQuestion()
        assert question.question_id is None
        assert question.question is None
        assert question.answer is None
        assert question.is_required is None

    def test_custom_question_with_values(self):
        """Test CustomQuestion dataclass with values."""
        question = CustomQuestion(
            question_id="q-123",
            question="What is your preferred contact method?",
            answer="Email",
            is_required=True,
            answer_options=["Email", "Phone", "Text"],
            selected_options=[0]
        )
        assert question.question_id == "q-123"
        assert question.question == "What is your preferred contact method?"
        assert question.answer == "Email"
        assert question.is_required is True
        assert len(question.answer_options) == 3
        assert question.selected_options == [0]
