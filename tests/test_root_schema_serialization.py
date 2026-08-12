"""Serialization tests for generated root schema definitions."""

from __future__ import annotations

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from azure.connectors.sdk.http_client import ConnectorHttpClient
from azure.connectors.sdk.options import ConnectorClientOptions
from azure.connectors.sdk.serialization import to_wire
from azure.connectors.signinghub import HandSignature, ValidationRule
from azure.connectors.teams import (
    ChannelWithOwnerTeamId,
    ChatMessage,
    ChatMessageList,
)


def test_string_enum_root_serializes_as_swagger_string() -> None:
    """Test that a string enum root preserves its Swagger scalar shape."""
    value: ValidationRule = "MANDATORY"

    emitted_json = json.dumps(to_wire(value))

    assert emitted_json == '"MANDATORY"'


def test_integer_enum_root_serializes_as_swagger_integer() -> None:
    """Test that an integer enum root preserves its Swagger scalar shape."""
    value: HandSignature = 2

    emitted_json = json.dumps(to_wire(value))

    assert emitted_json == "2"


def test_array_root_serializes_as_swagger_array() -> None:
    """Test that an array root emits an array instead of an object wrapper."""
    messages: ChatMessageList = [ChatMessage(id="message-1")]

    emitted_json = json.dumps(to_wire(messages), separators=(",", ":"))

    assert emitted_json == '[{"id":"message-1"}]'


@pytest.mark.asyncio
async def test_array_root_is_serialized_through_send_async(
    mock_token_provider,
) -> None:
    """Test that send_async serializes a top-level array of generated models."""
    mock_token_provider.get_access_token_async = AsyncMock(return_value="token")
    client = ConnectorHttpClient(mock_token_provider, ConnectorClientOptions())
    mock_response = MagicMock(status=200, headers={})
    mock_response.text = AsyncMock(return_value="{}")
    messages: ChatMessageList = [ChatMessage(id="message-1")]

    try:
        with patch.object(
            client,
            "_send_with_retry",
            new_callable=AsyncMock,
            return_value=mock_response,
        ) as mock_send:
            await client.send_async(
                "POST",
                "https://api.example.com/messages",
                body=messages,
            )

        emitted_json = mock_send.call_args.args[4]
        assert emitted_json == '[{"id": "message-1"}]'
    finally:
        await client.close()


def test_all_of_root_serializes_inherited_and_inline_fields() -> None:
    """Test that an allOf root emits both inherited and inline properties."""
    channel = ChannelWithOwnerTeamId(
        id="channel-1",
        display_name="General",
        owner_team_id="team-1",
    )

    emitted_json = json.dumps(
        to_wire(channel),
        separators=(",", ":"),
        sort_keys=True,
    )

    assert emitted_json == (
        '{"displayName":"General","id":"channel-1","ownerTeamId":"team-1"}'
    )
