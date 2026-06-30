# Copyright (c) Microsoft Corporation. All rights reserved.

"""Unit tests for ArmClient."""

import json
import pytest
from unittest.mock import AsyncMock, patch
from azure.connectors.arm import (
    ArmClient,
    LocationListResult,
    Location,
    Subscription,
    SubscriptionListResult,
    SubscriptionPolicies,
    DeploymentExtended,
    DeploymentValidateResult,
    DeploymentExportResult,
    DeploymentListResult,
    DeploymentOperation,
    DeploymentOperationProperties,
    Provider,
    ProviderListResult,
    ProviderResourceType,
    ResourceListResult,
    ResourceGroup,
    ResourceGroupProperties,
    ResourceGroupExportResult,
    ResourceGroupListResult,
    GenericResource,
    Plan,
    Sku,
    Identity,
    TagValue,
    TagDetails,
    TagCount,
    TagsListResult,
    Deployment,
    DeploymentProperties,
    TemplateLink,
    ParametersLink,
    DebugSetting,
    ResourceManagementErrorWithDetails,
)
from azure.connectors.sdk import (
    ConnectorClientOptions,
    ManagedIdentityTokenProvider,
    ConnectorException,
)
from tests.conftest import MockResponse


# Default API version for tests
DEFAULT_API_VERSION = "2021-04-01"


