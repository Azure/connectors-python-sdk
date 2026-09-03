# Copyright (c) Microsoft Corporation. All rights reserved.

"""Unit tests for FtpClient."""

import pytest
from unittest.mock import AsyncMock, patch

from azure.connectors.ftp import (
    BlobMetadata,
    BlobMetadataPage,
    FtpClient,
)
from azure.connectors.sdk import (
    ConnectorClientOptions,
    ConnectorException,
    ManagedIdentityTokenProvider,
)
from tests.conftest import MockResponse


async def _invoke_operation(client: FtpClient, operation: str):
    """Invoke an FTP operation by name for shared error tests."""
    if operation == "create_file":
        return await client.create_file_async(
            input=b"file content",
            folder_path="/inbound",
            name="sample.txt",
        )
    if operation == "get_file_metadata":
        return await client.get_file_metadata_async(id="file123")
    if operation == "update_file":
        return await client.update_file_async(input=b"updated content", id="file123")
    if operation == "delete_file":
        return await client.delete_file_async(id="file123")
    if operation == "copy_file":
        return await client.copy_file_async(
            source="/inbound/sample.txt",
            destination="/archive/sample.txt",
            overwrite="true",
        )
    if operation == "get_file_metadata_by_path":
        return await client.get_file_metadata_by_path_async(path="/inbound/sample.txt")
    if operation == "get_file_content_by_path":
        return await client.get_file_content_by_path_async(path="/inbound/sample.txt")
    if operation == "get_file_content":
        return await client.get_file_content_async(id="file123")
    if operation == "list_folder":
        return await client.list_folder_async(id="folder123")
    if operation == "list_root_folder":
        return await client.list_root_folder_async()
    if operation == "extract_folder":
        return await client.extract_folder_async(
            source="/inbound/archive.zip",
            destination="/expanded",
            overwrite="true",
            create_folders="true",
        )

    raise ValueError(f"Unsupported operation '{operation}'.")


class TestFtpClientInitialization:
    """Tests for FtpClient initialization."""

    def test_init_with_valid_url_and_defaults(self):
        """Test initialization with valid URL and default parameters."""
        client = FtpClient("https://example.azure.com/connections/test")

        assert client._connection_runtime_url == "https://example.azure.com/connections/test"
        assert client.connector_name == "ftp"
        assert isinstance(client._http_client._token_provider, ManagedIdentityTokenProvider)

    def test_init_with_trailing_slash(self):
        """Test that trailing slash is removed from URL."""
        client = FtpClient("https://example.azure.com/connections/test/")

        assert client._connection_runtime_url == "https://example.azure.com/connections/test"

    def test_init_with_custom_token_provider(self, mock_token_provider):
        """Test initialization with custom token provider."""
        client = FtpClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider,
        )

        assert client._http_client._token_provider is mock_token_provider

    def test_init_with_custom_options(self, mock_token_provider):
        """Test initialization with custom options."""
        options = ConnectorClientOptions(timeout_seconds=60.0, max_retry_attempts=5)
        client = FtpClient(
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
            FtpClient("")

    def test_init_with_none_url_raises_error(self):
        """Test that None URL raises ValueError."""
        with pytest.raises(ValueError, match="connection_runtime_url cannot be None or empty"):
            FtpClient(None)

    def test_connector_name_property(self, mock_token_provider):
        """Test connector_name property returns 'ftp'."""
        client = FtpClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider,
        )

        assert client.connector_name == "ftp"


class TestFtpClientLifecycle:
    """Tests for FtpClient lifecycle methods."""

    @pytest.mark.asyncio
    async def test_close(self, mock_token_provider):
        """Test close method calls http_client.close."""
        client = FtpClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider,
        )

        with patch.object(client._http_client, "close", new_callable=AsyncMock) as mock_close:
            await client.close()
            mock_close.assert_called_once()

    @pytest.mark.asyncio
    async def test_context_manager(self, mock_token_provider):
        """Test async context manager functionality."""
        with patch.object(FtpClient, "close", new_callable=AsyncMock) as mock_close:
            async with FtpClient(
                "https://example.azure.com/connections/test",
                token_provider=mock_token_provider,
            ) as client:
                assert isinstance(client, FtpClient)

            mock_close.assert_called_once()


