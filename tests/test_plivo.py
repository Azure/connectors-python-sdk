# Copyright (c) Microsoft Corporation. All rights reserved.

"""Unit tests for PlivoClient."""

from unittest.mock import AsyncMock, patch

import pytest

import azure.connectors.plivo as plivo_module
from azure.connectors.plivo import Call, PlivoClient, SMS
from azure.connectors.sdk import ConnectorException, ManagedIdentityTokenProvider
from tests.conftest import MockResponse
from tests.generated_connector_test_utils import (
    get_generated_operations,
    invoke_generated_operation,
)


SUCCESS_CONTRACTS = {
    "get_message": ("GET", "/v1/Account/value/Message/value", False),
    "list_messages": ("GET", "/v1/Account/value/Message/", False),
    "make_call": ("POST", "/v1/Account/value/Call/", True),
    "send_sms": ("POST", "/v1/Account/value/Message/", True),
}
ALL_OPERATIONS = list(SUCCESS_CONTRACTS)


class TestPlivoClient:
    """Tests for PlivoClient."""

    def test_init_with_defaults(self):
        """Test initialization with default authentication."""
        client = PlivoClient("https://example.azure.com/connections/test/")

        assert client._connection_runtime_url == "https://example.azure.com/connections/test"
        assert client.connector_name == "plivo"
        assert isinstance(client._http_client._token_provider, ManagedIdentityTokenProvider)

    @pytest.mark.parametrize("connection_runtime_url", ["", None])
    def test_init_with_invalid_url_raises_error(self, connection_runtime_url):
        """Test invalid runtime URLs are rejected."""
        with pytest.raises(ValueError, match="connection_runtime_url cannot be None or empty"):
            PlivoClient(connection_runtime_url)

    @pytest.mark.asyncio
    async def test_context_manager(self, mock_token_provider):
        """Test async context manager cleanup."""
        with patch.object(PlivoClient, "close", new_callable=AsyncMock) as mock_close:
            async with PlivoClient(
                "https://example.azure.com/connections/test",
                token_provider=mock_token_provider,
            ) as client:
                assert isinstance(client, PlivoClient)

        mock_close.assert_called_once()

    def test_all_generated_operations_are_covered(self):
        """Test the expected generated operation surface."""
        assert get_generated_operations(PlivoClient) == set(ALL_OPERATIONS)

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
        mock_token_provider,
    ):
        """Test every generated operation's successful HTTP contract."""
        client = PlivoClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider,
        )

        with patch.object(
            client._http_client,
            "send_async",
            new_callable=AsyncMock,
            return_value=MockResponse(status=200, text='{"ok": true}'),
        ) as mock_send:
            result = await invoke_generated_operation(client, operation, plivo_module)

        method, url = mock_send.call_args.args[:2]
        assert method == expected_method
        assert url.endswith(expected_url_suffix)
        assert (mock_send.call_args.kwargs["body"] is not None) is expects_body
        assert result == {"ok": True}

    @pytest.mark.asyncio
    async def test_send_sms_success(self, mock_token_provider):
        """Test sending an SMS uses the account message route and body."""
        client = PlivoClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider,
        )

        with patch.object(
            client._http_client,
            "send_async",
            new_callable=AsyncMock,
            return_value=MockResponse(status=202, text='{"message_uuid": ["id"]}'),
        ) as mock_send:
            result = await client.send_sms_async(
                input=SMS(src="15550000000", dst="15551111111", text="Hello"),
                auth_id="account/id",
            )

        method, url = mock_send.call_args.args[:2]
        assert method == "POST"
        assert url.endswith("/v1/Account/account%2Fid/Message/")
        assert mock_send.call_args.kwargs["body"].text == "Hello"
        assert result == {"message_uuid": ["id"]}

    @pytest.mark.asyncio
    async def test_make_call_success(self, mock_token_provider):
        """Test making a call sends the generated call model."""
        client = PlivoClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider,
        )

        with patch.object(
            client._http_client,
            "send_async",
            new_callable=AsyncMock,
            return_value=MockResponse(status=201, text='{"request_uuid": "id"}'),
        ) as mock_send:
            await client.make_call_async(
                input=Call(
                    from_="15550000000",
                    to="15551111111",
                    answer_url="https://example.com/answer",
                ),
                auth_id="account",
            )

        assert mock_send.call_args.args[0] == "POST"
        assert mock_send.call_args.kwargs["body"].from_ == "15550000000"

    @pytest.mark.asyncio
    @pytest.mark.parametrize("operation", ALL_OPERATIONS)
    async def test_non_success_response_raises_exception(
        self,
        operation,
        mock_token_provider,
    ):
        """Test every generated operation raises for a non-success response."""
        client = PlivoClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider,
        )

        with patch.object(
            client._http_client,
            "send_async",
            new_callable=AsyncMock,
            return_value=MockResponse(status=400, text="bad request"),
        ):
            with pytest.raises(ConnectorException):
                await invoke_generated_operation(client, operation, plivo_module)