class TestArmClientInitialization:
    """Tests for ArmClient initialization."""

    def test_init_with_valid_url_and_defaults(self):
        """Test initialization with valid URL and default parameters."""
        client = ArmClient("https://example.azure.com/connections/test")

        assert client._connection_runtime_url == "https://example.azure.com/connections/test"
        assert client.connector_name == "arm"
        assert isinstance(client._http_client._token_provider, ManagedIdentityTokenProvider)

    def test_init_with_trailing_slash(self):
        """Test that trailing slash is removed from URL."""
        client = ArmClient("https://example.azure.com/connections/test/")

        assert client._connection_runtime_url == "https://example.azure.com/connections/test"

    def test_init_with_custom_token_provider(self, mock_token_provider):
        """Test initialization with custom token provider."""
        client = ArmClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        assert client._http_client._token_provider is mock_token_provider

    def test_init_with_custom_options(self, mock_token_provider):
        """Test initialization with custom options."""
        options = ConnectorClientOptions(timeout_seconds=60.0, max_retry_attempts=5)
        client = ArmClient(
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
            ArmClient("")

    def test_init_with_none_url_raises_error(self):
        """Test that None URL raises ValueError."""
        with pytest.raises(ValueError, match="connection_runtime_url cannot be None or empty"):
            ArmClient(None)

    def test_connector_name_property(self, mock_token_provider):
        """Test connector_name property returns 'arm'."""
        client = ArmClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        assert client.connector_name == "arm"


class TestArmClientLifecycle:
    """Tests for ArmClient lifecycle methods."""

    @pytest.mark.asyncio
    async def test_close(self, mock_token_provider):
        """Test close method calls http_client.close."""
        client = ArmClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        with patch.object(client._http_client, 'close', new_callable=AsyncMock) as mock_close:
            await client.close()
            mock_close.assert_called_once()

    @pytest.mark.asyncio
    async def test_context_manager(self, mock_token_provider):
        """Test async context manager functionality."""
        with patch.object(ArmClient, 'close', new_callable=AsyncMock) as mock_close:
            async with ArmClient(
                "https://example.azure.com/connections/test",
                token_provider=mock_token_provider
            ) as client:
                assert isinstance(client, ArmClient)

            mock_close.assert_called_once()


class TestSubscriptionsListAsync:
    """Tests for subscriptions_list_async method."""

    @pytest.mark.asyncio
    async def test_success_with_subscriptions(self, mock_token_provider):
        """Test successful GET request returns subscriptions."""
        client = ArmClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response_data = {
            "value": [
                {
                    "id": "/subscriptions/00000000-0000-0000-0000-000000000001",
                    "subscriptionId": "00000000-0000-0000-0000-000000000001",
                    "tenantId": "00000000-0000-0000-0000-000000000000",
                    "displayName": "Production Subscription",
                    "state": "Enabled",
                    "authorizationSource": "RoleBased"
                },
                {
                    "id": "/subscriptions/00000000-0000-0000-0000-000000000002",
                    "subscriptionId": "00000000-0000-0000-0000-000000000002",
                    "tenantId": "00000000-0000-0000-0000-000000000000",
                    "displayName": "Development Subscription",
                    "state": "Enabled",
                    "authorizationSource": "Legacy"
                }
            ],
            "nextLink": None
        }
        mock_response = MockResponse(status=200, text=json.dumps(mock_response_data))

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ) as mock_send:
            result = await client.subscriptions_list_async(
                x_ms_api_version=DEFAULT_API_VERSION
            )

            mock_send.assert_called_once_with(
                "GET",
                "https://example.azure.com/connections/test/subscriptions"
                f"?x-ms-api-version={DEFAULT_API_VERSION}",
                body=None
            )
            assert result is not None
            assert "value" in result
            assert len(result["value"]) == 2
            assert result["value"][0]["displayName"] == "Production Subscription"
            assert result["value"][1]["displayName"] == "Development Subscription"

    @pytest.mark.asyncio
    async def test_success_without_api_version(self, mock_token_provider):
        """Test GET request without api version omits query parameter."""
        client = ArmClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response_data = {"value": [], "nextLink": None}
        mock_response = MockResponse(status=200, text=json.dumps(mock_response_data))

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ) as mock_send:
            result = await client.subscriptions_list_async(x_ms_api_version=None)

            mock_send.assert_called_once_with(
                "GET",
                "https://example.azure.com/connections/test/subscriptions",
                body=None
            )
            assert result is not None

    @pytest.mark.asyncio
    async def test_success_with_empty_subscriptions(self, mock_token_provider):
        """Test successful GET request with no subscriptions."""
        client = ArmClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response_data = {"value": [], "nextLink": None}
        mock_response = MockResponse(status=200, text=json.dumps(mock_response_data))

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ) as mock_send:
            result = await client.subscriptions_list_async(
                x_ms_api_version=DEFAULT_API_VERSION
            )

            mock_send.assert_called_once()
            assert result is not None
            assert result["value"] == []

    @pytest.mark.asyncio
    async def test_success_with_empty_response_body(self, mock_token_provider):
        """Test successful GET request with empty response body returns None."""
        client = ArmClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(status=200, text="")

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ) as mock_send:
            result = await client.subscriptions_list_async(
                x_ms_api_version=DEFAULT_API_VERSION
            )

            mock_send.assert_called_once()
            assert result is None

    @pytest.mark.asyncio
    async def test_success_with_pagination(self, mock_token_provider):
        """Test response includes nextLink for pagination."""
        client = ArmClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response_data = {
            "value": [
                {
                    "id": "/subscriptions/00000000-0000-0000-0000-000000000001",
                    "subscriptionId": "00000000-0000-0000-0000-000000000001",
                    "displayName": "Subscription 1",
                    "state": "Enabled"
                }
            ],
            "nextLink": "https://management.azure.com/subscriptions?$skiptoken=abc123"
        }
        mock_response = MockResponse(status=200, text=json.dumps(mock_response_data))

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ):
            result = await client.subscriptions_list_async(
                x_ms_api_version=DEFAULT_API_VERSION
            )

            assert result is not None
            assert "nextLink" in result
            assert result["nextLink"] is not None

    @pytest.mark.asyncio
    async def test_error_unauthorized(self, mock_token_provider):
        """Test 401 Unauthorized raises ConnectorException."""
        client = ArmClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(
            status=401,
            text='{"error": {"code": "Unauthorized", "message": "Authentication failed"}}'
        )

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ):
            with pytest.raises(ConnectorException) as exc_info:
                await client.subscriptions_list_async(
                    x_ms_api_version=DEFAULT_API_VERSION
                )

            assert exc_info.value.status_code == 401

    @pytest.mark.asyncio
    async def test_error_forbidden(self, mock_token_provider):
        """Test 403 Forbidden raises ConnectorException."""
        client = ArmClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(
            status=403,
            text='{"error": {"code": "Forbidden", "message": "Access denied"}}'
        )

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ):
            with pytest.raises(ConnectorException) as exc_info:
                await client.subscriptions_list_async(
                    x_ms_api_version=DEFAULT_API_VERSION
                )

            assert exc_info.value.status_code == 403

    @pytest.mark.asyncio
    async def test_error_not_found(self, mock_token_provider):
        """Test 404 Not Found raises ConnectorException."""
        client = ArmClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(
            status=404,
            text='{"error": {"code": "NotFound", "message": "Resource not found"}}'
        )

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ):
            with pytest.raises(ConnectorException) as exc_info:
                await client.subscriptions_list_async(
                    x_ms_api_version=DEFAULT_API_VERSION
                )

            assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    async def test_error_server_error(self, mock_token_provider):
        """Test 500 Internal Server Error raises ConnectorException."""
        client = ArmClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(
            status=500,
            text='{"error": {"code": "InternalServerError", "message": "Server error"}}'
        )

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ):
            with pytest.raises(ConnectorException) as exc_info:
                await client.subscriptions_list_async(
                    x_ms_api_version=DEFAULT_API_VERSION
                )

            assert exc_info.value.status_code == 500


