# Sample Connector Usage

This directory contains samples demonstrating how to use the Azure Connectors SDK for Python.

## Prerequisites

1. **Python 3.10+**
2. **Azure Connectors SDK**: `pip install azure-connectors`
3. **Connection runtime URL** from Azure Portal

## Samples

Each sample file (`sample_connector_usage_*.py`) demonstrates a specific connector's operations. Run any sample with:

```bash
python sample_connector_usage_<connector>.py
```

| Sample | Connector | Environment Variable |
|--------|-----------|---------------------|
| `sample_connector_usage_office365.py` | Office 365 Outlook | `OFFICE365_CONNECTION_URL` |
| `sample_connector_usage_sharepoint.py` | SharePoint Online | `SHAREPOINT_CONNECTION_URL` |
| `sample_connector_usage_kusto.py` | Azure Data Explorer | `KUSTO_CONNECTION_URL` |
| `sample_connector_usage_teams.py` | Microsoft Teams | `TEAMS_CONNECTION_URL` |
| `sample_connector_usage_msgraph.py` | MS Graph Groups & Users | `MSGRAPH_CONNECTION_URL` |

Set the appropriate environment variable to your connection runtime URL before running:

```bash
# PowerShell
$env:OFFICE365_CONNECTION_URL = "https://[region].azure-apihub.net/apim/office365/[connection-id]"

# Bash
export OFFICE365_CONNECTION_URL="https://[region].azure-apihub.net/apim/office365/[connection-id]"
```

## Usage Pattern

All connector clients follow the same async context manager pattern:

```python
import asyncio
from azure.identity.aio import DefaultAzureCredential
from azure.connectors import ConnectorException
from azure.connectors.<connector> import <Connector>Client

CONNECTION_URL = "https://[region].azure-apihub.net/apim/<connector>/[connection-id]"

async def main():
    credential = DefaultAzureCredential()
    
    async with <Connector>Client(CONNECTION_URL, credential) as client:
        try:
            result = await client.<operation>_async()
            print(result)
        except ConnectorException as ex:
            print(f"Connector error: {ex}")

asyncio.run(main())
```

## Error Handling

The SDK provides structured error handling via `ConnectorException`:

```python
from azure.connectors import ConnectorException

try:
    result = await client.some_operation_async()
except ConnectorException as ex:
    print(f"Status: {ex.status_code}, Message: {ex}")
```

## Next Steps

1. Set up a connection in Azure Portal (see [connection-setup.md](../../docs/connection-setup.md))
2. Set the connection runtime URL environment variable
3. Run the sample for your connector
4. Use typed clients in your application
5. Deploy to Azure Functions or run locally

## Reference

- Python SDK: [PythonSDK/src/azure_workflows_connectors_sdk](../../src/azure_workflows_connectors_sdk)
- Generation Guide: [GENERATION.md](../../GENERATION.md)
- .NET Sample: [DotnetSDK/samples/SampleConnectorUsage](../../../DotnetSDK/samples/SampleConnectorUsage)
