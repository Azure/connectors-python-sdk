# Copyright (c) Microsoft Corporation. All rights reserved.

"""Unit tests for GithubClient."""

from unittest.mock import AsyncMock, patch

import pytest

from azure.connectors.github import (
    GithubClient,
    IssueBasicDetailsModel,
    PullRequestUpdateRequest,
    QueryRequest,
    RequestReviewersBody,
)
from azure.connectors.sdk import (
    ConnectorClientOptions,
    ConnectorException,
    ManagedIdentityTokenProvider,
)
from tests.conftest import MockResponse


class TestGithubClientInitialization:
    """Tests for GithubClient initialization."""

    def test_init_with_valid_url_and_defaults(self):
        """Test initialization with valid URL and default parameters."""
        client = GithubClient("https://example.azure.com/connections/test")

        assert client._connection_runtime_url == "https://example.azure.com/connections/test"
        assert client.connector_name == "github"
        assert isinstance(client._http_client._token_provider, ManagedIdentityTokenProvider)

    def test_init_with_trailing_slash(self):
        """Test that trailing slash is removed from URL."""
        client = GithubClient("https://example.azure.com/connections/test/")

        assert client._connection_runtime_url == "https://example.azure.com/connections/test"

    def test_init_with_custom_token_provider(self, mock_token_provider):
        """Test initialization with custom token provider."""
        client = GithubClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider,
        )

        assert client._http_client._token_provider is mock_token_provider

    def test_init_with_custom_options(self, mock_token_provider):
        """Test initialization with custom options."""
        options = ConnectorClientOptions(timeout_seconds=60.0, max_retry_attempts=5)
        client = GithubClient(
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
            GithubClient("")

    def test_init_with_none_url_raises_error(self):
        """Test that None URL raises ValueError."""
        with pytest.raises(ValueError, match="connection_runtime_url cannot be None or empty"):
            GithubClient(None)

    def test_connector_name_property(self, mock_token_provider):
        """Test connector_name property returns 'github'."""
        client = GithubClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider,
        )

        assert client.connector_name == "github"


class TestGithubClientLifecycle:
    """Tests for GithubClient lifecycle methods."""

    @pytest.mark.asyncio
    async def test_close(self, mock_token_provider):
        """Test close method calls http_client.close."""
        client = GithubClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider,
        )

        with patch.object(client._http_client, "close", new_callable=AsyncMock) as mock_close:
            await client.close()
            mock_close.assert_called_once()

    @pytest.mark.asyncio
    async def test_context_manager(self, mock_token_provider):
        """Test async context manager functionality."""
        with patch.object(GithubClient, "close", new_callable=AsyncMock) as mock_close:
            async with GithubClient(
                "https://example.azure.com/connections/test",
                token_provider=mock_token_provider,
            ) as client:
                assert isinstance(client, GithubClient)

            mock_close.assert_called_once()


class TestInvokeMcpServerAsync:
    """Tests for invoke_mcp_server_async method."""

    @pytest.mark.asyncio
    async def test_success_uses_acronym_aware_name(self, mock_token_provider):
        """Test invoking the MCP server through its acronym-aware method name."""
        client = GithubClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider,
        )
        payload = QueryRequest(jsonrpc="2.0", id="request-1", method="tools/list")
        mock_response = MockResponse(status=200, text="")

        with patch.object(
            client._http_client,
            "send_async",
            new_callable=AsyncMock,
            return_value=mock_response,
        ) as mock_send:
            await client.invoke_mcp_server_async(input=payload)

            mock_send.assert_called_once_with(
                "POST",
                "https://example.azure.com/connections/test/mcp",
                body=payload,
            )
            assert not hasattr(GithubClient, "invoke_m_c_p_server_async")

    @pytest.mark.asyncio
    async def test_error_response_raises_exception(self, mock_token_provider):
        """Test MCP server errors raise ConnectorException."""
        client = GithubClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider,
        )
        mock_response = MockResponse(status=500, text='{"error": "Server error"}')

        with patch.object(
            client._http_client,
            "send_async",
            new_callable=AsyncMock,
            return_value=mock_response,
        ):
            with pytest.raises(ConnectorException):
                await client.invoke_mcp_server_async(input=QueryRequest())


