# Copyright (c) Microsoft Corporation. All rights reserved.

"""Unit tests for JiraClient."""

from unittest.mock import AsyncMock, patch

import pytest

from azure.connectors.jira import JiraClient, CreateIssueInput, EditIssueInput
from azure.connectors.sdk import (
    ConnectorClientOptions,
    ConnectorException,
    ManagedIdentityTokenProvider,
)
from tests.conftest import MockResponse


class TestJiraClientInitialization:
    """Tests for JiraClient initialization."""

    def test_init_with_valid_url_and_defaults(self):
        """Test initialization with valid URL and default parameters."""
        client = JiraClient("https://example.azure.com/connections/test")

        assert client._connection_runtime_url == "https://example.azure.com/connections/test"
        assert client.connector_name == "jira"
        assert isinstance(client._http_client._token_provider, ManagedIdentityTokenProvider)

    def test_init_with_trailing_slash(self):
        """Test that trailing slash is removed from URL."""
        client = JiraClient("https://example.azure.com/connections/test/")

        assert client._connection_runtime_url == "https://example.azure.com/connections/test"

    def test_init_with_custom_token_provider(self, mock_token_provider):
        """Test initialization with custom token provider."""
        client = JiraClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider,
        )

        assert client._http_client._token_provider is mock_token_provider

    def test_init_with_custom_options(self, mock_token_provider):
        """Test initialization with custom options."""
        options = ConnectorClientOptions(timeout_seconds=60.0, max_retry_attempts=5)
        client = JiraClient(
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
            JiraClient("")

    def test_init_with_none_url_raises_error(self):
        """Test that None URL raises ValueError."""
        with pytest.raises(ValueError, match="connection_runtime_url cannot be None or empty"):
            JiraClient(None)

    def test_connector_name_property(self, mock_token_provider):
        """Test connector_name property returns 'jira'."""
        client = JiraClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider,
        )

        assert client.connector_name == "jira"


class TestJiraClientLifecycle:
    """Tests for JiraClient lifecycle methods."""

    @pytest.mark.asyncio
    async def test_close(self, mock_token_provider):
        """Test close method calls http_client.close."""
        client = JiraClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider,
        )

        with patch.object(client._http_client, "close", new_callable=AsyncMock) as mock_close:
            await client.close()
            mock_close.assert_called_once()

    @pytest.mark.asyncio
    async def test_context_manager(self, mock_token_provider):
        """Test async context manager functionality."""
        with patch.object(JiraClient, "close", new_callable=AsyncMock) as mock_close:
            async with JiraClient(
                "https://example.azure.com/connections/test",
                token_provider=mock_token_provider,
            ) as client:
                assert isinstance(client, JiraClient)

            mock_close.assert_called_once()


class TestListResourcesAsync:
    """Tests for list_resources_async method."""

    @pytest.mark.asyncio
    async def test_success(self, mock_token_provider):
        """Test successful resource listing."""
        client = JiraClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider,
        )
        mock_response = MockResponse(
            status=200,
            text='{"value": [{"id": "site-1"}]}',
        )

        with patch.object(
            client._http_client,
            "send_async",
            new_callable=AsyncMock,
            return_value=mock_response,
        ) as mock_send:
            result = await client.list_resources_async()

            mock_send.assert_called_once()
            method, path = mock_send.call_args[0][0], mock_send.call_args[0][1]
            assert method == "GET"
            assert "/oauth/token/accessible-resources" in path
            assert result is not None
            assert "value" in result

    @pytest.mark.asyncio
    async def test_error_response_raises_exception(self, mock_token_provider):
        """Test resource listing error path."""
        client = JiraClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider,
        )
        mock_response = MockResponse(
            status=401,
            text='{"error": "Unauthorized"}',
        )

        with patch.object(
            client._http_client,
            "send_async",
            new_callable=AsyncMock,
            return_value=mock_response,
        ):
            with pytest.raises(ConnectorException):
                await client.list_resources_async()


class TestListIssuesAsync:
    """Tests for list_issues_async method."""

    @pytest.mark.asyncio
    async def test_success(self, mock_token_provider):
        """Test successful issue listing with query parameters."""
        client = JiraClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider,
        )
        mock_response = MockResponse(
            status=200,
            text='{"issues": [{"key": "PROJ-1"}], "maxResults": 50}',
        )

        with patch.object(
            client._http_client,
            "send_async",
            new_callable=AsyncMock,
            return_value=mock_response,
        ) as mock_send:
            result = await client.list_issues_async()

            mock_send.assert_called_once()
            method, path = mock_send.call_args[0][0], mock_send.call_args[0][1]
            assert method == "GET"
            assert "/2/search" in path
            assert "jql=created%20%3E%3D%20-3650d" in path
            assert result is not None
            assert "issues" in result

    @pytest.mark.asyncio
    async def test_error_response_raises_exception(self, mock_token_provider):
        """Test issue listing error path."""
        client = JiraClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider,
        )
        mock_response = MockResponse(
            status=500,
            text='{"error": "Server error"}',
        )

        with patch.object(
            client._http_client,
            "send_async",
            new_callable=AsyncMock,
            return_value=mock_response,
        ):
            with pytest.raises(ConnectorException):
                await client.list_issues_async()


