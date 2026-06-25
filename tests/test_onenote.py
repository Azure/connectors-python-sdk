# Copyright (c) Microsoft Corporation. All rights reserved.

"""Unit tests for OnenoteClient."""

import pytest
from unittest.mock import AsyncMock, patch

from azure.connectors.onenote import (
    OnenoteClient,
    CreateSectionInNotebookResponse,
    CreatePageInSectionInput,
    Page,
    GetPagesInSectionResponse,
    CreatePageInQuickNotesInput,
    Notebook,
    GetSectionsInNotebookResponse,
    NewSectionResponse,
    NewSectionGroupResponse,
    NewPageResponse,
    CreateSectionRequest,
    UpdatePageContentRequest,
    GetPageResponse,
    ParentNotebook,
    Link,
    OneNoteClientUrl,
    OneNoteWebUrl,
    SectionListItem,
    SectionResponse,
    SectionGroupResponse,
)
from azure.connectors.sdk import (
    ConnectorClientOptions,
    ManagedIdentityTokenProvider,
    ConnectorException,
)
from tests.conftest import MockResponse


class TestOnenoteClientInitialization:
    """Tests for OnenoteClient initialization."""

    def test_init_with_valid_url_and_defaults(self):
        """Test initialization with valid URL and default parameters."""
        client = OnenoteClient("https://example.azure.com/connections/test")

        assert client._connection_runtime_url == "https://example.azure.com/connections/test"
        assert client.connector_name == "onenote"
        assert isinstance(client._http_client._token_provider, ManagedIdentityTokenProvider)

    def test_init_with_trailing_slash(self):
        """Test that trailing slash is removed from URL."""
        client = OnenoteClient("https://example.azure.com/connections/test/")

        assert client._connection_runtime_url == "https://example.azure.com/connections/test"

    def test_init_with_custom_token_provider(self, mock_token_provider):
        """Test initialization with custom token provider."""
        client = OnenoteClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        assert client._http_client._token_provider is mock_token_provider

    def test_init_with_custom_options(self, mock_token_provider):
        """Test initialization with custom options."""
        options = ConnectorClientOptions(timeout_seconds=60.0, max_retry_attempts=5)
        client = OnenoteClient(
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
            OnenoteClient("")

    def test_init_with_none_url_raises_error(self):
        """Test that None URL raises ValueError."""
        with pytest.raises(ValueError, match="connection_runtime_url cannot be None or empty"):
            OnenoteClient(None)

    def test_connector_name_property(self, mock_token_provider):
        """Test connector_name property returns 'onenote'."""
        client = OnenoteClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        assert client.connector_name == "onenote"

    def test_init_preserves_url_without_trailing_slash(self, mock_token_provider):
        """Test that URL without trailing slash is preserved."""
        client = OnenoteClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        assert client._connection_runtime_url == "https://example.azure.com/connections/test"


class TestOnenoteClientLifecycle:
    """Tests for OnenoteClient lifecycle methods."""

    @pytest.mark.asyncio
    async def test_close(self, mock_token_provider):
        """Test close method calls http_client.close."""
        client = OnenoteClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        with patch.object(client._http_client, 'close', new_callable=AsyncMock) as mock_close:
            await client.close()
            mock_close.assert_called_once()

    @pytest.mark.asyncio
    async def test_context_manager(self, mock_token_provider):
        """Test async context manager functionality."""
        with patch.object(OnenoteClient, 'close', new_callable=AsyncMock) as mock_close:
            async with OnenoteClient(
                "https://example.azure.com/connections/test",
                token_provider=mock_token_provider
            ) as client:
                assert isinstance(client, OnenoteClient)

            mock_close.assert_called_once()


class TestGetNotebooksAsync:
    """Tests for get_notebooks_async method."""

    @pytest.mark.asyncio
    async def test_success(self, mock_token_provider):
        """Test successful get notebooks request."""
        client = OnenoteClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(
            status=200,
            text='{"value": [{"fileName": "Work Notes", "key": "nb-123"}]}'
        )

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ) as mock_send:
            result = await client.get_notebooks_async()

            mock_send.assert_called_once()
            assert result is not None
            assert "value" in result

    @pytest.mark.asyncio
    async def test_empty_response_returns_none(self, mock_token_provider):
        """Test that empty response returns None."""
        client = OnenoteClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(status=200, text='')

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ):
            result = await client.get_notebooks_async()
            assert result is None

    @pytest.mark.asyncio
    async def test_error_response_raises_exception(self, mock_token_provider):
        """Test that error response raises ConnectorException."""
        client = OnenoteClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(status=401, text='{"error": "Unauthorized"}')

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ):
            with pytest.raises(ConnectorException):
                await client.get_notebooks_async()


