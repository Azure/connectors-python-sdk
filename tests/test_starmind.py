# Copyright (c) Microsoft Corporation. All rights reserved.

"""Unit tests for StarmindClient."""

from unittest.mock import AsyncMock, patch

import pytest

import azure.connectors.starmind as starmind_module
from azure.connectors.sdk import ConnectorException, ManagedIdentityTokenProvider
from azure.connectors.starmind import (
    FindExpertsInput,
    PostQuestionDraftInput,
    StarmindClient,
)
from tests.conftest import MockResponse
from tests.generated_connector_test_utils import (
    get_generated_operations,
    invoke_generated_operation,
)


ALL_OPERATIONS = [
    "find_experts",
    "find_questions",
    "get_user_by_id",
    "post_question_draft",
    "publish_question_draft",
]


class TestStarmindClient:
    """Tests for StarmindClient."""

    def test_init_with_defaults(self):
        """Test initialization with default authentication."""
        client = StarmindClient("https://example.azure.com/connections/test/")

        assert client._connection_runtime_url == "https://example.azure.com/connections/test"
        assert client.connector_name == "starmind"
        assert isinstance(client._http_client._token_provider, ManagedIdentityTokenProvider)

    @pytest.mark.parametrize("connection_runtime_url", ["", None])
    def test_init_with_invalid_url_raises_error(self, connection_runtime_url):
        """Test invalid runtime URLs are rejected."""
        with pytest.raises(ValueError, match="connection_runtime_url cannot be None or empty"):
            StarmindClient(connection_runtime_url)

    @pytest.mark.asyncio
    async def test_context_manager(self, mock_token_provider):
        """Test async context manager cleanup."""
        with patch.object(StarmindClient, "close", new_callable=AsyncMock) as mock_close:
            async with StarmindClient(
                "https://example.azure.com/connections/test",
                token_provider=mock_token_provider,
            ) as client:
                assert isinstance(client, StarmindClient)

        mock_close.assert_called_once()

    def test_all_generated_operations_are_covered(self):
        """Test the expected generated operation surface."""
        assert get_generated_operations(StarmindClient) == set(ALL_OPERATIONS)

    @pytest.mark.asyncio
    async def test_find_experts_success(self, mock_token_provider):
        """Test expert search sends the generated query body."""
        client = StarmindClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider,
        )

        with patch.object(
            client._http_client,
            "send_async",
            new_callable=AsyncMock,
            return_value=MockResponse(status=200, text='{"experts": []}'),
        ) as mock_send:
            result = await client.find_experts_async(
                input=FindExpertsInput(text_query="distributed systems"),
            )

        assert mock_send.call_args.args[0] == "POST"
        assert mock_send.call_args.args[1].endswith("/api/v3/experts")
        assert mock_send.call_args.kwargs["body"].text_query == "distributed systems"
        assert result == {"experts": []}

    @pytest.mark.asyncio
    async def test_post_question_draft_success(self, mock_token_provider):
        """Test posting a question draft uses the questions route."""
        client = StarmindClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider,
        )

        with patch.object(
            client._http_client,
            "send_async",
            new_callable=AsyncMock,
            return_value=MockResponse(status=201, text='{"id": 42}'),
        ) as mock_send:
            await client.post_question_draft_async(
                input=PostQuestionDraftInput(
                    title="How does this work?",
                    description="Looking for an expert explanation.",
                ),
            )

        assert mock_send.call_args.args[0] == "POST"
        assert mock_send.call_args.args[1].endswith("/api/v3/questions")

    @pytest.mark.asyncio
    @pytest.mark.parametrize("operation", ALL_OPERATIONS)
    async def test_non_success_response_raises_exception(
        self,
        operation,
        mock_token_provider,
    ):
        """Test every generated operation raises for a non-success response."""
        client = StarmindClient(
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
                await invoke_generated_operation(client, operation, starmind_module)