class TestCreateIssueAsync:
    """Tests for create_issue_async method."""

    @pytest.mark.asyncio
    async def test_success(self, mock_token_provider):
        """Test successful issue creation."""
        client = JiraClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider,
        )
        payload = CreateIssueInput(
            additional_properties={"fields": {"project": {"key": "PROJ"}}},
        )
        mock_response = MockResponse(
            status=201,
            text='{"id": "10001", "key": "PROJ-1"}',
        )

        with patch.object(
            client._http_client,
            "send_async",
            new_callable=AsyncMock,
            return_value=mock_response,
        ) as mock_send:
            result = await client.create_issue_async(
                input=payload,
                project_key="PROJ",
                issue_type_ids="10001",
            )

            mock_send.assert_called_once()
            method, path = mock_send.call_args[0][0], mock_send.call_args[0][1]
            body = mock_send.call_args[1].get("body")
            assert method == "POST"
            assert "/v3/issue" in path
            assert "projectKey=PROJ" in path
            assert "issueTypeIds=10001" in path
            assert body is payload
            assert result is not None
            assert result.get("key") == "PROJ-1"

    @pytest.mark.asyncio
    async def test_error_response_raises_exception(self, mock_token_provider):
        """Test create issue error path."""
        client = JiraClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider,
        )
        payload = CreateIssueInput(additional_properties={"fields": {}})
        mock_response = MockResponse(
            status=400,
            text='{"error": "Bad request"}',
        )

        with patch.object(
            client._http_client,
            "send_async",
            new_callable=AsyncMock,
            return_value=mock_response,
        ):
            with pytest.raises(ConnectorException):
                await client.create_issue_async(
                    input=payload,
                    project_key="PROJ",
                    issue_type_ids="10001",
                )


class TestGetIssueAsync:
    """Tests for get_issue_async method."""

    @pytest.mark.asyncio
    async def test_success(self, mock_token_provider):
        """Test successful get issue request."""
        client = JiraClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider,
        )
        mock_response = MockResponse(
            status=200,
            text='{"key": "PROJ-1"}',
        )

        with patch.object(
            client._http_client,
            "send_async",
            new_callable=AsyncMock,
            return_value=mock_response,
        ) as mock_send:
            result = await client.get_issue_async(issue_key="PROJ-1")

            mock_send.assert_called_once()
            method, path = mock_send.call_args[0][0], mock_send.call_args[0][1]
            assert method == "GET"
            assert "/v2/issue/PROJ-1" in path
            assert result is not None
            assert result.get("key") == "PROJ-1"


class TestDeleteProjectAsync:
    """Tests for delete_project_async method (DELETE)."""

    @pytest.mark.asyncio
    async def test_success(self, mock_token_provider):
        """Test successful project deletion."""
        client = JiraClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider,
        )
        mock_response = MockResponse(status=204, text="")

        with patch.object(
            client._http_client,
            "send_async",
            new_callable=AsyncMock,
            return_value=mock_response,
        ) as mock_send:
            await client.delete_project_async(project_id_or_key="PROJ")

            mock_send.assert_called_once()
            method, path = mock_send.call_args[0][0], mock_send.call_args[0][1]
            assert method == "DELETE"
            assert "/v2/project/PROJ" in path

    @pytest.mark.asyncio
    async def test_error_response_raises_exception(self, mock_token_provider):
        """Test DELETE error path raises ConnectorException."""
        client = JiraClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider,
        )
        mock_response = MockResponse(status=403, text='{"error": "Forbidden"}')

        with patch.object(
            client._http_client,
            "send_async",
            new_callable=AsyncMock,
            return_value=mock_response,
        ):
            with pytest.raises(ConnectorException):
                await client.delete_project_async(project_id_or_key="PROJ")


class TestEditIssueAsync:
    """Tests for edit_issue_async method (PUT with body)."""

    @pytest.mark.asyncio
    async def test_success_sends_body_and_returns_result(self, mock_token_provider):
        """Test PUT sends input body and returns result."""
        client = JiraClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider,
        )
        payload = EditIssueInput(fields={"summary": "Updated"})
        mock_response = MockResponse(status=200, text='{"key": "PROJ-1"}')

        with patch.object(
            client._http_client,
            "send_async",
            new_callable=AsyncMock,
            return_value=mock_response,
        ) as mock_send:
            result = await client.edit_issue_async(
                input=payload,
                issue_id_or_key="PROJ-1",
            )

            mock_send.assert_called_once()
            method, path = mock_send.call_args[0][0], mock_send.call_args[0][1]
            body = mock_send.call_args[1].get("body")
            assert method == "PUT"
            assert "/v2/3/issue/PROJ-1" in path
            assert body is payload
            assert result is not None

    @pytest.mark.asyncio
    async def test_error_response_raises_exception(self, mock_token_provider):
        """Test PUT error path raises ConnectorException."""
        client = JiraClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider,
        )
        payload = EditIssueInput(fields={})
        mock_response = MockResponse(status=400, text='{"error": "Bad request"}')

        with patch.object(
            client._http_client,
            "send_async",
            new_callable=AsyncMock,
            return_value=mock_response,
        ):
            with pytest.raises(ConnectorException):
                await client.edit_issue_async(
                    input=payload,
                    issue_id_or_key="PROJ-1",
                )
