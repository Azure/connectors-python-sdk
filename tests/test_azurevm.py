# Copyright (c) Microsoft Corporation. All rights reserved.

"""Unit tests for AzurevmClient."""

import pytest
from unittest.mock import AsyncMock, patch
from azure.connectors.azurevm import (
    AzurevmClient,
    VirtualMachine,
    VirtualMachineProperties,
    VirtualMachineInScaleSet,
    VirtualMachineInScaleSetProperties,
    VirtualMachineListResult,
    VirtualMachineInScaleSetListResult,
    VirtualMachineScaleSet,
    VirtualMachineScaleSetProperties,
    VirtualMachineScaleSetListResult,
    ResourceGroup,
    ResourceGroupListResult,
    Subscription,
    SubscriptionListResult,
)
from azure.connectors.sdk import (
    ConnectorClientOptions,
    ManagedIdentityTokenProvider,
    ConnectorException,
)
from tests.conftest import MockResponse


class TestAzurevmClientInitialization:
    """Tests for AzurevmClient initialization."""

    def test_init_with_valid_url_and_defaults(self):
        """Test initialization with valid URL and default parameters."""
        client = AzurevmClient(
            "https://example.azure.com/connections/test"
        )

        assert client._connection_runtime_url == (
            "https://example.azure.com/connections/test"
        )
        assert client.connector_name == "azurevm"
        assert isinstance(
            client._http_client._token_provider, ManagedIdentityTokenProvider
        )

    def test_init_with_trailing_slash(self):
        """Test that trailing slash is removed from URL."""
        client = AzurevmClient(
            "https://example.azure.com/connections/test/"
        )

        assert client._connection_runtime_url == (
            "https://example.azure.com/connections/test"
        )

    def test_init_with_custom_token_provider(self, mock_token_provider):
        """Test initialization with custom token provider."""
        client = AzurevmClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        assert client._http_client._token_provider is mock_token_provider

    def test_init_with_custom_options(self, mock_token_provider):
        """Test initialization with custom options."""
        options = ConnectorClientOptions(
            timeout_seconds=60.0, max_retry_attempts=5
        )
        client = AzurevmClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider,
            options=options
        )

        assert client._options is options
        assert client._options.timeout_seconds == 60.0
        assert client._options.max_retry_attempts == 5

    def test_init_with_empty_url_raises_error(self):
        """Test that empty URL raises ValueError."""
        with pytest.raises(
            ValueError, match="connection_runtime_url cannot be None or empty"
        ):
            AzurevmClient("")

    def test_init_with_none_url_raises_error(self):
        """Test that None URL raises ValueError."""
        with pytest.raises(
            ValueError, match="connection_runtime_url cannot be None or empty"
        ):
            AzurevmClient(None)

    def test_connector_name_property(self, mock_token_provider):
        """Test connector_name property returns 'azurevm'."""
        client = AzurevmClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        assert client.connector_name == "azurevm"


class TestAzurevmClientLifecycle:
    """Tests for AzurevmClient lifecycle methods."""

    @pytest.mark.asyncio
    async def test_close(self, mock_token_provider):
        """Test close method calls http_client.close."""
        client = AzurevmClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        with patch.object(
            client._http_client, 'close', new_callable=AsyncMock
        ) as mock_close:
            await client.close()
            mock_close.assert_called_once()

    @pytest.mark.asyncio
    async def test_context_manager(self, mock_token_provider):
        """Test async context manager functionality."""
        with patch.object(
            AzurevmClient, 'close', new_callable=AsyncMock
        ) as mock_close:
            async with AzurevmClient(
                "https://example.azure.com/connections/test",
                token_provider=mock_token_provider
            ) as client:
                assert isinstance(client, AzurevmClient)

            mock_close.assert_called_once()


