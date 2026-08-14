# Copyright (c) Microsoft Corporation. All rights reserved.

"""Unit tests for WordonlinebusinessClient."""

import pytest
from unittest.mock import AsyncMock, patch
from azure.connectors.wordonlinebusiness import (
    WordonlinebusinessClient,
    CreateFileItemInput,
    ContentBody,
    BlobMetadata,
    SensitivityLabelMetadata,
    GetFiles,
)
from azure.connectors.sdk import (
    ConnectorClientOptions,
    ManagedIdentityTokenProvider,
    ConnectorException,
)
from tests.conftest import MockResponse


class TestWordonlinebusinessClientInitialization:
    """Tests for WordonlinebusinessClient initialization."""

    def test_init_with_valid_url_and_defaults(self):
        """Test initialization with valid URL and default parameters."""
        client = WordonlinebusinessClient("https://example.azure.com/connections/test")

        assert client._connection_runtime_url == "https://example.azure.com/connections/test"
        assert client.connector_name == "wordonlinebusiness"
        assert isinstance(client._http_client._token_provider, ManagedIdentityTokenProvider)

    def test_init_with_trailing_slash(self):
        """Test that trailing slash is removed from URL."""
        client = WordonlinebusinessClient("https://example.azure.com/connections/test/")

        assert client._connection_runtime_url == "https://example.azure.com/connections/test"

    def test_init_with_custom_token_provider(self, mock_token_provider):
        """Test initialization with custom token provider."""
        client = WordonlinebusinessClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        assert client._http_client._token_provider is mock_token_provider

    def test_init_with_custom_options(self, mock_token_provider):
        """Test initialization with custom options."""
        options = ConnectorClientOptions(timeout_seconds=60.0, max_retry_attempts=5)
        client = WordonlinebusinessClient(
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
            WordonlinebusinessClient("")

    def test_init_with_none_url_raises_error(self):
        """Test that None URL raises ValueError."""
        with pytest.raises(ValueError, match="connection_runtime_url cannot be None or empty"):
            WordonlinebusinessClient(None)

    def test_connector_name_property(self, mock_token_provider):
        """Test connector_name property returns 'wordonlinebusiness'."""
        client = WordonlinebusinessClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        assert client.connector_name == "wordonlinebusiness"


class TestWordonlinebusinessClientLifecycle:
    """Tests for WordonlinebusinessClient lifecycle methods."""

    @pytest.mark.asyncio
    async def test_close(self, mock_token_provider):
        """Test close method calls http_client.close."""
        client = WordonlinebusinessClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        with patch.object(client._http_client, 'close', new_callable=AsyncMock) as mock_close:
            await client.close()
            mock_close.assert_called_once()

    @pytest.mark.asyncio
    async def test_context_manager(self, mock_token_provider):
        """Test async context manager functionality."""
        with patch.object(
            WordonlinebusinessClient, 'close', new_callable=AsyncMock
        ) as mock_close:
            async with WordonlinebusinessClient(
                "https://example.azure.com/connections/test",
                token_provider=mock_token_provider
            ) as client:
                assert isinstance(client, WordonlinebusinessClient)

            mock_close.assert_called_once()


class TestCreateFileItem:
    """Tests for create_file_item_async method."""

    @pytest.mark.asyncio
    async def test_create_file_item_success(self, mock_token_provider):
        """Test successful template population."""
        client = WordonlinebusinessClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(
            status=200,
            text="PDF_BINARY_CONTENT"
        )

        with patch.object(
            client._http_client, 'send_async', new_callable=AsyncMock
        ) as mock_send:
            mock_send.return_value = mock_response

            input_data = CreateFileItemInput(
                additional_properties={"field1": "value1", "field2": "value2"}
            )
            result = await client.create_file_item_async(
                input=input_data,
                source="me",
                drive="drive-1",
                file="file-1"
            )

            mock_send.assert_called_once()
            call_args = mock_send.call_args
            assert call_args[0][0] == "POST"
            assert "/api/templates/getFile" in call_args[0][1]
            assert "source=me" in call_args[0][1]
            assert "drive=drive-1" in call_args[0][1]
            assert "file=file-1" in call_args[0][1]
            assert isinstance(result, bytes)

    @pytest.mark.asyncio
    async def test_create_file_item_empty_response(self, mock_token_provider):
        """Test template population with empty response."""
        client = WordonlinebusinessClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(status=200, text="")

        with patch.object(
            client._http_client, 'send_async', new_callable=AsyncMock
        ) as mock_send:
            mock_send.return_value = mock_response

            input_data = CreateFileItemInput()
            result = await client.create_file_item_async(
                input=input_data,
                source="me",
                drive="drive-1",
                file="file-1"
            )

            assert result == b''

    @pytest.mark.asyncio
    async def test_create_file_item_error_response(self, mock_token_provider):
        """Test that error response raises ConnectorException."""
        client = WordonlinebusinessClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(status=400, text="Bad Request")

        with patch.object(
            client._http_client, 'send_async', new_callable=AsyncMock
        ) as mock_send:
            mock_send.return_value = mock_response

            input_data = CreateFileItemInput()
            with pytest.raises(ConnectorException) as exc_info:
                await client.create_file_item_async(
                    input=input_data,
                    source="me",
                    drive="drive-1",
                    file="file-1"
                )

            assert exc_info.value.status_code == 400


class TestCreateWordFileWithContent:
    """Tests for create_word_file_with_content_async method."""

    @pytest.mark.asyncio
    async def test_create_word_file_success(self, mock_token_provider):
        """Test successful Word document creation."""
        client = WordonlinebusinessClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(
            status=200,
            text='{"id": "doc-123", "name": "test.docx"}'
        )

        with patch.object(
            client._http_client, 'send_async', new_callable=AsyncMock
        ) as mock_send:
            mock_send.return_value = mock_response

            input_data = ContentBody(content="Hello World document content")
            result = await client.create_word_file_with_content_async(
                input=input_data,
                file_name="test.docx"
            )

            mock_send.assert_called_once()
            call_args = mock_send.call_args
            assert call_args[0][0] == "POST"
            assert "/api/templates/createWordFileWithContent" in call_args[0][1]
            assert "fileName=test.docx" in call_args[0][1]
            assert result["id"] == "doc-123"

    @pytest.mark.asyncio
    async def test_create_word_file_without_filename(self, mock_token_provider):
        """Test Word document creation without filename parameter."""
        client = WordonlinebusinessClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(
            status=200,
            text='{"id": "doc-456"}'
        )

        with patch.object(
            client._http_client, 'send_async', new_callable=AsyncMock
        ) as mock_send:
            mock_send.return_value = mock_response

            input_data = ContentBody(content="Document content")
            result = await client.create_word_file_with_content_async(input=input_data)

            call_args = mock_send.call_args
            assert "fileName=" not in call_args[0][1]
            assert result["id"] == "doc-456"

    @pytest.mark.asyncio
    async def test_create_word_file_empty_response(self, mock_token_provider):
        """Test Word document creation with empty response."""
        client = WordonlinebusinessClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(status=200, text="")

        with patch.object(
            client._http_client, 'send_async', new_callable=AsyncMock
        ) as mock_send:
            mock_send.return_value = mock_response

            input_data = ContentBody(content="Content")
            result = await client.create_word_file_with_content_async(input=input_data)

            assert result is None

    @pytest.mark.asyncio
    async def test_create_word_file_error_response(self, mock_token_provider):
        """Test that error response raises ConnectorException."""
        client = WordonlinebusinessClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(status=500, text="Internal Server Error")

        with patch.object(
            client._http_client, 'send_async', new_callable=AsyncMock
        ) as mock_send:
            mock_send.return_value = mock_response

            input_data = ContentBody(content="Content")
            with pytest.raises(ConnectorException) as exc_info:
                await client.create_word_file_with_content_async(input=input_data)

            assert exc_info.value.status_code == 500

    @pytest.mark.asyncio
    async def test_create_word_file_with_special_characters_in_name(self, mock_token_provider):
        """Test Word document creation with special characters in filename."""
        client = WordonlinebusinessClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(
            status=200,
            text='{"id": "doc-789"}'
        )

        with patch.object(
            client._http_client, 'send_async', new_callable=AsyncMock
        ) as mock_send:
            mock_send.return_value = mock_response

            input_data = ContentBody(content="Content")
            await client.create_word_file_with_content_async(
                input=input_data,
                file_name="my document.docx"
            )

            call_args = mock_send.call_args
            # URL encoding of space
            assert "fileName=my%20document.docx" in call_args[0][1]


class TestGetFilePDF:
    """Tests for get_file_p_d_f_async method."""

    @pytest.mark.asyncio
    async def test_convert_to_pdf_success(self, mock_token_provider):
        """Test successful Word to PDF conversion."""
        client = WordonlinebusinessClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(
            status=200,
            text="PDF_BINARY_CONTENT"
        )

        with patch.object(
            client._http_client, 'send_async', new_callable=AsyncMock
        ) as mock_send:
            mock_send.return_value = mock_response

            result = await client.get_file_p_d_f_async(
                source="me",
                drive="drive-1",
                file="file-1"
            )

            mock_send.assert_called_once()
            call_args = mock_send.call_args
            assert call_args[0][0] == "GET"
            assert "/api/templates/convertFile" in call_args[0][1]
            assert "format=pdf" in call_args[0][1]
            assert isinstance(result, bytes)

    @pytest.mark.asyncio
    async def test_convert_to_pdf_with_sensitivity_label(self, mock_token_provider):
        """Test PDF conversion with sensitivity label extraction."""
        client = WordonlinebusinessClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(status=200, text="PDF_CONTENT")

        with patch.object(
            client._http_client, 'send_async', new_callable=AsyncMock
        ) as mock_send:
            mock_send.return_value = mock_response

            await client.get_file_p_d_f_async(
                source="me",
                drive="drive-1",
                file="file-1",
                extract_sensitivity_label="true",
                fetch_sensitivity_label_metadata="true"
            )

            call_args = mock_send.call_args
            assert "extractSensitivityLabel=true" in call_args[0][1]
            assert "fetchSensitivityLabelMetadata=true" in call_args[0][1]

    @pytest.mark.asyncio
    async def test_convert_to_pdf_empty_response(self, mock_token_provider):
        """Test PDF conversion with empty response."""
        client = WordonlinebusinessClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(status=200, text="")

        with patch.object(
            client._http_client, 'send_async', new_callable=AsyncMock
        ) as mock_send:
            mock_send.return_value = mock_response

            result = await client.get_file_p_d_f_async(
                source="me",
                drive="drive-1",
                file="file-1"
            )

            assert result == b''

    @pytest.mark.asyncio
    async def test_convert_to_pdf_error_response(self, mock_token_provider):
        """Test that error response raises ConnectorException."""
        client = WordonlinebusinessClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(status=404, text="File not found")

        with patch.object(
            client._http_client, 'send_async', new_callable=AsyncMock
        ) as mock_send:
            mock_send.return_value = mock_response

            with pytest.raises(ConnectorException) as exc_info:
                await client.get_file_p_d_f_async(
                    source="me",
                    drive="drive-1",
                    file="file-1"
                )

            assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    async def test_get_drives_injects_personal_source(self, mock_token_provider):
        """Test drive discovery injects the personal source value."""
        client = WordonlinebusinessClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(status=200, text='{"value": []}')

        with patch.object(
            client._http_client, 'send_async', new_callable=AsyncMock
        ) as mock_send:
            mock_send.return_value = mock_response

            await client.get_drives_async()

            call_args = mock_send.call_args
            assert "source=me" in call_args[0][1]


class TestDataclasses:
    """Tests for dataclass serialization."""

    def test_create_file_item_input_defaults(self):
        """Test CreateFileItemInput default values."""
        input_data = CreateFileItemInput()
        assert input_data.additional_properties == {}

    def test_create_file_item_input_with_values(self):
        """Test CreateFileItemInput with custom values."""
        input_data = CreateFileItemInput(
            additional_properties={"field1": "value1", "templateId": "abc123"}
        )
        assert input_data.additional_properties["field1"] == "value1"
        assert input_data.additional_properties["templateId"] == "abc123"

    def test_content_body_defaults(self):
        """Test ContentBody default values."""
        body = ContentBody()
        assert body.content is None

    def test_content_body_with_content(self):
        """Test ContentBody with content."""
        body = ContentBody(content="Hello World")
        assert body.content == "Hello World"

    def test_blob_metadata_defaults(self):
        """Test BlobMetadata default values."""
        metadata = BlobMetadata()
        assert metadata.id is None
        assert metadata.name is None
        assert metadata.display_name is None
        assert metadata.path is None
        assert metadata.media_type is None
        assert metadata.is_folder is None
        assert metadata.file_locator is None

    def test_blob_metadata_with_values(self):
        """Test BlobMetadata with custom values."""
        metadata = BlobMetadata(
            id="file-123",
            name="document.docx",
            display_name="Document",
            path="/root/document.docx",
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            is_folder=False,
            file_locator="locator-abc"
        )
        assert metadata.id == "file-123"
        assert metadata.name == "document.docx"
        assert metadata.is_folder is False

    def test_sensitivity_label_metadata_defaults(self):
        """Test SensitivityLabelMetadata default values."""
        metadata: SensitivityLabelMetadata = []
        assert metadata == []

    def test_get_files_defaults(self):
        """Test GetFiles default values."""
        files: GetFiles = []
        assert files == []
