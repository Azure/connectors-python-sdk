# Copyright (c) Microsoft Corporation. All rights reserved.

"""Unit tests for SalesforceClient."""

from unittest.mock import AsyncMock, patch

import pytest

from azure.connectors.salesforce import (
    CloseJobRequest,
    SalesforceClient,
    TRIGGER_OPERATIONS,
)
from azure.connectors.sdk import (
    ConnectorClientOptions,
    ManagedIdentityTokenProvider,
    ConnectorException,
)
from tests.conftest import MockResponse


class TestSalesforceClientInitialization:
    """Tests for SalesforceClient initialization."""

    def test_init_with_valid_url_and_defaults(self):
        """Test initialization with valid URL and default parameters."""
        client = SalesforceClient("https://example.azure.com/connections/test")

        assert client._connection_runtime_url == (
            "https://example.azure.com/connections/test"
        )
        assert client.connector_name == "salesforce"
        assert isinstance(
            client._http_client._token_provider, ManagedIdentityTokenProvider
        )

    def test_init_with_trailing_slash(self):
        """Test that trailing slash is removed from URL."""
        client = SalesforceClient("https://example.azure.com/connections/test/")

        assert client._connection_runtime_url == (
            "https://example.azure.com/connections/test"
        )

    def test_init_with_custom_token_provider(self, mock_token_provider):
        """Test initialization with custom token provider."""
        client = SalesforceClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider,
        )

        assert client._http_client._token_provider is mock_token_provider

    def test_init_with_custom_options(self, mock_token_provider):
        """Test initialization with custom options."""
        options = ConnectorClientOptions(
            timeout_seconds=60.0,
            max_retry_attempts=5,
        )
        client = SalesforceClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider,
            options=options,
        )

        assert client._options is options
        assert client._options.timeout_seconds == 60.0
        assert client._options.max_retry_attempts == 5

    def test_init_with_empty_url_raises_error(self):
        """Test that empty URL raises ValueError."""
        with pytest.raises(
            ValueError, match="connection_runtime_url cannot be None or empty"
        ):
            SalesforceClient("")

    def test_init_with_none_url_raises_error(self):
        """Test that None URL raises ValueError."""
        with pytest.raises(
            ValueError, match="connection_runtime_url cannot be None or empty"
        ):
            SalesforceClient(None)

    def test_connector_name_property(self, mock_token_provider):
        """Test connector_name property returns 'salesforce'."""
        client = SalesforceClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider,
        )

        assert client.connector_name == "salesforce"


class TestSalesforceClientLifecycle:
    """Tests for SalesforceClient lifecycle methods."""

    @pytest.mark.asyncio
    async def test_close(self, mock_token_provider):
        """Test close method calls http_client.close."""
        client = SalesforceClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider,
        )

        with patch.object(
            client._http_client,
            "close",
            new_callable=AsyncMock,
        ) as mock_close:
            await client.close()
            mock_close.assert_called_once()

    @pytest.mark.asyncio
    async def test_context_manager(self, mock_token_provider):
        """Test async context manager functionality."""
        with patch.object(
            SalesforceClient,
            "close",
            new_callable=AsyncMock,
        ) as mock_close:
            async with SalesforceClient(
                "https://example.azure.com/connections/test",
                token_provider=mock_token_provider,
            ) as client:
                assert isinstance(client, SalesforceClient)

            mock_close.assert_called_once()


class TestGetTables:
    """Tests for get_tables_async method."""

    @pytest.mark.asyncio
    async def test_success(self, mock_token_provider):
        """Test successful GET request."""
        client = SalesforceClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider,
        )

        mock_response = MockResponse(
            status=200,
            text='{"value": [{"name": "account", "displayName": "Account"}]}'
        )

        with patch.object(
            client._http_client,
            "send_async",
            new_callable=AsyncMock,
            return_value=mock_response,
        ) as mock_send:
            result = await client.get_tables_async()

            mock_send.assert_called_once()
            call_args = mock_send.call_args
            assert call_args[0][0] == "GET"
            assert "/datasets/default/tables" in call_args[0][1]
            assert result["value"][0]["name"] == "account"

    @pytest.mark.asyncio
    async def test_error_response_raises_exception(self, mock_token_provider):
        """Test that error response raises ConnectorException."""
        client = SalesforceClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider,
        )

        mock_response = MockResponse(status=401, text='{"error": "Unauthorized"}')

        with patch.object(
            client._http_client,
            "send_async",
            new_callable=AsyncMock,
            return_value=mock_response,
        ):
            with pytest.raises(ConnectorException) as exc_info:
                await client.get_tables_async()

            assert exc_info.value.status_code == 401


