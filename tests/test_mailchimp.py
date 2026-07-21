# Copyright (c) Microsoft Corporation. All rights reserved.

"""Unit tests for MailchimpClient."""

from unittest.mock import AsyncMock, patch

import pytest

from azure.connectors.mailchimp import (
    MailchimpClient,
    NewCampaignRequest,
    NewListRequest,
    NewMemberInListRequest,
    NewMembersInListRequest,
    TRIGGER_OPERATIONS,
    UpdateMemberInListRequest,
)
from azure.connectors.sdk import (
    ConnectorClientOptions,
    ConnectorException,
    ManagedIdentityTokenProvider,
)
from tests.conftest import MockResponse


class TestMailchimpClientInitialization:
    """Tests for MailchimpClient initialization."""

    def test_init_with_valid_url_and_defaults(self):
        """Test initialization with valid URL and default parameters."""
        client = MailchimpClient("https://example.azure.com/connections/test")

        assert client._connection_runtime_url == "https://example.azure.com/connections/test"
        assert client.connector_name == "mailchimp"
        assert isinstance(client._http_client._token_provider, ManagedIdentityTokenProvider)

    def test_init_with_trailing_slash(self):
        """Test that trailing slash is removed from URL."""
        client = MailchimpClient("https://example.azure.com/connections/test/")

        assert client._connection_runtime_url == "https://example.azure.com/connections/test"

    def test_init_with_custom_token_provider(self, mock_token_provider):
        """Test initialization with custom token provider."""
        client = MailchimpClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider,
        )

        assert client._http_client._token_provider is mock_token_provider

    def test_init_with_custom_options(self, mock_token_provider):
        """Test initialization with custom options."""
        options = ConnectorClientOptions(timeout_seconds=60.0, max_retry_attempts=5)
        client = MailchimpClient(
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
            MailchimpClient("")

    def test_init_with_none_url_raises_error(self):
        """Test that None URL raises ValueError."""
        with pytest.raises(ValueError, match="connection_runtime_url cannot be None or empty"):
            MailchimpClient(None)

    def test_connector_name_property(self, mock_token_provider):
        """Test connector_name property returns 'mailchimp'."""
        client = MailchimpClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider,
        )

        assert client.connector_name == "mailchimp"


class TestMailchimpClientLifecycle:
    """Tests for MailchimpClient lifecycle methods."""

    @pytest.mark.asyncio
    async def test_close(self, mock_token_provider):
        """Test close method calls http_client.close."""
        client = MailchimpClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider,
        )

        with patch.object(client._http_client, "close", new_callable=AsyncMock) as mock_close:
            await client.close()
            mock_close.assert_called_once()

    @pytest.mark.asyncio
    async def test_context_manager(self, mock_token_provider):
        """Test async context manager functionality."""
        with patch.object(MailchimpClient, "close", new_callable=AsyncMock) as mock_close:
            async with MailchimpClient(
                "https://example.azure.com/connections/test",
                token_provider=mock_token_provider,
            ) as client:
                assert isinstance(client, MailchimpClient)

            mock_close.assert_called_once()


