# Copyright (c) Microsoft Corporation. All rights reserved.

"""Unit tests for CommondataserviceClient."""

import pytest
from unittest.mock import AsyncMock, patch
from azure.connectors.commondataservice import (
    CommondataserviceClient,
    CallbackRegistration,
    CreateRecordInput,
    UpdateRecordInput,
    UpdateEntityFileImageFieldContentInput,
    PerformUnboundActionInput,
    PerformBoundActionInput,
    AssociateEntityRequest,
    SearchRequestBody,
    WhenAnActionIsPerformedSubscriptionRequest,
    EntityItemList,
    SearchOutput,
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


class TestListRecords:
    """Tests for list_records_async method."""

    @pytest.mark.asyncio
    async def test_list_records_success(self, mock_token_provider):
        """Test successful list records."""
        client = CommondataserviceClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(
            status=200,
            text='{"value": [{"id": "1", "name": "Account1"}], "@odata.nextLink": null}'
        )

        with patch.object(
            client._http_client, 'send_async', new_callable=AsyncMock
        ) as mock_send:
            mock_send.return_value = mock_response

            result = await client.list_records_async(entity_name="accounts")

            mock_send.assert_called_once()
            call_args = mock_send.call_args
            assert call_args[0][0] == "GET"
            assert "/api/data/v9.1/accounts" in call_args[0][1]
            assert result["value"][0]["id"] == "1"

    @pytest.mark.asyncio
    async def test_list_records_with_query_params(self, mock_token_provider):
        """Test list records with query parameters."""
        client = CommondataserviceClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(status=200, text='{"value": []}')

        with patch.object(
            client._http_client, 'send_async', new_callable=AsyncMock
        ) as mock_send:
            mock_send.return_value = mock_response

            await client.list_records_async(
                entity_name="contacts",
                select="name,email",
                filter="status eq 'active'",
                orderby="name asc",
                top="10"
            )

            call_args = mock_send.call_args
            url = call_args[0][1]
            assert "$select=" in url
            assert "$filter=" in url
            assert "$orderby=" in url
            assert "$top=" in url

    @pytest.mark.asyncio
    async def test_list_records_error_response(self, mock_token_provider):
        """Test that error response raises ConnectorException."""
        client = CommondataserviceClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(status=404, text="Entity not found")

        with patch.object(
            client._http_client, 'send_async', new_callable=AsyncMock
        ) as mock_send:
            mock_send.return_value = mock_response

            with pytest.raises(ConnectorException) as exc_info:
                await client.list_records_async(entity_name="invalid")

            assert exc_info.value.status_code == 404


class TestCreateRecord:
    """Tests for create_record_async method."""

    @pytest.mark.asyncio
    async def test_create_record_success(self, mock_token_provider):
        """Test successful record creation."""
        client = CommondataserviceClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(
            status=201,
            text='{"id": "new-record-id", "name": "New Account"}'
        )

        with patch.object(
            client._http_client, 'send_async', new_callable=AsyncMock
        ) as mock_send:
            mock_send.return_value = mock_response

            input_data = CreateRecordInput(
                additional_properties={"name": "New Account", "industry": "Technology"}
            )
            result = await client.create_record_async(
                input=input_data,
                entity_name="accounts"
            )

            mock_send.assert_called_once()
            call_args = mock_send.call_args
            assert call_args[0][0] == "POST"
            assert "/api/data/v9.1/accounts" in call_args[0][1]
            assert result["id"] == "new-record-id"

    @pytest.mark.asyncio
    async def test_create_record_error_response(self, mock_token_provider):
        """Test that error response raises ConnectorException."""
        client = CommondataserviceClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(status=400, text="Validation error")

        with patch.object(
            client._http_client, 'send_async', new_callable=AsyncMock
        ) as mock_send:
            mock_send.return_value = mock_response

            input_data = CreateRecordInput()
            with pytest.raises(ConnectorException) as exc_info:
                await client.create_record_async(
                    input=input_data,
                    entity_name="accounts"
                )

            assert exc_info.value.status_code == 400


class TestGetItemCodeless:
    """Tests for get_item_codeless_async method."""

    @pytest.mark.asyncio
    async def test_get_record_success(self, mock_token_provider):
        """Test successful record retrieval by ID."""
        client = CommondataserviceClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(
            status=200,
            text='{"id": "record-123", "name": "Test Account"}'
        )

        with patch.object(
            client._http_client, 'send_async', new_callable=AsyncMock
        ) as mock_send:
            mock_send.return_value = mock_response

            result = await client.get_item_codeless_async(
                entity_name="accounts",
                record_id="record-123"
            )

            call_args = mock_send.call_args
            assert call_args[0][0] == "GET"
            assert "/accounts(record-123)" in call_args[0][1]
            assert result["id"] == "record-123"

    @pytest.mark.asyncio
    async def test_get_record_with_select_expand(self, mock_token_provider):
        """Test record retrieval with select and expand."""
        client = CommondataserviceClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(status=200, text='{"id": "123"}')

        with patch.object(
            client._http_client, 'send_async', new_callable=AsyncMock
        ) as mock_send:
            mock_send.return_value = mock_response

            await client.get_item_codeless_async(
                entity_name="accounts",
                record_id="123",
                select="name,email",
                expand="contacts"
            )

            url = mock_send.call_args[0][1]
            assert "$select=" in url
            assert "$expand=" in url

    @pytest.mark.asyncio
    async def test_get_record_not_found(self, mock_token_provider):
        """Test that 404 raises ConnectorException."""
        client = CommondataserviceClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(status=404, text="Record not found")

        with patch.object(
            client._http_client, 'send_async', new_callable=AsyncMock
        ) as mock_send:
            mock_send.return_value = mock_response

            with pytest.raises(ConnectorException) as exc_info:
                await client.get_item_codeless_async(
                    entity_name="accounts",
                    record_id="invalid"
                )

            assert exc_info.value.status_code == 404


class TestDeleteRecord:
    """Tests for delete_record_async method."""

    @pytest.mark.asyncio
    async def test_delete_record_success(self, mock_token_provider):
        """Test successful record deletion."""
        client = CommondataserviceClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(status=204, text="")

        with patch.object(
            client._http_client, 'send_async', new_callable=AsyncMock
        ) as mock_send:
            mock_send.return_value = mock_response

            await client.delete_record_async(
                entity_name="accounts",
                record_id="record-to-delete"
            )

            call_args = mock_send.call_args
            assert call_args[0][0] == "DELETE"
            assert "/accounts(record-to-delete)" in call_args[0][1]

    @pytest.mark.asyncio
    async def test_delete_record_with_partition(self, mock_token_provider):
        """Test record deletion with partition ID."""
        client = CommondataserviceClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(status=204, text="")

        with patch.object(
            client._http_client, 'send_async', new_callable=AsyncMock
        ) as mock_send:
            mock_send.return_value = mock_response

            await client.delete_record_async(
                entity_name="accounts",
                record_id="123",
                partition_id="partition-1"
            )

            url = mock_send.call_args[0][1]
            assert "partitionId=" in url


class TestUpdateRecord:
    """Tests for update_record_async method."""

    @pytest.mark.asyncio
    async def test_update_record_success(self, mock_token_provider):
        """Test successful record update."""
        client = CommondataserviceClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(
            status=200,
            text='{"id": "123", "name": "Updated Account"}'
        )

        with patch.object(
            client._http_client, 'send_async', new_callable=AsyncMock
        ) as mock_send:
            mock_send.return_value = mock_response

            input_data = UpdateRecordInput(
                additional_properties={"name": "Updated Account"}
            )
            result = await client.update_record_async(
                input=input_data,
                entity_name="accounts",
                record_id="123"
            )

            call_args = mock_send.call_args
            assert call_args[0][0] == "PATCH"
            assert "/accounts(123)" in call_args[0][1]
            assert result["name"] == "Updated Account"

    @pytest.mark.asyncio
    async def test_update_record_error(self, mock_token_provider):
        """Test that error response raises ConnectorException."""
        client = CommondataserviceClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(status=400, text="Invalid data")

        with patch.object(
            client._http_client, 'send_async', new_callable=AsyncMock
        ) as mock_send:
            mock_send.return_value = mock_response

            input_data = UpdateRecordInput()
            with pytest.raises(ConnectorException) as exc_info:
                await client.update_record_async(
                    input=input_data,
                    entity_name="accounts",
                    record_id="123"
                )

            assert exc_info.value.status_code == 400


class TestFileImageOperations:
    """Tests for file and image operations."""

    @pytest.mark.asyncio
    async def test_upload_file_success(self, mock_token_provider):
        """Test successful file upload."""
        client = CommondataserviceClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(status=204, text="")

        with patch.object(
            client._http_client, 'send_async', new_callable=AsyncMock
        ) as mock_send:
            mock_send.return_value = mock_response

            input_data = UpdateEntityFileImageFieldContentInput()
            await client.update_entity_file_image_field_content_async(
                input=input_data,
                entity_name="annotations",
                record_id="123",
                file_image_field_name="documentbody",
                x_ms_file_name="test.pdf"
            )

            call_args = mock_send.call_args
            assert call_args[0][0] == "PUT"
            assert "/annotations(123)/documentbody" in call_args[0][1]
            assert "x-ms-file-name=" in call_args[0][1]

    @pytest.mark.asyncio
    async def test_download_file_success(self, mock_token_provider):
        """Test successful file download."""
        client = CommondataserviceClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(status=200, text="FILE_CONTENT_BINARY")

        with patch.object(
            client._http_client, 'send_async', new_callable=AsyncMock
        ) as mock_send:
            mock_send.return_value = mock_response

            result = await client.get_entity_file_image_field_content_async(
                entity_name="annotations",
                record_id="123",
                file_image_field_name="documentbody"
            )

            call_args = mock_send.call_args
            assert call_args[0][0] == "GET"
            assert "/$value" in call_args[0][1]
            assert isinstance(result, bytes)

    @pytest.mark.asyncio
    async def test_download_file_with_size(self, mock_token_provider):
        """Test file download with size parameter."""
        client = CommondataserviceClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(status=200, text="IMAGE_DATA")

        with patch.object(
            client._http_client, 'send_async', new_callable=AsyncMock
        ) as mock_send:
            mock_send.return_value = mock_response

            await client.get_entity_file_image_field_content_async(
                entity_name="contacts",
                record_id="456",
                file_image_field_name="entityimage",
                size="thumbnail"
            )

            url = mock_send.call_args[0][1]
            assert "size=thumbnail" in url

    @pytest.mark.asyncio
    async def test_download_file_error(self, mock_token_provider):
        """Test that error response raises ConnectorException."""
        client = CommondataserviceClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(status=404, text="File not found")

        with patch.object(
            client._http_client, 'send_async', new_callable=AsyncMock
        ) as mock_send:
            mock_send.return_value = mock_response

            with pytest.raises(ConnectorException) as exc_info:
                await client.get_entity_file_image_field_content_async(
                    entity_name="annotations",
                    record_id="invalid",
                    file_image_field_name="documentbody"
                )

            assert exc_info.value.status_code == 404


class TestPerformActions:
    """Tests for action operations."""

    @pytest.mark.asyncio
    async def test_perform_unbound_action_success(self, mock_token_provider):
        """Test successful unbound action."""
        client = CommondataserviceClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(
            status=200,
            text='{"result": "success"}'
        )

        with patch.object(
            client._http_client, 'send_async', new_callable=AsyncMock
        ) as mock_send:
            mock_send.return_value = mock_response

            input_data = PerformUnboundActionInput(
                additional_properties={"param1": "value1"}
            )
            result = await client.perform_unbound_action_async(
                input=input_data,
                action_name="WhoAmI"
            )

            call_args = mock_send.call_args
            assert call_args[0][0] == "POST"
            assert "/api/data/v9.2/WhoAmI" in call_args[0][1]
            assert result["result"] == "success"

    @pytest.mark.asyncio
    async def test_perform_unbound_action_error(self, mock_token_provider):
        """Test unbound action error."""
        client = CommondataserviceClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(status=400, text="Action failed")

        with patch.object(
            client._http_client, 'send_async', new_callable=AsyncMock
        ) as mock_send:
            mock_send.return_value = mock_response

            input_data = PerformUnboundActionInput()
            with pytest.raises(ConnectorException) as exc_info:
                await client.perform_unbound_action_async(
                    input=input_data,
                    action_name="InvalidAction"
                )

            assert exc_info.value.status_code == 400

    @pytest.mark.asyncio
    async def test_perform_bound_action_success(self, mock_token_provider):
        """Test successful bound action."""
        client = CommondataserviceClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(
            status=200,
            text='{"message": "Action completed"}'
        )

        with patch.object(
            client._http_client, 'send_async', new_callable=AsyncMock
        ) as mock_send:
            mock_send.return_value = mock_response

            input_data = PerformBoundActionInput(
                additional_properties={"reason": "test"}
            )
            result = await client.perform_bound_action_async(
                input=input_data,
                entity_name="accounts",
                action_name="Microsoft.Dynamics.CRM.DeactivateAccount",
                record_id="123"
            )

            call_args = mock_send.call_args
            assert call_args[0][0] == "POST"
            assert "/accounts(123)/Microsoft.Dynamics.CRM.DeactivateAccount" in call_args[0][1]
            assert result["message"] == "Action completed"

    @pytest.mark.asyncio
    async def test_perform_bound_action_error(self, mock_token_provider):
        """Test bound action error."""
        client = CommondataserviceClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(status=500, text="Internal error")

        with patch.object(
            client._http_client, 'send_async', new_callable=AsyncMock
        ) as mock_send:
            mock_send.return_value = mock_response

            input_data = PerformBoundActionInput()
            with pytest.raises(ConnectorException) as exc_info:
                await client.perform_bound_action_async(
                    input=input_data,
                    entity_name="accounts",
                    action_name="FailingAction",
                    record_id="123"
                )

            assert exc_info.value.status_code == 500


class TestRelationshipOperations:
    """Tests for relationship operations."""

    @pytest.mark.asyncio
    async def test_associate_entities_success(self, mock_token_provider):
        """Test successful entity association."""
        client = CommondataserviceClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(status=204, text="")

        with patch.object(
            client._http_client, 'send_async', new_callable=AsyncMock
        ) as mock_send:
            mock_send.return_value = mock_response

            input_data = AssociateEntityRequest(
                id="https://org.crm.dynamics.com/api/data/v9.0/contacts(456)"
            )
            await client.associate_entities_async(
                input=input_data,
                entity_name="accounts",
                record_id="123",
                association_entity_relationship="contact_customer_accounts"
            )

            call_args = mock_send.call_args
            assert call_args[0][0] == "POST"
            assert "/accounts(123)/contact_customer_accounts/$ref" in call_args[0][1]

    @pytest.mark.asyncio
    async def test_disassociate_entities_success(self, mock_token_provider):
        """Test successful entity disassociation."""
        client = CommondataserviceClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(status=204, text="")

        with patch.object(
            client._http_client, 'send_async', new_callable=AsyncMock
        ) as mock_send:
            mock_send.return_value = mock_response

            await client.disassociate_entities_async(
                entity_name="accounts",
                record_id="123",
                association_entity_relationship="contact_customer_accounts",
                id="https://org.crm.dynamics.com/api/data/v9.0/contacts(456)"
            )

            call_args = mock_send.call_args
            assert call_args[0][0] == "DELETE"
            assert "$ref" in call_args[0][1]
            assert "$id=" in call_args[0][1]


class TestSearchRecords:
    """Tests for search operations."""

    @pytest.mark.asyncio
    async def test_search_rows_success(self, mock_token_provider):
        """Test successful relevance search."""
        client = CommondataserviceClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(
            status=200,
            text='{"value": [{"id": "1", "name": "Contoso"}], "totalrecordcount": 1}'
        )

        with patch.object(
            client._http_client, 'send_async', new_callable=AsyncMock
        ) as mock_send:
            mock_send.return_value = mock_response

            input_data = SearchRequestBody(
                search="Contoso",
                searchtype="simple",
                top=10
            )
            result = await client.get_relevant_rows_async(input=input_data)

            call_args = mock_send.call_args
            assert call_args[0][0] == "POST"
            assert "/api/search/v1.0/query" in call_args[0][1]
            assert result["value"][0]["name"] == "Contoso"

    @pytest.mark.asyncio
    async def test_search_rows_error(self, mock_token_provider):
        """Test search error response."""
        client = CommondataserviceClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(status=400, text="Invalid search query")

        with patch.object(
            client._http_client, 'send_async', new_callable=AsyncMock
        ) as mock_send:
            mock_send.return_value = mock_response

            input_data = SearchRequestBody(search="")
            with pytest.raises(ConnectorException) as exc_info:
                await client.get_relevant_rows_async(input=input_data)

            assert exc_info.value.status_code == 400


class TestTriggerOperations:
    """Tests for trigger/webhook operations."""

    @pytest.mark.asyncio
    async def test_subscribe_webhook_trigger(self, mock_token_provider):
        """Test webhook subscription for row changes."""
        client = CommondataserviceClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(status=200, text="")

        with patch.object(
            client._http_client, 'send_async', new_callable=AsyncMock
        ) as mock_send:
            mock_send.return_value = mock_response

            input_data = CallbackRegistration(
                url="https://callback.example.com",
                entityname="accounts",
                message=1,
                scope=1
            )
            await client.subscribe_webhook_trigger_async(input=input_data)

            call_args = mock_send.call_args
            assert call_args[0][0] == "POST"
            assert "/callbackregistrations" in call_args[0][1]

    @pytest.mark.asyncio
    async def test_business_events_trigger(self, mock_token_provider):
        """Test business events trigger subscription."""
        client = CommondataserviceClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(status=200, text="")

        with patch.object(
            client._http_client, 'send_async', new_callable=AsyncMock
        ) as mock_send:
            mock_send.return_value = mock_response

            input_data = WhenAnActionIsPerformedSubscriptionRequest(
                url="https://callback.example.com",
                entityname="accounts",
                sdkmessagename="Create",
                scope=1
            )
            await client.business_events_trigger_async(input=input_data)

            call_args = mock_send.call_args
            assert call_args[0][0] == "POST"
            assert "/v9.2/callbackregistrations" in call_args[0][1]


class TestExecuteChangeset:
    """Tests for changeset operations."""

    @pytest.mark.asyncio
    async def test_execute_changeset_success(self, mock_token_provider):
        """Test successful changeset execution."""
        client = CommondataserviceClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(status=200, text="")

        with patch.object(
            client._http_client, 'send_async', new_callable=AsyncMock
        ) as mock_send:
            mock_send.return_value = mock_response

            await client.execute_changeset_async()

            call_args = mock_send.call_args
            assert call_args[0][0] == "POST"
            assert "/$batch" in call_args[0][1]


class TestDataclasses:
    """Tests for dataclass serialization."""

    def test_create_record_input_defaults(self):
        """Test CreateRecordInput default values."""
        input_data = CreateRecordInput()
        assert input_data.additional_properties == {}

    def test_create_record_input_with_values(self):
        """Test CreateRecordInput with custom values."""
        input_data = CreateRecordInput(
            additional_properties={"name": "Test", "revenue": 1000000}
        )
        assert input_data.additional_properties["name"] == "Test"
        assert input_data.additional_properties["revenue"] == 1000000

    def test_update_record_input_defaults(self):
        """Test UpdateRecordInput default values."""
        input_data = UpdateRecordInput()
        assert input_data.additional_properties == {}

    def test_search_request_body_defaults(self):
        """Test SearchRequestBody default values."""
        body = SearchRequestBody()
        assert body.search is None
        assert body.top is None

    def test_search_request_body_with_values(self):
        """Test SearchRequestBody with values."""
        body = SearchRequestBody(
            search="Contoso",
            searchtype="full",
            searchmode="all",
            top=20,
            filter="status eq 'active'"
        )
        assert body.search == "Contoso"
        assert body.top == 20

    def test_callback_registration_defaults(self):
        """Test CallbackRegistration default values."""
        reg = CallbackRegistration()
        assert reg.url is None
        assert reg.entityname is None

    def test_callback_registration_with_values(self):
        """Test CallbackRegistration with values."""
        reg = CallbackRegistration(
            url="https://callback.example.com",
            entityname="accounts",
            message=1,
            scope=1,
            filteringattributes="name,revenue"
        )
        assert reg.url == "https://callback.example.com"
        assert reg.entityname == "accounts"
        assert reg.filteringattributes == "name,revenue"

    def test_entity_item_list_defaults(self):
        """Test EntityItemList default values."""
        item_list = EntityItemList()
        assert item_list.value is None
        assert item_list.next_link is None

    def test_search_output_defaults(self):
        """Test SearchOutput default values."""
        output = SearchOutput()
        assert output.value is None
        assert output.totalrecordcount is None
        assert output.facets is None

    def test_associate_entity_request(self):
        """Test AssociateEntityRequest."""
        request = AssociateEntityRequest(
            id="https://org.crm.dynamics.com/api/data/v9.0/contacts(123)"
        )
        assert "contacts(123)" in request.id