class TestSubscriptionDataClasses:
    """Tests for Subscription-related data classes."""

    def test_subscription_creation(self):
        """Test Subscription dataclass creation with all fields."""
        policies = SubscriptionPolicies(
            location_placement_id="Public_2014-09-01",
            quota_id="Free_2014-09-01",
            spending_limit="On"
        )
        subscription = Subscription(
            id="/subscriptions/00000000-0000-0000-0000-000000000001",
            subscription_id="00000000-0000-0000-0000-000000000001",
            tenant_id="00000000-0000-0000-0000-000000000000",
            display_name="Test Subscription",
            state="Enabled",
            subscription_policies=policies,
            authorization_source="RoleBased"
        )

        assert subscription.id == "/subscriptions/00000000-0000-0000-0000-000000000001"
        assert subscription.subscription_id == "00000000-0000-0000-0000-000000000001"
        assert subscription.tenant_id == "00000000-0000-0000-0000-000000000000"
        assert subscription.display_name == "Test Subscription"
        assert subscription.state == "Enabled"
        assert subscription.subscription_policies.quota_id == "Free_2014-09-01"
        assert subscription.authorization_source == "RoleBased"

    def test_subscription_list_result_creation(self):
        """Test SubscriptionListResult dataclass creation."""
        sub1 = Subscription(
            subscription_id="sub-1",
            display_name="Sub 1"
        )
        sub2 = Subscription(
            subscription_id="sub-2",
            display_name="Sub 2"
        )
        result = SubscriptionListResult(
            value=[sub1, sub2],
            next_link="https://example.com/next"
        )

        assert len(result.value) == 2
        assert result.value[0].subscription_id == "sub-1"
        assert result.next_link == "https://example.com/next"

    def test_subscription_policies_creation(self):
        """Test SubscriptionPolicies dataclass creation."""
        policies = SubscriptionPolicies(
            location_placement_id="Public_2014-09-01",
            quota_id="PayAsYouGo_2014-09-01",
            spending_limit="Off"
        )

        assert policies.location_placement_id == "Public_2014-09-01"
        assert policies.quota_id == "PayAsYouGo_2014-09-01"
        assert policies.spending_limit == "Off"


class TestLocationDataClasses:
    """Tests for Location-related data classes."""

    def test_location_creation(self):
        """Test Location dataclass creation with all fields."""
        location = Location(
            id="/subscriptions/00000000-0000-0000-0000-000000000001/locations/westus",
            subscription_id="00000000-0000-0000-0000-000000000001",
            name="westus",
            display_name="West US",
            latitude="37.783",
            longitude="-122.417"
        )

        assert location.name == "westus"
        assert location.display_name == "West US"
        assert location.latitude == "37.783"
        assert location.longitude == "-122.417"

    def test_location_list_result_creation(self):
        """Test LocationListResult dataclass creation."""
        loc1 = Location(name="westus", display_name="West US")
        loc2 = Location(name="eastus", display_name="East US")
        result = LocationListResult(value=[loc1, loc2])

        assert len(result.value) == 2
        assert result.value[0].name == "westus"
        assert result.value[1].name == "eastus"


