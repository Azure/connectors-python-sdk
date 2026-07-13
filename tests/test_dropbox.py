# Copyright (c) Microsoft Corporation. All rights reserved.

"""Unit tests for DropboxClient."""

import pytest
from unittest.mock import AsyncMock, patch

from azure.connectors.dropbox import (
    BlobMetadata,
    BlobMetadataPage,
    CreateFileInput,
    DropboxClient,
    UpdateFileInput,
)
from azure.connectors.sdk import (
    ConnectorClientOptions,
    ConnectorException,
    ManagedIdentityTokenProvider,
)
from tests.conftest import MockResponse


async def _invoke_operation(client: DropboxClient, operation: str):
    """Invoke a Dropbox operation by name for shared parameterized tests."""
    if operation == "get_file_metadata":
        return await client.get_file_metadata_async(id="file123")
    if operation == "update_file":
        return await client.update_file_async(input=UpdateFileInput(), id="file123")
    if operation == "delete_file":
        return await client.delete_file_async(id="file123")
    if operation == "get_file_metadata_by_path":
        return await client.get_file_metadata_by_path_async(path="/Documents/file.txt")
    if operation == "get_file_content_by_path":
        return await client.get_file_content_by_path_async(path="/Documents/file.txt")
    if operation == "get_file_content":
        return await client.get_file_content_async(id="file123")
    if operation == "create_file":
        return await client.create_file_async(
            input=CreateFileInput(),
            folder_path="/Documents",
            name="created.txt",
        )
    if operation == "copy_file":
        return await client.copy_file_async(
            source="/Documents/source.txt",
            destination="/Documents/copy.txt",
        )
    if operation == "on_new_file":
        return await client.on_new_file_async(folder_id="folder123")
    if operation == "on_updated_file":
        return await client.on_updated_file_async(folder_id="folder123")
    if operation == "on_new_files":
        return await client.on_new_files_async(folder_id="folder123")
    if operation == "on_updated_files":
        return await client.on_updated_files_async(folder_id="folder123")
    if operation == "list_folder":
        return await client.list_folder_async(id="folder123")
    if operation == "list_root_folder":
        return await client.list_root_folder_async()
    if operation == "extract_folder":
        return await client.extract_folder_async(
            source="/Documents/archive.zip",
            destination="/Documents/extracted",
        )

    raise ValueError(f"Unsupported operation '{operation}'.")


class TestDropboxClientInitialization:
    """Tests for DropboxClient initialization."""

    def test_init_with_valid_url_and_defaults(self):
        """Test initialization with valid URL and default parameters."""
        client = DropboxClient("https://example.azure.com/connections/test")

        assert client._connection_runtime_url == "https://example.azure.com/connections/test"
        assert client.connector_name == "dropbox"
        assert isinstance(client._http_client._token_provider, ManagedIdentityTokenProvider)

    def test_init_with_trailing_slash(self):
        """Test that trailing slash is removed from URL."""
        client = DropboxClient("https://example.azure.com/connections/test/")

        assert client._connection_runtime_url == "https://example.azure.com/connections/test"

    def test_init_with_custom_token_provider(self, mock_token_provider):
        """Test initialization with custom token provider."""
        client = DropboxClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider,
        )

        assert client._http_client._token_provider is mock_token_provider

    def test_init_with_custom_options(self, mock_token_provider):
        """Test initialization with custom options."""
        options = ConnectorClientOptions(timeout_seconds=60.0, max_retry_attempts=5)
        client = DropboxClient(
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
            DropboxClient("")

    def test_init_with_none_url_raises_error(self):
        """Test that None URL raises ValueError."""
        with pytest.raises(ValueError, match="connection_runtime_url cannot be None or empty"):
            DropboxClient(None)

    def test_connector_name_property(self, mock_token_provider):
        """Test connector_name property returns 'dropbox'."""
        client = DropboxClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider,
        )

        assert client.connector_name == "dropbox"


class TestDropboxClientLifecycle:
    """Tests for DropboxClient lifecycle methods."""

    @pytest.mark.asyncio
    async def test_close(self, mock_token_provider):
        """Test close method calls http_client.close."""
        client = DropboxClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider,
        )

        with patch.object(client._http_client, "close", new_callable=AsyncMock) as mock_close:
            await client.close()
            mock_close.assert_called_once()

    @pytest.mark.asyncio
    async def test_context_manager(self, mock_token_provider):
        """Test async context manager functionality."""
        with patch.object(DropboxClient, "close", new_callable=AsyncMock) as mock_close:
            async with DropboxClient(
                "https://example.azure.com/connections/test",
                token_provider=mock_token_provider,
            ) as client:
                assert isinstance(client, DropboxClient)

            mock_close.assert_called_once()


