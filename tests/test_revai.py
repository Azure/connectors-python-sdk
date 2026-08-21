# Copyright (c) Microsoft Corporation. All rights reserved.

"""Unit tests for RevaiClient."""

from unittest.mock import AsyncMock, patch

import pytest

import azure.connectors.revai as revai_module
from azure.connectors.revai import AlignmentInput, RevaiClient, TranscriptionInput
from azure.connectors.sdk import ConnectorException, ManagedIdentityTokenProvider
from tests.conftest import MockResponse
from tests.generated_connector_test_utils import (
    get_generated_operations,
    invoke_generated_operation,
)


ALL_OPERATIONS = [
    "account_get",
    "alignment",
    "alignment_delete",
    "alignment_get",
    "alignment_transcript_get",
    "alignments_get",
    "analysis",
    "analysis_delete",
    "analysis_get",
    "analysis_result_get",
    "analysises_get",
    "captions_get",
    "extraction",
    "extraction_delete",
    "extraction_get",
    "extraction_result_get",
    "extractions_get",
    "identification",
    "identification_delete",
    "identification_get",
    "identification_result_get",
    "identifications_get",
    "transcript_get",
    "transcription",
    "transcription_delete",
    "transcription_get",
    "transcriptions_get",
    "vocabularies_get",
    "vocabulary",
    "vocabulary_delete",
    "vocabulary_get",
]


class TestRevaiClient:
    """Tests for RevaiClient."""

    def test_init_with_defaults(self):
        """Test initialization with default authentication."""
        client = RevaiClient("https://example.azure.com/connections/test/")

        assert client._connection_runtime_url == "https://example.azure.com/connections/test"
        assert client.connector_name == "revai"
        assert isinstance(client._http_client._token_provider, ManagedIdentityTokenProvider)

    @pytest.mark.parametrize("connection_runtime_url", ["", None])
    def test_init_with_invalid_url_raises_error(self, connection_runtime_url):
        """Test invalid runtime URLs are rejected."""
        with pytest.raises(ValueError, match="connection_runtime_url cannot be None or empty"):
            RevaiClient(connection_runtime_url)

    @pytest.mark.asyncio
    async def test_context_manager(self, mock_token_provider):
        """Test async context manager cleanup."""
        with patch.object(RevaiClient, "close", new_callable=AsyncMock) as mock_close:
            async with RevaiClient(
                "https://example.azure.com/connections/test",
                token_provider=mock_token_provider,
            ) as client:
                assert isinstance(client, RevaiClient)

        mock_close.assert_called_once()

    def test_all_generated_operations_are_covered(self):
        """Test the expected generated operation surface."""
        assert get_generated_operations(RevaiClient) == set(ALL_OPERATIONS)

    @pytest.mark.asyncio
    async def test_create_transcription_success(self, mock_token_provider):
        """Test creating a transcription sends the generated request model."""
        client = RevaiClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider,
        )

        with patch.object(
            client._http_client,
            "send_async",
            new_callable=AsyncMock,
            return_value=MockResponse(status=200, text='{"id": "job-1"}'),
        ) as mock_send:
            result = await client.transcription_async(
                input=TranscriptionInput(
                    source_config={"url": "https://example.com/audio.wav"},
                    metadata="sample",
                ),
            )

        method, url = mock_send.call_args.args[:2]
        assert method == "POST"
        assert url.endswith("/speechtotext/v1/jobs")
        assert mock_send.call_args.kwargs["body"].metadata == "sample"
        assert result == {"id": "job-1"}

    @pytest.mark.asyncio
    async def test_alignment_success(self, mock_token_provider):
        """Test creating an alignment uses the alignment jobs route."""
        client = RevaiClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider,
        )

        with patch.object(
            client._http_client,
            "send_async",
            new_callable=AsyncMock,
            return_value=MockResponse(status=200, text='{"id": "alignment-1"}'),
        ) as mock_send:
            await client.alignment_async(
                input=AlignmentInput(
                    source_config={"url": "https://example.com/audio.wav"},
                    transcript_text="Hello world",
                ),
            )

        assert mock_send.call_args.args[0] == "POST"
        assert mock_send.call_args.args[1].endswith("/alignment/v1/jobs")
        assert mock_send.call_args.kwargs["body"].transcript_text == "Hello world"

    @pytest.mark.asyncio
    async def test_empty_response_returns_none(self, mock_token_provider):
        """Test an empty successful response returns None."""
        client = RevaiClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider,
        )

        with patch.object(
            client._http_client,
            "send_async",
            new_callable=AsyncMock,
            return_value=MockResponse(status=204, text=""),
        ):
            result = await client.account_get_async()

        assert result is None

    @pytest.mark.asyncio
    @pytest.mark.parametrize("operation", ALL_OPERATIONS)
    async def test_non_success_response_raises_exception(
        self,
        operation,
        mock_token_provider,
    ):
        """Test every generated operation raises for a non-success response."""
        client = RevaiClient(
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
                await invoke_generated_operation(client, operation, revai_module)