class TestGetItems:
    """Tests for get_items_async method."""

    @pytest.mark.asyncio
    async def test_with_query_parameters(self, mock_token_provider):
        """Test GET request includes expected query parameters."""
        client = SalesforceClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider,
        )

        mock_response = MockResponse(status=200, text='{"value": []}')

        with patch.object(
            client._http_client,
            "send_async",
            new_callable=AsyncMock,
            return_value=mock_response,
        ) as mock_send:
            await client.get_items_async(
                table="account",
                filter="Name eq 'Contoso'",
                top="5",
                select="Id,Name",
            )

            call_args = mock_send.call_args
            url = call_args[0][1]
            assert "/datasets/default/tables/account/items" in url
            assert "$filter=" in url
            assert "$top=5" in url
            assert "$select=Id%2CName" in url


class TestCreateJob:
    """Tests for create_job_async method."""

    @pytest.mark.asyncio
    async def test_sends_request_body(self, mock_token_provider):
        """Test create_job_async sends the input payload in request body."""
        client = SalesforceClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider,
        )

        payload = {
            "object": "Account",
            "operation": "insert",
            "contentType": "CSV",
        }
        mock_response = MockResponse(status=200, text='{"id": "750xx0000000001"}')

        with patch.object(
            client._http_client,
            "send_async",
            new_callable=AsyncMock,
            return_value=mock_response,
        ) as mock_send:
            result = await client.create_job_async(input=payload)

            call_args = mock_send.call_args
            assert call_args[0][0] == "POST"
            assert "/bulk/createjob" in call_args[0][1]
            assert call_args.kwargs["body"] == payload
            assert result["id"] == "750xx0000000001"


class TestPostItem:
    """Tests for post_item_async method."""

    @pytest.mark.asyncio
    async def test_sends_request_body(self, mock_token_provider):
        """Test post_item_async sends the input payload in request body."""
        client = SalesforceClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider,
        )

        payload = {
            "Name": "Contoso",
            "Phone": "425-555-0100",
        }
        mock_response = MockResponse(status=200, text='{"id": "001xx0000000001"}')

        with patch.object(
            client._http_client,
            "send_async",
            new_callable=AsyncMock,
            return_value=mock_response,
        ) as mock_send:
            result = await client.post_item_async(input=payload, table="account")

            call_args = mock_send.call_args
            assert call_args[0][0] == "POST"
            assert "/v2/datasets/default/tables/account/items" in call_args[0][1]
            assert call_args.kwargs["body"] == payload
            assert result["id"] == "001xx0000000001"


class TestDeleteItemAsync:
    """Tests for delete_item_async method (DELETE)."""

    @pytest.mark.asyncio
    async def test_success(self, mock_token_provider):
        """Test successful record deletion."""
        client = SalesforceClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider,
        )
        mock_response = MockResponse(status=200, text="")

        with patch.object(
            client._http_client,
            "send_async",
            new_callable=AsyncMock,
            return_value=mock_response,
        ) as mock_send:
            await client.delete_item_async(table="account", id="001xx0000000001")

            mock_send.assert_called_once()
            method, path = mock_send.call_args[0][0], mock_send.call_args[0][1]
            assert method == "DELETE"
            assert "/datasets/default/tables/account/items/001xx0000000001" in path

    @pytest.mark.asyncio
    async def test_error_response_raises_exception(self, mock_token_provider):
        """Test DELETE error path raises ConnectorException."""
        client = SalesforceClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider,
        )
        mock_response = MockResponse(status=404, text='{"error": "Not found"}')

        with patch.object(
            client._http_client,
            "send_async",
            new_callable=AsyncMock,
            return_value=mock_response,
        ):
            with pytest.raises(ConnectorException):
                await client.delete_item_async(table="account", id="missing-id")


