# Copyright (c) Microsoft Corporation. All rights reserved.

"""Unit tests for OnedriveforbusinessClient."""

from unittest.mock import AsyncMock, patch

import pytest

from azure.connectors.onedriveforbusiness import (
    BlobMetadata,
    BlobMetadataPage,
    ForASelectedFileResponse,
    OnedriveforbusinessClient,
    SharingLink,
    Tags,
    Thumbnail,
)
from azure.connectors.sdk import (
    ConnectorClientOptions,
    ConnectorException,
    ManagedIdentityTokenProvider,
)
from tests.conftest import MockResponse


METHOD_ARGUMENTS: list[tuple[str, dict]] = [
    ("get_file_metadata_async", {"id": "file123"}),
    ("update_file_async", {"id": "file123", "input": b"updated content"}),
    ("delete_file_async", {"id": "file123"}),
    ("get_file_metadata_by_path_async", {"path": "/Documents/file.txt"}),
    ("get_file_content_by_path_async", {"path": "/Documents/file.txt"}),
    ("get_file_content_async", {"id": "file123"}),
    (
        "create_file_async",
        {
            "input": b"file content",
            "folder_path": "/Documents",
            "name": "new.txt",
        },
    ),
    (
        "copy_file_async",
        {"source": "https://contoso.com/file.txt", "destination": "/Documents/copy.txt"},
    ),
    (
        "copy_drive_file_async",
        {"id": "file123", "destination": "/Documents/copy.txt"},
    ),
    (
        "copy_drive_file_by_path_async",
        {"source": "/Documents/source.txt", "destination": "/Documents/copy.txt"},
    ),
    (
        "move_file_async",
        {"id": "file123", "destination": "/Documents/moved.txt"},
    ),
    (
        "move_file_by_path_async",
        {"source": "/Documents/source.txt", "destination": "/Documents/moved.txt"},
    ),
    ("convert_file_async", {"id": "file123"}),
    ("convert_file_by_path_async", {"path": "/Documents/file.docx"}),
    ("get_file_thumbnail_async", {"id": "file123", "size": "small"}),
    ("list_root_folder_async", {}),
    (
        "find_files_async",
        {"id": "folder123", "query": "report", "find_mode": "search"},
    ),
    (
        "find_files_by_path_async",
        {
            "query": "report",
            "path": "/Documents",
            "find_mode": "search",
        },
    ),
    ("create_share_link_async", {"id": "file123", "type_": "view"}),
    (
        "create_share_link_by_path_async",
        {"path": "/Documents/file.txt", "type_": "view"},
    ),
    (
        "extract_folder_async",
        {"source": "/Documents/archive.zip", "destination": "/Documents/extracted"},
    ),
    ("list_folder_async", {"id": "folder123"}),
]


class TestOnedriveforbusinessClientInitialization:
    """Tests for OnedriveforbusinessClient initialization."""

    def test_init_with_valid_url_and_defaults(self):
        """Test initialization with valid URL and default parameters."""
        client = OnedriveforbusinessClient("https://example.azure.com/connections/test")

        assert client._connection_runtime_url == "https://example.azure.com/connections/test"
        assert client.connector_name == "onedriveforbusiness"
        assert isinstance(client._http_client._token_provider, ManagedIdentityTokenProvider)

    def test_init_with_custom_token_provider(self, mock_token_provider):
        """Test initialization with custom token provider."""
        client = OnedriveforbusinessClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider,
        )

        assert client._http_client._token_provider is mock_token_provider

    def test_init_with_custom_options(self, mock_token_provider):
        """Test initialization with custom options."""
        options = ConnectorClientOptions(timeout_seconds=60.0, max_retry_attempts=5)
        client = OnedriveforbusinessClient(
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
            OnedriveforbusinessClient("")

    def test_init_with_none_url_raises_error(self):
        """Test that None URL raises ValueError."""
        with pytest.raises(ValueError, match="connection_runtime_url cannot be None or empty"):
            OnedriveforbusinessClient(None)  # type: ignore[arg-type]


class TestOnedriveforbusinessClientLifecycle:
    """Tests for OnedriveforbusinessClient lifecycle methods."""

    @pytest.mark.asyncio
    async def test_close(self, mock_token_provider):
        """Test close method calls http_client.close."""
        client = OnedriveforbusinessClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider,
        )

        with patch.object(client._http_client, "close", new_callable=AsyncMock) as mock_close:
            await client.close()
            mock_close.assert_called_once()

    @pytest.mark.asyncio
    async def test_context_manager(self, mock_token_provider):
        """Test async context manager functionality."""
        with patch.object(OnedriveforbusinessClient, "close", new_callable=AsyncMock) as mock_close:
            async with OnedriveforbusinessClient(
                "https://example.azure.com/connections/test",
                token_provider=mock_token_provider,
            ) as client:
                assert isinstance(client, OnedriveforbusinessClient)

            mock_close.assert_called_once()


