# Copyright (c) Microsoft Corporation. All rights reserved.

"""Unit tests for ClicksendsmsClient."""

from unittest.mock import AsyncMock, patch

import pytest

from azure.core.credentials import AzureKeyCredential
from azure.connectors.clicksendsms import ClicksendsmsClient
from azure.connectors.clicksendsms import (
    CreateListContactInput,
    CreateListInput,
    DeleteListResponse,
    SendFaxInput,
    SendLetterInput,
    SendMmsInput,
    SendPostcardInput,
    SendVoiceInput,
    SmsSendInput,
    SmsSendResponse,
    TRIGGER_OPERATIONS,
    UploadMediaInput,
)
from azure.connectors.sdk import (
    ConnectorException,
)
from tests.conftest import MockResponse
from tests.generated_connector_test_utils import model_instance


class TestClicksendsmsClientInitialization:
    """Tests for ClicksendsmsClient initialization."""

    def test_init_with_valid_url_and_defaults(self):
        """Test initialization with valid URL and default parameters."""
        client = ClicksendsmsClient(
            "https://example.azure.com/connections/test", AzureKeyCredential("test-key"))

        assert client._connection_runtime_url == "https://example.azure.com/connections/test"
        assert client.connector_name == "clicksendsms"
        assert isinstance(client._http_client._credential, AzureKeyCredential)

    def test_init_with_trailing_slash(self):
        """Test that trailing slash is removed from URL."""
        client = ClicksendsmsClient(
            "https://example.azure.com/connections/test/", AzureKeyCredential("test-key"))

        assert client._connection_runtime_url == "https://example.azure.com/connections/test"

    def test_init_with_custom_credential(self, mock_credential):
        """Test initialization with custom token provider."""
        client = ClicksendsmsClient(
            "https://example.azure.com/connections/test",
            credential=mock_credential,
        )

        assert client._http_client._credential is mock_credential

    def test_init_with_custom_settings(self, mock_credential):
        """Test initialization with custom pipeline settings."""
        client = ClicksendsmsClient(
            "https://example.azure.com/connections/test",
            credential=mock_credential,
            timeout=60.0,
            max_retry_attempts=5,
        )
        assert client._http_client._timeout_seconds == 60.0

    def test_init_with_empty_url_raises_error(self):
        """Test that empty URL raises ValueError."""
        with pytest.raises(ValueError, match="connection_runtime_url cannot be None or empty"):
            ClicksendsmsClient("", AzureKeyCredential("test-key"))

    def test_init_with_none_url_raises_error(self):
        """Test that None URL raises ValueError."""
        with pytest.raises(ValueError, match="connection_runtime_url cannot be None or empty"):
            ClicksendsmsClient(None, AzureKeyCredential("test-key"))

    def test_connector_name_property(self, mock_credential):
        """Test connector_name property returns 'clicksendsms'."""
        client = ClicksendsmsClient(
            "https://example.azure.com/connections/test",
            credential=mock_credential,
        )

        assert client.connector_name == "clicksendsms"


class TestClicksendsmsClientLifecycle:
    """Tests for ClicksendsmsClient lifecycle methods."""

    @pytest.mark.asyncio
    async def test_close(self, mock_credential):
        """Test close method calls http_client.close."""
        client = ClicksendsmsClient(
            "https://example.azure.com/connections/test",
            credential=mock_credential,
        )

        with patch.object(client._http_client, "close", new_callable=AsyncMock) as mock_close:
            await client.close()
            mock_close.assert_called_once()

    @pytest.mark.asyncio
    async def test_context_manager(self, mock_credential):
        """Test async context manager functionality."""
        with patch.object(ClicksendsmsClient, "close", new_callable=AsyncMock) as mock_close:
            async with ClicksendsmsClient(
                "https://example.azure.com/connections/test",
                credential=mock_credential,
            ) as client:
                assert isinstance(client, ClicksendsmsClient)

            mock_close.assert_called_once()