class TestUploadJobDataAsync:
    """Tests for upload_job_data_async method (PUT with body)."""

    @pytest.mark.asyncio
    async def test_success_sends_body(self, mock_token_provider):
        """Test PUT operation sends input body."""
        client = SalesforceClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider,
        )
        payload = b"Name\r\nContoso\r\n"
        mock_response = MockResponse(status=201, text="")

        with patch.object(
            client._http_client,
            "send_async",
            new_callable=AsyncMock,
            return_value=mock_response,
        ) as mock_send:
            await client.upload_job_data_async(input=payload, job_id="job-1")

            mock_send.assert_called_once()
            method, path = mock_send.call_args[0][0], mock_send.call_args[0][1]
            body = mock_send.call_args[1].get("body")
            assert method == "PUT"
            assert "/codeless/jobs/ingest/job-1/batches" in path
            assert body is payload
            assert mock_send.call_args.kwargs["content_type"] == (
                "application/octet-stream"
            )

    @pytest.mark.asyncio
    async def test_error_response_raises_exception(self, mock_token_provider):
        """Test PUT error path raises ConnectorException."""
        client = SalesforceClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider,
        )
        payload = b"Name\r\nContoso\r\n"
        mock_response = MockResponse(status=400, text='{"error": "Bad request"}')

        with patch.object(
            client._http_client,
            "send_async",
            new_callable=AsyncMock,
            return_value=mock_response,
        ):
            with pytest.raises(ConnectorException):
                await client.upload_job_data_async(input=payload, job_id="job-1")


class TestHttpRequestAsync:
    """Tests for http_request_async raw request bodies."""

    @pytest.mark.asyncio
    async def test_success_sends_raw_body(self, mock_token_provider):
        """Test generic HTTP requests send raw bytes and parse the response."""
        client = SalesforceClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider,
        )
        payload = b'{"method":"GET","url":"/services/data"}'
        mock_response = MockResponse(status=200, text='{"status": 200}')

        with patch.object(
            client._http_client,
            "send_async",
            new_callable=AsyncMock,
            return_value=mock_response,
        ) as mock_send:
            result = await client.http_request_async(input=payload)

            mock_send.assert_called_once_with(
                "POST",
                "https://example.azure.com/connections/test/codeless/httprequest",
                body=payload,
                content_type="application/octet-stream",
            )
            assert result == {"status": 200}

    @pytest.mark.asyncio
    async def test_error_response_raises_exception(self, mock_token_provider):
        """Test generic HTTP request errors raise ConnectorException."""
        client = SalesforceClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider,
        )
        mock_response = MockResponse(status=400, text='{"error": "Bad request"}')

        with patch.object(
            client._http_client,
            "send_async",
            new_callable=AsyncMock,
            return_value=mock_response,
        ):
            with pytest.raises(ConnectorException) as exc_info:
                await client.http_request_async(input=b"invalid request")

            assert exc_info.value.status_code == 400


class TestExecuteSoslQueryAsync:
    """Tests for execute_sosl_query_async method."""

    @pytest.mark.asyncio
    async def test_success_uses_acronym_aware_name(self, mock_token_provider):
        """Test executing SOSL through its acronym-aware method name."""
        client = SalesforceClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider,
        )
        mock_response = MockResponse(status=200, text='{"searchRecords": []}')

        with patch.object(
            client._http_client,
            "send_async",
            new_callable=AsyncMock,
            return_value=mock_response,
        ) as mock_send:
            result = await client.execute_sosl_query_async(q="FIND {Contoso}")

            assert mock_send.call_args.args[0] == "GET"
            assert "/codeless/search?q=FIND%20%7BContoso%7D" in (
                mock_send.call_args.args[1]
            )
            assert result == {"searchRecords": []}
            assert not hasattr(SalesforceClient, "execute_s_o_s_l_query_async")

    @pytest.mark.asyncio
    async def test_error_response_raises_exception(self, mock_token_provider):
        """Test SOSL errors raise ConnectorException."""
        client = SalesforceClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider,
        )
        mock_response = MockResponse(status=400, text='{"error": "Bad query"}')

        with patch.object(
            client._http_client,
            "send_async",
            new_callable=AsyncMock,
            return_value=mock_response,
        ):
            with pytest.raises(ConnectorException):
                await client.execute_sosl_query_async(q="FIND")