class TestVirtualMachineGetAsync:
    """Tests for virtual_machine_get_async method."""

    @pytest.mark.asyncio
    async def test_success_returns_vm_data(self, mock_token_provider):
        """Test successful request returns VM data."""
        response_json = (
            '{"id": "/subscriptions/sub1/resourceGroups/rg1/providers/'
            'Microsoft.Compute/virtualMachines/vm1", "name": "vm1", '
            '"properties": {"provisioningState": "Succeeded"}}'
        )
        mock_response = MockResponse(status=200, text=response_json)

        client = AzurevmClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ) as mock_send:
            result = await client.virtual_machine_get_async(
                subscription_id="sub1",
                resource_group_name="rg1",
                virtual_machine_name="vm1"
            )

            mock_send.assert_called_once()
            call_args = mock_send.call_args
            assert call_args[0][0] == "GET"
            assert "/subscriptions/sub1" in call_args[0][1]
            assert "/resourcegroups/rg1" in call_args[0][1]
            assert "/virtualMachines/vm1" in call_args[0][1]
            assert result is not None
            assert result["name"] == "vm1"

    @pytest.mark.asyncio
    async def test_empty_response_returns_none(self, mock_token_provider):
        """Test empty response returns None."""
        mock_response = MockResponse(status=200, text='')

        client = AzurevmClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ):
            result = await client.virtual_machine_get_async(
                subscription_id="sub1",
                resource_group_name="rg1",
                virtual_machine_name="vm1"
            )

            assert result is None

    @pytest.mark.asyncio
    async def test_error_response_raises_exception(self, mock_token_provider):
        """Test that error response raises ConnectorException."""
        mock_response = MockResponse(
            status=404,
            text='{"error": {"code": "ResourceNotFound", "message": "VM not found"}}'
        )

        client = AzurevmClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ):
            with pytest.raises(ConnectorException) as exc_info:
                await client.virtual_machine_get_async(
                    subscription_id="sub1",
                    resource_group_name="rg1",
                    virtual_machine_name="vm1"
                )

            assert exc_info.value.status_code == 404


class TestVirtualMachineStartAsync:
    """Tests for virtual_machine_start_async method."""

    @pytest.mark.asyncio
    async def test_success(self, mock_token_provider):
        """Test successful request."""
        mock_response = MockResponse(status=202, text='')

        client = AzurevmClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ) as mock_send:
            await client.virtual_machine_start_async(
                subscription_id="sub1",
                resource_group_name="rg1",
                virtual_machine_name="vm1"
            )

            mock_send.assert_called_once()
            call_args = mock_send.call_args
            assert call_args[0][0] == "POST"
            assert "/virtualMachines/vm1/start" in call_args[0][1]


class TestVirtualMachineDeallocateAsync:
    """Tests for virtual_machine_deallocate_async method."""

    @pytest.mark.asyncio
    async def test_success(self, mock_token_provider):
        """Test successful request."""
        mock_response = MockResponse(status=202, text='')

        client = AzurevmClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ) as mock_send:
            await client.virtual_machine_deallocate_async(
                subscription_id="sub1",
                resource_group_name="rg1",
                virtual_machine_name="vm1"
            )

            mock_send.assert_called_once()
            call_args = mock_send.call_args
            assert call_args[0][0] == "POST"
            assert "/virtualMachines/vm1/deallocate" in call_args[0][1]


class TestVirtualMachinePowerOffAsync:
    """Tests for virtual_machine_poweroff_async method."""

    @pytest.mark.asyncio
    async def test_success(self, mock_token_provider):
        """Test successful request."""
        mock_response = MockResponse(status=202, text='')

        client = AzurevmClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ) as mock_send:
            await client.virtual_machine_poweroff_async(
                subscription_id="sub1",
                resource_group_name="rg1",
                virtual_machine_name="vm1"
            )

            mock_send.assert_called_once()
            call_args = mock_send.call_args
            assert call_args[0][0] == "POST"
            assert "/virtualMachines/vm1/powerOff" in call_args[0][1]


class TestVirtualMachineReapplyAsync:
    """Tests for virtual_machine_reapply_async method."""

    @pytest.mark.asyncio
    async def test_success(self, mock_token_provider):
        """Test successful request."""
        mock_response = MockResponse(status=202, text='')

        client = AzurevmClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ) as mock_send:
            await client.virtual_machine_reapply_async(
                subscription_id="sub1",
                resource_group_name="rg1",
                virtual_machine_name="vm1"
            )

            mock_send.assert_called_once()
            call_args = mock_send.call_args
            assert call_args[0][0] == "POST"
            assert "/virtualMachines/vm1/reapply" in call_args[0][1]


class TestVirtualMachineRedeployAsync:
    """Tests for virtual_machine_redeploy_async method."""

    @pytest.mark.asyncio
    async def test_success(self, mock_token_provider):
        """Test successful request."""
        mock_response = MockResponse(status=202, text='')

        client = AzurevmClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ) as mock_send:
            await client.virtual_machine_redeploy_async(
                subscription_id="sub1",
                resource_group_name="rg1",
                virtual_machine_name="vm1"
            )

            mock_send.assert_called_once()
            call_args = mock_send.call_args
            assert call_args[0][0] == "POST"
            assert "/virtualMachines/vm1/redeploy" in call_args[0][1]