class TestClicksendsmsClientOperations:
    """Tests for ClicksendsmsClient operations against expected HTTP calls."""

    def _make_client(self, mock_credential):
        return ClicksendsmsClient(
            "https://example.azure.com/connections/test",
            credential=mock_credential,
        )

    @pytest.mark.asyncio
    async def test_sms_send_success(self, mock_credential):
        """Test sms_send issues a POST to the sms/send route with the input body."""
        client = self._make_client(mock_credential)
        payload = SmsSendInput(messages=[{"to": "+61411111111", "body": "hi"}])
        mock_response = MockResponse(status=200, text='{"data": {}}')

        with patch.object(
            client._http_client, "send", new_callable=AsyncMock,
            return_value=mock_response,
        ) as mock_send:
            result = await client.sms_send(input=payload)

            assert mock_send.call_args[0][0] == "POST"
            assert "/sms/send" in mock_send.call_args[0][1]
            assert mock_send.call_args.kwargs["body"] is payload
            assert result == {"data": {}}

    @pytest.mark.asyncio
    async def test_create_list_success(self, mock_credential):
        """Test create_list issues a POST to the lists route with the input body."""
        client = self._make_client(mock_credential)
        payload = CreateListInput(list_name="My List")
        mock_response = MockResponse(status=200, text='{"data": {}}')

        with patch.object(
            client._http_client, "send", new_callable=AsyncMock,
            return_value=mock_response,
        ) as mock_send:
            result = await client.create_list(input=payload)

            assert mock_send.call_args[0][0] == "POST"
            assert "/lists" in mock_send.call_args[0][1]
            assert mock_send.call_args.kwargs["body"] is payload
            assert result == {"data": {}}

    @pytest.mark.asyncio
    async def test_get_contact_lists_success(self, mock_credential):
        """Test get_contact_lists issues a GET to the lists route with query params."""
        client = self._make_client(mock_credential)
        mock_response = MockResponse(status=200, text='{"data": {}}')

        with patch.object(
            client._http_client, "send", new_callable=AsyncMock,
            return_value=mock_response,
        ) as mock_send:
            result = await client.get_contact_lists(page="2", limit="10")

            url = mock_send.call_args[0][1]
            assert mock_send.call_args[0][0] == "GET"
            assert "/lists" in url
            assert "page=2" in url
            assert "limit=10" in url
            assert result == {"data": {}}

    @pytest.mark.asyncio
    async def test_send_voice_success(self, mock_credential):
        """Test send_voice issues a POST to the voice/send route with the input body."""
        client = self._make_client(mock_credential)
        payload = SendVoiceInput(messages=[{"to": "+61411111111", "body": "hi"}])
        mock_response = MockResponse(status=200, text='{"data": {}}')

        with patch.object(
            client._http_client, "send", new_callable=AsyncMock,
            return_value=mock_response,
        ) as mock_send:
            result = await client.send_voice(input=payload)

            assert mock_send.call_args[0][0] == "POST"
            assert "/voice/send" in mock_send.call_args[0][1]
            assert mock_send.call_args.kwargs["body"] is payload
            assert result == {"data": {}}

    @pytest.mark.asyncio
    async def test_delete_list_success(self, mock_credential):
        """Test delete_list issues a DELETE to the lists/{id} route."""
        client = self._make_client(mock_credential)
        mock_response = MockResponse(status=200, text='{"data": {}}')

        with patch.object(
            client._http_client, "send", new_callable=AsyncMock,
            return_value=mock_response,
        ) as mock_send:
            result = await client.delete_list(list_id="123")

            assert mock_send.call_args[0][0] == "DELETE"
            assert "/lists/123" in mock_send.call_args[0][1]
            assert result == {"data": {}}

    @pytest.mark.asyncio
    async def test_create_list_contact_success(self, mock_credential):
        """Test create_list_contact issues a POST to the list contacts route."""
        client = self._make_client(mock_credential)
        payload = model_instance(
            CreateListContactInput,
            first_name="Ada",
            phone_number="+61411111111",
        )
        mock_response = MockResponse(status=200, text='{"data": {}}')

        with patch.object(
            client._http_client, "send", new_callable=AsyncMock,
            return_value=mock_response,
        ) as mock_send:
            result = await client.create_list_contact(input=payload, list_id="123")

            assert mock_send.call_args[0][0] == "POST"
            assert "/lists/123/contacts" in mock_send.call_args[0][1]
            assert mock_send.call_args.kwargs["body"] is payload
            assert result == {"data": {}}

    @pytest.mark.asyncio
    async def test_view_list_contacts_success(self, mock_credential):
        """Test view_list_contacts issues a GET to the list contacts route."""
        client = self._make_client(mock_credential)
        mock_response = MockResponse(status=200, text='{"data": {}}')

        with patch.object(
            client._http_client, "send", new_callable=AsyncMock,
            return_value=mock_response,
        ) as mock_send:
            result = await client.view_list_contacts(list_id="123")

            assert mock_send.call_args[0][0] == "GET"
            assert "/lists/123/contacts" in mock_send.call_args[0][1]
            assert result == {"data": {}}

    @pytest.mark.asyncio
    async def test_delete_list_contact_success(self, mock_credential):
        """Test delete_list_contact issues a DELETE to the single contact route."""
        client = self._make_client(mock_credential)
        mock_response = MockResponse(status=200, text='{"data": {}}')

        with patch.object(
            client._http_client, "send", new_callable=AsyncMock,
            return_value=mock_response,
        ) as mock_send:
            result = await client.delete_list_contact(list_id="123", contact_id="456")

            assert mock_send.call_args[0][0] == "DELETE"
            assert "/lists/123/contacts/456" in mock_send.call_args[0][1]
            assert result == {"data": {}}

    @pytest.mark.asyncio
    async def test_send_mms_success(self, mock_credential):
        """Test send_mms issues a POST to the mms/send route with the input body."""
        client = self._make_client(mock_credential)
        payload = SendMmsInput(messages=[{"to": "+61411111111"}], media_file="url")
        mock_response = MockResponse(status=200, text='{"data": {}}')

        with patch.object(
            client._http_client, "send", new_callable=AsyncMock,
            return_value=mock_response,
        ) as mock_send:
            result = await client.send_mms(input=payload)

            assert mock_send.call_args[0][0] == "POST"
            assert "/mms/send" in mock_send.call_args[0][1]
            assert mock_send.call_args.kwargs["body"] is payload
            assert result == {"data": {}}

    @pytest.mark.asyncio
    async def test_send_fax_success(self, mock_credential):
        """Test send_fax issues a POST to the fax/send route with the input body."""
        client = self._make_client(mock_credential)
        payload = SendFaxInput(messages=[{"to": "+61411111111"}], file_url="url")
        mock_response = MockResponse(status=200, text='{"data": {}}')

        with patch.object(
            client._http_client, "send", new_callable=AsyncMock,
            return_value=mock_response,
        ) as mock_send:
            result = await client.send_fax(input=payload)

            assert mock_send.call_args[0][0] == "POST"
            assert "/fax/send" in mock_send.call_args[0][1]
            assert mock_send.call_args.kwargs["body"] is payload
            assert result == {"data": {}}

    @pytest.mark.asyncio
    async def test_upload_media_success(self, mock_credential):
        """Test upload_media issues a POST to the uploads route with the convert query."""
        client = self._make_client(mock_credential)
        payload = UploadMediaInput(content="base64==")
        mock_response = MockResponse(status=200, text='{"data": {}}')

        with patch.object(
            client._http_client, "send", new_callable=AsyncMock,
            return_value=mock_response,
        ) as mock_send:
            result = await client.upload_media(input=payload, convert="mms")

            url = mock_send.call_args[0][1]
            assert mock_send.call_args[0][0] == "POST"
            assert "/uploads" in url
            assert "convert=mms" in url
            assert mock_send.call_args.kwargs["body"] is payload
            assert result == {"data": {}}

    @pytest.mark.asyncio
    async def test_search_contact_list_success(self, mock_credential):
        """Test search_contact_list issues a GET to the search route with the q query."""
        client = self._make_client(mock_credential)
        mock_response = MockResponse(status=200, text='{"data": {}}')

        with patch.object(
            client._http_client, "send", new_callable=AsyncMock,
            return_value=mock_response,
        ) as mock_send:
            result = await client.search_contact_list(q="friends")

            url = mock_send.call_args[0][1]
            assert mock_send.call_args[0][0] == "GET"
            assert "/search/contacts-lists" in url
            assert "q=friends" in url
            assert result == {"data": {}}

    @pytest.mark.asyncio
    async def test_send_letter_success(self, mock_credential):
        """Test send_letter issues a POST to the letters route with the input body."""
        client = self._make_client(mock_credential)
        payload = model_instance(
            SendLetterInput,
            file_url="url",
            recipients=[{"address_name": "Ada"}],
        )
        mock_response = MockResponse(status=200, text='{"data": {}}')

        with patch.object(
            client._http_client, "send", new_callable=AsyncMock,
            return_value=mock_response,
        ) as mock_send:
            result = await client.send_letter(input=payload)

            assert mock_send.call_args[0][0] == "POST"
            assert "/post/letters/send" in mock_send.call_args[0][1]
            assert mock_send.call_args.kwargs["body"] is payload
            assert result == {"data": {}}

    @pytest.mark.asyncio
    async def test_send_postcard_success(self, mock_credential):
        """Test send_postcard issues a POST to the postcards route with the input body."""
        client = self._make_client(mock_credential)
        payload = SendPostcardInput(recipients=[{"address_name": "Ada"}], file_urls=["url"])
        mock_response = MockResponse(status=200, text='{"data": {}}')

        with patch.object(
            client._http_client, "send", new_callable=AsyncMock,
            return_value=mock_response,
        ) as mock_send:
            result = await client.send_postcard(input=payload)

            assert mock_send.call_args[0][0] == "POST"
            assert "/post/postcards/send" in mock_send.call_args[0][1]
            assert mock_send.call_args.kwargs["body"] is payload
            assert result == {"data": {}}

    @pytest.mark.asyncio
    async def test_empty_response_body_returns_none(self, mock_credential):
        """Test a 2xx response with no body returns None."""
        client = self._make_client(mock_credential)
        mock_response = MockResponse(status=200, text="")

        with patch.object(
            client._http_client, "send", new_callable=AsyncMock,
            return_value=mock_response,
        ):
            result = await client.view_list_contacts(list_id="123")

            assert result is None