class TestResourceGroupDataClasses:
    """Tests for ResourceGroup-related data classes."""

    def test_resource_group_creation(self):
        """Test ResourceGroup dataclass creation with all fields."""
        properties = ResourceGroupProperties(provisioning_state="Succeeded")
        rg = ResourceGroup(
            id="/subscriptions/sub-1/resourceGroups/my-rg",
            name="my-rg",
            location="westus",
            managed_by=None,
            tags={"environment": "production", "team": "backend"},
            properties=properties
        )

        assert rg.id == "/subscriptions/sub-1/resourceGroups/my-rg"
        assert rg.name == "my-rg"
        assert rg.location == "westus"
        assert rg.tags["environment"] == "production"
        assert rg.properties.provisioning_state == "Succeeded"

    def test_resource_group_list_result_creation(self):
        """Test ResourceGroupListResult dataclass creation."""
        rg1 = ResourceGroup(name="rg-1", location="westus")
        rg2 = ResourceGroup(name="rg-2", location="eastus")
        result = ResourceGroupListResult(
            value=[rg1, rg2],
            next_link="https://example.com/next"
        )

        assert len(result.value) == 2
        assert result.value[0].name == "rg-1"
        assert result.next_link == "https://example.com/next"

    def test_resource_group_export_result_creation(self):
        """Test ResourceGroupExportResult dataclass creation."""
        schema_url = "https://schema.management.azure.com/schemas/2019-04-01"
        template = {
            "$schema": f"{schema_url}/deploymentTemplate.json#",
            "contentVersion": "1.0.0.0",
            "resources": []
        }
        result = ResourceGroupExportResult(
            template=template,
            error=None
        )

        assert result.template["$schema"] is not None
        assert result.error is None


class TestDeploymentDataClasses:
    """Tests for Deployment-related data classes."""

    def test_deployment_creation(self):
        """Test Deployment dataclass creation."""
        template_link = TemplateLink(
            uri="https://example.com/template.json",
            content_version="1.0.0.0"
        )
        parameters_link = ParametersLink(
            uri="https://example.com/parameters.json",
            content_version="1.0.0.0"
        )
        debug_setting = DebugSetting(detail_level="requestContent")
        schema_url = "https://schema.management.azure.com/schemas/2019-04-01"
        properties = DeploymentProperties(
            template={"$schema": f"{schema_url}/deploymentTemplate.json#"},
            template_link=template_link,
            parameters={"param1": {"value": "value1"}},
            parameters_link=parameters_link,
            mode="Incremental",
            debug_setting=debug_setting
        )

        deployment = Deployment(properties=properties)

        assert deployment.properties.mode == "Incremental"
        assert deployment.properties.template_link.uri == "https://example.com/template.json"

    def test_deployment_extended_creation(self):
        """Test DeploymentExtended dataclass creation."""
        deploy_id = (
            "/subscriptions/sub-1/resourceGroups/rg-1"
            "/providers/Microsoft.Resources/deployments/deploy-1"
        )
        deployment = DeploymentExtended(
            id=deploy_id,
            name="deploy-1",
            properties=None
        )

        assert deployment.name == "deploy-1"
        assert "deployments/deploy-1" in deployment.id

    def test_deployment_validate_result_creation(self):
        """Test DeploymentValidateResult dataclass creation."""
        error = ResourceManagementErrorWithDetails(
            code="InvalidTemplate",
            message="Template validation failed",
            target="template",
            details=None
        )
        result = DeploymentValidateResult(error=error, properties=None)

        assert result.error.code == "InvalidTemplate"
        assert result.error.message == "Template validation failed"

    def test_deployment_export_result_creation(self):
        """Test DeploymentExportResult dataclass creation."""
        schema_url = "https://schema.management.azure.com/schemas/2019-04-01"
        template = {
            "$schema": f"{schema_url}/deploymentTemplate.json#",
            "resources": []
        }
        result = DeploymentExportResult(template=template)

        assert result.template["$schema"] is not None

    def test_deployment_list_result_creation(self):
        """Test DeploymentListResult dataclass creation."""
        d1 = DeploymentExtended(name="deploy-1")
        d2 = DeploymentExtended(name="deploy-2")
        result = DeploymentListResult(value=[d1, d2], next_link=None)

        assert len(result.value) == 2
        assert result.value[0].name == "deploy-1"

    def test_deployment_operation_creation(self):
        """Test DeploymentOperation dataclass creation."""
        props = DeploymentOperationProperties(
            provisioning_state="Succeeded",
            timestamp="2024-01-15T10:00:00Z",
            status_code="OK"
        )
        operation = DeploymentOperation(
            id="/subscriptions/sub-1/operations/op-1",
            operation_id="op-1",
            properties=props
        )

        assert operation.operation_id == "op-1"
        assert operation.properties.provisioning_state == "Succeeded"