class TestOnedriveforbusinessClientMethods:
    """Tests for representative connector methods."""

    @pytest.mark.asyncio
    async def test_get_file_metadata_success(self, mock_token_provider):
        """Test successful JSON response for file metadata."""
        client = OnedriveforbusinessClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider,
        )
        mock_response = MockResponse(status=200, text='{"id": "file123", "name": "doc.txt"}')

        with patch.object(
            client._http_client,
            "send_async",
            new_callable=AsyncMock,
            return_value=mock_response,
        ) as mock_send:
            result = await client.get_file_metadata_async(id="file123")

            assert result["id"] == "file123"
            assert result["name"] == "doc.txt"
            assert mock_send.call_args[0][0] == "GET"
            assert "/datasets/default/files/file123" in mock_send.call_args[0][1]

    @pytest.mark.asyncio
    async def test_get_file_content_returns_bytes(self, mock_token_provider):
        """Test that content endpoints return bytes."""
        client = OnedriveforbusinessClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider,
        )
        content = b"file-content"
        mock_response = MockResponse(status=200, content=content)

        with patch.object(
            client._http_client,
            "send_async",
            new_callable=AsyncMock,
            return_value=mock_response,
        ):
            result = await client.get_file_content_async(id="file123")

            assert result == content

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "method_name,kwargs",
        METHOD_ARGUMENTS,
        ids=[method_name for method_name, _ in METHOD_ARGUMENTS],
    )
    async def test_all_methods_raise_connector_exception_on_error(
        self,
        method_name: str,
        kwargs: dict,
        mock_token_provider,
    ):
        """Test that all generated methods raise ConnectorException on HTTP errors."""
        client = OnedriveforbusinessClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider,
        )
        mock_response = MockResponse(status=500, text='{"error": "server error"}')

        with patch.object(
            client._http_client,
            "send_async",
            new_callable=AsyncMock,
            return_value=mock_response,
        ):
            method = getattr(client, method_name)
            with pytest.raises(ConnectorException) as exc_info:
                await method(**kwargs)

            assert exc_info.value.status_code == 500


class TestOnedriveforbusinessTypeDefinitions:
    """Tests for generated type definitions."""

    def test_type_instantiation(self):
        """Test dataclass types can be instantiated with expected properties."""
        metadata = BlobMetadata(id="file123", name="doc.txt")
        page = BlobMetadataPage(value=[metadata], next_link="https://next")
        sharing_link = SharingLink(web_url="https://contoso")
        tags = Tags(tags=["important", "finance"])
        thumbnail = Thumbnail(url="https://thumb", width=64, height=64)
        selected = ForASelectedFileResponse(file_path="/Documents/doc.txt")

        assert metadata.id == "file123"
        assert page.value[0].name == "doc.txt"
        assert sharing_link.web_url == "https://contoso"
        assert tags.tags == ["important", "finance"]
        assert thumbnail.width == 64
        assert selected.file_path == "/Documents/doc.txt"