class TestClicksendsmsClientErrorHandling:
    """Error handling tests for ClicksendsmsClient operations."""

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "operation",
        [
            "sms_send",
            "create_list",
            "get_contact_lists",
            "send_voice",
            "delete_list",
            "create_list_contact",
            "view_list_contacts",
            "delete_list_contact",
            "send_mms",
            "send_fax",
            "upload_media",
            "search_contact_list",
            "send_letter",
            "send_postcard",
        ],
    )
    async def test_error_response_raises_exception(self, mock_credential, operation):
        """Test non-2xx responses raise ConnectorException for every operation."""
        client = ClicksendsmsClient(
            "https://example.azure.com/connections/test",
            credential=mock_credential,
        )
        mock_response = MockResponse(status=500, text='{"error":"server failure"}')

        with patch.object(
            client._http_client, "send", new_callable=AsyncMock,
            return_value=mock_response,
        ):
            with pytest.raises(ConnectorException) as exc_info:
                if operation == "sms_send":
                    await client.sms_send(input=model_instance(SmsSendInput))
                elif operation == "create_list":
                    await client.create_list(input=model_instance(CreateListInput))
                elif operation == "get_contact_lists":
                    await client.get_contact_lists()
                elif operation == "send_voice":
                    await client.send_voice(input=model_instance(SendVoiceInput))
                elif operation == "delete_list":
                    await client.delete_list(list_id="123")
                elif operation == "create_list_contact":
                    await client.create_list_contact(
                        input=model_instance(CreateListContactInput),
                        list_id="123",
                    )
                elif operation == "view_list_contacts":
                    await client.view_list_contacts(list_id="123")
                elif operation == "delete_list_contact":
                    await client.delete_list_contact(list_id="123", contact_id="456")
                elif operation == "send_mms":
                    await client.send_mms(input=model_instance(SendMmsInput))
                elif operation == "send_fax":
                    await client.send_fax(input=model_instance(SendFaxInput))
                elif operation == "upload_media":
                    await client.upload_media(
                        input=model_instance(UploadMediaInput),
                        convert="mms",
                    )
                elif operation == "search_contact_list":
                    await client.search_contact_list(q="friends")
                elif operation == "send_letter":
                    await client.send_letter(input=model_instance(SendLetterInput))
                else:
                    await client.send_postcard(input=model_instance(SendPostcardInput))

            assert exc_info.value.status_code == 500


