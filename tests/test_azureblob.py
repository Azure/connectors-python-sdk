# Copyright (c) Microsoft Corporation. All rights reserved.

"""Unit tests for AzureblobClient."""

import pytest
from unittest.mock import AsyncMock, patch
from azure.connectors.azureblob import (
    AzureblobClient,
    CreateBlockBlobInput,
    CreateFileInput,
    SharedAccessSignatureBlobPolicy,
    UpdateFileInput,
)
from azure.connectors.sdk import (
    ConnectorClientOptions,
    ManagedIdentityTokenProvider,
    ConnectorException,
)
from tests.conftest import MockResponse


class TestAzureblobClientInitialization:
    """Tests for AzureblobClient initialization."""

    def test_init_with_valid_url_and_defaults(self):
        """Test initialization with valid URL and default parameters."""
        client = AzureblobClient("https://example.azure.com/connections/test")

        assert client._connection_runtime_url == "https://example.azure.com/connections/test"
        assert client.connector_name == "azureblob"
        assert isinstance(client._http_client._token_provider, ManagedIdentityTokenProvider)

    def test_init_with_trailing_slash(self):
        """Test that trailing slash is removed from URL."""
        client = AzureblobClient("https://example.azure.com/connections/test/")

        assert client._connection_runtime_url == "https://example.azure.com/connections/test"

    def test_init_with_custom_token_provider(self, mock_token_provider):
        """Test initialization with custom token provider."""
        client = AzureblobClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        assert client._http_client._token_provider is mock_token_provider

    def test_init_with_custom_options(self, mock_token_provider):
        """Test initialization with custom options."""
        options = ConnectorClientOptions(timeout_seconds=60.0, max_retry_attempts=5)
        client = AzureblobClient(
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
            AzureblobClient("")

    def test_init_with_none_url_raises_error(self):
        """Test that None URL raises ValueError."""
        with pytest.raises(ValueError, match="connection_runtime_url cannot be None or empty"):
            AzureblobClient(None)

    def test_connector_name_property(self, mock_token_provider):
        """Test connector_name property returns 'azureblob'."""
        client = AzureblobClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        assert client.connector_name == "azureblob"


class TestAzureblobClientLifecycle:
    """Tests for AzureblobClient lifecycle methods."""

    @pytest.mark.asyncio
    async def test_close(self, mock_token_provider):
        """Test close method calls http_client.close."""
        client = AzureblobClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        with patch.object(client._http_client, 'close', new_callable=AsyncMock) as mock_close:
            await client.close()
            mock_close.assert_called_once()

    @pytest.mark.asyncio
    async def test_context_manager(self, mock_token_provider):
        """Test async context manager functionality."""
        with patch.object(AzureblobClient, 'close', new_callable=AsyncMock) as mock_close:
            async with AzureblobClient(
                "https://example.azure.com/connections/test",
                token_provider=mock_token_provider
            ) as client:
                assert isinstance(client, AzureblobClient)

            mock_close.assert_called_once()


class TestCopyFile:
    """Tests for copy_file_async method."""

    @pytest.mark.asyncio
    async def test_success_with_json_response(self, mock_token_provider):
        """Test successful POST request."""
        client = AzureblobClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(
            status=200,
            text='{"id": "blob123", "name": "copied-file.txt"}'
        )

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ) as mock_send:
            result = await client.copy_file_async(
                dataset="mycontainer",
                source="/source/file.txt",
                destination="/dest/file.txt"
            )

            mock_send.assert_called_once()
            call_args = mock_send.call_args
            assert call_args[0][0] == "POST"
            assert "copyFile" in call_args[0][1]
            assert "source=" in call_args[0][1]
            assert "destination=" in call_args[0][1]
            assert result["id"] == "blob123"

    @pytest.mark.asyncio
    async def test_with_overwrite_parameter(self, mock_token_provider):
        """Test POST request with overwrite parameter."""
        client = AzureblobClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(status=200, text='{}')

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ) as mock_send:
            await client.copy_file_async(
                dataset="mycontainer",
                source="/source/file.txt",
                destination="/dest/file.txt",
                overwrite="true"
            )

            call_args = mock_send.call_args
            assert "overwrite=true" in call_args[0][1]

    @pytest.mark.asyncio
    async def test_empty_response_returns_none(self, mock_token_provider):
        """Test that empty response returns None."""
        client = AzureblobClient(
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
            result = await client.copy_file_async(
                dataset="mycontainer",
                source="/source/file.txt",
                destination="/dest/file.txt"
            )
            assert result is None

    @pytest.mark.asyncio
    async def test_error_response_raises_exception(self, mock_token_provider):
        """Test that error response raises ConnectorException."""
        client = AzureblobClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(status=404, text='{"error": "Blob not found"}')

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ):
            with pytest.raises(ConnectorException) as exc_info:
                await client.copy_file_async(
                    dataset="mycontainer",
                    source="/source/file.txt",
                    destination="/dest/file.txt"
                )

            assert exc_info.value.status_code == 404