class TestGetSectionsInNotebookAsync:
    """Tests for get_sections_in_notebook_async method."""

    @pytest.mark.asyncio
    async def test_success(self, mock_token_provider):
        """Test successful get sections request."""
        client = OnenoteClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(
            status=200,
            text='{"value": [{"name": "Section 1", "id": "sec-123"}]}'
        )

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ) as mock_send:
            result = await client.get_sections_in_notebook_async(notebook_key="nb-123")

            mock_send.assert_called_once()
            call_args = mock_send.call_args
            assert "notebookKey=nb-123" in call_args[0][1]
            assert result is not None

    @pytest.mark.asyncio
    async def test_error_response_raises_exception(self, mock_token_provider):
        """Test that error response raises ConnectorException."""
        client = OnenoteClient(
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
            with pytest.raises(ConnectorException):
                await client.get_sections_in_notebook_async(notebook_key="invalid")


class TestCreateSectionInNotebookAsync:
    """Tests for create_section_in_notebook_async method."""

    @pytest.mark.asyncio
    async def test_success(self, mock_token_provider):
        """Test successful create section request."""
        client = OnenoteClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(
            status=201,
            text='{"id": "sec-new", "name": "New Section"}'
        )

        section_request = CreateSectionRequest(name="New Section")

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ) as mock_send:
            result = await client.create_section_in_notebook_async(
                input=section_request,
                notebook_key="nb-123"
            )

            mock_send.assert_called_once()
            call_args = mock_send.call_args
            assert call_args[0][0] == "POST"
            assert result is not None
            assert result["name"] == "New Section"

    @pytest.mark.asyncio
    async def test_empty_response_returns_none(self, mock_token_provider):
        """Test that empty response returns None."""
        client = OnenoteClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(status=201, text='')

        section_request = CreateSectionRequest(name="New Section")

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ):
            result = await client.create_section_in_notebook_async(
                input=section_request,
                notebook_key="nb-123"
            )
            assert result is None


class TestGetPagesInSectionAsync:
    """Tests for get_pages_in_section_async method."""

    @pytest.mark.asyncio
    async def test_success(self, mock_token_provider):
        """Test successful get pages request."""
        client = OnenoteClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(
            status=200,
            text='{"value": [{"id": "page-1", "title": "My Page"}]}'
        )

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ) as mock_send:
            result = await client.get_pages_in_section_async(
                notebook_key="nb-123",
                section_id="sec-123"
            )

            mock_send.assert_called_once()
            call_args = mock_send.call_args
            path = call_args[0][1]
            assert "notebookKey=nb-123" in path
            assert "sectionId=sec-123" in path
            assert result is not None

    @pytest.mark.asyncio
    async def test_error_response_raises_exception(self, mock_token_provider):
        """Test that error response raises ConnectorException."""
        client = OnenoteClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(status=403, text='{"error": "Forbidden"}')

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ):
            with pytest.raises(ConnectorException):
                await client.get_pages_in_section_async(
                    notebook_key="nb-123",
                    section_id="sec-123"
                )