class TestVirtualMachineRestartAsync:
    """Tests for virtual_machine_restart_async method."""

    @pytest.mark.asyncio
    async def test_success(self, mock_token_provider):
        """Test successful request."""
        mock_response = MockResponse(status=202, text='')

        client = AzurevmClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ) as mock_send:
            await client.virtual_machine_restart_async(
                subscription_id="sub1",
                resource_group_name="rg1",
                virtual_machine_name="vm1"
            )

            mock_send.assert_called_once()
            call_args = mock_send.call_args
            assert call_args[0][0] == "POST"
            assert "/virtualMachines/vm1/restart" in call_args[0][1]


class TestVirtualMachineInScaleSetGetAsync:
    """Tests for virtual_machine_in_scale_set_get_async method."""

    @pytest.mark.asyncio
    async def test_success_returns_vm_data(self, mock_token_provider):
        """Test successful request returns VM in scale set data."""
        response_json = (
            '{"id": "/subscriptions/sub1/resourceGroups/rg1/providers/'
            'Microsoft.Compute/virtualMachineScaleSets/vmss1/virtualMachines/0", '
            '"name": "vmss1_0", "instanceId": "0", '
            '"properties": {"provisioningState": "Succeeded"}}'
        )
        mock_response = MockResponse(status=200, text=response_json)

        client = AzurevmClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ) as mock_send:
            result = await client.virtual_machine_in_scale_set_get_async(
                subscription_id="sub1",
                resource_group_name="rg1",
                virtual_machine_scale_set_name="vmss1",
                virtual_machine_in_scale_set_instance_id="0"
            )

            mock_send.assert_called_once()
            call_args = mock_send.call_args
            assert call_args[0][0] == "GET"
            assert "/virtualMachineScaleSets/vmss1/virtualMachines/0" in call_args[0][1]
            assert result is not None
            assert result["instanceId"] == "0"

    @pytest.mark.asyncio
    async def test_error_response_raises_exception(self, mock_token_provider):
        """Test that error response raises ConnectorException."""
        mock_response = MockResponse(
            status=404,
            text='{"error": {"code": "ResourceNotFound", "message": "VM not found"}}'
        )

        client = AzurevmClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ):
            with pytest.raises(ConnectorException) as exc_info:
                await client.virtual_machine_in_scale_set_get_async(
                    subscription_id="sub1",
                    resource_group_name="rg1",
                    virtual_machine_scale_set_name="vmss1",
                    virtual_machine_in_scale_set_instance_id="0"
                )

            assert exc_info.value.status_code == 404


class TestVirtualMachineInScaleSetDeallocateAsync:
    """Tests for virtual_machine_in_scale_set_deallocate_async method."""

    @pytest.mark.asyncio
    async def test_success(self, mock_token_provider):
        """Test successful request."""
        mock_response = MockResponse(status=202, text='')

        client = AzurevmClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ) as mock_send:
            await client.virtual_machine_in_scale_set_deallocate_async(
                subscription_id="sub1",
                resource_group_name="rg1",
                virtual_machine_scale_set_name="vmss1",
                virtual_machine_in_scale_set_instance_id="0"
            )

            mock_send.assert_called_once()
            call_args = mock_send.call_args
            assert call_args[0][0] == "POST"
            assert "/virtualMachineScaleSets/vmss1/virtualMachines/0/deallocate" in call_args[0][1]


class TestVirtualMachineInScaleSetPowerOffAsync:
    """Tests for virtual_machine_in_scale_set_power_off_async method."""

    @pytest.mark.asyncio
    async def test_success(self, mock_token_provider):
        """Test successful request."""
        mock_response = MockResponse(status=202, text='')

        client = AzurevmClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ) as mock_send:
            await client.virtual_machine_in_scale_set_power_off_async(
                subscription_id="sub1",
                resource_group_name="rg1",
                virtual_machine_scale_set_name="vmss1",
                virtual_machine_in_scale_set_instance_id="0"
            )

            mock_send.assert_called_once()
            call_args = mock_send.call_args
            assert call_args[0][0] == "POST"
            assert "/virtualMachineScaleSets/vmss1/virtualMachines/0/poweroff" in call_args[0][1]