class TestClicksendsmsTriggerOperations:
    """Tests for the module-level TRIGGER_OPERATIONS registry."""

    def test_all_expected_triggers_registered(self):
        """Test the registry exposes every ClickSend SMS trigger operation."""
        assert set(TRIGGER_OPERATIONS) == {"sms_inbound_automation"}

    @pytest.mark.parametrize("operation_id", list(TRIGGER_OPERATIONS))
    def test_trigger_metadata_shape(self, operation_id):
        """Test each trigger entry carries the expected metadata fields."""
        trigger = TRIGGER_OPERATIONS[operation_id]

        assert trigger["operation_id"] == operation_id
        assert trigger["method"] == "post"
        assert trigger["path"].startswith("/{connectionId}/")
        assert trigger["required_parameters"] == ["body"]
        assert "callback_payload_type" in trigger

    def test_triggers_are_not_client_methods(self):
        """Test trigger operations are not emitted as callable client methods."""
        assert not hasattr(ClicksendsmsClient, "sms_inbound_automation_async")


class TestClicksendsmsTypeSerialization:
    """Tests for ClickSend SMS dataclass defaults."""

    def test_dataclass_defaults(self):
        """Test dataclasses default their fields to None."""
        assert SmsSendResponse().http_code is None
        assert SmsSendResponse().response_msg is None
        assert DeleteListResponse().response_msg is None
        contact = CreateListContactInput(
            first_name="Ada",
            last_name="Lovelace",
            phone_number="+61411111111",
        )
        assert contact.first_name == "Ada"
        assert contact.custom1 is None
        assert contact.address_line1 is None