class TestCreatePageInSectionAsync:
    """Tests for create_page_in_section_async method."""

    @pytest.mark.asyncio
    async def test_success(self, mock_token_provider):
        """Test successful create page in section request."""
        client = OnenoteClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(
            status=201,
            text='{"id": "page-new", "title": "New Page"}'
        )

        page_input = CreatePageInSectionInput(
            additional_properties={"title": "New Page"}
        )

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ) as mock_send:
            result = await client.create_page_in_section_async(
                input=page_input,
                notebook_key="nb-123",
                section_id="sec-123"
            )

            mock_send.assert_called_once()
            call_args = mock_send.call_args
            assert call_args[0][0] == "POST"
            assert result is not None


class TestCreatePageInQuickNotesAsync:
    """Tests for create_page_in_quick_notes_async method."""

    @pytest.mark.asyncio
    async def test_success(self, mock_token_provider):
        """Test successful create page in quick notes request."""
        client = OnenoteClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(
            status=201,
            text='{"id": "page-quick", "title": "Quick Note"}'
        )

        page_input = CreatePageInQuickNotesInput(
            additional_properties={"title": "Quick Note"}
        )

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ) as mock_send:
            result = await client.create_page_in_quick_notes_async(input=page_input)

            mock_send.assert_called_once()
            call_args = mock_send.call_args
            assert call_args[0][0] == "POST"
            assert result is not None

    @pytest.mark.asyncio
    async def test_error_response_raises_exception(self, mock_token_provider):
        """Test that error response raises ConnectorException."""
        client = OnenoteClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(status=400, text='{"error": "Bad request"}')

        page_input = CreatePageInQuickNotesInput()

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ):
            with pytest.raises(ConnectorException):
                await client.create_page_in_quick_notes_async(input=page_input)


class TestDeletePageAsync:
    """Tests for delete_page_async method."""

    @pytest.mark.asyncio
    async def test_success(self, mock_token_provider):
        """Test successful delete page request."""
        client = OnenoteClient(
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
            await client.delete_page_async(
                notebook_key="nb-123",
                section_id="sec-123",
                page_id="page-123"
            )

            mock_send.assert_called_once()
            call_args = mock_send.call_args
            assert call_args[0][0] == "DELETE"
            path = call_args[0][1]
            assert "notebookKey=nb-123" in path
            assert "sectionId=sec-123" in path
            assert "pageId=page-123" in path


class TestGetPageContentAsync:
    """Tests for get_page_content_async method."""

    @pytest.mark.asyncio
    async def test_success(self, mock_token_provider):
        """Test successful get page content request."""
        client = OnenoteClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(
            status=200,
            text='{"content": "<html><body>Page content</body></html>"}'
        )

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ) as mock_send:
            result = await client.get_page_content_async(
                notebook_key="nb-123",
                section_id="sec-123",
                page_id="page-123",
                pre_authenticated="true"
            )

            mock_send.assert_called_once()
            call_args = mock_send.call_args
            path = call_args[0][1]
            assert "preAuthenticated=true" in path
            assert result is not None

    @pytest.mark.asyncio
    async def test_error_response_raises_exception(self, mock_token_provider):
        """Test that error response raises ConnectorException."""
        client = OnenoteClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(status=404, text='{"error": "Page not found"}')

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ):
            with pytest.raises(ConnectorException):
                await client.get_page_content_async(
                    notebook_key="nb-123",
                    section_id="sec-123",
                    page_id="invalid",
                    pre_authenticated=None
                )


class TestUpdatePageContentAsync:
    """Tests for update_page_content_async method."""

    @pytest.mark.asyncio
    async def test_success(self, mock_token_provider):
        """Test successful update page content request."""
        client = OnenoteClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(
            status=200,
            text='{"result": "success"}'
        )

        update_request = UpdatePageContentRequest(
            additional_properties={"target": "body", "action": "append"}
        )

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ) as mock_send:
            result = await client.update_page_content_async(
                input=update_request,
                notebook_key="nb-123",
                section_id="sec-123",
                page_id="page-123"
            )

            mock_send.assert_called_once()
            call_args = mock_send.call_args
            assert call_args[0][0] == "PATCH"
            assert result is not None


