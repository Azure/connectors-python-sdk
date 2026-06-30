# Copyright (c) Microsoft Corporation. All rights reserved.

"""Unit tests for SharepointonlineClient."""

import json
import pytest
from unittest.mock import AsyncMock, patch
from azure.connectors.sharepointonline import (
    SharepointonlineClient,
    CreateFileInput,
    UpdateFileInput,
    PostItemInput,
    PatchItemInput,
    CreateApprovalRequestInput,
    CreateAttachmentInput,
    FileCheckInParameters,
    ItemPermissionCreateLinkBody,
    ItemGrantAccessBody,
    MoveFileParameters,
    CopyFolderParameters,
    MoveFolderParameters,
    PatchFileItemInput,
)
from azure.connectors.sdk import (
    ConnectorClientOptions,
    ManagedIdentityTokenProvider,
    ConnectorException,
)
from tests.conftest import MockTokenProvider, MockResponse


class TestSharepointonlineClientInitialization:
    """Tests for SharepointonlineClient initialization."""

    def test_init_with_valid_url_and_defaults(self):
        """Test initialization with valid URL and default parameters."""
        client = SharepointonlineClient("https://example.azure.com/connections/test")

        assert client._connection_runtime_url == "https://example.azure.com/connections/test"
        assert client.connector_name == "sharepointonline"
        assert isinstance(client._http_client._token_provider, ManagedIdentityTokenProvider)

    def test_init_with_trailing_slash(self):
        """Test that trailing slash is removed from URL."""
        client = SharepointonlineClient("https://example.azure.com/connections/test/")

        assert client._connection_runtime_url == "https://example.azure.com/connections/test"

    def test_init_with_custom_token_provider(self, mock_token_provider):
        """Test initialization with custom token provider."""
        client = SharepointonlineClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        assert client._http_client._token_provider is mock_token_provider

    def test_init_with_custom_options(self, mock_token_provider):
        """Test initialization with custom options."""
        options = ConnectorClientOptions(timeout_seconds=60.0, max_retry_attempts=5)
        client = SharepointonlineClient(
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
            SharepointonlineClient("")

    def test_init_with_none_url_raises_error(self):
        """Test that None URL raises ValueError."""
        with pytest.raises(ValueError, match="connection_runtime_url cannot be None or empty"):
            SharepointonlineClient(None)

    def test_connector_name_property(self, mock_token_provider):
        """Test connector_name property returns 'sharepointonline'."""
        client = SharepointonlineClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        assert client.connector_name == "sharepointonline"


class TestSharepointonlineClientLifecycle:
    """Tests for SharepointonlineClient lifecycle methods."""

    @pytest.mark.asyncio
    async def test_close(self, mock_token_provider):
        """Test close method calls http_client.close."""
        client = SharepointonlineClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        with patch.object(client._http_client, 'close', new_callable=AsyncMock) as mock_close:
            await client.close()
            mock_close.assert_called_once()

    @pytest.mark.asyncio
    async def test_context_manager(self, mock_token_provider):
        """Test async context manager functionality."""
        with patch.object(SharepointonlineClient, 'close', new_callable=AsyncMock) as mock_close:
            async with SharepointonlineClient(
                "https://example.azure.com/connections/test",
                token_provider=mock_token_provider
            ) as client:
                assert isinstance(client, SharepointonlineClient)

            mock_close.assert_called_once()


class TestGetAllTables:
    """Tests for get_all_tables_async method."""

    @pytest.mark.asyncio
    async def test_success_with_json_response(self, mock_token_provider):
        """Test successful GET request with dataset parameter."""
        client = SharepointonlineClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(
            status=200,
            text=(
                '{"value": [{"name": "Documents", "id": "list1"}, '
                '{"name": "Lists", "id": "list2"}]}'
            )
        )

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ) as mock_send:
            result = await client.get_all_tables_async("https://contoso.sharepoint.com/sites/site1")

            call_args = mock_send.call_args
            assert call_args[0][0] == "GET"
            assert "/datasets/" in call_args[0][1]
            assert "/alltables" in call_args[0][1]
            assert "value" in result
            assert len(result["value"]) == 2

    @pytest.mark.asyncio
    async def test_dataset_url_encoding(self, mock_token_provider):
        """Test that dataset URL is properly encoded."""
        client = SharepointonlineClient(
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
            await client.get_all_tables_async(
                "https://contoso.sharepoint.com/sites/site with spaces"
            )

            call_args = mock_send.call_args
            path = call_args[0][1]
            # URL encoding should handle special characters
            assert "/datasets/" in path

    @pytest.mark.asyncio
    async def test_empty_response_returns_none(self, mock_token_provider):
        """Test that empty response returns None."""
        client = SharepointonlineClient(
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
            result = await client.get_all_tables_async("https://contoso.sharepoint.com/sites/site1")
            assert result is None

    @pytest.mark.asyncio
    async def test_error_response_raises_exception(self, mock_token_provider):
        """Test that error response raises ConnectorException."""
        client = SharepointonlineClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(
            status=404,
            text='{"error": "Site not found"}'
        )

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ):
            with pytest.raises(ConnectorException) as exc_info:
                await client.get_all_tables_async("https://contoso.sharepoint.com/sites/missing")

            assert exc_info.value.status_code == 404


class TestFileOperations:
    """Tests for file operation methods."""

    @pytest.mark.asyncio
    async def test_create_file_success(self, mock_token_provider):
        """Test successful file creation."""
        client = SharepointonlineClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(
            status=201,
            text=(
                '{"Id": "file123", "Name": "document.docx", '
                '"Path": "/Shared Documents/document.docx"}'
            )
        )

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ) as mock_send:
            input_data = CreateFileInput()
            result = await client.create_file_async(
                input_data,
                "https://contoso.sharepoint.com/sites/site1",
                "/Shared Documents",
                "document.docx"
            )

            call_args = mock_send.call_args
            assert call_args[0][0] == "POST"
            assert result["Id"] == "file123"
            assert result["Name"] == "document.docx"

    @pytest.mark.asyncio
    async def test_get_file_metadata(self, mock_token_provider):
        """Test getting file metadata."""
        client = SharepointonlineClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(
            status=200,
            text='{"Id": "file123", "Name": "report.pdf", "Size": 1024}'
        )

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ):
            result = await client.get_file_metadata_async(
                "https://contoso.sharepoint.com/sites/site1",
                "file123"
            )

            assert result["Id"] == "file123"
            assert result["Name"] == "report.pdf"
            assert result["Size"] == 1024

    @pytest.mark.asyncio
    async def test_update_file(self, mock_token_provider):
        """Test updating file."""
        client = SharepointonlineClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(
            status=200,
            text='{"Id": "file123", "Name": "updated.docx"}'
        )

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ) as mock_send:
            input_data = UpdateFileInput()
            result = await client.update_file_async(
                "https://contoso.sharepoint.com/sites/site1",
                "file123",
                input_data
            )

            call_args = mock_send.call_args
            assert call_args[0][0] == "PUT"
            assert result["Name"] == "updated.docx"

    @pytest.mark.asyncio
    async def test_delete_file(self, mock_token_provider):
        """Test deleting file."""
        client = SharepointonlineClient(
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
            result = await client.delete_file_async(
                "https://contoso.sharepoint.com/sites/site1",
                "file123"
            )

            call_args = mock_send.call_args
            assert call_args[0][0] == "DELETE"
            assert result is None

    @pytest.mark.asyncio
    async def test_get_file_content(self, mock_token_provider):
        """Test getting file content."""
        client = SharepointonlineClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )
        file_content = b"file binary content"
        # NOTE(sdk): Method uses response.text.encode('latin-1') so we provide text as string.
        mock_response = MockResponse(
            status=200,
            text=file_content.decode('latin-1')
        )

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ):
            result = await client.get_file_content_async(
                "https://contoso.sharepoint.com/sites/site1",
                "file123"
            )

            assert result == file_content

    @pytest.mark.asyncio
    async def test_create_file_error_raises_exception(self, mock_token_provider):
        """Test that error response raises ConnectorException."""
        client = SharepointonlineClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(
            status=400,
            text='{"error": "Bad request"}'
        )

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ):
            with pytest.raises(ConnectorException) as exc_info:
                await client.create_file_async(
                    CreateFileInput(),
                    "https://contoso.sharepoint.com/sites/site1",
                    "/Shared Documents",
                    "document.docx"
                )

            assert exc_info.value.status_code == 400

    @pytest.mark.asyncio
    async def test_get_file_metadata_error_raises_exception(self, mock_token_provider):
        """Test that error response raises ConnectorException."""
        client = SharepointonlineClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(
            status=404,
            text='{"error": "File not found"}'
        )

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ):
            with pytest.raises(ConnectorException) as exc_info:
                await client.get_file_metadata_async(
                    "https://contoso.sharepoint.com/sites/site1",
                    "missing_file"
                )

            assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    async def test_delete_file_error_raises_exception(self, mock_token_provider):
        """Test that error response raises ConnectorException."""
        client = SharepointonlineClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(
            status=403,
            text='{"error": "Forbidden"}'
        )

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ):
            with pytest.raises(ConnectorException) as exc_info:
                await client.delete_file_async(
                    "https://contoso.sharepoint.com/sites/site1",
                    "protected_file"
                )

            assert exc_info.value.status_code == 403


