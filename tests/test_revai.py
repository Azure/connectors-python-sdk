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


SUCCESS_CONTRACTS = {
    "account_get": ("GET", "/speechtotext/v1/account", False),
    "alignment": ("POST", "/alignment/v1/jobs", True),
    "alignment_delete": ("DELETE", "/alignment/v1/jobs/value", False),
    "alignment_get": ("GET", "/alignment/v1/jobs/value", False),
    "alignment_transcript_get": (
        "GET",
        "/alignment/v1/jobs/value/transcript",
        False,
    ),
    "alignments_get": ("GET", "/alignment/v1/jobs", False),
    "analysis": ("POST", "/sentiment_analysis/v1/jobs", True),
    "analysis_delete": ("DELETE", "/sentiment_analysis/v1/jobs/value", False),
    "analysis_get": ("GET", "/sentiment_analysis/v1/jobs/value", False),
    "analysis_result_get": (
        "GET",
        "/sentiment_analysis/v1/jobs/value/result",
        False,
    ),
    "analysises_get": ("GET", "/sentiment_analysis/v1/jobs", False),
    "captions_get": (
        "GET",
        "/speechtotext/v1/jobs/value/captions",
        False,
    ),
    "extraction": ("POST", "/topic_extraction/v1/jobs", True),
    "extraction_delete": ("DELETE", "/topic_extraction/v1/jobs/value", False),
    "extraction_get": ("GET", "/topic_extraction/v1/jobs/value", False),
    "extraction_result_get": (
        "GET",
        "/topic_extraction/v1/jobs/value/result",
        False,
    ),
    "extractions_get": ("GET", "/topic_extraction/v1/jobs", False),
    "identification": ("POST", "/languageid/v1/jobs", True),
    "identification_delete": ("DELETE", "/languageid/v1/jobs/value", False),
    "identification_get": ("GET", "/languageid/v1/jobs/value", False),
    "identification_result_get": (
        "GET",
        "/languageid/v1/jobs/value/result",
        False,
    ),
    "identifications_get": ("GET", "/languageid/v1/jobs", False),
    "transcript_get": (
        "GET",
        "/speechtotext/v1/jobs/value/transcript",
        False,
    ),
    "transcription": ("POST", "/speechtotext/v1/jobs", True),
    "transcription_delete": ("DELETE", "/speechtotext/v1/jobs/value", False),
    "transcription_get": ("GET", "/speechtotext/v1/jobs/value", False),
    "transcriptions_get": ("GET", "/speechtotext/v1/jobs", False),
    "vocabularies_get": ("GET", "/speechtotext/v1/vocabularies", False),
    "vocabulary": ("POST", "/speechtotext/v1/vocabularies", True),
    "vocabulary_delete": (
        "DELETE",
        "/speechtotext/v1/vocabularies/value",
        False,
    ),
    "vocabulary_get": ("GET", "/speechtotext/v1/vocabularies/value", False),
}
ALL_OPERATIONS = list(SUCCESS_CONTRACTS)
NO_RESULT_OPERATIONS = {"analysises_get"}


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
        client = RevaiClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider,
        )

        with patch.object(
            client._http_client,
            "send_async",
            new_callable=AsyncMock,
            return_value=MockResponse(status=200, text='{"ok": true}'),
        ) as mock_send:
            result = await invoke_generated_operation(client, operation, revai_module)

        method, url = mock_send.call_args.args[:2]
        assert method == expected_method
        assert url.endswith(expected_url_suffix)
        assert (mock_send.call_args.kwargs["body"] is not None) is expects_body
        expected_result = None if operation in NO_RESULT_OPERATIONS else {"ok": True}
        assert result == expected_result

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