class TestCreateBlockBlob:
    """Tests for create_block_blob_async method."""

    @pytest.mark.asyncio
    async def test_success(self, mock_token_provider):
        """Test successful POST request."""
        client = AzureblobClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(status=200, text='{}')
        blob_input = CreateBlockBlobInput()

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ) as mock_send:
            await client.create_block_blob_async(
                input=blob_input,
                storage_account_name="mystorageaccount",
                folder_path="/uploads",
                name="newfile.txt"
            )

            mock_send.assert_called_once()
            call_args = mock_send.call_args
            assert call_args[0][0] == "POST"
            assert "CreateBlockBlob" in call_args[0][1]
            assert "folderPath=" in call_args[0][1]
            assert "name=" in call_args[0][1]


class TestCreateFile:
    """Tests for create_file_async method."""

    @pytest.mark.asyncio
    async def test_success_with_json_response(self, mock_token_provider):
        """Test successful POST request."""
        client = AzureblobClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(
            status=200,
            text='{"id": "blob456", "name": "new-file.txt", "path": "/uploads/new-file.txt"}'
        )
        file_input = CreateFileInput()

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ) as mock_send:
            result = await client.create_file_async(
                input=file_input,
                dataset="mycontainer",
                folder_path="/uploads",
                name="new-file.txt"
            )

            mock_send.assert_called_once()
            call_args = mock_send.call_args
            assert call_args[0][0] == "POST"
            assert "/files" in call_args[0][1]
            assert result["id"] == "blob456"

    @pytest.mark.asyncio
    async def test_error_response_raises_exception(self, mock_token_provider):
        """Test that error response raises ConnectorException."""
        client = AzureblobClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(status=409, text='{"error": "Blob already exists"}')

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ):
            with pytest.raises(ConnectorException) as exc_info:
                await client.create_file_async(
                    input=CreateFileInput(),
                    dataset="mycontainer",
                    folder_path="/uploads",
                    name="existing-file.txt"
                )

            assert exc_info.value.status_code == 409


class TestCreateShareLinkByPath:
    """Tests for create_share_link_by_path_async method."""

    @pytest.mark.asyncio
    async def test_success_with_json_response(self, mock_token_provider):
        """Test successful POST request."""
        client = AzureblobClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(
            status=200,
            text='{"webUrl": "https://storage.blob.core.windows.net/container/file?sv=..."}'
        )
        policy_input = SharedAccessSignatureBlobPolicy()

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ) as mock_send:
            result = await client.create_share_link_by_path_async(
                input=policy_input,
                storage_account_name="mystorageaccount",
                path="/container/file.txt"
            )

            mock_send.assert_called_once()
            call_args = mock_send.call_args
            assert call_args[0][0] == "POST"
            assert "CreateSharedLinkByPath" in call_args[0][1]
            assert "webUrl" in result

    @pytest.mark.asyncio
    async def test_error_response_raises_exception(self, mock_token_provider):
        """Test that error response raises ConnectorException."""
        client = AzureblobClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(status=403, text='{"error": "Access denied"}')

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ):
            with pytest.raises(ConnectorException) as exc_info:
                await client.create_share_link_by_path_async(
                    input=SharedAccessSignatureBlobPolicy(),
                    storage_account_name="mystorageaccount",
                    path="/container/file.txt"
                )

            assert exc_info.value.status_code == 403