class TestCloseJobAsync:
    """Tests for close_job_async method (PATCH with body)."""

    @pytest.mark.asyncio
    async def test_success_sends_body_and_returns_result(self, mock_token_provider):
        """Test PATCH sends input body and returns result."""
        client = SalesforceClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider,
        )
        payload = CloseJobRequest(state="UploadComplete")
        mock_response = MockResponse(status=200, text='{"id": "job-1", "state": "UploadComplete"}')

        with patch.object(
            client._http_client,
            "send_async",
            new_callable=AsyncMock,
            return_value=mock_response,
        ) as mock_send:
            result = await client.close_job_async(input=payload, job_id="job-1")

            mock_send.assert_called_once()
            method, path = mock_send.call_args[0][0], mock_send.call_args[0][1]
            body = mock_send.call_args[1].get("body")
            assert method == "PATCH"
            assert "/codeless/jobs/ingest/job-1" in path
            assert body is payload
            assert result is not None

    @pytest.mark.asyncio
    async def test_error_response_raises_exception(self, mock_token_provider):
        """Test PATCH error path raises ConnectorException."""
        client = SalesforceClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider,
        )
        payload = CloseJobRequest(state="Aborted")
        mock_response = MockResponse(status=404, text='{"error": "Job not found"}')

        with patch.object(
            client._http_client,
            "send_async",
            new_callable=AsyncMock,
            return_value=mock_response,
        ):
            with pytest.raises(ConnectorException):
                await client.close_job_async(input=payload, job_id="missing-job")


class TestSalesforceDiscoveryOperations:
    """Tests for Salesforce external ID and table metadata operations."""

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        ("method_name", "path_suffix"),
        [
            (
                "get_external_id_fields_async",
                "/datasets/default/tables/account/externalIdFields",
            ),
            (
                "get_metadata_for_get_item_async",
                "/$metadata.json/datasets/default/tables/account/getitem",
            ),
            (
                "get_metadata_for_patch_item_async",
                "/$metadata.json/datasets/default/tables/account/patchitem",
            ),
            (
                "get_metadata_for_post_item_async",
                "/$metadata.json/datasets/default/tables/account/postitem",
            ),
            (
                "get_table_async",
                "/$metadata.json/datasets/default/tables/account",
            ),
        ],
    )
    async def test_success_uses_expected_path(
        self,
        mock_token_provider,
        method_name,
        path_suffix,
    ):
        """Test each discovery operation uses its generated GET route."""
        client = SalesforceClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider,
        )
        mock_response = MockResponse(status=200, text='{"name": "account"}')

        with patch.object(
            client._http_client,
            "send_async",
            new_callable=AsyncMock,
            return_value=mock_response,
        ) as mock_send:
            result = await getattr(client, method_name)(table="account")

            mock_send.assert_called_once_with(
                "GET",
                f"https://example.azure.com/connections/test{path_suffix}",
                body=None,
            )
            assert result == {"name": "account"}

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "method_name",
        [
            "get_external_id_fields_async",
            "get_metadata_for_get_item_async",
            "get_metadata_for_patch_item_async",
            "get_metadata_for_post_item_async",
            "get_table_async",
        ],
    )
    async def test_error_response_raises_exception(
        self,
        mock_token_provider,
        method_name,
    ):
        """Test each discovery operation raises for a non-success response."""
        client = SalesforceClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider,
        )
        mock_response = MockResponse(status=404, text='{"error": "Not found"}')

        with patch.object(
            client._http_client,
            "send_async",
            new_callable=AsyncMock,
            return_value=mock_response,
        ):
            with pytest.raises(ConnectorException) as exc_info:
                await getattr(client, method_name)(table="account")

            assert exc_info.value.status_code == 404


class TestSalesforceTriggerOperations:
    """Tests for Salesforce trigger registration metadata."""

    def test_triggers_are_registered_without_callable_methods(self):
        """Test polling triggers are exposed only as registration metadata."""
        assert TRIGGER_OPERATIONS == {
            "GetOnNewItems": {
                "operation_id": "GetOnNewItems",
                "path": (
                    "/{connectionId}/datasets/default/tables/{table}/onnewitems"
                ),
                "method": "get",
                "required_parameters": ["table"],
                "callback_payload_type": "ItemsList",
            },
            "GetOnUpdatedItems": {
                "operation_id": "GetOnUpdatedItems",
                "path": (
                    "/{connectionId}/datasets/default/tables/{table}/onupdateditems"
                ),
                "method": "get",
                "required_parameters": ["table"],
                "callback_payload_type": "ItemsList",
            },
        }
        assert not hasattr(SalesforceClient, "get_on_new_items_async")
        assert not hasattr(SalesforceClient, "get_on_updated_items_async")
