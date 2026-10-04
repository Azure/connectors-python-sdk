# Copyright (c) Microsoft Corporation. All rights reserved.

"""Unit tests for PowerbiClient."""

from unittest.mock import AsyncMock, patch

import pytest

from azure.core.credentials import AzureKeyCredential
from azure.connectors.powerbi import PowerbiClient, UpdateGoalRequest, QuerySpecification
from azure.connectors.sdk import (
    ConnectorException,
)
from tests.conftest import MockResponse


class TestPowerbiClientInitialization:
    """Tests for PowerbiClient initialization."""

    def test_init_with_valid_url_and_defaults(self):
        """Test initialization with valid URL and default parameters."""
        client = PowerbiClient("https://example.azure.com/connections/test",
                               AzureKeyCredential("test-key"))

        assert client._connection_runtime_url == "https://example.azure.com/connections/test"
        assert client.connector_name == "powerbi"
        assert isinstance(client._http_client._credential, AzureKeyCredential)

    def test_init_with_trailing_slash(self):
        """Test that trailing slash is removed from URL."""
        client = PowerbiClient("https://example.azure.com/connections/test/",
                               AzureKeyCredential("test-key"))

        assert client._connection_runtime_url == "https://example.azure.com/connections/test"

    def test_init_with_custom_credential(self, mock_credential):
        """Test initialization with custom token provider."""
        client = PowerbiClient(
            "https://example.azure.com/connections/test",
            credential=mock_credential,
        )

        assert client._http_client._credential is mock_credential

    def test_init_with_custom_settings(self, mock_credential):
        """Test initialization with custom pipeline settings."""
        client = PowerbiClient(
            "https://example.azure.com/connections/test",
            credential=mock_credential,
            timeout_seconds=60.0,
            max_retry_attempts=5,
        )
        assert client._http_client._timeout_seconds == 60.0

    def test_init_with_empty_url_raises_error(self):
        """Test that empty URL raises ValueError."""
        with pytest.raises(ValueError, match="connection_runtime_url cannot be None or empty"):
            PowerbiClient("", AzureKeyCredential("test-key"))

    def test_init_with_none_url_raises_error(self):
        """Test that None URL raises ValueError."""
        with pytest.raises(ValueError, match="connection_runtime_url cannot be None or empty"):
            PowerbiClient(None, AzureKeyCredential("test-key"))

    def test_connector_name_property(self, mock_credential):
        """Test connector_name property returns 'powerbi'."""
        client = PowerbiClient(
            "https://example.azure.com/connections/test",
            credential=mock_credential,
        )

        assert client.connector_name == "powerbi"


class TestPowerbiClientLifecycle:
    """Tests for PowerbiClient lifecycle methods."""

    @pytest.mark.asyncio
    async def test_close(self, mock_credential):
        """Test close method calls http_client.close."""
        client = PowerbiClient(
            "https://example.azure.com/connections/test",
            credential=mock_credential,
        )

        with patch.object(client._http_client, "close", new_callable=AsyncMock) as mock_close:
            await client.close()
            mock_close.assert_called_once()

    @pytest.mark.asyncio
    async def test_context_manager(self, mock_credential):
        """Test async context manager functionality."""
        with patch.object(PowerbiClient, "close", new_callable=AsyncMock) as mock_close:
            async with PowerbiClient(
                "https://example.azure.com/connections/test",
                credential=mock_credential,
            ) as client:
                assert isinstance(client, PowerbiClient)

            mock_close.assert_called_once()