class TestOnNewSectionInNotebookAsync:
    """Tests for on_new_section_in_notebook_async method."""

    @pytest.mark.asyncio
    async def test_success(self, mock_token_provider):
        """Test successful trigger registration."""
        client = OnenoteClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(
            status=200,
            text='{"value": [{"id": "sec-1", "name": "New Section"}]}'
        )

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ) as mock_send:
            result = await client.on_new_section_in_notebook_async(notebook_key="nb-123")

            mock_send.assert_called_once()
            assert result is not None

    @pytest.mark.asyncio
    async def test_error_response_raises_exception(self, mock_token_provider):
        """Test that error response raises ConnectorException."""
        client = OnenoteClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(status=500, text='{"error": "Internal error"}')

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ):
            with pytest.raises(ConnectorException):
                await client.on_new_section_in_notebook_async(notebook_key="nb-123")


class TestOnNewSectionGroupInNotebookAsync:
    """Tests for on_new_section_group_in_notebook_async method."""

    @pytest.mark.asyncio
    async def test_success(self, mock_token_provider):
        """Test successful trigger registration."""
        client = OnenoteClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(
            status=200,
            text='{"value": [{"id": "grp-1", "name": "New Group"}]}'
        )

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ) as mock_send:
            result = await client.on_new_section_group_in_notebook_async(notebook_key="nb-123")

            mock_send.assert_called_once()
            assert result is not None


class TestOnNewPageInSectionAsync:
    """Tests for on_new_page_in_section_async method."""

    @pytest.mark.asyncio
    async def test_success(self, mock_token_provider):
        """Test successful trigger registration."""
        client = OnenoteClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(
            status=200,
            text='{"value": [{"id": "page-1", "title": "New Page"}]}'
        )

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ) as mock_send:
            result = await client.on_new_page_in_section_async(
                notebook_key="nb-123",
                section_id="sec-123"
            )

            mock_send.assert_called_once()
            call_args = mock_send.call_args
            path = call_args[0][1]
            assert "notebookKey=nb-123" in path
            assert "sectionId=sec-123" in path
            assert result is not None