class TestVirtualMachineInScaleSetRedeployAsync:
    """Tests for virtual_machine_in_scale_set_redeploy_async method."""

    @pytest.mark.asyncio
    async def test_success(self, mock_token_provider):
        """Test successful request."""
        mock_response = MockResponse(status=202, text='')

        client = AzurevmClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ) as mock_send:
            await client.virtual_machine_in_scale_set_redeploy_async(
                subscription_id="sub1",
                resource_group_name="rg1",
                virtual_machine_scale_set_name="vmss1",
                virtual_machine_in_scale_set_instance_id="0"
            )

            mock_send.assert_called_once()
            call_args = mock_send.call_args
            assert call_args[0][0] == "POST"
            assert "/virtualMachineScaleSets/vmss1/virtualMachines/0/redeploy" in call_args[0][1]


class TestVirtualMachineInScaleSetReimageAsync:
    """Tests for virtual_machine_in_scale_set_reimage_async method."""

    @pytest.mark.asyncio
    async def test_success(self, mock_token_provider):
        """Test successful request."""
        mock_response = MockResponse(status=202, text='')

        client = AzurevmClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ) as mock_send:
            await client.virtual_machine_in_scale_set_reimage_async(
                subscription_id="sub1",
                resource_group_name="rg1",
                virtual_machine_scale_set_name="vmss1",
                virtual_machine_in_scale_set_instance_id="0"
            )

            mock_send.assert_called_once()
            call_args = mock_send.call_args
            assert call_args[0][0] == "POST"
            assert "/virtualMachineScaleSets/vmss1/virtualMachines/0/reimage" in call_args[0][1]


class TestVirtualMachineInScaleSetRestartAsync:
    """Tests for virtual_machine_in_scale_set_restart_async method."""

    @pytest.mark.asyncio
    async def test_success(self, mock_token_provider):
        """Test successful request."""
        mock_response = MockResponse(status=202, text='')

        client = AzurevmClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ) as mock_send:
            await client.virtual_machine_in_scale_set_restart_async(
                subscription_id="sub1",
                resource_group_name="rg1",
                virtual_machine_scale_set_name="vmss1",
                virtual_machine_in_scale_set_instance_id="0"
            )

            mock_send.assert_called_once()
            call_args = mock_send.call_args
            assert call_args[0][0] == "POST"
            assert "/virtualMachineScaleSets/vmss1/virtualMachines/0/restart" in call_args[0][1]


class TestVirtualMachineInScaleSetStartAsync:
    """Tests for virtual_machine_in_scale_set_start_async method."""

    @pytest.mark.asyncio
    async def test_success(self, mock_token_provider):
        """Test successful request."""
        mock_response = MockResponse(status=202, text='')

        client = AzurevmClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ) as mock_send:
            await client.virtual_machine_in_scale_set_start_async(
                subscription_id="sub1",
                resource_group_name="rg1",
                virtual_machine_scale_set_name="vmss1",
                virtual_machine_in_scale_set_instance_id="0"
            )

            mock_send.assert_called_once()
            call_args = mock_send.call_args
            assert call_args[0][0] == "POST"
            assert "/virtualMachineScaleSets/vmss1/virtualMachines/0/start" in call_args[0][1]