class TestListGroupsAsync:
    """Tests for list_groups_async method."""

    @pytest.mark.asyncio
    async def test_success(self, mock_credential):
        """Test successful list groups request."""
        client = PowerbiClient(
            "https://example.azure.com/connections/test",
            credential=mock_credential,
        )

        mock_response = MockResponse(status=200, text='{"value": [{"id": "group-1"}]}')

        with patch.object(
            client._http_client,
            "send_async",
            new_callable=AsyncMock,
            return_value=mock_response,
        ) as mock_send:
            result = await client.list_groups_async()

            mock_send.assert_called_once()
            method, path = mock_send.call_args[0][0], mock_send.call_args[0][1]
            assert method == "GET"
            assert "/v1.0/myorg/groups" in path
            assert "pbi_source=powerAutomate" in path
            assert result is not None
            assert "value" in result

    @pytest.mark.asyncio
    async def test_empty_response_returns_none(self, mock_credential):
        """Test that empty response returns None."""
        client = PowerbiClient(
            "https://example.azure.com/connections/test",
            credential=mock_credential,
        )

        mock_response = MockResponse(status=200, text="")

        with patch.object(
            client._http_client,
            "send_async",
            new_callable=AsyncMock,
            return_value=mock_response,
        ):
            result = await client.list_groups_async()
            assert result is None

    @pytest.mark.asyncio
    async def test_error_response_raises_exception(self, mock_credential):
        """Test that error response raises ConnectorException."""
        client = PowerbiClient(
            "https://example.azure.com/connections/test",
            credential=mock_credential,
        )

        mock_response = MockResponse(status=403, text='{"error": "Forbidden"}')

        with patch.object(
            client._http_client,
            "send_async",
            new_callable=AsyncMock,
            return_value=mock_response,
        ):
            with pytest.raises(ConnectorException):
                await client.list_groups_async()


class TestListDatasetsAsync:
    """Tests for list_datasets_async method."""

    @pytest.mark.asyncio
    async def test_success(self, mock_credential):
        """Test successful list datasets request."""
        client = PowerbiClient(
            "https://example.azure.com/connections/test",
            credential=mock_credential,
        )

        mock_response = MockResponse(status=200, text='{"value": [{"id": "dataset-1"}]}')

        with patch.object(
            client._http_client,
            "send_async",
            new_callable=AsyncMock,
            return_value=mock_response,
        ) as mock_send:
            result = await client.list_datasets_async(groupid="group-123")

            mock_send.assert_called_once()
            method, path = mock_send.call_args[0][0], mock_send.call_args[0][1]
            assert method == "GET"
            assert "/groups/group-123/datasets" in path
            assert "pbi_source=powerAutomate" in path
            assert result is not None

    @pytest.mark.asyncio
    async def test_error_response_raises_exception(self, mock_credential):
        """Test that error response raises ConnectorException."""
        client = PowerbiClient(
            "https://example.azure.com/connections/test",
            credential=mock_credential,
        )

        mock_response = MockResponse(status=404, text='{"error": "Not found"}')

        with patch.object(
            client._http_client,
            "send_async",
            new_callable=AsyncMock,
            return_value=mock_response,
        ):
            with pytest.raises(ConnectorException):
                await client.list_datasets_async(groupid="missing-group")


class TestExecuteDatasetQueryAsync:
    """Tests for execute_dataset_query_async method."""

    @pytest.mark.asyncio
    async def test_success(self, mock_credential):
        """Test successful execute dataset query request."""
        client = PowerbiClient(
            "https://example.azure.com/connections/test",
            credential=mock_credential,
        )

        query = QuerySpecification()
        mock_response = MockResponse(status=200, text='{"results": [{"tables": []}]}')

        with patch.object(
            client._http_client,
            "send_async",
            new_callable=AsyncMock,
            return_value=mock_response,
        ) as mock_send:
            result = await client.execute_dataset_query_async(
                input=query,
                groupid="group-123",
                datasetid="dataset-456",
            )

            mock_send.assert_called_once()
            method, path = mock_send.call_args[0][0], mock_send.call_args[0][1]
            body = mock_send.call_args[1].get("body")
            assert method == "POST"
            assert "/groups/group-123/datasets/dataset-456/executeQueries" in path
            assert "pbi_source=powerAutomate" in path
            assert body is query
            assert result is not None
            assert "results" in result

    @pytest.mark.asyncio
    async def test_error_response_raises_exception(self, mock_credential):
        """Test that error response raises ConnectorException."""
        client = PowerbiClient(
            "https://example.azure.com/connections/test",
            credential=mock_credential,
        )

        query = QuerySpecification()
        mock_response = MockResponse(status=500, text='{"error": "Server error"}')

        with patch.object(
            client._http_client,
            "send_async",
            new_callable=AsyncMock,
            return_value=mock_response,
        ):
            with pytest.raises(ConnectorException):
                await client.execute_dataset_query_async(
                    input=query,
                    groupid="group-123",
                    datasetid="dataset-456",
                )