class TestFolderOperations:
    """Tests for folder operation methods."""

    @pytest.mark.asyncio
    async def test_create_new_folder(self, mock_token_provider):
        """Test creating new folder."""
        client = SharepointonlineClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(
            status=201,
            text='{"Id": "folder456", "Name": "NewFolder", "Path": "/Shared Documents/NewFolder"}'
        )

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ):
            result = await client.create_new_folder_async(
                "https://contoso.sharepoint.com/sites/site1",
                "Documents",
                "/Shared Documents",
                "NewFolder"
            )

            assert result["Name"] == "NewFolder"

    @pytest.mark.asyncio
    async def test_get_folder_metadata(self, mock_token_provider):
        """Test getting folder metadata."""
        client = SharepointonlineClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(
            status=200,
            text='{"Id": "folder123", "Name": "Documents", "ItemCount": 10}'
        )

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ):
            result = await client.get_folder_metadata_async(
                "https://contoso.sharepoint.com/sites/site1",
                "folder123"
            )

            assert result["ItemCount"] == 10

    @pytest.mark.asyncio
    async def test_create_folder_error_raises_exception(self, mock_token_provider):
        """Test that error response raises ConnectorException."""
        client = SharepointonlineClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(
            status=409,
            text='{"error": "Folder already exists"}'
        )

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ):
            with pytest.raises(ConnectorException) as exc_info:
                await client.create_new_folder_async(
                    "https://contoso.sharepoint.com/sites/site1",
                    "Documents",
                    "/Shared Documents",
                    "ExistingFolder"
                )

            assert exc_info.value.status_code == 409

    @pytest.mark.asyncio
    async def test_get_folder_metadata_error_raises_exception(self, mock_token_provider):
        """Test that error response raises ConnectorException."""
        client = SharepointonlineClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(
            status=404,
            text='{"error": "Folder not found"}'
        )

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ):
            with pytest.raises(ConnectorException) as exc_info:
                await client.get_folder_metadata_async(
                    "https://contoso.sharepoint.com/sites/site1",
                    "missing_folder"
                )

            assert exc_info.value.status_code == 404