class TestDeleteFile:
    """Tests for delete_file_async method."""

    @pytest.mark.asyncio
    async def test_success(self, mock_token_provider):
        """Test successful DELETE request."""
        client = AzureblobClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(status=200, text='')

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ) as mock_send:
            await client.delete_file_async(
                dataset="mycontainer",
                id="blob123"
            )

            mock_send.assert_called_once()
            call_args = mock_send.call_args
            assert call_args[0][0] == "DELETE"
            assert "/files/blob123" in call_args[0][1]


class TestExtractFolder:
    """Tests for extract_folder_async method."""

    @pytest.mark.asyncio
    async def test_success_with_json_response(self, mock_token_provider):
        """Test successful POST request."""
        client = AzureblobClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(
            status=200,
            text='{"extractedFiles": ["file1.txt", "file2.txt"]}'
        )

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ) as mock_send:
            result = await client.extract_folder_async(
                dataset="mycontainer",
                source="/archive.zip",
                destination="/extracted"
            )

            mock_send.assert_called_once()
            call_args = mock_send.call_args
            assert call_args[0][0] == "POST"
            assert "extractFolderV2" in call_args[0][1]
            assert "extractedFiles" in result

    @pytest.mark.asyncio
    async def test_with_overwrite_parameter(self, mock_token_provider):
        """Test POST request with overwrite parameter."""
        client = AzureblobClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(status=200, text='{}')

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ) as mock_send:
            await client.extract_folder_async(
                dataset="mycontainer",
                source="/archive.zip",
                destination="/extracted",
                overwrite="true"
            )

            call_args = mock_send.call_args
            assert "overwrite=true" in call_args[0][1]

    @pytest.mark.asyncio
    async def test_error_response_raises_exception(self, mock_token_provider):
        """Test that error response raises ConnectorException."""
        client = AzureblobClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(status=400, text='{"error": "Invalid archive format"}')

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ):
            with pytest.raises(ConnectorException) as exc_info:
                await client.extract_folder_async(
                    dataset="mycontainer",
                    source="/archive.zip",
                    destination="/extracted"
                )

            assert exc_info.value.status_code == 400


class TestGetAccessPolicies:
    """Tests for get_access_policies_async method."""

    @pytest.mark.asyncio
    async def test_success_with_json_response(self, mock_token_provider):
        """Test successful GET request."""
        client = AzureblobClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(
            status=200,
            text='{"policies": [{"id": "policy1", "permissions": "rwd"}]}'
        )

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ) as mock_send:
            result = await client.get_access_policies_async(
                storage_account_name="mystorageaccount",
                path="/container/file.txt"
            )

            mock_send.assert_called_once()
            call_args = mock_send.call_args
            assert call_args[0][0] == "GET"
            assert "/policies" in call_args[0][1]
            assert "policies" in result

    @pytest.mark.asyncio
    async def test_empty_response_returns_none(self, mock_token_provider):
        """Test that empty response returns None."""
        client = AzureblobClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(status=204, text="")

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ):
            result = await client.get_access_policies_async(
                storage_account_name="mystorageaccount",
                path="/container/file.txt"
            )
            assert result is None

    @pytest.mark.asyncio
    async def test_error_response_raises_exception(self, mock_token_provider):
        """Test that error response raises ConnectorException."""
        client = AzureblobClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(status=404, text='{"error": "Not found"}')

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ):
            with pytest.raises(ConnectorException) as exc_info:
                await client.get_access_policies_async(
                    storage_account_name="mystorageaccount",
                    path="/container/file.txt"
                )

            assert exc_info.value.status_code == 404


