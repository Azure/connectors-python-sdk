# Copyright (c) Microsoft Corporation. All rights reserved.

"""Unit tests for the asynchronous connector HTTP client."""

import json
from dataclasses import dataclass, field
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from azure.core.pipeline.transport import AsyncHttpTransport

from azure.connectors.sdk.exceptions import ConnectorException
from azure.connectors.sdk.http_client import ConnectorHttpClient, ConnectorResponse
from azure.connectors.sdk.response import ConnectorResponseSnapshot


@dataclass
class TestDataClass:
    """Test dataclass for body serialization."""

    name: str
    value: int
    optional: str | None = None


@dataclass
class WireNamedChild:
    """Nested dataclass with a wire-named attribute."""

    child_value: str | None = field(
        default=None,
        metadata={"wire_name": "childValue"},
    )


@dataclass
class WireNamedParent:
    """Dataclass with wire names, nested values, and extensions."""

    parent_name: str | None = field(
        default=None,
        metadata={"wire_name": "parentName"},
    )
    child: WireNamedChild | None = None
    children: list[WireNamedChild] | None = None
    additional_properties: dict[str, object] | None = None


def create_snapshot(
    status: int = 200,
    *,
    text: str = "{}",
    headers: dict[str, str] | None = None,
) -> ConnectorResponseSnapshot:
    """Create a completed connector response snapshot."""
    return ConnectorResponseSnapshot(
        status=status,
        headers=headers or {},
        text=text,
        content=text.encode("utf-8"),
    )


class TestConnectorResponse:
    """Tests for the legacy generic response wrapper."""

    def test_init_with_all_parameters(self) -> None:
        """Store status, headers, and value."""
        headers = {"Content-Type": "application/json"}
        response = ConnectorResponse[dict[str, str]](
            status_code=200,
            headers=headers,
            value={"key": "value"},
        )

        assert response.status_code == 200
        assert response.headers == headers
        assert response.value == {"key": "value"}

    @pytest.mark.parametrize(
        "status_code, expected",
        [(199, False), (200, True), (299, True), (300, False), (500, False)],
    )
    def test_is_success_status_code(
        self,
        status_code: int,
        expected: bool,
    ) -> None:
        """Classify only 2xx responses as successful."""
        response = ConnectorResponse[None](status_code, {}, None)

        assert response.is_success_status_code is expected


