# Copyright (c) Microsoft Corporation. All rights reserved.

"""Unit tests for CommondataserviceClient."""

import pytest
from unittest.mock import AsyncMock, patch
from azure.connectors.commondataservice import (
    AssociateRecordsPatchItemInput,
    CommondataserviceClient,
    PatchItemInput,
    PostItemInput,
)
from azure.connectors.sdk import (
    ConnectorClientOptions,
    ManagedIdentityTokenProvider,
    ConnectorException,
)
from tests.conftest import MockResponse


class TestCommondataserviceClientInitialization:
    """Tests for CommondataserviceClient initialization."""

    def test_init_with_valid_url_and_defaults(self):
        """Test initialization with valid URL and default parameters."""
        client = CommondataserviceClient("https://example.azure.com/connections/test")

        assert client._connection_runtime_url == "https://example.azure.com/connections/test"
        assert client.connector_name == "commondataservice"
        assert isinstance(client._http_client._token_provider, ManagedIdentityTokenProvider)

    def test_init_with_trailing_slash(self):
        """Test that trailing slash is removed from URL."""
        client = CommondataserviceClient("https://example.azure.com/connections/test/")

        assert client._connection_runtime_url == "https://example.azure.com/connections/test"

    def test_init_with_custom_token_provider(self, mock_token_provider):
        """Test initialization with custom token provider."""
        client = CommondataserviceClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        assert client._http_client._token_provider is mock_token_provider

    def test_init_with_custom_options(self, mock_token_provider):
        """Test initialization with custom options."""
        options = ConnectorClientOptions(timeout_seconds=60.0, max_retry_attempts=5)
        client = CommondataserviceClient(
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
            CommondataserviceClient("")

    def test_init_with_none_url_raises_error(self):
        """Test that None URL raises ValueError."""
        with pytest.raises(ValueError, match="connection_runtime_url cannot be None or empty"):
            CommondataserviceClient(None)

    def test_connector_name_property(self, mock_token_provider):
        """Test connector_name property returns 'commondataservice'."""
        client = CommondataserviceClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        assert client.connector_name == "commondataservice"


class TestCommondataserviceClientLifecycle:
    """Tests for CommondataserviceClient lifecycle methods."""

    @pytest.mark.asyncio
    async def test_close(self, mock_token_provider):
        """Test close method calls http_client.close."""
        client = CommondataserviceClient(
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
            CommondataserviceClient, 'close', new_callable=AsyncMock
        ) as mock_close:
            async with CommondataserviceClient(
                "https://example.azure.com/connections/test",
                token_provider=mock_token_provider
            ) as client:
                assert isinstance(client, CommondataserviceClient)

            mock_close.assert_called_once()


def _make_client(mock_token_provider):
    """Create a client with a mocked token provider for method tests."""
    return CommondataserviceClient(
        "https://example.azure.com/connections/test",
        token_provider=mock_token_provider,
    )


class TestGetItem:
    """Tests for get_item_async method."""

    @pytest.mark.asyncio
    async def test_get_item_success(self, mock_token_provider):
        """Test successful get item."""
        client = _make_client(mock_token_provider)
        mock_response = MockResponse(status=200, text='{"itemInternalId": "1"}')

        with patch.object(
            client._http_client, 'send_async', new_callable=AsyncMock
        ) as mock_send:
            mock_send.return_value = mock_response

            result = await client.get_item_async(dataset="default", table="accounts", id="1")

            call_args = mock_send.call_args
            assert call_args[0][0] == "GET"
            assert "/v2/datasets/default/tables/accounts/items/1" in call_args[0][1]
            assert result["itemInternalId"] == "1"

    @pytest.mark.asyncio
    async def test_get_item_error_response(self, mock_token_provider):
        """Test that error response raises ConnectorException."""
        client = _make_client(mock_token_provider)
        mock_response = MockResponse(status=404, text="Not found")

        with patch.object(
            client._http_client, 'send_async', new_callable=AsyncMock
        ) as mock_send:
            mock_send.return_value = mock_response

            with pytest.raises(ConnectorException) as exc_info:
                await client.get_item_async(dataset="default", table="accounts", id="99")

            assert exc_info.value.status_code == 404


class TestGetItems:
    """Tests for get_items_async method."""

    @pytest.mark.asyncio
    async def test_get_items_success(self, mock_token_provider):
        """Test successful list items."""
        client = _make_client(mock_token_provider)
        mock_response = MockResponse(status=200, text='{"value": []}')

        with patch.object(
            client._http_client, 'send_async', new_callable=AsyncMock
        ) as mock_send:
            mock_send.return_value = mock_response

            result = await client.get_items_async(dataset="default", table="accounts")

            call_args = mock_send.call_args
            assert call_args[0][0] == "GET"
            assert "/v2/datasets/default/tables/accounts/items" in call_args[0][1]
            assert result["value"] == []

    @pytest.mark.asyncio
    async def test_get_items_with_query_params(self, mock_token_provider):
        """Test list items serializes OData query parameters."""
        client = _make_client(mock_token_provider)
        mock_response = MockResponse(status=200, text='{"value": []}')

        with patch.object(
            client._http_client, 'send_async', new_callable=AsyncMock
        ) as mock_send:
            mock_send.return_value = mock_response

            await client.get_items_async(
                dataset="default",
                table="contacts",
                apply="groupby((name))",
                filter="statecode eq 0",
                orderby="name asc",
                top="10",
                expand="primarycontactid",
            )

            url = mock_send.call_args[0][1]
            assert "%24apply=" in url or "$apply=" in url
            assert "%24filter=" in url or "$filter=" in url
            assert "%24orderby=" in url or "$orderby=" in url
            assert "%24top=" in url or "$top=" in url
            assert "%24expand=" in url or "$expand=" in url

    @pytest.mark.asyncio
    async def test_get_items_error_response(self, mock_token_provider):
        """Test that error response raises ConnectorException."""
        client = _make_client(mock_token_provider)
        mock_response = MockResponse(status=500, text="Server error")

        with patch.object(
            client._http_client, 'send_async', new_callable=AsyncMock
        ) as mock_send:
            mock_send.return_value = mock_response

            with pytest.raises(ConnectorException) as exc_info:
                await client.get_items_async(dataset="default", table="accounts")

            assert exc_info.value.status_code == 500


class TestPatchItem:
    """Tests for patch_item_async method."""

    @pytest.mark.asyncio
    async def test_patch_item_success(self, mock_token_provider):
        """Test successful patch item."""
        client = _make_client(mock_token_provider)
        mock_response = MockResponse(status=200, text='{"itemInternalId": "1"}')
        body = PatchItemInput()

        with patch.object(
            client._http_client, 'send_async', new_callable=AsyncMock
        ) as mock_send:
            mock_send.return_value = mock_response

            result = await client.patch_item_async(
                input=body,
                dataset="default",
                table="accounts",
                id="1",
            )

            call_args = mock_send.call_args
            assert call_args[0][0] == "PATCH"
            assert "/v2/datasets/default/tables/accounts/items/1" in call_args[0][1]
            assert call_args.kwargs["body"] is body
            assert result["itemInternalId"] == "1"

    @pytest.mark.asyncio
    async def test_patch_item_error_response(self, mock_token_provider):
        """Test that error response raises ConnectorException."""
        client = _make_client(mock_token_provider)
        mock_response = MockResponse(status=400, text="Bad request")

        with patch.object(
            client._http_client, 'send_async', new_callable=AsyncMock
        ) as mock_send:
            mock_send.return_value = mock_response

            with pytest.raises(ConnectorException) as exc_info:
                await client.patch_item_async(
                    input=PatchItemInput(),
                    dataset="default",
                    table="accounts",
                    id="1",
                )

            assert exc_info.value.status_code == 400


class TestPostItem:
    """Tests for post_item_async method."""

    @pytest.mark.asyncio
    async def test_post_item_success(self, mock_token_provider):
        """Test successful post item."""
        client = _make_client(mock_token_provider)
        mock_response = MockResponse(status=201, text='{"itemInternalId": "new"}')
        body = PostItemInput()

        with patch.object(
            client._http_client, 'send_async', new_callable=AsyncMock
        ) as mock_send:
            mock_send.return_value = mock_response

            result = await client.post_item_async(
                input=body,
                dataset="default",
                table="accounts",
            )

            call_args = mock_send.call_args
            assert call_args[0][0] == "POST"
            assert "/v2/datasets/default/tables/accounts/items" in call_args[0][1]
            assert call_args.kwargs["body"] is body
            assert result["itemInternalId"] == "new"

    @pytest.mark.asyncio
    async def test_post_item_error_response(self, mock_token_provider):
        """Test that error response raises ConnectorException."""
        client = _make_client(mock_token_provider)
        mock_response = MockResponse(status=400, text="Bad request")

        with patch.object(
            client._http_client, 'send_async', new_callable=AsyncMock
        ) as mock_send:
            mock_send.return_value = mock_response

            with pytest.raises(ConnectorException) as exc_info:
                await client.post_item_async(
                    input=PostItemInput(),
                    dataset="default",
                    table="accounts",
                )

            assert exc_info.value.status_code == 400


class TestGetDataSets:
    """Tests for get_data_sets_async method."""

    @pytest.mark.asyncio
    async def test_get_data_sets_success(self, mock_token_provider):
        """Test successful get data sets."""
        client = _make_client(mock_token_provider)
        mock_response = MockResponse(status=200, text='{"value": []}')

        with patch.object(
            client._http_client, 'send_async', new_callable=AsyncMock
        ) as mock_send:
            mock_send.return_value = mock_response

            await client.get_data_sets_async()

            call_args = mock_send.call_args
            assert call_args[0][0] == "GET"
            assert "/v2/datasets" in call_args[0][1]

    @pytest.mark.asyncio
    async def test_get_data_sets_error_response(self, mock_token_provider):
        """Test that error response raises ConnectorException."""
        client = _make_client(mock_token_provider)
        mock_response = MockResponse(status=500, text="Server error")

        with patch.object(
            client._http_client, 'send_async', new_callable=AsyncMock
        ) as mock_send:
            mock_send.return_value = mock_response

            with pytest.raises(ConnectorException) as exc_info:
                await client.get_data_sets_async()

            assert exc_info.value.status_code == 500


class TestGetMetadataForPatchItem:
    """Tests for get_metadata_for_patch_item_async method."""

    @pytest.mark.asyncio
    async def test_get_metadata_for_patch_item_success(self, mock_token_provider):
        """Test successful get patch metadata."""
        client = _make_client(mock_token_provider)
        mock_response = MockResponse(status=200, text='{"name": "accounts"}')

        with patch.object(
            client._http_client, 'send_async', new_callable=AsyncMock
        ) as mock_send:
            mock_send.return_value = mock_response

            await client.get_metadata_for_patch_item_async(dataset="default", table="accounts")

            call_args = mock_send.call_args
            assert call_args[0][0] == "GET"
            assert (
                "/v2/$metadata.json/datasets/default/tables/accounts/patchitem"
                in call_args[0][1]
            )

    @pytest.mark.asyncio
    async def test_get_metadata_for_patch_item_error_response(self, mock_token_provider):
        """Test that error response raises ConnectorException."""
        client = _make_client(mock_token_provider)
        mock_response = MockResponse(status=404, text="Not found")

        with patch.object(
            client._http_client, 'send_async', new_callable=AsyncMock
        ) as mock_send:
            mock_send.return_value = mock_response

            with pytest.raises(ConnectorException) as exc_info:
                await client.get_metadata_for_patch_item_async(dataset="default", table="accounts")

            assert exc_info.value.status_code == 404


class TestGetMetadataForPostItem:
    """Tests for get_metadata_for_post_item_async method."""

    @pytest.mark.asyncio
    async def test_get_metadata_for_post_item_success(self, mock_token_provider):
        """Test successful get post metadata."""
        client = _make_client(mock_token_provider)
        mock_response = MockResponse(status=200, text='{"name": "accounts"}')

        with patch.object(
            client._http_client, 'send_async', new_callable=AsyncMock
        ) as mock_send:
            mock_send.return_value = mock_response

            await client.get_metadata_for_post_item_async(dataset="default", table="accounts")

            call_args = mock_send.call_args
            assert call_args[0][0] == "GET"
            assert (
                "/v2/$metadata.json/datasets/default/tables/accounts/postitem"
                in call_args[0][1]
            )

    @pytest.mark.asyncio
    async def test_get_metadata_for_post_item_error_response(self, mock_token_provider):
        """Test that error response raises ConnectorException."""
        client = _make_client(mock_token_provider)
        mock_response = MockResponse(status=404, text="Not found")

        with patch.object(
            client._http_client, 'send_async', new_callable=AsyncMock
        ) as mock_send:
            mock_send.return_value = mock_response

            with pytest.raises(ConnectorException) as exc_info:
                await client.get_metadata_for_post_item_async(dataset="default", table="accounts")

            assert exc_info.value.status_code == 404


class TestGetTable:
    """Tests for get_table_async method."""

    @pytest.mark.asyncio
    async def test_get_table_success(self, mock_token_provider):
        """Test successful get table metadata."""
        client = _make_client(mock_token_provider)
        mock_response = MockResponse(status=200, text='{"name": "accounts"}')

        with patch.object(
            client._http_client, 'send_async', new_callable=AsyncMock
        ) as mock_send:
            mock_send.return_value = mock_response

            result = await client.get_table_async(dataset="default", table="accounts")

            call_args = mock_send.call_args
            assert call_args[0][0] == "GET"
            assert "/v2/$metadata.json/datasets/default/tables/accounts" in call_args[0][1]
            assert result["name"] == "accounts"

    @pytest.mark.asyncio
    async def test_get_table_error_response(self, mock_token_provider):
        """Test that error response raises ConnectorException."""
        client = _make_client(mock_token_provider)
        mock_response = MockResponse(status=404, text="Not found")

        with patch.object(
            client._http_client, 'send_async', new_callable=AsyncMock
        ) as mock_send:
            mock_send.return_value = mock_response

            with pytest.raises(ConnectorException) as exc_info:
                await client.get_table_async(dataset="default", table="accounts")

            assert exc_info.value.status_code == 404


class TestGetDataSetsMetadata:
    """Tests for get_data_sets_metadata_async method."""

    @pytest.mark.asyncio
    async def test_get_data_sets_metadata_success(self, mock_token_provider):
        """Test successful get datasets metadata."""
        client = _make_client(mock_token_provider)
        mock_response = MockResponse(status=200, text='{"tabular": {}}')

        with patch.object(
            client._http_client, 'send_async', new_callable=AsyncMock
        ) as mock_send:
            mock_send.return_value = mock_response

            result = await client.get_data_sets_metadata_async()

            call_args = mock_send.call_args
            assert call_args[0][0] == "GET"
            assert call_args[0][1].endswith("/$metadata.json/datasets")
            assert result == {"tabular": {}}

    @pytest.mark.asyncio
    async def test_get_data_sets_metadata_error_response(self, mock_token_provider):
        """Test that error response raises ConnectorException."""
        client = _make_client(mock_token_provider)
        mock_response = MockResponse(status=500, text="Server error")

        with patch.object(
            client._http_client, 'send_async', new_callable=AsyncMock
        ) as mock_send:
            mock_send.return_value = mock_response

            with pytest.raises(ConnectorException) as exc_info:
                await client.get_data_sets_metadata_async()

            assert exc_info.value.status_code == 500


class TestGetNextPage:
    """Tests for get_next_page_async method."""

    @pytest.mark.asyncio
    async def test_get_next_page_success(self, mock_token_provider):
        """Test successful follow of nextLink."""
        client = _make_client(mock_token_provider)
        mock_response = MockResponse(status=200, text='{"value": []}')

        with patch.object(
            client._http_client, 'send_async', new_callable=AsyncMock
        ) as mock_send:
            mock_send.return_value = mock_response

            await client.get_next_page_async(next_link="token123")

            call_args = mock_send.call_args
            assert call_args[0][0] == "GET"
            assert "/nextLink/token123" in call_args[0][1]

    @pytest.mark.asyncio
    async def test_get_next_page_error_response(self, mock_token_provider):
        """Test that error response raises ConnectorException."""
        client = _make_client(mock_token_provider)
        mock_response = MockResponse(status=404, text="Not found")

        with patch.object(
            client._http_client, 'send_async', new_callable=AsyncMock
        ) as mock_send:
            mock_send.return_value = mock_response

            with pytest.raises(ConnectorException) as exc_info:
                await client.get_next_page_async(next_link="token123")

            assert exc_info.value.status_code == 404


class TestAssociateRecordsPatchItem:
    """Tests for associate_records_patch_item_async method."""

    @pytest.mark.asyncio
    async def test_associate_records_success(self, mock_token_provider):
        """Test successful associate records."""
        client = _make_client(mock_token_provider)
        mock_response = MockResponse(status=200, text='{}')

        with patch.object(
            client._http_client, 'send_async', new_callable=AsyncMock
        ) as mock_send:
            mock_send.return_value = mock_response

            await client.associate_records_patch_item_async(
                AssociateRecordsPatchItemInput(),
                dataset="default",
                table="accounts",
                id="1",
                relationship="primarycontactid",
            )

            call_args = mock_send.call_args
            assert call_args[0][0] == "PATCH"
            assert "/v2" in call_args[0][1]
            assert "/Relationship" in call_args[0][1]

    @pytest.mark.asyncio
    async def test_associate_records_error_response(self, mock_token_provider):
        """Test that error response raises ConnectorException."""
        client = _make_client(mock_token_provider)
        mock_response = MockResponse(status=400, text="Bad request")

        with patch.object(
            client._http_client, 'send_async', new_callable=AsyncMock
        ) as mock_send:
            mock_send.return_value = mock_response

            with pytest.raises(ConnectorException) as exc_info:
                await client.associate_records_patch_item_async(
                    AssociateRecordsPatchItemInput(),
                    dataset="default",
                    table="accounts",
                    id="1",
                    relationship="primarycontactid",
                )

            assert exc_info.value.status_code == 400


class TestCreateAttachment:
    """Tests for create_attachment_async method."""

    @pytest.mark.asyncio
    async def test_create_attachment_success(self, mock_token_provider):
        """Test successful create attachment."""
        client = _make_client(mock_token_provider)
        mock_response = MockResponse(status=200, text='{"annotationid": "abc"}')

        with patch.object(
            client._http_client, 'send_async', new_callable=AsyncMock
        ) as mock_send:
            mock_send.return_value = mock_response

            result = await client.create_attachment_async(
                b"file-bytes",
                dataset="default",
                table="accounts",
                id="1",
                display_name="note.txt",
            )

            call_args = mock_send.call_args
            assert call_args[0][0] == "POST"
            assert "/attachments" in call_args[0][1]
            assert "displayName=note.txt" in call_args[0][1]
            assert call_args.kwargs["content_type"] == "application/octet-stream"
            assert result == {"annotationid": "abc"}

    @pytest.mark.asyncio
    async def test_create_attachment_error_response(self, mock_token_provider):
        """Test that error response raises ConnectorException."""
        client = _make_client(mock_token_provider)
        mock_response = MockResponse(status=403, text="Forbidden")

        with patch.object(
            client._http_client, 'send_async', new_callable=AsyncMock
        ) as mock_send:
            mock_send.return_value = mock_response

            with pytest.raises(ConnectorException) as exc_info:
                await client.create_attachment_async(
                    b"file-bytes",
                    dataset="default",
                    table="accounts",
                    id="1",
                    display_name="note.txt",
                )

            assert exc_info.value.status_code == 403


class TestGetItemAttachments:
    """Tests for get_item_attachments_async method."""

    @pytest.mark.asyncio
    async def test_get_item_attachments_success(self, mock_token_provider):
        """Test successful get item attachments."""
        client = _make_client(mock_token_provider)
        mock_response = MockResponse(status=200, text='{"value": []}')

        with patch.object(
            client._http_client, 'send_async', new_callable=AsyncMock
        ) as mock_send:
            mock_send.return_value = mock_response

            await client.get_item_attachments_async(
                dataset="default", table="accounts", id="1"
            )

            call_args = mock_send.call_args
            assert call_args[0][0] == "GET"
            assert call_args[0][1].endswith("/attachments")

    @pytest.mark.asyncio
    async def test_get_item_attachments_error_response(self, mock_token_provider):
        """Test that error response raises ConnectorException."""
        client = _make_client(mock_token_provider)
        mock_response = MockResponse(status=404, text="Not found")

        with patch.object(
            client._http_client, 'send_async', new_callable=AsyncMock
        ) as mock_send:
            mock_send.return_value = mock_response

            with pytest.raises(ConnectorException) as exc_info:
                await client.get_item_attachments_async(
                    dataset="default", table="accounts", id="1"
                )

            assert exc_info.value.status_code == 404


class TestGetAttachmentContent:
    """Tests for get_attachment_content_async method."""

    @pytest.mark.asyncio
    async def test_get_attachment_content_success(self, mock_token_provider):
        """Test successful get attachment content returns bytes."""
        client = _make_client(mock_token_provider)
        mock_response = MockResponse(status=200, content=b"binary-data")

        with patch.object(
            client._http_client, 'send_async', new_callable=AsyncMock
        ) as mock_send:
            mock_send.return_value = mock_response

            result = await client.get_attachment_content_async(
                dataset="default", table="accounts", id="1", attachment_id="att1"
            )

            call_args = mock_send.call_args
            assert call_args[0][0] == "GET"
            assert call_args[0][1].endswith("/$value")
            assert result == b"binary-data"

    @pytest.mark.asyncio
    async def test_get_attachment_content_error_response(self, mock_token_provider):
        """Test that error response raises ConnectorException."""
        client = _make_client(mock_token_provider)
        mock_response = MockResponse(status=404, text="Not found")

        with patch.object(
            client._http_client, 'send_async', new_callable=AsyncMock
        ) as mock_send:
            mock_send.return_value = mock_response

            with pytest.raises(ConnectorException) as exc_info:
                await client.get_attachment_content_async(
                    dataset="default", table="accounts", id="1", attachment_id="att1"
                )

            assert exc_info.value.status_code == 404


class TestDeleteAttachment:
    """Tests for delete_attachment_async method."""

    @pytest.mark.asyncio
    async def test_delete_attachment_success(self, mock_token_provider):
        """Test successful delete attachment."""
        client = _make_client(mock_token_provider)
        mock_response = MockResponse(status=200, text="")

        with patch.object(
            client._http_client, 'send_async', new_callable=AsyncMock
        ) as mock_send:
            mock_send.return_value = mock_response

            await client.delete_attachment_async(
                dataset="default", table="accounts", id="1", attachment_id="att1"
            )

            call_args = mock_send.call_args
            assert call_args[0][0] == "DELETE"
            assert call_args[0][1].endswith("/attachments/att1")

    @pytest.mark.asyncio
    async def test_delete_attachment_error_response(self, mock_token_provider):
        """Test that error response raises ConnectorException."""
        client = _make_client(mock_token_provider)
        mock_response = MockResponse(status=404, text="Not found")

        with patch.object(
            client._http_client, 'send_async', new_callable=AsyncMock
        ) as mock_send:
            mock_send.return_value = mock_response

            with pytest.raises(ConnectorException) as exc_info:
                await client.delete_attachment_async(
                    dataset="default", table="accounts", id="1", attachment_id="att1"
                )

            assert exc_info.value.status_code == 404


class TestDeleteItem:
    """Tests for delete_item_async method."""

    @pytest.mark.asyncio
    async def test_delete_item_success(self, mock_token_provider):
        """Test successful delete item."""
        client = _make_client(mock_token_provider)
        mock_response = MockResponse(status=200, text="")

        with patch.object(
            client._http_client, 'send_async', new_callable=AsyncMock
        ) as mock_send:
            mock_send.return_value = mock_response

            await client.delete_item_async(dataset="default", table="accounts", id="1")

            call_args = mock_send.call_args
            assert call_args[0][0] == "DELETE"
            assert call_args[0][1].endswith("/items/1")

    @pytest.mark.asyncio
    async def test_delete_item_error_response(self, mock_token_provider):
        """Test that error response raises ConnectorException."""
        client = _make_client(mock_token_provider)
        mock_response = MockResponse(status=404, text="Not found")

        with patch.object(
            client._http_client, 'send_async', new_callable=AsyncMock
        ) as mock_send:
            mock_send.return_value = mock_response

            with pytest.raises(ConnectorException) as exc_info:
                await client.delete_item_async(
                    dataset="default", table="accounts", id="1"
                )

            assert exc_info.value.status_code == 404


class TestDisassociateRecordsPostItem:
    """Tests for disassociate_records_post_item_async method."""

    @pytest.mark.asyncio
    async def test_disassociate_records_success(self, mock_token_provider):
        """Test successful disassociate records from multi-valued relationship."""
        client = _make_client(mock_token_provider)
        mock_response = MockResponse(status=200, text='{}')

        with patch.object(
            client._http_client, 'send_async', new_callable=AsyncMock
        ) as mock_send:
            mock_send.return_value = mock_response

            await client.disassociate_records_post_item_async(
                dataset="default",
                table="accounts",
                id="1",
                relationship="contact_customer_accounts",
                related_id="2",
            )

            call_args = mock_send.call_args
            assert call_args[0][0] == "DELETE"
            assert "/Relationship" in call_args[0][1]
            assert call_args[0][1].endswith("/RelatedId/2")

    @pytest.mark.asyncio
    async def test_disassociate_records_error_response(self, mock_token_provider):
        """Test that error response raises ConnectorException."""
        client = _make_client(mock_token_provider)
        mock_response = MockResponse(status=400, text="Bad request")

        with patch.object(
            client._http_client, 'send_async', new_callable=AsyncMock
        ) as mock_send:
            mock_send.return_value = mock_response

            with pytest.raises(ConnectorException) as exc_info:
                await client.disassociate_records_post_item_async(
                    dataset="default",
                    table="accounts",
                    id="1",
                    relationship="contact_customer_accounts",
                    related_id="2",
                )

            assert exc_info.value.status_code == 400


class TestDisassociateSingleValueRecordDeleteItem:
    """Tests for disassociate_single_value_record_delete_item_async method."""

    @pytest.mark.asyncio
    async def test_disassociate_single_value_success(self, mock_token_provider):
        """Test successful disassociate from single-valued relationship."""
        client = _make_client(mock_token_provider)
        mock_response = MockResponse(status=200, text='{}')

        with patch.object(
            client._http_client, 'send_async', new_callable=AsyncMock
        ) as mock_send:
            mock_send.return_value = mock_response

            await client.disassociate_single_value_record_delete_item_async(
                dataset="default",
                table="accounts",
                id="1",
                relationship="primarycontactid",
            )

            call_args = mock_send.call_args
            assert call_args[0][0] == "DELETE"
            assert call_args[0][1].endswith("/Relationship/primarycontactid")

    @pytest.mark.asyncio
    async def test_disassociate_single_value_error_response(self, mock_token_provider):
        """Test that error response raises ConnectorException."""
        client = _make_client(mock_token_provider)
        mock_response = MockResponse(status=404, text="Not found")

        with patch.object(
            client._http_client, 'send_async', new_callable=AsyncMock
        ) as mock_send:
            mock_send.return_value = mock_response

            with pytest.raises(ConnectorException) as exc_info:
                await client.disassociate_single_value_record_delete_item_async(
                    dataset="default",
                    table="accounts",
                    id="1",
                    relationship="primarycontactid",
                )

            assert exc_info.value.status_code == 404


class TestGetCollectionRelationships:
    """Tests for get_collection_relationships_async method."""

    @pytest.mark.asyncio
    async def test_get_collection_relationships_success(self, mock_token_provider):
        """Test successful get collection relationships."""
        client = _make_client(mock_token_provider)
        mock_response = MockResponse(status=200, text='{"value": []}')

        with patch.object(
            client._http_client, 'send_async', new_callable=AsyncMock
        ) as mock_send:
            mock_send.return_value = mock_response

            await client.get_collection_relationships_async(
                dataset="default",
                table="accounts",
                id="1",
                collection_type="onetomany",
                relationship="account_tasks",
                target="task",
            )

            call_args = mock_send.call_args
            assert call_args[0][0] == "GET"
            assert "/Collection" in call_args[0][1]
            assert call_args[0][1].endswith("/TargetTable/task")

    @pytest.mark.asyncio
    async def test_get_collection_relationships_error_response(self, mock_token_provider):
        """Test that error response raises ConnectorException."""
        client = _make_client(mock_token_provider)
        mock_response = MockResponse(status=404, text="Not found")

        with patch.object(
            client._http_client, 'send_async', new_callable=AsyncMock
        ) as mock_send:
            mock_send.return_value = mock_response

            with pytest.raises(ConnectorException) as exc_info:
                await client.get_collection_relationships_async(
                    dataset="default",
                    table="accounts",
                    id="1",
                    collection_type="onetomany",
                    relationship="account_tasks",
                    target="task",
                )

            assert exc_info.value.status_code == 404


class TestGetMultiSelectMetadata:
    """Tests for get_multi_select_metadata_async method."""

    @pytest.mark.asyncio
    async def test_get_multi_select_metadata_success(self, mock_token_provider):
        """Test successful get multi-select metadata."""
        client = _make_client(mock_token_provider)
        mock_response = MockResponse(status=200, text='{"name": "col"}')

        with patch.object(
            client._http_client, 'send_async', new_callable=AsyncMock
        ) as mock_send:
            mock_send.return_value = mock_response

            await client.get_multi_select_metadata_async(
                dataset="default", table="accounts", item="col"
            )

            call_args = mock_send.call_args
            assert call_args[0][0] == "GET"
            assert call_args[0][1].endswith("/MultiSelect")

    @pytest.mark.asyncio
    async def test_get_multi_select_metadata_error_response(self, mock_token_provider):
        """Test that error response raises ConnectorException."""
        client = _make_client(mock_token_provider)
        mock_response = MockResponse(status=404, text="Not found")

        with patch.object(
            client._http_client, 'send_async', new_callable=AsyncMock
        ) as mock_send:
            mock_send.return_value = mock_response

            with pytest.raises(ConnectorException) as exc_info:
                await client.get_multi_select_metadata_async(
                    dataset="default", table="accounts", item="col"
                )

            assert exc_info.value.status_code == 404


class TestGetOptionSetMetadata:
    """Tests for get_option_set_metadata_async method."""

    @pytest.mark.asyncio
    async def test_get_option_set_metadata_success(self, mock_token_provider):
        """Test successful get option set metadata."""
        client = _make_client(mock_token_provider)
        mock_response = MockResponse(status=200, text='{"name": "col"}')

        with patch.object(
            client._http_client, 'send_async', new_callable=AsyncMock
        ) as mock_send:
            mock_send.return_value = mock_response

            await client.get_option_set_metadata_async(
                dataset="default", table="accounts", item="col", type_="Picklist"
            )

            call_args = mock_send.call_args
            assert call_args[0][0] == "GET"
            assert "/OptionSet" in call_args[0][1]
            assert call_args[0][1].endswith("/Picklist")

    @pytest.mark.asyncio
    async def test_get_option_set_metadata_error_response(self, mock_token_provider):
        """Test that error response raises ConnectorException."""
        client = _make_client(mock_token_provider)
        mock_response = MockResponse(status=404, text="Not found")

        with patch.object(
            client._http_client, 'send_async', new_callable=AsyncMock
        ) as mock_send:
            mock_send.return_value = mock_response

            with pytest.raises(ConnectorException) as exc_info:
                await client.get_option_set_metadata_async(
                    dataset="default", table="accounts", item="col", type_="Picklist"
                )

            assert exc_info.value.status_code == 404


class TestPathParameterEncoding:
    """Tests that path parameters are double-encoded.

    Dataverse routes requests through the apihub gateway, which decodes the
    path once before forwarding. Path segments must therefore be encoded
    twice so special characters survive. These tests use realistic values
    with special characters (the ':' and '/' in an environment URL, and a
    space in a table name) because plain values such as 'default' encode to
    themselves and cannot distinguish single from double encoding.
    """

    @pytest.mark.asyncio
    async def test_get_items_double_encodes_dataset_environment_url(self, mock_token_provider):
        """Test that the environment URL dataset is double-encoded, not single-encoded."""
        client = _make_client(mock_token_provider)
        mock_response = MockResponse(status=200, text='{"value": []}')

        with patch.object(
            client._http_client, 'send_async', new_callable=AsyncMock
        ) as mock_send:
            mock_send.return_value = mock_response

            await client.get_items_async(
                dataset="https://org12345.crm.dynamics.com",
                table="accounts",
            )

            url = mock_send.call_args[0][1]

            # Double-encoded: ':' -> '%3A' -> '%253A', '/' -> '%2F' -> '%252F'.
            assert (
                "/v2/datasets/https%253A%252F%252Forg12345.crm.dynamics.com"
                "/tables/accounts/items"
            ) in url
            # Single-encoded form must be absent (proves double, not single).
            assert "https%3A%2F%2Forg12345.crm.dynamics.com" not in url

    @pytest.mark.asyncio
    async def test_get_item_double_encodes_all_segments(self, mock_token_provider):
        """Test that dataset, table, and id segments are all double-encoded."""
        client = _make_client(mock_token_provider)
        mock_response = MockResponse(status=200, text='{"name": "row"}')

        with patch.object(
            client._http_client, 'send_async', new_callable=AsyncMock
        ) as mock_send:
            mock_send.return_value = mock_response

            await client.get_item_async(
                dataset="https://org12345.crm.dynamics.com",
                table="my table",
                id="a/b",
            )

            url = mock_send.call_args[0][1]

            # Table space: ' ' -> '%20' -> '%2520'.
            assert "/tables/my%2520table/" in url
            assert "/tables/my%20table/" not in url
            # Id slash: '/' -> '%2F' -> '%252F'.
            assert "/items/a%252Fb" in url
            assert "/items/a%2Fb" not in url
            # Dataset double-encoded.
            assert "https%253A%252F%252Forg12345.crm.dynamics.com" in url

    @pytest.mark.asyncio
    async def test_post_item_double_encodes_dataset_environment_url(self, mock_token_provider):
        """Test that post_item double-encodes the environment URL dataset segment."""
        client = _make_client(mock_token_provider)
        mock_response = MockResponse(status=200, text='{"accountid": "1"}')

        with patch.object(
            client._http_client, 'send_async', new_callable=AsyncMock
        ) as mock_send:
            mock_send.return_value = mock_response

            await client.post_item_async(
                input=PostItemInput(additional_properties={"name": "Contoso"}),
                dataset="https://org12345.crm.dynamics.com",
                table="accounts",
            )

            url = mock_send.call_args[0][1]

            expected_path = (
                "/v2/datasets/https%253A%252F%252Forg12345.crm.dynamics.com"
                "/tables/accounts/items"
            )
            assert expected_path in url
            assert "https%3A%2F%2Forg12345.crm.dynamics.com" not in url