class TestGetFileContent:
    """Tests for get_file_content_async method."""

    @pytest.mark.asyncio
    async def test_success_returns_binary_content(self, mock_token_provider):
        """Test successful GET request returns binary content."""
        client = AzureblobClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        binary_content = b'Hello, World! This is blob content.'
        mock_response = MockResponse(status=200, text="", content=binary_content)

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ) as mock_send:
            result = await client.get_file_content_async(
                dataset="mycontainer",
                id="blob123"
            )

            mock_send.assert_called_once()
            call_args = mock_send.call_args
            assert call_args[0][0] == "GET"
            assert "/content" in call_args[0][1]
            assert result == binary_content

    @pytest.mark.asyncio
    async def test_with_infer_content_type_parameter(self, mock_token_provider):
        """Test GET request with inferContentType parameter."""
        client = AzureblobClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(status=200, text="", content=b"content")

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ) as mock_send:
            await client.get_file_content_async(
                dataset="mycontainer",
                id="blob123",
                infer_content_type="true"
            )

            call_args = mock_send.call_args
            assert "inferContentType=true" in call_args[0][1]

    @pytest.mark.asyncio
    async def test_error_response_raises_exception(self, mock_token_provider):
        """Test that error response raises ConnectorException."""
        client = AzureblobClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(status=404, text='{"error": "Blob not found"}')

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ):
            with pytest.raises(ConnectorException) as exc_info:
                await client.get_file_content_async(
                    dataset="mycontainer",
                    id="nonexistent"
                )

            assert exc_info.value.status_code == 404


class TestGetFileContentByPath:
    """Tests for get_file_content_by_path_async method."""

    @pytest.mark.asyncio
    async def test_success_returns_binary_content(self, mock_token_provider):
        """Test successful GET request returns binary content."""
        client = AzureblobClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        binary_content = b'File content retrieved by path.'
        mock_response = MockResponse(status=200, text="", content=binary_content)

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ) as mock_send:
            result = await client.get_file_content_by_path_async(
                dataset="mycontainer",
                path="/folder/file.txt"
            )

            mock_send.assert_called_once()
            call_args = mock_send.call_args
            assert call_args[0][0] == "GET"
            assert "GetFileContentByPath" in call_args[0][1]
            assert result == binary_content

    @pytest.mark.asyncio
    async def test_error_response_raises_exception(self, mock_token_provider):
        """Test that error response raises ConnectorException."""
        client = AzureblobClient(
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
                await client.get_file_content_by_path_async(
                    dataset="mycontainer",
                    path="/nonexistent/path.txt"
                )

            assert exc_info.value.status_code == 404


class TestGetFileMetadata:
    """Tests for get_file_metadata_async method."""

    @pytest.mark.asyncio
    async def test_success_with_json_response(self, mock_token_provider):
        """Test successful GET request."""
        client = AzureblobClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(
            status=200,
            text='{"id": "blob123", "name": "file.txt", "size": 1024, "mediaType": "text/plain"}'
        )

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ) as mock_send:
            result = await client.get_file_metadata_async(
                dataset="mycontainer",
                id="blob123"
            )

            mock_send.assert_called_once()
            call_args = mock_send.call_args
            assert call_args[0][0] == "GET"
            assert "/files/blob123" in call_args[0][1]
            assert result["name"] == "file.txt"
            assert result["size"] == 1024

    @pytest.mark.asyncio
    async def test_empty_response_returns_none(self, mock_token_provider):
        """Test that empty response returns None."""
        client = AzureblobClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(status=204, text="")

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ):
            result = await client.get_file_metadata_async(
                dataset="mycontainer",
                id="blob123"
            )
            assert result is None

    @pytest.mark.asyncio
    async def test_error_response_raises_exception(self, mock_token_provider):
        """Test that error response raises ConnectorException."""
        client = AzureblobClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(status=404, text='{"error": "Blob not found"}')

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ):
            with pytest.raises(ConnectorException) as exc_info:
                await client.get_file_metadata_async(
                    dataset="mycontainer",
                    id="nonexistent"
                )

            assert exc_info.value.status_code == 404


