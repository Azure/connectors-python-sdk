# Copyright (c) Microsoft Corporation. All rights reserved.

"""Unit tests for WdatpClient."""

import json
import pytest
from unittest.mock import AsyncMock, patch
from azure.connectors.wdatp import (
    WdatpClient,
    AdvancedHuntingInput,
    PatchAlertInput,
    StartInvestigationInput,
    CollectInvestigationPackageInput,
    IsolateMachineInput,
    UnisolateMachineInput,
    RestrictAppExecutionInput,
    RunAntivirusScanInput,
    MachineTagInput,
)
from azure.connectors.sdk import (
    ConnectorClientOptions,
    ManagedIdentityTokenProvider,
    ConnectorException,
)
from tests.conftest import MockResponse


class TestWdatpClientInitialization:
    """Tests for WdatpClient initialization."""

    def test_init_with_valid_url_and_defaults(self):
        """Test initialization with valid URL and default parameters."""
        client = WdatpClient("https://example.azure.com/connections/test")

        assert client._connection_runtime_url == "https://example.azure.com/connections/test"
        assert client.connector_name == "wdatp"
        assert isinstance(client._http_client._token_provider, ManagedIdentityTokenProvider)

    def test_init_with_trailing_slash(self):
        """Test that trailing slash is removed from URL."""
        client = WdatpClient("https://example.azure.com/connections/test/")

        assert client._connection_runtime_url == "https://example.azure.com/connections/test"

    def test_init_with_custom_token_provider(self, mock_token_provider):
        """Test initialization with custom token provider."""
        client = WdatpClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        assert client._http_client._token_provider is mock_token_provider

    def test_init_with_custom_options(self, mock_token_provider):
        """Test initialization with custom options."""
        options = ConnectorClientOptions(timeout_seconds=60.0, max_retry_attempts=5)
        client = WdatpClient(
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
            WdatpClient("")

    def test_init_with_none_url_raises_error(self):
        """Test that None URL raises ValueError."""
        with pytest.raises(ValueError, match="connection_runtime_url cannot be None or empty"):
            WdatpClient(None)

    def test_connector_name_property(self, mock_token_provider):
        """Test connector_name property returns 'wdatp'."""
        client = WdatpClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        assert client.connector_name == "wdatp"


class TestWdatpClientLifecycle:
    """Tests for WdatpClient lifecycle methods."""

    @pytest.mark.asyncio
    async def test_close(self, mock_token_provider):
        """Test close method calls http_client.close."""
        client = WdatpClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        with patch.object(client._http_client, 'close', new_callable=AsyncMock) as mock_close:
            await client.close()
            mock_close.assert_called_once()

    @pytest.mark.asyncio
    async def test_context_manager(self, mock_token_provider):
        """Test async context manager functionality."""
        with patch.object(WdatpClient, 'close', new_callable=AsyncMock) as mock_close:
            async with WdatpClient(
                "https://example.azure.com/connections/test",
                token_provider=mock_token_provider
            ) as client:
                assert isinstance(client, WdatpClient)

            mock_close.assert_called_once()


class TestAdvancedHunting:
    """Tests for advanced_hunting_async method."""

    @pytest.mark.asyncio
    async def test_advanced_hunting_success(self, mock_token_provider):
        """Test successful advanced hunting query."""
        client = WdatpClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        response_data = {
            "stats": {"executionTime": 1.5},
            "results": [{"DeviceName": "Device1"}]
        }
        mock_response = MockResponse(200, json.dumps(response_data))
        with patch.object(
            client._http_client, 'send_async', new_callable=AsyncMock, return_value=mock_response
        ) as mock_send:
            input_data = AdvancedHuntingInput(query="DeviceInfo | take 10")
            result = await client.advanced_hunting_async(input=input_data)

            mock_send.assert_called_once()
            call_args = mock_send.call_args
            assert call_args[0][0] == "POST"
            assert "api/advancedqueries/run" in call_args[0][1]
            assert result["results"][0]["DeviceName"] == "Device1"

    @pytest.mark.asyncio
    async def test_advanced_hunting_error(self, mock_token_provider):
        """Test advanced hunting error response."""
        client = WdatpClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(400, "Invalid query")
        with patch.object(
            client._http_client, 'send_async', new_callable=AsyncMock, return_value=mock_response
        ):
            input_data = AdvancedHuntingInput(query="invalid")
            with pytest.raises(ConnectorException):
                await client.advanced_hunting_async(input=input_data)


class TestGetAlerts:
    """Tests for get_alerts_async method."""

    @pytest.mark.asyncio
    async def test_get_alerts_success(self, mock_token_provider):
        """Test successful alerts retrieval."""
        client = WdatpClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        response_data = {
            "count": 2,
            "value": [
                {"id": "alert-1", "title": "Alert 1"},
                {"id": "alert-2", "title": "Alert 2"}
            ]
        }
        mock_response = MockResponse(200, json.dumps(response_data))
        with patch.object(
            client._http_client, 'send_async', new_callable=AsyncMock, return_value=mock_response
        ) as mock_send:
            result = await client.get_alerts_async()

            call_args = mock_send.call_args
            assert call_args[0][0] == "GET"
            assert "api/alerts" in call_args[0][1]
            assert result["count"] == 2

    @pytest.mark.asyncio
    async def test_get_alerts_with_filter(self, mock_token_provider):
        """Test get alerts with filter parameter."""
        client = WdatpClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(200, '{"count": 0, "value": []}')
        with patch.object(
            client._http_client, 'send_async', new_callable=AsyncMock, return_value=mock_response
        ) as mock_send:
            await client.get_alerts_async(filter="severity eq 'High'")

            call_args = mock_send.call_args
            assert "$filter=" in call_args[0][1]

    @pytest.mark.asyncio
    async def test_get_alerts_with_pagination(self, mock_token_provider):
        """Test get alerts with pagination parameters."""
        client = WdatpClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(200, '{"count": 0, "value": []}')
        with patch.object(
            client._http_client, 'send_async', new_callable=AsyncMock, return_value=mock_response
        ) as mock_send:
            await client.get_alerts_async(top="10", skip="5")

            call_args = mock_send.call_args
            assert "$top=10" in call_args[0][1]
            assert "$skip=5" in call_args[0][1]


class TestGetSingleAlert:
    """Tests for get_single_alert_async method."""

    @pytest.mark.asyncio
    async def test_get_single_alert_success(self, mock_token_provider):
        """Test successful single alert retrieval."""
        client = WdatpClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        response_data = {"id": "alert-123", "title": "Test Alert", "severity": "High"}
        mock_response = MockResponse(200, json.dumps(response_data))
        with patch.object(
            client._http_client, 'send_async', new_callable=AsyncMock, return_value=mock_response
        ) as mock_send:
            result = await client.get_single_alert_async(alert_id="alert-123")

            call_args = mock_send.call_args
            assert "api/alerts/alert-123" in call_args[0][1]
            assert result["id"] == "alert-123"

    @pytest.mark.asyncio
    async def test_get_single_alert_not_found(self, mock_token_provider):
        """Test get single alert not found."""
        client = WdatpClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        mock_response = MockResponse(404, "Alert not found")
        with patch.object(
            client._http_client, 'send_async', new_callable=AsyncMock, return_value=mock_response
        ):
            with pytest.raises(ConnectorException):
                await client.get_single_alert_async(alert_id="nonexistent")


class TestPatchAlert:
    """Tests for patch_alert_async method."""

    @pytest.mark.asyncio
    async def test_patch_alert_success(self, mock_token_provider):
        """Test successful alert update."""
        client = WdatpClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        response_data = {"id": "alert-123", "status": "Resolved"}
        mock_response = MockResponse(200, json.dumps(response_data))
        with patch.object(
            client._http_client, 'send_async', new_callable=AsyncMock, return_value=mock_response
        ) as mock_send:
            input_data = PatchAlertInput(status="Resolved")
            result = await client.patch_alert_async(input=input_data, alert_id="alert-123")

            call_args = mock_send.call_args
            assert call_args[0][0] == "PATCH"
            assert "api/alerts/alert-123" in call_args[0][1]
            assert result["status"] == "Resolved"


class TestGetMachines:
    """Tests for get_machines_async method."""

    @pytest.mark.asyncio
    async def test_get_machines_success(self, mock_token_provider):
        """Test successful machines retrieval."""
        client = WdatpClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        response_data = {
            "count": 2,
            "value": [
                {"id": "machine-1", "computerDnsName": "PC1"},
                {"id": "machine-2", "computerDnsName": "PC2"}
            ]
        }
        mock_response = MockResponse(200, json.dumps(response_data))
        with patch.object(
            client._http_client, 'send_async', new_callable=AsyncMock, return_value=mock_response
        ) as mock_send:
            result = await client.get_machines_async()

            call_args = mock_send.call_args
            assert "api/machines" in call_args[0][1]
            assert result["count"] == 2


class TestGetSingleMachine:
    """Tests for get_single_machine_async method."""

    @pytest.mark.asyncio
    async def test_get_single_machine_success(self, mock_token_provider):
        """Test successful single machine retrieval."""
        client = WdatpClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        response_data = {"id": "machine-123", "computerDnsName": "TestPC"}
        mock_response = MockResponse(200, json.dumps(response_data))
        with patch.object(
            client._http_client, 'send_async', new_callable=AsyncMock, return_value=mock_response
        ) as mock_send:
            result = await client.get_single_machine_async(machine_id="machine-123")

            call_args = mock_send.call_args
            assert "api/machines/machine-123" in call_args[0][1]
            assert result["computerDnsName"] == "TestPC"


class TestIsolateMachine:
    """Tests for isolate_machine_async method."""

    @pytest.mark.asyncio
    async def test_isolate_machine_success(self, mock_token_provider):
        """Test successful machine isolation."""
        client = WdatpClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        response_data = {"id": "action-123", "type": "Isolate", "status": "InProgress"}
        mock_response = MockResponse(200, json.dumps(response_data))
        with patch.object(
            client._http_client, 'send_async', new_callable=AsyncMock, return_value=mock_response
        ) as mock_send:
            input_data = IsolateMachineInput(comment="Security investigation")
            result = await client.isolate_machine_async(
                input=input_data,
                machine_id="machine-123"
            )

            call_args = mock_send.call_args
            assert call_args[0][0] == "POST"
            assert "machines/machine-123/isolate" in call_args[0][1]
            assert result["type"] == "Isolate"


class TestUnisolateMachine:
    """Tests for unisolate_machine_async method."""

    @pytest.mark.asyncio
    async def test_unisolate_machine_success(self, mock_token_provider):
        """Test successful machine unisolation."""
        client = WdatpClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        response_data = {"id": "action-124", "type": "Unisolate", "status": "InProgress"}
        mock_response = MockResponse(200, json.dumps(response_data))
        with patch.object(
            client._http_client, 'send_async', new_callable=AsyncMock, return_value=mock_response
        ) as mock_send:
            input_data = UnisolateMachineInput(comment="Investigation complete")
            await client.unisolate_machine_async(
                input=input_data,
                machine_id="machine-123"
            )

            call_args = mock_send.call_args
            assert "machines/machine-123/unisolate" in call_args[0][1]


class TestRunAntivirusScan:
    """Tests for run_antivirus_scan_async method."""

    @pytest.mark.asyncio
    async def test_run_antivirus_scan_success(self, mock_token_provider):
        """Test successful antivirus scan initiation."""
        client = WdatpClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        response_data = {"id": "action-125", "type": "RunAntiVirusScan", "status": "InProgress"}
        mock_response = MockResponse(200, json.dumps(response_data))
        with patch.object(
            client._http_client, 'send_async', new_callable=AsyncMock, return_value=mock_response
        ) as mock_send:
            input_data = RunAntivirusScanInput(comment="Routine scan", scan_type="Quick")
            await client.run_antivirus_scan_async(
                input=input_data,
                machine_id="machine-123"
            )

            call_args = mock_send.call_args
            assert "machines/machine-123/runAntiVirusScan" in call_args[0][1]


class TestCollectInvestigationPackage:
    """Tests for collect_investigation_package_async method."""

    @pytest.mark.asyncio
    async def test_collect_investigation_package_success(self, mock_token_provider):
        """Test successful investigation package collection."""
        client = WdatpClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        response_data = {"id": "action-126", "type": "CollectInvestigationPackage"}
        mock_response = MockResponse(200, json.dumps(response_data))
        with patch.object(
            client._http_client, 'send_async', new_callable=AsyncMock, return_value=mock_response
        ) as mock_send:
            input_data = CollectInvestigationPackageInput(comment="Forensic analysis")
            await client.collect_investigation_package_async(
                input=input_data,
                machine_id="machine-123"
            )

            call_args = mock_send.call_args
            assert "collectInvestigationPackage" in call_args[0][1]


class TestGetMachineActions:
    """Tests for get_machine_actions_async method."""

    @pytest.mark.asyncio
    async def test_get_machine_actions_success(self, mock_token_provider):
        """Test successful machine actions retrieval."""
        client = WdatpClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        response_data = {
            "count": 1,
            "value": [{"id": "action-1", "type": "Isolate"}]
        }
        mock_response = MockResponse(200, json.dumps(response_data))
        with patch.object(
            client._http_client, 'send_async', new_callable=AsyncMock, return_value=mock_response
        ) as mock_send:
            result = await client.get_machine_actions_async()

            call_args = mock_send.call_args
            assert "api/machineactions" in call_args[0][1]
            assert result["count"] == 1


class TestGetInvestigations:
    """Tests for get_investigations_async method."""

    @pytest.mark.asyncio
    async def test_get_investigations_success(self, mock_token_provider):
        """Test successful investigations retrieval."""
        client = WdatpClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        response_data = {
            "count": 1,
            "value": [{"id": "inv-1", "state": "Running"}]
        }
        mock_response = MockResponse(200, json.dumps(response_data))
        with patch.object(
            client._http_client, 'send_async', new_callable=AsyncMock, return_value=mock_response
        ) as mock_send:
            result = await client.get_investigations_async()

            call_args = mock_send.call_args
            assert "api/investigations" in call_args[0][1]
            assert result["count"] == 1


class TestStartInvestigation:
    """Tests for start_investigation_async method."""

    @pytest.mark.asyncio
    async def test_start_investigation_success(self, mock_token_provider):
        """Test successful investigation start."""
        client = WdatpClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        response_data = {"id": "inv-123", "state": "Running"}
        mock_response = MockResponse(200, json.dumps(response_data))
        with patch.object(
            client._http_client, 'send_async', new_callable=AsyncMock, return_value=mock_response
        ) as mock_send:
            input_data = StartInvestigationInput(comment="Suspicious activity")
            await client.start_investigation_async(
                input=input_data,
                machine_id="machine-123"
            )

            call_args = mock_send.call_args
            assert "startInvestigation" in call_args[0][1]


class TestMachineTag:
    """Tests for machine_tag_async method."""

    @pytest.mark.asyncio
    async def test_add_machine_tag_success(self, mock_token_provider):
        """Test successful machine tag addition."""
        client = WdatpClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        response_data = {"id": "machine-123", "machineTags": ["HighValue"]}
        mock_response = MockResponse(200, json.dumps(response_data))
        with patch.object(
            client._http_client, 'send_async', new_callable=AsyncMock, return_value=mock_response
        ) as mock_send:
            input_data = MachineTagInput(value="HighValue", action="Add")
            result = await client.machine_tag_async(
                input=input_data,
                machine_id="machine-123"
            )

            call_args = mock_send.call_args
            assert "machines/machine-123/tags" in call_args[0][1]
            assert "HighValue" in result["machineTags"]


class TestGetFileStats:
    """Tests for get_file_stats_async method."""

    @pytest.mark.asyncio
    async def test_get_file_stats_success(self, mock_token_provider):
        """Test successful file statistics retrieval."""
        client = WdatpClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        response_data = {"sha1": "abc123", "globallyPrevalence": 100}
        mock_response = MockResponse(200, json.dumps(response_data))
        with patch.object(
            client._http_client, 'send_async', new_callable=AsyncMock, return_value=mock_response
        ) as mock_send:
            result = await client.get_file_stats_async(file_id="abc123")

            call_args = mock_send.call_args
            assert "api/files/abc123/stats" in call_args[0][1]
            assert result["sha1"] == "abc123"


class TestGetDomainStats:
    """Tests for get_domain_stats_async method."""

    @pytest.mark.asyncio
    async def test_get_domain_stats_success(self, mock_token_provider):
        """Test successful domain statistics retrieval."""
        client = WdatpClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        response_data = {"host": "example.com", "organizationPrevalence": 50}
        mock_response = MockResponse(200, json.dumps(response_data))
        with patch.object(
            client._http_client, 'send_async', new_callable=AsyncMock, return_value=mock_response
        ) as mock_send:
            result = await client.get_domain_stats_async(domain_name="example.com")

            call_args = mock_send.call_args
            assert "api/domains/example.com/stats" in call_args[0][1]
            assert result["host"] == "example.com"


class TestGetIpStats:
    """Tests for get_ip_stats_async method."""

    @pytest.mark.asyncio
    async def test_get_ip_stats_success(self, mock_token_provider):
        """Test successful IP statistics retrieval."""
        client = WdatpClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        response_data = {"ipAddress": "192.168.1.1", "organizationPrevalence": 25}
        mock_response = MockResponse(200, json.dumps(response_data))
        with patch.object(
            client._http_client, 'send_async', new_callable=AsyncMock, return_value=mock_response
        ) as mock_send:
            result = await client.get_ip_stats_async(ip_address="192.168.1.1")

            call_args = mock_send.call_args
            assert "api/ips/192.168.1.1/stats" in call_args[0][1]
            assert result["ipAddress"] == "192.168.1.1"


class TestRestrictAppExecution:
    """Tests for restrict_app_execution_async method."""

    @pytest.mark.asyncio
    async def test_restrict_app_execution_success(self, mock_token_provider):
        """Test successful app execution restriction."""
        client = WdatpClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        response_data = {"id": "action-127", "type": "RestrictCodeExecution"}
        mock_response = MockResponse(200, json.dumps(response_data))
        with patch.object(
            client._http_client, 'send_async', new_callable=AsyncMock, return_value=mock_response
        ) as mock_send:
            input_data = RestrictAppExecutionInput(comment="Containment")
            await client.restrict_app_execution_async(
                input=input_data,
                machine_id="machine-123"
            )

            call_args = mock_send.call_args
            assert "restrictCodeExecution" in call_args[0][1]


class TestGetRemediationActivities:
    """Tests for get_remediation_activities_async method."""

    @pytest.mark.asyncio
    async def test_get_remediation_activities_success(self, mock_token_provider):
        """Test successful remediation activities retrieval."""
        client = WdatpClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        response_data = {
            "count": 1,
            "value": [{"id": "rem-1", "title": "Update software"}]
        }
        mock_response = MockResponse(200, json.dumps(response_data))
        with patch.object(
            client._http_client, 'send_async', new_callable=AsyncMock, return_value=mock_response
        ) as mock_send:
            result = await client.get_remediation_activities_async()

            call_args = mock_send.call_args
            assert "api/remediationtasks" in call_args[0][1]
            assert result["count"] == 1