class TestItemOperations:
    """Tests for list item operation methods."""

    @pytest.mark.asyncio
    async def test_get_items(self, mock_token_provider):
        """Test getting list items."""
        client = SharepointonlineClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(
            status=200,
            text='{"value": [{"Id": 1, "Title": "Item 1"}, {"Id": 2, "Title": "Item 2"}]}'
        )

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ):
            result = await client.get_items_async(
                "https://contoso.sharepoint.com/sites/site1",
                "CustomList"
            )

            assert "value" in result
            assert len(result["value"]) == 2

    @pytest.mark.asyncio
    async def test_post_item(self, mock_token_provider):
        """Test creating list item."""
        client = SharepointonlineClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(
            status=201,
            text='{"Id": 3, "Title": "New Item"}'
        )

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ) as mock_send:
            input_data = PostItemInput()
            result = await client.post_item_async(
                "https://contoso.sharepoint.com/sites/site1",
                "CustomList",
                input_data
            )

            call_args = mock_send.call_args
            assert call_args[0][0] == "POST"
            assert result["Id"] == 3

    @pytest.mark.asyncio
    async def test_get_item(self, mock_token_provider):
        """Test getting single list item."""
        client = SharepointonlineClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(
            status=200,
            text='{"Id": 1, "Title": "Item 1", "Status": "Active"}'
        )

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ):
            result = await client.get_item_async(
                "https://contoso.sharepoint.com/sites/site1",
                "CustomList",
                1
            )

            assert result["Id"] == 1
            assert result["Status"] == "Active"

    @pytest.mark.asyncio
    async def test_patch_item(self, mock_token_provider):
        """Test updating list item."""
        client = SharepointonlineClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(
            status=200,
            text='{"Id": 1, "Title": "Updated Item"}'
        )

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ) as mock_send:
            input_data = PatchItemInput()
            result = await client.patch_item_async(
                "https://contoso.sharepoint.com/sites/site1",
                "CustomList",
                1,
                input_data
            )

            call_args = mock_send.call_args
            assert call_args[0][0] == "PATCH"
            assert result["Title"] == "Updated Item"

    @pytest.mark.asyncio
    async def test_delete_item(self, mock_token_provider):
        """Test deleting list item."""
        client = SharepointonlineClient(
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
            result = await client.delete_item_async(
                "https://contoso.sharepoint.com/sites/site1",
                "CustomList",
                1
            )

            call_args = mock_send.call_args
            assert call_args[0][0] == "DELETE"
            assert result is None

    @pytest.mark.asyncio
    async def test_get_items_error_raises_exception(self, mock_token_provider):
        """Test that error response raises ConnectorException."""
        client = SharepointonlineClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(
            status=404,
            text='{"error": "List not found"}'
        )

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ):
            with pytest.raises(ConnectorException) as exc_info:
                await client.get_items_async(
                    "https://contoso.sharepoint.com/sites/site1",
                    "MissingList"
                )

            assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    async def test_post_item_error_raises_exception(self, mock_token_provider):
        """Test that error response raises ConnectorException."""
        client = SharepointonlineClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(
            status=400,
            text='{"error": "Invalid item data"}'
        )

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ):
            with pytest.raises(ConnectorException) as exc_info:
                await client.post_item_async(
                    "https://contoso.sharepoint.com/sites/site1",
                    "CustomList",
                    PostItemInput()
                )

            assert exc_info.value.status_code == 400

    @pytest.mark.asyncio
    async def test_delete_item_error_raises_exception(self, mock_token_provider):
        """Test that error response raises ConnectorException."""
        client = SharepointonlineClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(
            status=403,
            text='{"error": "Access denied"}'
        )

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ):
            with pytest.raises(ConnectorException) as exc_info:
                await client.delete_item_async(
                    "https://contoso.sharepoint.com/sites/site1",
                    "CustomList",
                    999
                )

            assert exc_info.value.status_code == 403