class TestFtpClientMethods:
    """Success path tests for representative FTP methods."""

    @pytest.mark.asyncio
    async def test_create_file_success(self, mock_token_provider):
        """Test create_file_async sends query parameters and body."""
        client = FtpClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider,
        )
        mock_response = MockResponse(status=201, text='{"id":"new1","name":"sample.txt"}')

        with patch.object(
            client._http_client,
            "send_async",
            new_callable=AsyncMock,
            return_value=mock_response,
        ) as mock_send:
            result = await client.create_file_async(
                input=b"file content",
                folder_path="/inbound",
                name="sample.txt",
            )

            assert result["id"] == "new1"
            call_args = mock_send.call_args
            assert call_args[0][0] == "POST"
            assert "folderPath=/inbound" in call_args[0][1]
            assert call_args.kwargs["body"] == b"file content"

    @pytest.mark.asyncio
    async def test_get_file_metadata_success(self, mock_token_provider):
        """Test get_file_metadata_async returns parsed JSON."""
        client = FtpClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider,
        )
        mock_response = MockResponse(status=200, text='{"id":"file123","name":"sample.txt"}')

        with patch.object(
            client._http_client,
            "send_async",
            new_callable=AsyncMock,
            return_value=mock_response,
        ) as mock_send:
            result = await client.get_file_metadata_async(id="file123")

            assert result["name"] == "sample.txt"
            assert "/datasets/default/files/file123" in mock_send.call_args[0][1]

    @pytest.mark.asyncio
    async def test_get_file_content_by_path_success(self, mock_token_provider):
        """Test get_file_content_by_path_async returns bytes content."""
        client = FtpClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider,
        )
        mock_response = MockResponse(status=200, content=b"ftp file content")

        with patch.object(
            client._http_client,
            "send_async",
            new_callable=AsyncMock,
            return_value=mock_response,
        ):
            result = await client.get_file_content_by_path_async(path="/inbound/sample.txt")

            assert result == b"ftp file content"

    @pytest.mark.asyncio
    async def test_list_root_folder_success(self, mock_token_provider):
        """Test list_root_folder_async returns parsed JSON response."""
        client = FtpClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider,
        )
        mock_response = MockResponse(status=200, text='{"value":[{"name":"inbound"}]}')

        with patch.object(
            client._http_client,
            "send_async",
            new_callable=AsyncMock,
            return_value=mock_response,
        ):
            result = await client.list_root_folder_async()

            assert len(result["value"]) == 1
            assert result["value"][0]["name"] == "inbound"

    @pytest.mark.asyncio
    async def test_extract_folder_success(self, mock_token_provider):
        """Test extract_folder_async serializes extraction query parameters."""
        client = FtpClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider,
        )
        mock_response = MockResponse(status=200, text='{"status":"ok"}')

        with patch.object(
            client._http_client,
            "send_async",
            new_callable=AsyncMock,
            return_value=mock_response,
        ) as mock_send:
            result = await client.extract_folder_async(
                source="/inbound/archive.zip",
                destination="/expanded",
                overwrite="true",
                create_folders="true",
            )

            call_path = mock_send.call_args[0][1]
            assert "source=/inbound/archive.zip" in call_path
            assert "destination=/expanded" in call_path
            assert result["status"] == "ok"


class TestFtpClientErrorHandling:
    """Error handling tests that ensure all operations raise ConnectorException."""

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "operation",
        [
            "create_file",
            "get_file_metadata",
            "update_file",
            "delete_file",
            "copy_file",
            "get_file_metadata_by_path",
            "get_file_content_by_path",
            "get_file_content",
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
        """Test non-2xx responses raise ConnectorException for each operation."""
        client = FtpClient(
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


class TestFtpTypeSerialization:
    """Tests for FTP connector dataclass defaults."""

    def test_dataclass_instances_initialize_expected_defaults(self):
        """Test generated dataclasses initialize with expected default values."""
        metadata = BlobMetadata()
        page = BlobMetadataPage()
        assert metadata.id is None
        assert page.value is None