class TestMailchimpClientOperations:
    """Tests for MailchimpClient operations against expected HTTP calls."""

    @pytest.mark.asyncio
    async def test_get_campaigns_success(self, mock_token_provider):
        """Test list campaigns issues a GET to the campaigns route."""
        client = MailchimpClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider,
        )
        mock_response = MockResponse(status=200, text='{"campaigns": []}')

        with patch.object(
            client._http_client,
            "send_async",
            new_callable=AsyncMock,
            return_value=mock_response,
        ) as mock_send:
            result = await client.get_campaigns_async()

            method, url = mock_send.call_args[0][0], mock_send.call_args[0][1]
            assert method == "GET"
            assert url.endswith("/campaigns")
            assert result == {"campaigns": []}

    @pytest.mark.asyncio
    async def test_sendcampaign_success(self, mock_token_provider):
        """Test send campaign issues a POST to the send action route."""
        client = MailchimpClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider,
        )
        mock_response = MockResponse(status=204, text="")

        with patch.object(
            client._http_client,
            "send_async",
            new_callable=AsyncMock,
            return_value=mock_response,
        ) as mock_send:
            result = await client.sendcampaign_async(campaign_id="c1")

            method, url = mock_send.call_args[0][0], mock_send.call_args[0][1]
            assert method == "POST"
            assert url.endswith("/campaigns/c1/actions/send")
            assert result is None

    @pytest.mark.asyncio
    async def test_get_lists_success(self, mock_token_provider):
        """Test get all lists issues a GET to the lists route."""
        client = MailchimpClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider,
        )
        mock_response = MockResponse(status=200, text='{"lists": []}')

        with patch.object(
            client._http_client,
            "send_async",
            new_callable=AsyncMock,
            return_value=mock_response,
        ) as mock_send:
            result = await client.get_lists_async(count="10", offset="0")

            method, url = mock_send.call_args[0][0], mock_send.call_args[0][1]
            assert method == "GET"
            assert "/lists" in url
            assert "count=10" in url
            assert "offset=0" in url
            assert result == {"lists": []}

    @pytest.mark.asyncio
    async def test_newlist_success(self, mock_token_provider):
        """Test new list issues a POST to the lists route with a body."""
        client = MailchimpClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider,
        )
        mock_response = MockResponse(status=200, text='{"id": "abc"}')

        with patch.object(
            client._http_client,
            "send_async",
            new_callable=AsyncMock,
            return_value=mock_response,
        ) as mock_send:
            result = await client.newlist_async(input=NewListRequest(name="Test"))

            method, url = mock_send.call_args[0][0], mock_send.call_args[0][1]
            assert method == "POST"
            assert url.endswith("/lists")
            assert mock_send.call_args.kwargs["body"] is not None
            assert result == {"id": "abc"}

    @pytest.mark.asyncio
    async def test_add_members_success(self, mock_token_provider):
        """Test batch subscribe issues a POST to the list route with a body."""
        client = MailchimpClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider,
        )
        mock_response = MockResponse(status=200, text='{"new_members": []}')

        with patch.object(
            client._http_client,
            "send_async",
            new_callable=AsyncMock,
            return_value=mock_response,
        ) as mock_send:
            result = await client.add_members_async(
                input=NewMembersInListRequest(),
                list_id="L1",
            )

            method, url = mock_send.call_args[0][0], mock_send.call_args[0][1]
            assert method == "POST"
            assert url.endswith("/lists/L1")
            assert mock_send.call_args.kwargs["body"] is not None
            assert result == {"new_members": []}

    @pytest.mark.asyncio
    async def test_get_list_members_success(self, mock_token_provider):
        """Test show list members issues a GET to the members route."""
        client = MailchimpClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider,
        )
        mock_response = MockResponse(status=200, text='{"members": []}')

        with patch.object(
            client._http_client,
            "send_async",
            new_callable=AsyncMock,
            return_value=mock_response,
        ) as mock_send:
            result = await client.get_list_members_async(list_id="L1")

            method, url = mock_send.call_args[0][0], mock_send.call_args[0][1]
            assert method == "GET"
            assert url.endswith("/lists/L1/members")
            assert result == {"members": []}

    @pytest.mark.asyncio
    async def test_addmember_success(self, mock_token_provider):
        """Test add member issues a POST to the members route with a body."""
        client = MailchimpClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider,
        )
        mock_response = MockResponse(status=200, text='{"id": "m1"}')

        with patch.object(
            client._http_client,
            "send_async",
            new_callable=AsyncMock,
            return_value=mock_response,
        ) as mock_send:
            result = await client.addmember_async(
                input=NewMemberInListRequest(),
                list_id="L1",
            )

            method, url = mock_send.call_args[0][0], mock_send.call_args[0][1]
            assert method == "POST"
            assert url.endswith("/lists/L1/members")
            assert mock_send.call_args.kwargs["body"] is not None
            assert result == {"id": "m1"}

    @pytest.mark.asyncio
    async def test_newcampaign_success(self, mock_token_provider):
        """Test new campaign issues a POST to the v2 campaigns route with a body."""
        client = MailchimpClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider,
        )
        mock_response = MockResponse(status=200, text='{"id": "camp1"}')

        with patch.object(
            client._http_client,
            "send_async",
            new_callable=AsyncMock,
            return_value=mock_response,
        ) as mock_send:
            result = await client.newcampaign_async(input=NewCampaignRequest())

            method, url = mock_send.call_args[0][0], mock_send.call_args[0][1]
            assert method == "POST"
            assert url.endswith("/v2/campaigns")
            assert mock_send.call_args.kwargs["body"] is not None
            assert result == {"id": "camp1"}

    @pytest.mark.asyncio
    async def test_removemember_success(self, mock_token_provider):
        """Test remove member issues a DELETE to the members route."""
        client = MailchimpClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider,
        )
        mock_response = MockResponse(status=204, text="")

        with patch.object(
            client._http_client,
            "send_async",
            new_callable=AsyncMock,
            return_value=mock_response,
        ) as mock_send:
            result = await client.removemember_async(list_id="L1")

            method, url = mock_send.call_args[0][0], mock_send.call_args[0][1]
            assert method == "DELETE"
            assert url.endswith("/members")
            assert "L1" in url
            assert result is None

    @pytest.mark.asyncio
    async def test_updatemember_success(self, mock_token_provider):
        """Test update member issues a PATCH to the members route with a body."""
        client = MailchimpClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider,
        )
        mock_response = MockResponse(status=200, text='{"id": "m1"}')

        with patch.object(
            client._http_client,
            "send_async",
            new_callable=AsyncMock,
            return_value=mock_response,
        ) as mock_send:
            result = await client.updatemember_async(
                input=UpdateMemberInListRequest(),
                list_id="L1",
            )

            method, url = mock_send.call_args[0][0], mock_send.call_args[0][1]
            assert method == "PATCH"
            assert url.endswith("/members")
            assert "L1" in url
            assert mock_send.call_args.kwargs["body"] is not None
            assert result == {"id": "m1"}

    @pytest.mark.asyncio
    async def test_empty_response_body_returns_none(self, mock_token_provider):
        """Test a 2xx response with no body returns None."""
        client = MailchimpClient(
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
            result = await client.get_campaigns_async()

            assert result is None


class TestMailchimpClientErrorHandling:
    """Error handling tests for MailchimpClient operations."""

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "operation",
        [
            "get_campaigns",
            "sendcampaign",
            "get_lists",
            "newlist",
            "add_members",
            "get_list_members",
            "addmember",
            "newcampaign",
            "removemember",
            "updatemember",
        ],
    )
    async def test_error_response_raises_exception(self, mock_token_provider, operation):
        """Test non-2xx responses raise ConnectorException for every operation."""
        client = MailchimpClient(
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
                if operation == "get_campaigns":
                    await client.get_campaigns_async()
                elif operation == "sendcampaign":
                    await client.sendcampaign_async(campaign_id="c1")
                elif operation == "get_lists":
                    await client.get_lists_async()
                elif operation == "newlist":
                    await client.newlist_async(input=NewListRequest())
                elif operation == "add_members":
                    await client.add_members_async(
                        input=NewMembersInListRequest(), list_id="L1"
                    )
                elif operation == "get_list_members":
                    await client.get_list_members_async(list_id="L1")
                elif operation == "addmember":
                    await client.addmember_async(
                        input=NewMemberInListRequest(), list_id="L1"
                    )
                elif operation == "newcampaign":
                    await client.newcampaign_async(input=NewCampaignRequest())
                elif operation == "removemember":
                    await client.removemember_async(list_id="L1")
                else:
                    await client.updatemember_async(
                        input=UpdateMemberInListRequest(), list_id="L1"
                    )

            assert exc_info.value.status_code == 500


class TestMailchimpTriggerOperations:
    """Tests for the module-level TRIGGER_OPERATIONS registry."""

    def test_all_expected_triggers_registered(self):
        """Test the registry exposes every Mailchimp trigger operation."""
        assert set(TRIGGER_OPERATIONS) == {
            "OnMemberSubscribed",
            "OnCreateList",
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

    def test_on_member_subscribed_requires_list_id(self):
        """Test the OnMemberSubscribed trigger declares list_id as required."""
        trigger = TRIGGER_OPERATIONS["OnMemberSubscribed"]

        assert trigger["required_parameters"] == ["list_id"]
        assert trigger["callback_payload_type"] == "GetMembersResponseModel"

    def test_on_create_list_has_no_required_parameters(self):
        """Test the OnCreateList trigger declares no required parameters."""
        trigger = TRIGGER_OPERATIONS["OnCreateList"]

        assert trigger["required_parameters"] == []
        assert trigger["callback_payload_type"] == "GetListsResponseModel"

    def test_triggers_are_not_client_methods(self):
        """Test trigger operations are not emitted as callable client methods."""
        assert not hasattr(MailchimpClient, "on_member_subscribed_async")
        assert not hasattr(MailchimpClient, "on_create_list_async")


class TestMailchimpTypeSerialization:
    """Tests for Mailchimp connector dataclass defaults."""

    def test_request_dataclasses_instantiate(self):
        """Test generated request dataclasses instantiate without arguments."""
        assert NewListRequest().name is None
        assert NewCampaignRequest().type_ is None
        assert NewMemberInListRequest().email_address is None
        assert UpdateMemberInListRequest().status is None
