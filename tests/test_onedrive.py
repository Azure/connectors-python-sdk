# Copyright (c) Microsoft Corporation. All rights reserved.

"""Unit tests for OnedriveClient."""

import pytest
from unittest.mock import AsyncMock, patch
from azure.connectors.onedrive import (
    OnedriveClient,
    BlobMetadata,
    BlobMetadataPage,
    CreateFileInput,
    UpdateFileInput,
    SharingLink,
    Tags,
    Thumbnail,
)
from azure.connectors.sdk import (
    ConnectorClientOptions,
    ManagedIdentityTokenProvider,
    ConnectorException,
)
from tests.conftest import MockResponse


class TestOnedriveClientInitialization:
    """Tests for OnedriveClient initialization."""

    def test_init_with_valid_url_and_defaults(self):
        """Test initialization with valid URL and default parameters."""
        client = OnedriveClient("https://example.azure.com/connections/test")

        assert client._connection_runtime_url == "https://example.azure.com/connections/test"
        assert client.connector_name == "onedrive"
        assert isinstance(client._http_client._token_provider, ManagedIdentityTokenProvider)

    def test_init_with_trailing_slash(self):
        """Test that trailing slash is removed from URL."""
        client = OnedriveClient("https://example.azure.com/connections/test/")

        assert client._connection_runtime_url == "https://example.azure.com/connections/test"

    def test_init_with_custom_token_provider(self, mock_token_provider):
        """Test initialization with custom token provider."""
        client = OnedriveClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        assert client._http_client._token_provider is mock_token_provider

    def test_init_with_custom_options(self, mock_token_provider):
        """Test initialization with custom options."""
        options = ConnectorClientOptions(timeout_seconds=60.0, max_retry_attempts=5)
        client = OnedriveClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider,
            options=options
        )

        assert client._options is options
        assert client._options.timeout_seconds == 60.0
        assert client._options.max_retry_attempts == 5

    def test_init_with_empty_url_raises_error(self):
        """Test that empty URL raises ValueError."""
        with pytest.raises(ValueError, match="connection_runtime_url cannot be None or empty"):
            OnedriveClient("")

    def test_init_with_none_url_raises_error(self):
        """Test that None URL raises ValueError."""
        with pytest.raises(ValueError, match="connection_runtime_url cannot be None or empty"):
            OnedriveClient(None)

    def test_connector_name_property(self, mock_token_provider):
        """Test connector_name property returns 'onedrive'."""
        client = OnedriveClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        assert client.connector_name == "onedrive"


class TestOnedriveClientLifecycle:
    """Tests for OnedriveClient lifecycle methods."""

    @pytest.mark.asyncio
    async def test_close(self, mock_token_provider):
        """Test close method calls http_client.close."""
        client = OnedriveClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        with patch.object(client._http_client, 'close', new_callable=AsyncMock) as mock_close:
            await client.close()
            mock_close.assert_called_once()

    @pytest.mark.asyncio
    async def test_context_manager(self, mock_token_provider):
        """Test async context manager functionality."""
        with patch.object(OnedriveClient, 'close', new_callable=AsyncMock) as mock_close:
            async with OnedriveClient(
                "https://example.azure.com/connections/test",
                token_provider=mock_token_provider
            ) as client:
                assert isinstance(client, OnedriveClient)

            mock_close.assert_called_once()


class TestGetFileMetadata:
    """Tests for get_file_metadata_async method."""

    @pytest.mark.asyncio
    async def test_success_with_json_response(self, mock_token_provider):
        """Test successful GET request."""
        client = OnedriveClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(
            status=200,
            text='{"id": "file123", "name": "document.docx", "size": 1024}'
        )

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ) as mock_send:
            result = await client.get_file_metadata_async(id="file123")

            mock_send.assert_called_once()
            call_args = mock_send.call_args
            assert call_args[0][0] == "GET"
            assert "/files/file123" in call_args[0][1]
            assert result["name"] == "document.docx"

    @pytest.mark.asyncio
    async def test_empty_response_returns_none(self, mock_token_provider):
        """Test that empty response returns None."""
        client = OnedriveClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(status=200, text="")

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ):
            result = await client.get_file_metadata_async(id="file123")

            assert result is None

    @pytest.mark.asyncio
    async def test_error_response_raises_exception(self, mock_token_provider):
        """Test that error response raises ConnectorException."""
        client = OnedriveClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(status=404, text='{"error": "File not found"}')

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ):
            with pytest.raises(ConnectorException) as exc_info:
                await client.get_file_metadata_async(id="nonexistent")

            assert exc_info.value.status_code == 404