class TestSharingOperations:
    """Tests for sharing and permissions operations."""

    @pytest.mark.asyncio
    async def test_create_sharing_link(self, mock_token_provider):
        """Test creating sharing link."""
        client = SharepointonlineClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(
            status=200,
            text='{"link": {"webUrl": "https://contoso.sharepoint.com/share/abc123"}}'
        )

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ):
            input_data = ItemPermissionCreateLinkBody()
            result = await client.create_sharing_link_async(
                input_data,
                "https://contoso.sharepoint.com/sites/site1",
                "Documents",
                "item123"
            )

            assert "link" in result

    @pytest.mark.asyncio
    async def test_grant_access(self, mock_token_provider):
        """Test granting access to item."""
        client = SharepointonlineClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(status=204, text='')

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ) as mock_send:
            from azure.connectors.sharepointonline import ItemGrantAccessBody
            input_data = ItemGrantAccessBody()
            result = await client.grant_access_async(
                input_data,
                "https://contoso.sharepoint.com/sites/site1",
                "Documents",
                "item123"
            )

            call_args = mock_send.call_args
            assert call_args[0][0] == "POST"
            assert result is None

    @pytest.mark.asyncio
    async def test_create_sharing_link_error_raises_exception(self, mock_token_provider):
        """Test that error response raises ConnectorException."""
        client = SharepointonlineClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(
            status=400,
            text='{"error": "Invalid sharing parameters"}'
        )

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ):
            with pytest.raises(ConnectorException) as exc_info:
                await client.create_sharing_link_async(
                    ItemPermissionCreateLinkBody(),
                    "https://contoso.sharepoint.com/sites/site1",
                    "Documents",
                    "item123"
                )

            assert exc_info.value.status_code == 400

    @pytest.mark.asyncio
    async def test_grant_access_error_raises_exception(self, mock_token_provider):
        """Test that error response raises ConnectorException."""
        client = SharepointonlineClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(
            status=403,
            text='{"error": "Insufficient permissions"}'
        )

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ):
            with pytest.raises(ConnectorException) as exc_info:
                await client.grant_access_async(
                    ItemGrantAccessBody(),
                    "https://contoso.sharepoint.com/sites/site1",
                    "Documents",
                    "item123"
                )

            assert exc_info.value.status_code == 403