class TestGetFileMetadataByPath:
    """Tests for get_file_metadata_by_path_async method."""

    @pytest.mark.asyncio
    async def test_success_with_json_response(self, mock_token_provider):
        """Test successful GET request."""
        client = AzureblobClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(
            status=200,
            text='{"id": "blob456", "path": "/folder/file.txt", "size": 2048}'
        )

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ) as mock_send:
            result = await client.get_file_metadata_by_path_async(
                dataset="mycontainer",
                path="/folder/file.txt"
            )

            mock_send.assert_called_once()
            call_args = mock_send.call_args
            assert call_args[0][0] == "GET"
            assert "GetFileByPath" in call_args[0][1]
            assert result["path"] == "/folder/file.txt"

    @pytest.mark.asyncio
    async def test_empty_response_returns_none(self, mock_token_provider):
        """Test that empty response returns None."""
        client = AzureblobClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(status=204, text="")

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ):
            result = await client.get_file_metadata_by_path_async(
                dataset="mycontainer",
                path="/folder/file.txt"
            )
            assert result is None

    @pytest.mark.asyncio
    async def test_error_response_raises_exception(self, mock_token_provider):
        """Test that error response raises ConnectorException."""
        client = AzureblobClient(
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
                await client.get_file_metadata_by_path_async(
                    dataset="mycontainer",
                    path="/nonexistent/path.txt"
                )

            assert exc_info.value.status_code == 404


class TestListFolder:
    """Tests for list_folder_async method."""

    @pytest.mark.asyncio
    async def test_success_with_json_response(self, mock_token_provider):
        """Test successful GET request."""
        client = AzureblobClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(
            status=200,
            text='{"value": [{"name": "file1.txt"}, {"name": "file2.txt"}]}'
        )

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ) as mock_send:
            result = await client.list_folder_async(
                dataset="mycontainer",
                id="folder123"
            )

            mock_send.assert_called_once()
            call_args = mock_send.call_args
            assert call_args[0][0] == "GET"
            assert "foldersV2/folder123" in call_args[0][1]
            assert len(result["value"]) == 2

    @pytest.mark.asyncio
    async def test_with_pagination_parameters(self, mock_token_provider):
        """Test GET request with pagination parameters."""
        client = AzureblobClient(
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
            await client.list_folder_async(
                dataset="mycontainer",
                id="folder123",
                next_page_marker="marker123",
                use_flat_listing="true"
            )

            call_args = mock_send.call_args
            assert "nextPageMarker=" in call_args[0][1]
            assert "useFlatListing=true" in call_args[0][1]

    @pytest.mark.asyncio
    async def test_empty_response_returns_none(self, mock_token_provider):
        """Test that empty response returns None."""
        client = AzureblobClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(status=204, text="")

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ):
            result = await client.list_folder_async(
                dataset="mycontainer",
                id="folder123"
            )
            assert result is None

    @pytest.mark.asyncio
    async def test_error_response_raises_exception(self, mock_token_provider):
        """Test that error response raises ConnectorException."""
        client = AzureblobClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(status=404, text='{"error": "Folder not found"}')

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ):
            with pytest.raises(ConnectorException) as exc_info:
                await client.list_folder_async(
                    dataset="mycontainer",
                    id="nonexistent"
                )

            assert exc_info.value.status_code == 404


class TestListRootFolder:
    """Tests for list_root_folder_async method."""

    @pytest.mark.asyncio
    async def test_success_with_json_response(self, mock_token_provider):
        """Test successful GET request."""
        client = AzureblobClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(
            status=200,
            text='{"value": [{"name": "folder1", "isFolder": true}, {"name": "file.txt"}]}'
        )

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ) as mock_send:
            result = await client.list_root_folder_async(dataset="mycontainer")

            mock_send.assert_called_once()
            call_args = mock_send.call_args
            assert call_args[0][0] == "GET"
            assert "foldersV2" in call_args[0][1]
            assert len(result["value"]) == 2

    @pytest.mark.asyncio
    async def test_with_pagination_parameters(self, mock_token_provider):
        """Test GET request with pagination parameters."""
        client = AzureblobClient(
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
            await client.list_root_folder_async(
                dataset="mycontainer",
                next_page_marker="marker456",
                use_flat_listing="false"
            )

            call_args = mock_send.call_args
            assert "nextPageMarker=" in call_args[0][1]
            assert "useFlatListing=false" in call_args[0][1]

    @pytest.mark.asyncio
    async def test_empty_response_returns_none(self, mock_token_provider):
        """Test that empty response returns None."""
        client = AzureblobClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(status=204, text="")

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ):
            result = await client.list_root_folder_async(dataset="mycontainer")
            assert result is None

    @pytest.mark.asyncio
    async def test_error_response_raises_exception(self, mock_token_provider):
        """Test that error response raises ConnectorException."""
        client = AzureblobClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(status=403, text='{"error": "Access denied"}')

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ):
            with pytest.raises(ConnectorException) as exc_info:
                await client.list_root_folder_async(dataset="mycontainer")

            assert exc_info.value.status_code == 403