class TestGetFileContent:
    """Tests for get_file_content_async method."""

    @pytest.mark.asyncio
    async def test_success_returns_binary_content(self, mock_token_provider):
        """Test successful GET request returns binary content."""
        client = OnedriveClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        binary_content = b'Hello, OneDrive! This is file content.'
        # NOTE(sdk): Method uses response.text.encode('latin-1') so we provide text as string.
        mock_response = MockResponse(status=200, text=binary_content.decode('latin-1'))

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ) as mock_send:
            result = await client.get_file_content_async(id="file123")

            mock_send.assert_called_once()
            call_args = mock_send.call_args
            assert call_args[0][0] == "GET"
            assert "/content" in call_args[0][1]
            assert result == binary_content

    @pytest.mark.asyncio
    async def test_with_infer_content_type_parameter(self, mock_token_provider):
        """Test GET request with inferContentType parameter."""
        client = OnedriveClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        # NOTE(sdk): Method uses response.text.encode('latin-1') so we provide text as string.
        mock_response = MockResponse(status=200, text="content")

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ) as mock_send:
            await client.get_file_content_async(
                id="file123",
                infer_content_type="true"
            )

            call_args = mock_send.call_args
            assert "inferContentType=true" in call_args[0][1]

    @pytest.mark.asyncio
    async def test_error_response_raises_exception(self, mock_token_provider):
        """Test that error response raises ConnectorException."""
        client = OnedriveClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(status=404, text='{"error": "File not found"}')

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ):
            with pytest.raises(ConnectorException) as exc_info:
                await client.get_file_content_async(id="nonexistent")

            assert exc_info.value.status_code == 404


class TestGetFileContentByPath:
    """Tests for get_file_content_by_path_async method."""

    @pytest.mark.asyncio
    async def test_success_returns_binary_content(self, mock_token_provider):
        """Test successful GET request returns binary content."""
        client = OnedriveClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        binary_content = b'File content retrieved by path.'
        # NOTE(sdk): Method uses response.text.encode('latin-1') so we provide text as string.
        mock_response = MockResponse(status=200, text=binary_content.decode('latin-1'))

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ) as mock_send:
            result = await client.get_file_content_by_path_async(
                path="/Documents/file.txt"
            )

            mock_send.assert_called_once()
            call_args = mock_send.call_args
            assert call_args[0][0] == "GET"
            assert "GetFileContentByPath" in call_args[0][1]
            assert result == binary_content

    @pytest.mark.asyncio
    async def test_error_response_raises_exception(self, mock_token_provider):
        """Test that error response raises ConnectorException."""
        client = OnedriveClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(status=404, text='{"error": "Path not found"}')

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ):
            with pytest.raises(ConnectorException) as exc_info:
                await client.get_file_content_by_path_async(path="/invalid/path")

            assert exc_info.value.status_code == 404


class TestCreateFile:
    """Tests for create_file_async method."""

    @pytest.mark.asyncio
    async def test_success_with_json_response(self, mock_token_provider):
        """Test successful POST request."""
        client = OnedriveClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(
            status=201,
            text='{"id": "newfile123", "name": "newfile.txt"}'
        )

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ) as mock_send:
            input_data = CreateFileInput()
            result = await client.create_file_async(
                input=input_data,
                folder_path="/Documents",
                name="newfile.txt"
            )

            mock_send.assert_called_once()
            call_args = mock_send.call_args
            assert call_args[0][0] == "POST"
            assert "folderPath=" in call_args[0][1]
            assert "name=" in call_args[0][1]
            assert result["id"] == "newfile123"

    @pytest.mark.asyncio
    async def test_error_response_raises_exception(self, mock_token_provider):
        """Test that error response raises ConnectorException."""
        client = OnedriveClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(status=400, text='{"error": "Invalid folder path"}')

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ):
            with pytest.raises(ConnectorException) as exc_info:
                await client.create_file_async(
                    input=CreateFileInput(),
                    folder_path="/invalid",
                    name="file.txt"
                )

            assert exc_info.value.status_code == 400