class TestCopyMoveOperations:
    """Tests for copy and move operations."""

    @pytest.mark.asyncio
    async def test_copy_file(self, mock_token_provider):
        """Test copying file."""
        client = SharepointonlineClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(
            status=200,
            text='{"Id": "file456", "Name": "document_copy.docx"}'
        )

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ) as mock_send:
            result = await client.copy_file_async(
                dataset="https://contoso.sharepoint.com/sites/site1",
                source="/Shared Documents/document.docx",
                destination="/Shared Documents/Backup/document_copy.docx"
            )

            mock_send.assert_called_once()
            call_args = mock_send.call_args
            assert "copyFile" in call_args[0][1]
            assert "source=" in call_args[0][1]
            assert "destination=" in call_args[0][1]
            assert result["Name"] == "document_copy.docx"

    @pytest.mark.asyncio
    async def test_move_file(self, mock_token_provider):
        """Test moving file."""
        client = SharepointonlineClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(
            status=200,
            text='{"Id": "file123", "Path": "/Archive/document.docx"}'
        )

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ):
            from azure.connectors.sharepointonline import MoveFileParameters
            input_data = MoveFileParameters()
            result = await client.move_file_async(
                input_data,
                "https://contoso.sharepoint.com/sites/site1"
            )

            assert "/Archive/" in result["Path"]

    @pytest.mark.asyncio
    async def test_copy_folder(self, mock_token_provider):
        """Test copying folder."""
        client = SharepointonlineClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(status=200, text='{"success": true}')

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ):
            input_data = CopyFolderParameters()
            result = await client.copy_folder_async(
                input_data,
                "https://contoso.sharepoint.com/sites/site1"
            )

            assert result["success"] is True

    @pytest.mark.asyncio
    async def test_copy_file_error_raises_exception(self, mock_token_provider):
        """Test that error response raises ConnectorException."""
        client = SharepointonlineClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(
            status=404,
            text='{"error": "Source file not found"}'
        )

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ):
            with pytest.raises(ConnectorException) as exc_info:
                await client.copy_file_async(
                    dataset="https://contoso.sharepoint.com/sites/site1",
                    source="/Shared Documents/missing.docx",
                    destination="/Backup/missing.docx"
                )

            assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    async def test_move_file_error_raises_exception(self, mock_token_provider):
        """Test that error response raises ConnectorException."""
        client = SharepointonlineClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(
            status=400,
            text='{"error": "Invalid destination"}'
        )

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ):
            with pytest.raises(ConnectorException) as exc_info:
                await client.move_file_async(
                    MoveFileParameters(),
                    "https://contoso.sharepoint.com/sites/site1"
                )

            assert exc_info.value.status_code == 400


class TestApprovalOperations:
    """Tests for approval operations."""

    @pytest.mark.asyncio
    async def test_create_approval_request(self, mock_token_provider):
        """Test creating approval request."""
        client = SharepointonlineClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(
            status=200,
            text='{"approvalId": "approval123", "status": "pending"}'
        )

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ):
            input_data = CreateApprovalRequestInput()
            result = await client.create_approval_request_async(
                input_data,
                "https://contoso.sharepoint.com/sites/site1",
                "Documents",
                "item123",
                "basic"
            )

            assert result["status"] == "pending"

    @pytest.mark.asyncio
    async def test_set_approval_status(self, mock_token_provider):
        """Test setting approval status."""
        client = SharepointonlineClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(status=200, text='{"status": "approved"}')

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ):
            result = await client.set_approval_status_async(
                "https://contoso.sharepoint.com/sites/site1",
                "Documents",
                "item123",
                "approved"
            )

            assert result["status"] == "approved"

    @pytest.mark.asyncio
    async def test_create_approval_request_error_raises_exception(self, mock_token_provider):
        """Test that error response raises ConnectorException."""
        client = SharepointonlineClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(
            status=400,
            text='{"error": "Invalid approval type"}'
        )

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ):
            with pytest.raises(ConnectorException) as exc_info:
                await client.create_approval_request_async(
                    CreateApprovalRequestInput(),
                    "https://contoso.sharepoint.com/sites/site1",
                    "Documents",
                    "item123",
                    "invalid"
                )

            assert exc_info.value.status_code == 400

    @pytest.mark.asyncio
    async def test_set_approval_status_error_raises_exception(self, mock_token_provider):
        """Test that error response raises ConnectorException."""
        client = SharepointonlineClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(
            status=404,
            text='{"error": "Item not found"}'
        )

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ):
            with pytest.raises(ConnectorException) as exc_info:
                await client.set_approval_status_async(
                    "https://contoso.sharepoint.com/sites/site1",
                    "Documents",
                    "missing_item",
                    "approved"
                )

            assert exc_info.value.status_code == 404


class TestDataClasses:
    """Tests for data classes and type definitions."""

    def test_create_file_input_creation(self):
        """Test CreateFileInput dataclass creation."""
        input_data = CreateFileInput()
        assert input_data is not None

    def test_update_file_input_creation(self):
        """Test UpdateFileInput dataclass creation."""
        input_data = UpdateFileInput()
        assert input_data is not None

    def test_post_item_input_creation(self):
        """Test PostItemInput dataclass creation."""
        input_data = PostItemInput()
        assert input_data is not None

    def test_patch_item_input_creation(self):
        """Test PatchItemInput dataclass creation."""
        input_data = PatchItemInput()
        assert input_data is not None