class TestGetUserAsync:
    """Tests for get_user_async method."""

    @pytest.mark.asyncio
    async def test_success(self, mock_token_provider):
        """Test successful authenticated user retrieval."""
        client = GithubClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider,
        )
        mock_response = MockResponse(
            status=200,
            text='{"login": "octocat", "id": 1}',
        )

        with patch.object(
            client._http_client,
            "send_async",
            new_callable=AsyncMock,
            return_value=mock_response,
        ) as mock_send:
            result = await client.get_user_async()

            mock_send.assert_called_once()
            method, path = mock_send.call_args[0][0], mock_send.call_args[0][1]
            assert method == "GET"
            assert path.endswith("/user")
            assert result is not None
            assert result.get("login") == "octocat"

    @pytest.mark.asyncio
    async def test_error_response_raises_exception(self, mock_token_provider):
        """Test get user error path."""
        client = GithubClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider,
        )
        mock_response = MockResponse(
            status=401,
            text='{"message": "Requires authentication"}',
        )

        with patch.object(
            client._http_client,
            "send_async",
            new_callable=AsyncMock,
            return_value=mock_response,
        ):
            with pytest.raises(ConnectorException):
                await client.get_user_async()


class TestCreateIssueAsync:
    """Tests for create_issue_async method."""

    @pytest.mark.asyncio
    async def test_success(self, mock_token_provider):
        """Test successful issue creation."""
        client = GithubClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider,
        )
        payload = IssueBasicDetailsModel(
            title="Connector SDK test issue",
            body="Created by unit test.",
        )
        mock_response = MockResponse(
            status=201,
            text='{"number": 123, "title": "Connector SDK test issue"}',
        )

        with patch.object(
            client._http_client,
            "send_async",
            new_callable=AsyncMock,
            return_value=mock_response,
        ) as mock_send:
            result = await client.create_issue_async(
                input=payload,
                repository_owner="octocat",
                repository_name="hello-world",
            )

            mock_send.assert_called_once()
            method, path = mock_send.call_args[0][0], mock_send.call_args[0][1]
            body = mock_send.call_args[1].get("body")
            assert method == "POST"
            assert "/repos/octocat/hello-world/issues" in path
            assert body is payload
            assert result is not None
            assert result.get("number") == 123

    @pytest.mark.asyncio
    async def test_error_response_raises_exception(self, mock_token_provider):
        """Test create issue error path."""
        client = GithubClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider,
        )
        payload = IssueBasicDetailsModel(title="", body="")
        mock_response = MockResponse(
            status=422,
            text='{"message": "Validation Failed"}',
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
                    repository_owner="octocat",
                    repository_name="hello-world",
                )


class TestGetIssuesAsync:
    """Tests for get_issues_async method."""

    @pytest.mark.asyncio
    async def test_success(self, mock_token_provider):
        """Test successful issue listing with filters."""
        client = GithubClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider,
        )
        mock_response = MockResponse(
            status=200,
            text='[{"number": 1, "title": "Issue one"}]',
        )

        with patch.object(
            client._http_client,
            "send_async",
            new_callable=AsyncMock,
            return_value=mock_response,
        ) as mock_send:
            result = await client.get_issues_async(
                repository_owner="octocat",
                repository_name="hello-world",
                state="open",
                per_page="10",
            )

            mock_send.assert_called_once()
            method, path = mock_send.call_args[0][0], mock_send.call_args[0][1]
            assert method == "GET"
            assert "/repos/octocat/hello-world/issues" in path
            assert "state=open" in path
            assert "per_page=10" in path
            assert isinstance(result, list)
            assert result[0].get("number") == 1

    @pytest.mark.asyncio
    async def test_error_response_raises_exception(self, mock_token_provider):
        """Test get issues error path."""
        client = GithubClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider,
        )
        mock_response = MockResponse(
            status=404,
            text='{"message": "Not Found"}',
        )

        with patch.object(
            client._http_client,
            "send_async",
            new_callable=AsyncMock,
            return_value=mock_response,
        ):
            with pytest.raises(ConnectorException):
                await client.get_issues_async(
                    repository_owner="octocat",
                    repository_name="hello-world",
                )