class TestProviderDataClasses:
    """Tests for Provider-related data classes."""

    def test_provider_creation(self):
        """Test Provider dataclass creation."""
        resource_type = ProviderResourceType(
            resource_type="virtualMachines",
            locations=None,
            api_versions=["2023-01-01", "2022-01-01"]
        )
        provider = Provider(
            id="/subscriptions/sub-1/providers/Microsoft.Compute",
            namespace="Microsoft.Compute",
            registration_state="Registered",
            resource_types=[resource_type]
        )

        assert provider.namespace == "Microsoft.Compute"
        assert provider.registration_state == "Registered"
        assert len(provider.resource_types) == 1
        assert provider.resource_types[0].resource_type == "virtualMachines"

    def test_provider_list_result_creation(self):
        """Test ProviderListResult dataclass creation."""
        p1 = Provider(namespace="Microsoft.Compute")
        p2 = Provider(namespace="Microsoft.Storage")
        result = ProviderListResult(value=[p1, p2], next_link=None)

        assert len(result.value) == 2
        assert result.value[0].namespace == "Microsoft.Compute"


class TestResourceDataClasses:
    """Tests for Resource-related data classes."""

    def test_generic_resource_creation(self):
        """Test GenericResource dataclass creation with all fields."""
        plan = Plan(
            name="standard",
            publisher="Microsoft",
            product="WindowsServer",
            promotion_code=None
        )
        sku = Sku(
            name="Standard_DS1_v2",
            tier="Standard",
            size="DS1_v2",
            family="D",
            model=None
        )
        identity = Identity(
            principal_id="00000000-0000-0000-0000-000000000001",
            tenant_id="00000000-0000-0000-0000-000000000000",
            type_="SystemAssigned"
        )
        resource_id = (
            "/subscriptions/sub-1/resourceGroups/rg-1"
            "/providers/Microsoft.Compute/virtualMachines/vm-1"
        )
        resource = GenericResource(
            id=resource_id,
            name="vm-1",
            type_="Microsoft.Compute/virtualMachines",
            location="westus",
            tags={"environment": "dev"},
            plan=plan,
            kind=None,
            managed_by=None,
            sku=sku,
            identity=identity,
            properties={"vmSize": "Standard_DS1_v2"}
        )

        assert resource.name == "vm-1"
        assert resource.location == "westus"
        assert resource.sku.name == "Standard_DS1_v2"
        assert resource.identity.type_ == "SystemAssigned"

    def test_resource_list_result_creation(self):
        """Test ResourceListResult dataclass creation."""
        r1 = GenericResource(name="resource-1", location="westus")
        r2 = GenericResource(name="resource-2", location="eastus")
        result = ResourceListResult(value=[r1, r2], next_link=None)

        assert len(result.value) == 2
        assert result.value[0].name == "resource-1"


class TestTagDataClasses:
    """Tests for Tag-related data classes."""

    def test_tag_value_creation(self):
        """Test TagValue dataclass creation."""
        count = TagCount(type_="Total", value=5)
        tag_value = TagValue(
            id="/subscriptions/sub-1/tagNames/environment/tagValues/production",
            tag_value="production",
            count=count
        )

        assert tag_value.tag_value == "production"
        assert tag_value.count.value == 5

    def test_tag_details_creation(self):
        """Test TagDetails dataclass creation."""
        value1 = TagValue(tag_value="production")
        value2 = TagValue(tag_value="development")
        tag = TagDetails(
            id="/subscriptions/sub-1/tagNames/environment",
            tag_name="environment",
            count=TagCount(value=2),
            values=[value1, value2]
        )

        assert tag.tag_name == "environment"
        assert len(tag.values) == 2

    def test_tags_list_result_creation(self):
        """Test TagsListResult dataclass creation."""
        tag1 = TagDetails(tag_name="environment")
        tag2 = TagDetails(tag_name="team")
        result = TagsListResult(value=[tag1, tag2], next_link=None)

        assert len(result.value) == 2
        assert result.value[0].tag_name == "environment"


class TestErrorDataClasses:
    """Tests for Error-related data classes."""

    def test_resource_management_error_creation(self):
        """Test ResourceManagementErrorWithDetails dataclass creation."""
        error = ResourceManagementErrorWithDetails(
            code="BadRequest",
            message="The request is invalid.",
            target="properties.location",
            details=[
                {"code": "InvalidLocation", "message": "Location 'invalid' is not valid."}
            ]
        )

        assert error.code == "BadRequest"
        assert error.message == "The request is invalid."
        assert error.target == "properties.location"
        assert len(error.details) == 1
        assert error.details[0]["code"] == "InvalidLocation"