class TestDataclasses:
    """Tests for dataclass serialization and defaults."""

    def test_create_section_in_notebook_response_defaults(self):
        """Test CreateSectionInNotebookResponse default values."""
        response = CreateSectionInNotebookResponse()
        assert response.context is None
        assert response.id is None
        assert response.name is None
        assert response.is_default is None

    def test_create_section_in_notebook_response_with_values(self):
        """Test CreateSectionInNotebookResponse with values."""
        response = CreateSectionInNotebookResponse(
            id="sec-123",
            name="My Section",
            is_default=True,
            created_by="John Doe"
        )
        assert response.id == "sec-123"
        assert response.name == "My Section"
        assert response.is_default is True

    def test_create_page_in_section_input_defaults(self):
        """Test CreatePageInSectionInput default values."""
        input_obj = CreatePageInSectionInput()
        assert input_obj.additional_properties == {}

    def test_create_page_in_section_input_with_values(self):
        """Test CreatePageInSectionInput with values."""
        input_obj = CreatePageInSectionInput(
            additional_properties={"title": "New Page", "content": "<p>Hello</p>"}
        )
        assert input_obj.additional_properties["title"] == "New Page"

    def test_page_defaults(self):
        """Test Page default values."""
        page = Page()
        assert page.title is None
        assert page.id is None
        assert page.content_url is None

    def test_page_with_values(self):
        """Test Page with values."""
        page = Page(
            id="page-123",
            title="My Page",
            content_url="https://example.com/content"
        )
        assert page.id == "page-123"
        assert page.title == "My Page"

    def test_get_pages_in_section_response_defaults(self):
        """Test GetPagesInSectionResponse default values."""
        response = GetPagesInSectionResponse()
        assert response.context is None
        assert response.value is None

    def test_create_page_in_quick_notes_input_defaults(self):
        """Test CreatePageInQuickNotesInput default values."""
        input_obj = CreatePageInQuickNotesInput()
        assert input_obj.additional_properties == {}

    def test_notebook_defaults(self):
        """Test Notebook default values."""
        notebook = Notebook()
        assert notebook.file_name is None
        assert notebook.key is None

    def test_notebook_with_values(self):
        """Test Notebook with values."""
        notebook = Notebook(file_name="Work Notes", key="nb-123")
        assert notebook.file_name == "Work Notes"
        assert notebook.key == "nb-123"

    def test_get_sections_in_notebook_response_defaults(self):
        """Test GetSectionsInNotebookResponse default values."""
        response = GetSectionsInNotebookResponse()
        assert response.value is None

    def test_new_section_response_defaults(self):
        """Test NewSectionResponse default values."""
        response = NewSectionResponse()
        assert response.value is None

    def test_new_section_group_response_defaults(self):
        """Test NewSectionGroupResponse default values."""
        response = NewSectionGroupResponse()
        assert response.value is None

    def test_new_page_response_defaults(self):
        """Test NewPageResponse default values."""
        response = NewPageResponse()
        assert response.value is None

    def test_create_section_request_defaults(self):
        """Test CreateSectionRequest default values."""
        request = CreateSectionRequest()
        assert request.name is None

    def test_create_section_request_with_values(self):
        """Test CreateSectionRequest with values."""
        request = CreateSectionRequest(name="New Section")
        assert request.name == "New Section"

    def test_update_page_content_request_defaults(self):
        """Test UpdatePageContentRequest default values."""
        request = UpdatePageContentRequest()
        assert request.additional_properties == {}

    def test_get_page_response_defaults(self):
        """Test GetPageResponse default values."""
        response = GetPageResponse()
        assert response.context is None
        assert response.value is None

    def test_parent_notebook_defaults(self):
        """Test ParentNotebook default values."""
        parent = ParentNotebook()
        assert parent.id is None
        assert parent.name is None
        assert parent.self is None

    def test_parent_notebook_with_values(self):
        """Test ParentNotebook with values."""
        parent = ParentNotebook(
            id="nb-123",
            name="Work Notebook",
            self="https://example.com/notebooks/nb-123"
        )
        assert parent.id == "nb-123"
        assert parent.name == "Work Notebook"

    def test_link_defaults(self):
        """Test Link default values."""
        link = Link()
        assert link.one_note_client_url is None
        assert link.one_note_web_url is None

    def test_one_note_client_url_defaults(self):
        """Test OneNoteClientUrl default values."""
        url = OneNoteClientUrl()
        assert url.href is None

    def test_one_note_client_url_with_values(self):
        """Test OneNoteClientUrl with values."""
        url = OneNoteClientUrl(href="onenote:https://example.com/notebook")
        assert url.href == "onenote:https://example.com/notebook"

    def test_one_note_web_url_defaults(self):
        """Test OneNoteWebUrl default values."""
        url = OneNoteWebUrl()
        assert url.href is None

    def test_section_list_item_defaults(self):
        """Test SectionListItem default values."""
        item = SectionListItem()
        assert item.name is None
        assert item.pages_url is None
        assert item.id is None

    def test_section_list_item_with_values(self):
        """Test SectionListItem with values."""
        item = SectionListItem(
            id="sec-123",
            name="Section 1",
            pages_url="https://example.com/pages"
        )
        assert item.id == "sec-123"
        assert item.name == "Section 1"

    def test_section_response_defaults(self):
        """Test SectionResponse default values."""
        response = SectionResponse()
        assert response.id is None
        assert response.name is None
        assert response.is_default is None

    def test_section_response_with_values(self):
        """Test SectionResponse with values."""
        response = SectionResponse(
            id="sec-123",
            name="My Section",
            is_default=False,
            created_by="John Doe"
        )
        assert response.id == "sec-123"
        assert response.is_default is False

    def test_section_group_response_defaults(self):
        """Test SectionGroupResponse default values."""
        response = SectionGroupResponse()
        assert response.id is None
        assert response.name is None

    def test_section_group_response_with_values(self):
        """Test SectionGroupResponse with values."""
        response = SectionGroupResponse(
            id="grp-123",
            name="My Group",
            sections_url="https://example.com/sections"
        )
        assert response.id == "grp-123"
        assert response.name == "My Group"