class TestEdgeCases:
    """Tests for edge cases and boundary conditions."""

    @pytest.mark.asyncio
    async def test_multiple_consecutive_calls(self, mock_token_provider):
        """Test multiple consecutive API calls work correctly."""
        client = SharepointonlineClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response_1 = MockResponse(status=200, text='{"result": "first"}')
        mock_response_2 = MockResponse(status=200, text='{"result": "second"}')

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            side_effect=[mock_response_1, mock_response_2]
        ):
            site_url = "https://contoso.sharepoint.com/sites/site1"
            result_1 = await client.get_all_tables_async(site_url)
            result_2 = await client.get_all_tables_async(site_url)

            assert result_1 == {"result": "first"}
            assert result_2 == {"result": "second"}

    @pytest.mark.asyncio
    async def test_json_parse_error_raises_exception(self, mock_token_provider):
        """Test that invalid JSON in response raises an error."""
        client = SharepointonlineClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(status=200, text='invalid json{')

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ):
            with pytest.raises(json.JSONDecodeError):
                await client.get_all_tables_async("https://contoso.sharepoint.com/sites/site1")

    @pytest.mark.asyncio
    async def test_url_construction_with_multiple_trailing_slashes(self):
        """Test URL construction handles multiple trailing slashes."""
        client = SharepointonlineClient(
            "https://example.azure.com/connections/test///",
            token_provider=MockTokenProvider()
        )

        assert client._connection_runtime_url == "https://example.azure.com/connections/test"

    def test_http_client_property_access(self, mock_token_provider):
        """Test that http_client property is accessible."""
        client = SharepointonlineClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        assert client.http_client is not None
        assert client.http_client is client._http_client

    @pytest.mark.asyncio
    async def test_dataset_with_special_characters(self, mock_token_provider):
        """Test handling of dataset URLs with special characters."""
        client = SharepointonlineClient(
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
            await client.get_all_tables_async(
                "https://contoso.sharepoint.com/sites/site-name/subsite"
            )

            # Verify the call was made (URL encoding handled internally)
            mock_send.assert_called_once()

    @pytest.mark.asyncio
    async def test_server_error_raises_exception(self, mock_token_provider):
        """Test that 500 error raises ConnectorException."""
        client = SharepointonlineClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(
            status=500,
            text='{"error": "Internal Server Error"}'
        )

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ):
            with pytest.raises(ConnectorException) as exc_info:
                await client.get_all_tables_async("https://contoso.sharepoint.com/sites/site1")

            assert exc_info.value.status_code == 500


class TestCheckInOutOperations:
    """Tests for file check-in/check-out operations."""

    @pytest.mark.asyncio
    async def test_check_out_file(self, mock_token_provider):
        """Test checking out a file."""
        client = SharepointonlineClient(
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
            await client.check_out_file_async(
                "https://contoso.sharepoint.com/sites/site1",
                "Documents",
                "file123"
            )

            call_args = mock_send.call_args
            assert call_args[0][0] == "POST"
            assert "checkoutfile" in call_args[0][1]

    @pytest.mark.asyncio
    async def test_check_in_file(self, mock_token_provider):
        """Test checking in a file."""
        client = SharepointonlineClient(
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
            input_data = FileCheckInParameters()
            await client.check_in_file_async(
                input_data,
                "https://contoso.sharepoint.com/sites/site1",
                "Documents",
                "file123"
            )

            call_args = mock_send.call_args
            assert call_args[0][0] == "POST"
            assert "checkinfile" in call_args[0][1]

    @pytest.mark.asyncio
    async def test_discard_check_out(self, mock_token_provider):
        """Test discarding a file check-out."""
        client = SharepointonlineClient(
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
            await client.discard_file_check_out_async(
                "https://contoso.sharepoint.com/sites/site1",
                "Documents",
                "file123"
            )

            call_args = mock_send.call_args
            assert call_args[0][0] == "POST"
            assert "discardfilecheckout" in call_args[0][1]

    @pytest.mark.asyncio
    async def test_check_out_file_error_raises_exception(self, mock_token_provider):
        """Test that error response raises ConnectorException."""
        client = SharepointonlineClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(
            status=423,
            text='{"error": "File is locked"}'
        )

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ):
            with pytest.raises(ConnectorException) as exc_info:
                await client.check_out_file_async(
                    "https://contoso.sharepoint.com/sites/site1",
                    "Documents",
                    "locked_file"
                )

            assert exc_info.value.status_code == 423


class TestAttachmentOperations:
    """Tests for attachment operations."""

    @pytest.mark.asyncio
    async def test_get_item_attachments(self, mock_token_provider):
        """Test getting attachments for a list item."""
        client = SharepointonlineClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(
            status=200,
            text='[{"id": "att1", "display_name": "doc.pdf"}]'
        )

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ):
            result = await client.get_item_attachments_async(
                "https://contoso.sharepoint.com/sites/site1",
                "CustomList",
                "1"
            )

            assert isinstance(result, list)

    @pytest.mark.asyncio
    async def test_create_attachment(self, mock_token_provider):
        """Test creating an attachment."""
        client = SharepointonlineClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(
            status=201,
            text='{"id": "att123", "display_name": "newfile.pdf"}'
        )

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ) as mock_send:
            input_data = CreateAttachmentInput()
            result = await client.create_attachment_async(
                input_data,
                "https://contoso.sharepoint.com/sites/site1",
                "CustomList",
                "1",
                "newfile.pdf"
            )

            call_args = mock_send.call_args
            assert call_args[0][0] == "POST"
            assert result["id"] == "att123"

    @pytest.mark.asyncio
    async def test_delete_attachment(self, mock_token_provider):
        """Test deleting an attachment."""
        client = SharepointonlineClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(status=204, text='')

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ) as mock_send:
            await client.delete_attachment_async(
                "https://contoso.sharepoint.com/sites/site1",
                "CustomList",
                "1",
                "att123"
            )

            call_args = mock_send.call_args
            assert call_args[0][0] == "DELETE"

    @pytest.mark.asyncio
    async def test_get_attachment_content(self, mock_token_provider):
        """Test getting attachment content."""
        client = SharepointonlineClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        file_content = b"attachment binary content"
        mock_response = MockResponse(
            status=200,
            text=file_content.decode('latin-1')
        )

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ):
            result = await client.get_attachment_content_async(
                "https://contoso.sharepoint.com/sites/site1",
                "CustomList",
                "1",
                "att123"
            )

            assert result == file_content

    @pytest.mark.asyncio
    async def test_create_attachment_error_raises_exception(self, mock_token_provider):
        """Test that error response raises ConnectorException."""
        client = SharepointonlineClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(
            status=413,
            text='{"error": "Attachment too large"}'
        )

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ):
            with pytest.raises(ConnectorException) as exc_info:
                await client.create_attachment_async(
                    CreateAttachmentInput(),
                    "https://contoso.sharepoint.com/sites/site1",
                    "CustomList",
                    "1",
                    "largefile.pdf"
                )

            assert exc_info.value.status_code == 413