class TestConnectorHttpClient:
    """Tests for ConnectorHttpClient."""

    def test_init_uses_direct_settings(self, mock_credential) -> None:
        """Store the credential, transport, timeout, and retry opt-in."""
        transport = AsyncMock(spec=AsyncHttpTransport)
        client = ConnectorHttpClient(
            mock_credential,
            timeout_seconds=45.0,
            retry_unsafe_http_methods=True,
            transport=transport,
        )

        assert client._credential is mock_credential
        assert client._transport is transport
        assert client._timeout_seconds == 45.0
        assert client._retry_unsafe_http_methods is True

    def test_init_rejects_none_credential(self) -> None:
        """Reject a missing Azure Core credential."""
        with pytest.raises(ValueError, match="credential cannot be None"):
            ConnectorHttpClient(None)

    def test_api_hub_scopes_constant(self) -> None:
        """Keep the fixed API Hub token scope."""
        assert ConnectorHttpClient.API_HUB_SCOPES == [
            "https://apihub.azure.com/.default"
        ]

    @pytest.mark.asyncio
    async def test_close_closes_transport_not_credential(self, mock_credential) -> None:
        """Release owned transport resources without closing caller credentials."""
        transport = AsyncMock(spec=AsyncHttpTransport)
        mock_credential.close = AsyncMock()
        client = ConnectorHttpClient(mock_credential, transport=transport)

        await client.close()

        transport.close.assert_awaited_once()
        mock_credential.close.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_send_async_serializes_dataclass_body(self, mock_credential) -> None:
        """Serialize dataclasses as JSON and omit None fields."""
        client = ConnectorHttpClient(mock_credential)
        body = TestDataClass(name="test", value=42)

        with patch.object(
            client,
            "_send_with_retry",
            new_callable=AsyncMock,
            return_value=create_snapshot(),
        ) as mock_send:
            await client.send_async(
                "POST",
                "https://api.example.com/items",
                body=body,
            )

        call = mock_send.await_args
        assert json.loads(call.args[4]) == {"name": "test", "value": 42}
        assert call.args[3]["Content-Type"] == "application/json"

    @pytest.mark.asyncio
    async def test_send_async_preserves_wire_names_and_extensions(
        self,
        mock_credential,
    ) -> None:
        """Serialize nested wire names and merge additional properties."""
        client = ConnectorHttpClient(mock_credential)
        body = WireNamedParent(
            parent_name="root",
            child=WireNamedChild(child_value="one"),
            children=[WireNamedChild(child_value="two")],
            additional_properties={"extension": True},
        )

        with patch.object(
            client,
            "_send_with_retry",
            new_callable=AsyncMock,
            return_value=create_snapshot(),
        ) as mock_send:
            await client.send_async(
                "POST",
                "https://api.example.com/items",
                body=body,
            )

        assert json.loads(mock_send.await_args.args[4]) == {
            "parentName": "root",
            "child": {"childValue": "one"},
            "children": [{"childValue": "two"}],
            "extension": True,
        }

    @pytest.mark.asyncio
    async def test_send_async_serializes_dict_and_none_bodies(
        self,
        mock_credential,
    ) -> None:
        """Serialize dictionary bodies and preserve an absent body."""
        client = ConnectorHttpClient(mock_credential)

        with patch.object(
            client,
            "_send_with_retry",
            new_callable=AsyncMock,
            return_value=create_snapshot(),
        ) as mock_send:
            await client.send_async(
                "POST",
                "https://api.example.com/items",
                body={"key": "value"},
            )
            await client.send_async(
                "GET",
                "https://api.example.com/items",
                body=None,
            )

        assert json.loads(mock_send.await_args_list[0].args[4]) == {"key": "value"}
        assert mock_send.await_args_list[1].args[4] is None

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "content_type, expected_content_type",
        [
            (None, "application/octet-stream"),
            ("application/pdf", "application/pdf"),
        ],
    )
    async def test_send_async_sends_binary_body_verbatim(
        self,
        mock_credential,
        content_type: str | None,
        expected_content_type: str,
    ) -> None:
        """Send bytes unchanged with the inferred or explicit content type."""
        client = ConnectorHttpClient(mock_credential)
        body = b"\x00\x01binary\xff"

        with patch.object(
            client,
            "_send_with_retry",
            new_callable=AsyncMock,
            return_value=create_snapshot(),
        ) as mock_send:
            await client.send_async(
                "POST",
                "https://api.example.com/upload",
                body=body,
                content_type=content_type,
            )

        call = mock_send.await_args
        assert call.args[3]["Content-Type"] == expected_content_type
        assert call.args[4] == body

    @pytest.mark.asyncio
    async def test_send_async_filters_protected_headers(self, mock_credential) -> None:
        """Prevent callers from replacing authentication and request identity."""
        client = ConnectorHttpClient(mock_credential)

        with patch.object(
            client,
            "_send_with_retry",
            new_callable=AsyncMock,
            return_value=create_snapshot(),
        ) as mock_send:
            await client.send_async(
                "GET",
                "https://api.example.com/items",
                headers={
                    "Authorization": "ignored",
                    "Content-Type": "ignored",
                    "x-ms-client-request-id": "ignored",
                    "x-custom": "value",
                },
            )

        assert mock_send.await_args.args[3] == {
            "x-custom": "value",
            "Content-Type": "application/json",
        }

    @pytest.mark.asyncio
    async def test_send_async_forwards_controls_and_invokes_hook(
        self,
        mock_credential,
    ) -> None:
        """Forward timeout and request ID and invoke the response hook."""
        client = ConnectorHttpClient(mock_credential)
        response = create_snapshot(headers={"x-result": "complete"})
        hook = MagicMock()

        with patch.object(
            client,
            "_send_with_retry",
            new_callable=AsyncMock,
            return_value=response,
        ) as mock_send:
            result = await client.send_async(
                "GET",
                "https://api.example.com/items",
                timeout=5.0,
                client_request_id="request-id",
                response_hook=hook,
            )

        assert mock_send.await_args.kwargs == {
            "client_request_id": "request-id",
            "timeout": 5.0,
        }
        hook.assert_called_once_with(response, response.headers)
        assert result is response

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "method_name, expected_method, arguments",
        [
            ("get_async", "GET", ("https://api.example.com/item",)),
            (
                "post_async",
                "POST",
                ("https://api.example.com/item", {"name": "item"}),
            ),
        ],
    )
    async def test_json_helpers_return_successful_payloads(
        self,
        mock_credential,
        method_name: str,
        expected_method: str,
        arguments: tuple[object, ...],
    ) -> None:
        """Deserialize successful GET and POST helper responses."""
        client = ConnectorHttpClient(mock_credential)
        client.send_async = AsyncMock(
            return_value=create_snapshot(text='{"name": "item"}')
        )

        result = await getattr(client, method_name)(*arguments)

        assert result == {"name": "item"}
        assert client.send_async.await_args.args[0] == expected_method

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "method_name, expected_method, arguments",
        [
            ("get_async", "GET", ("https://api.example.com/item",)),
            (
                "post_async",
                "POST",
                ("https://api.example.com/item", {"name": "item"}),
            ),
        ],
    )
    async def test_json_helpers_raise_for_non_success(
        self,
        mock_credential,
        method_name: str,
        expected_method: str,
        arguments: tuple[object, ...],
    ) -> None:
        """Raise ConnectorException for non-success helper responses."""
        client = ConnectorHttpClient(mock_credential)
        client.send_async = AsyncMock(
            return_value=create_snapshot(status=404, text="missing")
        )

        with pytest.raises(ConnectorException) as exc_info:
            await getattr(client, method_name)(*arguments)

        assert exc_info.value.method == expected_method
        assert exc_info.value.path == "https://api.example.com/item"
        assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    @pytest.mark.parametrize("method_name", ["get_async", "post_async"])
    async def test_json_helpers_return_none_for_empty_body(
        self,
        mock_credential,
        method_name: str,
    ) -> None:
        """Return None for a successful response without content."""
        client = ConnectorHttpClient(mock_credential)
        client.send_async = AsyncMock(return_value=create_snapshot(text=""))
        arguments = (
            ("https://api.example.com/item", {})
            if method_name == "post_async"
            else ("https://api.example.com/item",)
        )

        result = await getattr(client, method_name)(*arguments)

        assert result is None