class TestResourceGroupsListAsync:
    """Tests for resource_groups_list_async method."""

    @pytest.mark.asyncio
    async def test_success_with_resource_groups(self, mock_token_provider):
        """Test successful GET request returns resource groups."""
        client = ArmClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response_data = {
            "value": [
                {
                    "id": "/subscriptions/sub-1/resourceGroups/rg-1",
                    "name": "rg-1",
                    "location": "westus",
                    "properties": {"provisioningState": "Succeeded"}
                },
                {
                    "id": "/subscriptions/sub-1/resourceGroups/rg-2",
                    "name": "rg-2",
                    "location": "eastus",
                    "properties": {"provisioningState": "Succeeded"}
                }
            ],
            "nextLink": None
        }
        mock_response = MockResponse(status=200, text=json.dumps(mock_response_data))

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ) as mock_send:
            result = await client.resource_groups_list_async(
                x_ms_api_version=DEFAULT_API_VERSION,
                subscription_id="sub-1"
            )

            mock_send.assert_called_once_with(
                "GET",
                "https://example.azure.com/connections/test/subscriptions/"
                f"sub-1/resourcegroups?x-ms-api-version={DEFAULT_API_VERSION}",
                body=None
            )
            assert result is not None
            assert len(result["value"]) == 2
            assert result["value"][0]["name"] == "rg-1"

    @pytest.mark.asyncio
    async def test_error_not_found(self, mock_token_provider):
        """Test 404 Not Found raises ConnectorException."""
        client = ArmClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(
            status=404,
            text='{"error": {"code": "NotFound", "message": "Subscription not found"}}'
        )

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ):
            with pytest.raises(ConnectorException) as exc_info:
                await client.resource_groups_list_async(
                    x_ms_api_version=DEFAULT_API_VERSION,
                    subscription_id="sub-1"
                )

            assert exc_info.value.status_code == 404


class TestResourceGroupsGetAsync:
    """Tests for resource_groups_get_async method."""

    @pytest.mark.asyncio
    async def test_success(self, mock_token_provider):
        """Test successful GET request returns resource group."""
        client = ArmClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response_data = {
            "id": "/subscriptions/sub-1/resourceGroups/rg-1",
            "name": "rg-1",
            "location": "westus",
            "tags": {"environment": "production"},
            "properties": {"provisioningState": "Succeeded"}
        }
        mock_response = MockResponse(status=200, text=json.dumps(mock_response_data))

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ) as mock_send:
            result = await client.resource_groups_get_async(
                x_ms_api_version=DEFAULT_API_VERSION,
                subscription_id="sub-1",
                resource_group_name="rg-1"
            )

            mock_send.assert_called_once()
            assert result is not None
            assert result["name"] == "rg-1"
            assert result["location"] == "westus"


class TestResourceGroupsDeleteAsync:
    """Tests for resource_groups_delete_async method (void operation)."""

    @pytest.mark.asyncio
    async def test_success_returns_none(self, mock_token_provider):
        """Test successful DELETE request returns None."""
        client = ArmClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(status=200, text="")

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ) as mock_send:
            result = await client.resource_groups_delete_async(
                x_ms_api_version=DEFAULT_API_VERSION,
                subscription_id="sub-1",
                resource_group_name="rg-1"
            )

            mock_send.assert_called_once_with(
                "DELETE",
                "https://example.azure.com/connections/test/subscriptions/"
                f"sub-1/resourcegroups/rg-1?x-ms-api-version={DEFAULT_API_VERSION}",
                body=None
            )
            assert result is None

    @pytest.mark.asyncio
    async def test_success_202_accepted(self, mock_token_provider):
        """Test 202 Accepted for async delete returns None."""
        client = ArmClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(status=202, text="")

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ):
            result = await client.resource_groups_delete_async(
                x_ms_api_version=DEFAULT_API_VERSION,
                subscription_id="sub-1",
                resource_group_name="rg-1"
            )

            assert result is None

    @pytest.mark.asyncio
    async def test_error_not_found(self, mock_token_provider):
        """Test 404 Not Found raises ConnectorException."""
        client = ArmClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(
            status=404,
            text='{"error": {"code": "NotFound", "message": "Resource group not found"}}'
        )

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ):
            with pytest.raises(ConnectorException) as exc_info:
                await client.resource_groups_delete_async(
                    x_ms_api_version=DEFAULT_API_VERSION,
                    subscription_id="sub-1",
                    resource_group_name="rg-1"
                )

            assert exc_info.value.status_code == 404