class TestUpdateFile:
    """Tests for update_file_async method."""

    @pytest.mark.asyncio
    async def test_success_with_json_response(self, mock_token_provider):
        """Test successful PUT request."""
        client = OnedriveClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(
            status=200,
            text='{"id": "file123", "name": "updated.txt"}'
        )

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ) as mock_send:
            input_data = UpdateFileInput()
            result = await client.update_file_async(
                input=input_data,
                id="file123"
            )

            mock_send.assert_called_once()
            call_args = mock_send.call_args
            assert call_args[0][0] == "PUT"
            assert "/files/file123" in call_args[0][1]
            assert result["name"] == "updated.txt"

    @pytest.mark.asyncio
    async def test_error_response_raises_exception(self, mock_token_provider):
        """Test that error response raises ConnectorException."""
        client = OnedriveClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(status=404, text='{"error": "File not found"}')

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ):
            with pytest.raises(ConnectorException) as exc_info:
                await client.update_file_async(
                    input=UpdateFileInput(),
                    id="nonexistent"
                )

            assert exc_info.value.status_code == 404


class TestDeleteFile:
    """Tests for delete_file_async method."""

    @pytest.mark.asyncio
    async def test_success_returns_none(self, mock_token_provider):
        """Test successful DELETE request."""
        client = OnedriveClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(status=204, text="")

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ) as mock_send:
            await client.delete_file_async(id="file123")

            mock_send.assert_called_once()
            call_args = mock_send.call_args
            assert call_args[0][0] == "DELETE"
            assert "/files/file123" in call_args[0][1]

    @pytest.mark.asyncio
    async def test_error_response_raises_exception(self, mock_token_provider):
        """Test that error response raises ConnectorException."""
        client = OnedriveClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(status=404, text='{"error": "File not found"}')

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ):
            with pytest.raises(ConnectorException) as exc_info:
                await client.delete_file_async(id="nonexistent")

            assert exc_info.value.status_code == 404


class TestCopyFile:
    """Tests for copy_file_async method."""

    @pytest.mark.asyncio
    async def test_success_with_json_response(self, mock_token_provider):
        """Test successful POST request."""
        client = OnedriveClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(
            status=200,
            text='{"id": "copiedfile123", "name": "file_copy.txt"}'
        )

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ) as mock_send:
            result = await client.copy_file_async(
                source="https://example.com/source.txt",
                destination="/Documents/destination.txt"
            )

            mock_send.assert_called_once()
            call_args = mock_send.call_args
            assert call_args[0][0] == "POST"
            assert "copyFile" in call_args[0][1]
            assert "source=" in call_args[0][1]
            assert "destination=" in call_args[0][1]
            assert result["id"] == "copiedfile123"

    @pytest.mark.asyncio
    async def test_with_overwrite_parameter(self, mock_token_provider):
        """Test POST request with overwrite parameter."""
        client = OnedriveClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(status=200, text='{"id": "file123"}')

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ) as mock_send:
            await client.copy_file_async(
                source="https://example.com/source.txt",
                destination="/Documents/destination.txt",
                overwrite="true"
            )

            call_args = mock_send.call_args
            assert "overwrite=true" in call_args[0][1]

    @pytest.mark.asyncio
    async def test_error_response_raises_exception(self, mock_token_provider):
        """Test that error response raises ConnectorException."""
        client = OnedriveClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(status=400, text='{"error": "Invalid destination"}')

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ):
            with pytest.raises(ConnectorException) as exc_info:
                await client.copy_file_async(
                    source="invalid",
                    destination="invalid"
                )

            assert exc_info.value.status_code == 400