class TestSearchOperations:
    """Tests for search operations."""

    @pytest.mark.asyncio
    async def test_search_for_user(self, mock_token_provider):
        """Test searching for a user."""
        client = SharepointonlineClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(
            status=200,
            text='{"display_name": "John Doe", "email": "john@contoso.com"}'
        )

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ):
            result = await client.search_for_user_async(
                "https://contoso.sharepoint.com/sites/site1",
                "CustomList",
                "entity1",
                "john"
            )

            assert result["display_name"] == "John Doe"

    @pytest.mark.asyncio
    async def test_search_for_user_error_raises_exception(self, mock_token_provider):
        """Test that error response raises ConnectorException."""
        client = SharepointonlineClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(
            status=400,
            text='{"error": "Multiple users found"}'
        )

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ):
            with pytest.raises(ConnectorException) as exc_info:
                await client.search_for_user_async(
                    "https://contoso.sharepoint.com/sites/site1",
                    "CustomList",
                    "entity1",
                    "smith"
                )

            assert exc_info.value.status_code == 400


class TestFileItemOperations:
    """Tests for file item operations."""

    @pytest.mark.asyncio
    async def test_get_file_item(self, mock_token_provider):
        """Test getting file item properties."""
        client = SharepointonlineClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(
            status=200,
            text='{"Id": "file123", "Name": "document.docx", "Size": 1024}'
        )

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ):
            result = await client.get_file_item_async(
                "https://contoso.sharepoint.com/sites/site1",
                "Documents",
                "file123"
            )

            assert result["Id"] == "file123"

    @pytest.mark.asyncio
    async def test_patch_file_item(self, mock_token_provider):
        """Test updating file item properties."""
        client = SharepointonlineClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(
            status=200,
            text='{"Id": "file123", "Title": "Updated Title"}'
        )

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ) as mock_send:
            input_data = PatchFileItemInput()
            result = await client.patch_file_item_async(
                input_data,
                "https://contoso.sharepoint.com/sites/site1",
                "Documents",
                "file123"
            )

            call_args = mock_send.call_args
            assert call_args[0][0] == "PATCH"
            assert result["Title"] == "Updated Title"

    @pytest.mark.asyncio
    async def test_unshare_item(self, mock_token_provider):
        """Test unsharing an item."""
        client = SharepointonlineClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(status=204, text='')

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ) as mock_send:
            await client.unshare_item_async(
                "https://contoso.sharepoint.com/sites/site1",
                "Documents",
                "item123"
            )

            call_args = mock_send.call_args
            assert call_args[0][0] == "POST"
            assert "unshare" in call_args[0][1]

    @pytest.mark.asyncio
    async def test_get_file_item_error_raises_exception(self, mock_token_provider):
        """Test that error response raises ConnectorException."""
        client = SharepointonlineClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(
            status=404,
            text='{"error": "File not found"}'
        )

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ):
            with pytest.raises(ConnectorException) as exc_info:
                await client.get_file_item_async(
                    "https://contoso.sharepoint.com/sites/site1",
                    "Documents",
                    "missing_file"
                )

            assert exc_info.value.status_code == 404