class TestDeploymentsGetAsync:
    """Tests for deployments_get_async method."""

    @pytest.mark.asyncio
    async def test_success(self, mock_token_provider):
        """Test successful GET request returns deployment."""
        client = ArmClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response_data = {
            "id": (
                "/subscriptions/sub-1/resourceGroups/rg-1"
                "/providers/Microsoft.Resources/deployments/deploy-1"
            ),
            "name": "deploy-1",
            "properties": {
                "provisioningState": "Succeeded",
                "mode": "Incremental"
            }
        }
        mock_response = MockResponse(status=200, text=json.dumps(mock_response_data))

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ) as mock_send:
            result = await client.deployments_get_async(
                x_ms_api_version=DEFAULT_API_VERSION,
                subscription_id="sub-1",
                resource_group_name="rg-1",
                deployment_name="deploy-1"
            )

            mock_send.assert_called_once()
            assert result is not None
            assert result["name"] == "deploy-1"


class TestDeploymentsDeleteAsync:
    """Tests for deployments_delete_async method (void operation)."""

    @pytest.mark.asyncio
    async def test_success_returns_none(self, mock_token_provider):
        """Test successful DELETE request returns None."""
        client = ArmClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(status=200, text="")

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ):
            result = await client.deployments_delete_async(
                x_ms_api_version=DEFAULT_API_VERSION,
                subscription_id="sub-1",
                resource_group_name="rg-1",
                deployment_name="deploy-1"
            )

            assert result is None


class TestDeploymentsCancelAsync:
    """Tests for deployments_cancel_async method (void operation)."""

    @pytest.mark.asyncio
    async def test_success_returns_none(self, mock_token_provider):
        """Test successful POST cancel request returns None."""
        client = ArmClient(
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
            result = await client.deployments_cancel_async(
                x_ms_api_version=DEFAULT_API_VERSION,
                subscription_id="sub-1",
                resource_group_name="rg-1",
                deployment_name="deploy-1"
            )

            mock_send.assert_called_once_with(
                "POST",
                "https://example.azure.com/connections/test/subscriptions/"
                "sub-1/resourcegroups/rg-1/providers/Microsoft.Resources/"
                f"deployments/deploy-1/cancel?x-ms-api-version={DEFAULT_API_VERSION}",
                body=None
            )
            assert result is None


class TestProvidersListAsync:
    """Tests for providers_list_async method."""

    @pytest.mark.asyncio
    async def test_success_with_providers(self, mock_token_provider):
        """Test successful GET request returns providers."""
        client = ArmClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response_data = {
            "value": [
                {
                    "namespace": "Microsoft.Compute",
                    "registrationState": "Registered"
                },
                {
                    "namespace": "Microsoft.Storage",
                    "registrationState": "Registered"
                }
            ],
            "nextLink": None
        }
        mock_response = MockResponse(status=200, text=json.dumps(mock_response_data))

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ) as mock_send:
            result = await client.providers_list_async(
                x_ms_api_version=DEFAULT_API_VERSION,
                subscription_id="sub-1"
            )

            mock_send.assert_called_once()
            assert result is not None
            assert len(result["value"]) == 2


class TestProvidersRegisterAsync:
    """Tests for providers_register_async method."""

    @pytest.mark.asyncio
    async def test_success(self, mock_token_provider):
        """Test successful POST request registers provider."""
        client = ArmClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response_data = {
            "namespace": "Microsoft.Compute",
            "registrationState": "Registered"
        }
        mock_response = MockResponse(status=200, text=json.dumps(mock_response_data))

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ) as mock_send:
            result = await client.providers_register_async(
                x_ms_api_version=DEFAULT_API_VERSION,
                subscription_id="sub-1",
                resource_provider_namespace="Microsoft.Compute"
            )

            mock_send.assert_called_once()
            assert result is not None
            assert result["namespace"] == "Microsoft.Compute"