class TestCopyDriveFile:
    """Tests for copy_drive_file_async method."""

    @pytest.mark.asyncio
    async def test_success_with_json_response(self, mock_token_provider):
        """Test successful POST request."""
        client = OnedriveClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(
            status=200,
            text='{"id": "copiedfile123", "name": "file_copy.txt"}'
        )

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ) as mock_send:
            result = await client.copy_drive_file_async(
                id="sourcefile123",
                destination="/Documents/copy.txt"
            )

            mock_send.assert_called_once()
            call_args = mock_send.call_args
            assert call_args[0][0] == "POST"
            assert "/copy" in call_args[0][1]
            assert "destination=" in call_args[0][1]
            assert result["id"] == "copiedfile123"

    @pytest.mark.asyncio
    async def test_error_response_raises_exception(self, mock_token_provider):
        """Test that error response raises ConnectorException."""
        client = OnedriveClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(status=404, text='{"error": "Source file not found"}')

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ):
            with pytest.raises(ConnectorException) as exc_info:
                await client.copy_drive_file_async(
                    id="nonexistent",
                    destination="/Documents/copy.txt"
                )

            assert exc_info.value.status_code == 404


class TestMoveFile:
    """Tests for move_file_async method."""

    @pytest.mark.asyncio
    async def test_success_with_json_response(self, mock_token_provider):
        """Test successful POST request."""
        client = OnedriveClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(
            status=200,
            text='{"id": "file123", "name": "moved_file.txt", "path": "/Archive/moved_file.txt"}'
        )

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ) as mock_send:
            result = await client.move_file_async(
                id="file123",
                destination="/Archive/moved_file.txt"
            )

            mock_send.assert_called_once()
            call_args = mock_send.call_args
            assert call_args[0][0] == "POST"
            assert "/move" in call_args[0][1]
            assert "destination=" in call_args[0][1]
            assert result["path"] == "/Archive/moved_file.txt"

    @pytest.mark.asyncio
    async def test_error_response_raises_exception(self, mock_token_provider):
        """Test that error response raises ConnectorException."""
        client = OnedriveClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(status=404, text='{"error": "File not found"}')

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ):
            with pytest.raises(ConnectorException) as exc_info:
                await client.move_file_async(
                    id="nonexistent",
                    destination="/Archive/file.txt"
                )

            assert exc_info.value.status_code == 404


class TestListFolder:
    """Tests for list_folder_async method."""

    @pytest.mark.asyncio
    async def test_success_with_json_response(self, mock_token_provider):
        """Test successful GET request."""
        client = OnedriveClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(
            status=200,
            text='{"value": [{"id": "file1", "name": "doc1.txt"}, '
                 '{"id": "file2", "name": "doc2.txt"}]}'
        )

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ) as mock_send:
            result = await client.list_folder_async(id="folder123")

            mock_send.assert_called_once()
            call_args = mock_send.call_args
            assert call_args[0][0] == "GET"
            assert "/foldersV2/folder123" in call_args[0][1]
            assert len(result["value"]) == 2

    @pytest.mark.asyncio
    async def test_with_default_pagination_query_parameters(self, mock_token_provider):
        """Test GET request includes default pagination query parameters."""
        client = OnedriveClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(status=200, text='{"value": []}')

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ) as mock_send:
            await client.list_folder_async(id="folder123")

            call_args = mock_send.call_args
            assert "skipToken=" in call_args[0][1]
            assert "top=20" in call_args[0][1]


class TestListRootFolder:
    """Tests for list_root_folder_async method."""

    @pytest.mark.asyncio
    async def test_success_with_json_response(self, mock_token_provider):
        """Test successful GET request."""
        client = OnedriveClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(
            status=200,
            text='{"value": [{"id": "folder1", "name": "Documents"}, '
                 '{"id": "folder2", "name": "Pictures"}]}'
        )

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ) as mock_send:
            result = await client.list_root_folder_async()

            mock_send.assert_called_once()
            call_args = mock_send.call_args
            assert call_args[0][0] == "GET"
            assert "/folders" in call_args[0][1]
            assert len(result["value"]) == 2