class TestMoveFolderOperations:
    """Tests for move folder operations."""

    @pytest.mark.asyncio
    async def test_move_folder(self, mock_token_provider):
        """Test moving a folder."""
        client = SharepointonlineClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(
            status=200,
            text='{"Id": "folder123", "Path": "/Archive/OldFolder"}'
        )

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ):
            input_data = MoveFolderParameters()
            result = await client.move_folder_async(
                input_data,
                "https://contoso.sharepoint.com/sites/site1"
            )

            assert "/Archive/" in result["Path"]

    @pytest.mark.asyncio
    async def test_move_folder_error_raises_exception(self, mock_token_provider):
        """Test that error response raises ConnectorException."""
        client = SharepointonlineClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(
            status=400,
            text='{"error": "Invalid destination"}'
        )

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ):
            with pytest.raises(ConnectorException) as exc_info:
                await client.move_folder_async(
                    MoveFolderParameters(),
                    "https://contoso.sharepoint.com/sites/site1"
                )

            assert exc_info.value.status_code == 400


class TestTriggerOperations:
    """Tests for trigger operations."""

    @pytest.mark.asyncio
    async def test_get_on_new_items(self, mock_token_provider):
        """Test getting new items trigger."""
        client = SharepointonlineClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(
            status=200,
            text='{"value": [{"Id": 1, "Title": "New Item"}]}'
        )

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ):
            result = await client.get_on_new_items_async(
                "https://contoso.sharepoint.com/sites/site1",
                "CustomList"
            )

            assert "value" in result

    @pytest.mark.asyncio
    async def test_get_on_updated_items(self, mock_token_provider):
        """Test getting updated items trigger."""
        client = SharepointonlineClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(
            status=200,
            text='{"value": [{"Id": 1, "Title": "Updated Item"}]}'
        )

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ):
            result = await client.get_on_updated_items_async(
                "https://contoso.sharepoint.com/sites/site1",
                "CustomList"
            )

            assert "value" in result

    @pytest.mark.asyncio
    async def test_get_on_new_items_error_raises_exception(self, mock_token_provider):
        """Test that error response raises ConnectorException."""
        client = SharepointonlineClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(
            status=404,
            text='{"error": "List not found"}'
        )

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ):
            with pytest.raises(ConnectorException) as exc_info:
                await client.get_on_new_items_async(
                    "https://contoso.sharepoint.com/sites/site1",
                    "MissingList"
                )

            assert exc_info.value.status_code == 404


class TestByPathOperations:
    """Tests for operations using file/folder paths."""

    @pytest.mark.asyncio
    async def test_get_file_metadata_by_path(self, mock_token_provider):
        """Test getting file metadata by path."""
        client = SharepointonlineClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(
            status=200,
            text='{"Id": "file123", "Name": "document.docx", '
                 '"Path": "/Shared Documents/document.docx"}'
        )

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ):
            result = await client.get_file_metadata_by_path_async(
                "https://contoso.sharepoint.com/sites/site1",
                "/Shared Documents/document.docx"
            )

            assert result["Name"] == "document.docx"

    @pytest.mark.asyncio
    async def test_get_file_content_by_path(self, mock_token_provider):
        """Test getting file content by path."""
        client = SharepointonlineClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        file_content = b"file binary content"
        mock_response = MockResponse(
            status=200,
            text=file_content.decode('latin-1')
        )

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ):
            result = await client.get_file_content_by_path_async(
                "https://contoso.sharepoint.com/sites/site1",
                "/Shared Documents/document.docx"
            )

            assert result == file_content

    @pytest.mark.asyncio
    async def test_get_folder_metadata_by_path(self, mock_token_provider):
        """Test getting folder metadata by path."""
        client = SharepointonlineClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(
            status=200,
            text='{"Id": "folder123", "Name": "Documents", "ItemCount": 10}'
        )

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ):
            result = await client.get_folder_metadata_by_path_async(
                "https://contoso.sharepoint.com/sites/site1",
                "/Shared Documents"
            )

            assert result["ItemCount"] == 10

    @pytest.mark.asyncio
    async def test_get_file_metadata_by_path_error_raises_exception(self, mock_token_provider):
        """Test that error response raises ConnectorException."""
        client = SharepointonlineClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(
            status=404,
            text='{"error": "File not found at path"}'
        )

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ):
            with pytest.raises(ConnectorException) as exc_info:
                await client.get_file_metadata_by_path_async(
                    "https://contoso.sharepoint.com/sites/site1",
                    "/Shared Documents/missing.docx"
                )

            assert exc_info.value.status_code == 404