class TestUpdatePullRequestAsync:
    """Tests for update_pull_request_async method (PATCH with body)."""

    @pytest.mark.asyncio
    async def test_success_sends_body_and_returns_result(self, mock_token_provider):
        """Test PATCH sends input body and returns updated PR."""
        client = GithubClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider,
        )
        payload = PullRequestUpdateRequest(title="Updated title", state="closed")
        mock_response = MockResponse(
            status=200,
            text='{"number": 42, "state": "closed"}',
        )

        with patch.object(
            client._http_client,
            "send_async",
            new_callable=AsyncMock,
            return_value=mock_response,
        ) as mock_send:
            result = await client.update_pull_request_async(
                input=payload,
                repository_owner="octocat",
                repository_name="hello-world",
                pull_number="42",
            )

            mock_send.assert_called_once()
            method, path = mock_send.call_args[0][0], mock_send.call_args[0][1]
            body = mock_send.call_args[1].get("body")
            assert method == "PATCH"
            assert "/repos/octocat/hello-world/pulls/42" in path
            assert body is payload
            assert result is not None

    @pytest.mark.asyncio
    async def test_error_response_raises_exception(self, mock_token_provider):
        """Test PATCH error path raises ConnectorException."""
        client = GithubClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider,
        )
        payload = PullRequestUpdateRequest(title="")
        mock_response = MockResponse(
            status=422,
            text='{"message": "Validation Failed"}',
        )

        with patch.object(
            client._http_client,
            "send_async",
            new_callable=AsyncMock,
            return_value=mock_response,
        ):
            with pytest.raises(ConnectorException):
                await client.update_pull_request_async(
                    input=payload,
                    repository_owner="octocat",
                    repository_name="hello-world",
                    pull_number="42",
                )


class TestRemoveReviewersPullRequestAsync:
    """Tests for remove_reviewers_pull_request_async method (DELETE)."""

    @pytest.mark.asyncio
    async def test_success(self, mock_token_provider):
        """Test successful DELETE of PR reviewers."""
        client = GithubClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider,
        )
        payload = RequestReviewersBody(reviewers=["alice"])
        mock_response = MockResponse(status=200, text='{"number": 42}')

        with patch.object(
            client._http_client,
            "send_async",
            new_callable=AsyncMock,
            return_value=mock_response,
        ) as mock_send:
            await client.remove_reviewers_pull_request_async(
                input=payload,
                repository_owner="octocat",
                repository_name="hello-world",
                pull_number="42",
            )

            mock_send.assert_called_once()
            method = mock_send.call_args[0][0]
            assert method == "DELETE"

    @pytest.mark.asyncio
    async def test_error_response_raises_exception(self, mock_token_provider):
        """Test DELETE error path raises ConnectorException."""
        client = GithubClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider,
        )
        payload = RequestReviewersBody(reviewers=["alice"])
        mock_response = MockResponse(status=404, text='{"message": "Not Found"}')

        with patch.object(
            client._http_client,
            "send_async",
            new_callable=AsyncMock,
            return_value=mock_response,
        ):
            with pytest.raises(ConnectorException):
                await client.remove_reviewers_pull_request_async(
                    input=payload,
                    repository_owner="octocat",
                    repository_name="missing-repo",
                    pull_number="0",
                )