class TestFindFiles:
    """Tests for find_files_async method."""

    @pytest.mark.asyncio
    async def test_success_with_json_response(self, mock_token_provider):
        """Test successful GET request."""
        client = OnedriveClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(
            status=200,
            text='{"value": [{"id": "file1", "name": "report.docx"}]}'
        )

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ) as mock_send:
            result = await client.find_files_async(
                id="folder123",
                query="report",
                find_mode="search"
            )

            mock_send.assert_called_once()
            call_args = mock_send.call_args
            assert call_args[0][0] == "GET"
            assert "/search" in call_args[0][1]
            assert "query=report" in call_args[0][1]
            assert len(result["value"]) == 1


class TestCreateShareLink:
    """Tests for create_share_link_async method."""

    @pytest.mark.asyncio
    async def test_success_with_json_response(self, mock_token_provider):
        """Test successful POST request."""
        client = OnedriveClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(
            status=200,
            text='{"webUrl": "https://onedrive.live.com/share/abc123"}'
        )

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ) as mock_send:
            result = await client.create_share_link_async(
                id="file123",
                type_="view"
            )

            mock_send.assert_called_once()
            call_args = mock_send.call_args
            assert call_args[0][0] == "POST"
            assert "/shareV2" in call_args[0][1]
            assert "type=view" in call_args[0][1]
            assert "onedrive.live.com" in result["webUrl"]


class TestGetFileTags:
    """Tests for get_file_tags_async method."""

    @pytest.mark.asyncio
    async def test_success_with_json_response(self, mock_token_provider):
        """Test successful GET request."""
        client = OnedriveClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(
            status=200,
            text='{"tags": ["important", "work", "2026"]}'
        )

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ) as mock_send:
            result = await client.get_file_tags_async(id="file123")

            mock_send.assert_called_once()
            call_args = mock_send.call_args
            assert call_args[0][0] == "GET"
            assert "/tags" in call_args[0][1]
            assert "important" in result["tags"]


class TestAddFileTag:
    """Tests for add_file_tag_async method."""

    @pytest.mark.asyncio
    async def test_success_with_json_response(self, mock_token_provider):
        """Test successful POST request."""
        client = OnedriveClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(
            status=200,
            text='{"tags": ["important", "work", "new-tag"]}'
        )

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ) as mock_send:
            await client.add_file_tag_async(
                id="file123",
                tag="new-tag"
            )

            mock_send.assert_called_once()
            call_args = mock_send.call_args
            assert call_args[0][0] == "POST"
            assert "/tags" in call_args[0][1]
            assert "tag=new-tag" in call_args[0][1]


class TestRemoveFileTag:
    """Tests for remove_file_tag_async method."""

    @pytest.mark.asyncio
    async def test_success_returns_none(self, mock_token_provider):
        """Test successful DELETE request."""
        client = OnedriveClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(status=204, text="")

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ) as mock_send:
            await client.remove_file_tag_async(
                id="file123",
                tag="old-tag"
            )

            mock_send.assert_called_once()
            call_args = mock_send.call_args
            assert call_args[0][0] == "DELETE"
            assert "/tags" in call_args[0][1]
            assert "tag=old-tag" in call_args[0][1]


class TestGetFileThumbnail:
    """Tests for get_file_thumbnail_async method."""

    @pytest.mark.asyncio
    async def test_success_with_json_response(self, mock_token_provider):
        """Test successful GET request."""
        client = OnedriveClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(
            status=200,
            text='{"url": "https://thumbnail.url/image.jpg", "width": 200, "height": 150}'
        )

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ) as mock_send:
            result = await client.get_file_thumbnail_async(
                id="file123",
                size="medium"
            )

            mock_send.assert_called_once()
            call_args = mock_send.call_args
            assert call_args[0][0] == "GET"
            assert "/thumbnail" in call_args[0][1]
            assert "size=medium" in call_args[0][1]
            assert result["width"] == 200