class TestRefreshDatasetAsync:
    """Tests for refresh_dataset_async method."""

    @pytest.mark.asyncio
    async def test_success(self, mock_credential):
        """Test successful refresh dataset request."""
        client = PowerbiClient(
            "https://example.azure.com/connections/test",
            credential=mock_credential,
        )

        mock_response = MockResponse(status=202, text="")

        with patch.object(
            client._http_client,
            "send_async",
            new_callable=AsyncMock,
            return_value=mock_response,
        ) as mock_send:
            result = await client.refresh_dataset_async(
                groupid="group-123",
                datasetid="dataset-456",
            )

            mock_send.assert_called_once()
            method, path = mock_send.call_args[0][0], mock_send.call_args[0][1]
            assert method == "POST"
            assert "/groups/group-123/datasets/dataset-456/refreshes" in path
            assert "pbi_source=powerAutomate" in path
            assert result is None

    @pytest.mark.asyncio
    async def test_error_response_raises_exception(self, mock_credential):
        """Test that error response raises ConnectorException."""
        client = PowerbiClient(
            "https://example.azure.com/connections/test",
            credential=mock_credential,
        )

        mock_response = MockResponse(status=400, text='{"error": "Bad request"}')

        with patch.object(
            client._http_client,
            "send_async",
            new_callable=AsyncMock,
            return_value=mock_response,
        ):
            with pytest.raises(ConnectorException):
                await client.refresh_dataset_async(
                    groupid="group-123",
                    datasetid="dataset-456",
                )


class TestUpdateGoalAsync:
    """Tests for update_goal_async method (PATCH with body)."""

    @pytest.mark.asyncio
    async def test_success_sends_body(self, mock_credential):
        """Test PATCH sends input body."""
        client = PowerbiClient(
            "https://example.azure.com/connections/test",
            credential=mock_credential,
        )
        payload = UpdateGoalRequest()
        mock_response = MockResponse(status=200, text='{"id": "goal-1"}')

        with patch.object(
            client._http_client,
            "send_async",
            new_callable=AsyncMock,
            return_value=mock_response,
        ) as mock_send:
            await client.update_goal_async(
                input=payload,
                groupid="group-1",
                scorecard_id="sc-1",
                goal_id="goal-1",
            )

            mock_send.assert_called_once()
            method, path = mock_send.call_args[0][0], mock_send.call_args[0][1]
            body = mock_send.call_args[1].get("body")
            assert method == "PATCH"
            assert "/groups/group-1/internalScorecards(sc-1)/goals(goal-1)" in path
            assert body is payload

    @pytest.mark.asyncio
    async def test_error_response_raises_exception(self, mock_credential):
        """Test PATCH error path raises ConnectorException."""
        client = PowerbiClient(
            "https://example.azure.com/connections/test",
            credential=mock_credential,
        )
        payload = UpdateGoalRequest()
        mock_response = MockResponse(status=403, text='{"error": "Forbidden"}')

        with patch.object(
            client._http_client,
            "send_async",
            new_callable=AsyncMock,
            return_value=mock_response,
        ):
            with pytest.raises(ConnectorException):
                await client.update_goal_async(
                    input=payload,
                    groupid="group-1",
                    scorecard_id="sc-1",
                    goal_id="goal-1",
                )