class TestSubscriptionsListLocationsAsync:
    """Tests for subscriptions_list_locations_async method."""

    @pytest.mark.asyncio
    async def test_success_with_locations(self, mock_token_provider):
        """Test successful GET request returns locations."""
        client = ArmClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response_data = {
            "value": [
                {
                    "id": "/subscriptions/sub-1/locations/westus",
                    "name": "westus",
                    "displayName": "West US"
                },
                {
                    "id": "/subscriptions/sub-1/locations/eastus",
                    "name": "eastus",
                    "displayName": "East US"
                }
            ]
        }
        mock_response = MockResponse(status=200, text=json.dumps(mock_response_data))

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ) as mock_send:
            result = await client.subscriptions_list_locations_async(
                x_ms_api_version=DEFAULT_API_VERSION,
                subscription_id="sub-1"
            )

            mock_send.assert_called_once_with(
                "GET",
                "https://example.azure.com/connections/test/subscriptions/"
                f"sub-1/locations?x-ms-api-version={DEFAULT_API_VERSION}",
                body=None
            )
            assert result is not None
            assert len(result["value"]) == 2


class TestSubscriptionsGetAsync:
    """Tests for subscriptions_get_async method."""

    @pytest.mark.asyncio
    async def test_success(self, mock_token_provider):
        """Test successful GET request returns subscription."""
        client = ArmClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response_data = {
            "id": "/subscriptions/sub-1",
            "subscriptionId": "sub-1",
            "displayName": "Production Subscription",
            "state": "Enabled"
        }
        mock_response = MockResponse(status=200, text=json.dumps(mock_response_data))

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ) as mock_send:
            result = await client.subscriptions_get_async(
                x_ms_api_version=DEFAULT_API_VERSION,
                subscription_id="sub-1"
            )

            mock_send.assert_called_once_with(
                "GET",
                "https://example.azure.com/connections/test/subscriptions/"
                f"sub-1?x-ms-api-version={DEFAULT_API_VERSION}",
                body=None
            )
            assert result is not None
            assert result["subscriptionId"] == "sub-1"


class TestTagsDeleteValueAsync:
    """Tests for tags_delete_value_async method (void operation)."""

    @pytest.mark.asyncio
    async def test_success_returns_none(self, mock_token_provider):
        """Test successful DELETE request returns None."""
        client = ArmClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(status=200, text="")

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ):
            result = await client.tags_delete_value_async(
                x_ms_api_version=DEFAULT_API_VERSION,
                subscription_id="sub-1",
                tag_name="environment",
                tag_value="deprecated"
            )

            assert result is None


class TestTagsDeleteAsync:
    """Tests for tags_delete_async method (void operation)."""

    @pytest.mark.asyncio
    async def test_success_returns_none(self, mock_token_provider):
        """Test successful DELETE request returns None."""
        client = ArmClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(status=200, text="")

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ):
            result = await client.tags_delete_async(
                x_ms_api_version=DEFAULT_API_VERSION,
                subscription_id="sub-1",
                tag_name="obsolete-tag"
            )

            assert result is None


class TestResourcesDeleteByIdAsync:
    """Tests for resources_delete_by_id_async method (void operation)."""

    @pytest.mark.asyncio
    async def test_success_returns_none(self, mock_token_provider):
        """Test successful DELETE request returns None."""
        client = ArmClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(status=200, text="")

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ):
            result = await client.resources_delete_by_id_async(
                x_ms_api_version=DEFAULT_API_VERSION,
                subscription_id="sub-1",
                resource_group_name="rg-1",
                resource_provider_namespace="Microsoft.Compute",
                short_resource_id="virtualMachines/vm-1"
            )

            assert result is None

    @pytest.mark.asyncio
    async def test_error_not_found(self, mock_token_provider):
        """Test 404 Not Found raises ConnectorException."""
        client = ArmClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(
            status=404,
            text='{"error": {"code": "NotFound", "message": "Resource not found"}}'
        )

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ):
            with pytest.raises(ConnectorException) as exc_info:
                await client.resources_delete_by_id_async(
                    x_ms_api_version=DEFAULT_API_VERSION,
                    subscription_id="sub-1",
                    resource_group_name="rg-1",
                    resource_provider_namespace="Microsoft.Compute",
                    short_resource_id="virtualMachines/vm-1"
                )

            assert exc_info.value.status_code == 404