class TestConvertFile:
    """Tests for convert_file_async method."""

    @pytest.mark.asyncio
    async def test_success_returns_binary_content(self, mock_token_provider):
        """Test successful GET request returns binary content."""
        client = OnedriveClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        binary_content = b'%PDF-1.4 converted content'
        # NOTE(sdk): Method uses response.text.encode('latin-1') so we provide text as string.
        mock_response = MockResponse(status=200, text=binary_content.decode('latin-1'))

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ) as mock_send:
            result = await client.convert_file_async(
                id="file123",
                type_="pdf"
            )

            mock_send.assert_called_once()
            call_args = mock_send.call_args
            assert call_args[0][0] == "GET"
            assert "/convert" in call_args[0][1]
            assert "type=pdf" in call_args[0][1]
            assert result == binary_content


class TestExtractFolder:
    """Tests for extract_folder_async method."""

    @pytest.mark.asyncio
    async def test_success_with_json_response(self, mock_token_provider):
        """Test successful POST request."""
        client = OnedriveClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(
            status=200,
            text='{"id": "folder123", "name": "extracted"}'
        )

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ) as mock_send:
            await client.extract_folder_async(
                source="/Documents/archive.zip",
                destination="/Documents/extracted"
            )

            mock_send.assert_called_once()
            call_args = mock_send.call_args
            assert call_args[0][0] == "POST"
            assert "extractFolderV2" in call_args[0][1]
            assert "source=" in call_args[0][1]
            assert "destination=" in call_args[0][1]


class TestDataClasses:
    """Tests for OneDrive dataclasses."""

    def test_blob_metadata_creation(self):
        """Test BlobMetadata dataclass creation."""
        metadata = BlobMetadata(
            id="file123",
            name="document.docx",
            path="/Documents/document.docx",
            size=1024,
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            is_folder=False
        )

        assert metadata.id == "file123"
        assert metadata.name == "document.docx"
        assert metadata.size == 1024
        assert metadata.is_folder is False

    def test_blob_metadata_page_creation(self):
        """Test BlobMetadataPage dataclass creation."""
        page = BlobMetadataPage(
            value=[
                BlobMetadata(id="file1", name="doc1.txt"),
                BlobMetadata(id="file2", name="doc2.txt")
            ],
            next_link="https://api.onedrive.com/next?token=abc"
        )

        assert len(page.value) == 2
        assert page.next_link is not None

    def test_sharing_link_creation(self):
        """Test SharingLink dataclass creation."""
        link = SharingLink(web_url="https://onedrive.live.com/share/abc123")

        assert "onedrive.live.com" in link.web_url

    def test_tags_creation(self):
        """Test Tags dataclass creation."""
        tags = Tags(tags=["important", "work", "2026"])

        assert len(tags.tags) == 3
        assert "important" in tags.tags

    def test_thumbnail_creation(self):
        """Test Thumbnail dataclass creation."""
        thumbnail = Thumbnail(
            url="https://thumbnail.url/image.jpg",
            width=200,
            height=150
        )

        assert thumbnail.width == 200
        assert thumbnail.height == 150


class TestEdgeCases:
    """Tests for edge cases and error handling."""

    @pytest.mark.asyncio
    async def test_special_characters_in_path(self, mock_token_provider):
        """Test handling of special characters in file paths."""
        client = OnedriveClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(status=200, text='{"id": "file123"}')

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ) as mock_send:
            await client.get_file_metadata_by_path_async(
                path="/Documents/My File (2026).docx"
            )

            call_args = mock_send.call_args
            # URL should be encoded
            assert "path=" in call_args[0][1]

    @pytest.mark.asyncio
    async def test_multiple_consecutive_calls(self, mock_token_provider):
        """Test multiple consecutive API calls."""
        client = OnedriveClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(status=200, text='{"id": "file123"}')

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ):
            await client.get_file_metadata_async(id="file1")
            await client.get_file_metadata_async(id="file2")
            await client.get_file_metadata_async(id="file3")

            assert client._http_client.send_async.call_count == 3

    @pytest.mark.asyncio
    async def test_http_client_property_access(self, mock_token_provider):
        """Test that http_client property is accessible."""
        client = OnedriveClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        assert client.http_client is not None
        assert client._http_client is client.http_client