class TestDropboxClientMethods:
    """Success path tests for representative Dropbox methods."""

    @pytest.mark.asyncio
    async def test_get_file_metadata_success(self, mock_token_provider):
        """Test get_file_metadata_async returns parsed JSON."""
        client = DropboxClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider,
        )
        mock_response = MockResponse(status=200, text='{"id":"file123","name":"doc.txt"}')

        with patch.object(
            client._http_client,
            "send_async",
            new_callable=AsyncMock,
            return_value=mock_response,
        ) as mock_send:
            result = await client.get_file_metadata_async(id="file123")

            assert result["name"] == "doc.txt"
            call_args = mock_send.call_args
            assert call_args[0][0] == "GET"
            assert "/datasets/default/files/file123" in call_args[0][1]

    @pytest.mark.asyncio
    async def test_get_file_content_by_path_success(self, mock_token_provider):
        """Test get_file_content_by_path_async returns bytes content."""
        client = DropboxClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider,
        )
        mock_response = MockResponse(status=200, content=b"dropbox file content")

        with patch.object(
            client._http_client,
            "send_async",
            new_callable=AsyncMock,
            return_value=mock_response,
        ):
            result = await client.get_file_content_by_path_async(path="/Documents/file.txt")

            assert result == b"dropbox file content"

    @pytest.mark.asyncio
    async def test_create_file_success(self, mock_token_provider):
        """Test create_file_async sends query params and body."""
        client = DropboxClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider,
        )
        mock_response = MockResponse(status=201, text='{"id":"new1","name":"created.txt"}')

        with patch.object(
            client._http_client,
            "send_async",
            new_callable=AsyncMock,
            return_value=mock_response,
        ) as mock_send:
            result = await client.create_file_async(
                input=CreateFileInput(),
                folder_path="/Documents",
                name="created.txt",
            )

            assert result["id"] == "new1"
            call_args = mock_send.call_args
            assert call_args[0][0] == "POST"
            assert "folderPath=/Documents" in call_args[0][1]
            assert "name=created.txt" in call_args[0][1]

    @pytest.mark.asyncio
    async def test_on_new_file_success(self, mock_token_provider):
        """Test on_new_file_async returns binary callback content."""
        client = DropboxClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider,
        )
        mock_response = MockResponse(status=200, content=b"event payload")

        with patch.object(
            client._http_client,
            "send_async",
            new_callable=AsyncMock,
            return_value=mock_response,
        ) as mock_send:
            result = await client.on_new_file_async(folder_id="folder123")

            assert result == b"event payload"
            call_args = mock_send.call_args
            assert "/triggers/onnewfile" in call_args[0][1]

    @pytest.mark.asyncio
    async def test_on_new_files_success(self, mock_token_provider):
        """Test on_new_files_async serializes trigger query parameters."""
        client = DropboxClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider,
        )
        mock_response = MockResponse(status=200, text='{"value": []}')

        with patch.object(
            client._http_client,
            "send_async",
            new_callable=AsyncMock,
            return_value=mock_response,
        ) as mock_send:
            await client.on_new_files_async(folder_id="folder123", max_file_count="20")

            call_args = mock_send.call_args
            assert "folderId=folder123" in call_args[0][1]
            assert "maxFileCount=20" in call_args[0][1]


class TestDropboxClientErrorHandling:
    """Error handling tests that ensure all methods raise ConnectorException."""

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "operation",
        [
            "get_file_metadata",
            "update_file",
            "delete_file",
            "get_file_metadata_by_path",
            "get_file_content_by_path",
            "get_file_content",
            "create_file",
            "copy_file",
            "on_new_file",
            "on_updated_file",
            "on_new_files",
            "on_updated_files",
            "list_folder",
            "list_root_folder",
            "extract_folder",
        ],
    )
    async def test_error_response_raises_exception_for_all_operations(
        self,
        mock_token_provider,
        operation,
    ):
        """Test non-2xx responses raise ConnectorException for every operation."""
        client = DropboxClient(
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
                await _invoke_operation(client, operation)

            assert exc_info.value.status_code == 500


class TestDropboxTypeSerialization:
    """Tests for Dropbox connector dataclass type behavior."""

    def test_dataclass_instances_initialize_expected_defaults(self):
        """Test generated dataclasses initialize with expected default values."""
        metadata = BlobMetadata()
        page = BlobMetadataPage()
        create_input = CreateFileInput()
        update_input = UpdateFileInput()

        assert metadata.id is None
        assert page.value is None
        assert create_input.additional_properties == {}
        assert update_input.additional_properties == {}