class TestOnUpdatedFiles:
    """Tests for on_updated_files_async method."""

    @pytest.mark.asyncio
    async def test_success_with_json_response(self, mock_token_provider):
        """Test successful GET request."""
        client = AzureblobClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(
            status=200,
            text='{"value": [{"id": "blob1", "lastModified": "2024-01-15T10:00:00Z"}]}'
        )

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ) as mock_send:
            result = await client.on_updated_files_async(
                dataset="mycontainer",
                folder_id="folder123"
            )

            mock_send.assert_called_once()
            call_args = mock_send.call_args
            assert call_args[0][0] == "GET"
            assert "triggers/batch/onupdatedfile" in call_args[0][1]
            assert "value" in result

    @pytest.mark.asyncio
    async def test_with_all_parameters(self, mock_token_provider):
        """Test GET request with all parameters."""
        client = AzureblobClient(
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
            await client.on_updated_files_async(
                dataset="mycontainer",
                folder_id="folder123",
                max_file_count="10",
                check_both_created_and_modified_date_time="true"
            )

            call_args = mock_send.call_args
            assert "maxFileCount=10" in call_args[0][1]
            assert "checkBothCreatedAndModifiedDateTime=true" in call_args[0][1]

    @pytest.mark.asyncio
    async def test_error_response_raises_exception(self, mock_token_provider):
        """Test that error response raises ConnectorException."""
        client = AzureblobClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(status=500, text='{"error": "Internal Server Error"}')

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ):
            with pytest.raises(ConnectorException) as exc_info:
                await client.on_updated_files_async(
                    dataset="mycontainer",
                    folder_id="folder123"
                )

            assert exc_info.value.status_code == 500


class TestSetBlobTierByPath:
    """Tests for set_blob_tier_by_path_async method."""

    @pytest.mark.asyncio
    async def test_success(self, mock_token_provider):
        """Test successful POST request."""
        client = AzureblobClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(status=200, text='')

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ) as mock_send:
            await client.set_blob_tier_by_path_async(
                storage_account_name="mystorageaccount",
                path="/container/file.txt",
                new_tier="Cool"
            )

            mock_send.assert_called_once()
            call_args = mock_send.call_args
            assert call_args[0][0] == "POST"
            assert "SetBlobTierByPath" in call_args[0][1]
            assert "newTier=Cool" in call_args[0][1]


class TestUpdateFile:
    """Tests for update_file_async method."""

    @pytest.mark.asyncio
    async def test_success_with_json_response(self, mock_token_provider):
        """Test successful PUT request."""
        client = AzureblobClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(
            status=200,
            text='{"id": "blob123", "name": "updated-file.txt", "lastModified": "2024-01-15"}'
        )
        update_input = UpdateFileInput()

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ) as mock_send:
            result = await client.update_file_async(
                input=update_input,
                dataset="mycontainer",
                id="blob123"
            )

            mock_send.assert_called_once()
            call_args = mock_send.call_args
            assert call_args[0][0] == "PUT"
            assert "/files/blob123" in call_args[0][1]
            assert result["name"] == "updated-file.txt"

    @pytest.mark.asyncio
    async def test_empty_response_returns_none(self, mock_token_provider):
        """Test that empty response returns None."""
        client = AzureblobClient(
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
            result = await client.update_file_async(
                input=UpdateFileInput(),
                dataset="mycontainer",
                id="blob123"
            )
            assert result is None

    @pytest.mark.asyncio
    async def test_error_response_raises_exception(self, mock_token_provider):
        """Test that error response raises ConnectorException."""
        client = AzureblobClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(status=404, text='{"error": "Blob not found"}')

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ):
            with pytest.raises(ConnectorException) as exc_info:
                await client.update_file_async(
                    input=UpdateFileInput(),
                    dataset="mycontainer",
                    id="nonexistent"
                )

            assert exc_info.value.status_code == 404