class TestDataClasses:
    """Tests for dataclass definitions."""

    def test_virtual_machine_defaults(self):
        """Test VirtualMachine dataclass with defaults."""
        vm = VirtualMachine()
        assert vm.id is None
        assert vm.name is None
        assert vm.properties is None

    def test_virtual_machine_with_values(self):
        """Test VirtualMachine dataclass with values."""
        props = VirtualMachineProperties(provisioning_state="Succeeded")
        vm = VirtualMachine(
            id="/subscriptions/sub1/vms/vm1",
            name="vm1",
            properties=props
        )
        assert vm.id == "/subscriptions/sub1/vms/vm1"
        assert vm.name == "vm1"
        assert vm.properties.provisioning_state == "Succeeded"

    def test_virtual_machine_properties_defaults(self):
        """Test VirtualMachineProperties dataclass with defaults."""
        props = VirtualMachineProperties()
        assert props.provisioning_state is None

    def test_virtual_machine_in_scale_set_defaults(self):
        """Test VirtualMachineInScaleSet dataclass with defaults."""
        vm = VirtualMachineInScaleSet()
        assert vm.id is None
        assert vm.name is None
        assert vm.instance_id is None
        assert vm.properties is None

    def test_virtual_machine_in_scale_set_with_values(self):
        """Test VirtualMachineInScaleSet dataclass with values."""
        props = VirtualMachineInScaleSetProperties(provisioning_state="Running")
        vm = VirtualMachineInScaleSet(
            id="/subscriptions/sub1/vmss/vmss1/virtualMachines/0",
            name="vmss1_0",
            instance_id="0",
            properties=props
        )
        assert vm.id == "/subscriptions/sub1/vmss/vmss1/virtualMachines/0"
        assert vm.name == "vmss1_0"
        assert vm.instance_id == "0"
        assert vm.properties.provisioning_state == "Running"

    def test_virtual_machine_list_result_defaults(self):
        """Test VirtualMachineListResult dataclass with defaults."""
        result = VirtualMachineListResult()
        assert result.value is None
        assert result.next_link is None

    def test_virtual_machine_list_result_with_values(self):
        """Test VirtualMachineListResult dataclass with values."""
        vm1 = VirtualMachine(id="vm1", name="VM 1")
        vm2 = VirtualMachine(id="vm2", name="VM 2")
        result = VirtualMachineListResult(
            value=[vm1, vm2],
            next_link="https://example.com/next"
        )
        assert len(result.value) == 2
        assert result.value[0].name == "VM 1"
        assert result.next_link == "https://example.com/next"

    def test_virtual_machine_scale_set_defaults(self):
        """Test VirtualMachineScaleSet dataclass with defaults."""
        vmss = VirtualMachineScaleSet()
        assert vmss.id is None
        assert vmss.name is None
        assert vmss.properties is None

    def test_virtual_machine_scale_set_with_values(self):
        """Test VirtualMachineScaleSet dataclass with values."""
        props = VirtualMachineScaleSetProperties(provisioning_state="Succeeded")
        vmss = VirtualMachineScaleSet(
            id="/subscriptions/sub1/vmss/vmss1",
            name="vmss1",
            properties=props
        )
        assert vmss.id == "/subscriptions/sub1/vmss/vmss1"
        assert vmss.name == "vmss1"
        assert vmss.properties.provisioning_state == "Succeeded"

    def test_resource_group_defaults(self):
        """Test ResourceGroup dataclass with defaults."""
        rg = ResourceGroup()
        assert rg.id is None
        assert rg.name is None
        assert rg.managed_by is None

    def test_resource_group_with_values(self):
        """Test ResourceGroup dataclass with values."""
        rg = ResourceGroup(
            id="/subscriptions/sub1/resourceGroups/rg1",
            name="rg1",
            managed_by="/subscriptions/sub1/aks/cluster1"
        )
        assert rg.id == "/subscriptions/sub1/resourceGroups/rg1"
        assert rg.name == "rg1"
        assert rg.managed_by == "/subscriptions/sub1/aks/cluster1"

    def test_subscription_defaults(self):
        """Test Subscription dataclass with defaults."""
        sub = Subscription()
        assert sub.id is None
        assert sub.subscription_id is None
        assert sub.tenant_id is None
        assert sub.display_name is None
        assert sub.state is None
        assert sub.authorization_source is None

    def test_subscription_with_values(self):
        """Test Subscription dataclass with values."""
        sub = Subscription(
            id="/subscriptions/12345",
            subscription_id="12345",
            tenant_id="tenant1",
            display_name="My Subscription",
            state="Enabled",
            authorization_source="RoleBased"
        )
        assert sub.subscription_id == "12345"
        assert sub.display_name == "My Subscription"
        assert sub.state == "Enabled"

    def test_subscription_list_result_defaults(self):
        """Test SubscriptionListResult dataclass with defaults."""
        result = SubscriptionListResult()
        assert result.value is None
        assert result.next_link is None

    def test_resource_group_list_result_defaults(self):
        """Test ResourceGroupListResult dataclass with defaults."""
        result = ResourceGroupListResult()
        assert result.value is None
        assert result.next_link is None

    def test_virtual_machine_scale_set_list_result_defaults(self):
        """Test VirtualMachineScaleSetListResult dataclass with defaults."""
        result = VirtualMachineScaleSetListResult()
        assert result.value is None
        assert result.next_link is None

    def test_virtual_machine_in_scale_set_list_result_defaults(self):
        """Test VirtualMachineInScaleSetListResult dataclass with defaults."""
        result = VirtualMachineInScaleSetListResult()
        assert result.value is None
        assert result.next_link is None
